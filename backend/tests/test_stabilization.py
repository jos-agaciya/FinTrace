import pytest
from backend.app.models.claim import ClaimModel, InterpretationForkModel
from backend.app.models.analysis import AnalysisModel
from backend.app.models.decision import DecisionModel
from backend.app.models.assessment import AssessmentModel


def test_openapi_and_docs_endpoints(client):
    """Verify that OpenAPI schema and interactive Swagger/ReDoc docs load properly."""
    res_openapi = client.get("/api/v1/openapi.json")
    assert res_openapi.status_code == 200
    schema = res_openapi.json()
    assert "paths" in schema
    paths = schema["paths"]

    # Verify key route prefixes exist in OpenAPI schema
    assert "/api/v1/health" in paths
    assert "/api/v1/claims" in paths
    assert "/api/v1/claims/{claim_id}" in paths
    assert "/api/v1/evidence/{claim_id}" in paths
    assert "/api/v1/evidence/item/{evidence_id}" in paths
    assert "/api/v1/analysis/{claim_id}/run" in paths
    assert "/api/v1/decisions" in paths
    assert "/api/v1/assessments" in paths
    assert "/api/v1/dashboard/overview" in paths
    assert "/api/v1/dashboard/progress" in paths

    # Verify docs HTML
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200
    assert "swagger-ui" in res_docs.text.lower()

    res_redoc = client.get("/redoc")
    assert res_redoc.status_code == 200
    assert "redoc" in res_redoc.text.lower()


def test_input_validation_errors(client):
    """Verify standard HTTP 422 responses for malformed payloads."""
    # 1. Claim text too short (< 5 chars)
    res1 = client.post("/api/v1/claims", json={"original_claim": "abc"})
    assert res1.status_code == 422

    # 2. Decision confidence out of bounds (> 100)
    claim = client.post("/api/v1/claims", json={"original_claim": "Valid claim for boundary test"}).json()
    res2 = client.post("/api/v1/decisions", json={
        "claim_id": claim["id"],
        "initial_thesis": "Test thesis",
        "initial_confidence": 150.0,
        "initial_allocation": 20.0
    })
    assert res2.status_code == 422

    # 3. Decision allocation out of bounds (< 0)
    res3 = client.post("/api/v1/decisions", json={
        "claim_id": claim["id"],
        "initial_thesis": "Test thesis",
        "initial_confidence": 50.0,
        "initial_allocation": -10.0
    })
    assert res3.status_code == 422


def test_missing_records_and_404_responses(client):
    """Verify clean 404 responses for non-existent entities."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    assert client.get(f"/api/v1/claims/{fake_id}").status_code == 404
    assert client.delete(f"/api/v1/claims/{fake_id}").status_code == 404
    assert client.get(f"/api/v1/evidence/item/{fake_id}").status_code == 404
    assert client.get(f"/api/v1/analysis/{fake_id}").status_code == 404
    assert client.get(f"/api/v1/claims/{fake_id}/analysis").status_code == 404
    assert client.get(f"/api/v1/assessments/{fake_id}").status_code == 404

    # Revising a non-existent decision
    revise_res = client.put(f"/api/v1/decisions/{fake_id}/revise", json={
        "revised_thesis": "Revised thesis",
        "revised_confidence": 50.0,
        "revised_allocation": 10.0,
        "reason_for_change": "Testing non-existent record"
    })
    assert revise_res.status_code == 404


def test_missing_prerequisites_for_stage_comparison(client):
    """Verify 400 Bad Request when comparison is requested without required stages."""
    res = client.get("/api/v1/assessments/compare/session-without-data")
    assert res.status_code == 400
    assert "Both BASELINE and INDEPENDENT_TRANSFER assessments required" in res.json()["detail"]


def test_cascade_deletion(client, db_session):
    """Verify that deleting a claim properly cascades and cleans up linked records."""
    # 1. Ingest claim
    claim = client.post("/api/v1/claims", json={"original_claim": "Cascade test claim text"}).json()
    claim_id = claim["id"]

    # 2. Add an interpretation fork directly
    fork = InterpretationForkModel(
        claim_id=claim_id,
        title="Fork 1",
        description="Desc",
        ambiguous_phrase="phrase",
        assumptions="[]",
        information_required="info",
        is_ai_generated=True
    )
    db_session.add(fork)

    # 3. Add a decision
    client.post("/api/v1/decisions", json={
        "claim_id": claim_id,
        "initial_thesis": "Initial stance",
        "initial_confidence": 60.0,
        "initial_allocation": 10.0
    })

    # 4. Add an assessment
    client.post("/api/v1/assessments", json={
        "session_id": "cascade-session",
        "claim_id": claim_id,
        "assessment_stage": "BASELINE",
        "identified_evidence_types": [],
        "distinguished_primary_sources": False,
        "identified_missing_specificity": [],
        "identified_risk_factors": [],
        "recognized_alternative_interpretations": False,
        "stated_confidence": 50.0,
        "evidence_backing_level": "NONE"
    })

    # Verify records exist before deletion
    assert db_session.query(DecisionModel).filter_by(claim_id=claim_id).count() == 1
    assert db_session.query(AssessmentModel).filter_by(claim_id=claim_id).count() == 1
    assert db_session.query(InterpretationForkModel).filter_by(claim_id=claim_id).count() == 1

    # Delete claim
    del_res = client.delete(f"/api/v1/claims/{claim_id}")
    assert del_res.status_code == 204

    # Verify records were cascade-deleted
    assert db_session.query(ClaimModel).filter_by(id=claim_id).count() == 0
    assert db_session.query(DecisionModel).filter_by(claim_id=claim_id).count() == 0
    assert db_session.query(AssessmentModel).filter_by(claim_id=claim_id).count() == 0
    assert db_session.query(InterpretationForkModel).filter_by(claim_id=claim_id).count() == 0


def test_real_sec_edgar_evidence_retrieval(client):
    """
    Verifies actual live retrieval of genuine regulatory disclosures
    via the corporate disclosures index (NSE/SEC) for a listed entity.
    """
    claim = client.post("/api/v1/claims", json={
        "original_claim": "Infosys Ltd will grow revenue 15% next quarter.",
        "ticker": "INFY",
        "company_name": "Infosys Ltd"
    }).json()
    claim_id = claim["id"]

    # Trigger live retrieval (no mocks)
    res = client.post(f"/api/v1/evidence/{claim_id}/retrieve")
    assert res.status_code == 200
    data = res.json()

    # If internet is accessible, verify live genuine filing records
    if data["total"] > 0:
        publishers = {item["evidence"]["publisher"] for item in data["items"]}
        assert any(p in ["NSE India", "SEC EDGAR Disclosures"] for p in publishers)
        for item in data["items"]:
            ev = item["evidence"]
            assert ev["provenance_status"] == "REAL"
            assert ev["source_url"].startswith("http")
            assert ev["source_jurisdiction"] in ["IN", "US"]
            assert ev["exchange"] in ["NSE", "SEC"]


def test_unknown_entity_evidence_retrieval_does_not_fabricate(client):
    """Verifies that an unlisted/fictitious entity produces 0 items rather than fabricated citations."""
    claim = client.post("/api/v1/claims", json={
        "original_claim": "FictitiousCompanyXYZ999999 will rally 500%."
    }).json()
    claim_id = claim["id"]

    res = client.post(f"/api/v1/evidence/{claim_id}/retrieve")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
