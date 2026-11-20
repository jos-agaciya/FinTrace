"""Unified public engine facade for FinTrace AI Engine.

Implements FinTraceAIEngineProtocol to coordinate claim understanding,
deterministic validation, interpretation forks, and dual-model review.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from claim_extraction.extractor import ClaimExtractor
from claim_extraction.schemas import EvidenceItem, ExtractedClaim
from assessment.evaluator import AssessmentEvaluator
from assessment.schemas import AssessmentEvaluationOutput, UserAssessmentInput
from engine_interface import (
    ClaimExtractionInput,
    DualModelReviewInput,
    DualModelReviewOutput,
    FinTraceAIEngineProtocol,
    ForkAnalysisInput,
    FullPipelineAnalysisResult,
)
from fallback.fallback_manager import FallbackManager
from interpretation.counterfactual import (
    CounterfactualClaimGenerator,
    CounterfactualGenerationResult,
)
from interpretation.fork_engine import InterpretationForkEngine
from interpretation.schemas import ForkAnalysisResult
from interpretation.sensitivity import (
    DecisionSensitivityEngine,
    DecisionSensitivityExplanation,
    DecisionSensitivityInput,
)
from orchestration.reviewer import DualModelReviewer
from providers.base import BaseLLMProvider
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider
from providers.mock_provider import MockProvider
from validation.deterministic import DeterministicValidator
from validation.schemas import ValidationResult

logger = logging.getLogger("fintrace.ai.facade")


# FullPipelineAnalysisResult imported from engine_interface


class FinTraceAIEngine(FinTraceAIEngineProtocol):
    """Primary operational facade consumed by the FinTrace backend."""

    def __init__(
        self,
        primary_provider: Optional[BaseLLMProvider] = None,
        reviewer_provider: Optional[BaseLLMProvider] = None,
    ):
        self.primary_provider = primary_provider or MockProvider(name="mock-primary")
        self.reviewer_provider = reviewer_provider

        # Subsystems
        self.extractor = ClaimExtractor(self.primary_provider)
        self.validator = DeterministicValidator()
        self.fork_engine = InterpretationForkEngine(self.primary_provider)
        self.reviewer = DualModelReviewer(self.primary_provider, self.reviewer_provider)
        self.counterfactual_generator = CounterfactualClaimGenerator()
        self.sensitivity_engine = DecisionSensitivityEngine()
        self.assessment_evaluator = AssessmentEvaluator()

    @classmethod
    def from_env(
        cls,
        env_file: Optional[str] = None,
        use_fallback_manager: bool = True,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 60.0,
    ) -> "FinTraceAIEngine":
        """Factory creating live production AI Engine configured from environment variables.

        Loads .env file if available, wires Groq as primary, Gemini as reviewer/fallback,
        and wraps in FallbackManager with circuit breaker protection.
        """
        try:
            from dotenv import load_dotenv
            if env_file:
                load_dotenv(env_file)
            else:
                # Look in current working dir or ai-engine root
                ai_env = Path(__file__).parent / ".env"
                if ai_env.exists():
                    load_dotenv(ai_env)
                else:
                    load_dotenv()
        except ImportError:
            pass

        groq_key = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        groq_provider = GroqProvider(api_key=groq_key) if groq_key else None
        gemini_provider = GeminiProvider(api_key=gemini_key) if gemini_key else None

        if not groq_provider and not gemini_provider:
            logger.warning(
                "Neither GROQ_API_KEY nor GEMINI_API_KEY found in environment. "
                "Defaulting to MockProvider for offline execution."
            )
            mock_primary = MockProvider(name="mock-primary")
            mock_reviewer = MockProvider(name="mock-reviewer", disagree_with_primary=False)
            return cls(primary_provider=mock_primary, reviewer_provider=mock_reviewer)

        # Configure primary provider with fallback resiliency
        if use_fallback_manager and groq_provider and gemini_provider:
            primary: BaseLLMProvider = FallbackManager(
                primary_provider=groq_provider,
                secondary_provider=gemini_provider,
                failure_threshold=failure_threshold,
                recovery_timeout_seconds=recovery_timeout_seconds,
            )
            reviewer: Optional[BaseLLMProvider] = gemini_provider
        elif groq_provider:
            primary = groq_provider
            reviewer = gemini_provider
        else:
            # Only gemini available
            primary = gemini_provider  # type: ignore
            reviewer = None

        return cls(primary_provider=primary, reviewer_provider=reviewer)

    def get_health_status(self) -> Dict[str, Any]:
        """Telemetry snapshot of engine subsystems and underlying circuit breakers."""
        status: Dict[str, Any] = {
            "primary_provider": getattr(self.primary_provider, "provider_name", "unknown"),
            "reviewer_provider": (
                getattr(self.reviewer_provider, "provider_name", "none")
                if self.reviewer_provider
                else "none"
            ),
        }
        if isinstance(self.primary_provider, FallbackManager):
            status["resilience"] = self.primary_provider.get_health_status()
        return status

    async def extract_and_compile(
        self, input_data: ClaimExtractionInput
    ) -> ExtractedClaim:
        """Extract a structured claim and compile falsifiability criteria."""
        return await self.extractor.extract_claim(input_data)

    async def analyze_forks(
        self, input_data: ForkAnalysisInput
    ) -> ForkAnalysisResult:
        """Detect ambiguities and synthesize alternative interpretation forks."""
        return await self.fork_engine.analyze_forks(
            claim=input_data.claim,
            max_forks=input_data.max_forks,
        )

    async def review_dual_model(
        self, input_data: DualModelReviewInput
    ) -> DualModelReviewOutput:
        """Execute independent reviewer model critique over primary claim."""
        return await self.reviewer.review(input_data)

    async def validate_claim(
        self,
        claim: ExtractedClaim,
        raw_text: Optional[str] = None,
        published_at: Optional[datetime] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> ValidationResult:
        """Run deterministic non-LLM validation over an extracted claim."""
        return self.validator.validate_claim(
            claim=claim,
            raw_text=raw_text,
            published_at=published_at,
            evidence=evidence,
        )

    async def analyze_end_to_end(
        self, input_data: ClaimExtractionInput
    ) -> FullPipelineAnalysisResult:
        """Execute the complete end-to-end AI pipeline in one coordinated call."""
        start_time = time.perf_counter()

        # 1. Extraction
        claim = await self.extract_and_compile(input_data)

        # 2. Deterministic Validation & Grounding
        validation = self.validator.validate_claim(
            claim=claim,
            raw_text=input_data.raw_text,
            published_at=input_data.published_at,
            evidence=input_data.retrieved_evidence,
        )

        # 3. Interpretation Forks
        fork_input = ForkAnalysisInput(claim=claim, max_forks=3)
        fork_analysis = await self.analyze_forks(fork_input)

        # 4. Dual Model Review (if reviewer configured)
        review_output = None
        meta = claim.metadata or {}
        primary_provider = meta.get("provider_name", getattr(self.primary_provider, "provider_name", "unknown"))
        primary_model = meta.get("model_id", "unknown")
        fallback_used = meta.get("fallback_used", False)
        is_degraded = meta.get("degraded", False)
        primary_failure_reason = meta.get("primary_failure_reason")

        if self.reviewer_provider:
            review_input = DualModelReviewInput(
                claim=claim,
                evidence=input_data.retrieved_evidence,
                extractor_provider=primary_provider,
                extractor_model=primary_model,
            )
            review_output = await self.review_dual_model(review_input)

            if review_output and (review_output.review_mode != "INDEPENDENT_DUAL_MODEL" or not review_output.independent_review_valid):
                is_degraded = True

            # If dual-model review identified disagreements and spawned uncertainty forks, merge them
            if review_output and review_output.spawned_forks:
                merged_forks = fork_analysis.forks + review_output.spawned_forks
                merged_ambiguities = list(set(fork_analysis.ambiguity_reasons + review_output.disagreement_reasons))
                fork_analysis = ForkAnalysisResult(
                    claim_id=claim.claim_id,
                    ambiguity_detected=True,
                    ambiguity_reasons=merged_ambiguities,
                    forks=merged_forks,
                    distinguishing_data_checklist=fork_analysis.distinguishing_data_checklist,
                    metadata=fork_analysis.metadata,
                )

        duration = (time.perf_counter() - start_time) * 1000.0

        return FullPipelineAnalysisResult(
            claim=claim,
            validation=validation,
            fork_analysis=fork_analysis,
            dual_model_review=review_output,
            pipeline_duration_ms=round(duration, 2),
            primary_provider=primary_provider,
            primary_model=primary_model,
            fallback_used=fallback_used,
            is_degraded=is_degraded,
            primary_failure_reason=primary_failure_reason,
            telemetry={
                "extraction": meta,
                "fork_analysis": fork_analysis.metadata,
                "review": review_output.metadata if review_output else {},
            },
        )

    def generate_practice_claim(
        self,
        claim: Optional[ExtractedClaim] = None,
        template_category: Optional[str] = None,
    ) -> CounterfactualGenerationResult:
        """Generate a structurally comparable synthetic practice claim for independent learning."""
        return self.counterfactual_generator.generate_practice_claim(
            claim=claim, template_category=template_category
        )

    def explain_sensitivity(
        self, input_data: DecisionSensitivityInput
    ) -> DecisionSensitivityExplanation:
        """Construct an explainable comparison of investor reasoning shifts."""
        return self.sensitivity_engine.explain_sensitivity(input_data)

    def evaluate_assessment(
        self, input_data: UserAssessmentInput
    ) -> AssessmentEvaluationOutput:
        """Evaluate an investor's independent written claim critique across the 5 FinTrace dimensions."""
        return self.assessment_evaluator.evaluate_assessment(input_data)
