"""Structured contracts for deterministic validation and evidence grounding."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity of a detected validation issue."""
    ERROR = "ERROR"          # Invalidation or corruption: claim cannot be trusted
    WARNING = "WARNING"      # Potential anomaly or ambiguity requiring review
    INFO = "INFO"            # Informational observation (e.g. unstated optional field)


class GroundingStatus(str, Enum):
    """Factual relationship between a claim and retrieved evidence.

    CRITICAL: An unsupported statement must NEVER be automatically assumed false.
    Clear distinction between CONTRADICTED and INSUFFICIENT_EVIDENCE is mandatory.
    """
    SUPPORTED = "SUPPORTED"                          # Verifiable evidence directly corroborates claim
    CONTRADICTED = "CONTRADICTED"                    # Verifiable evidence directly contradicts claim
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"  # Evidence exists but lacks necessary specificity
    UNVERIFIED = "UNVERIFIED"                        # No relevant evidence was provided for grounding


class ValidationIssue(BaseModel):
    """Specific diagnostic issue discovered by deterministic validation."""
    issue_code: str = Field(
        ...,
        description="Machine-readable error/warning code (e.g. 'CHRONOLOGY_INVERSION', 'HALLUCINATED_NUMERIC')."
    )
    severity: ValidationSeverity = Field(
        ...,
        description="Severity classification."
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the validation defect."
    )
    field_name: Optional[str] = Field(
        default=None,
        description="Attribute name where the defect was found, or None if global."
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Non-speculative contextual values."
    )


class GroundingCheckResult(BaseModel):
    """Detailed result of checking a specific claim assertion against an evidence item."""
    claim_id: str
    evidence_id: str
    source_name: str
    status: GroundingStatus
    rationale: str
    matched_facts: List[str] = Field(default_factory=list)
    contradicted_facts: List[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Aggregated output of deterministic validation."""
    claim_id: str
    is_valid: bool = Field(
        ...,
        description="True if no ERROR severity issues were identified."
    )
    validation_status: str = Field(
        ...,
        description="'PASSED', 'PASSED_WITH_WARNINGS', or 'FAILED'."
    )
    null_preservation_verified: bool = Field(
        ...,
        description="True if unstated attributes strictly remained None."
    )
    chronology_verified: bool = Field(
        ...,
        description="True if time horizon does not precede publication date."
    )
    numeric_bounds_verified: bool = Field(
        ...,
        description="True if all numeric figures adhere to plausibility bounds."
    )
    issues: List[ValidationIssue] = Field(default_factory=list)
    grounding_checks: List[GroundingCheckResult] = Field(default_factory=list)
    validated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when deterministic validation was performed."
    )
