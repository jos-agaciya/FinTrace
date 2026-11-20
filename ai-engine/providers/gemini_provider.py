"""Google Gemini LLM Provider implementation for FinTrace AI Engine.

CRITICAL INVARIANTS:
1. Native integration with Google GenAI SDK (google.genai.Client).
2. Robust async execution and timeout enforcement.
3. Strict mapping of API errors (429, timeouts, authentication) to FinTrace AIEngineError hierarchy.
4. Schema-enforced structured generation with Pydantic validation.
5. Preserves null values faithfully; never extrapolates unstated targets.
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
    from google import genai
    from google.genai import errors as genai_errors
    from google.genai import types
except ImportError:
    genai = None
    genai_errors = None
    types = None

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

logger = logging.getLogger("fintrace.ai.providers.gemini")
T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseLLMProvider):
    """Secondary provider and independent reviewer utilizing Google Gemini models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gemini-3.5-flash",
        timeout_seconds: float = 15.0,
        client: Optional[Any] = None,
    ):
        """Initialize Gemini provider.

        Args:
            api_key: Optional API key. Defaults to GEMINI_API_KEY environment variable.
            default_model: Default Gemini model ID (e.g. 'gemini-2.5-flash').
            timeout_seconds: Network call timeout boundary.
            client: Optional injected genai.Client instance (for testing/mocking).
        """
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.default_model = os.getenv("GEMINI_MODEL", default_model)
        self.timeout_seconds = timeout_seconds

        if client is not None:
            self._client = client
        elif genai is not None and self._api_key:
            self._client = genai.Client(api_key=self._api_key)
        else:
            self._client = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def name(self) -> str:
        return f"gemini:{self.default_model}"

    def _ensure_client(self) -> Any:
        """Validate that the genai.Client is ready for calls."""
        if self._client is not None:
            return self._client
        if genai is None:
            raise ProviderError("Google GenAI SDK is not installed. Install with 'pip install google-genai'.")
        if not self._api_key:
            self._api_key = os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            raise ProviderAuthenticationError(
                "Gemini API key is missing. Set GEMINI_API_KEY in environment or pass to constructor."
            )
        self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _prepare_prompt(self, messages: List[LLMMessage]) -> Tuple[Optional[str], str]:
        """Separate system instruction and synthesize prompt contents for Gemini."""
        system_parts = []
        user_parts = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_parts.append(msg.content)
            elif msg.role == MessageRole.USER:
                user_parts.append(msg.content)
            elif msg.role == MessageRole.ASSISTANT:
                user_parts.append(f"Assistant: {msg.content}")

        system_instruction = "\n\n".join(system_parts) if system_parts else None
        contents = "\n\n".join(user_parts) if user_parts else ""
        return system_instruction, contents

    async def generate_text(self, request: ProviderRequest) -> ProviderResponse:
        """Execute text completion via Gemini Async API."""
        client = self._ensure_client()
        model_id = (
            self.default_model
            if (not request.model_id or request.model_id in ("default", "claim-extractor-v1", "fork-engine-v1", "independent-reviewer-v1"))
            else request.model_id
        )
        timeout = request.timeout_seconds or self.timeout_seconds
        system_instruction, contents = self._prepare_prompt(request.messages)

        config_kwargs: Dict[str, Any] = {
            "temperature": request.temperature,
        }
        if request.max_tokens:
            config_kwargs["max_output_tokens"] = request.max_tokens
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_kwargs) if types else None

        start_time = time.perf_counter()
        try:
            call_coro = client.aio.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )
            resp = await asyncio.wait_for(call_coro, timeout=timeout)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            content = resp.text or ""
            usage_meta = getattr(resp, "usage_metadata", None)
            usage = TokenUsage(
                prompt_tokens=getattr(usage_meta, "prompt_token_count", 0) or 0,
                completion_tokens=getattr(usage_meta, "candidates_token_count", 0) or 0,
                total_tokens=getattr(usage_meta, "total_token_count", 0) or 0,
            )

            return ProviderResponse(
                provider_name="gemini",
                raw_content=content,
                model_id=model_id,
                latency_ms=round(latency_ms, 2),
                token_usage=usage,
                metadata={"gemini_response_id": getattr(resp, "response_id", None)},
            )

        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                f"Gemini request timed out after {timeout:.1f}s for model '{model_id}'."
            ) from exc
        except Exception as exc:
            self._map_gemini_exception(exc, model_id)

    async def generate_structured(
        self, request: ProviderRequest, response_model: Type[T]
    ) -> Tuple[T, ProviderResponse]:
        """Execute structured JSON completion using Gemini response_schema / JSON mode."""
        client = self._ensure_client()
        model_id = (
            self.default_model
            if (not request.model_id or request.model_id in ("default", "claim-extractor-v1", "fork-engine-v1", "independent-reviewer-v1"))
            else request.model_id
        )
        timeout = request.timeout_seconds or self.timeout_seconds
        system_instruction, contents = self._prepare_prompt(request.messages)

        schema_json_str = json.dumps(response_model.model_json_schema())
        json_instruction = (
            f"\nYou MUST respond with a single, valid JSON object conforming to the schema:\n"
            f"{schema_json_str}\n"
            f"Do not include markdown code fences (```json) or conversational text."
        )

        full_system_instruction = (
            f"{system_instruction}\n\n{json_instruction}"
            if system_instruction
            else json_instruction
        )

        config_kwargs: Dict[str, Any] = {
            "temperature": request.temperature,
            "response_mime_type": "application/json",
            "system_instruction": full_system_instruction,
        }
        if request.max_tokens:
            config_kwargs["max_output_tokens"] = request.max_tokens

        config = types.GenerateContentConfig(**config_kwargs) if types else None

        start_time = time.perf_counter()
        try:
            call_coro = client.aio.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )
            resp = await asyncio.wait_for(call_coro, timeout=timeout)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            content = resp.text or ""
            usage_meta = getattr(resp, "usage_metadata", None)
            usage = TokenUsage(
                prompt_tokens=getattr(usage_meta, "prompt_token_count", 0) or 0,
                completion_tokens=getattr(usage_meta, "candidates_token_count", 0) or 0,
                total_tokens=getattr(usage_meta, "total_token_count", 0) or 0,
            )

            provider_resp = ProviderResponse(
                provider_name="gemini",
                raw_content=content,
                model_id=model_id,
                latency_ms=round(latency_ms, 2),
                token_usage=usage,
                metadata={"gemini_response_id": getattr(resp, "response_id", None)},
            )

            # Parse and validate with Pydantic
            try:
                clean_json_str = content.strip()
                if clean_json_str.startswith("```"):
                    clean_json_str = clean_json_str.strip("`").strip()
                    if clean_json_str.lower().startswith("json"):
                        clean_json_str = clean_json_str[4:].strip()

                parsed_model = response_model.model_validate_json(clean_json_str)
                return parsed_model, provider_resp

            except (ValidationError, json.JSONDecodeError) as val_err:
                raise SchemaValidationError(
                    f"Gemini response for model '{model_id}' failed schema validation: {str(val_err)}",
                    details={"raw_output": content[:1000], "error": str(val_err)},
                ) from val_err

        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                f"Gemini structured request timed out after {timeout:.1f}s for model '{model_id}'."
            ) from exc
        except Exception as exc:
            self._map_gemini_exception(exc, model_id)

    async def health_check(self) -> ProviderStatus:
        """Lightweight health check assessing Gemini configuration."""
        if not self._api_key:
            return ProviderStatus.UNAVAILABLE
        try:
            self._ensure_client()
            return ProviderStatus.HEALTHY
        except Exception:
            return ProviderStatus.UNAVAILABLE

    def _map_gemini_exception(self, exc: Exception, model_id: str) -> None:
        """Map Google GenAI SDK exceptions to FinTrace AIEngineError hierarchy."""
        if isinstance(exc, (SchemaValidationError, ProviderTimeoutError)):
            raise exc

        exc_str = str(exc).lower()

        # Check status or code
        code = getattr(exc, "code", None)
        status = getattr(exc, "status", None)

        if code == 429 or status == 429 or "429" in exc_str or "resource_exhausted" in exc_str or "quota" in exc_str:
            raise ProviderRateLimitError(
                f"Gemini rate limit exceeded on model '{model_id}': {str(exc)}",
                details={"model": model_id, "original_error": str(exc)},
            ) from exc

        if "timeout" in exc_str or "deadline" in exc_str:
            raise ProviderTimeoutError(
                f"Gemini API timeout on model '{model_id}': {str(exc)}",
                details={"model": model_id, "original_error": str(exc)},
            ) from exc

        if code in (401, 403) or status in (401, 403) or "unauthenticated" in exc_str or "permission_denied" in exc_str or "invalid api key" in exc_str:
            raise ProviderAuthenticationError(
                f"Gemini authentication failed: {str(exc)}",
                details={"model": model_id, "original_error": str(exc)},
            ) from exc

        raise ProviderError(
            f"Gemini provider error on model '{model_id}': {str(exc)}",
            details={"model": model_id, "original_error": str(exc)},
        ) from exc
