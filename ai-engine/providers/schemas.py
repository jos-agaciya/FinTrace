"""Provider request, response, and status contracts.

CRITICAL INVARIANTS:
1. Provider responses encapsulate token metrics, latency, and status without exposing raw credentials.
2. Two-model agreement must NEVER be treated as proof of truth.
3. Provider metadata must not be confused with evidence provenance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of the message author in a chat-based LLM completion."""
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class LLMMessage(BaseModel):
    """A single structured message in an LLM conversation prompt."""
    role: MessageRole = Field(
        ...,
        description="Role of the message: SYSTEM, USER, or ASSISTANT."
    )
    content: str = Field(
        ...,
        description="Text content of the message."
    )


class ProviderRequest(BaseModel):
    """Provider-independent input specification for LLM generation."""
    model_id: str = Field(
        default="default",
        description="Identifier of the target model (e.g. 'llama-3.3-70b-versatile', 'gemini-2.5-flash')."
    )
    messages: List[LLMMessage] = Field(
        ...,
        description="List of conversation turns or instructions."
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature; 0.0 for deterministic, highly focused extraction."
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum tokens to generate, or None for provider default."
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Maximum duration before timing out the request."
    )
    response_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional JSON Schema dictionary for structured output enforcement."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional tracking metadata (request_id, correlation_id, etc.)."
    )


class ProviderStatus(str, Enum):
    """Health and operational status of an AI model provider."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    RATE_LIMITED = "RATE_LIMITED"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    UNAVAILABLE = "UNAVAILABLE"


class TokenUsage(BaseModel):
    """Token consumption statistics for provider request."""
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class ProviderResponse(BaseModel):
    """Standardized wrapper for responses from LLM providers (Groq, Gemini, Mock)."""
    provider_name: str = Field(
        default="unknown",
        description="Name of provider ('groq', 'gemini', 'mock')."
    )
    model_id: str = Field(
        default="default",
        description="Exact model identifier (e.g. 'llama-3.3-70b-versatile', 'gemini-2.5-flash')."
    )
    raw_content: str = Field(
        default="",
        description="Raw string output from model."
    )
    structured_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parsed JSON payload if structured output was requested."
    )
    latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="End-to-end request duration in milliseconds."
    )
    token_usage: TokenUsage = Field(
        default_factory=TokenUsage,
        description="Token telemetry."
    )
    status: ProviderStatus = Field(
        default=ProviderStatus.HEALTHY,
        description="Operational status returned by provider wrapper."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary response metadata (e.g. fallback flags, provider ids)."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of provider response."
    )

    def __init__(self, **data: Any):
        # Backward/convenience compatibility aliases
        if "raw_text" in data and "raw_content" not in data:
            data["raw_content"] = data.pop("raw_text")
        if "model_identifier" in data and "model_id" not in data:
            data["model_id"] = data.pop("model_identifier")
        if "raw_metadata" in data and "metadata" not in data:
            data["metadata"] = data.pop("raw_metadata")
        super().__init__(**data)

    @property
    def raw_text(self) -> str:
        return self.raw_content

    @property
    def model_identifier(self) -> str:
        return self.model_id

    @property
    def raw_metadata(self) -> Dict[str, Any]:
        return self.metadata
