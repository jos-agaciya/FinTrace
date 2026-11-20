"""Data contracts for the Interpretation Fork Engine.

CRITICAL INVARIANTS:
1. All generated interpretations MUST be explicitly labelled as AI-generated hypotheses,
   never confused with confirmed author intent.
2. Identifies required distinguishing data needed to falsify or validate each fork.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from claim_extraction.schemas import DirectionEnum


class InterpretationFork(BaseModel):
    """An alternative plausible reading of an ambiguous financial thesis.

    CRITICAL: Labelled as an AI-generated hypothesis to distinguish from author intent.
    """
    fork_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique UUID for this interpretation fork."
    )
    fork_title: str = Field(
        ...,
        description="Concise scenario title (e.g. 'Automotive Gross Margin Recovery Ex-Regulatory Credits')."
    )
    scenario_description: str = Field(
        ...,
        description="Detailed description of what this interpretation entails."
    )
    plausibility_weight: float = Field(
        ge=0.0,
        le=1.0,
        description="Relative plausibility weight among discovered forks (summing to <= 1.0)."
    )
    implied_direction: DirectionEnum = Field(
        ...,
        description="Direction implied under this specific interpretation."
    )
    key_assumptions: List[str] = Field(
        default_factory=list,
        description="Underlying premises necessary for this fork to hold."
    )
    distinguishing_evidence_needed: str = Field(
        ...,
        description="Exact observable event, metric, or disclosure needed to distinguish this fork."
    )
    provenance_label: str = Field(
        default="AI-Generated Interpretation (Hypothesis)",
        frozen=True,
        description="Immutable label ensuring consumers do not treat this as author intent."
    )


class ForkAnalysisResult(BaseModel):
    """Collection of interpretation forks and ambiguity diagnostics for a claim."""
    claim_id: str = Field(
        ...,
        description="Reference to the underlying ExtractedClaim."
    )
    ambiguity_detected: bool = Field(
        ...,
        description="True if linguistic or numeric ambiguity exists in the statement."
    )
    ambiguity_reasons: List[str] = Field(
        default_factory=list,
        description="List of detected ambiguous terms, unanchored percentages, or vague horizons."
    )
    forks: List[InterpretationFork] = Field(
        default_factory=list,
        description="Plausible alternative readings."
    )
    distinguishing_data_checklist: List[str] = Field(
        default_factory=list,
        description="Checklist of future metrics or data points to monitor."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution telemetry and provider provenance metadata."
    )
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of fork analysis."
    )

    @model_validator(mode="after")
    def validate_or_normalize_plausibility_weights(self) -> "ForkAnalysisResult":
        """Ensures that the sum of plausibility weights across all forks <= 1.0 (Audit Item H-2)."""
        if not self.forks:
            return self
        total_weight = sum(f.plausibility_weight for f in self.forks)
        if total_weight > 1.0 + 1e-6:
            normalized_forks = []
            for f in self.forks:
                norm_weight = round(f.plausibility_weight / total_weight, 4)
                normalized_forks.append(
                    f.model_copy(update={"plausibility_weight": norm_weight})
                )
            self.forks = normalized_forks
        return self
