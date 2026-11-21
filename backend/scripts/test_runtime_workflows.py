"""Simulates all 8 frontend page runtime workflows against the FastAPI backend."""

import sys
import json
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi.testclient import TestClient
from backend.app.main import app


def test_runtime_workflows():
    results = {}

    with TestClient(app) as client:
        print("--- 1. Registration and Login ---")
    # Registration
    r_reg = client.post("/api/v1/auth/register", json={
        "name": "Arjun Rao",
        "email": "arjun@example.com",
        "password": "mypassword123"
    })
    results["registration"] = {
        "status": r_reg.status_code,
        "token": r_reg.json().get("token"),
        "user_name": r_reg.json().get("user", {}).get("name")
    }

    # Login
    r_login = client.post("/api/v1/auth/login", json={
        "email": "arjun@example.com",
        "password": "mypassword123"
    })
    results["login"] = {
        "status": r_login.status_code,
        "token": r_login.json().get("token")
    }

    # Auth Me
    r_me = client.get("/api/v1/auth/me")
    results["auth_me"] = {
        "status": r_me.status_code,
        "user": r_me.json()
    }

    print("--- 2. Dashboard Loading ---")
    # Dashboard Overview
    r_dash = client.get("/api/v1/dashboard/overview")
    results["dashboard_overview"] = {
        "status": r_dash.status_code,
        "data": r_dash.json()
    }

    # Claims List for Dashboard Recent Activity
    r_claims = client.get("/api/v1/claims")
    results["dashboard_claims"] = {
        "status": r_claims.status_code,
        "total": r_claims.json().get("total"),
        "items_count": len(r_claims.json().get("items", []))
    }

    print("--- 3. Claim Submission and Analysis ---")
    claim_payload = {
        "statement": "State Bank of India will increase net interest margins by 25 bps in Q3 on robust retail loan growth.",
        "ticker": "SBIN",
        "company": "State Bank of India",
        "horizon": "3 months",
        "sourceUrl": "https://economictimes.indiatimes.com/news"
    }
    r_analyze = client.post("/api/v1/claims/analyze", json=claim_payload)
    results["claim_analyze"] = {
        "status": r_analyze.status_code,
        "claim_id": r_analyze.json().get("id"),
        "validation_status": r_analyze.json().get("validationStatus"),
        "evidence_coverage": r_analyze.json().get("evidenceCoverage"),
        "forks_count": len(r_analyze.json().get("interpretations", []))
    }
    created_claim_id = r_analyze.json().get("id")

    print("--- 4. Evidence Centre Search ---")
    # Global listing
    r_ev_all = client.get("/api/v1/evidence")
    results["evidence_all"] = {
        "status": r_ev_all.status_code,
        "count": len(r_ev_all.json())
    }

    # Filtered search
    r_ev_filt = client.get("/api/v1/evidence?q=bank")
    results["evidence_filtered"] = {
        "status": r_ev_filt.status_code,
        "count": len(r_ev_filt.json())
    }

    print("--- 5. Analysis Report Rendering ---")
    r_report = client.get(f"/api/v1/claims/{created_claim_id}")
    results["claim_report"] = {
        "status": r_report.status_code,
        "has_breakdown": "breakdown" in r_report.json(),
        "has_interpretations": "interpretations" in r_report.json(),
        "has_completeness": "completeness" in r_report.json(),
        "has_supporting_evidence": "supportingEvidence" in r_report.json()
    }

    print("--- 6. Decision Lab Initial and Revised Decisions ---")
    # Initial decision
    dec_init_payload = {
        "claim_id": created_claim_id,
        "initial_thesis": "Strong retail growth supports margin expansion despite rising deposit rates.",
        "initial_confidence": 80.0,
        "initial_allocation": 15.0,
        "assumptions_evaluated": ["Deposit costs remain stable", "Credit growth > 14%"]
    }
    r_dec_init = client.post("/api/v1/decisions", json=dec_init_payload)
    results["decision_initial"] = {
        "status": r_dec_init.status_code,
        "decision_id": r_dec_init.json().get("id") if r_dec_init.status_code == 201 else None
    }
    created_decision_id = r_dec_init.json().get("id") if r_dec_init.status_code == 201 else None

    # Revised decision
    if created_decision_id:
        dec_rev_payload = {
            "revised_thesis": "Deposit competition may compress margins faster than retail yield expansion.",
            "revised_confidence": 60.0,
            "revised_allocation": 8.0,
            "reason_for_change": "Reviewed RBI sector liquidity data and peer deposit repricing trends."
        }
        r_dec_rev = client.put(f"/api/v1/decisions/{created_decision_id}/revise", json=dec_rev_payload)
        results["decision_revise"] = {
            "status": r_dec_rev.status_code,
            "shift_type": r_dec_rev.json().get("sensitivity_summary", {}).get("reasoning_shift_type") if r_dec_rev.status_code == 200 else None,
            "explanation": r_dec_rev.json().get("sensitivity_summary", {}).get("shift_explanation") if r_dec_rev.status_code == 200 else None
        }

    print("--- 7. Decision Calibration ---")
    calib_payload = {
        "initialStance": "GOOD",
        "initialConfidence": 80.0,
        "revisedStance": "NEUTRAL",
        "revisedConfidence": 60.0,
        "refutedAssumptions": {"ev_deposit_costs": True}
    }
    r_calib = client.post("/decision-lab/calibrate", json=calib_payload)
    results["decision_calibration"] = {
        "status": r_calib.status_code,
        "score": r_calib.json().get("calibrationScore"),
        "delta": r_calib.json().get("delta")
    }

    print("--- 8. Logout & Session Handling ---")
    # Frontend navigation to /login
    results["logout_session"] = {
        "status": "CLIENT_SIDE_NAVIGATION_ONLY",
        "notes": "Frontend clears state locally. No backend session revocation endpoint exists."
    }

    print("\nRESULTS SUMMARY:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    test_runtime_workflows()
