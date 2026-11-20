import pytest


def test_deterministic_scoring_and_stage_comparison(client):
    # 1. Create 2 claims (one for baseline, one for transfer)
    c1 = client.post("/api/v1/claims", json={"original_claim": "Claim 1 baseline test"}).json()
    c2 = client.post("/api/v1/claims", json={"original_claim": "Claim 2 transfer test"}).json()

    session_id = "investor-test-session-42"

    # 2. Submit Baseline Assessment (User shows ungrounded high confidence without justification)
    baseline_payload = {
        "session_id": session_id,
        "claim_id": c1["id"],
        "assessment_stage": "BASELINE",
        "identified_evidence_types": ["UNVERIFIED_COMMENTARY"],
        "distinguished_primary_sources": False,
        "identified_missing_specificity": ["time_horizon"],
        "identified_risk_factors": [],
        "recognized_alternative_interpretations": False,
        "stated_confidence": 90.0,
        "evidence_backing_level": "NONE"
    }

    b_res = client.post("/api/v1/assessments", json=baseline_payload)
    assert b_res.status_code == 201
    baseline = b_res.json()
    assert baseline["assessment_stage"] == "BASELINE"
    assert baseline["score_evidence_eval"] < 10.0
    # Ungrounded high confidence receives a low justification score (<= 8.0/20)
    assert baseline["score_confidence_calibration"] <= 8.0
    assert baseline["total_score"] < 50.0

    # 3. Submit Independent Transfer Assessment (User provides disciplined justification connecting evidence to confidence)
    transfer_payload = {
        "session_id": session_id,
        "claim_id": c2["id"],
        "assessment_stage": "INDEPENDENT_TRANSFER",
        "identified_evidence_types": ["COMPANY_DISCLOSURE", "REGULATORY_FILING", "MARKET_DATA"],
        "distinguished_primary_sources": True,
        "identified_missing_specificity": ["time_horizon", "invalidation_condition", "entry_condition", "exit_condition"],
        "identified_risk_factors": ["Solvency risk", "Sector macro headwind", "Customer concentration"],
        "recognized_alternative_interpretations": True,
        "stated_confidence": 35.0,
        "evidence_backing_level": "NONE",
        "confidence_justification": (
            "Maintained restrained 35% confidence because despite identifying disclosure types, "
            "the claim omits entry and invalidation conditions and faces severe solvency and macro risks."
        )
    }

    t_res = client.post("/api/v1/assessments", json=transfer_payload)
    assert t_res.status_code == 201
    transfer = t_res.json()
    assert transfer["assessment_stage"] == "INDEPENDENT_TRANSFER"
    # Disciplined, coherent justification achieves a high score (>= 18.0/20)
    assert transfer["score_confidence_calibration"] >= 18.0
    assert transfer["total_score"] > 70.0

    # 4. Compare Stages
    comp_res = client.get(f"/api/v1/assessments/compare/{session_id}")
    assert comp_res.status_code == 200
    comp = comp_res.json()

    expected_delta = round(transfer["total_score"] - baseline["total_score"], 1)
    assert comp["percentage_point_delta"] == expected_delta
    assert comp["percentage_point_delta"] > 0
    assert f"increased by {expected_delta} percentage points" in comp["comparison_summary"]
    assert "from" in comp["comparison_summary"]
    assert "to" in comp["comparison_summary"]

    # 5. History endpoint
    hist_res = client.get(f"/api/v1/assessments/history?session_id={session_id}")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) == 2
