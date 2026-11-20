import pytest
from unittest.mock import AsyncMock, patch


def test_evidence_creation_and_retrieval(client):
    payload = {
        "title": "Q3 Audited Results - XYZ Ltd.",
        "publisher": "NSE India Corporate Disclosures",
        "source_url": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
        "publication_date": "2026-10-15T10:00:00Z",
        "evidence_category": "COMPANY_DISCLOSURE",
        "company_identifier": "XYZ Ltd.",
        "content_summary": "Net profit increased 12% YoY, EBITDA margin stable at 18.5%.",
        "provenance_status": "REAL"
    }

    res = client.post("/api/v1/evidence", json=payload)
    assert res.status_code == 201
    created = res.json()
    assert created["id"] is not None
    assert created["provenance_status"] == "REAL"
    assert created["publisher"] == payload["publisher"]

    # Retrieve by item ID
    get_res = client.get(f"/api/v1/evidence/item/{created['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == payload["title"]


def test_claim_evidence_association_and_retrieval(client):
    # 1. Create claim
    claim = client.post("/api/v1/claims", json={"original_claim": "XYZ Ltd will rise 30% next month"}).json()
    claim_id = claim["id"]

    # 2. Check evidence is empty initially
    empty_res = client.get(f"/api/v1/evidence/{claim_id}")
    assert empty_res.status_code == 200
    assert empty_res.json()["total"] == 0

    # 3. Trigger verifiable disclosure retrieval with mock
    mock_items = [{
        "title": "Annual Report FY2026",
        "publisher": "BSE Filings",
        "source_url": "https://bseindia.com/filings/123",
        "publication_date": "2026-09-01T00:00:00Z",
        "evidence_category": "COMPANY_DISCLOSURE",
        "company_identifier": "XYZ Ltd",
        "content_summary": "Official audited annual report.",
        "provenance_status": "REAL",
        "raw_payload": None
    }]

    with patch("backend.app.integrations.evidence_provider.CorporateDisclosuresProvider.retrieve_evidence", new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = mock_items
        trigger_res = client.post(f"/api/v1/evidence/{claim_id}/retrieve")
        assert trigger_res.status_code == 200
        data = trigger_res.json()
        assert data["total"] == 1
        assert data["items"][0]["evidence"]["title"] == "Annual Report FY2026"
        assert data["items"][0]["evidence"]["provenance_status"] == "REAL"
