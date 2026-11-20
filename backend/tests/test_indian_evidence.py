import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from datetime import datetime, timezone

from backend.app.integrations.evidence_provider import (
    NSEDisclosuresProvider,
    SECDisclosuresProvider,
    CorporateDisclosuresProvider,
    VERIFIED_NSE_REGISTRY
)
from backend.app.services.evidence_service import EvidenceService


# ---------------------------------------------------------------------------
# 1. Symbol and Entity Resolution Tests
# ---------------------------------------------------------------------------

def test_nse_symbol_resolution():
    """Requirement 2: INFY, TCS, and RELIANCE resolve to verified NSE entities."""
    provider = NSEDisclosuresProvider()

    res_infy = provider.resolve_nse_symbol("Infosys Limited", "INFY")
    assert res_infy is not None
    assert res_infy["symbol"] == "INFY"
    assert res_infy["isin"] == "INE009A01021"
    assert res_infy["has_us_adr"] is True

    res_tcs = provider.resolve_nse_symbol("Tata Consultancy Services", "TCS")
    assert res_tcs is not None
    assert res_tcs["symbol"] == "TCS"
    assert res_tcs["isin"] == "INE467B01029"
    assert res_tcs["has_us_adr"] is False

    res_rel = provider.resolve_nse_symbol("Reliance Industries Limited", "RELIANCE")
    assert res_rel is not None
    assert res_rel["symbol"] == "RELIANCE"
    assert res_rel["isin"] == "INE002A01018"
    assert res_rel["has_us_adr"] is False


def test_unknown_symbol_returns_no_fabricated_evidence(client):
    """Requirement 4: Unknown NSE symbol returns empty list without inventing evidence."""
    provider = NSEDisclosuresProvider()
    resolved = provider.resolve_nse_symbol("NonExistentCorp", "UNKNOWN9999999999")
    # Symbols over 12 characters or unverified names do not resolve
    assert resolved is None or resolved["isin"] is None

    claim = client.post("/api/v1/claims", json={
        "original_claim": "FictitiousEntity999 will rally 200%",
        "ticker": "NONEXISTENTXYZ99"
    }).json()

    res = client.post(f"/api/v1/evidence/{claim['id']}/retrieve")
    assert res.status_code == 200
    assert res.json()["total"] == 0


# ---------------------------------------------------------------------------
# 2. Strict Entity Resolution: Reliance vs Reliance, Inc. & TCS vs SEC
# ---------------------------------------------------------------------------

def test_reliance_industries_never_matches_reliance_inc():
    """Requirement 5: Reliance Industries Limited must NEVER match Reliance, Inc. (Scottsdale, AZ) in SEC."""
    sec_provider = SECDisclosuresProvider()

    # Querying SEC for Indian Reliance must return empty list
    items_by_ticker = asyncio.run(
        sec_provider.retrieve_evidence("Reliance Industries Limited", "RELIANCE")
    )
    assert len(items_by_ticker) == 0

    items_by_name = asyncio.run(
        sec_provider.retrieve_evidence("Reliance Industries", None)
    )
    assert len(items_by_name) == 0


def test_tcs_does_not_produce_false_sec_results():
    """Requirement 6: TCS is a domestic Indian company; must not produce false SEC results."""
    sec_provider = SECDisclosuresProvider()

    items = asyncio.run(
        sec_provider.retrieve_evidence("Tata Consultancy Services", "TCS")
    )
    assert len(items) == 0


# ---------------------------------------------------------------------------
# 3. Dual-Listed Companies: Separate Jurisdictions
# ---------------------------------------------------------------------------

