import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.assessment import AssessmentModel
from backend.app.models.claim import ClaimModel
from backend.app.repositories.assessment_repository import AssessmentRepository
from backend.app.repositories.claim_repository import ClaimRepository
from backend.app.utils.scoring import DeterministicRubricScorer
from backend.app.schemas.common import AssessmentStage
from backend.app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    DimensionScores,
    AssessmentComparisonResponse,
    AssessmentPromptResponse,
    AssessmentDimensionPrompt,
    AssessmentQuestionOption
)


class AssessmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AssessmentRepository(db)
        self.claim_repo = ClaimRepository(db)

    def submit_assessment(self, assessment_in: AssessmentCreate) -> AssessmentResponse:
        claim = self.claim_repo.get_by_id(assessment_in.claim_id)
        if not claim:
            raise ValueError(f"Claim {assessment_in.claim_id} not found.")

        # Compute deterministic scores across all 5 dimensions
        dim_scores, total_score, feedback = DeterministicRubricScorer.score_assessment(
            identified_evidence_types=assessment_in.identified_evidence_types,
            distinguished_primary_sources=assessment_in.distinguished_primary_sources,
            identified_missing_specificity=assessment_in.identified_missing_specificity,
            identified_risk_factors=assessment_in.identified_risk_factors,
            recognized_alternative_interpretations=assessment_in.recognized_alternative_interpretations,
            stated_confidence=assessment_in.stated_confidence,
            evidence_backing_level=assessment_in.evidence_backing_level,
            confidence_justification=assessment_in.confidence_justification
        )

        user_responses_payload = {
            "identified_evidence_types": assessment_in.identified_evidence_types,
            "distinguished_primary_sources": assessment_in.distinguished_primary_sources,
            "identified_missing_specificity": assessment_in.identified_missing_specificity,
            "identified_risk_factors": assessment_in.identified_risk_factors,
            "recognized_alternative_interpretations": assessment_in.recognized_alternative_interpretations,
            "stated_confidence": assessment_in.stated_confidence,
            "evidence_backing_level": assessment_in.evidence_backing_level,
            "confidence_justification": assessment_in.confidence_justification,
            "raw_answers": assessment_in.raw_answers
        }

        assessment = AssessmentModel(
            session_id=assessment_in.session_id,
            claim_id=assessment_in.claim_id,
            assessment_stage=assessment_in.assessment_stage.value,
            score_evidence_eval=dim_scores["evidence_evaluation"],
            score_claim_specificity=dim_scores["claim_specificity"],
            score_risk_awareness=dim_scores["risk_awareness"],
            score_assumption_awareness=dim_scores["assumption_awareness"],
            score_confidence_calibration=dim_scores["confidence_calibration"],
            total_score=total_score,
            user_responses=json.dumps(user_responses_payload),
            rubric_feedback=json.dumps(feedback)
        )

        created = self.repository.create(assessment)
        return self._build_response(created)

    def get_assessment(self, assessment_id: str) -> Optional[AssessmentResponse]:
        assessment = self.repository.get_by_id(assessment_id)
        if not assessment:
            return None
        return self._build_response(assessment)

    def get_session_history(self, session_id: str) -> List[AssessmentResponse]:
        items = self.repository.get_by_session(session_id)
        return [self._build_response(a) for a in items]

    def compare_stages(self, session_id: str) -> AssessmentComparisonResponse:
        baseline = self.repository.get_latest_by_stage(session_id, "BASELINE")
        transfer = self.repository.get_latest_by_stage(session_id, "INDEPENDENT_TRANSFER")

        if not baseline or not transfer:
            raise ValueError(
                f"Both BASELINE and INDEPENDENT_TRANSFER assessments required for comparison. "
                f"Found baseline: {baseline is not None}, transfer: {transfer is not None}."
            )

        percentage_point_delta = round(transfer.total_score - baseline.total_score, 1)

        dim_deltas = {
            "evidence_evaluation": round(transfer.score_evidence_eval - baseline.score_evidence_eval, 1),
            "claim_specificity": round(transfer.score_claim_specificity - baseline.score_claim_specificity, 1),
            "risk_awareness": round(transfer.score_risk_awareness - baseline.score_risk_awareness, 1),
            "assumption_awareness": round(transfer.score_assumption_awareness - baseline.score_assumption_awareness, 1),
            "confidence_calibration": round(transfer.score_confidence_calibration - baseline.score_confidence_calibration, 1)
        }

        if percentage_point_delta > 0:
            summary = (
                f"Investor decision evaluation score increased by {percentage_point_delta} percentage points "
                f"from {baseline.total_score:.1f}/100 (baseline) to {transfer.total_score:.1f}/100 (independent transfer). "
                "Demonstrates improved analytical rigor and critical evaluation of financial claims without AI assistance."
            )
        elif percentage_point_delta < 0:
            summary = (
                f"Investor decision evaluation score decreased by {abs(percentage_point_delta)} percentage points "
                f"from {baseline.total_score:.1f}/100 to {transfer.total_score:.1f}/100."
            )
        else:
            summary = f"Investor decision evaluation score remained unchanged at {baseline.total_score:.1f}/100."

        return AssessmentComparisonResponse(
            session_id=session_id,
            baseline_score=baseline.total_score,
            latest_transfer_score=transfer.total_score,
            percentage_point_delta=percentage_point_delta,
            dimension_deltas=dim_deltas,
            comparison_summary=summary
        )

    def get_assessment_prompt(self, stage: AssessmentStage, user_id: Optional[str] = None) -> AssessmentPromptResponse:
        if stage == AssessmentStage.BASELINE:
            claim = self.db.query(ClaimModel).filter(ClaimModel.ticker == "APEX").first()
            if not claim:
                claim = ClaimModel(
                    ticker="APEX",
                    company_name="Apex Dynamics Ltd.",
                    original_claim="Apex Dynamics Ltd. is set to achieve 25% operating margin expansion and 40% EPS growth over the next two fiscal years driven by new cloud enterprise deals and proprietary hardware integration.",
                    source_platform="Social Media Forum / Speculative Note",
                    source_url="https://market-dispatches.internal/apex-margins-growth",
                    provenance_status="USER_PROVIDED",
                    claim_direction="BULLISH",
                    target_value=25.0,
                    target_unit="%",
                    time_horizon="2 fiscal years (unstated contract milestones)",
                    user_id=user_id,
                    evidence_or_rationale="Viral speculative thread asserting enterprise cloud expansion."
                )
                self.db.add(claim)
                self.db.commit()
                self.db.refresh(claim)

            guidance = (
                "Stage 1: Baseline Onboarding. Evaluate this viral financial claim without pre-revealed AI forks or hints. "
                "Assess whether primary statutory evidence backs the assertion, identify missing boundary conditions, "
                "and calibrate your investment conviction against downside risks."
            )
            context = "Unverified viral social post and investment newsletter note without attached statutory disclosures."
        else:
            claim = self.db.query(ClaimModel).filter(ClaimModel.ticker == "NVEC").first()
            if not claim:
                claim = ClaimModel(
                    ticker="NVEC",
                    company_name="Novus Energy Corp.",
                    original_claim="Novus Energy Corp. projected full-year EBITDA will double following European grid interconnectivity approvals, despite pending regulatory tariff renegotiations.",
                    source_platform="Corporate Analyst Dispatch",
                    source_url="https://market-dispatches.internal/novus-energy-ebitda-projection",
                    provenance_status="USER_PROVIDED",
                    claim_direction="BULLISH",
                    target_value=100.0,
                    target_unit="%",
                    time_horizon="Full fiscal year (unstated regulatory milestone dates)",
                    user_id=user_id,
                    evidence_or_rationale="Brokerage note with aggressive forward assumptions and unconfirmed tariff outcomes."
                )
                self.db.add(claim)
                self.db.commit()
                self.db.refresh(claim)

            guidance = (
                "Stage 3: Independent Assessment. Autonomously scrutinize this corporate projection without AI assistance. "
                "Challenge unstated premises, test invalidation criteria, and formulate a calibrated conviction stance."
            )
            context = "Brokerage dispatch with aggressive forward projections and unconfirmed tariff outcomes."

        dimensions = [
            AssessmentDimensionPrompt(
                id="identified_evidence_types",
                name="Evidence Scrutiny",
                description="Depth of inquiry into primary regulatory filings, audited disclosures, and official reports.",
                prompt="Which statutory disclosures and audited filings are strictly required to verify the claim's financial metrics?",
                type="multi_select",
                options=[
                    AssessmentQuestionOption(id="REGULATORY_FILING", label="Audited Annual Report (10-K / Form 20-F)", description="Authoritative statutory audited balance sheet and income statement"),
                    AssessmentQuestionOption(id="COMPANY_DISCLOSURE", label="Quarterly Segment Disclosures (10-Q)", description="Unaudited interim financial metrics and segment operating margins"),
                    AssessmentQuestionOption(id="BOARD_RESOLUTION", label="Material Contract / Board Resolution (8-K / Clause 30)", description="Official corporate disclosure confirming signed commercial contracts"),
                    AssessmentQuestionOption(id="EARNINGS_TRANSCRIPT", label="Earnings Call Transcript & Guidance Q&A", description="Executive management commentary and analyst question records"),
                    AssessmentQuestionOption(id="PRESS_RELEASE", label="Unverified Promotional Press Release", description="Secondary company marketing material without statutory audit certification"),
                    AssessmentQuestionOption(id="UNVERIFIED_COMMENTARY", label="Social Media / Forum Speculation", description="Anonymous commentary, newsletter hype, or message board assertions")
                ]
            ),
            AssessmentDimensionPrompt(
                id="distinguished_primary_sources",
                name="Source Provenance",
                description="Differentiating statutory filings from social commentary, rumours, and promotional claims.",
                prompt="Does this statement originate from an authoritative primary statutory disclosure, or secondary unverified commentary?",
                type="boolean",
                options=[
                    AssessmentQuestionOption(id="true", label="Secondary unverified commentary (Requires independent statutory audit)", description="The claim lacks regulatory filing backing and requires verification before capital allocation"),
                    AssessmentQuestionOption(id="false", label="Primary audited regulatory source (Directly verifiable)", description="The claim is directly grounded in an active statutory disclosure")
                ]
            ),
            AssessmentDimensionPrompt(
                id="identified_missing_specificity",
                name="Horizon Realism & Claim Specificity",
                description="Detecting mismatched timelines between physical catalysts and forecasted target dates.",
                prompt="Which critical boundary conditions, baseline metrics, or time horizons are missing from this claim?",
                type="multi_select",
                options=[
                    AssessmentQuestionOption(id="time_horizon", label="Definite contract delivery / execution milestones", description="Omission of exact dates when enterprise deals will reflect on revenue"),
                    AssessmentQuestionOption(id="baseline_definition", label="Clear margin baseline definition (Gross vs. Operating)", description="Ambiguity whether 25% represents GAAP operating margin or non-GAAP adjusted metric"),
                    AssessmentQuestionOption(id="invalidation_condition", label="Explicit invalidation or falsification threshold", description="Absence of criteria under which the thesis is invalidated"),
                    AssessmentQuestionOption(id="entry_condition", label="Prerequisite capital expenditure or licensing approvals", description="Unstated capital requirements or regulatory clearance prerequisites"),
                    AssessmentQuestionOption(id="exit_condition", label="Downside risk boundaries / stop-loss parameters", description="Lack of clear operational boundaries if enterprise deal churn occurs")
                ]
            ),
            AssessmentDimensionPrompt(
                id="recognized_alternative_interpretations",
                name="Assumption Invalidation",
                description="Capability to identify counterfactual factors and divergent interpretations under varying premises.",
                prompt="Can this projection yield divergent financial interpretations under different operational or macroeconomic assumptions?",
                type="boolean",
                options=[
                    AssessmentQuestionOption(id="true", label="Yes — divergent interpretations exist under varying assumptions", description="e.g. margin compression if deal integration costs escalate or competitive repricing occurs"),
                    AssessmentQuestionOption(id="false", label="No — single deterministic outcome guaranteed if current revenue trajectory holds", description="Thesis assumes direct translation of deal volume into net earnings")
                ]
            ),
            AssessmentDimensionPrompt(
                id="cognitive_calibration",
                name="Cognitive Calibration & Confidence Justification",
                description="Aligning subjective investment conviction with empirical evidence probability.",
                prompt="Calibrate your stated confidence level and articulate a structured justification connecting available evidence, identified missing conditions, and downside risk factors.",
                type="calibration_group",
                options=[
                    AssessmentQuestionOption(id="Execution Delay Risk", label="Enterprise Deal Execution & Integration Delay", description="Extended sales cycles or customer deployment bottlenecks"),
                    AssessmentQuestionOption(id="Margin Compression Risk", label="Cost Inflation / Raw Hardware Margin Dilution", description="Rising component costs compressing gross margins"),
                    AssessmentQuestionOption(id="Regulatory Risk", label="Regulatory & Antitrust Scrutiny", description="Compliance inquiries or delayed certification"),
                    AssessmentQuestionOption(id="Customer Concentration", label="Customer Concentration & Churn Volatility", description="Over-reliance on a few flagship clients"),
                    AssessmentQuestionOption(id="Macro Headwind", label="Macroeconomic Capital Spending Pullback", description="Enterprise IT budget contractions")
                ]
            )
        ]

        return AssessmentPromptResponse(
            stage=stage,
            claim_id=claim.id,
            ticker=claim.ticker,
            company_name=claim.company_name or "Target Entity",
            statement=claim.original_claim,
            time_horizon=claim.time_horizon or "Unspecified",
            source_context=context,
            target_value=claim.target_value,
            target_unit=claim.target_unit,
            guidance=guidance,
            dimensions=dimensions
        )

    def _build_response(self, a: AssessmentModel) -> AssessmentResponse:
        feedback = json.loads(a.rubric_feedback) if isinstance(a.rubric_feedback, str) else a.rubric_feedback
        dim_scores = DimensionScores(
            evidence_evaluation=a.score_evidence_eval,
            claim_specificity=a.score_claim_specificity,
            risk_awareness=a.score_risk_awareness,
            assumption_awareness=a.score_assumption_awareness,
            confidence_calibration=a.score_confidence_calibration,
            invalidation_sensitivity=a.score_assumption_awareness,
            horizon_calibration=a.score_claim_specificity,
            provenance_rigor=a.score_evidence_eval,
            epistemic_calibration=a.score_confidence_calibration
        )

        return AssessmentResponse(
            id=a.id,
            session_id=a.session_id,
            claim_id=a.claim_id,
            assessment_stage=a.assessment_stage,
            score_evidence_eval=a.score_evidence_eval,
            score_claim_specificity=a.score_claim_specificity,
            score_risk_awareness=a.score_risk_awareness,
            score_assumption_awareness=a.score_assumption_awareness,
            score_confidence_calibration=a.score_confidence_calibration,
            total_score=a.total_score,
            dimension_scores=dim_scores,
            rubric_feedback=feedback,
            created_at=a.created_at
        )
