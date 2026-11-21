"""Tests verifying packaging, subpackage imports, and core data contracts."""

import asyncio
import json
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError


def test_subpackage_imports():
    """Verify all 7 core subpackages can be imported cleanly without syntax errors."""
    import assessment
    import claim_extraction
    import fallback
    import interpretation
    import orchestration
    import providers
    import validation

    assert assessment is not None
    assert claim_extraction is not None
    assert fallback is not None
    assert interpretation is not None
    assert orchestration is not None
    assert providers is not None
    assert validation is not None


def test_extracted_claim_null_invariants():
    """Verify missing claim parameters strictly remain None in Python and null in JSON."""
    from claim_extraction.schemas import (
        ConfidenceLanguageEnum,
        DirectionEnum,
        ExtractedClaim,
    )

    claim = ExtractedClaim(
        direction=DirectionEnum.BULLISH,
        claim_summary="Growth in EV deliveries",
        raw_statement_excerpt="Deliveries expected to grow.",
        confidence_language=ConfidenceLanguageEnum.MODERATE,
        is_falsifiable=False,
        falsifiability_score=0.2,
    )

    # Invariant: unstated details must default to None
    assert claim.company_name is None
    assert claim.ticker is None
    assert claim.target_metric is None
    assert claim.time_horizon is None
    assert claim.entry_condition is None
    assert claim.exit_condition is None
    assert claim.invalidation_criteria == []
    assert claim.stated_rationale == []
    assert claim.unstated_assumptions == []

    # JSON serialization check: must serialize as literal JSON null
    raw_json = claim.model_dump_json()
    data = json.loads(raw_json)
    assert data["target_metric"] is None
    assert data["time_horizon"] is None
    assert data["entry_condition"] is None
    assert data["exit_condition"] is None
    assert data["company_name"] is None
    assert data["ticker"] is None

    # Deserialization round-trip
    restored = ExtractedClaim.model_validate_json(raw_json)
    assert restored.claim_id == claim.claim_id
    assert restored.target_metric is None


def test_extracted_claim_invalid_bounds_and_types():
    """Verify validation boundaries on score and enums."""
    from claim_extraction.schemas import (
        ConfidenceLanguageEnum,
        DirectionEnum,
        ExtractedClaim,
    )

    with pytest.raises(ValidationError):
        ExtractedClaim(
            direction=DirectionEnum.BULLISH,
            claim_summary="Invalid score claim",
            raw_statement_excerpt="Excerpt",
            confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
            is_falsifiable=True,
            falsifiability_score=1.5,
        )

    with pytest.raises(ValidationError):
        ExtractedClaim(
            direction=DirectionEnum.BULLISH,
            claim_summary="Invalid score claim",
            raw_statement_excerpt="Excerpt",
            confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
            is_falsifiable=True,
            falsifiability_score=-0.1,
        )

    with pytest.raises(ValidationError):
        ExtractedClaim(
            direction="MEGA_BULLISH",  # type: ignore
            claim_summary="Invalid direction",
            raw_statement_excerpt="Excerpt",
            confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
            is_falsifiable=True,
            falsifiability_score=0.5,
        )


def test_invalidation_criteria_null_invariants():
    """Verify invalidation criteria preserve None for missing thresholds."""
    from claim_extraction.schemas import InvalidationCriteria

    crit = InvalidationCriteria(
        metric_or_trigger="Operating margin compression"
    )

    assert crit.invalidation_threshold is None
    assert crit.time_boundary is None
    assert crit.observable_source is None

    data = json.loads(crit.model_dump_json())
    assert data["invalidation_threshold"] is None
    assert data["time_boundary"] is None
    assert data["observable_source"] is None


def test_evidence_item_contract_and_timezone():
    """Verify EvidenceItem fields, source types, and timezone-aware timestamps."""
    from claim_extraction.schemas import EvidenceItem, SourceTypeEnum

    now_utc = datetime.now(timezone.utc)
    item = EvidenceItem(
        source_name="SEC Form 10-K",
        source_url="https://www.sec.gov/Archives/edgar/data/1318605/000131860524000008/tsla-20231231.htm",
        source_type=SourceTypeEnum.SEC_FILING,
        published_at=now_utc,
        text_content="Total automotive revenues were $82,419 million in 2023.",
        provenance_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        provenance_metadata={"accession_number": "0001318605-24-000008", "page": 45},
    )

    assert item.source_type == SourceTypeEnum.SEC_FILING
    assert item.source_name == "SEC Form 10-K"
    assert item.retrieved_at.tzinfo is not None
    assert item.provenance_metadata["accession_number"] == "0001318605-24-000008"

    serialized = item.model_dump_json()
    parsed = json.loads(serialized)
    assert parsed["source_type"] == "SEC_FILING"
    assert parsed["provenance_metadata"]["page"] == 45


