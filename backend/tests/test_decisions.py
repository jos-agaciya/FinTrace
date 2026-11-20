import pytest


def test_decision_lifecycle_and_sensitivity_tracking(client):
    # 1. Create a claim
    claim = client.post("/api/v1/claims", json={
        "original_claim": "XYZ Ltd will rise 40% based on Q3 rumor."
    }).json()
    claim_id = claim["id"]

    # 2. Record initial decision
    initial_payload = {
        "claim_id": claim_id,
        "initial_thesis": "Buying early to capture momentum pump.",
        "initial_confidence": 85.0,
        "initial_allocation": 30.0,
        "assumptions_evaluated": ["Momentum holds", "Earnings beat consensus"]
    }
    create_res = client.post("/api/v1/decisions", json=initial_payload)
    assert create_res.status_code == 201
    decision = create_res.json()
    assert decision["id"] is not None
    assert decision["initial_confidence"] == 85.0
    assert decision["revised_confidence"] is None
    assert decision["sensitivity_summary"] is None

    # 3. Revise decision after reviewing counter-evidence
    revision_payload = {
        "revised_thesis": "Reducing allocation; disclosure filing reveals declining operating margins and high debt.",
        "revised_confidence": 45.0,
        "revised_allocation": 5.0,
        "reason_for_change": "Primary source disclosures contradicted the viral social post.",
        "assumptions_evaluated": ["Debt overhang risks", "Declining operating margin"]
    }
    revise_res = client.put(f"/api/v1/decisions/{decision['id']}/revise", json=revision_payload)
    assert revise_res.status_code == 200
    revised = revise_res.json()

    assert revised["revised_confidence"] == 45.0
    assert revised["revised_allocation"] == 5.0
    assert revised["reason_for_change"] == revision_payload["reason_for_change"]

    # Check sensitivity summary
    summary = revised["sensitivity_summary"]
    assert summary is not None
    assert summary["confidence_delta_points"] == -40.0
    assert summary["allocation_delta_points"] == -25.0
    assert summary["reasoning_shift_type"] == "REDUCED_EXPOSURE"
    assert "Allocation decreased by 25.0 percentage points" in summary["shift_explanation"]

    # 4. Query decisions for claim
    list_res = client.get(f"/api/v1/decisions/{claim_id}")
    assert list_res.status_code == 200
    records = list_res.json()
    assert len(records) == 1
    assert records[0]["id"] == decision["id"]
