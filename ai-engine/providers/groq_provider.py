"""Groq LLM Provider implementation for FinTrace AI Engine.

CRITICAL INVARIANTS:
1. Production integration with Groq Async API client.
2. Strict mapping of HTTP/SDK exceptions to FinTrace AIEngineError hierarchy.
3. Strict JSON schema validation for structured claim extraction and interpretation.
4. Preserves null values faithfully; never extrapolates unstated targets.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

try:
    import groq
    from groq import AsyncGroq
except ImportError:
    groq = None
    AsyncGroq = None

from providers.base import BaseLLMProvider
from providers.schemas import (
    LLMMessage,
    MessageRole,
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
    TokenUsage,
)
from validation.errors import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SchemaValidationError,
)

logger = logging.getLogger("fintrace.ai.providers.groq")
T = TypeVar("T", bound=BaseModel)


class GroqProvider(BaseLLMProvider):
    """Primary high-throughput provider utilizing Groq Llama models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "openai/gpt-oss-120b",
        timeout_seconds: float = 25.0,
        max_retries: int = 2,
        client: Optional[Any] = None,
    ):
        """Initialize Groq provider.

        Args:
            api_key: Optional API key. Defaults to GROQ_API_KEY environment variable.
            default_model: Default Groq model ID.
            timeout_seconds: Network call timeout boundary.
            max_retries: Internal client retries.
            client: Optional injected AsyncGroq client (for testing/mocking).
        """
        self._api_key = api_key or os.getenv("GROQ_API_KEY")
        self.default_model = os.getenv("GROQ_MODEL", default_model)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        if client is not None:
            self._client = client
        elif AsyncGroq is not None and self._api_key:
            self._client = AsyncGroq(
                api_key=self._api_key,
                max_retries=self.max_retries,
                timeout=self.timeout_seconds,
            )
        else:
            self._client = None

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def name(self) -> str:
        return f"groq:{self.default_model}"

    def _ensure_client(self) -> Any:
        """Validate that the AsyncGroq client is ready for calls."""
        if self._client is not None:
            return self._client
        if AsyncGroq is None:
            raise ProviderError("Groq SDK is not installed. Install with 'pip install groq'.")
        if not self._api_key:
            self._api_key = os.getenv("GROQ_API_KEY")
        if not self._api_key:
            raise ProviderAuthenticationError(
                "Groq API key is missing. Set GROQ_API_KEY in environment or pass to constructor."
            )
        self._client = AsyncGroq(
            api_key=self._api_key,
            max_retries=self.max_retries,
            timeout=self.timeout_seconds,
        )
        return self._client

    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """Format domain LLM messages to Groq chat completions format."""
        formatted = []
        for msg in messages:
            role_str = "user"
            if msg.role == MessageRole.SYSTEM:
                role_str = "system"
            elif msg.role == MessageRole.ASSISTANT:
                role_str = "assistant"
            formatted.append({"role": role_str, "content": msg.content})
        return formatted

    async def generate_text(self, request: ProviderRequest) -> ProviderResponse:
        """Execute text completion via Groq Async API."""
        client = self._ensure_client()
        model_id = (
            self.default_model
            if (not request.model_id or request.model_id in ("default", "claim-extractor-v1", "fork-engine-v1", "independent-reviewer-v1"))
            else request.model_id
        )
        messages = self._format_messages(request.messages)
        timeout = request.timeout_seconds or self.timeout_seconds

        start_time = time.perf_counter()
        try:
            call_coro = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens or 2048,
            )
            completion = await asyncio.wait_for(call_coro, timeout=timeout)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            content = completion.choices[0].message.content or ""
            usage = TokenUsage(
                prompt_tokens=completion.usage.prompt_tokens if completion.usage else 0,
                completion_tokens=completion.usage.completion_tokens if completion.usage else 0,
                total_tokens=completion.usage.total_tokens if completion.usage else 0,
            )

            return ProviderResponse(
                provider_name="groq",
                raw_content=content,
                model_id=completion.model or model_id,
                latency_ms=round(latency_ms, 2),
                token_usage=usage,
                metadata={"groq_id": getattr(completion, "id", None)},
            )

        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                f"Groq request timed out after {timeout:.1f}s for model '{model_id}'."
            ) from exc
        except Exception as exc:
            self._map_groq_exception(exc, model_id)

    async def generate_structured(
        self, request: ProviderRequest, response_model: Type[T]
    ) -> Tuple[T, ProviderResponse]:
        """Execute structured JSON completion and parse into the requested Pydantic model."""
        client = self._ensure_client()
        model_id = (
            self.default_model
            if (not request.model_id or request.model_id in ("default", "claim-extractor-v1", "fork-engine-v1", "independent-reviewer-v1"))
            else request.model_id
        )
        timeout = request.timeout_seconds or self.timeout_seconds

        # Enforce JSON instruction for Groq's json_object mode
        messages = self._format_messages(request.messages)
        json_instruction = (
            f"\nYou MUST respond with a single, valid JSON object strictly conforming to "
            f"the {response_model.__name__} schema:\n"
            f"{json.dumps(response_model.model_json_schema())}\n"
            f"Do not include markdown codeblocks or preamble. Output raw JSON only."
        )

        # Inject into system or last user message
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] += json_instruction
        else:
            messages.insert(0, {"role": "system", "content": json_instruction})

        start_time = time.perf_counter()
        try:
            call_coro = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens or 2048,
                response_format={"type": "json_object"},
            )
            completion = await asyncio.wait_for(call_coro, timeout=timeout)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            content = completion.choices[0].message.content or ""
            usage = TokenUsage(
                prompt_tokens=completion.usage.prompt_tokens if completion.usage else 0,
                completion_tokens=completion.usage.completion_tokens if completion.usage else 0,
                total_tokens=completion.usage.total_tokens if completion.usage else 0,
            )

            provider_resp = ProviderResponse(
                provider_name="groq",
                raw_content=content,
                model_id=completion.model or model_id,
                latency_ms=round(latency_ms, 2),
                token_usage=usage,
                metadata={"groq_id": getattr(completion, "id", None)},
            )

            # Parse and validate with Pydantic
            try:
                # Strip any accidental ```json ... ``` wrapper if present
                clean_json_str = content.strip()
                if clean_json_str.startswith("```"):
                    clean_json_str = clean_json_str.strip("`").strip()
                    if clean_json_str.lower().startswith("json"):
                        clean_json_str = clean_json_str[4:].strip()

                parsed_model = response_model.model_validate_json(clean_json_str)
                return parsed_model, provider_resp

            except (ValidationError, json.JSONDecodeError) as val_err:
                raise SchemaValidationError(
                    f"Groq response for model '{model_id}' failed schema validation: {str(val_err)}",
                    details={"raw_output": content[:1000], "error": str(val_err)},
                ) from val_err

        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                f"Groq structured request timed out after {timeout:.1f}s for model '{model_id}'."
            ) from exc
        except Exception as exc:
            self._map_groq_exception(exc, model_id)

    async def health_check(self) -> ProviderStatus:
        """Lightweight health check assessing Groq configuration."""
        if not self._api_key:
            return ProviderStatus.UNAVAILABLE
        try:
            client = self._ensure_client()
            return ProviderStatus.HEALTHY
        except Exception:
            return ProviderStatus.UNAVAILABLE

    def _map_groq_exception(self, exc: Exception, model_id: str) -> None:
        """Map Groq SDK exceptions to FinTrace AIEngineError hierarchy."""
        if isinstance(exc, (SchemaValidationError, ProviderTimeoutError)):
            raise exc

        exc_str = str(exc).lower()

        # Check Groq RateLimitError
        if groq and isinstance(exc, groq.RateLimitError) or "429" in exc_str or "rate limit" in exc_str:
            raise ProviderRateLimitError(
                f"Groq rate limit exceeded on model '{model_id}': {str(exc)}",
                details={"model": model_id, "original_error": str(exc)},
            ) from exc

        # Check Groq APITimeoutError
        if groq and isinstance(exc, groq.APITimeoutError) or "timeout" in exc_str:
            raise ProviderTimeoutError(
                f"Groq API timeout on model '{model_id}': {str(exc)}",
                details={"model": model_id, "original_error": str(exc)},
            ) from exc

        # Check Groq AuthenticationError
        if groq and isinstance(exc, groq.AuthenticationError) or "401" in exc_str or "invalid api key" in exc_str:
            raise ProviderAuthenticationError(
                f"Groq authentication failed: {str(exc)}",
                details={"model": model_id, "original_error": str(exc)},
            ) from exc

        # Default fallback
        raise ProviderError(
            f"Groq provider error on model '{model_id}': {str(exc)}",
            details={"model": model_id, "original_error": str(exc)},
        ) from exc
