"""Data contracts for Independent Assessment Evaluation Support.

CRITICAL INVARIANTS:
1. Evaluates reasoning quality across the five FinTrace assessment dimensions.
2. The backend owns assessment session persistence and composite score tracking;
   this AI engine module provides transparent, explainable evaluation support.
3. Scoring anchors are transparent and deterministic; LLM evaluations are never
   presented as unverified objective ground truth.
4. Distinguishes unmentioned issues from incorrect statements.
5. Does NOT penalize a user merely because their conclusion differs from an AI hypothesis.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from claim_extraction.schemas import EvidenceItem, ExtractedClaim
from interpretation.schemas import InterpretationFork


class AssessmentDimensionEnum(str, Enum):
    """The five pedagogical assessment dimensions defined by the FinTrace rubric."""
    EVIDENCE_EVALUATION = "EVIDENCE_EVALUATION"
    CLAIM_SPECIFICITY = "CLAIM_SPECIFICITY"
    RISK_AWARENESS = "RISK_AWARENESS"
    ASSUMPTION_AWARENESS = "ASSUMPTION_AWARENESS"
    CONFIDENCE_CALIBRATION = "CONFIDENCE_CALIBRATION"


class DimensionEvaluationResult(BaseModel):
    """Evaluation result for a single pedagogical dimension."""
    dimension: AssessmentDimensionEnum = Field(
        ...,
        description="The evaluated FinTrace assessment dimension."
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=20.0,
        description="Suggested score for this dimension on a 0.0 to 20.0 anchor scale."
    )
    max_score: float = Field(
        default=20.0,
        description="Maximum possible score for this dimension (5 dimensions sum to 100)."
    )
    scoring_anchor: str = Field(
        ...,
        description="Predefined scoring anchor justifying the awarded score (e.g. 'Good: 15/20')."
    )
    correctly_identified_issues: List[str] = Field(
        default_factory=list,
        description="Flaws, criteria, or evidence items the user correctly pointed out."
    )
    omitted_or_unmentioned_issues: List[str] = Field(
        default_factory=list,
        description="Relevant structural flaws or evidence gaps the user omitted."
    )
    feedback: str = Field(
        ...,
        description="Constructive, evidence-grounded feedback explaining how to improve."
    )


class UserAssessmentInput(BaseModel):
    """Input payload representing an investor's independent evaluation of a claim."""
    claim: ExtractedClaim = Field(
        ...,
        description="The practice or evaluation claim being critiqued."
    )
    user_critique_text: str = Field(
        ...,
        description="The user's actual written critique and rationale."
    )
    user_confidence: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="User's expressed confidence level on a 1.0 to 5.0 scale."
    )
    user_identified_evidence: Optional[List[str]] = Field(
        default=None,
        description="Optional evidence sources or keywords cited by the user."
    )
    available_forks: Optional[List[InterpretationFork]] = Field(
        default=None,
        description="Optional interpretation forks available for ground-truth comparison."
    )
    available_evidence: Optional[List[EvidenceItem]] = Field(
        default=None,
        description="Optional evidence items available for ground-truth comparison."
    )


class AssessmentEvaluationOutput(BaseModel):
    """Comprehensive structured output evaluating the user's independent claim critique."""
    evaluation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this assessment evaluation."
    )
    dimension_evaluations: Dict[AssessmentDimensionEnum, DimensionEvaluationResult] = Field(
        ...,
        description="Breakdown of evaluations across the five rubric dimensions."
    )
    total_suggested_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Total suggested composite Decision Evaluation Score (0 to 100)."
    )
    overall_feedback: str = Field(
        ...,
        description="High-level pedagogical summary of the user's evaluation strengths and growth areas."
    )
    provenance_label: str = Field(
        default="Rule-Based Assessment Evaluation (Rubric Recommendation)",
        frozen=True,
        description="Immutable label ensuring consumers recognize this as a deterministic assessment support tool."
    )
    advisory_note: str = Field(
        default=(
            "Dimension scores and feedback are transparent rubric recommendations for backend analytics. "
            "Evaluations measure reasoning quality under uncertainty, not market trading predictions."
        ),
        frozen=True,
        description="Mandatory disclaimer outlining assessment boundaries."
    )
