import pytest


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "FinTrace" in data["app_name"]


def test_claim_submission_and_null_preservation(client):
    claim_payload = {
        "original_claim": "XYZ Ltd. will rise 30% in the next two months. Strong fundamentals. Buy before it's too late!",
        "source_url": "https://t.me/pennystocks/123",
        "source_platform": "Telegram",
        "provenance_status": "USER_PROVIDED"
    }

    response = client.post("/api/v1/claims", json=claim_payload)
    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["original_claim"] == claim_payload["original_claim"]
    assert data["source_url"] == claim_payload["source_url"]
    assert data["source_platform"] == "Telegram"
    assert data["provenance_status"] == "USER_PROVIDED"

    # Extracted fields
    assert data["target_value"] == 30.0
    assert data["target_unit"] == "%"
    assert data["claim_direction"] == "BULLISH"
    assert "next two months" in data["time_horizon"].lower()

    # CRITICAL: Missing information MUST remain null
    assert data["ticker"] is None
    assert data["exchange"] is None
    assert data["entry_condition"] is None
    assert data["exit_condition"] is None
    assert data["invalidation_condition"] is None
    assert data["is_ambiguous_entity"] is False


def test_ambiguous_company_detection(client):
    claim_payload = {
        "original_claim": "Tata will rise 25% by next month. Huge contract coming!",
        "source_platform": "Twitter"
    }

    response = client.post("/api/v1/claims", json=claim_payload)
    assert response.status_code == 201
    data = response.json()

    # Ambiguity check
    assert data["is_ambiguous_entity"] is True
    assert "Tata" in data["entity_ambiguity_notes"]
    assert "Tata Motors" in data["entity_ambiguity_notes"]


def test_claim_retrieval_and_deletion(client):
    # Submit 2 claims
    c1 = client.post("/api/v1/claims", json={"original_claim": "Claim 1 test text here"}).json()
    c2 = client.post("/api/v1/claims", json={"original_claim": "Claim 2 test text here"}).json()

    # List claims
    list_res = client.get("/api/v1/claims")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 2

    # Get claim 1
    get_res = client.get(f"/api/v1/claims/{c1['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == c1["id"]

    # Delete claim 1
    del_res = client.delete(f"/api/v1/claims/{c1['id']}")
    assert del_res.status_code == 204

    # Verify deleted
    get_deleted = client.get(f"/api/v1/claims/{c1['id']}")
    assert get_deleted.status_code == 404