def test_infosys_adr_and_nse_jurisdictions_separated():
    """Requirement 7: Infosys ADR (US) and NSE (IN) remain separate without merging jurisdictions."""
    mock_nse_items = [{
        "title": "NSE Disclosure: Audited Results",
        "document_title": "Audited Financial Results Q2",
        "publisher": "NSE India",
        "source_url": "https://nsearchives.nseindia.in/corporate/INFY_Q2.pdf",
        "publication_date": datetime(2026, 10, 15, tzinfo=timezone.utc),
        "evidence_category": "COMPANY_DISCLOSURE",
        "company_identifier": "INFY",
        "company_symbol": "INFY",
        "company_isin": "INE009A01021",
        "source_jurisdiction": "IN",
        "exchange": "NSE",
        "content_summary": "Statutory disclosure to NSE India.",
        "provenance_status": "REAL",
        "raw_payload": None
    }]

    mock_sec_items = [{
        "title": "SEC Form 6-K: Official Filing for Infosys Limited",
        "document_title": "SEC Form 6-K",
        "publisher": "SEC EDGAR Disclosures",
        "source_url": "https://www.sec.gov/edgar/browse/?CIK=0001067491",
        "publication_date": datetime(2026, 10, 16, tzinfo=timezone.utc),
        "evidence_category": "COMPANY_DISCLOSURE",
        "company_identifier": "INFY",
        "company_symbol": "INFY",
        "company_isin": None,
        "source_jurisdiction": "US",
        "exchange": "SEC",
        "content_summary": "US SEC periodic filing Form 6-K.",
        "provenance_status": "REAL",
        "raw_payload": None
    }]

    corp_provider = CorporateDisclosuresProvider()

    with patch.object(corp_provider.nse_provider, "retrieve_evidence", new_callable=AsyncMock) as mock_nse, \
         patch.object(corp_provider.sec_provider, "retrieve_evidence", new_callable=AsyncMock) as mock_sec:

        mock_nse.return_value = mock_nse_items
        mock_sec.return_value = mock_sec_items

        results = asyncio.run(corp_provider.retrieve_evidence("Infosys Limited", "INFY"))
        assert len(results) == 2

        # Verify jurisdictions remain distinct
        nse_rec = [r for r in results if r["exchange"] == "NSE"][0]
        sec_rec = [r for r in results if r["exchange"] == "SEC"][0]

        assert nse_rec["source_jurisdiction"] == "IN"
        assert nse_rec["publisher"] == "NSE India"
        assert "nsearchives.nseindia.in" in nse_rec["source_url"]

        assert sec_rec["source_jurisdiction"] == "US"
        assert sec_rec["publisher"] == "SEC EDGAR Disclosures"
        assert "sec.gov" in sec_rec["source_url"]


# ---------------------------------------------------------------------------
# 4. Correct Extraction of Title, Date, and PDF URL
# ---------------------------------------------------------------------------

def test_nse_extraction_fields():
    """Requirement 3: Correct extraction of title, date, and authentic PDF URL."""
    sample_nse_api_response = [{
        "an_dt": "18-Nov-2026 22:10:55",
        "sort_date": "2026-11-18 22:10:55",
        "attchmntFile": "https://nsearchives.nseindia.in/corporate/INFY_test_filing.pdf",
        "attchmntText": "Infosys Limited has informed the Exchange regarding dividend declaration.",
        "desc": "Dividend Updates",
        "sm_name": "Infosys Limited",
        "sm_isin": "INE009A01021",
        "symbol": "INFY"
    }]

    nse_provider = NSEDisclosuresProvider()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = sample_nse_api_response
        mock_get.return_value = mock_res

        items = asyncio.run(nse_provider.retrieve_evidence("Infosys", "INFY"))
        assert len(items) == 1
        record = items[0]

        assert "Infosys Limited" in record["title"] or "dividend declaration" in record["title"]
        assert record["source_url"] == "https://nsearchives.nseindia.in/corporate/INFY_test_filing.pdf"
        assert record["publication_date"] == datetime(2026, 11, 18, 22, 10, 55, tzinfo=timezone.utc)
        assert record["company_isin"] == "INE009A01021"
        assert record["publisher"] == "NSE India"
        assert record["exchange"] == "NSE"
        assert record["source_jurisdiction"] == "IN"


# ---------------------------------------------------------------------------
# 5. Network Failures, Timeouts, 403, 429, and Malformed Responses
# ---------------------------------------------------------------------------

def test_nse_error_handling_403_429_timeout():
    """Requirements 9 & 10: NSE handles 403, 429, timeouts, and malformed JSON safely."""
    nse_provider = NSEDisclosuresProvider()

    # Test HTTP 403 Forbidden
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 403
        mock_get.return_value = mock_res
        assert asyncio.run(nse_provider.retrieve_evidence("Infosys", "INFY")) == []

    # Test HTTP 429 Too Many Requests
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 429
        mock_get.return_value = mock_res
        assert asyncio.run(nse_provider.retrieve_evidence("Infosys", "INFY")) == []

    # Test Request Timeout
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
        assert asyncio.run(nse_provider.retrieve_evidence("Infosys", "INFY")) == []

    # Test Malformed JSON
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.side_effect = ValueError("Malformed JSON string")
        mock_get.return_value = mock_res
        assert asyncio.run(nse_provider.retrieve_evidence("Infosys", "INFY")) == []


