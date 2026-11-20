# FinTrace — Comprehensive API Reference

This document provides complete documentation for all HTTP endpoints exposed by the FinTrace backend API.

- **Base URL:** `http://localhost:8000/api/v1`
- **Interactive Documentation:** `http://localhost:8000/docs` (Swagger UI)
- **ReDoc Documentation:** `http://localhost:8000/redoc`
- **Authentication:** **None** (Open session-based architecture for hackathon evaluation; sessions are tracked via caller-supplied `session_id`).

---

## Table of Contents
1. [System & Health](#1-system--health)
2. [Claims Management](#2-claims-management)
3. [Evidence & Exchange Disclosures](#3-evidence--exchange-disclosures)
4. [Decision Robustness Compiler & Analysis](#4-decision-robustness-compiler--analysis)
5. [Virtual Decision Lab](#5-virtual-decision-lab)
6. [Investor Assessments & Scoring](#6-investor-assessments--scoring)
7. [Dashboard & Analytics](#7-dashboard--analytics)

---

## 1. System & Health

### `GET /`
- **Description:** Root welcome endpoint confirming service operational status.
- **Request Body:** None.
- **Response (200 OK):**
```json
{
  "message": "Welcome to FinTrace API",
  "status": "operational",
  "docs": "/docs"
}
```

### `GET /api/v1/health`
- **Description:** System health check endpoint for monitoring uptime, service availability, and database connectivity.
- **Request Body:** None.
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "app_name": "FinTrace API",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## 2. Claims Management

### `POST /api/v1/claims`
- **Description:** Submits a raw or annotated financial claim. Performs rule-based entity ambiguity checks and preserves omitted parameters strictly as `null`.
- **Request Headers:** `Content-Type: application/json`
- **Request Schema (`ClaimCreate`):**
  - `original_claim` *(string, required)*: Minimum 5 characters.
  - `source_url` *(string, optional)*: Observed link.
  - `source_platform` *(string, optional)*: E.g., `"Telegram"`, `"Twitter/X"`, `"Reddit"`.
  - `provenance_status` *(string, optional)*: Enum: `REAL`, `SYNTHETIC`, `USER_PROVIDED` (default), `AI_GENERATED`.
  - `company_name` *(string, optional)*
  - `ticker` *(string, optional)*
  - `exchange` *(string, optional)*: E.g., `"NSE"`, `"BSE"`, `"NYSE"`.
  - `claim_direction` *(string, optional)*: Enum: `BULLISH`, `BEARISH`, `NEUTRAL`, `UNKNOWN`.
  - `target_value` *(float, optional)*
  - `target_unit` *(string, optional)*: E.g., `"%"`, `"INR"`, `"USD"`.
  - `time_horizon` *(string, optional)*: E.g., `"2 weeks"`, `"Q3 FY26"`.
  - `entry_condition` *(string, optional)*
  - `exit_condition` *(string, optional)*
  - `invalidation_condition` *(string, optional)*
  - `evidence_or_rationale` *(string, optional)*
- **Response (201 Created):**
```json
{
  "id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
  "original_claim": "Infosys will surge 20% in the next 3 weeks after strong Q3 results.",
  "source_url": "https://x.com/trader_tips/status/123456",
  "source_platform": "Twitter/X",
  "submitted_at": "2026-11-20T14:30:00Z",
  "company_name": "Infosys",
  "ticker": "INFY",
  "exchange": "NSE",
  "claim_direction": "BULLISH",
  "target_value": 20.0,
  "target_unit": "%",
  "time_horizon": "3 weeks",
  "entry_condition": null,
  "exit_condition": null,
  "invalidation_condition": null,
  "evidence_or_rationale": null,
  "provenance_status": "USER_PROVIDED",
  "is_ambiguous_entity": false,
  "entity_ambiguity_notes": null,
  "created_at": "2026-11-20T14:30:00Z"
}
```
- **Error Responses:**
  - `422 Unprocessable Entity`: Claim text shorter than 5 characters or invalid data types.

### `GET /api/v1/claims`
- **Description:** Returns paginated list of submitted claims ordered newest first.
- **Query Parameters:**
  - `skip` *(int, default: 0)*
  - `limit` *(int, default: 50, max: 100)*
- **Response (200 OK):**
```json
{
  "total": 1,
  "items": [
    {
      "id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
      "original_claim": "Infosys will surge 20% in the next 3 weeks...",
      "company_name": "Infosys",
      "ticker": "INFY",
      "provenance_status": "USER_PROVIDED",
      "created_at": "2026-11-20T14:30:00Z"
    }
  ]
}
```

### `GET /api/v1/claims/{claim_id}`
- **Description:** Retrieves a single claim by UUID.
- **Response (200 OK):** `ClaimResponse` object.
- **Error Responses:** `404 Not Found` if `claim_id` does not exist.

### `DELETE /api/v1/claims/{claim_id}`
- **Description:** Deletes a claim and cascades deletion across its associated analyses, interpretation forks, evidence associations, and decision lab records.
- **Response (204 No Content):** Empty body.
- **Error Responses:** `404 Not Found` if `claim_id` does not exist.

---

## 3. Evidence & Exchange Disclosures

### `POST /api/v1/evidence`
- **Description:** Manually records a verified evidence item and stores it in the global registry.
- **Request Schema (`EvidenceCreate`):**
  - `title` *(string, required)*: Minimum 3 characters.
  - `document_title` *(string, optional)*: Specific filing name.
  - `publisher` *(string, required)*: Minimum 2 characters.
  - `source_url` *(string, required)*: Minimum 5 characters.
  - `publication_date` *(datetime string, optional)*: ISO 8601 format.
  - `evidence_category` *(string, optional)*: Enum: `COMPANY_DISCLOSURE` (default), `MARKET_DATA`, `NEWS`, `REGULATORY`, `SYNTHETIC_BENCHMARK`.
  - `company_identifier` *(string, optional)*: Company name or ticker.
  - `company_symbol` *(string, optional)*: E.g., `"INFY"`.
  - `company_isin` *(string, optional)*: E.g., `"INE009A01021"`.
  - `source_jurisdiction` *(string, optional, default: "IN")*: E.g., `"IN"`, `"US"`.
  - `exchange` *(string, optional, default: "NSE")*: E.g., `"NSE"`, `"SEC"`.
  - `content_summary` *(string, required)*: Minimum 10 characters.
  - `provenance_status` *(string, optional, default: "REAL")*: Enum: `REAL`, `SYNTHETIC`, `USER_PROVIDED`, `AI_GENERATED`.
- **Response (201 Created):**
```json
{
  "id": "e4a2c1d0-9f8e-4a6b-8c5d-2e1f0a9b8c7d",
  "title": "NSE Announcement: Q2 Audited Financial Results",
  "document_title": "Audited Standalone and Consolidated Results",
  "publisher": "NSE India",
  "source_url": "https://nsearchives.nseindia.in/corporate/INFY_Results.pdf",
  "publication_date": "2026-10-15T14:30:00Z",
  "retrieval_timestamp": "2026-11-20T14:35:00Z",
  "retrieved_at": "2026-11-20T14:35:00Z",
  "evidence_category": "COMPANY_DISCLOSURE",
  "company_identifier": "INFY",
  "company_symbol": "INFY",
  "company_isin": "INE009A01021",
  "source_jurisdiction": "IN",
  "exchange": "NSE",
  "content_summary": "Q2 revenue grew 5.1% YoY in constant currency, operating margin stood at 21.1%.",
  "provenance_status": "REAL",
  "raw_payload": null,
  "created_at": "2026-11-20T14:35:00Z"
}
```

### `GET /api/v1/evidence/{claim_id}`
- **Description:** Returns all verified evidence items linked to a given claim.
- **Response (200 OK):**
```json
{
  "claim_id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
  "total": 1,
  "items": [
    {
      "claim_id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
      "evidence": {
        "id": "e4a2c1d0-9f8e-4a6b-8c5d-2e1f0a9b8c7d",
        "title": "NSE Announcement: Q2 Audited Financial Results",
        "publisher": "NSE India",
        "source_url": "https://nsearchives.nseindia.in/corporate/INFY_Results.pdf",
        "publication_date": "2026-10-15T14:30:00Z",
        "retrieval_timestamp": "2026-11-20T14:35:00Z",
        "evidence_category": "COMPANY_DISCLOSURE",
        "company_symbol": "INFY",
        "company_isin": "INE009A01021",
        "source_jurisdiction": "IN",
        "exchange": "NSE",
        "content_summary": "Q2 revenue grew 5.1% YoY...",
        "provenance_status": "REAL"
      },
      "relevance_score": 1.0,
      "association_notes": "Automated corporate disclosure retrieval"
    }
  ]
}
```

### `GET /api/v1/evidence/item/{evidence_id}`
- **Description:** Retrieves a single evidence record by UUID.
- **Response (200 OK):** `EvidenceResponse` object.
- **Error Responses:** `404 Not Found`.

### `POST /api/v1/evidence/{claim_id}/retrieve`
- **Description:** Triggers automated multi-exchange disclosure retrieval:
  1. Resolves ticker / company name against verified registry (`INFY`, `TCS`, `RELIANCE`, `HDFCBANK`, `WIPRO`).
  2. Queries NSE India corporate announcements API.
  3. Queries SEC EDGAR submissions API strictly if the entity is a confirmed US ADR issuer.
  4. Automatically deduplicates identical source URLs.
  5. If the entity is ambiguous or unverified, safely returns 0 items without inventing citations.
- **Response (200 OK):** `ClaimEvidenceListResponse` object.
- **Error Responses:** `404 Not Found` if `claim_id` does not exist.

---

## 4. Decision Robustness Compiler & Analysis

### `POST /api/v1/analysis/{claim_id}/run`
- **Description:** Runs the multi-provider Decision Robustness Compiler pipeline:
  1. Retrieves verified evidence bundle.
  2. Requests extraction from primary provider (Groq Llama 3.3 70B).
  3. Falls back to secondary provider (Gemini 2.5 Flash) on timeout or failure.
  4. Executes independent secondary review.
  5. Flags `provider_status="NEEDS_VERIFICATION"` on material disagreements.
  6. Calculates deterministic falsifiability score (0–100).
  7. Categorizes statements into `SOURCE_FACT`, `AI_INTERPRETATION`, `USER_ASSUMPTION`, and `UNRESOLVED_QUESTION`.
  8. Generates two counterfactual `InterpretationFork` records.
- **Response (200 OK):**
```json
{
  "analysis": {
    "id": "1c9b8a7f-6e5d-4c3b-2a1f-0e9d8c7b6a5f",
    "claim_id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
    "primary_provider": "groq",
    "secondary_provider": "gemini",
    "provider_status": "SUCCESS",
    "fallback_reason": null,
    "falsifiability_score": 40.0,
    "missing_fields": "[\"entry_condition\", \"exit_condition\", \"invalidation_condition\"]",
    "testability_explanation": "Claim has concrete target and horizon, but lacks clear entry, exit, or invalidation boundaries.",
    "categorized_statements": "{\"SOURCE_FACT\": [...], \"AI_INTERPRETATION\": [...], \"USER_ASSUMPTION\": [...], \"UNRESOLVED_QUESTION\": [...]}",
    "validation_status": "PASSED",
    "validation_notes": null,
    "primary_output_summary": "{\"interpretation_summary\": \"Claim predicts 20% upside based on Q3 earnings...\"}",
    "secondary_output_summary": "{\"agrees\": true, \"critique\": \"Analysis verified without contradiction.\"}",
    "created_at": "2026-11-20T14:40:00Z"
  },
  "categorized_statements_parsed": {
    "SOURCE_FACT": [
      "Target value stated: 20.0 %",
      "Time horizon stated: 3 weeks",
      "Company identified: Infosys (INFY)"
    ],
    "AI_INTERPRETATION": [
      "Claim assumes momentum continuation from reported earnings.",
      "Primary provider interpretation: Claim predicts 20% upside based on Q3 earnings..."
    ],
    "USER_ASSUMPTION": [
      "Implies earnings acceleration outweighs macroeconomic headwinds.",
      "Assumes broad IT spending cycle will remain resilient."
    ],
    "UNRESOLVED_QUESTION": [
      "Missing invalidation condition: What price level or event invalidates this claim?",
      "Missing entry condition: What trigger determines optimal entry?",
      "Missing exit condition: What explicit exit criterion is defined?"
    ]
  },
  "missing_fields_list": [
    "entry_condition",
    "exit_condition",
    "invalidation_condition"
  ],
  "interpretation_forks": [
    {
      "id": "2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
      "claim_id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
      "title": "Direct Fundamental Thesis (BULLISH)",
      "description": "Interprets claim as driven by verified earnings growth and expanding operational margins over 3 weeks.",
      "ambiguous_phrase": "3 weeks",
      "assumptions": "[\"Management guidance sustained\", \"No macro headwinds\", \"Sector peer multiples hold\"]",
      "information_required": "Audited quarterly financial statements and segment reports",
      "is_ai_generated": true,
      "created_at": "2026-11-20T14:40:00Z"
    },
    {
      "id": "3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
      "claim_id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
      "title": "Speculative Momentum Thesis",
      "description": "Interprets claim as social-media momentum rally driven by retail speculation rather than fundamental valuation.",
      "ambiguous_phrase": "buy before it's too late",
      "assumptions": "[\"Short-term retail volume continues\", \"Momentum indicators stay overbought\"]",
      "information_required": "Order book depth, institutional holding shifts, exchange delivery data",
      "is_ai_generated": true,
      "created_at": "2026-11-20T14:40:00Z"
    }
  ]
}
```

### `GET /api/v1/claims/{claim_id}/analysis`
- **Description:** Retrieves the latest existing analysis and parsed statements for a claim without triggering a new LLM execution.
- **Response (200 OK):** `AnalysisDetailedResponse` object.
- **Error Responses:** `404 Not Found` if no analysis exists.

### `GET /api/v1/analysis/{analysis_id}`
- **Description:** Retrieves an analysis record by its primary key.
- **Response (200 OK):** `AnalysisResponse` object.

### `GET /api/v1/claims/{claim_id}/forks`
- **Description:** Retrieves all generated counterfactual interpretation forks for a claim.
- **Response (200 OK):** Array of `InterpretationForkResponse`.

### `POST /api/v1/claims/{claim_id}/forks`
- **Description:** Manually creates an additional user or AI interpretation fork.
- **Request Schema (`InterpretationForkCreate`):**
  - `title` *(string, required)*
  - `description` *(string, required)*
  - `ambiguous_phrase` *(string, required)*
  - `assumptions` *(list of strings, optional)*
  - `information_required` *(string, required)*
  - `is_ai_generated` *(bool, optional, default: true)*
- **Response (201 Created):** `InterpretationForkResponse`.

---

## 5. Virtual Decision Lab

### `POST /api/v1/decisions`
- **Description:** Records an initial stance and hypothetical portfolio allocation before viewing counter-evidence.
- **Request Schema (`DecisionCreate`):**
  - `claim_id` *(string, required)*
  - `interpretation_id` *(string, optional)*
  - `initial_thesis` *(string, required)*: Minimum 5 characters.
  - `initial_confidence` *(float, required)*: 0.0 to 100.0%.
  - `initial_allocation` *(float, required)*: 0.0 to 100.0%.
  - `assumptions_evaluated` *(list of strings, optional)*
- **Response (201 Created):**
```json
{
  "id": "5d6e7f8a-9b0c-1d2e-3f4a-5b6c7d8e9f0a",
  "claim_id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
  "interpretation_id": null,
  "initial_thesis": "Strong social media sentiment and positive headline revenue growth.",
  "initial_confidence": 85.0,
  "initial_allocation": 25.0,
  "revised_thesis": null,
  "revised_confidence": null,
  "revised_allocation": null,
  "reason_for_change": null,
  "assumptions_evaluated": "[\"Revenue guidance unchanged\", \"Margin expansion\"]",
  "created_at": "2026-11-20T14:45:00Z",
  "updated_at": "2026-11-20T14:45:00Z",
  "sensitivity_summary": null
}
```

### `PUT /api/v1/decisions/{decision_id}/revise`
- **Description:** Records the revised stance after the user reviews counter-evidence, regulatory disclosures, and interpretation forks. Computes sensitivity deltas automatically.
- **Request Schema (`DecisionRevise`):**
  - `revised_thesis` *(string, required)*: Minimum 5 characters.
  - `revised_confidence` *(float, required)*: 0.0 to 100.0%.
  - `revised_allocation` *(float, required)*: 0.0 to 100.0%.
  - `reason_for_change` *(string, required)*: Minimum 5 characters.
  - `assumptions_evaluated` *(list of strings, optional)*
- **Response (200 OK):**
```json
{
  "id": "5d6e7f8a-9b0c-1d2e-3f4a-5b6c7d8e9f0a",
  "claim_id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
  "initial_thesis": "Strong social media sentiment...",
  "initial_confidence": 85.0,
  "initial_allocation": 25.0,
  "revised_thesis": "Reduced position after finding no audited invalidation bounds and margin headwinds in NSE filing.",
  "revised_confidence": 40.0,
  "revised_allocation": 5.0,
  "reason_for_change": "Audited filing revealed operating margin pressures not mentioned in the viral tweet.",
  "created_at": "2026-11-20T14:45:00Z",
  "updated_at": "2026-11-20T14:48:00Z",
  "sensitivity_summary": {
    "confidence_delta_points": -45.0,
    "allocation_delta_points": -20.0,
    "reasoning_shift_type": "REDUCED_EXPOSURE",
    "shift_explanation": "Decision shifted to reduced exposure: confidence changed by -45.0 points, allocation changed by -20.0 points."
  }
}
```

### `GET /api/v1/decisions/{claim_id}`
- **Description:** Retrieves all decisions recorded for a claim.
- **Response (200 OK):** Array of `DecisionResponse`.

---

## 6. Investor Assessments & Scoring

### `POST /api/v1/assessments`
- **Description:** Submits answers evaluated against the transparent 5-dimension deterministic rubric.
- **Request Schema (`AssessmentCreate`):**
  - `session_id` *(string, required)*: Minimum 3 characters.
  - `claim_id` *(string, required)*
  - `assessment_stage` *(string, required)*: Enum: `BASELINE`, `ASSISTED_PRACTICE`, `INDEPENDENT_TRANSFER`.
  - `identified_evidence_types` *(list of strings, required)*: E.g., `["COMPANY_DISCLOSURE"]`.
  - `distinguished_primary_sources` *(bool, required)*
  - `identified_missing_specificity` *(list of strings, required)*: E.g., `["entry_condition", "invalidation_condition"]`.
  - `identified_risk_factors` *(list of strings, required)*
  - `recognized_alternative_interpretations` *(bool, required)*
  - `stated_confidence` *(float, required)*: 0.0 to 100.0%.
  - `evidence_backing_level` *(string, optional, default: "NONE")*: Enum: `NONE`, `LOW`, `MODERATE`, `HIGH`.
  - `confidence_justification` *(string, optional)*: Rationale explaining how evidence, uncertainty, and risks connect to stated confidence.
- **Response (201 Created):**
```json
{
  "id": "a984023c-99a1-4328-8742-1c0989b5cfa1",
  "session_id": "investor-session-101",
  "claim_id": "7b8f9e21-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
  "assessment_stage": "BASELINE",
  "score_evidence_eval": 15.0,
  "score_claim_specificity": 12.0,
  "score_risk_awareness": 10.0,
  "score_assumption_awareness": 20.0,
  "score_confidence_calibration": 17.5,
  "total_score": 74.5,
  "dimension_scores": {
    "evidence_evaluation": 15.0,
    "claim_specificity": 12.0,
    "risk_awareness": 10.0,
    "assumption_awareness": 20.0,
    "confidence_calibration": 17.5
  },
  "rubric_feedback": {
    "evidence_evaluation": "Scored 15.0/20. Correctly separated primary regulatory filings from unverified claims.",
    "claim_specificity": "Scored 12.0/20. Identified 2 unstated claim parameters (missing invalidation bounds).",
    "risk_awareness": "Scored 10.0/20. Articulated 2 distinct downside risk factors.",
    "assumption_awareness": "Scored 20.0/20. Demonstrated clear comprehension of multiple interpretations.",
    "confidence_calibration": "Confidence Justification & Epistemic Alignment: Scored 17.5/20. [Evidence-Confidence: 5.5/6, Uncertainty Awareness: 4.0/5, Risk Relationship: 4.0/5, Justification Quality: 4.0/4]. Substantive, coherent justification connecting confidence to evidence, uncertainty, and risks."
  },
  "created_at": "2026-11-20T14:50:00Z"
}
```

### `GET /api/v1/assessments/compare/{session_id}`
- **Description:** Computes rigorous learning delta between `BASELINE` and `INDEPENDENT_TRANSFER` stages for a user session.
- **Response (200 OK):**
```json
{
  "session_id": "investor-session-101",
  "baseline_score": 45.0,
  "latest_transfer_score": 78.5,
  "percentage_point_delta": 33.5,
  "dimension_deltas": {
    "evidence_evaluation": 7.5,
    "claim_specificity": 8.0,
    "risk_awareness": 6.0,
    "assumption_awareness": 5.0,
    "confidence_calibration": 7.0
  },
  "comparison_summary": "Investor demonstrated a +33.5 percentage-point improvement in independent critical evaluation capability."
}
```
- **Error Responses:** `400 Bad Request` if user has not completed both a baseline and a transfer assessment.

### `GET /api/v1/assessments/history`
- **Description:** Retrieves paginated assessment evaluations.
- **Query Parameters:** `session_id` (optional), `skip` (default: 0), `limit` (default: 50).
- **Response (200 OK):** Array of `AssessmentResponse`.

### `GET /api/v1/assessments/{assessment_id}`
- **Description:** Retrieves an assessment record by UUID.
- **Response (200 OK):** `AssessmentResponse` object.

---

## 7. Dashboard & Analytics

### `GET /api/v1/dashboard/overview`
- **Description:** Platform-wide metrics, total claims analyzed, evidence count, and latest claims/decisions.
- **Response (200 OK):**
```json
{
  "total_claims_submitted": 42,
  "total_claims_analyzed": 38,
  "total_evidence_records": 115,
  "total_decisions_recorded": 29,
  "recent_claims": [...],
  "recent_decisions": [...]
}
```

### `GET /api/v1/dashboard/progress?session_id={session_id}`
- **Description:** Stage completion status and rubric delta for a given user session.
- **Response (200 OK):**
```json
{
  "session_id": "investor-session-101",
  "has_baseline": true,
  "has_independent_transfer": true,
  "baseline_total_score": 45.0,
  "latest_transfer_score": 78.5,
  "percentage_point_delta": 33.5,
  "dimension_breakdown": {
    "evidence_evaluation": 15.0,
    "claim_specificity": 12.0,
    "risk_awareness": 10.0,
    "assumption_awareness": 20.0,
    "confidence_calibration": 17.5
  },
  "status": "ASSESSMENT_COMPLETED",
  "learning_progress_summary": "Completed Baseline and Independent Transfer assessments. Critical capability improved by +33.5 points."
}
```

### `GET /api/v1/dashboard/history?session_id={session_id}`
- **Description:** Chronological timeline of all assessments completed in a session.
- **Response (200 OK):**
```json
{
  "session_id": "investor-session-101",
  "total_evaluations": 3,
  "evaluation_timeline": [...]
}
```
