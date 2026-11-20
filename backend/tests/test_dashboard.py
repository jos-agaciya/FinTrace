import pytest


def test_dashboard_overview_and_progress_flow(client):
    # 1. Overview initially empty
    init_res = client.get("/api/v1/dashboard/overview")
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["total_claims_submitted"] == 0
    assert init_data["total_decisions_recorded"] == 0

    # 2. Ingest a claim and decision
    claim = client.post("/api/v1/claims", json={"original_claim": "Dashboard test claim 100"}).json()
    claim_id = claim["id"]

    decision = client.post("/api/v1/decisions", json={
        "claim_id": claim_id,
        "initial_thesis": "Initial thesis test",
        "initial_confidence": 70.0,
        "initial_allocation": 15.0
    }).json()

    # Verify overview updated strictly from database
    after_res = client.get("/api/v1/dashboard/overview")
    assert after_res.status_code == 200
    after_data = after_res.json()
    assert after_data["total_claims_submitted"] == 1
    assert after_data["total_decisions_recorded"] == 1
    assert len(after_data["recent_claims"]) == 1
    assert len(after_data["recent_decisions"]) == 1

    # 3. Test progress endpoint across session lifecycle
    session_id = "dashboard-investor-88"

    # Stage 0: Not started
    p0 = client.get(f"/api/v1/dashboard/progress?session_id={session_id}").json()
    assert p0["status"] == "NOT_STARTED"
    assert p0["has_baseline"] is False

    # Stage 1: Baseline completed
    client.post("/api/v1/assessments", json={
        "session_id": session_id,
        "claim_id": claim_id,
        "assessment_stage": "BASELINE",
        "identified_evidence_types": [],
        "distinguished_primary_sources": False,
        "identified_missing_specificity": [],
        "identified_risk_factors": [],
        "recognized_alternative_interpretations": False,
        "stated_confidence": 80.0,
        "evidence_backing_level": "NONE"
    })

    p1 = client.get(f"/api/v1/dashboard/progress?session_id={session_id}").json()
    assert p1["status"] == "BASELINE_COMPLETED"
    assert p1["has_baseline"] is True
    assert p1["has_independent_transfer"] is False
    assert p1["baseline_total_score"] is not None

    # Stage 2: Independent Transfer completed
    client.post("/api/v1/assessments", json={
        "session_id": session_id,
        "claim_id": claim_id,
        "assessment_stage": "INDEPENDENT_TRANSFER",
        "identified_evidence_types": ["COMPANY_DISCLOSURE"],
        "distinguished_primary_sources": True,
        "identified_missing_specificity": ["time_horizon", "exit_condition"],
        "identified_risk_factors": ["Operational risk"],
        "recognized_alternative_interpretations": True,
        "stated_confidence": 30.0,
        "evidence_backing_level": "NONE"
    })

    p2 = client.get(f"/api/v1/dashboard/progress?session_id={session_id}").json()
    assert p2["status"] == "ASSESSMENT_COMPLETED"
    assert p2["has_baseline"] is True
    assert p2["has_independent_transfer"] is True
    assert p2["percentage_point_delta"] is not None
    assert p2["percentage_point_delta"] == round(p2["latest_transfer_score"] - p2["baseline_total_score"], 1)

    # 4. History endpoint
    h_res = client.get(f"/api/v1/dashboard/history?session_id={session_id}")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert h_data["total_evaluations"] == 2
