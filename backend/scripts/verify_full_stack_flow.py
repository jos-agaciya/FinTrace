"""End-to-End Full-Stack Flow Verification Script.

Tests complete user journey through FastAPI Backend, AI Engine Compiler, and Evidence Providers:
1. User registration & authentication
2. Claim submission (with entity resolution)
3. External evidence retrieval (NSE statutory disclosures)
4. AI Robustness compilation & interpretation fork generation
5. Virtual Decision Lab calibration & conviction shift tracking
6. Dashboard intelligence overview
"""

import sys
from pathlib import Path

# Setup paths
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def verify_flow():
    print("=" * 70)
    print("FinTrace Full-Stack Integration Verification")
    print("=" * 70)

    # 1. Health & AI Engine Telemetry
    print("[1/6] Checking Health & AI Engine Telemetry...")
    res = client.get("/api/v1/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health = res.json()
    print(f"      App Status: {health['status']}")
    print(f"      AI Engine Status: {health.get('ai_engine', {}).get('status')}")

    # 2. User Authentication
    print("[2/6] Verifying User Authentication...")
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Integration Tester",
        "email": "test@fintrace.ai",
        "password": "strongPassword123!"
    })
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    auth = reg_res.json()
    token = auth["token"]
    print(f"      User Authenticated: {auth['user']['name']} ({auth['user']['email']})")
    print(f"      Token Generated: {token[:16]}...")

    # 3. Analyze Claim via Convenience Workflow
    print("[3/6] Running End-to-End Claim Robustness Compilation...")
    claim_payload = {
        "statement": "TCS will achieve 15% revenue growth by Q4 driven by sovereign cloud contracts in the UK.",
        "ticker": "TCS",
        "company": "Tata Consultancy Services Limited",
        "horizon": "6 months",
        "sourceUrl": "https://twitter.com/analyst/status/12345678"
    }
    analyze_res = client.post("/api/v1/claims/analyze", json=claim_payload)
    assert analyze_res.status_code == 200, f"Claim compilation failed: {analyze_res.text}"
    report = analyze_res.json()
    claim_id = report["id"]
    print(f"      Claim ID: {claim_id}")
    print(f"      Company: {report['company']} ({report['ticker']})")
    print(f"      Validation Status: {report['validationStatus']}")
    print(f"      Evidence Coverage: {report['evidenceCoverage']}%")
    print(f"      Forks Generated: {len(report['interpretations'])}")
    for i, fork in enumerate(report["interpretations"][:2], 1):
        print(f"        - Fork {i}: {fork['fork']} [{fork['stance']}]")

    # 4. Evidence Centre Listing & Search
    print("[4/6] Querying Evidence Centre Disclosures...")
    ev_res = client.get("/api/v1/evidence")
    assert ev_res.status_code == 200
    evidence_items = ev_res.json()
    print(f"      Total Disclosures Stored: {len(evidence_items)}")

    filtered_ev = client.get("/api/v1/evidence?q=TCS")
    assert filtered_ev.status_code == 200
    print(f"      Filtered Disclosures for 'TCS': {len(filtered_ev.json())}")

    # 5. Virtual Decision Lab Calibration
    print("[5/6] Testing Virtual Decision Lab Calibration...")
    calib_payload = {
        "initialStance": "GOOD",
        "initialConfidence": 85.0,
        "revisedStance": "NEUTRAL",
        "revisedConfidence": 55.0,
        "refutedAssumptions": {"ev_tcs_01": True}
    }
    calib_res = client.post("/decision-lab/calibrate", json=calib_payload)
    assert calib_res.status_code == 200, f"Decision calibration failed: {calib_res.text}"
    calib_data = calib_res.json()
    print(f"      Calibration Score: {calib_data['calibrationScore']} / 100")
    print(f"      Conviction Delta: {calib_data['delta']} pts")
    print(f"      Insights: {calib_data['insights']}")

    # 6. Dashboard Overview
    print("[6/6] Verifying Investor Dashboard Overview...")
    dash_res = client.get("/api/v1/dashboard/overview")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    print(f"      Claims Submitted: {dash_data['total_claims_submitted']}")
    print(f"      Claims Analyzed: {dash_data['total_claims_analyzed']}")
    print(f"      Evidence Records: {dash_data['total_evidence_records']}")
    print(f"      Decisions Recorded: {dash_data['total_decisions_recorded']}")

    print("=" * 70)
    print("ALL FULL-STACK FLOW CHECKS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    verify_flow()
