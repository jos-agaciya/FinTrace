"""Observable persuasion and risk indicators extractor for financial claims.

CRITICAL INVARIANTS:
1. Indicators are review prompts ("needs verification"), NEVER proof of fraud,
   manipulation, guilt, or intentional wrongdoing.
2. Distinguishes directly matched language from inferred absence of risk disclosures.
3. Preserves exact verbatim matched phrases without fabrication.
4. Employs case-insensitive, explainable, deterministic pattern matching.
5. Missing risk disclosure is an absence in the submitted claim, not proof that the
   underlying company has no risk disclosures in statutory filings.
"""

from __future__ import annotations

import re
from typing import List, Optional, Set, Tuple

from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    ExtractedClaim,
    RiskIndicator,
    RiskIndicatorType,
)


class RiskIndicatorExtractor:
    """Deterministic extractor for observable persuasion patterns and missing risk disclosures."""

    # Category A: Urgency Wording
    URGENCY_PATTERNS: List[Tuple[str, str]] = [
        (
            r"\bbuy\s+before\s+it(?:'s|\s+is)\s+too\s+late\b",
            "Urgency phrase urging purchase before an imminent, unverified cutoff.",
        ),
        (
            r"\bact\s+now\b",
            "Urgency phrase prompting immediate action without providing due diligence time.",
        ),
        (
            r"\bdon(?:'t|\s+not)\s+miss\s+(?:this|out|the)\b",
            "Fear-of-missing-out (FOMO) wording encouraging unconsidered participation.",
        ),
        (
            r"\blast\s+chance\b",
            "Time-pressure phrase suggesting immediate scarcity or irreversible price change.",
        ),
        (
            r"\bhurry\b",
            "Direct speed imperative discouraging thorough thesis verification.",
        ),
        (
            r"\bget\s+in\s+now\b",
            "Immediate entry imperative without specifying entry price bounds.",
        ),
        (
            r"\blimited\s+time\b",
            "Artificial scarcity wording suggesting a narrow action window.",
        ),
        (
            r"\bbefore\s+it\s+moons\b",
            "Speculative urgency phrase asserting impending explosive upward momentum.",
        ),
        (
            r"\brally\s+starting\s+now\b",
            "Immediate timing assertion implying imminent directional momentum.",
        ),
    ]

    # Category B: Guaranteed Return Language
    GUARANTEED_PATTERNS: List[Tuple[str, str]] = [
        (
            r"\bguaranteed\s+(?:profit|return|growth|money|yield)s?\b",
            "Assertion of guaranteed financial return, contradicting standard market uncertainty.",
        ),
        (
            r"\brisk[- ]free\s*(?:profit|return|investment|money)?\b",
            "Explicit claim of zero risk or risk-free returns in an equity or derivative instrument.",
        ),
        (
            r"\bcannot\s+(?:lose|fail)\b",
            "Absolute denial of downside probability in financial speculation.",
        ),
        (
            r"\bcan(?:'t|\s+not)\s+lose\b",
            "Colloquial assertion of impossible failure or guaranteed success.",
        ),
        (
            r"\b100%\s+(?:assured|guaranteed|safe|win)\b",
            "Deterministic 100% certainty claimed for an uncertain financial outcome.",
        ),
        (
            r"\bzero\s+risk\b",
            "Assertion that an investment carries no risk of capital loss.",
        ),
        (
            r"\bsure\s+shot\b",
            "Colloquial guarantee implying a certain financial outcome.",
        ),
    ]

    # Category C: Unsupported Certainty
    CERTAINTY_PATTERNS: List[Tuple[str, str]] = [
        (
            r"\bdefinitely\s+(?:going\s+to|will)\s+(?:double|rise|surge|moon|explode|reach)\b",
            "Unconditional certainty expressed regarding price movement magnitude.",
        ),
        (
            r"\bcertain\s+breakout\b",
            "Technical analysis assertion presented as guaranteed rather than probabilistic.",
        ),
        (
            r"\babsolutely\s+guaranteed\b",
            "Hyperbolic certainty language removing standard probabilistic caveats.",
        ),
        (
            r"\bwill\s+100%(?=\s|\b|$)",
            "Mathematical certainty asserted for a future market event.",
        ),
        (
            r"\binevitably\s+will\b",
            "Deterministic phrasing denying alternative macroeconomic or operational outcomes.",
        ),
        (
            r"\bguaranteed\s+growth\b",
            "Growth presented as unconditional without operational prerequisites.",
        ),
    ]

    # Negative tokens that indicate presence of genuine risk context
    RISK_CONTEXT_TOKENS: List[str] = [
        "risk",
        "downside",
        "stop loss",
        "stop-loss",
        "drawdown",
        "volatility",
        "regulatory",
        "invalidation",
        "uncertainty",
        "if revenue falls",
        "losses",
        "bear case",
        "worst case",
    ]

    def extract_indicators(
        self,
        text: str,
        claim: Optional[ExtractedClaim] = None,
    ) -> List[RiskIndicator]:
        """Extract observable persuasion indicators and evaluate missing risk context.

        Args:
            text: Raw input statement text.
            claim: Optional ExtractedClaim for structural cross-referencing.

        Returns:
            List of neutral RiskIndicator instances.
        """
        if not text or not text.strip():
            return []

        indicators: List[RiskIndicator] = []
        seen_keys: Set[str] = set()

        # 1. Scan Urgency Wording
        for pattern, explanation in self.URGENCY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0)
                dedup_key = f"{RiskIndicatorType.URGENCY_WORDING}:{matched_phrase.lower()}"
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    indicators.append(
                        RiskIndicator(
                            indicator_type=RiskIndicatorType.URGENCY_WORDING,
                            label="Risk indicator",
                            matched_phrase=matched_phrase,
                            explanation=explanation,
                            is_inferred_absence=False,
                            review_prompt=(
                                "Review prompt: Verify whether external disclosures substantiate an immediate "
                                "deadline, or whether this represents artificial timing pressure."
                            ),
                        )
                    )

        # 2. Scan Guaranteed Return Language
        for pattern, explanation in self.GUARANTEED_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0)
                dedup_key = f"{RiskIndicatorType.GUARANTEED_RETURN_LANGUAGE}:{matched_phrase.lower()}"
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    indicators.append(
                        RiskIndicator(
                            indicator_type=RiskIndicatorType.GUARANTEED_RETURN_LANGUAGE,
                            label="Needs verification",
                            matched_phrase=matched_phrase,
                            explanation=explanation,
                            is_inferred_absence=False,
                            review_prompt=(
                                "Review prompt: Financial instruments inherently carry risk of capital loss. "
                                "Inspect statutory filings for material downside risks."
                            ),
                        )
                    )

        # 3. Scan Unsupported Certainty
        for pattern, explanation in self.CERTAINTY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0)
                dedup_key = f"{RiskIndicatorType.UNSUPPORTED_CERTAINTY}:{matched_phrase.lower()}"
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    indicators.append(
                        RiskIndicator(
                            indicator_type=RiskIndicatorType.UNSUPPORTED_CERTAINTY,
                            label="Needs verification",
                            matched_phrase=matched_phrase,
                            explanation=explanation,
                            is_inferred_absence=False,
                            review_prompt=(
                                "Review prompt: Assess whether the author provides measurable invalidation criteria "
                                "or baseline evidence supporting this high degree of certainty."
                            ),
                        )
                    )

        # 4. Check for Missing Risk Disclosure
        # Condition: Claim makes a directional or target assertion, but provides zero risk context or invalidation criteria.
        text_lower = text.lower()
        has_risk_words = any(token in text_lower for token in self.RISK_CONTEXT_TOKENS)
        has_invalidation_criteria = bool(claim and claim.invalidation_criteria)

        # Check if text makes an actionable directional assertion
        makes_assertion = bool(
            re.search(r"\b(will|going to|target|rise|fall|gain|double|rally|crash|drop)\b", text_lower)
            or (claim and (claim.target_metric or claim.direction.value in ["BULLISH", "BEARISH"]))
        )

        if makes_assertion and not has_risk_words and not has_invalidation_criteria:
            dedup_key = f"{RiskIndicatorType.MISSING_RISK_DISCLOSURE}:absence"
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                indicators.append(
                    RiskIndicator(
                        indicator_type=RiskIndicatorType.MISSING_RISK_DISCLOSURE,
                        label="Missing risk context",
                        matched_phrase=None,
                        explanation=(
                            "The submitted statement makes a financial return or price assertion without providing "
                            "downside scenarios, stop levels, or risk caveats in the text. "
                            "(Note: This represents an absence in this specific post, not proof that the company "
                            "lacks risk disclosures in official filings)."
                        ),
                        is_inferred_absence=True,
                        review_prompt=(
                            "Review prompt: Seek independent risk factors in regulatory disclosures (e.g. Item 1A / "
                            "SEBI disclosures) to understand conditions under which this thesis fails."
                        ),
                    )
                )

        return indicators
