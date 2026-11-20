"""Dual-model review and independent critique coordinator.

CRITICAL INVARIANTS:
1. Two-model agreement is NEVER treated as proof of factual truth.
2. The consensus warning is mandatory and cannot be bypassed.
3. Disagreement between primary and reviewer models spawns uncertainty interpretation forks.
4. Degraded single-provider operation is explicitly marked; never pretend dual-model review occurred.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from claim_extraction.evidence_formatter import format_evidence_bundle
from claim_extraction.schemas import EvidenceItem, ExtractedClaim
from interpretation.schemas import InterpretationFork
from orchestration.schemas import DualModelReviewInput, DualModelReviewOutput
from providers.base import BaseLLMProvider
from providers.schemas import LLMMessage, MessageRole, ProviderRequest, ProviderStatus
from validation.errors import ProviderError


class DualModelReviewer:
    """Coordinates primary extraction and independent reviewer critique."""

    def __init__(
        self,
        primary_provider: BaseLLMProvider,
        reviewer_provider: Optional[BaseLLMProvider] = None,
    ):
        self.primary = primary_provider
        self.reviewer = reviewer_provider

    async def review(self, input_data: DualModelReviewInput) -> DualModelReviewOutput:
        """Execute independent reviewer model critique over primary claim."""
        claim = input_data.claim
        evidence = input_data.evidence

        # Determine actual extractor provider and model (H-2 / H-3)
        extractor_prov = (
            input_data.extractor_provider
            or claim.metadata.get("provider_name")
            or getattr(self.primary, "provider_name", "unknown")
        )
        extractor_mod = (
            input_data.extractor_model
            or claim.metadata.get("model_id")
            or "unknown"
        )

        # Check if reviewer provider is present
        if not self.reviewer:
            return DualModelReviewOutput(
                primary_claim=claim,
                reviewer_critique_notes="DEGRADED OPERATION: Independent reviewer model was unavailable. Dual-model verification NOT performed.",
                is_concordant=False,
                independent_review_valid=False,
                review_mode="DEGRADED_SINGLE_PROVIDER",
                extractor_provider=extractor_prov,
                extractor_model=extractor_mod,
                reviewer_provider="none",
                reviewer_model="none",
                disagreement_reasons=["Reviewer unavailable - degraded single-provider mode."],
                spawned_forks=[],
            )

        # Check health of reviewer
        try:
            status = await self.reviewer.health_check()
            if status in [ProviderStatus.UNAVAILABLE, ProviderStatus.CIRCUIT_OPEN]:
                return DualModelReviewOutput(
                    primary_claim=claim,
                    reviewer_critique_notes="DEGRADED OPERATION: Reviewer circuit open or unavailable.",
                    is_concordant=False,
                    independent_review_valid=False,
                    review_mode="DEGRADED_SINGLE_PROVIDER",
                    extractor_provider=extractor_prov,
                    extractor_model=extractor_mod,
                    reviewer_provider=getattr(self.reviewer, "provider_name", "unknown"),
                    reviewer_model="unknown",
                    disagreement_reasons=["Secondary provider health check failed."],
                    spawned_forks=[],
                )
        except Exception:
            return DualModelReviewOutput(
                primary_claim=claim,
                reviewer_critique_notes="DEGRADED OPERATION: Secondary provider communication failed.",
                is_concordant=False,
                independent_review_valid=False,
                review_mode="DEGRADED_SINGLE_PROVIDER",
                extractor_provider=extractor_prov,
                extractor_model=extractor_mod,
                reviewer_provider=getattr(self.reviewer, "provider_name", "unknown"),
                reviewer_model="unknown",
                disagreement_reasons=["Secondary provider unreachable."],
                spawned_forks=[],
            )

        # Format evidence bundle safely with limits (H-1)
        evidence_text, evidence_meta = format_evidence_bundle(evidence)

        system_instruction = (
            "You are the FinTrace Independent Model Reviewer. "
            "Act as a skeptical, adversarial auditor of the primary model's claim extraction.\n"
            "MANDATORY INVARIANTS:\n"
            "- Inspect for hallucinated targets, unstated conditions, or unjustified direction.\n"
            "- Cross-reference the claim against the provided external grounding evidence.\n"
            "- If you disagree on falsifiability, identify specific discrepancy reasons.\n"
            "- Model agreement does not prove correctness."
        )

        user_content = (
            f"=== PRIMARY EXTRACTED CLAIM TO AUDIT ===\n"
            f"{claim.model_dump_json(indent=2)}\n\n"
            f"{evidence_text}"
        )

        request = ProviderRequest(
            model_id="independent-reviewer-v1",
            messages=[
                LLMMessage(role=MessageRole.SYSTEM, content=system_instruction),
                LLMMessage(role=MessageRole.USER, content=user_content),
            ],
            temperature=0.1,
            response_schema=DualModelReviewOutput.model_json_schema(),
            metadata={"claim_id": claim.claim_id},
        )

        try:
            review_out, response = await self.reviewer.generate_structured(request, DualModelReviewOutput)

            rev_prov = response.provider_name or getattr(self.reviewer, "provider_name", "unknown")
            rev_mod = response.model_id or getattr(self.reviewer, "default_model", "unknown")

            # Detect same-provider self-review (H-2)
            # Normalize provider identifiers (e.g. "gemini" vs "gemini")
            ext_clean = extractor_prov.lower().split(":")[0].strip()
            rev_clean = rev_prov.lower().split(":")[0].strip()
            is_same_provider = (ext_clean == rev_clean) and (ext_clean != "unknown")

            # Format notes and review mode
            review_mode = "DEGRADED_SAME_PROVIDER" if is_same_provider else "INDEPENDENT_DUAL_MODEL"
            notes = review_out.reviewer_critique_notes or ""
            if is_same_provider:
                notes = (
                    f"[DEGRADED SAME-PROVIDER SELF-REVIEW: Claim was extracted and reviewed by the same provider "
                    f"('{rev_clean}') following primary failover. Independent dual-model validation is invalid.] {notes}"
                )

            return review_out.model_copy(
                update={
                    "extractor_provider": extractor_prov,
                    "extractor_model": extractor_mod,
                    "reviewer_provider": rev_prov,
                    "reviewer_model": rev_mod,
                    "independent_review_valid": not is_same_provider,
                    "review_mode": review_mode,
                    "reviewer_critique_notes": notes,
                    "metadata": {
                        "reviewer_latency_ms": response.latency_ms,
                        "reviewer_token_usage": response.token_usage.model_dump(),
                        "evidence_summary": evidence_meta,
                        "same_provider_self_review": is_same_provider,
                    },
                }
            )

        except Exception as e:
            return DualModelReviewOutput(
                primary_claim=claim,
                reviewer_critique_notes=f"DEGRADED OPERATION: Independent review failed: {str(e)}",
                is_concordant=False,
                independent_review_valid=False,
                review_mode="DEGRADED_SINGLE_PROVIDER",
                extractor_provider=extractor_prov,
                extractor_model=extractor_mod,
                reviewer_provider=getattr(self.reviewer, "provider_name", "unknown"),
                reviewer_model="unknown",
                disagreement_reasons=[f"Reviewer execution exception: {str(e)}"],
                spawned_forks=[],
            )
