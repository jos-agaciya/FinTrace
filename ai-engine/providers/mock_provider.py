"""Genuinely executable Mock Provider for offline testing and deterministic verification.

CRITICAL INVARIANTS:
1. Genuinely analyzes input prompt patterns instead of returning a static hardcoded string.
2. Preserves strict null invariants (missing target/horizon -> None).
3. Simulates realistic failure modes (timeout, rate limit, degraded mode, model disagreement).
4. Zero network access or API credentials required.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from claim_extraction.schemas import (
    ConfidenceLanguageEnum,
    DirectionEnum,
    ExtractedClaim,
    InvalidationCriteria,
)
from interpretation.schemas import ForkAnalysisResult, InterpretationFork
from orchestration.schemas import DualModelReviewOutput
from providers.base import BaseLLMProvider
from providers.schemas import (
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
    TokenUsage,
)
from validation.errors import (
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SchemaValidationError,
)

T = TypeVar("T", bound=BaseModel)


class MockProvider(BaseLLMProvider):
    """Deterministic mock provider simulating Groq/Gemini execution patterns."""

    def __init__(
        self,
        name: str = "mock-provider",
        simulated_latency_ms: float = 12.5,
        force_timeout: bool = False,
        force_rate_limit: bool = False,
        force_malformed_json: bool = False,
        disagree_with_primary: bool = False,
        degraded: bool = False,
    ):
        self._name = name
        self.simulated_latency_ms = simulated_latency_ms
        self.force_timeout = force_timeout
        self.force_rate_limit = force_rate_limit
        self.force_malformed_json = force_malformed_json
        self.disagree_with_primary = disagree_with_primary
        self.degraded = degraded

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate_text(self, request: ProviderRequest) -> ProviderResponse:
        self._check_simulated_failures(request)
        return ProviderResponse(
            provider_name=self.provider_name,
            model_id=request.model_id,
            raw_content="Mock generated text output based on prompt.",
            latency_ms=self.simulated_latency_ms,
            token_usage=TokenUsage(prompt_tokens=45, completion_tokens=25, total_tokens=70),
            status=ProviderStatus.DEGRADED if self.degraded else ProviderStatus.HEALTHY,
        )

    async def generate_structured(
        self, request: ProviderRequest, response_model: Type[T]
    ) -> Tuple[T, ProviderResponse]:
        self._check_simulated_failures(request)

        prompt_text = " ".join(m.content for m in request.messages)

        if issubclass(response_model, ExtractedClaim):
            instance = self._synthesize_claim(prompt_text)
        elif issubclass(response_model, ForkAnalysisResult):
            instance = self._synthesize_forks(prompt_text)
        elif issubclass(response_model, DualModelReviewOutput):
            instance = self._synthesize_review(prompt_text)
        else:
            raise SchemaValidationError(f"MockProvider does not support model {response_model.__name__}")

        raw_json = instance.model_dump_json()

        resp = ProviderResponse(
            provider_name=self.provider_name,
            model_id=request.model_id,
            raw_content=raw_json,
            structured_data=instance.model_dump(),
            latency_ms=self.simulated_latency_ms,
            token_usage=TokenUsage(prompt_tokens=120, completion_tokens=85, total_tokens=205),
            status=ProviderStatus.DEGRADED if self.degraded else ProviderStatus.HEALTHY,
        )

        return instance, resp  # type: ignore

    async def health_check(self) -> ProviderStatus:
        if self.force_rate_limit:
            return ProviderStatus.RATE_LIMITED
        if self.degraded:
            return ProviderStatus.DEGRADED
        return ProviderStatus.HEALTHY

    def _check_simulated_failures(self, request: ProviderRequest) -> None:
        if self.force_timeout or request.timeout_seconds <= 0.01:
            raise ProviderTimeoutError(
                f"Request to {self.provider_name} timed out after {request.timeout_seconds}s.",
                details={"timeout_seconds": request.timeout_seconds},
            )
        if self.force_rate_limit:
            raise ProviderRateLimitError(
                f"Rate limit exceeded (HTTP 429) on {self.provider_name}.",
                details={"status_code": 429},
            )
        if self.force_malformed_json:
            raise SchemaValidationError(
                f"Model response was unparseable or corrupted JSON.",
                details={"raw": "{malformed_json:"},
            )

    def _synthesize_claim(self, prompt: str) -> ExtractedClaim:
        prompt_lower = prompt.lower()

        if "massive rally very soon" in prompt_lower or ("tech stocks" in prompt_lower and "soon" in prompt_lower):
            return ExtractedClaim(
                direction=DirectionEnum.BULLISH,
                claim_summary="General speculative rally in tech equities",
                raw_statement_excerpt=prompt,
                confidence_language=ConfidenceLanguageEnum.HYPERBOLIC,
                is_falsifiable=False,
                falsifiability_score=0.15,
                company_name=None,
                ticker=None,
                target_metric=None,
                time_horizon=None,
                entry_condition=None,
                exit_condition=None,
                invalidation_criteria=[],
                stated_rationale=["Broad market momentum"],
                unstated_assumptions=["Unspecified monetary tailwinds"],
            )

        if "tesla" in prompt_lower or "tsla" in prompt_lower:
            return ExtractedClaim(
                company_name="Tesla, Inc.",
                ticker="TSLA",
                direction=DirectionEnum.BULLISH,
                claim_summary="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
                raw_statement_excerpt="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling.",
                target_metric="$400",
                time_horizon="end of 2026",
                entry_condition="Robotaxi autonomy platform deployment",
                exit_condition=None,
                invalidation_criteria=[
                    InvalidationCriteria(
                        metric_or_trigger="Robotaxi commercial launch not achieved",
                        invalidation_threshold="0 operational commercial cities",
                        time_boundary="Q4 2026",
                        observable_source="SEC 10-K / Regulatory filings",
                    )
                ],
                stated_rationale=["Robotaxi autonomy scaling"],
                unstated_assumptions=["FSD regulatory approval across multiple jurisdictions"],
                confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
                is_falsifiable=True,
                falsifiability_score=0.85,
            )

        if "delta" in prompt_lower and "travel" in prompt_lower:
            return ExtractedClaim(
                company_name="Delta",
                ticker=None,
                direction=DirectionEnum.BULLISH,
                claim_summary="Delta record summer travel demand",
                raw_statement_excerpt=prompt,
                target_metric=None,
                time_horizon="summer",
                confidence_language=ConfidenceLanguageEnum.MODERATE,
                is_falsifiable=False,
                falsifiability_score=0.25,
            )

        if "apple" in prompt_lower:
            target = "20%" if "20%" in prompt else None
            horizon = "fiscal 2026" if "2026" in prompt else None
            return ExtractedClaim(
                company_name="Apple",
                ticker="AAPL" if "AAPL" in prompt else None,
                direction=DirectionEnum.BULLISH,
                claim_summary="Apple services revenue growth expansion",
                raw_statement_excerpt=prompt,
                target_metric=target,
                time_horizon=horizon,
                confidence_language=ConfidenceLanguageEnum.ASSERTIVE,
                is_falsifiable=True,
                falsifiability_score=0.70,
                invalidation_criteria=[
                    InvalidationCriteria(
                        metric_or_trigger="Services revenue growth YoY",
                        invalidation_threshold="< 10%",
                        time_boundary="fiscal 2026",
                        observable_source="Apple SEC 10-K",
                    )
                ],
            )

        return ExtractedClaim(
            direction=DirectionEnum.NEUTRAL,
            claim_summary="Unspecified financial observation",
            raw_statement_excerpt=prompt[:300],
            confidence_language=ConfidenceLanguageEnum.MODERATE,
            is_falsifiable=False,
            falsifiability_score=0.10,
        )

    def _synthesize_forks(self, prompt: str) -> ForkAnalysisResult:
        claim_id = str(uuid4())

        fork1 = InterpretationFork(
            fork_title="Primary Segment Core Expansion",
            scenario_description="Thesis relies strictly on automotive hardware unit volumes and core COGS deflation.",
            plausibility_weight=0.60,
            implied_direction=DirectionEnum.BULLISH,
            key_assumptions=["Battery cell manufacturing costs fall > 15%", "Delivery volume growth > 20%"],
            distinguishing_evidence_needed="SEC 10-Q Segment Gross Margin Excluding Regulatory Credits",
        )

        fork2 = InterpretationFork(
            fork_title="Full Autonomous Network Valuation",
            scenario_description="Thesis requires Robotaxi high-margin software revenue contribution to justify multiple.",
            plausibility_weight=0.40,
            implied_direction=DirectionEnum.VOLATILITY,
            key_assumptions=["Unsupervised autonomy deployed by Q4 2026", "Zero human safety driver required"],
            distinguishing_evidence_needed="NHTSA / State DMV Autonomous Commercial Ride-Hail Licensing Disclosures",
        )

        return ForkAnalysisResult(
            claim_id=claim_id,
            ambiguity_detected=True,
            ambiguity_reasons=[
                "Multiple business segments could drive target multiple (Auto vs Energy vs Software).",
                "Unanchored milestone definitions for commercial autonomy.",
            ],
            forks=[fork1, fork2],
            distinguishing_data_checklist=[
                "Quarterly 10-Q Automotive ex-credit gross margin",
                "State DMV autonomous ride-hail permit approvals",
            ],
        )

    def _synthesize_review(self, prompt: str) -> DualModelReviewOutput:
        claim = self._synthesize_claim(prompt)

        if self.disagree_with_primary:
            return DualModelReviewOutput(
                primary_claim=claim,
                reviewer_critique_notes="Reviewer disputes falsifiability score: invalidation threshold lacks explicit GAAP/non-GAAP metric.",
                is_concordant=False,
                disagreement_reasons=[
                    "Disagreement on whether 'scaling' constitutes a verifiable entry condition.",
                    "Reviewer assesses confidence as HYPERBOLIC rather than ASSERTIVE.",
                ],
                spawned_forks=[
                    InterpretationFork(
                        fork_title="Disputed Valuation Multiple Interpretation",
                        scenario_description="Reviewer hypothesis: Growth multiple is unsustainable without recurring SaaS revenue.",
                        plausibility_weight=0.50,
                        implied_direction=DirectionEnum.BEARISH,
                        distinguishing_evidence_needed="Quarterly recurring FSD subscription revenue disclosure.",
                    )
                ],
            )

        return DualModelReviewOutput(
            primary_claim=claim,
            reviewer_critique_notes="Reviewer confirmed invalidation criteria and null-fidelity.",
            is_concordant=True,
            disagreement_reasons=[],
            spawned_forks=[],
        )
