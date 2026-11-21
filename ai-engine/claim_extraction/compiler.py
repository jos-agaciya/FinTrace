"""Falsifiability Compiler for financial claims.

Evaluates testability, observable invalidation criteria, and assigns an objective
falsifiability score without guessing or inventing unstated facts.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    ExtractedClaim,
    InvalidationCriteria,
)


class FalsifiabilityCompiler:
    """Evaluates whether financial claims have testable, observable falsification boundaries."""

    @staticmethod
    def compile_falsifiability(
        claim: ExtractedClaim,
    ) -> Tuple[bool, float, List[InvalidationCriteria]]:
        """Assess testability and compute objective falsifiability score in range [0.0, 1.0].

        Returns:
            Tuple of (is_falsifiable: bool, score: float, validated_criteria: List[InvalidationCriteria])
        """
        criteria = claim.invalidation_criteria or []
        has_criteria = len(criteria) > 0

        # Assess criteria concreteness
        concrete_criteria_count = 0
        has_quant_threshold = False
        has_time_boundary = False
        has_observable_source = False

        for c in criteria:
            if c.metric_or_trigger and len(c.metric_or_trigger.strip()) > 3:
                concrete_criteria_count += 1
            if c.invalidation_threshold:
                has_quant_threshold = True
            if c.time_boundary:
                has_time_boundary = True
            if c.observable_source:
                has_observable_source = True

        # Base score calculations
        score = 0.05

        if has_criteria and concrete_criteria_count > 0:
            score += 0.30
        if has_quant_threshold:
            score += 0.25
        if has_time_boundary or claim.time_horizon:
            score += 0.20
        if has_observable_source:
            score += 0.20

        # Penalize unanchored / hyperbolic language
        if claim.confidence_language == ConfidenceLanguageEnum.HYPERBOLIC:
            score -= 0.15
        elif claim.confidence_language == ConfidenceLanguageEnum.HIGHLY_HEDGED:
            score -= 0.05

        # Check for vague hype tokens without numbers in summary
        summary_lower = claim.claim_summary.lower()
        vague_patterns = [r"\bmoon\b", r"\bmassive rally\b", r"\bsoon\b", r"\bgreat\b", r"\bhuge\b"]
        if any(re.search(pat, summary_lower) for pat in vague_patterns) and not claim.target_metric:
            score = min(score, 0.15)

        # Clamping
        score = max(0.0, min(1.0, round(score, 2)))
        is_falsifiable = score >= 0.40 and concrete_criteria_count > 0

        return is_falsifiable, score, criteria
