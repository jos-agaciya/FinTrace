import pytest
from fastapi.testclient import TestClient
from backend.app.models.claim import ClaimModel
from backend.app.models.evidence import EvidenceModel, ClaimEvidenceModel
from backend.app.models.user import UserModel
from backend.app.api.routes.claims import _enrich_claim_response


def test_put_auth_me_updates_profile(client: TestClient):
    """Verifies PUT /auth/me updates user display name and role."""
    reg = client.post("/api/v1/auth/register", json={
        "name": "Initial Name",
        "email": "update_test_user@fintrace.app",
        "password": "SecurePassword123!"
    })
    assert reg.status_code == 201
    token = reg.json()["token"]

    # Update profile
    headers = {"Authorization": f"Bearer {token}"}
    update_res = client.put("/api/v1/auth/me", headers=headers, json={
        "name": "Updated Analytical Name",
        "role": "Lead Risk Analyst"
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["name"] == "Updated Analytical Name"
    assert updated_data["role"] == "Lead Risk Analyst"
    assert updated_data["initials"] == "UN"

    # Verify GET /auth/me reflects update
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Updated Analytical Name"
    assert me_res.json()["role"] == "Lead Risk Analyst"


def test_user_isolated_claims_and_dashboard(client: TestClient):
    """Verifies that new user with 0 records sees 0 claims and 0 overview metrics."""
    reg1 = client.post("/api/v1/auth/register", json={
        "name": "User One",
        "email": "user1_isolation@fintrace.app",
        "password": "SecurePassword123!"
    })
    token1 = reg1.json()["token"]

    reg2 = client.post("/api/v1/auth/register", json={
        "name": "User Two",
        "email": "user2_isolation@fintrace.app",
        "password": "SecurePassword123!"
    })
    token2 = reg2.json()["token"]

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 submits a claim
    c1_res = client.post("/api/v1/claims", headers=headers1, json={
        "original_claim": "Infosys will grow 20% on AI services.",
        "ticker": "INFY"
    })
    assert c1_res.status_code == 201
    claim1_id = c1_res.json()["id"]

    # User 1 lists claims -> sees 1 claim
    list1 = client.get("/api/v1/claims", headers=headers1).json()
    assert list1["total"] == 1
    assert list1["items"][0]["id"] == claim1_id

    # User 2 lists claims -> sees 0 claims (strictly isolated!)
    list2 = client.get("/api/v1/claims", headers=headers2).json()
    assert list2["total"] == 0
    assert len(list2["items"]) == 0

    # User 2 dashboard overview -> 0 claims, 0 decisions
    ov2 = client.get("/api/v1/dashboard/overview", headers=headers2).json()
    assert ov2["total_claims_submitted"] == 0
    assert ov2["total_decisions_recorded"] == 0


def test_decision_lab_scenarios_and_persistence(client: TestClient, db_session):
    """Verifies GET /decision-lab/scenarios returns practice scenarios and persists decisions."""
    # Seed a claim with evidence
    claim = ClaimModel(
        original_claim="Meridian Grid will expand capacity 50% across 2027.",
        company_name="Meridian Grid",
        ticker="MGS",
        claim_direction="BULLISH",
        provenance_status="REAL"
    )
    db_session.add(claim)
    db_session.commit()

    ev1 = EvidenceModel(
        title="MGS Form 10-Q Backlog",
        content_summary="Contracted backlog reached $2.4B with firm utility delivery commitments.",
        publisher="SEC EDGAR",
        exchange="SEC",
        evidence_category="REGULATORY_FILING",
        source_url="https://sec.gov/edgar/mgs-q3",
        provenance_status="REAL"
    )
    db_session.add(ev1)
    db_session.commit()

    assoc = ClaimEvidenceModel(claim_id=claim.id, evidence_id=ev1.id, relevance_score=1.0)
    db_session.add(assoc)
    db_session.commit()

    # Query scenarios
    scenarios_res = client.get("/api/v1/decision-lab/scenarios")
    assert scenarios_res.status_code == 200
    scenarios = scenarios_res.json()
    assert len(scenarios) >= 1
    mgs_sc = next((s for s in scenarios if s["id"] == claim.id), None)
    assert mgs_sc is not None
    assert mgs_sc["ticker"] == "MGS"
    assert len(mgs_sc["evidenceItems"]) >= 1

    # Record initial decision
    dec_create_res = client.post("/api/v1/decisions", json={
        "claim_id": claim.id,
        "initial_thesis": "Strong initial growth expectation based on reported backlog",
        "initial_confidence": 85.0,
        "initial_allocation": 50.0,
        "assumptions_evaluated": ["Order delivery lead time"]
    })
    assert dec_create_res.status_code == 201
    decision_data = dec_create_res.json()
    dec_id = decision_data["id"]

    # Record revised decision
    dec_revise_res = client.put(f"/api/v1/decisions/{dec_id}/revise", json={
        "revised_thesis": "Adjusted view downwards due to 84-week transformer constraints",
        "revised_confidence": 58.0,
        "revised_allocation": 30.0,
        "reason_for_change": "Observed severe supplier lead times",
        "assumptions_evaluated": ["Order delivery lead time", "Transformer lead times"]
    })
    assert dec_revise_res.status_code == 200
    revised_data = dec_revise_res.json()
    assert revised_data["revised_confidence"] == 58.0
    assert revised_data["sensitivity_summary"] is not None
    assert revised_data["sensitivity_summary"]["confidence_delta_points"] == -27.0


def test_semantic_evidence_classification_directional(db_session):
    """Verifies that evidence is classified semantically based on claim thesis and directional context."""
    bullish_claim = ClaimModel(
        original_claim="Vortex Semis will capture 60% market share and expand margins.",
        claim_direction="BULLISH",
        provenance_status="REAL"
    )
    bearish_claim = ClaimModel(
        original_claim="Legacy Retail will face severe margin decline and insolvency.",
        claim_direction="BEARISH",
        provenance_status="REAL"
    )
    db_session.add_all([bullish_claim, bearish_claim])
    db_session.commit()

    ev_growth = EvidenceModel(
        title="Vortex Patent Award and Order Surge",
        content_summary="Company reported record patent approval and massive revenue growth acceleration.",
        publisher="Patent Office",
        exchange="USPTO",
        evidence_category="REGULATORY_FILING",
        provenance_status="REAL",
        source_url="https://uspto.gov/patents/vrtx"
    )
    ev_risk = EvidenceModel(
        title="Subcomponent Bottleneck and Severe Delay Warning",
        content_summary="Foundry reported production drop, severe shipment delay, and supply bottleneck.",
        publisher="Industry Analyst",
        exchange="Reports",
        evidence_category="INDUSTRY_REPORT",
        provenance_status="REAL",
        source_url="https://reports.com/delay"
    )
    db_session.add_all([ev_growth, ev_risk])
    db_session.commit()

    db_session.add_all([
        ClaimEvidenceModel(claim_id=bullish_claim.id, evidence_id=ev_growth.id, relevance_score=1.0),
        ClaimEvidenceModel(claim_id=bullish_claim.id, evidence_id=ev_risk.id, relevance_score=1.0),
        ClaimEvidenceModel(claim_id=bearish_claim.id, evidence_id=ev_growth.id, relevance_score=1.0),
        ClaimEvidenceModel(claim_id=bearish_claim.id, evidence_id=ev_risk.id, relevance_score=1.0)
    ])
    db_session.commit()

    # For Bullish claim: growth supports, risk contradicts
    enriched_bull = _enrich_claim_response(bullish_claim, db_session)
    assert any("Patent" in e["title"] for e in enriched_bull.supportingEvidence)
    assert any("Bottleneck" in e["title"] for e in enriched_bull.contradictoryEvidence)

    # For Bearish claim: risk supports thesis, growth contradicts thesis
    enriched_bear = _enrich_claim_response(bearish_claim, db_session)
    assert any("Bottleneck" in e["title"] for e in enriched_bear.supportingEvidence)
    assert any("Patent" in e["title"] for e in enriched_bear.contradictoryEvidence)
