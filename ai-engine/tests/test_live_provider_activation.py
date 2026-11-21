"""Comprehensive verification suite for Phase 1: Live AI Provider Activation & Verification.

Executes the 8 mandatory test scenarios:
1. Both available (Groq primary, Gemini reviewer).
2. Groq down (failover to Gemini, same-provider review flagged).
3. Gemini down (Groq available, degraded single-provider mode).
4. Both down (AllProvidersFailedError with diagnostics).
5. Invalid credentials (ProviderAuthenticationError, no silent mock substitution).
6. Timeout handling (ProviderTimeoutError, circuit breaker recorded).
7. Malformed response (SchemaValidationError, raw payload captured).
8. Evidence unavailable (empty evidence bundle, zero fabricated evidence).

Plus dual-model review independence verification with identical claim and evidence.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    EvidenceItem,
    ExtractedClaim,
    InvalidationCriteria,
    SourceTypeEnum,
)
from engine_interface import ClaimExtractionInput, DualModelReviewInput
from facade import FinTraceAIEngine
from fallback.circuit_breaker import CircuitBreaker, CircuitState
from fallback.fallback_manager import FallbackManager
from interpretation.schemas import ForkAnalysisResult, InterpretationFork
from orchestration.reviewer import DualModelReviewer
from orchestration.schemas import DualModelReviewOutput
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider
from providers.schemas import LLMMessage, MessageRole, ProviderRequest, ProviderResponse, TokenUsage
from validation.errors import (
    AllProvidersFailedError,
    CircuitBreakerOpenError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    SchemaValidationError,
)


def _make_sample_claim(
    company: str = "Tesla, Inc.",
    ticker: str = "TSLA",
    summary: str = "Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
    direction: DirectionEnum = DirectionEnum.BULLISH,
    target: str = "$400",
    horizon: str = "end of 2026",
    provider: str = "groq",
    model: str = "llama-3.3-70b-versatile",
) -> ExtractedClaim:
    return ExtractedClaim(
        company_name=company,
        ticker=ticker,
        claim_summary=summary,
        direction=direction,
        target_metric=target,
        time_horizon=horizon,
        entry_condition="Commercial rollout of autonomous Robotaxi fleet",
        exit_condition=None,
        confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
        is_falsifiable=True,
        falsifiability_score=0.85,
        invalidation_criteria=[
            InvalidationCriteria(
                metric_or_trigger="Zero commercial autonomous ride-hail cities active",
                invalidation_threshold="0 cities",
                time_boundary="Q4 2026",
                observable_source="SEC Form 10-K / NHTSA Filings",
            )
        ],
        stated_rationale=["Robotaxi autonomy scaling"],
        unstated_assumptions=["Unsupervised autonomy regulatory approvals granted across US states"],
        raw_statement_excerpt=summary,
        metadata={"provider_name": provider, "model_id": model},
    )


def _make_mock_groq_completion(content: str, model: str = "llama-3.3-70b-versatile"):
    choice = MagicMock()
    choice.message.content = content
    usage = MagicMock()
    usage.prompt_tokens = 50
    usage.completion_tokens = 65
    usage.total_tokens = 115
    completion = MagicMock()
    completion.choices = [choice]
    completion.usage = usage
    completion.model = model
    completion.id = "groq-test-live-1"
    return completion


def _make_mock_gemini_response(content: str, model_id: str = "gemini-1.5-flash"):
    resp = MagicMock()
    resp.text = content
    usage = MagicMock()
    usage.prompt_token_count = 55
    usage.candidates_token_count = 70
    usage.total_token_count = 125
    resp.usage_metadata = usage
    resp.response_id = "gemini-test-live-1"
    return resp


# ==============================================================================
# SCENARIO 1: Both Providers Available (Groq primary, Gemini reviewer)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_1_both_providers_available():
    """Verify live dual-model orchestration when both Groq and Gemini are healthy."""
    sample_claim = _make_sample_claim(provider="groq", model="llama-3.3-70b-versatile")
    fork_result = ForkAnalysisResult(
        claim_id=sample_claim.claim_id,
        ambiguity_detected=True,
        ambiguity_reasons=["Automotive unit sales multiple vs software licensing multiple."],
        forks=[
            InterpretationFork(
                fork_title="Core Automotive Hardware Thesis",
                scenario_description="Valuation supported by automotive deliveries and manufacturing margin expansion.",
                plausibility_weight=0.55,
                implied_direction=DirectionEnum.BULLISH,
                distinguishing_evidence_needed="SEC 10-Q Automotive Gross Margin",
            )
        ],
    )

    # 1. Mock Groq client
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create = AsyncMock()

    call_count = 0

    async def groq_structured_mock(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_mock_groq_completion(sample_claim.model_dump_json())
        return _make_mock_groq_completion(fork_result.model_dump_json())

    mock_groq_client.chat.completions.create.side_effect = groq_structured_mock

    # 2. Mock Gemini client for reviewer
    mock_gemini_client = MagicMock()
    review_output = DualModelReviewOutput(
        primary_claim=sample_claim,
        reviewer_critique_notes="Verified by Gemini: invalidation criteria and null parameters confirmed.",
        is_concordant=True,
        disagreement_reasons=[],
    )
    mock_gemini_client.aio.models.generate_content = AsyncMock(
        return_value=_make_mock_gemini_response(review_output.model_dump_json())
    )

    groq_provider = GroqProvider(api_key="test-groq-key", client=mock_groq_client)
    gemini_provider = GeminiProvider(api_key="test-gemini-key", client=mock_gemini_client)

    engine = FinTraceAIEngine(
        primary_provider=groq_provider,
        reviewer_provider=gemini_provider,
    )

    evidence = [
        EvidenceItem(
            source_name="SEC 10-K",
            source_url="https://sec.gov/edgar/data/tsla-10k",
            source_type=SourceTypeEnum.SEC_FILING,
            text_content="Tesla reports full vehicle deliveries and segment disclosures.",
        )
    ]

    inp = ClaimExtractionInput(
        raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
        retrieved_evidence=evidence,
    )

    result = await engine.analyze_end_to_end(inp)

    # Assertions for Scenario 1
    assert result.claim.company_name == "Tesla, Inc."
    assert result.claim.target_metric == "$400"
    assert result.primary_provider == "groq"
    assert result.primary_model == "llama-3.3-70b-versatile"
    assert result.fallback_used is False
    assert result.is_degraded is False

    assert result.dual_model_review is not None
    assert result.dual_model_review.is_concordant is True
    assert result.dual_model_review.independent_review_valid is True
    assert result.dual_model_review.review_mode == "INDEPENDENT_DUAL_MODEL"
    assert result.dual_model_review.extractor_provider == "groq"
    assert result.dual_model_review.reviewer_provider == "gemini"
    assert "Two-model agreement is not proof of factual correctness" in result.dual_model_review.consensus_warning


# ==============================================================================
# SCENARIO 2: Groq Down (Failover to Gemini, same-provider review flagged)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_2_groq_down_failover_to_gemini():
    """Verify that when Groq experiences an outage, Gemini handles primary extraction and review is flagged degraded."""
    sample_claim = _make_sample_claim(provider="gemini", model="gemini-1.5-flash")
    fork_result = ForkAnalysisResult(
        claim_id=sample_claim.claim_id,
        ambiguity_detected=False,
        forks=[],
    )

    # 1. Failing Groq
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create = AsyncMock(
        side_effect=Exception("HTTP 429: Groq rate limit reached for model llama-3.3-70b")
    )
    groq_provider = GroqProvider(api_key="test-groq-key", client=mock_groq_client)

    # 2. Healthy Gemini
    mock_gemini_client = MagicMock()
    gemini_calls = 0

    async def gemini_mock(*args, **kwargs):
        nonlocal gemini_calls
        gemini_calls += 1
        if gemini_calls == 1:
            # Claim extraction
            return _make_mock_gemini_response(sample_claim.model_dump_json())
        elif gemini_calls == 2:
            # Fork analysis
            return _make_mock_gemini_response(fork_result.model_dump_json())
        else:
            # Dual-model review
            rev = DualModelReviewOutput(
                primary_claim=sample_claim,
                reviewer_critique_notes="Audit completed.",
                is_concordant=True,
            )
            return _make_mock_gemini_response(rev.model_dump_json())

    mock_gemini_client.aio.models.generate_content = AsyncMock(side_effect=gemini_mock)
    gemini_provider = GeminiProvider(api_key="test-gemini-key", client=mock_gemini_client)

    resilient_primary = FallbackManager(
        primary_provider=groq_provider,
        secondary_provider=gemini_provider,
    )

    engine = FinTraceAIEngine(
        primary_provider=resilient_primary,
        reviewer_provider=gemini_provider,
    )

    inp = ClaimExtractionInput(raw_text="Tesla will reach $400 by end of 2026.")
    result = await engine.analyze_end_to_end(inp)

    # Assertions for Scenario 2
    assert result.primary_provider == "gemini"
    assert result.fallback_used is True
    assert result.is_degraded is True
    assert "rate limit" in result.primary_failure_reason.lower()

    # Reviewer was also Gemini -> must flag same-provider degraded self-review!
    assert result.dual_model_review is not None
    assert result.dual_model_review.independent_review_valid is False
    assert result.dual_model_review.review_mode == "DEGRADED_SAME_PROVIDER"
    assert "DEGRADED SAME-PROVIDER SELF-REVIEW" in result.dual_model_review.reviewer_critique_notes


# ==============================================================================
# SCENARIO 3: Gemini Down (Groq available, degraded single-provider mode)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_3_gemini_down_groq_available():
    """Verify that when Gemini reviewer is unavailable, Groq extraction succeeds in degraded single-provider mode."""
    sample_claim = _make_sample_claim(provider="groq", model="llama-3.3-70b-versatile")
    fork_result = ForkAnalysisResult(claim_id=sample_claim.claim_id, ambiguity_detected=False, forks=[])

    # 1. Healthy Groq
    mock_groq_client = MagicMock()
    groq_calls = 0

    async def groq_mock(*args, **kwargs):
        nonlocal groq_calls
        groq_calls += 1
        if groq_calls == 1:
            return _make_mock_groq_completion(sample_claim.model_dump_json())
        return _make_mock_groq_completion(fork_result.model_dump_json())

    mock_groq_client.chat.completions.create = AsyncMock(side_effect=groq_mock)
    groq_provider = GroqProvider(api_key="test-groq-key", client=mock_groq_client)

    # 2. Failing Gemini
    mock_gemini_client = MagicMock()
    mock_gemini_client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("503 Service Unavailable: Gemini cluster unreachable")
    )
    gemini_provider = GeminiProvider(api_key="test-gemini-key", client=mock_gemini_client)

    engine = FinTraceAIEngine(
        primary_provider=groq_provider,
        reviewer_provider=gemini_provider,
    )

    inp = ClaimExtractionInput(raw_text="Tesla will reach $400 by end of 2026.")
    result = await engine.analyze_end_to_end(inp)

    # Assertions for Scenario 3
    assert result.claim.company_name == "Tesla, Inc."
    assert result.primary_provider == "groq"
    assert result.fallback_used is False
    assert result.is_degraded is True  # Degraded due to single-provider reviewer failure

    assert result.dual_model_review is not None
    assert result.dual_model_review.independent_review_valid is False
    assert result.dual_model_review.review_mode == "DEGRADED_SINGLE_PROVIDER"
    assert "DEGRADED OPERATION" in result.dual_model_review.reviewer_critique_notes


# ==============================================================================
# SCENARIO 4: Both Providers Down (AllProvidersFailedError)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_4_both_providers_down():
    """Verify that when both Groq and Gemini fail, AllProvidersFailedError is raised with full diagnostics."""
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create = AsyncMock(
        side_effect=Exception("HTTP 429 RateLimit")
    )
    groq_provider = GroqProvider(api_key="test-groq-key", client=mock_groq_client)

    mock_gemini_client = MagicMock()
    mock_gemini_client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("HTTP 500 Internal Server Error")
    )
    gemini_provider = GeminiProvider(api_key="test-gemini-key", client=mock_gemini_client)

    resilient_primary = FallbackManager(
        primary_provider=groq_provider,
        secondary_provider=gemini_provider,
    )

    engine = FinTraceAIEngine(
        primary_provider=resilient_primary,
        reviewer_provider=gemini_provider,
    )

    inp = ClaimExtractionInput(raw_text="Tesla will reach $400 by end of 2026.")

    with pytest.raises(AllProvidersFailedError) as exc_info:
        await engine.analyze_end_to_end(inp)

    err = exc_info.value
    assert "All AI providers failed" in str(err)
    assert err.details["primary_provider"] == "groq"
    assert err.details["secondary_provider"] == "gemini"


# ==============================================================================
# SCENARIO 5: Invalid API Credentials (No silent mock substitution)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_5_invalid_credentials_and_no_silent_mock_substitution():
    """Verify 401/403 credential errors raise ProviderAuthenticationError and live mode forbids mock substitution."""
    # 1. Groq invalid credential
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create = AsyncMock(
        side_effect=Exception("HTTP 401: Invalid API Key provided")
    )
    groq_provider = GroqProvider(api_key="invalid-key", client=mock_groq_client)

    req = ProviderRequest(messages=[LLMMessage(role=MessageRole.USER, content="Hello")])
    with pytest.raises(ProviderAuthenticationError):
        await groq_provider.generate_text(req)

    # 2. Gemini invalid credential
    mock_gemini_client = MagicMock()
    err = Exception("PERMISSION_DENIED: API key not valid")
    setattr(err, "code", 403)
    mock_gemini_client.aio.models.generate_content = AsyncMock(side_effect=err)
    gemini_provider = GeminiProvider(api_key="invalid-key", client=mock_gemini_client)

    with pytest.raises(ProviderAuthenticationError):
        await gemini_provider.generate_text(req)

    # 3. FinTraceAIEngine.from_env(require_live=True) refuses silent mock fallback when keys missing
    with patch.dict(os.environ, {"GROQ_API_KEY": "", "GEMINI_API_KEY": ""}, clear=True):
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(ProviderUnavailableError) as exc_info:
                FinTraceAIEngine.from_env(require_live=True)
            assert "LIVE PROVIDER UNAVAILABLE" in str(exc_info.value)


# ==============================================================================
# SCENARIO 6: Timeout Handling
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_6_timeout_handling():
    """Verify request timeout boundaries raise ProviderTimeoutError and record circuit failures."""
    mock_client = MagicMock()

    async def slow_call(*args, **kwargs):
        await asyncio.sleep(0.5)

    mock_client.chat.completions.create = slow_call

    # Set aggressive timeout of 0.05s
    groq_provider = GroqProvider(api_key="test-key", timeout_seconds=0.05, client=mock_client)
    req = ProviderRequest(
        messages=[LLMMessage(role=MessageRole.USER, content="Slow query")],
        timeout_seconds=0.05,
    )

    with pytest.raises(ProviderTimeoutError) as exc_info:
        await groq_provider.generate_text(req)
    assert "timed out after 0.1s" in str(exc_info.value) or "timed out" in str(exc_info.value).lower()

    # Circuit breaker records the failure
    circuit = CircuitBreaker(provider_name="groq", failure_threshold=2)
    with pytest.raises(ProviderTimeoutError):
        await circuit.call(groq_provider.generate_text, req)
    assert circuit.consecutive_failures == 1


# ==============================================================================
# SCENARIO 7: Malformed Model Response
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_7_malformed_response_handling():
    """Verify unparseable JSON from model raises SchemaValidationError with captured snippet."""
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create = AsyncMock(
        return_value=_make_mock_groq_completion("{corrupted:json:data...not valid")
    )
    groq_provider = GroqProvider(api_key="test-key", client=mock_groq_client)

    req = ProviderRequest(messages=[LLMMessage(role=MessageRole.USER, content="Extract")])

    with pytest.raises(SchemaValidationError) as exc_info:
        await groq_provider.generate_structured(req, ExtractedClaim)

    err = exc_info.value
    assert "failed schema validation" in str(err).lower()
    assert "raw_output" in err.details
    assert "{corrupted:json" in err.details["raw_output"]


# ==============================================================================
# SCENARIO 8: Evidence Unavailable (Empty Evidence Bundle)
# ==============================================================================
@pytest.mark.asyncio
async def test_scenario_8_evidence_unavailable_handled_safely():
    """Verify that when no external evidence is available, the pipeline executes safely without fabricating sources."""
    sample_claim = _make_sample_claim()
    fork_result = ForkAnalysisResult(claim_id=sample_claim.claim_id, ambiguity_detected=False, forks=[])

    mock_groq_client = MagicMock()
    calls = 0

    async def groq_mock(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _make_mock_groq_completion(sample_claim.model_dump_json())
        return _make_mock_groq_completion(fork_result.model_dump_json())

    mock_groq_client.chat.completions.create = AsyncMock(side_effect=groq_mock)
    groq_provider = GroqProvider(api_key="test-key", client=mock_groq_client)

    mock_gemini_client = MagicMock()
    rev = DualModelReviewOutput(
        primary_claim=sample_claim,
        reviewer_critique_notes="No external grounding evidence was provided; evaluated purely on textual falsifiability.",
        is_concordant=True,
    )
    mock_gemini_client.aio.models.generate_content = AsyncMock(
        return_value=_make_mock_gemini_response(rev.model_dump_json())
    )
    gemini_provider = GeminiProvider(api_key="test-key", client=mock_gemini_client)

    engine = FinTraceAIEngine(primary_provider=groq_provider, reviewer_provider=gemini_provider)

    # Empty evidence bundle
    inp = ClaimExtractionInput(
        raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
        retrieved_evidence=[],
    )

    result = await engine.analyze_end_to_end(inp)

    # Assertions
    assert result.claim.company_name == "Tesla, Inc."
    assert result.validation.is_valid is True
    assert result.validation.null_preservation_verified is True
    assert result.dual_model_review is not None
    assert result.dual_model_review.is_concordant is True
    # Verify no fabricated evidence items
    meta = result.dual_model_review.metadata
    assert meta["evidence_summary"]["evidence_items_total"] == 0
    assert meta["evidence_summary"]["evidence_items_included"] == 0


# ==============================================================================
# DUAL-MODEL REVIEW INDEPENDENCE INTEGRITY VERIFICATION
# ==============================================================================
@pytest.mark.asyncio
async def test_dual_model_review_independence_integrity():
    """Verify that Groq and Gemini independently critique the same claim and evidence, and disagreements spawn forks."""
    claim = _make_sample_claim(provider="groq", model="llama-3.3-70b-versatile")
    evidence = [
        EvidenceItem(
            source_name="SEC 10-Q",
            source_url="https://sec.gov/edgar/data/tsla-10q",
            source_type=SourceTypeEnum.SEC_FILING,
            text_content="Tesla reported automotive revenues and $400 scaling targets.",
        )
    ]

    primary_groq = MagicMock()
    primary_groq.provider_name = "groq"
    primary_groq.default_model = "llama-3.3-70b-versatile"

    # Secondary Gemini reviewer DISAGREES with primary
    reviewer_gemini = MagicMock()
    reviewer_gemini.provider_name = "gemini"
    reviewer_gemini.default_model = "gemini-1.5-flash"
    reviewer_gemini.health_check = AsyncMock(return_value="HEALTHY")

    disagreement_fork = InterpretationFork(
        fork_title="Regulatory Non-Approval Autonomous Delay",
        scenario_description="Reviewer thesis: commercial robotaxi deployment will be delayed past 2026 by NHTSA regulatory inquiries.",
        plausibility_weight=0.45,
        implied_direction=DirectionEnum.BEARISH,
        distinguishing_evidence_needed="NHTSA Part 555 Exemption Grant or Denial Order",
    )

    rev_output = DualModelReviewOutput(
        primary_claim=claim,
        reviewer_critique_notes="Reviewer disputes target feasibility: Autonomous fleet permits remain ungranted.",
        is_concordant=False,
        disagreement_reasons=["NHTSA commercial deployment permits unobtained."],
        spawned_forks=[disagreement_fork],
    )

    reviewer_gemini.generate_structured = AsyncMock(
        return_value=(
            rev_output,
            ProviderResponse(
                provider_name="gemini",
                model_id="gemini-1.5-flash",
                latency_ms=95.0,
                token_usage=TokenUsage(prompt_tokens=40, completion_tokens=30, total_tokens=70),
            ),
        )
    )

    reviewer = DualModelReviewer(primary_provider=primary_groq, reviewer_provider=reviewer_gemini)
    review_input = DualModelReviewInput(
        claim=claim,
        evidence=evidence,
        extractor_provider="groq",
        extractor_model="llama-3.3-70b-versatile",
    )

    result = await reviewer.review(review_input)

    # Verify genuine independent dual-model review
    assert result.independent_review_valid is True
    assert result.review_mode == "INDEPENDENT_DUAL_MODEL"
    assert result.extractor_provider == "groq"
    assert result.extractor_model == "llama-3.3-70b-versatile"
    assert result.reviewer_provider == "gemini"
    assert result.reviewer_model == "gemini-1.5-flash"

    # Verify disagreement mechanics
    assert result.is_concordant is False
    assert len(result.disagreement_reasons) == 1
    assert "NHTSA" in result.disagreement_reasons[0]
    assert len(result.spawned_forks) == 1
    assert result.spawned_forks[0].fork_title == "Regulatory Non-Approval Autonomous Delay"
    assert "Two-model agreement is not proof of factual correctness" in result.consensus_warning