def test_interpretation_fork_provenance_label():
    """Verify interpretation forks enforce immutable AI-generated hypothesis provenance."""
    from claim_extraction.schemas import DirectionEnum
    from interpretation.schemas import InterpretationFork

    fork = InterpretationFork(
        fork_title="Automotive Margin Excluding Credits",
        scenario_description="Margin rebound relies strictly on auto COGS reduction.",
        plausibility_weight=0.6,
        implied_direction=DirectionEnum.BULLISH,
        distinguishing_evidence_needed="SEC 10-Q Segment Breakdown",
    )

    assert fork.provenance_label == "AI-Generated Interpretation (Hypothesis)"

    with pytest.raises(ValidationError):
        fork.provenance_label = "Confirmed Author Intent"


def test_provider_schemas_and_request_contract():
    """Verify LLMMessage, ProviderRequest, ProviderResponse, and TokenUsage."""
    from providers.schemas import (
        LLMMessage,
        MessageRole,
        ProviderRequest,
        ProviderResponse,
        ProviderStatus,
        TokenUsage,
    )

    msg = LLMMessage(role=MessageRole.USER, content="Extract thesis")
    req = ProviderRequest(
        model_id="mock-falsifier-v1",
        messages=[msg],
        temperature=0.0,
        timeout_seconds=15.0,
    )

    assert req.model_id == "mock-falsifier-v1"
    assert req.temperature == 0.0
    assert len(req.messages) == 1

    with pytest.raises(ValidationError):
        TokenUsage(prompt_tokens=-1)

    resp = ProviderResponse(
        provider_name="mock",
        model_id="mock-falsifier-v1",
        raw_content='{"is_falsifiable": true}',
        structured_data={"is_falsifiable": True},
        latency_ms=45.2,
        token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        status=ProviderStatus.HEALTHY,
    )

    assert resp.provider_name == "mock"
    assert resp.status == ProviderStatus.HEALTHY
    assert resp.created_at.tzinfo is not None


def test_base_provider_interface_compliance():
    """Verify that a provider subclass can implement BaseLLMProvider correctly."""
    from typing import Tuple, Type, TypeVar
    from pydantic import BaseModel
    from providers.base import BaseLLMProvider
    from providers.schemas import (
        LLMMessage,
        MessageRole,
        ProviderRequest,
        ProviderResponse,
        ProviderStatus,
        TokenUsage,
    )

    M = TypeVar("M", bound=BaseModel)

    class MockTestProvider(BaseLLMProvider):
        @property
        def provider_name(self) -> str:
            return "mock-test"

        async def generate_text(self, request: ProviderRequest) -> ProviderResponse:
            return ProviderResponse(
                provider_name=self.provider_name,
                model_id=request.model_id,
                raw_content="Mock test text",
                latency_ms=10.0,
                token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            )

        async def generate_structured(
            self, request: ProviderRequest, response_model: Type[M]
        ) -> Tuple[M, ProviderResponse]:
            instance = response_model()
            resp = await self.generate_text(request)
            return instance, resp

        async def health_check(self) -> ProviderStatus:
            return ProviderStatus.HEALTHY

    async def run():
        provider = MockTestProvider()
        assert provider.provider_name == "mock-test"
        status = await provider.health_check()
        assert status == ProviderStatus.HEALTHY
        req = ProviderRequest(
            model_id="test-model",
            messages=[LLMMessage(role=MessageRole.USER, content="Hello")],
        )
        resp = await provider.generate_text(req)
        assert resp.raw_content == "Mock test text"
        assert resp.latency_ms == 10.0

    asyncio.run(run())


def test_error_hierarchy():
    """Verify AI Engine exception inheritance and details dictionary."""
    from validation.errors import (
        AIEngineError,
        ChronologicalInconsistencyError,
        CircuitBreakerOpenError,
        FalsifiabilityValidationError,
        HallucinationError,
        ProviderError,
        ProviderRateLimitError,
        ProviderTimeoutError,
        SchemaValidationError,
    )

    assert issubclass(FalsifiabilityValidationError, AIEngineError)
    assert issubclass(HallucinationError, AIEngineError)
    assert issubclass(ChronologicalInconsistencyError, AIEngineError)
    assert issubclass(SchemaValidationError, AIEngineError)
    assert issubclass(ProviderError, AIEngineError)
    assert issubclass(ProviderTimeoutError, ProviderError)
    assert issubclass(ProviderRateLimitError, ProviderError)
    assert issubclass(CircuitBreakerOpenError, ProviderError)

    err = ProviderTimeoutError(
        "Request exceeded 30s", details={"timeout_seconds": 30.0, "provider": "groq"}
    )
    assert err.message == "Request exceeded 30s"
    assert err.details["timeout_seconds"] == 30.0
