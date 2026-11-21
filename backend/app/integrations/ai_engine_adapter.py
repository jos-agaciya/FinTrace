"""Adapter bridging the FinTrace FastAPI backend to the autonomous AI Engine.

Consumes FinTraceAIEngine from ai-engine/facade.py and engine_interface.py
without duplicating prompt templates, model routing, or circuit breaker logic.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fintrace.backend.ai_engine_adapter")

# Add ai-engine to sys.path if not present
ai_engine_dir = Path(__file__).resolve().parents[3] / "ai-engine"
if str(ai_engine_dir) not in sys.path and ai_engine_dir.exists():
    sys.path.insert(0, str(ai_engine_dir))

try:
    from engine_interface import (
        ClaimExtractionInput,
        DecisionRecord,
        DecisionSensitivityInput,
        DualModelReviewInput,
        DualModelReviewOutput,
        ExtractedClaim,
        ForkAnalysisInput,
        FullPipelineAnalysisResult,
        UserAssessmentInput,
    )
    from claim_extraction.schemas import EvidenceItem, SourceTypeEnum
    from facade import FinTraceAIEngine
    AI_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Failed to import FinTraceAIEngine from ai-engine: {e}. Fallback to mock providers.")
    AI_ENGINE_AVAILABLE = False


class AIEngineAdapter:
    """Unified bridge for backend services to invoke FinTraceAIEngine."""

    _instance: Optional["AIEngineAdapter"] = None

    def __init__(self, engine: Optional[Any] = None):
        if engine:
            self.engine = engine
        elif AI_ENGINE_AVAILABLE:
            try:
                # Initialize from environment credentials (.env)
                self.engine = FinTraceAIEngine.from_env()
                logger.info("FinTraceAIEngine successfully initialized from environment.")
            except Exception as e:
                logger.warning(f"FinTraceAIEngine.from_env() failed: {e}. Initializing default mock facade.")
                self.engine = FinTraceAIEngine()
        else:
            self.engine = None

    @classmethod
    def get_instance(cls) -> "AIEngineAdapter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_available(self) -> bool:
        return self.engine is not None

    async def analyze_claim_end_to_end(
        self,
        raw_text: str,
        source_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        retrieved_evidence: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[FullPipelineAnalysisResult]:
        """Runs the complete 4-stage Decision Robustness Compiler pipeline in the AI Engine."""
        if not self.engine:
            return None

        evidence_items: List[EvidenceItem] = []
        if retrieved_evidence:
            for item in retrieved_evidence:
                try:
                    source_type = SourceTypeEnum.FINANCIAL_PORTAL
                    publisher = str(item.get("publisher", "")).upper()
                    if "SEC" in publisher:
                        source_type = SourceTypeEnum.SEC_FILING
                    elif "NSE" in publisher or "BSE" in publisher:
                        source_type = SourceTypeEnum.REGULATORY_DISCLOSURE

                    evidence_items.append(
                        EvidenceItem(
                            source_name=item.get("publisher") or item.get("title") or "Corporate Filing",
                            source_url=item.get("source_url") or "https://fintrace.ai/disclosure",
                            source_type=source_type,
                            text_content=item.get("content_summary") or item.get("title") or "Statutory corporate disclosure.",
                            publication_date=item.get("publication_date"),
                        )
                    )
                except Exception as ex:
                    logger.debug(f"Skipping malformed evidence item: {ex}")

        input_data = ClaimExtractionInput(
            raw_text=raw_text,
            source_url=source_url,
            published_at=published_at or datetime.now(timezone.utc),
            retrieved_evidence=evidence_items,
            metadata=metadata or {},
        )

        return await self.engine.analyze_end_to_end(input_data)

    def explain_decision_sensitivity(
        self,
        initial_confidence: float,
        initial_allocation: float,
        initial_thesis: str,
        revised_confidence: float,
        revised_allocation: float,
        revised_thesis: str,
        selected_fork_titles: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Invokes the DecisionSensitivityEngine to analyze shift between pre and post decisions."""
        if not self.engine:
            return None

        try:
            # Map 0-100 to 1.0-5.0 scale enforcing DecisionRecord ge=1.0, le=5.0 bounds
            conf_initial_clamped = max(min(float(initial_confidence) / 20.0, 5.0), 1.0)
            conf_revised_clamped = max(min(float(revised_confidence) / 20.0, 5.0), 1.0)

            input_data = DecisionSensitivityInput(
                initial_decision=DecisionRecord(
                    confidence_level=conf_initial_clamped,
                    hypothetical_allocation_pct=initial_allocation,
                    written_rationale=initial_thesis,
                ),
                revised_decision=DecisionRecord(
                    confidence_level=conf_revised_clamped,
                    hypothetical_allocation_pct=revised_allocation,
                    written_rationale=revised_thesis,
                ),
                selected_interpretation_forks=[],
            )
            explanation = self.engine.explain_sensitivity(input_data)
            return {
                "summary_of_change": explanation.summary_of_change,
                "confidence_delta": explanation.confidence_delta,
                "allocation_delta_pct": explanation.allocation_delta_pct,
                "unexplained_variance_flag": explanation.unexplained_variance_flag,
                "uncertainties": explanation.uncertainties_and_limitations,
            }
        except Exception as e:
            logger.warning(f"explain_sensitivity failed in AI Engine: {e}")
            return None

    def generate_practice_claim(
        self,
        template_category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generates a synthetic practice claim using the CounterfactualClaimGenerator."""
        if not self.engine:
            return None

        try:
            res = self.engine.generate_practice_claim(template_category=template_category)
            return {
                "practice_claim_id": res.practice_claim.practice_claim_id,
                "claim_text": res.practice_claim.claim_text,
                "template_category": res.metadata.get("template_category", template_category or "VAGUE_TIMEFRAME"),
                "target_entity": res.practice_claim.synthetic_company_name,
                "preserved_flaws": [p.property_name for p in res.preserved_properties],
                "learning_focus": res.evaluation_rubric_focus,
            }
        except Exception as e:
            logger.warning(f"generate_practice_claim failed in AI Engine: {e}")
            return None

    def get_health_status(self) -> Dict[str, Any]:
        """Returns health status and telemetry from AI Engine."""
        if not self.engine:
            return {"status": "unavailable", "reason": "AIEngine module not loaded"}
        try:
            return {"status": "operational", **self.engine.get_health_status()}
        except Exception as e:
            return {"status": "degraded", "error": str(e)}
