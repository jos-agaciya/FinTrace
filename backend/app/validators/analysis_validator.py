from typing import Dict, Any, List, Optional, Tuple


class AnalysisValidator:
    """
    Independent deterministic validation layer.
    Ensures that factual assertions are backed by evidence,
    classifies statements epistemologically, and detects material disagreements.
    """

    @staticmethod
    def calculate_falsifiability(
        target_value: Optional[float],
        time_horizon: Optional[str],
        entry_condition: Optional[str],
        exit_condition: Optional[str],
        invalidation_condition: Optional[str]
    ) -> Tuple[float, List[str], str]:
        """
        Evaluates whether a claim is sufficiently specific to be tested.
        Scores from 0 to 100 based on presence of key falsifiability dimensions.
        """
        missing = []
        score = 0.0

        if target_value is not None:
            score += 25.0
        else:
            missing.append("target_value")

        if time_horizon:
            score += 25.0
        else:
            missing.append("time_horizon")

        if entry_condition:
            score += 15.0
        else:
            missing.append("entry_condition")

        if exit_condition:
            score += 15.0
        else:
            missing.append("exit_condition")

        if invalidation_condition:
            score += 20.0
        else:
            missing.append("invalidation_condition")

        # Explain what is needed to make the claim testable
        if not missing:
            explanation = "Claim satisfies all core testability dimensions with explicit invalidation conditions."
        else:
            missing_str = ", ".join(missing)
            explanation = (
                f"Claim lacks critical falsifiability parameters: [{missing_str}]. "
                "Without an explicit invalidation condition and definite timeframe, this claim cannot be falsified."
            )

        return score, missing, explanation

    @staticmethod
    def categorize_statements(
        claim_text: str,
        evidence_items: List[Dict[str, Any]],
        analysis_summary: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Deterministically separates statements into 4 distinct epistemological categories:
        1. SOURCE_FACT
        2. AI_INTERPRETATION
        3. USER_ASSUMPTION
        4. UNRESOLVED_QUESTION
        """
        facts: List[str] = []
        interpretations: List[str] = []
        assumptions: List[str] = []
        unresolved: List[str] = []

        # Extract verified facts from evidence
        for ev in evidence_items:
            summary = ev.get("content_summary") or ev.get("title", "")
            publisher = ev.get("publisher", "Disclosures")
            facts.append(f"[{publisher}] {summary}")

        if not facts:
            unresolved.append("No primary company disclosures or regulatory filings verified for this claim.")

        # Classify claim components
        interpretations.append(
            f"[AI_INTERPRETATION] System parsed claim as: '{claim_text}'. Potential thesis requires verifying underlying corporate fundamentals."
        )

        assumptions.append("[USER_ASSUMPTION] Author assumes past trends or social sentiment will drive future price movement.")

        unresolved.append("[UNRESOLVED_QUESTION] What specific operational catalyst supports the projected valuation within the stated window?")

        return {
            "SOURCE_FACT": facts,
            "AI_INTERPRETATION": interpretations,
            "USER_ASSUMPTION": assumptions,
            "UNRESOLVED_QUESTION": unresolved
        }

    @staticmethod
    def detect_material_disagreements(
        primary_output: Dict[str, Any],
        secondary_output: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Compares primary and secondary outputs for material contradictions.
        Returns (has_disagreement, list_of_reasons).
        """
        disagreements = []

        # Check explicit review disagreement flag
        if not secondary_output.get("agrees", True):
            for issue in secondary_output.get("material_disagreements", []):
                disagreements.append(f"Secondary model flagged: {issue}")

        # Check directional conflict if both provided
        prim_dir = primary_output.get("direction")
        sec_dir = secondary_output.get("direction")
        if prim_dir and sec_dir and prim_dir.upper() != sec_dir.upper():
            disagreements.append(f"Directional conflict: Primary concluded '{prim_dir}' while Secondary concluded '{sec_dir}'.")

        has_disagreement = len(disagreements) > 0
        return has_disagreement, disagreements
