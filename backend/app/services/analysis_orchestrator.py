import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.claim import ClaimModel, InterpretationForkModel
from backend.app.models.analysis import AnalysisModel
from backend.app.repositories.claim_repository import ClaimRepository
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.validators.analysis_validator import AnalysisValidator
from backend.app.integrations.ai_client import (
    BaseAIProvider,
    GroqProvider,
    GeminiProvider,
    ProviderUnavailableException,
    get_ai_provider
)


class AnalysisOrchestrator:
    """
    Multi-provider AI orchestration layer.
    Coordinates Groq and Gemini with fallback handling,
    independent cross-review, and deterministic epistemological classification.
    """

    def __init__(
        self,
        db: Session,
        primary_provider: Optional[BaseAIProvider] = None,
        secondary_provider: Optional[BaseAIProvider] = None
    ):
        self.db = db
        self.claim_repo = ClaimRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.validator = AnalysisValidator()

        # Set configurable providers
        self.primary_provider = primary_provider or self._safe_init_provider(settings.PRIMARY_AI_PROVIDER)
        self.secondary_provider = secondary_provider or self._safe_init_provider(settings.SECONDARY_AI_PROVIDER)

    def _safe_init_provider(self, name: str) -> BaseAIProvider:
        try:
            return get_ai_provider(name)
        except Exception:
            return GroqProvider() if name == "groq" else GeminiProvider()

    async def run_analysis(self, claim_id: str) -> AnalysisModel:
        """Executes the full 11-step multi-provider validation workflow."""
        claim = self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found.")

        # 1. Retrieve evidence bundle
        evidence_assocs = self.evidence_repo.get_claim_evidence(claim_id)
        evidence_bundle = [
            {
                "title": a.evidence.title,
                "publisher": a.evidence.publisher,
                "content_summary": a.evidence.content_summary,
                "source_url": a.evidence.source_url,
                "provenance_status": a.evidence.provenance_status
            }
            for a in evidence_assocs
        ]

        provider_status = "SUCCESS"
        fallback_reason = None
        primary_output: Dict[str, Any] = {}
        secondary_output: Dict[str, Any] = {}

        # 2. Primary Provider Call (with fallback)
        try:
            primary_output = await self.primary_provider.analyze_claim(
                claim_text=claim.original_claim,
                evidence_bundle=evidence_bundle
            )
        except ProviderUnavailableException as e_primary:
            fallback_reason = f"Primary provider ({self.primary_provider.name}) failed: {str(e_primary)}"
            # Attempt fallback to secondary provider
            try:
                primary_output = await self.secondary_provider.analyze_claim(
                    claim_text=claim.original_claim,
                    evidence_bundle=evidence_bundle
                )
                provider_status = "FALLBACK_USED"
            except ProviderUnavailableException as e_secondary:
                # Both providers unavailable - do not fabricate!
                provider_status = "PROVIDER_UNAVAILABLE"
                fallback_reason = f"Both providers unavailable: Primary ({str(e_primary)}), Secondary ({str(e_secondary)})"
                primary_output = {
                    "interpretation_summary": "Service limitation: External AI providers unavailable. Analysis conducted using deterministic rules only."
                }

        # 3. Secondary Independent Review (if providers available)
        if provider_status in ["SUCCESS", "FALLBACK_USED"]:
            try:
                review_provider = self.secondary_provider if provider_status == "SUCCESS" else self.primary_provider
                secondary_output = await review_provider.review_analysis(
                    claim_text=claim.original_claim,
                    evidence_bundle=evidence_bundle,
                    primary_analysis=primary_output
                )
            except Exception as e_rev:
                secondary_output = {"agrees": True, "critique": f"Secondary review bypassed: {str(e_rev)}"}

        # 4. Deterministic Falsifiability Analysis
        falsifiability_score, missing_fields, testability_explanation = self.validator.calculate_falsifiability(
            target_value=claim.target_value,
            time_horizon=claim.time_horizon,
            entry_condition=claim.entry_condition,
            exit_condition=claim.exit_condition,
            invalidation_condition=claim.invalidation_condition
        )

        # 5. Deterministic Statement Categorization
        categorized = self.validator.categorize_statements(
            claim_text=claim.original_claim,
            evidence_items=evidence_bundle,
            analysis_summary=primary_output.get("interpretation_summary")
        )

        # 6. Check for Material Disagreements
        has_disagreement, issues = self.validator.detect_material_disagreements(
            primary_output=primary_output,
            secondary_output=secondary_output
        )

        validation_status = "PASSED"
        if has_disagreement:
            provider_status = "NEEDS_VERIFICATION"
            validation_status = "WARNING"

        # 7. Persist Analysis Record
        analysis = AnalysisModel(
            claim_id=claim.id,
            primary_provider=self.primary_provider.name,
            secondary_provider=self.secondary_provider.name,
            provider_status=provider_status,
            fallback_reason=fallback_reason,
            falsifiability_score=falsifiability_score,
            missing_fields=json.dumps(missing_fields),
            testability_explanation=testability_explanation,
            categorized_statements=json.dumps(categorized),
            validation_status=validation_status,
            validation_notes=json.dumps(issues) if issues else None,
            primary_output_summary=json.dumps(primary_output),
            secondary_output_summary=json.dumps(secondary_output) if secondary_output else None
        )
        self.db.add(analysis)

        # 8. Generate Interpretation Forks for ambiguous or multiple interpretations
        self._generate_interpretation_forks(claim)

        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def _generate_interpretation_forks(self, claim: ClaimModel):
        """Generates explicit alternative interpretation forks labeled as AI_GENERATED."""
        existing_forks = self.db.query(InterpretationForkModel).filter_by(claim_id=claim.id).count()
        if existing_forks > 0:
            return

        horizon_str = claim.time_horizon or "unspecified timeframe"
        direction = claim.claim_direction or "BULLISH"

        fork1 = InterpretationForkModel(
            claim_id=claim.id,
            title=f"Direct Fundamental Thesis ({direction})",
            description=f"Interprets claim as driven by verified earnings growth and expanding operational margins over {horizon_str}.",
            ambiguous_phrase=claim.time_horizon or "strong fundamentals",
            assumptions=json.dumps(["Management guidance sustained", "No macro headwinds", "Sector peer multiples hold"]),
            information_required="Audited quarterly financial statements and segment reports",
            is_ai_generated=True
        )

        fork2 = InterpretationForkModel(
            claim_id=claim.id,
            title="Speculative Momentum Thesis",
            description="Interprets claim as social-media momentum rally driven by retail speculation rather than fundamental valuation.",
            ambiguous_phrase="buy before it's too late",
            assumptions=json.dumps(["Short-term retail volume continues", "Momentum indicators stay overbought"]),
            information_required="Order book depth, institutional holding shifts, exchange delivery data",
            is_ai_generated=True
        )

        self.db.add(fork1)
        self.db.add(fork2)
