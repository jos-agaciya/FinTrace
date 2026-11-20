import pytest
from unittest.mock import AsyncMock, patch
from backend.app.integrations.ai_client import ProviderUnavailableException


def test_analysis_run_success(client):
    # 1. Create a claim
    claim = client.post("/api/v1/claims", json={
        "original_claim": "XYZ Ltd will rise 30% in two months. Strong fundamentals.",
        "provenance_status": "USER_PROVIDED"
    }).json()
    claim_id = claim["id"]

    # 2. Mock primary and secondary providers
    mock_primary_output = {
        "direction": "BULLISH",
        "target": 30.0,
        "horizon": "two months",
        "missing_fields": ["entry_condition", "exit_condition", "invalidation_condition"],
        "interpretation_summary": "Strong fundamental bullish expectation."
    }
    mock_secondary_output = {
        "agrees": True,
        "material_disagreements": [],
        "critique": "Analysis aligns with stated metrics."
    }

    with patch("backend.app.integrations.ai_client.GroqProvider.analyze_claim", new_callable=AsyncMock) as mock_groq, \
         patch("backend.app.integrations.ai_client.GeminiProvider.review_analysis", new_callable=AsyncMock) as mock_gemini:

        mock_groq.return_value = mock_primary_output
        mock_gemini.return_value = mock_secondary_output

        res = client.post(f"/api/v1/analysis/{claim_id}/run")
        assert res.status_code == 200
        data = res.json()

        assert data["analysis"]["claim_id"] == claim_id
        assert data["analysis"]["provider_status"] == "SUCCESS"
        assert data["analysis"]["falsifiability_score"] > 0
        assert len(data["missing_fields_list"]) > 0

        # Verify 4 epistemological categories
        cats = data["categorized_statements_parsed"]
        assert len(cats["AI_INTERPRETATION"]) > 0
        assert len(cats["USER_ASSUMPTION"]) > 0
        assert len(cats["UNRESOLVED_QUESTION"]) > 0

        # Verify Interpretation Forks generated
        assert len(data["interpretation_forks"]) >= 2
        assert any("Fundamental Thesis" in f["title"] for f in data["interpretation_forks"])
        assert any("Speculative Momentum" in f["title"] for f in data["interpretation_forks"])


def test_analysis_fallback_used(client):
    claim = client.post("/api/v1/claims", json={
        "original_claim": "ABC Corp will drop 15% next week.",
        "provenance_status": "USER_PROVIDED"
    }).json()
    claim_id = claim["id"]

    with patch("backend.app.integrations.ai_client.GroqProvider.analyze_claim", new_callable=AsyncMock) as mock_groq, \
         patch("backend.app.integrations.ai_client.GeminiProvider.analyze_claim", new_callable=AsyncMock) as mock_gemini:

        # Primary provider fails with connection or auth issue
        mock_groq.side_effect = ProviderUnavailableException("Connection to Groq timed out")
        mock_gemini.return_value = {"direction": "BEARISH", "interpretation_summary": "Bearish breakdown"}

        res = client.post(f"/api/v1/analysis/{claim_id}/run")
        assert res.status_code == 200
        data = res.json()
        assert data["analysis"]["provider_status"] == "FALLBACK_USED"
        assert "Primary provider (groq) failed" in data["analysis"]["fallback_reason"]


def test_analysis_both_providers_unavailable(client):
    claim = client.post("/api/v1/claims", json={
        "original_claim": "DEF Ltd multibagger in 1 year.",
        "provenance_status": "USER_PROVIDED"
    }).json()
    claim_id = claim["id"]

    with patch("backend.app.integrations.ai_client.GroqProvider.analyze_claim", new_callable=AsyncMock) as mock_groq, \
         patch("backend.app.integrations.ai_client.GeminiProvider.analyze_claim", new_callable=AsyncMock) as mock_gemini:

        mock_groq.side_effect = ProviderUnavailableException("Groq offline")
        mock_gemini.side_effect = ProviderUnavailableException("Gemini quota exceeded")

        res = client.post(f"/api/v1/analysis/{claim_id}/run")
        assert res.status_code == 200
        data = res.json()
        assert data["analysis"]["provider_status"] == "PROVIDER_UNAVAILABLE"
        # Deterministic falsifiability still calculated without hallucinations
        assert data["analysis"]["falsifiability_score"] is not None


def test_analysis_material_disagreement_needs_verification(client):
    claim = client.post("/api/v1/claims", json={
        "original_claim": "GHI Ltd will surge 50%.",
        "provenance_status": "USER_PROVIDED"
    }).json()
    claim_id = claim["id"]

    with patch("backend.app.integrations.ai_client.GroqProvider.analyze_claim", new_callable=AsyncMock) as mock_groq, \
         patch("backend.app.integrations.ai_client.GeminiProvider.review_analysis", new_callable=AsyncMock) as mock_gemini:

        mock_groq.return_value = {"direction": "BULLISH", "interpretation_summary": "Extremely bullish"}
        mock_secondary_review = {
            "agrees": False,
            "material_disagreements": ["Debt obligations threaten solvency; claim contradicts official filings."],
            "critique": "Unrealistic price projection."
        }
        mock_gemini.return_value = mock_secondary_review

        res = client.post(f"/api/v1/analysis/{claim_id}/run")
        assert res.status_code == 200
        data = res.json()
        assert data["analysis"]["provider_status"] == "NEEDS_VERIFICATION"
        assert data["analysis"]["validation_status"] == "WARNING"
