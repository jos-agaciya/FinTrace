import re
from typing import Dict, Any, List, Tuple, Optional

# Generic / low-effort phrases that should not receive full justification quality points
GENERIC_BOILERPLATE_PATTERNS = [
    r"^(?:good|bad|nice|buy|sell|to the moon|to the moon!|trust me|looks good|pump|dump|bullish|bearish)[\.!]?$",
    r"^i (?:think|feel|believe) so[\.!]?$",
    r"^strong fundamentals[\.!]?$",
    r"^because (?:it will|i want to|i say so)[\.!]?$",
    r"^no comment[\.!]?$",
    r"^just my opinion[\.!]?$"
]


class DeterministicRubricScorer:
    """
    Transparent 5-dimension deterministic evaluation rubric.
    Never uses opaque LLM guesses or Brier scores. Applies fixed, objective anchors.
    Each dimension: 0 to 20 points. Composite: 0 to 100 points.

    Dimension 5 evaluates: 'Confidence Justification & Epistemic Alignment'
    (Stored under `confidence_calibration` for backward compatibility).
    """

    @classmethod
    def score_assessment(
        cls,
        identified_evidence_types: List[str],
        distinguished_primary_sources: bool,
        identified_missing_specificity: List[str],
        identified_risk_factors: List[str],
        recognized_alternative_interpretations: bool,
        stated_confidence: float,
        evidence_backing_level: str,
        confidence_justification: Optional[str] = None
    ) -> Tuple[Dict[str, float], float, Dict[str, str]]:
        feedback: Dict[str, str] = {}

        # -------------------------------------------------------------
        # 1. Evidence Evaluation (0 - 20 points)
        # -------------------------------------------------------------
        ev_score = 0.0
        if distinguished_primary_sources:
            ev_score += 10.0
        ev_types_score = min(10.0, len(identified_evidence_types) * 2.5)
        ev_score += ev_types_score
        feedback["evidence_evaluation"] = (
            f"Scored {ev_score:.1f}/20. "
            f"{'Correctly separated primary filings from social claims. ' if distinguished_primary_sources else 'Failed to distinguish primary disclosures from unverified claims. '}"
            f"Recognized {len(identified_evidence_types)} relevant evidence source(s)."
        )

        # -------------------------------------------------------------
        # 2. Claim Specificity (0 - 20 points)
        # -------------------------------------------------------------
        spec_count = len(identified_missing_specificity)
        spec_score = min(20.0, spec_count * 4.0)
        feedback["claim_specificity"] = (
            f"Scored {spec_score:.1f}/20. "
            f"Identified {spec_count} unstated claim parameters ({', '.join(identified_missing_specificity) if identified_missing_specificity else 'none'})."
        )

        # -------------------------------------------------------------
        # 3. Risk Awareness (0 - 20 points)
        # -------------------------------------------------------------
        risk_count = len(identified_risk_factors)
        risk_score = min(20.0, risk_count * 5.0)
        feedback["risk_awareness"] = (
            f"Scored {risk_score:.1f}/20. "
            f"Articulated {risk_count} distinct downside/uncertainty risk factors."
        )

        # -------------------------------------------------------------
        # 4. Assumption Awareness (0 - 20 points)
        # -------------------------------------------------------------
        assump_score = 20.0 if recognized_alternative_interpretations else 6.0
        feedback["assumption_awareness"] = (
            f"Scored {assump_score:.1f}/20. "
            f"{'Demonstrated clear comprehension that multiple interpretations exist under varying assumptions.' if recognized_alternative_interpretations else 'Assumed single intended meaning without exploring alternative interpretations.'}"
        )

        # -------------------------------------------------------------
        # 5. Confidence Justification & Epistemic Alignment (0 - 20 points)
        # -------------------------------------------------------------
        calib_score, calib_feedback = cls._score_confidence_justification(
            stated_confidence=stated_confidence,
            distinguished_primary_sources=distinguished_primary_sources,
            identified_evidence_types=identified_evidence_types,
            identified_missing_specificity=identified_missing_specificity,
            identified_risk_factors=identified_risk_factors,
            recognized_alternative_interpretations=recognized_alternative_interpretations,
            evidence_backing_level=evidence_backing_level,
            justification=confidence_justification
        )
        feedback["confidence_calibration"] = calib_feedback

        scores = {
            "evidence_evaluation": round(ev_score, 1),
            "claim_specificity": round(spec_score, 1),
            "risk_awareness": round(risk_score, 1),
            "assumption_awareness": round(assump_score, 1),
            "confidence_calibration": round(calib_score, 1)
        }
        total_score = round(sum(scores.values()), 1)

        return scores, total_score, feedback

    @classmethod
    def _score_confidence_justification(
        cls,
        stated_confidence: float,
        distinguished_primary_sources: bool,
        identified_evidence_types: List[str],
        identified_missing_specificity: List[str],
        identified_risk_factors: List[str],
        recognized_alternative_interpretations: bool,
        evidence_backing_level: str,
        justification: Optional[str]
    ) -> Tuple[float, str]:
        """
        Calculates Dimension 5: Confidence Justification & Epistemic Alignment.
        4 Components:
          A. Evidence-Confidence Connection (0-6)
          B. Uncertainty Awareness (0-5)
          C. Risk-Confidence Relationship (0-5)
          D. Justification Quality (0-4)
        Total: 20 points.
        """
        raw_text = justification.strip() if justification is not None else ""
        has_text = len(raw_text) > 0
        lower_text = raw_text.lower()

        # Keywords for analytical connection
        mentions_evidence = any(w in lower_text for w in [
            "evidence", "filing", "disclosure", "sec", "nse", "bse",
            "financial", "audited", "report", "revenue", "margin", "statement"
        ]) if has_text else False

        mentions_uncertainty = any(w in lower_text for w in [
            "missing", "unclear", "timeframe", "uncertain", "ambiguous",
            "not stated", "invalidation", "unresolved", "assumption"
        ]) if has_text else False

        mentions_risk = any(w in lower_text for w in [
            "risk", "downside", "loss", "debt", "macro", "headwind",
            "solvency", "liability", "competition"
        ]) if has_text else False

        # --- A. Evidence-Confidence Connection (0 to 6 points) ---
        has_primary = distinguished_primary_sources and len(identified_evidence_types) > 0

        if stated_confidence >= 60.0:
            if has_primary:
                part_a = 6.0 if (mentions_evidence or not has_text) else 4.5
            elif len(identified_evidence_types) > 0 and not distinguished_primary_sources:
                # Unsupported commentary used to back high confidence
                part_a = 1.5
            else:
                part_a = 0.5 if stated_confidence > 85.0 else 1.0  # High confidence with zero evidence
        else:  # Stated confidence < 60%
            if not has_primary:
                # Restrained confidence due to absent/limited evidence
                part_a = 5.5 if (mentions_evidence or not has_text) else 4.0
            else:
                # Conservative stance despite primary filings
                part_a = 4.5

        # Deduct if high confidence explicitly contradicts lack of primary evidence
        if has_text and stated_confidence > 75.0 and not has_primary and not mentions_evidence:
            part_a = min(part_a, 0.5)

        # --- B. Uncertainty Awareness (0 to 5 points) ---
        missing_count = len(identified_missing_specificity)

        if missing_count >= 3 or recognized_alternative_interpretations:
            if mentions_uncertainty or not has_text:
                part_b = 5.0
            else:
                part_b = 3.5
        elif missing_count >= 1:
            part_b = 3.0 if (mentions_uncertainty or not has_text) else 2.5
        else:
            part_b = 1.0

        # High confidence without addressing identified missing parameters
        if stated_confidence > 85.0 and missing_count >= 1 and not mentions_uncertainty:
            part_b = max(0.5, part_b - 3.0)
        elif stated_confidence > 75.0 and missing_count >= 1 and not mentions_uncertainty:
            part_b = max(0.5, part_b - 1.5)

        # --- C. Risk-Confidence Relationship (0 to 5 points) ---
        risk_count = len(identified_risk_factors)

        if risk_count >= 2:
            if stated_confidence <= 55.0:
                part_c = 5.0  # Proportionately reduced confidence due to identified risks
            elif mentions_risk:
                part_c = 4.0  # High confidence maintained with explicit risk mitigation discussed
            else:
                part_c = 0.5 if stated_confidence > 85.0 else 1.0  # Ignoring 2+ identified risks
        elif risk_count == 1:
            part_c = 4.0 if (stated_confidence <= 70.0 or mentions_risk) else 2.0
        else:
            part_c = 1.5 if stated_confidence > 75.0 else 3.0

        # --- D. Justification Quality (0 to 4 points) ---
        if not has_text:
            # Baseline for omitted justification; penalize extreme ungrounded stances
            if stated_confidence > 85.0 and (risk_count >= 2 or not has_primary):
                part_d = 1.0
                quality_note = "Standard baseline applied (extreme confidence omitted justification)."
            else:
                part_d = 1.5
                quality_note = "Standard baseline applied (optional justification text was omitted)."
        else:
            # Check for generic boilerplate
            is_boilerplate = any(re.match(p, raw_text, re.IGNORECASE) for p in GENERIC_BOILERPLATE_PATTERNS)
            word_count = len(raw_text.split())

            if is_boilerplate or word_count <= 2:
                part_d = 0.5
                quality_note = "Generic boilerplate detected; lacks analytical specificity."
            elif word_count <= 4:
                part_d = 1.0
                quality_note = "Justification is brief and lacks explanatory depth."
            else:
                # Substantive explanation provided
                if mentions_evidence or mentions_risk or mentions_uncertainty:
                    part_d = 4.0
                    quality_note = "Substantive, coherent justification connecting confidence to evidence, uncertainty, and risks."
                else:
                    part_d = 2.5
                    quality_note = "Articulated justification provided with moderate conceptual connection."

        total_dim5 = min(20.0, max(0.0, round(part_a + part_b + part_c + part_d, 1)))

        feedback_msg = (
            f"Confidence Justification & Epistemic Alignment: Scored {total_dim5:.1f}/20. "
            f"[Evidence-Confidence: {part_a:.1f}/6, Uncertainty Awareness: {part_b:.1f}/5, "
            f"Risk Relationship: {part_c:.1f}/5, Justification Quality: {part_d:.1f}/4]. {quality_note}"
        )

        return total_dim5, feedback_msg
