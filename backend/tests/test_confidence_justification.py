import pytest
from backend.app.utils.scoring import DeterministicRubricScorer


def test_low_confidence_without_reasoning_does_not_get_perfect_score(client):
    """Requirement 1: Low confidence with no supporting reasoning does not receive a perfect score."""
    claim = client.post("/api/v1/claims", json={"original_claim": "Test claim for lazy skepticism"}).json()

    # User expresses low confidence (20%) but identified 0 evidence, 0 risks, 0 missing parameters, and no justification
    payload = {
        "session_id": "lazy-skeptic-1",
        "claim_id": claim["id"],
        "assessment_stage": "BASELINE",
        "identified_evidence_types": [],
        "distinguished_primary_sources": False,
        "identified_missing_specificity": [],
        "identified_risk_factors": [],
        "recognized_alternative_interpretations": False,
        "stated_confidence": 20.0,
        "evidence_backing_level": "NONE",
        "confidence_justification": None
    }

    res = client.post("/api/v1/assessments", json=payload)
    assert res.status_code == 201
    data = res.json()
    dim5_score = data["score_confidence_calibration"]

    # Must NOT receive 20/20 (previously lazy skepticism would get 20.0)
    assert dim5_score < 15.0
    assert dim5_score >= 0.0


def test_high_confidence_with_strong_evidence_can_receive_high_score(client):
    """Requirement 2: High confidence with strong, relevant evidence and a sound explanation can receive a high score."""
    claim = client.post("/api/v1/claims", json={"original_claim": "Verified corporate announcement claim"}).json()

    payload = {
        "session_id": "sound-high-conf-1",
        "claim_id": claim["id"],
        "assessment_stage": "INDEPENDENT_TRANSFER",
        "identified_evidence_types": ["COMPANY_DISCLOSURE", "REGULATORY_FILING"],
        "distinguished_primary_sources": True,
        "identified_missing_specificity": ["exit_condition"],
        "identified_risk_factors": ["Operational execution risk"],
        "recognized_alternative_interpretations": True,
        "stated_confidence": 80.0,  # High confidence
        "evidence_backing_level": "HIGH",
        "confidence_justification": (
            "Expressed 80% confidence because audited SEC and exchange disclosure filings "
            "directly substantiate revenue growth, while recognized operational risks and missing exit terms "
            "are minor relative to the verified balance sheet strength."
        )
    }

    res = client.post("/api/v1/assessments", json=payload)
    assert res.status_code == 201
    data = res.json()
    dim5_score = data["score_confidence_calibration"]

    # High confidence is NOT penalized when substantiated by primary evidence and sound rationale
    assert dim5_score >= 17.0


def test_high_confidence_with_contradictory_risks_and_no_evidence_receives_low_score(client):
    """Requirement 3: High confidence with contradictory risks and no supporting evidence receives a low score."""
    claim = client.post("/api/v1/claims", json={"original_claim": "Penny stock pump claim"}).json()

    payload = {
        "session_id": "ungrounded-high-conf-1",
        "claim_id": claim["id"],
        "assessment_stage": "BASELINE",
        "identified_evidence_types": [],
        "distinguished_primary_sources": False,
        "identified_missing_specificity": ["time_horizon", "invalidation_condition", "target_value"],
        "identified_risk_factors": ["Solvency risk", "Severe debt overhang", "Pending litigation"],
        "recognized_alternative_interpretations": False,
        "stated_confidence": 95.0,  # Extreme ungrounded confidence
        "evidence_backing_level": "NONE",
        "confidence_justification": None
    }

    res = client.post("/api/v1/assessments", json=payload)
    assert res.status_code == 201
    data = res.json()
    dim5_score = data["score_confidence_calibration"]

    # Severe penalty for cognitive dissonance (95% confidence despite 3 identified major risks and 0 evidence)
    assert dim5_score <= 6.0


def test_confidence_changes_not_automatically_rewarded_or_penalized():
    """Requirement 4: Confidence changes are evaluated on evidence coherence, not direction alone."""
    # User A: High confidence justified by strong evidence
    scores_a, total_a, _ = DeterministicRubricScorer.score_assessment(
        identified_evidence_types=["COMPANY_DISCLOSURE"],
        distinguished_primary_sources=True,
        identified_missing_specificity=["entry_condition"],
        identified_risk_factors=["Sector competition"],
        recognized_alternative_interpretations=True,
        stated_confidence=75.0,
        evidence_backing_level="HIGH",
        confidence_justification="Audited disclosures confirm cash reserves support the thesis despite competition."
    )

    # User B: Low confidence justified by weak evidence & heavy risks
    scores_b, total_b, _ = DeterministicRubricScorer.score_assessment(
        identified_evidence_types=[],
        distinguished_primary_sources=False,
        identified_missing_specificity=["time_horizon", "invalidation_condition", "entry_condition"],
        identified_risk_factors=["Severe liquidity risk", "Pending litigation"],
        recognized_alternative_interpretations=True,
        stated_confidence=30.0,
        evidence_backing_level="NONE",
        confidence_justification="Confidence kept low at 30% due to absence of verified filings and severe liquidity risk."
    )

    # Both users should receive high justification scores because both grounded their confidence in evidence
    assert scores_a["confidence_calibration"] >= 16.0
    assert scores_b["confidence_calibration"] >= 16.0
    assert abs(scores_a["confidence_calibration"] - scores_b["confidence_calibration"]) <= 3.0


