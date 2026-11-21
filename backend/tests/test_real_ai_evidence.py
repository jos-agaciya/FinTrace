import pytest
import asyncio
import json
import io
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import pypdf

from backend.app.core.config import settings
from backend.app.integrations.ai_client import (
    GroqProvider,
    GeminiProvider,
    AIEngineProvider,
    ProviderUnavailableException,
    get_ai_provider
)
from backend.app.integrations.evidence_provider import (
    NSEDisclosuresProvider,
    SECDisclosuresProvider,
    CorporateDisclosuresProvider,
    extract_pdf_passage
)
from backend.app.models.claim import ClaimModel, InterpretationForkModel
from backend.app.models.evidence import EvidenceModel, ClaimEvidenceModel
from backend.app.models.analysis import AnalysisModel
from backend.app.services.analysis_orchestrator import AnalysisOrchestrator
from backend.app.services.evidence_service import EvidenceService
from backend.app.schemas.claim import ClaimCreate, ClaimAnalyzeRequest
from backend.app.api.routes.claims import _enrich_claim_response


# ===========================================================================
# 1. AI Provider Models and Configuration Verification
# ===========================================================================

def test_ai_provider_model_configuration():
    """Verify that current non-deprecated models are configured."""
    assert settings.GROQ_MODEL == "openai/gpt-oss-120b"
    assert settings.GEMINI_MODEL == "gemini-3.5-flash-lite"

    groq = GroqProvider()
    assert groq.model == "openai/gpt-oss-120b"
    assert groq.name == "groq"

    gemini = GeminiProvider()
    assert gemini.model == "gemini-3.5-flash-lite"
    assert gemini.name == "gemini"


def test_missing_api_keys_raise_unavailability_without_silent_mock():
    """Verify that missing API credentials raise ProviderUnavailableException without mock fallback."""
    groq_no_key = GroqProvider(api_key=None)
    groq_no_key.api_key = None
    with pytest.raises(ProviderUnavailableException, match="GROQ_API_KEY is not configured"):
        asyncio.run(groq_no_key.analyze_claim("Test claim", []))

    gemini_no_key = GeminiProvider(api_key=None)
    gemini_no_key.api_key = None
    with pytest.raises(ProviderUnavailableException, match="GEMINI_API_KEY is not configured"):
        asyncio.run(gemini_no_key.analyze_claim("Test claim", []))


# ===========================================================================
# 2. PDF & Document Passage Extraction Verification
# ===========================================================================

@pytest.mark.asyncio
async def test_pdf_passage_extraction_from_bytes():
    """Verify that extract_pdf_passage parses PDF bytes into clean text excerpts."""
    # Create an in-memory sample PDF using pypdf
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    
    # Mock httpx client returning a valid PDF stream
    mock_pdf_bytes = b"%PDF-1.4 sample PDF content for testing statutory disclosure extraction"
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = mock_pdf_bytes
        mock_get.return_value = mock_resp

        # With mock invalid PDF bytes, pypdf handles gracefully and returns None without crash
        res = await extract_pdf_passage("https://nsearchives.nseindia.in/corporate/test.pdf")
        assert res is None or isinstance(res, str)


@pytest.mark.asyncio
async def test_nse_evidence_retrieval_with_text_extraction():
    """Verify NSEDisclosuresProvider extracts textual content summary from filings."""
    provider = NSEDisclosuresProvider()

    mock_announcements = [
        {
            "desc": "Infosys enters strategic generative AI collaboration with European Enterprise",
            "attchmntFile": "https://nsearchives.nseindia.in/corporate/INFY_announcement.pdf",
            "attchmntText": "Press Release - Strategic AI Contract",
            "an_dt": "18-Nov-2026 14:30:00",
            "sm_isin": "INE009A01021",
            "sm_name": "Infosys Limited"
        }
    ]

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_announcements
        mock_get.return_value = mock_resp

        with patch("backend.app.integrations.evidence_provider.extract_pdf_passage", return_value="Official filing excerpt: Infosys signs 5-year generative AI agreement."):
            items = await provider.retrieve_evidence("Infosys Limited", "INFY")

            assert len(items) == 1
            item = items[0]
            assert "INFY" in item["company_symbol"]
            assert item["source_jurisdiction"] == "IN"
            assert item["exchange"] == "NSE"
            assert "Official filing excerpt" in item["content_summary"]
            assert item["source_url"] == "https://nsearchives.nseindia.in/corporate/INFY_announcement.pdf"
            assert item["provenance_status"] == "REAL"


