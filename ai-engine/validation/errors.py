"""Standard exception hierarchy for FinTrace AI Engine."""

from typing import Any, Dict, Optional


class AIEngineError(Exception):
    """Base exception for all FinTrace AI Engine failures."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FalsifiabilityValidationError(AIEngineError):
    """Raised when an extracted claim lacks concrete invalidation boundaries."""
    pass


class HallucinationError(AIEngineError):
    """Raised when an AI response asserts figures or criteria absent from source text."""
    pass


class ChronologicalInconsistencyError(AIEngineError):
    """Raised when time horizons precede publication dates or violate temporal causality."""
    pass


class SchemaValidationError(AIEngineError):
    """Raised when model output fails deterministic Pydantic schema validation."""
    pass


class ProviderError(AIEngineError):
    """Raised on LLM provider interaction errors."""
    pass


class ProviderUnavailableError(ProviderError):
    """Raised when live AI provider execution is requested but required credentials are missing."""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when provider request exceeds configured timeout boundary."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised on HTTP 429 rate limit errors from model provider."""
    pass


class ProviderAuthenticationError(ProviderError):
    """Raised on HTTP 401/403 authentication/authorization failures."""
    pass


class CircuitBreakerOpenError(ProviderError):
    """Raised when requests are rejected because the provider circuit breaker is OPEN."""
    pass


class AllProvidersFailedError(ProviderError):
    """Raised when all configured providers (primary and fallbacks) fail or have OPEN circuit breakers."""
    pass


class CounterfactualGenerationError(AIEngineError):
    """Raised when a structurally comparable practice claim cannot be generated safely."""
    pass


class SensitivityAnalysisError(AIEngineError):
    """Raised when decision sensitivity explanation cannot be constructed from supplied inputs."""
    pass


class AssessmentEvaluationError(AIEngineError):
    """Raised when independent assessment evaluation cannot be performed."""
    pass
