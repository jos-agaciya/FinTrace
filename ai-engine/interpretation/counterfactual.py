"""Counterfactual / Practice Claim Generator for independent investor learning.

CRITICAL INVARIANTS:
1. Generates a different, structurally comparable practice claim without showing AI analysis.
2. User-facing practice claim contains ZERO answers, hints, or interpretation forks.
3. Uses strictly synthetic entities; NEVER invents or misrepresents real company facts.
4. Provenance is permanently labeled as SYNTHETIC.
5. Preserves key structural evaluation challenges (e.g. missing timeframe, vague metric,
   unstated invalidation boundary, or entry/exit absence) for independent transfer learning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from claim_extraction.schemas import DirectionEnum, ExtractedClaim
from validation.errors import CounterfactualGenerationError


class PreservedLearningProperty(BaseModel):
    """A structural challenge or attribute preserved from the original claim to test transfer."""
    property_name: str = Field(
        ...,
        description="Name of the structural attribute (e.g. TIMEFRAME_SPECIFICITY, INVALIDATION_ABSENCE)."
    )
    original_state: str = Field(
        ...,
        description="How this attribute appeared in the original claim."
    )
    practice_state: str = Field(
        ...,
        description="How this attribute is presented in the new practice claim."
    )
    pedagogical_focus: str = Field(
        ...,
        description="What the learner is expected to identify independently."
    )


class PracticeClaim(BaseModel):
    """User-facing practice claim presented for independent evaluation.

    IMPORTANT: Contains NO answers, hints, interpretation forks, or solutions.
    """
    practice_claim_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the practice claim."
    )
    claim_text: str = Field(
        ...,
        description="Clean, user-facing synthetic financial claim statement."
    )
    synthetic_company_name: str = Field(
        ...,
        description="Synthetic demo company name (strictly non-existent)."
    )
    provenance_label: str = Field(
        default="SYNTHETIC",
        frozen=True,
        description="Immutable label ensuring consumers recognize this as a mock practice example."
    )
    is_synthetic: bool = Field(
        default=True,
        frozen=True,
        description="Always True to prevent confusing practice claims with real market disclosures."
    )


class CounterfactualGenerationResult(BaseModel):
    """Structured response containing the practice claim and internal evaluation metadata."""
    practice_claim: PracticeClaim = Field(
        ...,
        description="The practice claim to deliver to the user interface."
    )
    source_claim_id: Optional[str] = Field(
        default=None,
        description="ID of the original assisted claim that prompted this practice item."
    )
    preserved_properties: List[PreservedLearningProperty] = Field(
        default_factory=list,
        description="Structural properties preserved to measure transfer learning."
    )
    evaluation_rubric_focus: List[str] = Field(
        default_factory=list,
        description="Key evaluation dimensions to score when the user critiques this practice claim."
    )
    generation_method: str = Field(
        default="CONTROLLED_TEMPLATE_SYNTHESIS",
        description="Method used to produce the counterfactual claim."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution and pedagogical metadata."
    )


class CounterfactualClaimGenerator:
    """Generates structurally comparable synthetic claims for independent learning assessments."""

    # Controlled synthetic companies (strictly fictional entities)
    SYNTHETIC_COMPANIES: List[str] = [
        "Apex Dynamics Ltd.",
        "Novus Energy Corp.",
        "Vortex Logistics Ltd.",
        "AeroSphere Tech Inc.",
        "Kestrel Mobility Corp.",
        "Zenith BioHealth Ltd.",
    ]

    # Controlled template library indexed by primary structural challenge
    CONTROLLED_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "VAGUE_TIMEFRAME": {
            "template": "{company} will expand operating margin by {target} in the near term driven by automation.",
            "default_target": "25%",
            "flaw": "Vague temporal horizon ('near term') without specific calendar or fiscal boundary.",
            "rubric_focus": [
                "Claim specificity: Recognise missing calendar boundary for 'near term'.",
                "Assumption awareness: Identify whether margin refers to gross vs operating margin.",
            ],
            "property_name": "TIMEFRAME_SPECIFICITY",
            "pedagogical_focus": "Tests if the learner detects unanchored temporal horizons without AI assistance.",
        },
        "VAGUE_METRIC": {
            "template": "{company} will deliver massive growth across international divisions by Q4 2026.",
            "default_target": "massive growth",
            "flaw": "Ambiguous metric ('massive growth') without revenue, unit delivery, or EBITDA definition.",
            "rubric_focus": [
                "Claim specificity: Point out that 'massive growth' lacks a quantifiable benchmark.",
                "Evidence evaluation: Request segmental filing or historical unit volumes.",
            ],
            "property_name": "TARGET_SPECIFICITY",
            "pedagogical_focus": "Tests if the learner spots undefined financial targets.",
        },
        "MISSING_INVALIDATION": {
            "template": "{company} stock will reach {target} by mid-2026 as cloud contract pipeline doubles.",
            "default_target": "$220",
            "flaw": "Specific target and timeframe provided, but completely lacks downside stop or invalidation threshold.",
            "rubric_focus": [
                "Claim specificity: Identify absence of entry conditions or exit thresholds.",
                "Risk awareness: Point out lack of downside risk or falsification boundary.",
            ],
            "property_name": "INVALIDATION_ABSENCE",
            "pedagogical_focus": "Tests if the learner checks for testable falsification conditions.",
        },
        "HYPERBOLIC_CERTAINTY": {
            "template": "{company} is a guaranteed multi-bagger breakout before year-end. Buy before it's too late!",
            "default_target": "multi-bagger",
            "flaw": "Hyperbolic language ('guaranteed', 'buy before it's too late') with zero risk caveats.",
            "rubric_focus": [
                "Risk awareness: Flag persuasion and urgency indicators as review prompts.",
                "Confidence calibration: Express appropriately low confidence due to absence of verifiable data.",
            ],
            "property_name": "PERSUASION_AND_RISK",
            "pedagogical_focus": "Tests if the learner resists artificial urgency and absolute guarantees.",
        },
        "FO_STYLE_CLAIM": {
            "template": "{company} monthly 180 CE will surge 40% before Thursday expiry on heavy rollover volumes.",
            "default_target": "+40%",
            "flaw": "Derivative claim with strike and expiry, but no delta/theta decay risk or stop-loss level stated.",
            "rubric_focus": [
                "Claim specificity: Verify option strike and expiry date boundaries.",
                "Risk awareness: Identify extreme time-decay risk in expiring options.",
            ],
            "property_name": "DERIVATIVE_STRUCTURE",
            "pedagogical_focus": "Tests evaluation of F&O derivative claims and time-decay risks.",
        },
        "WELL_FORMED_CONTROL": {
            "template": "{company} is targeted at {target} by Dec 31, 2026; thesis is invalidated if operating margin drops below 18% in Q2.",
            "default_target": "$150",
            "flaw": "None (well-formed falsifiable thesis for baseline discrimination).",
            "rubric_focus": [
                "Claim specificity: Recognise that concrete invalidation boundary and explicit dates are present.",
                "Evidence evaluation: Check Q2 operating margin disclosure.",
            ],
            "property_name": "FALSIFIABILITY_COMPLETENESS",
            "pedagogical_focus": "Tests if the learner can identify a genuinely testable claim.",
        },
    }

    def generate_practice_claim(
        self,
        claim: Optional[ExtractedClaim] = None,
        template_category: Optional[str] = None,
    ) -> CounterfactualGenerationResult:
        """Generate a structurally comparable synthetic practice claim.

        Args:
            claim: Optional ExtractedClaim to derive structural characteristics from.
            template_category: Explicit category key if overriding claim analysis.

        Returns:
            CounterfactualGenerationResult with user-facing claim and internal rubric metadata.

        Raises:
            CounterfactualGenerationError: If input is invalid or generation cannot be completed.
        """
        try:
            # Determine which structural flaw to preserve
            chosen_key = "MISSING_INVALIDATION"
            orig_state_desc = "Unspecified"

            if template_category:
                if template_category not in self.CONTROLLED_TEMPLATES:
                    raise CounterfactualGenerationError(
                        f"Unknown template category '{template_category}'. "
                        f"Available: {list(self.CONTROLLED_TEMPLATES.keys())}"
                    )
                chosen_key = template_category
                orig_state_desc = f"Directly requested: {template_category}"

            elif claim is not None:
                # Analyze structural properties of the source claim
                has_target = bool(claim.target_metric)
                has_horizon = bool(claim.time_horizon)
                has_invalidation = bool(claim.invalidation_criteria and len(claim.invalidation_criteria) > 0)
                is_hyperbolic = getattr(claim, "confidence_language", None) and claim.confidence_language.value == "HYPERBOLIC"

                if is_hyperbolic:
                    chosen_key = "HYPERBOLIC_CERTAINTY"
                    orig_state_desc = "Original used hyperbolic certainty language."
                elif has_target and not has_horizon:
                    chosen_key = "VAGUE_TIMEFRAME"
                    orig_state_desc = "Original had target metric but omitted concrete timeframe."
                elif has_horizon and not has_target:
                    chosen_key = "VAGUE_METRIC"
                    orig_state_desc = "Original had timeframe but lacked explicit quantifiable benchmark."
                elif not has_invalidation:
                    chosen_key = "MISSING_INVALIDATION"
                    orig_state_desc = "Original lacked concrete falsification boundary."
                else:
                    chosen_key = "WELL_FORMED_CONTROL"
                    orig_state_desc = "Original was reasonably well-formed with invalidation criteria."

            template_info = self.CONTROLLED_TEMPLATES[chosen_key]

            # Select synthetic company deterministically based on claim id or fixed offset
            seed_idx = abs(hash(claim.claim_id if claim else chosen_key)) % len(self.SYNTHETIC_COMPANIES)
            company_name = self.SYNTHETIC_COMPANIES[seed_idx]

            # Format clean claim text (NO ANSWERS, NO HINTS)
            claim_text = template_info["template"].format(
                company=company_name,
                target=template_info["default_target"],
            )

            practice_claim = PracticeClaim(
                claim_text=claim_text,
                synthetic_company_name=company_name,
            )

            preserved_prop = PreservedLearningProperty(
                property_name=template_info["property_name"],
                original_state=orig_state_desc,
                practice_state=template_info["flaw"],
                pedagogical_focus=template_info["pedagogical_focus"],
            )

            return CounterfactualGenerationResult(
                practice_claim=practice_claim,
                source_claim_id=claim.claim_id if claim else None,
                preserved_properties=[preserved_prop],
                evaluation_rubric_focus=template_info["rubric_focus"],
                generation_method="CONTROLLED_TEMPLATE_SYNTHESIS",
                metadata={
                    "template_category": chosen_key,
                    "target_metric": template_info["default_target"],
                    "synthetic_entity": company_name,
                    "preserves_learning_challenge": True,
                },
            )

        except CounterfactualGenerationError:
            raise
        except Exception as e:
            raise CounterfactualGenerationError(
                f"Failed to safely synthesize counterfactual practice claim: {str(e)}",
                details={"error": str(e)},
            ) from e
