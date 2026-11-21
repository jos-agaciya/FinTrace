"""Abstract base class defining the provider-independent LLM interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple, Type, TypeVar

from pydantic import BaseModel

from providers.schemas import ProviderRequest, ProviderResponse, ProviderStatus

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract interface for all model providers (Groq, Gemini, and offline Mock).

    Ensures that downstream AI engines (extractor, falsifiability compiler,
    interpretation fork engine, and dual-model reviewer) interact with models
    through a unified, provider-agnostic contract.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'groq', 'gemini', 'mock')."""
        pass

    @abstractmethod
    async def generate_text(self, request: ProviderRequest) -> ProviderResponse:
        """Execute a text-generation request and return a standardized ProviderResponse.

        Args:
            request: Provider-independent request payload.

        Returns:
            ProviderResponse containing model response, latency, and telemetry.

        Raises:
            ProviderTimeoutError: When execution exceeds timeout_seconds.
            ProviderRateLimitError: When provider returns rate limit (HTTP 429).
            ProviderError: For general provider failures.
        """
        pass

    @abstractmethod
    async def generate_structured(
        self, request: ProviderRequest, response_model: Type[T]
    ) -> Tuple[T, ProviderResponse]:
        """Execute a structured extraction request and parse output into a Pydantic model.

        Args:
            request: Provider-independent request payload.
            response_model: Expected Pydantic model type.

        Returns:
            Tuple of (parsed_pydantic_instance, ProviderResponse).

        Raises:
            SchemaValidationError: When model output fails Pydantic validation.
            ProviderError: For provider-level failures.
        """
        pass

    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        """Perform a lightweight operational status check.

        Returns:
            ProviderStatus indicating current operational readiness.
        """
        pass