# ---------------------------------------------------------------------------
# 6. Duplicate Handling & Missing Publication Dates
# ---------------------------------------------------------------------------

def test_deduplication_and_missing_dates(client):
    """Requirements 11 & 12: Missing publication dates handled; duplicate source URLs deduplicated."""
    claim = client.post("/api/v1/claims", json={
        "original_claim": "TCS announcement claim",
        "ticker": "TCS"
    }).json()
    claim_id = claim["id"]

    mock_announcements = [
        {
            "an_dt": None,  # Missing publication date
            "sort_date": None,
            "attchmntFile": "https://nsearchives.nseindia.in/corporate/TCS_duplicate.pdf",
            "attchmntText": "Press release without date",
            "desc": "General",
            "symbol": "TCS",
            "sm_name": "Tata Consultancy Services Limited",
            "sm_isin": "INE467B01029"
        },
        {
            # Exact duplicate source URL
            "an_dt": "19-Nov-2026 10:00:00",
            "sort_date": "2026-11-19 10:00:00",
            "attchmntFile": "https://nsearchives.nseindia.in/corporate/TCS_duplicate.pdf",
            "attchmntText": "Second copy with same URL",
            "desc": "General",
            "symbol": "TCS",
            "sm_name": "Tata Consultancy Services Limited",
            "sm_isin": "INE467B01029"
        }
    ]

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = mock_announcements
        mock_get.return_value = mock_res

        # Retrieve evidence
        trigger_res = client.post(f"/api/v1/evidence/{claim_id}/retrieve")
        assert trigger_res.status_code == 200
        data = trigger_res.json()

        # Deduplication ensures only 1 record is stored despite 2 incoming items with identical URLs
        assert data["total"] == 1
        item = data["items"][0]["evidence"]
        assert item["publication_date"] is None or item["publication_date"] != ""
        assert item["source_jurisdiction"] == "IN"
        assert item["exchange"] == "NSE"


# ---------------------------------------------------------------------------
# 7. Live Network Test Against Real NSE Endpoints (Infy, TCS, Reliance)
# ---------------------------------------------------------------------------

def test_live_nse_announcements_retrieval(client):
    """
    Live test against authentic NSE endpoints for INFY, TCS, and RELIANCE.
    If internet is accessible, verifies genuine primary disclosures.
    """
    for sym, comp in [("INFY", "Infosys"), ("TCS", "Tata Consultancy Services"), ("RELIANCE", "Reliance Industries")]:
        claim = client.post("/api/v1/claims", json={
            "original_claim": f"{comp} will report strong growth this quarter.",
            "ticker": sym
        }).json()

        res = client.post(f"/api/v1/evidence/{claim['id']}/retrieve")
        assert res.status_code == 200
        data = res.json()

        # If live network request succeeded, verify actual real records
        if data["total"] > 0:
            first_ev = data["items"][0]["evidence"]
            assert first_ev["publisher"] in ["NSE India", "SEC EDGAR Disclosures"]
            assert first_ev["provenance_status"] == "REAL"
            if first_ev["exchange"] == "NSE":
                assert first_ev["source_jurisdiction"] == "IN"
                assert "nsearchives.nseindia.in" in first_ev["source_url"] or "nseindia.com" in first_ev["source_url"]


# ---------------------------------------------------------------------------
# 7. Live Network Test Against Real NSE Endpoints (Infy, TCS, Reliance)
# ---------------------------------------------------------------------------

def test_live_nse_announcements_retrieval(client):
    """
    Live test against authentic NSE endpoints for INFY, TCS, and RELIANCE.
    If internet is accessible, verifies genuine primary disclosures.
    """
    for sym, comp in [("INFY", "Infosys"), ("TCS", "Tata Consultancy Services"), ("RELIANCE", "Reliance Industries")]:
        claim = client.post("/api/v1/claims", json={
            "original_claim": f"{comp} will report strong growth this quarter.",
            "ticker": sym
        }).json()

        res = client.post(f"/api/v1/evidence/{claim['id']}/retrieve")
        assert res.status_code == 200
        data = res.json()

        # If live network request succeeded, verify actual real records
        if data["total"] > 0:
            first_ev = data["items"][0]["evidence"]
            assert first_ev["publisher"] in ["NSE India", "SEC EDGAR Disclosures"]
            assert first_ev["provenance_status"] == "REAL"
            if first_ev["exchange"] == "NSE":
                assert first_ev["source_jurisdiction"] == "IN"
                assert "nsearchives.nseindia.in" in first_ev["source_url"] or "nseindia.com" in first_ev["source_url"]
