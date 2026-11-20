"""Fallback Manager coordinating multi-provider resiliency and failover.

CRITICAL INVARIANTS:
1. Implements BaseLLMProvider so subsystems can consume it transparently.
2. Transparent failover from primary (Groq) to secondary (Gemini) on 429/timeouts/outages.
3. Degraded operational states are explicitly flagged in responses (never masqueraded as normal).
4. Both-provider exhaustion raises AllProvidersFailedError with complete diagnostic history.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel

from fallback.circuit_breaker import CircuitBreaker, CircuitState
from providers.base import BaseLLMProvider
from providers.schemas import ProviderRequest, ProviderResponse, ProviderStatus
from validation.errors import (
    AllProvidersFailedError,
    CircuitBreakerOpenError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SchemaValidationError,
)

logger = logging.getLogger("fintrace.ai.fallback_manager")
T = TypeVar("T", bound=BaseModel)


class FallbackManager(BaseLLMProvider):
    """Orchestrates resilient primary-to-secondary model failovers protected by circuit breakers."""

    def __init__(
        self,
        primary_provider: BaseLLMProvider,
        secondary_provider: Optional[BaseLLMProvider] = None,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 60.0,
    ):
        """Initialize the fallback manager.

        Args:
            primary_provider: Main LLM provider (e.g. GroqProvider).
            secondary_provider: Optional fallback provider (e.g. GeminiProvider).
            failure_threshold: Consecutive failures to trip breaker to OPEN.
            recovery_timeout_seconds: Seconds before testing HALF_OPEN state.
        """
        self.primary_provider = primary_provider
        self.secondary_provider = secondary_provider

        self.primary_circuit = CircuitBreaker(
            provider_name=getattr(primary_provider, "provider_name", "primary"),
            failure_threshold=failure_threshold,
            recovery_timeout_seconds=recovery_timeout_seconds,
        )

        self.secondary_circuit = (
            CircuitBreaker(
                provider_name=getattr(secondary_provider, "provider_name", "secondary"),
                failure_threshold=failure_threshold,
                recovery_timeout_seconds=recovery_timeout_seconds,
            )
            if secondary_provider
            else None
        )

    @property
    def provider_name(self) -> str:
        sec_name = getattr(self.secondary_provider, "provider_name", "none")
        return f"resilient({self.primary_circuit.provider_name}->{sec_name})"

    @property
    def name(self) -> str:
        return self.provider_name

    async def generate_text(self, request: ProviderRequest) -> ProviderResponse:
        """Execute text generation via primary provider, falling back to secondary on failure."""
        primary_error: Optional[Exception] = None

        # 1. Attempt Primary Provider
        try:
            response = await self.primary_circuit.call(
                self.primary_provider.generate_text, request
            )
            response.raw_metadata["fallback_used"] = False
            response.raw_metadata["degraded"] = False
            return response

        except (
            CircuitBreakerOpenError,
            ProviderRateLimitError,
            ProviderTimeoutError,
            ProviderAuthenticationError,
            ProviderError,
        ) as exc:
            primary_error = exc
            logger.warning(
                f"Primary provider [{self.primary_provider.provider_name}] failed: {exc}. "
                f"Evaluating failover to secondary provider."
            )

        # 2. Attempt Secondary Provider if available
        if self.secondary_provider and self.secondary_circuit:
            try:
                response = await self.secondary_circuit.call(
                    self.secondary_provider.generate_text, request
                )
                logger.info(
                    f"Failover successful: secondary provider [{self.secondary_provider.provider_name}] "
                    f"fulfilled text request after primary failed."
                )
                response.raw_metadata["fallback_used"] = True
                response.raw_metadata["degraded"] = True
                response.raw_metadata["primary_provider"] = self.primary_provider.provider_name
                response.raw_metadata["primary_failure_reason"] = str(primary_error)
                return response

            except Exception as secondary_exc:
                logger.error(
                    f"Secondary provider [{self.secondary_provider.provider_name}] also failed: {secondary_exc}. "
                    f"All configured providers exhausted."
                )
                raise AllProvidersFailedError(
                    f"All AI providers failed. Primary [{self.primary_provider.provider_name}]: {primary_error}; "
                    f"Secondary [{self.secondary_provider.provider_name}]: {secondary_exc}",
                    details={
                        "primary_provider": self.primary_provider.provider_name,
                        "primary_error": str(primary_error),
                        "primary_circuit": self.primary_circuit.get_diagnostics(),
                        "secondary_provider": self.secondary_provider.provider_name,
                        "secondary_error": str(secondary_exc),
                        "secondary_circuit": self.secondary_circuit.get_diagnostics(),
                    },
                ) from secondary_exc

        raise AllProvidersFailedError(
            f"Primary provider [{self.primary_provider.provider_name}] failed and no fallback is configured. "
            f"Error: {primary_error}",
            details={
                "primary_provider": self.primary_provider.provider_name,
                "primary_error": str(primary_error),
                "primary_circuit": self.primary_circuit.get_diagnostics(),
            },
        ) from primary_error

    async def generate_structured(
        self, request: ProviderRequest, response_model: Type[T]
    ) -> Tuple[T, ProviderResponse]:
        """Execute structured generation via primary provider, falling back to secondary on failure."""
        primary_error: Optional[Exception] = None

        # 1. Attempt Primary Provider
        try:
            parsed, response = await self.primary_circuit.call(
                self.primary_provider.generate_structured, request, response_model
            )
            response.raw_metadata["fallback_used"] = False
            response.raw_metadata["degraded"] = False
            return parsed, response

        except (
            CircuitBreakerOpenError,
            ProviderRateLimitError,
            ProviderTimeoutError,
            ProviderAuthenticationError,
            ProviderError,
            SchemaValidationError,
        ) as exc:
            primary_error = exc
            logger.warning(
                f"Primary provider [{self.primary_provider.provider_name}] structured generation failed: {exc}. "
                f"Evaluating failover to secondary provider."
            )

        # 2. Attempt Secondary Provider if available
        if self.secondary_provider and self.secondary_circuit:
            try:
                parsed, response = await self.secondary_circuit.call(
                    self.secondary_provider.generate_structured, request, response_model
                )
                logger.info(
                    f"Failover successful: secondary provider [{self.secondary_provider.provider_name}] "
                    f"fulfilled structured request after primary failed."
                )
                response.raw_metadata["fallback_used"] = True
                response.raw_metadata["degraded"] = True
                response.raw_metadata["primary_provider"] = self.primary_provider.provider_name
                response.raw_metadata["primary_failure_reason"] = str(primary_error)
                return parsed, response

            except Exception as secondary_exc:
                logger.error(
                    f"Secondary provider [{self.secondary_provider.provider_name}] also failed: {secondary_exc}. "
                    f"All configured providers exhausted."
                )
                raise AllProvidersFailedError(
                    f"All AI providers failed. Primary [{self.primary_provider.provider_name}]: {primary_error}; "
                    f"Secondary [{self.secondary_provider.provider_name}]: {secondary_exc}",
                    details={
                        "primary_provider": self.primary_provider.provider_name,
                        "primary_error": str(primary_error),
                        "primary_circuit": self.primary_circuit.get_diagnostics(),
                        "secondary_provider": self.secondary_provider.provider_name,
                        "secondary_error": str(secondary_exc),
                        "secondary_circuit": self.secondary_circuit.get_diagnostics(),
                    },
                ) from secondary_exc

        raise AllProvidersFailedError(
            f"Primary provider [{self.primary_provider.provider_name}] failed and no fallback is configured. "
            f"Error: {primary_error}",
            details={
                "primary_provider": self.primary_provider.provider_name,
                "primary_error": str(primary_error),
                "primary_circuit": self.primary_circuit.get_diagnostics(),
            },
        ) from primary_error

    async def health_check(self) -> ProviderStatus:
        """Evaluate combined health of primary and secondary providers."""
        primary_healthy = False
        try:
            status = await self.primary_provider.health_check()
            primary_healthy = (status == ProviderStatus.HEALTHY) and (self.primary_circuit.state != CircuitState.OPEN)
        except Exception:
            primary_healthy = False

        if primary_healthy:
            return ProviderStatus.HEALTHY

        if self.secondary_provider and self.secondary_circuit:
            try:
                sec_status = await self.secondary_provider.health_check()
                if sec_status == ProviderStatus.HEALTHY and self.secondary_circuit.state != CircuitState.OPEN:
                    return ProviderStatus.DEGRADED
            except Exception:
                pass

        return ProviderStatus.UNAVAILABLE

    def get_health_status(self) -> Dict[str, Any]:
        """Telemetry snapshot of provider health and circuit states."""
        status: Dict[str, Any] = {
            "primary": self.primary_circuit.get_diagnostics(),
        }
        if self.secondary_circuit:
            status["secondary"] = self.secondary_circuit.get_diagnostics()
        return status
