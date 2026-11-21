"""Core data contracts for financial claim extraction, falsifiability compilation, and evidence.

CRITICAL INVARIANTS:
1. Missing information MUST remain None (JSON null) or explicitly marked as not stated.
2. Never invent target prices, time horizons, entry conditions, exit conditions, or invalidation triggers.
3. Keep source facts and retrieved evidence distinct from AI-generated interpretations.
4. Provider metadata must never be confused with evidence provenance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class DirectionEnum(str, Enum):
    """Direction of the financial thesis."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    VOLATILITY = "VOLATILITY"


class ConfidenceLanguageEnum(str, Enum):
    """Categorisation of author linguistic assertiveness."""
    HIGHLY_HEDGED = "HIGHLY_HEDGED"      # e.g., "could possibly", "might perhaps"
    MODERATE = "MODERATE"                # e.g., "expected to", "likely"
    ASSERTIVE = "ASSERTIVE"              # e.g., "will achieve", "target is"
    HYPERBOLIC = "HYPERBOLIC"            # e.g., "guaranteed", "cannot fail", "to the moon"


class RiskIndicatorType(str, Enum):
    """Observable risk and persuasion features in financial claims."""
    URGENCY_WORDING = "URGENCY_WORDING"
    GUARANTEED_RETURN_LANGUAGE = "GUARANTEED_RETURN_LANGUAGE"
    UNSUPPORTED_CERTAINTY = "UNSUPPORTED_CERTAINTY"
    MISSING_RISK_DISCLOSURE = "MISSING_RISK_DISCLOSURE"


class RiskIndicator(BaseModel):
    """Observable persuasion feature or missing risk context in a claim.

    IMPORTANT: These are review prompts ('needs verification'), NEVER proof of fraud,
    manipulation, guilt, or intentional wrongdoing.
    """
    indicator_type: RiskIndicatorType = Field(
        ...,
        description="Category of observable persuasion or risk feature."
    )
    label: str = Field(
        default="Risk indicator",
        description="Neutral display label ('Risk indicator', 'Needs verification', 'Missing risk context')."
    )
    matched_phrase: Optional[str] = Field(
        default=None,
        description="Verbatim matched phrase in text, or None if representing an inferred absence."
    )
    explanation: str = Field(
        ...,
        description="Factual, neutral explanation of why this feature warrants review."
    )
    is_inferred_absence: bool = Field(
        default=False,
        description="True if representing an absence in the submitted post rather than matched text."
    )
    review_prompt: str = Field(
        ...,
        description="Neutral prompt guiding the investor to inspect external evidence or missing context."
    )


class SourceTypeEnum(str, Enum):
    """Type of source document from which evidence was retrieved."""
    SEC_FILING = "SEC_FILING"                        # 10-K, 10-Q, 8-K
    EARNINGS_CALL_TRANSCRIPT = "EARNINGS_CALL_TRANSCRIPT"
    REGULATORY_DISCLOSURE = "REGULATORY_DISCLOSURE"
    AUDITED_FINANCIALS = "AUDITED_FINANCIALS"
    NEWS_ARTICLE = "NEWS_ARTICLE"
    RESEARCH_NOTE = "RESEARCH_NOTE"
    OTHER = "OTHER"


class InvalidationCriteria(BaseModel):
    """Concrete conditions under which a financial claim is falsified.

    If any criteria attribute is not stated in the source text, it must remain None.
    """
    metric_or_trigger: str = Field(
        ...,
        description="Verifiable metric, price or event that invalidates the claim."
    )
    invalidation_threshold: Optional[str] = Field(
        default=None,
        description="Quantitative boundary, e.g. '< $140' or 'EPS drop > 5%'. Must be None if not stated."
    )
    time_boundary: Optional[str] = Field(
        default=None,
        description="Boundary date or period when invalidation is checked. Must be None if not stated."
    )
    observable_source: Optional[str] = Field(
        default=None,
        description="Source where metric is verified (e.g. SEC EDGAR 10-Q). Must be None if not stated."
    )


class EvidenceItem(BaseModel):
    """Retrieved evidence document snippet for claim grounding.

    Evidence retrieval is strictly decoupled from model providers.
    The AI engine consumes evidence supplied by the evidence/backend layer.
    """
    evidence_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the evidence item."
    )
    source_name: str = Field(
        ...,
        description="Human-readable source name (e.g. 'SEC Form 10-K', 'Reuters')."
    )
    source_url: str = Field(
        ...,
        description="Canonical URL, accession number, or permalink of the source document."
    )
    source_type: SourceTypeEnum = Field(
        default=SourceTypeEnum.OTHER,
        description="Classification of the evidence source document."
    )
    published_at: Optional[datetime] = Field(
        default=None,
        description="Publication timestamp of the evidence document, when available."
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when evidence was retrieved into the system."
    )
    text_content: str = Field(
        ...,
        description="Verbatim excerpt or relevant content used for grounding."
    )
    provenance_hash: Optional[str] = Field(
        default=None,
        description="Cryptographic hash (e.g. SHA-256) of the source excerpt for tamper-evidence."
    )
    provenance_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific provenance (e.g. SEC accession number, page/item number)."
    )


class ExtractedClaim(BaseModel):
    """Structured extraction of a financial claim and its falsifiability criteria.

    All unstated fields default strictly to None to prevent hallucination.
    """
    claim_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique UUID for this extracted claim."
    )
    company_name: Optional[str] = Field(
        default=None,
        description="Target company name, or None if not stated."
    )
    ticker: Optional[str] = Field(
        default=None,
        description="Stock ticker symbol (e.g. 'AAPL'), or None if not stated."
    )
    direction: DirectionEnum = Field(
        ...,
        description="Market direction of the claim: BULLISH, BEARISH, NEUTRAL, or VOLATILITY."
    )
    claim_summary: str = Field(
        ...,
        description="Concise synthesis of the core claim."
    )
    raw_statement_excerpt: str = Field(
        ...,
        description="Exact quotation from source text."
    )
    target_metric: Optional[str] = Field(
        default=None,
        description="Explicit price or financial target (e.g. '$180'). Must be None if not stated."
    )
    time_horizon: Optional[str] = Field(
        default=None,
        description="Explicit timeframe (e.g. 'Q3 2025', '6 months'). Must be None if not stated."
    )
    entry_condition: Optional[str] = Field(
        default=None,
        description="Stated prerequisite to activate thesis. Must be None if not stated."
    )
    exit_condition: Optional[str] = Field(
        default=None,
        description="Stated profit-taking or termination point. Must be None if not stated."
    )
    invalidation_criteria: List[InvalidationCriteria] = Field(
        default_factory=list,
        description="List of concrete falsification criteria. Never invented."
    )
    stated_rationale: List[str] = Field(
        default_factory=list,
        description="Explicit arguments provided by the author."
    )
    unstated_assumptions: List[str] = Field(
        default_factory=list,
        description="Implicit premises identified by analysis."
    )
    confidence_language: ConfidenceLanguageEnum = Field(
        ...,
        description="Author linguistic assertiveness category."
    )
    is_falsifiable: bool = Field(
        ...,
        description="True only if concrete invalidation criteria exist."
    )
    falsifiability_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Quantitative score from 0.0 (unfalsifiable hype) to 1.0 (rigorous falsifiable thesis)."
    )
    risk_indicators: List[RiskIndicator] = Field(
        default_factory=list,
        description="Observable persuasion and risk indicators detected in claim text."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional non-speculative extraction metadata."
    )