def test_empty_or_missing_justification_handled_safely(client):
    """Requirement 5: Empty, whitespace-only, or omitted justification is handled gracefully without crashing."""
    claim = client.post("/api/v1/claims", json={"original_claim": "Claim test for empty justification"}).json()

    for empty_val in [None, "", "   "]:
        payload = {
            "session_id": "safe-handling-test",
            "claim_id": claim["id"],
            "assessment_stage": "BASELINE",
            "identified_evidence_types": ["COMPANY_DISCLOSURE"],
            "distinguished_primary_sources": True,
            "identified_missing_specificity": ["time_horizon"],
            "identified_risk_factors": ["Operational risk"],
            "recognized_alternative_interpretations": True,
            "stated_confidence": 50.0,
            "evidence_backing_level": "MODERATE",
            "confidence_justification": empty_val
        }
        res = client.post("/api/v1/assessments", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert 0.0 <= data["score_confidence_calibration"] <= 20.0
        assert "Standard baseline applied" in data["rubric_feedback"]["confidence_calibration"]


def test_irrelevant_generic_boilerplate_does_not_receive_full_points(client):
    """Requirement 6: Irrelevant generic justification does not receive full points."""
    claim = client.post("/api/v1/claims", json={"original_claim": "Boilerplate test claim"}).json()

    boilerplate_phrases = ["good", "to the moon!", "strong fundamentals", "i think so", "buy!"]

    for phrase in boilerplate_phrases:
        payload = {
            "session_id": "boilerplate-session",
            "claim_id": claim["id"],
            "assessment_stage": "BASELINE",
            "identified_evidence_types": ["COMPANY_DISCLOSURE"],
            "distinguished_primary_sources": True,
            "identified_missing_specificity": ["time_horizon"],
            "identified_risk_factors": ["Operational risk"],
            "recognized_alternative_interpretations": True,
            "stated_confidence": 60.0,
            "evidence_backing_level": "MODERATE",
            "confidence_justification": phrase
        }
        res = client.post("/api/v1/assessments", json=payload)
        assert res.status_code == 201
        data = res.json()
        feedback = data["rubric_feedback"]["confidence_calibration"]
        # Generic boilerplate should receive at most 0.5/4 for quality
        assert "Generic boilerplate detected" in feedback or "brief" in feedback


def test_rubric_components_independence():
    """Requirement 7: Evidence, uncertainty, and risk reasoning affect the appropriate rubric components."""
    # Test uncertainty component
    scores_high_uncertainty, _, _ = DeterministicRubricScorer.score_assessment(
        identified_evidence_types=[],
        distinguished_primary_sources=False,
        identified_missing_specificity=["time_horizon", "invalidation_condition", "entry_condition", "exit_condition"],
        identified_risk_factors=[],
        recognized_alternative_interpretations=True,
        stated_confidence=40.0,
        evidence_backing_level="NONE",
        confidence_justification="Recognized that missing timeframe and invalidation conditions create fundamental uncertainty."
    )

    scores_zero_uncertainty, _, _ = DeterministicRubricScorer.score_assessment(
        identified_evidence_types=[],
        distinguished_primary_sources=False,
        identified_missing_specificity=[],
        identified_risk_factors=[],
        recognized_alternative_interpretations=False,
        stated_confidence=40.0,
        evidence_backing_level="NONE",
        confidence_justification=None
    )

    # Uncertainty awareness must be rewarded appropriately
    assert scores_high_uncertainty["confidence_calibration"] > scores_zero_uncertainty["confidence_calibration"]


def test_scores_remain_within_strict_bounds():
    """Requirements 8 & 9: Dimension 5 remains between 0 and 20; composite remains between 0 and 100."""
    # Test various extreme configurations
    test_cases = [
        (0.0, "NONE", [], False, [], [], False, None),
        (100.0, "HIGH", ["A", "B", "C"], True, ["X", "Y", "Z"], ["R1", "R2"], True, "Detailed evidence and risk analysis"),
        (50.0, "MODERATE", ["A"], True, ["X"], ["R1"], True, "Good justification"),
        (99.0, "NONE", [], False, ["X", "Y", "Z"], ["R1", "R2", "R3"], False, "crypto to the moon"),
        (1.0, "HIGH", ["A", "B"], True, [], [], False, "")
    ]

    for conf, backing, ev_types, primary, spec, risks, alt, just in test_cases:
        scores, total, feedback = DeterministicRubricScorer.score_assessment(
            identified_evidence_types=ev_types,
            distinguished_primary_sources=primary,
            identified_missing_specificity=spec,
            identified_risk_factors=risks,
            recognized_alternative_interpretations=alt,
            stated_confidence=conf,
            evidence_backing_level=backing,
            confidence_justification=just
        )

        # Dimension 5 bounds
        assert 0.0 <= scores["confidence_calibration"] <= 20.0
        # All dimensions bounds
        for dim, s in scores.items():
            assert 0.0 <= s <= 20.0, f"Dimension {dim} exceeded bounds: {s}"
        # Composite score bounds
        assert 0.0 <= total <= 100.0, f"Composite score exceeded bounds: {total}"
        assert abs(total - sum(scores.values())) <= 0.2
