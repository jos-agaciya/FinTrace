"""Formatting utilities for grounding evidence delivered to LLM prompts.

CRITICAL INVARIANTS:
1. Clearly demarcates user-submitted statements from retrieved external evidence.
2. Formats verbatim excerpt, source name, URL, and publication date.
3. Preserves missing source metadata honestly without fabrication.
4. Enforces strict character and item limits to prevent prompt bloat.
5. Exposes truncation status transparently through metadata.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from claim_extraction.schemas import EvidenceItem


def format_evidence_bundle(
    evidence: Optional[List[EvidenceItem]],
    max_items: int = 5,
    max_total_chars: int = 4000,
) -> Tuple[str, Dict[str, Any]]:
    """Format external retrieved evidence items safely for model prompts with strict length gating.

    Args:
        evidence: Optional list of retrieved EvidenceItem instances.
        max_items: Maximum number of evidence items to include in prompt.
        max_total_chars: Maximum aggregate characters allowed for evidence excerpt text.

    Returns:
        Tuple of (formatted_prompt_block, telemetry_metadata_dict).
    """
    if not evidence:
        return (
            "=== RETRIEVED GROUNDING EVIDENCE (EXTERNAL DOCUMENTS) ===\n"
            "No external grounding evidence was provided. Evaluate claim solely based on source text.",
            {
                "evidence_items_total": 0,
                "evidence_items_included": 0,
                "evidence_truncated": False,
                "evidence_chars_included": 0,
            },
        )

    lines = ["=== RETRIEVED GROUNDING EVIDENCE (EXTERNAL DOCUMENTS) ==="]
    included_count = 0
    total_chars = 0
    is_truncated = False

    for idx, item in enumerate(evidence[:max_items], 1):
        source_name = item.source_name or "Unknown Source"
        source_url = item.source_url or "Not specified"
        source_type = (
            item.source_type.value
            if hasattr(item.source_type, "value")
            else str(item.source_type)
        )
        pub_date = (
            item.published_at.isoformat() if item.published_at else "Not specified"
        )
        text = item.text_content.strip()

        item_text = (
            f"[Evidence Item {idx}]\n"
            f"- Source: {source_name} (Type: {source_type})\n"
            f"- Reference URL: {source_url}\n"
            f"- Publication Date: {pub_date}\n"
            f"- Verbatim Content Excerpt: \"{text}\"\n"
        )

        if total_chars + len(item_text) > max_total_chars:
            is_truncated = True
            break

        lines.append(item_text)
        total_chars += len(item_text)
        included_count += 1

    if len(evidence) > max_items or is_truncated:
        is_truncated = True
        lines.append(
            f"[NOTE: Evidence bundle truncated. Included {included_count} of {len(evidence)} total items "
            f"within prompt character boundary of {max_total_chars} chars.]"
        )

    formatted_text = "\n".join(lines)
    meta = {
        "evidence_items_total": len(evidence),
        "evidence_items_included": included_count,
        "evidence_truncated": is_truncated,
        "evidence_chars_included": total_chars,
    }
    return formatted_text, meta
