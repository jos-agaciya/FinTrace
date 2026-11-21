import pytest
from fastapi.testclient import TestClient


def test_auth_login_and_registration(client: TestClient):
    """Verifies that frontend auth routes are supported by backend."""
    # Test registration
    reg_payload = {
        "name": "Nakul Verma",
        "email": "nakul@fintrace.app",
        "password": "securepassword123"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    assert not reg_data["token"].startswith("ft_tok_")
    assert len(reg_data["token"].split(".")) == 3
    assert reg_data["user"]["name"] == "Nakul Verma"
    assert reg_data["user"]["initials"] == "NV"

    # Test login
    login_payload = {
        "email": "nakul@fintrace.app",
        "password": "securepassword123"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert login_data["user"]["email"] == "nakul@fintrace.app"
    token = login_data["token"]
    assert len(token.split(".")) == 3

    # Test auth me with bearer token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Nakul Verma"


def test_dual_prefix_routing(client: TestClient):
    """Verifies that routes are mounted and accessible under both /api/v1 and /api."""
    # /api/v1/health
    res_v1 = client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "healthy"

    # /api/health
    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    assert res_api.json()["status"] == "healthy"

    # /api/claims
    res_claims = client.get("/api/claims")
    assert res_claims.status_code == 200
    assert "items" in res_claims.json()


def test_evidence_global_listing_and_filtering(client: TestClient):
    """Verifies GET /api/v1/evidence global listing and keyword filtering."""
    # Create test evidence
    ev1 = {
        "title": "Reliance Q3 Earnings Report",
        "publisher": "NSE India",
        "source_url": "https://www.nseindia.com/corporate/reliance-q3",
        "evidence_category": "COMPANY_DISCLOSURE",
        "content_summary": "Net profit up 12% YoY driven by retail and digital services expansion.",
        "company_symbol": "RELIANCE",
        "provenance_status": "REAL"
    }
    ev2 = {
        "title": "TCS Cloud Migration Case Study",
        "publisher": "NSE India",
        "source_url": "https://www.nseindia.com/corporate/tcs-cloud",
        "evidence_category": "COMPANY_DISCLOSURE",
        "content_summary": "Multi-year enterprise cloud migration engagement signed.",
        "company_symbol": "TCS",
        "provenance_status": "REAL"
    }
    client.post("/api/v1/evidence", json=ev1)
    client.post("/api/v1/evidence", json=ev2)

    # List all
    all_res = client.get("/api/v1/evidence")
    assert all_res.status_code == 200
    all_data = all_res.json()
    assert isinstance(all_data, list)
    assert len(all_data) >= 2

    # Search filter
    filtered_res = client.get("/api/v1/evidence?q=Reliance")
    assert filtered_res.status_code == 200
    filtered_data = filtered_res.json()
    assert any("Reliance" in item["title"] for item in filtered_data)


def test_decision_lab_calibration_endpoints(client: TestClient):
    """Verifies decision lab calibration endpoint calculation."""
    calib_payload = {
        "initialStance": "GOOD",
        "initialConfidence": 85.0,
        "revisedStance": "NEUTRAL",
        "revisedConfidence": 58.0,
        "refutedAssumptions": {"ev_1": True, "ev_2": True}
    }

    # /api/v1/decision-lab/calibrate
    res1 = client.post("/api/v1/decision-lab/calibrate", json=calib_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["success"] is True
    assert data1["delta"] == -27.0
    assert data1["calibrationScore"] > 80.0
    assert "calibrated" in data1["insights"].lower()

    # Direct root path /decision-lab/calibrate
    res2 = client.post("/decision-lab/calibrate", json=calib_payload)
    assert res2.status_code == 200
    assert res2.json()["success"] is True


def test_claim_analyze_end_to_end_convenience(client: TestClient):
    """Verifies POST /api/v1/claims/analyze end-to-end convenience workflow."""
    req_payload = {
        "statement": "Infosys will see 20% margin expansion over the next 6 months due to AI services pipeline.",
        "ticker": "INFY",
        "company": "Infosys Limited",
        "horizon": "6 months",
        "sourceUrl": "https://twitter.com/analyst/status/987654"
    }

    res = client.post("/api/v1/claims/analyze", json=req_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["id"] is not None
    assert data["company"] == "Infosys Limited"
    assert data["ticker"] == "INFY"
    assert data["statement"] == req_payload["statement"]
    assert data["direction"] in ["Bullish", "Neutral", "Bearish"]
    assert data["validationStatus"] in ["Completed", "Needs Verification", "Degraded (No AI Provider)"]
    assert "breakdown" in data
    assert "completeness" in data
    assert "interpretations" in data
    assert len(data["interpretations"]) >= 2
    assert "supportingEvidence" in data


def test_ai_engine_adapter_status_and_health(client: TestClient):
    """Verifies AI Engine status reporting in health check."""
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200
    data = health_res.json()
    assert "ai_engine" in data
    assert data["ai_engine"]["status"] in ["operational", "degraded", "unavailable"]
