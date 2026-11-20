"""Interpretation Fork Engine for analyzing financial thesis ambiguity.

CRITICAL INVARIANTS:
1. Detects genuine semantic, temporal, and numeric ambiguities.
2. Synthesizes distinct alternative scenario interpretations.
3. Every fork is explicitly labelled as an 'AI-Generated Interpretation (Hypothesis)'.
4. Never asserts that an interpretation represents confirmed author intent.
"""

from __future__ import annotations

from typing import Any, List, Optional

from claim_extraction.schemas import ExtractedClaim
from interpretation.schemas import ForkAnalysisResult, InterpretationFork
from providers.base import BaseLLMProvider
from providers.schemas import LLMMessage, MessageRole, ProviderRequest
from validation.errors import ProviderError


class InterpretationForkEngine:
    """Service detecting ambiguities and generating alternative scenario forks."""

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def analyze_forks(
        self,
        claim_or_input: Any = None,
        claim: Optional[ExtractedClaim] = None,
        max_forks: int = 3,
        **kwargs: Any,
    ) -> ForkAnalysisResult:
        """Analyze claim for semantic ambiguity and generate alternative readings.

        Accepts either a ForkAnalysisInput DTO, positional ExtractedClaim, or keyword arguments.
        """
        if claim is not None:
            target_claim = claim
        elif hasattr(claim_or_input, "claim"):
            target_claim = claim_or_input.claim
            max_forks = getattr(claim_or_input, "max_forks", max_forks)
        else:
            target_claim = claim_or_input

        ambiguities: List[str] = []

        # Deterministic ambiguity scanning
        summary_lower = target_claim.claim_summary.lower()

        # Check for vague timeframes
        if not target_claim.time_horizon or any(w in summary_lower for w in ["soon", "near term", "eventually", "long run"]):
            ambiguities.append("Unanchored or vague temporal horizon ('soon'/'near term').")

        # Check for multi-meaning financial metrics
        if "margin" in summary_lower and not any(m in summary_lower for m in ["gross", "operating", "net", "ebitda"]):
            ambiguities.append("Unspecified margin definition (gross vs operating vs net margin).")

        if "growth" in summary_lower and not any(g in summary_lower for g in ["revenue", "earnings", "volume", "users"]):
            ambiguities.append("Ambiguous growth metric (unit deliveries vs dollar revenue).")

        if not target_claim.entry_condition and not target_claim.exit_condition:
            ambiguities.append("Thesis lacks explicit trigger prerequisites and termination boundaries.")

        has_ambiguity = len(ambiguities) > 0

        # LLM Request for Scenario Generation
        system_instruction = (
            "You are the FinTrace Interpretation Fork Engine. "
            "Your task is to identify plausible alternative semantic readings of genuine ambiguities within an author's stated thesis.\n"
            "MANDATORY INVARIANTS:\n"
            "- Focus strictly on textual/measurement ambiguities: metric definitions (gross vs operating vs net margin), "
            "unanchored horizons ('soon', 'near term'), baseline comparisons (YoY vs QoQ), or unstated operational scope.\n"
            "- DO NOT invent generic external macroeconomic or geopolitical risk scenarios (e.g. 'Global recession occurs', "
            "'Tariff war escalates', 'Broad market crash') unless the author's statement explicitly hinges on them.\n"
            "- If the thesis statement is explicit, unambiguous, and leaves no room for multiple readings, return ambiguity_detected=false "
            "and an empty forks list ([]). Do NOT manufacture artificial forks for unambiguous claims.\n"
            "- Label every interpretation as an AI-generated hypothesis, NEVER as confirmed author intent.\n"
            "- State the exact distinguishing evidence or future disclosure required to resolve each fork.\n"
            "- Distribute plausibility weights realistically (summing <= 1.0)."
        )

        user_content = (
            f"Claim Summary: {target_claim.claim_summary}\n"
            f"Direction: {target_claim.direction.value}\n"
            f"Target: {target_claim.target_metric or 'Not stated'}\n"
            f"Horizon: {target_claim.time_horizon or 'Not stated'}\n"
            f"Detected Ambiguities: {', '.join(ambiguities) if ambiguities else 'None flagged'}\n"
            f"Max Forks: {max_forks}"
        )

        request = ProviderRequest(
            model_id="fork-engine-v1",
            messages=[
                LLMMessage(role=MessageRole.SYSTEM, content=system_instruction),
                LLMMessage(role=MessageRole.USER, content=user_content),
            ],
            temperature=0.2,
            response_schema=ForkAnalysisResult.model_json_schema(),
            metadata={"claim_id": target_claim.claim_id},
        )

        try:
            fork_result, response = await self.provider.generate_structured(request, ForkAnalysisResult)
        except Exception as e:
            raise ProviderError(f"Fork engine provider failed: {str(e)}") from e

        # Ensure claim_id and ambiguity checks match
        validated_forks = []
        for fork in fork_result.forks[:max_forks]:
            clean_fork = fork.model_copy(
                update={"provenance_label": "AI-Generated Interpretation (Hypothesis)"}
            )
            validated_forks.append(clean_fork)

        # Merge detected ambiguities
        all_ambiguities = list(set(ambiguities + fork_result.ambiguity_reasons))

        return ForkAnalysisResult(
            claim_id=target_claim.claim_id,
            ambiguity_detected=has_ambiguity or fork_result.ambiguity_detected,
            ambiguity_reasons=all_ambiguities,
            forks=validated_forks,
            distinguishing_data_checklist=fork_result.distinguishing_data_checklist,
            metadata={
                "provider_name": response.provider_name,
                "model_id": response.model_id,
                "fallback_used": response.raw_metadata.get("fallback_used", False),
                "degraded": response.raw_metadata.get("degraded", False),
                "latency_ms": response.latency_ms,
                "token_usage": response.token_usage.model_dump(),
            },
        )