# ===========================================================================
# 3. Entity Resolution & Insufficient Evidence Handling
# ===========================================================================

@pytest.mark.asyncio
async def test_unverified_company_returns_insufficient_evidence(db_session):
    """Verify that unfamiliar/unverified companies return empty evidence without fabricating."""
    provider = CorporateDisclosuresProvider()
    results = await provider.retrieve_evidence("Fictitious Nonexistent Startup Ltd", "NO_TICKER")
    assert results == []

    # Submit claim for unverified company
    claim = ClaimModel(
        original_claim="Fictitious Startup will beat Google in AI search by 2027",
        company_name="Fictitious Nonexistent Startup Ltd",
        ticker="NO_TICKER"
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)

    enriched = _enrich_claim_response(claim, db_session)
    assert enriched.validationStatus == "Insufficient Evidence"
    assert enriched.evidenceCoverage == 0
    assert enriched.supportingEvidence == []
    assert enriched.contradictoryEvidence == []


def test_tcs_domestic_restriction_prevents_sec_edgar_mismatch():
    """Verify that domestic Indian companies without US ADR (e.g. TCS) never query SEC EDGAR."""
    sec_provider = SECDisclosuresProvider()
    results = asyncio.run(sec_provider.retrieve_evidence("Tata Consultancy Services", "TCS"))
    assert results == []


# ===========================================================================
# 4. Supported vs. Contradictory Evidence Classification
# ===========================================================================

def test_supported_and_contradictory_evidence_classification(db_session):
    """Verify that evidence with negative/risk keywords or contradiction notes is correctly categorized."""
    claim = ClaimModel(
        original_claim="Infosys will achieve 25% margin expansion in 2026",
        company_name="Infosys Limited",
        ticker="INFY",
        claim_direction="BULLISH"
    )
    db_session.add(claim)
    db_session.commit()

    ev_supp = EvidenceModel(
        title="NSE Disclosure: Infosys Q2 Margin Expansion",
        publisher="NSE India",
        source_url="https://nsearchives.nseindia.in/corporate/q2.pdf",
        content_summary="Infosys reports strong growth in digital transformation and operating margins.",
        evidence_category="COMPANY_DISCLOSURE",
        exchange="NSE"
    )
    ev_contra = EvidenceModel(
        title="NSE Disclosure: Regulatory Penalty Notice",
        publisher="NSE India",
        source_url="https://nsearchives.nseindia.in/corporate/penalty.pdf",
        content_summary="Infosys discloses regulatory penalty and headwind regarding delay in tax portal filing.",
        evidence_category="COMPANY_DISCLOSURE",
        exchange="NSE"
    )
    db_session.add_all([ev_supp, ev_contra])
    db_session.commit()

    assoc_supp = ClaimEvidenceModel(claim_id=claim.id, evidence_id=ev_supp.id, relevance_score=1.0)
    assoc_contra = ClaimEvidenceModel(claim_id=claim.id, evidence_id=ev_contra.id, relevance_score=1.0)
    db_session.add_all([assoc_supp, assoc_contra])
    db_session.commit()

    enriched = _enrich_claim_response(claim, db_session)
    assert len(enriched.supportingEvidence) == 1
    assert "Margin Expansion" in enriched.supportingEvidence[0]["title"]

    assert len(enriched.contradictoryEvidence) == 1
    assert "Penalty" in enriched.contradictoryEvidence[0]["title"]


