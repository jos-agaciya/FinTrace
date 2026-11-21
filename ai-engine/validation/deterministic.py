"""Deterministic validation engine for FinTrace AI Engine.

CRITICAL INVARIANTS:
1. Deterministic rules are mathematical and logical boundaries, not model opinions.
2. Missing details must remain None. Hallucinated numbers are flagged as errors.
3. Chronological causality must be preserved (horizons cannot precede statement dates).
4. Unsupported assertions are NOT automatically marked false (use INSUFFICIENT_EVIDENCE or UNVERIFIED).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from claim_extraction.schemas import EvidenceItem, ExtractedClaim
from interpretation.schemas import InterpretationFork
from validation.schemas import (
    GroundingCheckResult,
    GroundingStatus,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


class DeterministicValidator:
    """Non-LLM validator applying mathematical, chronological, and provenance rules."""

    def validate_claim(
        self,
        claim: ExtractedClaim,
        raw_text: Optional[str] = None,
        published_at: Optional[datetime] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> ValidationResult:
        """Execute full deterministic validation suite over an extracted claim."""
        issues: List[ValidationIssue] = []
        raw_text = raw_text or claim.raw_statement_excerpt

        # 1. Null preservation and hallucination check
        null_verified = self._check_null_and_hallucination(claim, raw_text, issues)

        # 2. Chronological causality check
        chronology_verified = self._check_chronology(claim, published_at, issues)

        # 3. Numeric and percentage bounds check
        numeric_verified = self._check_numeric_bounds(claim, issues)

        # 4. Falsifiability structural consistency
        self._check_falsifiability_consistency(claim, issues)

        # 5. Evidence grounding check (if evidence supplied)
        grounding_results = self._check_evidence_grounding(claim, evidence or [])

        # Determine overall validity
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        has_warnings = any(issue.severity == ValidationSeverity.WARNING for issue in issues)

        if has_errors:
            status = "FAILED"
        elif has_warnings:
            status = "PASSED_WITH_WARNINGS"
        else:
            status = "PASSED"

        return ValidationResult(
            claim_id=claim.claim_id,
            is_valid=not has_errors,
            validation_status=status,
            null_preservation_verified=null_verified,
            chronology_verified=chronology_verified,
            numeric_bounds_verified=numeric_verified,
            issues=issues,
            grounding_checks=grounding_results,
        )

    def validate_interpretation_fork(
        self, fork: InterpretationFork
    ) -> List[ValidationIssue]:
        """Validate an interpretation fork's provenance and plausibility boundaries."""
        issues: List[ValidationIssue] = []

        if fork.provenance_label != "AI-Generated Interpretation (Hypothesis)":
            issues.append(
                ValidationIssue(
                    issue_code="INVALID_PROVENANCE_LABEL",
                    severity=ValidationSeverity.ERROR,
                    message="Interpretation fork must be labelled strictly as an AI-generated hypothesis.",
                    field_name="provenance_label",
                    details={"found": fork.provenance_label},
                )
            )

        if not (0.0 <= fork.plausibility_weight <= 1.0):
            issues.append(
                ValidationIssue(
                    issue_code="WEIGHT_OUT_OF_BOUNDS",
                    severity=ValidationSeverity.ERROR,
                    message="Fork plausibility weight must be between 0.0 and 1.0.",
                    field_name="plausibility_weight",
                    details={"weight": fork.plausibility_weight},
                )
            )

        if not fork.distinguishing_evidence_needed or len(fork.distinguishing_evidence_needed.strip()) < 5:
            issues.append(
                ValidationIssue(
                    issue_code="MISSING_DISTINGUISHING_CRITERIA",
                    severity=ValidationSeverity.WARNING,
                    message="Fork should provide specific observable evidence needed to distinguish it.",
                    field_name="distinguishing_evidence_needed",
                )
            )

        return issues

    # -----------------------------------------------------------------------
    # Internal Validation Checkers
    # -----------------------------------------------------------------------

    # Common number word mappings for grounding checks (Audit Item M-2)
    _NUMBER_WORDS = {
        "0": ["zero", "nil", "none"],
        "1": ["one", "single", "a"],
        "2": ["two", "double", "couple"],
        "3": ["three", "triple"],
        "4": ["four"],
        "5": ["five"],
        "6": ["six"],
        "7": ["seven"],
        "8": ["eight"],
        "9": ["nine"],
        "10": ["ten"],
        "11": ["eleven"],
        "12": ["twelve", "dozen"],
        "15": ["fifteen"],
        "20": ["twenty"],
        "25": ["twenty-five", "twenty five"],
        "30": ["thirty"],
        "40": ["forty"],
        "50": ["fifty"],
        "60": ["sixty"],
        "70": ["seventy"],
        "80": ["eighty"],
        "90": ["ninety"],
        "100": ["hundred", "one hundred", "a hundred"],
        "400": ["four hundred"],
        "500": ["five hundred", "half thousand"],
        "1000": ["thousand", "one thousand", "a thousand", "1k"],
    }

    def _is_number_grounded_in_text(self, num_str: str, raw_text_lower: str) -> bool:
        """Check if a numeric value is grounded either as digits or as number words."""
        # 1. Direct digit match
        if num_str in raw_text_lower:
            return True

        # 2. Check integer vs float representation (e.g. "400.0" -> "400" or vice versa)
        try:
            val = float(num_str)
            int_val = int(val)
            if val == int_val and str(int_val) in raw_text_lower:
                return True
        except ValueError:
            pass

        # 3. Known word equivalents
        if num_str in self._NUMBER_WORDS:
            for word_variant in self._NUMBER_WORDS[num_str]:
                if word_variant in raw_text_lower:
                    return True

        # 4. Check for compound word numbers (e.g., 400 = "four hundred", 2500 = "twenty five hundred")
        try:
            int_num = int(float(num_str))
            hundreds, rem = divmod(int_num, 100)
            if hundreds > 0 and rem == 0 and str(hundreds) in self._NUMBER_WORDS:
                h_words = self._NUMBER_WORDS[str(hundreds)]
                for hw in h_words:
                    if f"{hw} hundred" in raw_text_lower:
                        return True
        except (ValueError, TypeError):
            pass

        return False

    def _check_null_and_hallucination(
        self, claim: ExtractedClaim, raw_text: str, issues: List[ValidationIssue]
    ) -> bool:
        """Verify that missing details remained None, and extracted numbers exist in text."""
        passed = True
        raw_text_lower = raw_text.lower()

        # Check target metric fidelity
        if claim.target_metric:
            # Extract numbers/digits from target metric (e.g. "$400" -> "400")
            numbers = re.findall(r"\d+(?:\.\d+)?", claim.target_metric)
            for num in numbers:
                if not self._is_number_grounded_in_text(num, raw_text_lower):
                    issues.append(
                        ValidationIssue(
                            issue_code="HALLUCINATED_NUMERIC_TARGET",
                            severity=ValidationSeverity.ERROR,
                            message=f"Extracted target number '{num}' was not found in source text (as digits or words).",
                            field_name="target_metric",
                            details={"target_metric": claim.target_metric, "missing_token": num},
                        )
                    )
                    passed = False

        # Check ticker symbol sanity
        if claim.ticker:
            cleaned_ticker = claim.ticker.strip().upper()
            if not re.match(r"^[A-Z]{1,5}$", cleaned_ticker):
                issues.append(
                    ValidationIssue(
                        issue_code="MALFORMED_TICKER",
                        severity=ValidationSeverity.WARNING,
                        message=f"Ticker '{claim.ticker}' does not follow standard 1-5 letter equity format.",
                        field_name="ticker",
                        details={"ticker": claim.ticker},
                    )
                )

        return passed

    def _check_chronology(
        self,
        claim: ExtractedClaim,
        published_at: Optional[datetime],
        issues: List[ValidationIssue],
    ) -> bool:
        """Verify that time horizon does not precede publication date (Audit Item M-1)."""
        if not published_at or not claim.time_horizon:
            return True

        horizon_str = claim.time_horizon
        candidate_years: List[int] = []

        # 1. 4-digit years (e.g. "2025", "2026")
        for match in re.finditer(r"\b(19\d\d|20\d\d)\b", horizon_str):
            candidate_years.append(int(match.group(1)))

        # 2. ISO dates (e.g. "2024-12-31")
        for match in re.finditer(r"\b(\d{4})-\d{2}(?:-\d{2})?\b", horizon_str):
            candidate_years.append(int(match.group(1)))

        # 3. Fiscal/Quarterly notations with 2-digit years: FY25, CY26, Q3 25, '24
        for match in re.finditer(r"(?:FY|CY|Q[1-4]|['’])\s*(\d{2})\b", horizon_str, re.IGNORECASE):
            two_digit = int(match.group(1))
            # Convert 2-digit to 4-digit (assuming 2000s)
            candidate_years.append(2000 + two_digit)

        # Deduplicate while preserving discovered years
        discovered_years = set(candidate_years)

        for year in discovered_years:
            if year < published_at.year:
                issues.append(
                    ValidationIssue(
                        issue_code="CHRONOLOGY_INVERSION",
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Time horizon year '{year}' precedes publication year "
                            f"'{published_at.year}'."
                        ),
                        field_name="time_horizon",
                        details={"horizon_year": year, "published_year": published_at.year},
                    )
                )
                return False

        return True

    def _check_numeric_bounds(
        self, claim: ExtractedClaim, issues: List[ValidationIssue]
    ) -> bool:
        """Verify numeric sanity on percentages and targets."""
        passed = True

        if not (0.0 <= claim.falsifiability_score <= 1.0):
            issues.append(
                ValidationIssue(
                    issue_code="SCORE_OUT_OF_BOUNDS",
                    severity=ValidationSeverity.ERROR,
                    message="Falsifiability score must be in range [0.0, 1.0].",
                    field_name="falsifiability_score",
                    details={"score": claim.falsifiability_score},
                )
            )
            passed = False

        if claim.target_metric:
            # Check for negative stock price targets
            if re.search(r"-\s*\$\d+", claim.target_metric):
                issues.append(
                    ValidationIssue(
                        issue_code="NEGATIVE_PRICE_TARGET",
                        severity=ValidationSeverity.ERROR,
                        message="Negative stock price target is mathematically invalid.",
                        field_name="target_metric",
                        details={"target": claim.target_metric},
                    )
                )
                passed = False

        return passed

    def _check_falsifiability_consistency(
        self, claim: ExtractedClaim, issues: List[ValidationIssue]
    ) -> None:
        """Verify logical consistency of falsifiability flags and score."""
        if claim.is_falsifiable and len(claim.invalidation_criteria) == 0:
            issues.append(
                ValidationIssue(
                    issue_code="FALSIFIABILITY_CONTRADICTION",
                    severity=ValidationSeverity.ERROR,
                    message="Claim is marked falsifiable, but invalidation criteria list is empty.",
                    field_name="is_falsifiable",
                )
            )

        if not claim.is_falsifiable and claim.falsifiability_score > 0.5:
            issues.append(
                ValidationIssue(
                    issue_code="UNFALSIFIABLE_HIGH_SCORE",
                    severity=ValidationSeverity.WARNING,
                    message="Unfalsifiable claim assigned unexpectedly high falsifiability score.",
                    field_name="falsifiability_score",
                    details={"score": claim.falsifiability_score},
                )
            )

    def _check_evidence_grounding(
        self, claim: ExtractedClaim, evidence_list: List[EvidenceItem]
    ) -> List[GroundingCheckResult]:
        """Check claim against provided evidence without assuming unsupported claims are false."""
        results: List[GroundingCheckResult] = []

        if not evidence_list:
            return results

        claim_tokens = set(re.findall(r"\w+", claim.claim_summary.lower()))
        target_numbers = set(re.findall(r"\d+(?:\.\d+)?", claim.target_metric or ""))

        for ev in evidence_list:
            ev_text_lower = ev.text_content.lower()
            ev_numbers = set(re.findall(r"\d+(?:\.\d+)?", ev.text_content))

            # Check overlap of ticker or company name
            has_entity = False
            if claim.ticker and claim.ticker.lower() in ev_text_lower:
                has_entity = True
            if claim.company_name and claim.company_name.lower() in ev_text_lower:
                has_entity = True

            matched_facts = []
            contradicted_facts = []

            if not has_entity:
                status = GroundingStatus.INSUFFICIENT_EVIDENCE
                rationale = f"Evidence from '{ev.source_name}' does not mention target company/ticker."
            else:
                # Check target numbers
                if target_numbers and target_numbers.issubset(ev_numbers):
                    status = GroundingStatus.SUPPORTED
                    matched_facts.append(f"Target numbers {target_numbers} corroborated in {ev.source_name}.")
                    rationale = f"Evidence explicitly supports numeric metrics in claim."
                elif "decline" in ev_text_lower and claim.direction.value == "BULLISH" and "growth" in claim.claim_summary.lower():
                    status = GroundingStatus.CONTRADICTED
                    contradicted_facts.append("Evidence reports decline where claim asserts growth.")
                    rationale = f"Contradictory directional indicators in {ev.source_name}."
                else:
                    status = GroundingStatus.INSUFFICIENT_EVIDENCE
                    rationale = f"Evidence from '{ev.source_name}' references the company but lacks specific claim metrics."

            results.append(
                GroundingCheckResult(
                    claim_id=claim.claim_id,
                    evidence_id=ev.evidence_id,
                    source_name=ev.source_name,
                    status=status,
                    rationale=rationale,
                    matched_facts=matched_facts,
                    contradicted_facts=contradicted_facts,
                )
            )

        return results
