"""Claim extraction pipeline orchestrating LLM providers and falsifiability compilation."""

from __future__ import annotations

from typing import Any, List, Optional

from claim_extraction.compiler import FalsifiabilityCompiler
from claim_extraction.evidence_formatter import format_evidence_bundle
from claim_extraction.risk_indicators import RiskIndicatorExtractor
from claim_extraction.schemas import EvidenceItem, ExtractedClaim
from providers.base import BaseLLMProvider
from providers.schemas import LLMMessage, MessageRole, ProviderRequest
from validation.errors import (
    AllProvidersFailedError,
    CircuitBreakerOpenError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SchemaValidationError,
)


class ClaimExtractor:
    """Service responsible for structured claim extraction and falsifiability compilation."""

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self.compiler = FalsifiabilityCompiler()
        self.risk_extractor = RiskIndicatorExtractor()

    async def extract_claim(
        self,
        raw_text_or_input: Any = None,
        raw_text: Optional[str] = None,
        source_url: Optional[str] = None,
        author: Optional[str] = None,
        retrieved_evidence: Optional[List[EvidenceItem]] = None,
        **kwargs: Any,
    ) -> ExtractedClaim:
        """Extract structured claim and compile falsifiability criteria.

        Accepts either a ClaimExtractionInput DTO, positional string, or keyword arguments.
        """
        evidence_items = retrieved_evidence or []
        if raw_text is not None:
            text = raw_text
        elif hasattr(raw_text_or_input, "raw_text"):
            text = raw_text_or_input.raw_text
            source_url = getattr(raw_text_or_input, "source_url", source_url)
            author = getattr(raw_text_or_input, "author", author)
            if hasattr(raw_text_or_input, "retrieved_evidence") and not evidence_items:
                evidence_items = raw_text_or_input.retrieved_evidence
        else:
            text = str(raw_text_or_input or "")

        evidence_text, evidence_meta = format_evidence_bundle(evidence_items)

        system_instruction = (
            "You are the FinTrace Financial Claim Understanding Engine. "
            "Extract structured financial theses strictly adhering to falsifiability principles.\n"
            "MANDATORY INVARIANTS:\n"
            "- If a target price, percentage, horizon, or condition is NOT stated, return null.\n"
            "- Never extrapolate or invent unstated targets.\n"
            "- Distinguish explicit author rationale from implicit premises.\n"
            "- Extract concrete invalidation triggers (what falsifies this thesis).\n"
            "- Distinguish user-submitted claims from external grounding evidence."
        )

        user_content = (
            f"=== USER-SUBMITTED CLAIM TO EVALUATE ===\n"
            f"Source Text: \"{text}\""
        )
        if source_url:
            user_content += f"\nSource URL: {source_url}"
        if author:
            user_content += f"\nAuthor: {author}"

        user_content += f"\n\n{evidence_text}"

        request = ProviderRequest(
            model_id="claim-extractor-v1",
            messages=[
                LLMMessage(role=MessageRole.SYSTEM, content=system_instruction),
                LLMMessage(role=MessageRole.USER, content=user_content),
            ],
            temperature=0.0,
            response_schema=ExtractedClaim.model_json_schema(),
            metadata={"source": "claim_extraction_pipeline"},
        )

        try:
            extracted, response = await self.provider.generate_structured(request, ExtractedClaim)
        except (
            AllProvidersFailedError,
            ProviderAuthenticationError,
            ProviderRateLimitError,
            ProviderTimeoutError,
            SchemaValidationError,
            CircuitBreakerOpenError,
        ):
            raise
        except Exception as e:
            raise ProviderError(f"Claim extraction provider failed: {str(e)}") from e

        # Apply Falsifiability Compiler pass
        is_falsifiable, score, compiled_criteria = self.compiler.compile_falsifiability(extracted)

        # Apply Risk and Persuasion Indicators pass
        indicators = self.risk_extractor.extract_indicators(text, extracted)

        # Build clean validated output with compiled scores and execution provenance (H-3)
        merged_metadata = {
            **extracted.metadata,
            "provider_name": response.provider_name,
            "model_id": response.model_id,
            "fallback_used": response.raw_metadata.get("fallback_used", False),
            "degraded": response.raw_metadata.get("degraded", False),
            "primary_provider": response.raw_metadata.get("primary_provider"),
            "primary_failure_reason": response.raw_metadata.get("primary_failure_reason"),
            "latency_ms": response.latency_ms,
            "evidence_summary": evidence_meta,
            "risk_indicators_count": len(indicators),
        }

        validated_claim = extracted.model_copy(
            update={
                "is_falsifiable": is_falsifiable,
                "falsifiability_score": score,
                "invalidation_criteria": compiled_criteria,
                "risk_indicators": indicators,
                "raw_statement_excerpt": text[:500] if not extracted.raw_statement_excerpt else extracted.raw_statement_excerpt,
                "metadata": merged_metadata,
            }
        )

        return validated_claim
