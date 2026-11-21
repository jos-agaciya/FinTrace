"""Tests for Observable Persuasion and Risk Indicators."""

import pytest
from claim_extraction.risk_indicators import RiskIndicatorExtractor
from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    ExtractedClaim,
    InvalidationCriteria,
    RiskIndicatorType,
)


@pytest.fixture
def extractor():
    return RiskIndicatorExtractor()


def test_urgency_wording_detection(extractor):
    """Verify various urgency patterns are correctly detected and matched."""
    examples = [
        ("Tesla will reach $400 soon. Buy before it's too late!", "Buy before it's too late"),
        ("Act now to get high returns in energy stocks.", "Act now"),
        ("Don't miss this opportunity in biotech.", "Don't miss this"),
        ("Last chance to accumulate before the surge.", "Last chance"),
        ("Hurry and buy before earnings tomorrow.", "Hurry"),
        ("Get in now before institutional buying starts.", "Get in now"),
    ]

    for text, expected_match in examples:
        indicators = extractor.extract_indicators(text)
        urgency_inds = [i for i in indicators if i.indicator_type == RiskIndicatorType.URGENCY_WORDING]
        assert len(urgency_inds) >= 1, f"Failed to detect urgency in: {text}"
        assert urgency_inds[0].matched_phrase is not None
        assert expected_match.lower() in urgency_inds[0].matched_phrase.lower()
        assert urgency_inds[0].label == "Risk indicator"
        assert not urgency_inds[0].is_inferred_absence


def test_guaranteed_return_detection(extractor):
    """Verify explicit promises of zero risk or guaranteed return are flagged."""
    examples = [
        ("Guaranteed profit of 30% in two months.", "Guaranteed profit"),
        ("This is a risk-free investment with 25% yield.", "risk-free"),
        ("Stock cannot lose from these valuations.", "cannot lose"),
        ("We offer 100% assured returns on this strategy.", "100% assured"),
        ("Zero risk arbitrage play.", "zero risk"),
    ]

    for text, expected_match in examples:
        indicators = extractor.extract_indicators(text)
        guar_inds = [i for i in indicators if i.indicator_type == RiskIndicatorType.GUARANTEED_RETURN_LANGUAGE]
        assert len(guar_inds) >= 1, f"Failed to detect guarantee in: {text}"
        assert guar_inds[0].label == "Needs verification"
        assert not guar_inds[0].is_inferred_absence
        assert expected_match.lower() in guar_inds[0].matched_phrase.lower()


def test_unsupported_certainty_detection(extractor):
    """Verify hyperbolic certainty language is flagged as requiring verification."""
    examples = [
        ("The stock is definitely going to double by year-end.", "definitely going to double"),
        ("A certain breakout is underway across all tech names.", "certain breakout"),
        ("This asset has absolutely guaranteed growth prospects.", "absolutely guaranteed"),
        ("Will 100% surge past all previous highs.", "will 100%"),
    ]

    for text, expected_match in examples:
        indicators = extractor.extract_indicators(text)
        cert_inds = [i for i in indicators if i.indicator_type == RiskIndicatorType.UNSUPPORTED_CERTAINTY]
        assert len(cert_inds) >= 1, f"Failed to detect certainty in: {text}"
        assert cert_inds[0].label == "Needs verification"
        assert expected_match.lower() in cert_inds[0].matched_phrase.lower()


def test_missing_risk_disclosure_detection(extractor):
    """Verify claims making financial assertions without downside context trigger missing risk notice."""
    text = "Company XYZ will reach $150 by December 2026."
    claim = ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="XYZ will reach $150 by December 2026",
        raw_statement_excerpt=text,
        target_metric="$150",
        time_horizon="December 2026",
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=False,
        falsifiability_score=0.2,
        invalidation_criteria=[],
    )

    indicators = extractor.extract_indicators(text, claim)
    missing_risk = [i for i in indicators if i.indicator_type == RiskIndicatorType.MISSING_RISK_DISCLOSURE]
    assert len(missing_risk) == 1
    assert missing_risk[0].is_inferred_absence is True
    assert missing_risk[0].matched_phrase is None
    assert missing_risk[0].label == "Missing risk context"
    assert "absence in this specific post" in missing_risk[0].explanation


def test_presence_of_risk_suppresses_missing_risk_indicator(extractor):
    """Verify that including downside/stop-loss in text suppresses missing risk flag."""
    text = "Company XYZ will rise to $150, but exit if downside risk breaks below $110 stop loss."
    claim = ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="XYZ to $150 with $110 stop",
        raw_statement_excerpt=text,
        target_metric="$150",
        confidence_language=ConfidenceLanguageEnum.MODERATE,
        is_falsifiable=True,
        falsifiability_score=0.6,
        invalidation_criteria=[
            InvalidationCriteria(metric_or_trigger="Price drops below $110")
        ],
    )

    indicators = extractor.extract_indicators(text, claim)
    missing_risk = [i for i in indicators if i.indicator_type == RiskIndicatorType.MISSING_RISK_DISCLOSURE]
    assert len(missing_risk) == 0


def test_case_insensitive_matching(extractor):
    """Verify matching works across diverse casing."""
    text = "BUY BEFORE IT'S TOO LATE! THIS IS A GUARANTEED PROFIT!"
    indicators = extractor.extract_indicators(text)
    types = [i.indicator_type for i in indicators]
    assert RiskIndicatorType.URGENCY_WORDING in types
    assert RiskIndicatorType.GUARANTEED_RETURN_LANGUAGE in types


def test_no_false_positives_on_factual_financial_text(extractor):
    """Verify neutral corporate or financial text yields no persuasion indicators."""
    text = (
        "Tata Motors reported quarterly revenues of Rs 105,000 crore. "
        "Commercial vehicle margins stood at 8.2% and passenger vehicles at 6.1%. "
        "Management noted ongoing chip supply chain stabilization."
    )
    indicators = extractor.extract_indicators(text)
    # No urgency, no guarantees, no unsupported certainty
    persuasion_inds = [
        i for i in indicators
        if i.indicator_type in (
            RiskIndicatorType.URGENCY_WORDING,
            RiskIndicatorType.GUARANTEED_RETURN_LANGUAGE,
            RiskIndicatorType.UNSUPPORTED_CERTAINTY,
        )
    ]
    assert len(persuasion_inds) == 0


def test_duplicate_indicator_suppression(extractor):
    """Verify repeating the same phrase does not create duplicate indicator entries."""
    text = "Act now! Act now! Act now! Buy before it's too late!"
    indicators = extractor.extract_indicators(text)
    urgency_inds = [i for i in indicators if i.indicator_type == RiskIndicatorType.URGENCY_WORDING]
    # Should only have 2 distinct matched phrases ('Act now' and 'Buy before it's too late')
    assert len(urgency_inds) == 2


def test_neutral_labels_and_zero_accusations(extractor):
    """CRITICAL INVARIANT: Verify that outputs never accuse anyone of fraud, scam, or crime."""
    text = "XYZ is a guaranteed profit, act now and buy before it's too late, certain breakout!"
    indicators = extractor.extract_indicators(text)
    assert len(indicators) >= 3

    forbidden_terms = ["fraud", "scam", "manipulat", "guilt", "illegal", "crime", "crook"]
    for ind in indicators:
        assert ind.label in ["Risk indicator", "Needs verification", "Missing risk context"]
        full_text = f"{ind.label} {ind.explanation} {ind.review_prompt}".lower()
        for term in forbidden_terms:
            assert term not in full_text, f"Forbidden accusatory term '{term}' found in indicator output!"
