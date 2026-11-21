"""Decision Sensitivity Explanation Engine.

CRITICAL INVARIANTS:
1. Explains only changes supported by supplied inputs; NEVER invents investor motivations.
2. Allocation sensitivity is purely descriptive; a smaller allocation is NOT automatically better or smarter.
3. Allocation reduction is NEVER classified as 'success' or 'improvement'.
4. Distinguishes observed textual correlation from demonstrated psychological causation.
5. If allocation or confidence changes without an explanation, explicitly states the reason is not established.
6. Clearly labels all outputs as AI-generated hypotheses.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from interpretation.schemas import InterpretationFork
from validation.errors import SensitivityAnalysisError


class DecisionRecord(BaseModel):
    """User decision record capturing confidence, hypothetical allocation, and rationale."""
    confidence_level: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="Investor confidence rating on a 1.0 to 5.0 scale."
    )
    hypothetical_allocation_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Hypothetical virtual allocation percentage (0.0 to 100.0%)."
    )
    written_rationale: Optional[str] = Field(
        default=None,
        description="User's stated reasoning at this decision point."
    )


class DecisionSensitivityInput(BaseModel):
    """Input payload to evaluate changes in decision reasoning."""
    initial_decision: DecisionRecord = Field(
        ...,
        description="Baseline decision recorded prior to reviewing AI analysis or evidence."
    )
    revised_decision: DecisionRecord = Field(
        ...,
        description="Revised decision recorded after reviewing report, forks, or evidence."
    )
    selected_interpretation_forks: List[InterpretationFork] = Field(
        default_factory=list,
        description="Interpretation forks reviewed or selected by the user."
    )
    relevant_evidence_observations: List[str] = Field(
        default_factory=list,
        description="Dated evidence points or disclosures presented to the user."
    )
    claim_summary: Optional[str] = Field(
        default=None,
        description="Summary of the underlying financial claim being assessed."
    )


class DecisionSensitivityExplanation(BaseModel):
    """Structured explanation of how an investor's reasoning shifted across decision points."""
    explanation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this sensitivity explanation."
    )
    summary_of_change: str = Field(
        ...,
        description="Factual synthesis of the change in reasoning."
    )
    confidence_delta: float = Field(
        ...,
        description="Numerical change in confidence rating (revised - initial)."
    )
    confidence_shift_description: str = Field(
        ...,
        description="Neutral textual description of confidence shift."
    )
    allocation_delta_pct: float = Field(
        ...,
        description="Change in hypothetical allocation percentage points (revised - initial)."
    )
    allocation_shift_description: str = Field(
        ...,
        description="Neutral textual description of allocation shift."
    )
    associated_assumptions_or_forks: List[str] = Field(
        default_factory=list,
        description="Interpretation forks or assumptions correlated with the user's revised thesis."
    )
    influential_evidence_observations: List[str] = Field(
        default_factory=list,
        description="Specific evidence observations cited or aligned with the revised rationale."
    )
    uncertainties_and_limitations: List[str] = Field(
        default_factory=list,
        description="Caveats distinguishing correlation from causation and noting data boundaries."
    )
    unexplained_variance_flag: bool = Field(
        default=False,
        description="True if allocation or confidence changed without a supporting written rationale."
    )
    initial_rationale_preserved: Optional[str] = Field(
        default=None,
        description="Verbatim initial rationale preserved without modification."
    )
    revised_rationale_preserved: Optional[str] = Field(
        default=None,
        description="Verbatim revised rationale preserved without modification."
    )
    provenance_label: str = Field(
        default="Deterministic Decision Sensitivity Analysis",
        frozen=True,
        description="Immutable label ensuring consumers recognize this as a deterministic analytical synthesis."
    )
    behavioral_disclaimer: str = Field(
        default=(
            "Allocation sensitivity is descriptive behavioral data, not an investment quality score. "
            "A smaller allocation is not inherently safer or better."
        ),
        frozen=True,
        description="Mandatory disclaimer preventing normative interpretation of allocation sizing."
    )


