"""Public integration interface contract for the future FinTraceAIEngine facade.

This module establishes the high-level boundary consumed by the backend layer
(Jos) without leaking provider-specific details, prompt templates, or orchestration
mechanics.

CRITICAL INVARIANTS:
1. Missing claim parameters must remain None.
2. Two-model agreement must NEVER be represented as factual verification.
3. Retrieved evidence and AI interpretation remain strictly separated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field

from claim_extraction.schemas import (
    EvidenceItem,
    ExtractedClaim,
    RiskIndicator,
    RiskIndicatorType,
)
from interpretation.schemas import ForkAnalysisResult, InterpretationFork
from orchestration.schemas import DualModelReviewInput, DualModelReviewOutput
from validation.schemas import ValidationResult
from interpretation.counterfactual import (
    CounterfactualGenerationResult,
    PracticeClaim,
    PreservedLearningProperty,
)
from interpretation.sensitivity import (
    DecisionRecord,
    DecisionSensitivityExplanation,
    DecisionSensitivityInput,
)
from assessment.schemas import (
    AssessmentDimensionEnum,
    AssessmentEvaluationOutput,
    DimensionEvaluationResult,
    UserAssessmentInput,
)


class ClaimExtractionInput(BaseModel):
    """Input payload submitted to the AI Engine for claim extraction."""
    raw_text: str = Field(
        ...,
        min_length=5,
        description="Raw financial statement, commentary, or analyst note to process."
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Optional canonical reference or URL where text was retrieved."
    )
    author: Optional[str] = Field(
        default=None,
        description="Optional identity or handle of statement author."
    )
    published_at: Optional[datetime] = Field(
        default=None,
        description="Optional timestamp when statement was published."
    )
    retrieved_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Optional grounding evidence retrieved by backend evidence layer."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional non-speculative caller metadata."
    )


class ForkAnalysisInput(BaseModel):
    """Input payload to evaluate an extracted claim for interpretation forks."""
    claim: ExtractedClaim = Field(
        ...,
        description="The extracted claim to be evaluated for ambiguity."
    )
    max_forks: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of alternative interpretations to generate."
    )


class FullPipelineAnalysisResult(BaseModel):
    """Complete, end-to-end output of the FinTrace AI pipeline."""
    claim: ExtractedClaim
    validation: ValidationResult
    fork_analysis: ForkAnalysisResult
    dual_model_review: Optional[DualModelReviewOutput] = None
    pipeline_duration_ms: float = Field(ge=0.0)
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Preserved execution & fallback telemetry (Audit Item H-3)
    primary_provider: str = Field(
        default="unknown",
        description="Actual provider that fulfilled primary extraction (e.g. 'groq', 'gemini')."
    )
    primary_model: str = Field(
        default="unknown",
        description="Actual model identifier used for extraction."
    )
    fallback_used: bool = Field(
        default=False,
        description="True if primary provider failed and request failed over to fallback."
    )
    is_degraded: bool = Field(
        default=False,
        description="True if pipeline executed in degraded mode (failover, reviewer outage, or same-provider review)."
    )
    primary_failure_reason: Optional[str] = Field(
        default=None,
        description="Reason for primary failure if failover occurred."
    )
    telemetry: Dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic telemetry from providers, circuit breakers, and sub-engines."
    )


class FinTraceAIEngineProtocol(Protocol):
    """Public protocol defining the exact methods exposed by the FinTraceAIEngine."""

    async def extract_and_compile(
        self, input_data: ClaimExtractionInput
    ) -> ExtractedClaim:
        """Extract a structured claim and compile falsifiability criteria."""
        ...

    async def analyze_forks(
        self, input_data: ForkAnalysisInput
    ) -> ForkAnalysisResult:
        """Detect ambiguities and synthesize alternative interpretation forks."""
        ...

    async def review_dual_model(
        self, input_data: DualModelReviewInput
    ) -> DualModelReviewOutput:
        """Execute independent reviewer model critique over primary claim."""
        ...

    async def validate_claim(
        self,
        claim: ExtractedClaim,
        raw_text: Optional[str] = None,
        published_at: Optional[datetime] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> ValidationResult:
        """Run deterministic non-LLM validation over an extracted claim."""
        ...

    async def analyze_end_to_end(
        self, input_data: ClaimExtractionInput
    ) -> FullPipelineAnalysisResult:
        """Execute the complete end-to-end AI pipeline in one coordinated call."""
        ...

    def get_health_status(self) -> Dict[str, Any]:
        """Telemetry snapshot of engine subsystems and underlying circuit breakers."""
        ...

    def generate_practice_claim(
        self,
        claim: Optional[ExtractedClaim] = None,
        template_category: Optional[str] = None,
    ) -> CounterfactualGenerationResult:
        """Generate a structurally comparable synthetic practice claim for independent learning."""
        ...

    def explain_sensitivity(
        self, input_data: DecisionSensitivityInput
    ) -> DecisionSensitivityExplanation:
        """Construct an explainable comparison of investor reasoning shifts."""
        ...

    def evaluate_assessment(
        self, input_data: UserAssessmentInput
    ) -> AssessmentEvaluationOutput:
        """Evaluate an investor's independent written claim critique across the 5 FinTrace dimensions."""
        ...
