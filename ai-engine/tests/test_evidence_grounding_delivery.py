"""Regression tests verifying evidence delivery to both models (Audit Item H-1)."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from claim_extraction.evidence_formatter import format_evidence_bundle
from claim_extraction.extractor import ClaimExtractor
from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    EvidenceItem,
    ExtractedClaim,
    SourceTypeEnum,
)
from engine_interface import ClaimExtractionInput
from orchestration.reviewer import DualModelReviewer
from orchestration.schemas import DualModelReviewInput, DualModelReviewOutput
from providers.mock_provider import MockProvider
from providers.schemas import ProviderRequest, ProviderResponse


def test_evidence_formatting_separates_claim_and_formats_metadata():
    """Verify format_evidence_bundle formats evidence items with source, URL, date, and excerpt."""
    evidence = [
        EvidenceItem(
            source_name="SEC Form 10-K",
            source_url="https://sec.gov/edgar/data/12345/10k",
            source_type=SourceTypeEnum.SEC_FILING,
            published_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
            text_content="Total automotive revenues rose 15% YoY with gross margin of 18.2%.",
        )
    ]

    bundle_text, meta = format_evidence_bundle(evidence)

    assert "=== RETRIEVED GROUNDING EVIDENCE (EXTERNAL DOCUMENTS) ===" in bundle_text
    assert "SEC Form 10-K" in bundle_text
    assert "https://sec.gov/edgar/data/12345/10k" in bundle_text
    assert "2025-02-01" in bundle_text
    assert "Total automotive revenues rose 15% YoY" in bundle_text
    assert meta["evidence_items_total"] == 1
    assert meta["evidence_items_included"] == 1
    assert meta["evidence_truncated"] is False


def test_evidence_formatting_empty_evidence():
    """Verify empty evidence is handled honestly without fabrication."""
    bundle_text, meta = format_evidence_bundle([])
    assert "No external grounding evidence was provided" in bundle_text
    assert meta["evidence_items_total"] == 0
    assert meta["evidence_items_included"] == 0
    assert meta["evidence_truncated"] is False


def test_evidence_truncation_limits_are_observable():
    """Verify evidence bundle truncation triggers observable metadata and notes."""
    # Create 8 evidence items where max_items is 3
    items = [
        EvidenceItem(
            source_name=f"Source {i}",
            source_url=f"https://source{i}.com",
            source_type=SourceTypeEnum.NEWS_ARTICLE,
            text_content=f"Report excerpt content for item {i}.",
        )
        for i in range(8)
    ]

    bundle_text, meta = format_evidence_bundle(items, max_items=3, max_total_chars=1000)

    assert meta["evidence_items_total"] == 8
    assert meta["evidence_items_included"] == 3
    assert meta["evidence_truncated"] is True
    assert "[NOTE: Evidence bundle truncated" in bundle_text


@pytest.mark.asyncio
async def test_claim_extractor_delivers_evidence_content_to_provider():
    """Verify ClaimExtractor passes serialized evidence into provider request prompt."""
    captured_request = None

    class CapturingProvider(MockProvider):
        async def generate_structured(self, request, response_model):
            nonlocal captured_request
            captured_request = request
            return await super().generate_structured(request, response_model)

    provider = CapturingProvider(name="capturing-extractor")
    extractor = ClaimExtractor(provider)

    evidence = [
        EvidenceItem(
            source_name="Tesla IR Shareholder Deck",
            source_url="https://ir.tesla.com/q4-deck",
            source_type=SourceTypeEnum.RESEARCH_NOTE,
            published_at=datetime(2025, 1, 28, tzinfo=timezone.utc),
            text_content="Next-gen platform pilot deployment scheduled for Q3 2026.",
        )
    ]

    inp = ClaimExtractionInput(
        raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
        retrieved_evidence=evidence,
    )

    await extractor.extract_claim(inp)

    assert captured_request is not None
    user_msg = captured_request.messages[1].content

    # 1. User claim is clearly segregated from evidence
    assert "=== USER-SUBMITTED CLAIM TO EVALUATE ===" in user_msg
    assert "Tesla will reach $400" in user_msg

    # 2. Retrieved evidence content is delivered, not just count
    assert "=== RETRIEVED GROUNDING EVIDENCE (EXTERNAL DOCUMENTS) ===" in user_msg
    assert "Tesla IR Shareholder Deck" in user_msg
    assert "https://ir.tesla.com/q4-deck" in user_msg
    assert "Next-gen platform pilot deployment scheduled for Q3 2026" in user_msg


@pytest.mark.asyncio
async def test_reviewer_delivers_evidence_content_to_reviewer_provider():
    """Verify DualModelReviewer passes actual evidence text and source metadata, not merely a count."""
    captured_request = None

    class CapturingReviewer(MockProvider):
        async def generate_structured(self, request, response_model):
            nonlocal captured_request
            captured_request = request
            return await super().generate_structured(request, response_model)

    primary = MockProvider(name="mock-primary")
    reviewer = CapturingReviewer(name="mock-reviewer")
    dual_reviewer = DualModelReviewer(primary_provider=primary, reviewer_provider=reviewer)

    claim = ExtractedClaim(
        company_name="Tesla, Inc.",
        claim_summary="Tesla will reach $400 by end of 2026.",
        direction=DirectionEnum.BULLISH if hasattr(DirectionEnum, "BULLISH") else "BULLISH",
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE if hasattr(ConfidenceLanguageEnum, "ASSERTIVE") else "ASSERTIVE",
        is_falsifiable=True,
        falsifiability_score=0.85,
        invalidation_criteria=[],
        raw_statement_excerpt="Tesla will reach $400 by end of 2026.",
    )

    evidence = [
        EvidenceItem(
            source_name="SEC 10-K Item 7",
            source_url="https://sec.gov/tsla-10k",
            source_type=SourceTypeEnum.SEC_FILING,
            published_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
            text_content="Automotive margin ex-regulatory credits was 17.2%.",
        )
    ]

    inp = DualModelReviewInput(claim=claim, evidence=evidence)
    await dual_reviewer.review(inp)

    assert captured_request is not None
    user_msg = captured_request.messages[1].content

    # Reviewer receives actual evidence content, not merely "1 items provided"
    assert "=== PRIMARY EXTRACTED CLAIM TO AUDIT ===" in user_msg
    assert "SEC 10-K Item 7" in user_msg
    assert "https://sec.gov/tsla-10k" in user_msg
    assert "Automotive margin ex-regulatory credits was 17.2%" in user_msg
    assert "Evidence Items: 1 items provided" not in user_msg