class DecisionSensitivityEngine:
    """Engine synthesizing explainable comparisons between pre- and post-analysis investor decisions."""

    def explain_sensitivity(
        self,
        input_data: DecisionSensitivityInput,
    ) -> DecisionSensitivityExplanation:
        """Construct an explainable, evidence-grounded sensitivity comparison.

        Args:
            input_data: DecisionSensitivityInput containing initial/revised records and context.

        Returns:
            DecisionSensitivityExplanation structured response.

        Raises:
            SensitivityAnalysisError: If input data is malformed or invalid.
        """
        try:
            init = input_data.initial_decision
            rev = input_data.revised_decision

            conf_delta = round(rev.confidence_level - init.confidence_level, 2)
            alloc_delta = round(rev.hypothetical_allocation_pct - init.hypothetical_allocation_pct, 2)

            # 1. Describe confidence delta neutrally
            if conf_delta > 0:
                conf_desc = f"Confidence increased by {conf_delta:.1f} points (from {init.confidence_level:.1f} to {rev.confidence_level:.1f} on a 1-5 scale)."
            elif conf_delta < 0:
                conf_desc = f"Confidence decreased by {abs(conf_delta):.1f} points (from {init.confidence_level:.1f} to {rev.confidence_level:.1f} on a 1-5 scale)."
            else:
                conf_desc = f"Confidence remained unchanged at {init.confidence_level:.1f} out of 5."

            # 2. Describe allocation delta neutrally
            if alloc_delta > 0:
                alloc_desc = f"Hypothetical allocation increased by {alloc_delta:.1f} percentage points ({init.hypothetical_allocation_pct:.1f}% -> {rev.hypothetical_allocation_pct:.1f}%)."
            elif alloc_delta < 0:
                alloc_desc = f"Hypothetical allocation decreased by {abs(alloc_delta):.1f} percentage points ({init.hypothetical_allocation_pct:.1f}% -> {rev.hypothetical_allocation_pct:.1f}%)."
            else:
                alloc_desc = f"Hypothetical allocation remained unchanged at {init.hypothetical_allocation_pct:.1f}%."

            # 3. Check for unexplained variance (decision changed but no rationale provided)
            init_rat = (init.written_rationale or "").strip()
            rev_rat = (rev.written_rationale or "").strip()
            decision_shifted = (conf_delta != 0 or alloc_delta != 0)
            unexplained_variance = False
            associated_forks: List[str] = []
            influential_evidence: List[str] = []
            limitations: List[str] = [
                "Observed alignments reflect textual thematic correlations, not verified cognitive causation.",
                "Allocation sensitivity is descriptive; an allocation reduction does not constitute an inherently better decision.",
            ]

            if decision_shifted and not rev_rat:
                unexplained_variance = True
                summary = (
                    f"The investor altered their decision ({alloc_desc}; {conf_desc}), but provided no revised "
                    f"written rationale. The specific underlying reason for this shift is not established."
                )
                limitations.append("No revised written explanation was provided to substantiate the shift in allocation or confidence.")

            elif not decision_shifted:
                summary = (
                    f"The investor's decision remained completely unchanged across both evaluation points "
                    f"({init.hypothetical_allocation_pct:.1f}% allocation at {init.confidence_level:.1f}/5 confidence)."
                )
                if rev_rat and rev_rat.lower() != init_rat.lower():
                    summary += f" However, the written rationale was expanded: \"{rev_rat}\"."

            else:
                # Both decisions exist and revised rationale is present
                summary_parts = [
                    f"The investor modified their position ({alloc_desc}; {conf_desc})."
                ]

                # Match words in revised rationale against interpretation forks
                rev_lower = rev_rat.lower()
                for fork in input_data.selected_interpretation_forks:
                    fork_tokens = re.findall(r"\b\w{4,}\b", fork.fork_title.lower())
                    matches = [tok for tok in fork_tokens if tok in rev_lower]
                    if matches:
                        associated_forks.append(
                            f"Fork '{fork.fork_title}' (correlated terms in rationale: {', '.join(matches)})"
                        )

                # Match against evidence observations
                for ev in input_data.relevant_evidence_observations:
                    ev_tokens = re.findall(r"\b\w{4,}\b", ev.lower())
                    matches = [tok for tok in ev_tokens if tok in rev_lower]
                    if len(matches) >= 2:
                        influential_evidence.append(
                            f"Evidence disclosure: \"{ev[:80]}...\" (matched keywords: {', '.join(matches[:3])})"
                        )

                if associated_forks:
                    summary_parts.append(
                        f"The revised rationale correlates with {len(associated_forks)} specific interpretation scenario(s)."
                    )
                if influential_evidence:
                    summary_parts.append(
                        f"The rationale explicitly references details present in external evidence disclosures."
                    )
                if not associated_forks and not influential_evidence:
                    summary_parts.append(
                        "The revised rationale provides self-directed reasoning without directly citing the provided interpretation forks or evidence excerpts."
                    )

                summary = " ".join(summary_parts)

            return DecisionSensitivityExplanation(
                summary_of_change=summary,
                confidence_delta=conf_delta,
                confidence_shift_description=conf_desc,
                allocation_delta_pct=alloc_delta,
                allocation_shift_description=alloc_desc,
                associated_assumptions_or_forks=associated_forks,
                influential_evidence_observations=influential_evidence,
                uncertainties_and_limitations=limitations,
                unexplained_variance_flag=unexplained_variance,
                initial_rationale_preserved=init.written_rationale,
                revised_rationale_preserved=rev.written_rationale,
            )

        except Exception as e:
            raise SensitivityAnalysisError(
                f"Failed to generate decision sensitivity explanation: {str(e)}",
                details={"error": str(e)},
            ) from e