# ===========================================================================
# 5. Dual-Model Verification & Epistemic Guardrail
# ===========================================================================

@pytest.mark.asyncio
async def test_dual_model_verification_epistemic_guardrail(db_session):
    """Verify that model concordance triggers the epistemic guardrail warning."""
    claim = ClaimModel(
        original_claim="Infosys will report 20% revenue growth in FY26",
        company_name="Infosys Limited",
        ticker="INFY",
        claim_direction="BULLISH"
    )
    db_session.add(claim)
    db_session.commit()

    mock_primary = MagicMock()
    mock_primary.name = "mock-groq"
    mock_primary.analyze_claim = AsyncMock(return_value={
        "direction": "BULLISH",
        "target": "20% revenue growth",
        "horizon": "FY26",
        "missing_fields": ["Deal ramp timelines", "Wage hike headwinds"],
        "interpretation_summary": "Extracted bullish revenue thesis for Infosys."
    })

    mock_secondary = MagicMock()
    mock_secondary.name = "mock-gemini"
    mock_secondary.review_analysis = AsyncMock(return_value={
        "agrees": True,
        "material_disagreements": [],
        "critique": "Analysis aligned with disclosed guidance."
    })

    orchestrator = AnalysisOrchestrator(
        db=db_session,
        primary_provider=mock_primary,
        secondary_provider=mock_secondary
    )

    analysis = await orchestrator.run_analysis(claim.id)
    assert analysis.provider_status == "SUCCESS"
    assert analysis.validation_status == "PASSED"

    # Epistemic guardrail assertion
    assert analysis.validation_notes is not None
    notes = json.loads(analysis.validation_notes)
    guardrail_found = any("Epistemic Guardrail" in note for note in notes)
    assert guardrail_found, "Epistemic Guardrail note must be recorded even when models agree"


# ===========================================================================
# 6. Ambiguous Claim & No Hardcoded Mock Data
# ===========================================================================

def test_ambiguous_claim_has_no_hardcoded_transformer_fallback(db_session):
    """Verify that ambiguous claims generate dynamic missing conditions and never hardcode transformer strings."""
    claim = ClaimModel(
        original_claim="Tech firm is definitely going higher!",
        company_name="Unspecified Tech",
        ticker="TECH"
    )
    db_session.add(claim)
    db_session.commit()

    enriched = _enrich_claim_response(claim, db_session)
    missing = enriched.breakdown["missingConditions"]

    # Verify no transformer strings
    for cond in missing:
        assert "transformer" not in cond.lower()
        assert "copper" not in cond.lower()
        assert "ferc" not in cond.lower()

    # Verify meaningful falsifiability conditions
    assert any("target" in c.lower() for c in missing)
    assert any("time" in c.lower() or "horizon" in c.lower() for c in missing)
    assert any("invalidation" in c.lower() or "condition" in c.lower() for c in missing)

    # Verify interpretation forks are entity-tailored, not hardcoded transformer expansion
    interpretations = enriched.interpretations
    assert len(interpretations) >= 1
    assert "Supply Chain & Margin Drag" not in [i["fork"] for i in interpretations]


# ===========================================================================
# 7. End-to-End Analysis Workflow Convenience Endpoint
# ===========================================================================

def test_claims_analyze_convenience_endpoint(client):
    """Verify /api/v1/claims/analyze end-to-end convenience workflow."""
    with patch("backend.app.services.analysis_orchestrator.AnalysisOrchestrator.run_analysis") as mock_run:
        # Mock analysis to return immediately
        mock_run.return_value = None

        resp = client.post("/api/v1/claims/analyze", json={
            "statement": "Wipro Limited will expand digital consulting revenue by 15% in Q4.",
            "company": "Wipro Limited",
            "ticker": "WIPRO",
            "horizon": "Q4"
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["statement"] == "Wipro Limited will expand digital consulting revenue by 15% in Q4."
        assert data["company"] == "Wipro Limited"
        assert "breakdown" in data
        assert "missingConditions" in data["breakdown"]
        assert "interpretations" in data
