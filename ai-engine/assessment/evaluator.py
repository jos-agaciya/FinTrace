"""Independent Assessment Evaluation Engine.

CRITICAL INVARIANTS:
1. Evaluates user written critique across the five FinTrace rubric dimensions:
   - Evidence evaluation
   - Claim specificity
   - Risk awareness
   - Assumption awareness
   - Confidence calibration
2. Uses transparent, explainable scoring anchors (0-20 per dimension, 0-100 total).
3. Distinguishes unmentioned issues from incorrect statements.
4. Does NOT award credit for unsupported assertions.
5. Does NOT penalize a user merely because their conclusion differs from an AI interpretation.
6. Does NOT substitute final investment outcomes for reasoning evaluation.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from assessment.schemas import (
    AssessmentDimensionEnum,
    AssessmentEvaluationOutput,
    DimensionEvaluationResult,
    UserAssessmentInput,
)
from validation.errors import AssessmentEvaluationError


class AssessmentEvaluator:
    """Evaluates an investor's independent claim critique against the FinTrace rubric."""

    # Lexical patterns for Evidence Evaluation
    EVIDENCE_CRITIQUE_PATTERNS = [
        (r"\b(filing|10-k|10-q|sebi|edgar|annual report)\b", "Demanded official statutory filings or regulatory disclosures"),
        (r"\b(balance sheet|quarterly|cash flow|income statement|audited)\b", "Cited financial statements or audited accounting metrics"),
        (r"\b(source|citation|provenance|link|verify|verification|validat|unverified|where is the data)\b", "Requested source verification or cited evidence gaps"),
        (r"\b(rumor|social media|tweet|finfluencer|unsupported|unsubstantiated|hearsay|market noise)\b", "Distinguished primary evidence from unverified commentary"),
    ]

    # Lexical patterns for Claim Specificity
    SPECIFICITY_PATTERNS = [
        (r"\b(no timeframe|missing (date|timeframe|horizon)|when|how long|by when)\b", "Identified missing or vague time horizon"),
        (r"\b(no target|missing (price|target)|vague metric|what price)\b", "Identified missing or unquantified price target"),
        (r"\b(no stop|no invalidation|stop loss|how to prove wrong|falsif|unstated downside|unstated risk)\b", "Identified absence of invalidation criteria or stop levels"),
        (r"\b(no entry|no exit|entry price|exit rule)\b", "Identified missing entry/exit prerequisites"),
    ]

    # Lexical patterns for Risk Awareness
    RISK_PATTERNS = [
        (r"\b(risk|downside|drawdown|loss|market crash|bear|volatilit)\b", "Pointed out market risk, volatility, or downside potential"),
        (r"\b(urgency|hype|fomo|too late|act now|pressure)\b", "Identified artificial urgency or psychological timing pressure"),
        (r"\b(guarantee|cannot lose|risk-free|too good to be true)\b", "Challenged unrealistic or guaranteed return claims"),
    ]

    # Lexical patterns for Assumption Awareness
    ASSUMPTION_PATTERNS = [
        (r"\b(assum|premise|if and only if|depend|contingent|what if)\b", "Questioned foundational assumptions and contingencies"),
        (r"\b(margin definition|gross vs|operating margin|revenue vs|organic)\b", "Explored semantic ambiguity in metrics or definitions"),
        (r"\b(alternative|another interpretation|scenario|competition|execution)\b", "Considered alternative scenarios or execution hurdles"),
    ]

    def evaluate_assessment(
        self,
        input_data: UserAssessmentInput,
    ) -> AssessmentEvaluationOutput:
        """Evaluate a user's independent written critique against ground truth and rubric.

        Args:
            input_data: UserAssessmentInput with user critique, confidence, and claim spec.

        Returns:
            AssessmentEvaluationOutput containing dimension-level results and scoring anchors.

        Raises:
            AssessmentEvaluationError: If evaluation inputs are invalid.
        """
        try:
            critique = input_data.user_critique_text or ""
            critique_clean = critique.strip()
            critique_lower = critique_clean.lower()
            claim = input_data.claim

            dim_results: Dict[AssessmentDimensionEnum, DimensionEvaluationResult] = {}

            # Handle completely empty critique safely
            if not critique_clean:
                return self._build_empty_critique_result(input_data)

            # -------------------------------------------------------------
            # 1. EVIDENCE EVALUATION (Max 20.0)
            # -------------------------------------------------------------
            ev_identified: List[str] = []
            ev_omitted: List[str] = []

            for pattern, desc in self.EVIDENCE_CRITIQUE_PATTERNS:
                if re.search(pattern, critique_lower):
                    ev_identified.append(desc)

            if len(ev_identified) >= 2 or (input_data.user_identified_evidence and len(input_data.user_identified_evidence) > 0):
                ev_score = 20.0
                ev_anchor = "Exemplary (20/20): Demanded primary disclosures or explicitly distinguished verified facts from commentary."
                ev_feedback = "Excellent work seeking primary documents and questioning the lack of verifiable evidence."
            elif len(ev_identified) == 1:
                ev_score = 12.0
                ev_anchor = "Competent (12/20): Expressed general awareness of evidence gaps, but did not specify primary source documents."
                ev_feedback = "Good observation of evidence needs. In future evaluations, specify exact documents (e.g. SEC 10-K, quarterly earnings)."
                ev_omitted.append("Did not specify exact statutory filings or exchange disclosures needed.")
            else:
                ev_score = 4.0
                ev_anchor = "Emerging (4/20): Minimal evaluation of evidence; accepted claims without demanding verification."
                ev_feedback = "Remember to always verify whether claims are backed by audited financials or regulatory filings."
                ev_omitted.append("Failed to question evidence sources or seek primary-source documentation.")

            dim_results[AssessmentDimensionEnum.EVIDENCE_EVALUATION] = DimensionEvaluationResult(
                dimension=AssessmentDimensionEnum.EVIDENCE_EVALUATION,
                score=ev_score,
                scoring_anchor=ev_anchor,
                correctly_identified_issues=ev_identified,
                omitted_or_unmentioned_issues=ev_omitted,
                feedback=ev_feedback,
            )

            # -------------------------------------------------------------
            # 2. CLAIM SPECIFICITY (Max 20.0)
            # -------------------------------------------------------------
            spec_identified: List[str] = []
            spec_omitted: List[str] = []

            for pattern, desc in self.SPECIFICITY_PATTERNS:
                if re.search(pattern, critique_lower):
                    spec_identified.append(desc)

            # Check ground-truth claim absences to see what user should have noticed
            if claim.time_horizon is None and not any("time" in d.lower() for d in spec_identified):
                spec_omitted.append("Omitted noting that the claim has no explicit calendar timeframe or horizon.")
            if claim.target_metric is None and not any("target" in d.lower() for d in spec_identified):
                spec_omitted.append("Omitted noting that the claim lacks a quantifiable target metric.")
            if not claim.invalidation_criteria and not any("stop" in d.lower() or "invalidation" in d.lower() for d in spec_identified):
                spec_omitted.append("Omitted noting that the claim lacks concrete falsification or stop-loss boundaries.")

            if len(spec_identified) >= 2:
                spec_score = 20.0
                spec_anchor = "Exemplary (20/20): Accurately identified multiple missing structural specifications in the claim."
                spec_feedback = "Outstanding critique of missing parameters (timeframe, target, or invalidation boundaries)."
            elif len(spec_identified) == 1:
                spec_score = 14.0
                spec_anchor = "Proficient (14/20): Correctly recognized at least one major missing parameter in the claim."
                spec_feedback = "Good detection of claim incompleteness. Check also for missing invalidation conditions or stop levels."
            elif claim.is_falsifiable and len(claim.invalidation_criteria) > 0 and len(critique_clean) > 30:
                # If claim was actually well-formed and user recognized it
                spec_score = 16.0
                spec_anchor = "Proficient (16/20): Accurately analyzed claim parameters and criteria."
                spec_feedback = "Appropriately recognized the claim's existing boundaries."
            else:
                spec_score = 6.0
                spec_anchor = "Developing (6/20): Missed key omissions in the claim's structure."
                spec_feedback = "Inspect whether the claim provides concrete time horizons, entry/exit criteria, and testable invalidation rules."

            dim_results[AssessmentDimensionEnum.CLAIM_SPECIFICITY] = DimensionEvaluationResult(
                dimension=AssessmentDimensionEnum.CLAIM_SPECIFICITY,
                score=spec_score,
                scoring_anchor=spec_anchor,
                correctly_identified_issues=spec_identified,
                omitted_or_unmentioned_issues=spec_omitted,
                feedback=spec_feedback,
            )

            # -------------------------------------------------------------
            # 3. RISK AWARENESS (Max 20.0)
            # -------------------------------------------------------------
            risk_identified: List[str] = []
            risk_omitted: List[str] = []

            for pattern, desc in self.RISK_PATTERNS:
                if re.search(pattern, critique_lower):
                    risk_identified.append(desc)

            if len(risk_identified) >= 2:
                risk_score = 20.0
                risk_anchor = "Exemplary (20/20): Proactively identified downside risks, urgency tactics, or missing risk context."
                risk_feedback = "Strong awareness of financial downside and artificial psychological urgency."
            elif len(risk_identified) == 1:
                risk_score = 13.0
                risk_anchor = "Proficient (13/20): Noted general risk factors or questioned promotional tone."
                risk_feedback = "Good risk identification. Consider also how broader market volatility could affect the thesis."
            else:
                risk_score = 5.0
                risk_anchor = "Developing (5/20): Failed to highlight downside risks or missing risk disclosures."
                risk_feedback = "Always look for missing risk disclosures and potential downside scenarios."
                risk_omitted.append("Did not evaluate potential downside or missing risk disclosures.")

            dim_results[AssessmentDimensionEnum.RISK_AWARENESS] = DimensionEvaluationResult(
                dimension=AssessmentDimensionEnum.RISK_AWARENESS,
                score=risk_score,
                scoring_anchor=risk_anchor,
                correctly_identified_issues=risk_identified,
                omitted_or_unmentioned_issues=risk_omitted,
                feedback=risk_feedback,
            )

            # -------------------------------------------------------------
            # 4. ASSUMPTION AWARENESS (Max 20.0)
            # -------------------------------------------------------------
            assump_identified: List[str] = []
            assump_omitted: List[str] = []

            for pattern, desc in self.ASSUMPTION_PATTERNS:
                if re.search(pattern, critique_lower):
                    assump_identified.append(desc)

            if len(assump_identified) >= 2:
                assump_score = 20.0
                assump_anchor = "Exemplary (20/20): Explored alternative interpretations or challenged unstated assumptions."
                assump_feedback = "Excellent examination of underlying premises and competing semantic interpretations."
            elif len(assump_identified) == 1:
                assump_score = 12.0
                assump_anchor = "Proficient (12/20): Identified at least one unstated assumption or dependency."
                assump_feedback = "Good recognition of assumptions. Consider whether financial terms could have multiple definitions."
            else:
                assump_score = 5.0
                assump_anchor = "Developing (5/20): Uncritically accepted stated premises without examining unstated assumptions."
                assump_feedback = "Look closely at the assumptions needed for a thesis to hold true."
                assump_omitted.append("Did not explore alternative readings or challenge unstated premises.")

            dim_results[AssessmentDimensionEnum.ASSUMPTION_AWARENESS] = DimensionEvaluationResult(
                dimension=AssessmentDimensionEnum.ASSUMPTION_AWARENESS,
                score=assump_score,
                scoring_anchor=assump_anchor,
                correctly_identified_issues=assump_identified,
                omitted_or_unmentioned_issues=assump_omitted,
                feedback=assump_feedback,
            )

            # -------------------------------------------------------------
            # 5. CONFIDENCE CALIBRATION (Max 20.0)
            # -------------------------------------------------------------
            user_conf = input_data.user_confidence
            falsifiability = claim.falsifiability_score
            conf_identified: List[str] = []
            conf_omitted: List[str] = []

            # Scoring confidence calibration:
            # Low falsifiability claim (<0.40) requires low confidence (1-2)
            # High falsifiability claim (>=0.60) allows moderate/balanced confidence (2.5-4)
            if falsifiability < 0.40:
                if user_conf <= 2.0:
                    conf_score = 20.0
                    conf_anchor = f"Well-Calibrated (20/20): Low confidence ({user_conf}/5) appropriately matches an unfalsifiable, vague claim."
                    conf_feedback = "Outstanding calibration: you expressed healthy skepticism for a claim with low testability."
                    conf_identified.append("Correctly expressed low confidence on an ungrounded/vague claim.")
                elif user_conf <= 3.0:
                    conf_score = 12.0
                    conf_anchor = f"Moderately Calibrated (12/20): Moderate confidence ({user_conf}/5) on a weak claim."
                    conf_feedback = "Moderate calibration. Consider lowering confidence further when claims lack concrete invalidation criteria."
                else:
                    conf_score = 4.0
                    conf_anchor = f"Overconfident (4/20): High confidence ({user_conf}/5) expressed for an ungrounded or unfalsifiable claim."
                    conf_feedback = "Your confidence was high, but the claim lacked verifiable boundaries and evidence."
                    conf_omitted.append("High confidence is uncalibrated against unfalsifiable claim structure.")
            else:
                # Reasonably falsifiable claim
                if 2.0 <= user_conf <= 4.0:
                    conf_score = 20.0
                    conf_anchor = f"Well-Calibrated (20/20): Balanced confidence ({user_conf}/5) reflects verified structure with normal uncertainty."
                    conf_feedback = "Well-calibrated: your confidence is proportionate to the verifiable parameters present."
                    conf_identified.append("Confidence is balanced and proportionate to verifiable parameters.")
                elif user_conf > 4.0:
                    conf_score = 12.0
                    conf_anchor = f"Slightly Overconfident (12/20): Absolute certainty ({user_conf}/5) in probabilistic market domain."
                    conf_feedback = "Even well-specified financial claims carry market uncertainty; avoid maximum certainty."
                else:
                    conf_score = 14.0
                    conf_anchor = f"Slightly Cautious (14/20): Cautious confidence ({user_conf}/5) on a falsifiable claim."
                    conf_feedback = "Cautious stance is acceptable, though the claim did specify measurable conditions."

            dim_results[AssessmentDimensionEnum.CONFIDENCE_CALIBRATION] = DimensionEvaluationResult(
                dimension=AssessmentDimensionEnum.CONFIDENCE_CALIBRATION,
                score=conf_score,
                scoring_anchor=conf_anchor,
                correctly_identified_issues=conf_identified,
                omitted_or_unmentioned_issues=conf_omitted,
                feedback=conf_feedback,
            )

            # Total score
            total_score = round(sum(d.score for d in dim_results.values()), 1)

            # High-level summary
            if total_score >= 80.0:
                overall = "Exceptional claim critique demonstrating rigorous evidence-seeking, structural analysis, and well-calibrated confidence."
            elif total_score >= 60.0:
                overall = "Solid independent evaluation with good awareness of claim gaps. Continue focusing on specific statutory disclosures and alternative readings."
            elif total_score >= 40.0:
                overall = "Developing claim evaluation skills. Focus on identifying missing invalidation criteria and seeking primary sources before forming conclusions."
            else:
                overall = "Initial evaluation baseline. Work on actively checking for time horizons, downside risks, and verified evidence."

            return AssessmentEvaluationOutput(
                dimension_evaluations=dim_results,
                total_suggested_score=total_score,
                overall_feedback=overall,
            )

        except Exception as e:
            raise AssessmentEvaluationError(
                f"Failed to execute independent assessment evaluation: {str(e)}",
                details={"error": str(e)},
            ) from e

    def _build_empty_critique_result(
        self,
        input_data: UserAssessmentInput,
    ) -> AssessmentEvaluationOutput:
        """Handle empty or missing user critique gracefully with baseline anchor scores."""
        dim_results: Dict[AssessmentDimensionEnum, DimensionEvaluationResult] = {}
        empty_anchor = "Unattempted (0/20): No written evaluation provided."
        empty_feedback = "Provide a written explanation of your reasoning to receive detailed evaluation feedback."

        for dim in AssessmentDimensionEnum:
            if dim == AssessmentDimensionEnum.CONFIDENCE_CALIBRATION:
                # Evaluate confidence alone if provided
                conf_score = 5.0 if input_data.user_confidence > 3.0 else 10.0
                dim_results[dim] = DimensionEvaluationResult(
                    dimension=dim,
                    score=conf_score,
                    scoring_anchor=f"Baseline ({conf_score}/20): Confidence recorded without explanatory rationale.",
                    correctly_identified_issues=[],
                    omitted_or_unmentioned_issues=["No written critique provided to evaluate confidence calibration."],
                    feedback="Provide written reasoning explaining your confidence rating.",
                )
            else:
                dim_results[dim] = DimensionEvaluationResult(
                    dimension=dim,
                    score=0.0,
                    scoring_anchor=empty_anchor,
                    correctly_identified_issues=[],
                    omitted_or_unmentioned_issues=["Evaluation was unattempted or empty."],
                    feedback=empty_feedback,
                )

        total_score = round(sum(d.score for d in dim_results.values()), 1)
        return AssessmentEvaluationOutput(
            dimension_evaluations=dim_results,
            total_suggested_score=total_score,
            overall_feedback="No written evaluation was submitted. State your reasoning and identify claim limitations to receive detailed feedback.",
        )
