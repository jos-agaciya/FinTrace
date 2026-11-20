# FinTrace API Integration Contract

**Document Version:** 1.1.0  
**Target Audience:** Frontend Team (`nakul-frontend`), AI Team (`venkat-ai`), Backend Integration  
**Base URL:** `http://localhost:8000/api/v1`  
**Interactive Docs (Swagger UI):** `http://localhost:8000/docs`  
**Interactive Docs (ReDoc):** `http://localhost:8000/redoc`

---

## 1. Global Architectural Standards

1. **Timestamps:** All timestamps are formatted in ISO 8601 with UTC timezone (e.g., `2026-11-20T14:15:22.039126Z`).
2. **Identifiers:** All entity IDs are RFC 4122 standard UUIDv4 strings.
3. **Missing Data Policy:** FinTrace never fabricates missing claim parameters. Missing fields return `null` and must be presented as `"Not Stated"` in the UI.
4. **Epistemological Classification:** All factual assertions must be attributed to one of four categories:
   - `SOURCE_FACT`: Verified corporate disclosures or regulatory records.
   - `AI_INTERPRETATION`: Machine-generated hypotheses and parse trees.
   - `USER_ASSUMPTION`: Unverified retail beliefs or sentiment drivers.
   - `UNRESOLVED_QUESTION`: Information needed to test or falsify the claim.
5. **CORS:** Configured via `CORS_ORIGINS` environment variable (defaults include `http://localhost:3000` and `http://localhost:5173`).

---

## 2. Standard Error Response Format

All error responses return standard HTTP error codes with a JSON body:
```json
{
  "detail": "Descriptive message explaining why the operation failed."
}
```

Common status codes:
- `400 Bad Request`: Invalid payload or missing prerequisite stages.
- `404 Not Found`: Entity with specified ID does not exist.
- `422 Unprocessable Entity`: Request body failed Pydantic schema validation.
- `500 Internal Server Error`: Unhandled server exception.

---

## 3. Endpoints Specification

### A. Health & Status
#### `GET /api/v1/health`
Verifies backend service availability and active environment.
- **Response:** `200 OK`
```json
{
  "status": "healthy",
  "app_name": "FinTrace API",
  "environment": "development",
  "version": "1.0.0"
}
```

---

### B. Claim Management

#### `POST /api/v1/claims`
Ingests a plain-text financial claim. Preserves original text exactly as submitted.
- **Request Body:**
```json
{
  "original_claim": "XYZ Ltd. will rise 30% in the next two months. Strong fundamentals. Buy before it's too late!",
  "source_url": "https://t.me/channel/123",
  "source_platform": "Telegram",
  "provenance_status": "USER_PROVIDED"
}
```
*`provenance_status` options:* `"REAL"`, `"SYNTHETIC"`, `"USER_PROVIDED"`, `"AI_GENERATED"`.

- **Response:** `201 Created`
```json
{
  "id": "e7b0d91a-7b3b-4876-b608-8121f1d1f05e",
  "original_claim": "XYZ Ltd. will rise 30% in the next two months. Strong fundamentals. Buy before it's too late!",
  "source_url": "https://t.me/channel/123",
  "source_platform": "Telegram",
  "submitted_at": "2026-11-20T14:15:22.039126Z",
  "company_name": "XYZ Ltd",
  "ticker": null,
  "exchange": null,
  "claim_direction": "BULLISH",
  "target_value": 30.0,
  "target_unit": "%",
  "time_horizon": "next two months",
  "entry_condition": null,
  "exit_condition": null,
  "invalidation_condition": null,
  "evidence_or_rationale": null,
  "provenance_status": "USER_PROVIDED",
  "is_ambiguous_entity": false,
  "entity_ambiguity_notes": null,
  "created_at": "2026-11-20T14:15:22.040112Z"
}
```

#### `GET /api/v1/claims`
Retrieves paginated list of claims.
- **Query Parameters:** `skip` (int, default 0), `limit` (int, default 50).
- **Response:** `200 OK`

#### `GET /api/v1/claims/{claim_id}`
Retrieves a single claim by UUID.
- **Response:** `200 OK` or `404 Not Found`.

#### `DELETE /api/v1/claims/{claim_id}`
Deletes a user-submitted claim and cascades to related analyses and decisions.
- **Response:** `204 No Content` or `404 Not Found`.

---

### C. Evidence Retrieval & Provenance

#### Provider Architecture & Strict Entity Resolution
- **Primary Indian Source (`NSE`):** Queries NSE India corporate announcements (`https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}`) for verified Indian-listed entities (e.g. INFY, TCS, RELIANCE, HDFCBANK, WIPRO). Extracts official announcement text, ISIN, announcement datetime, and direct PDF circulars from `https://nsearchives.nseindia.in/corporate/...`.
- **Supplementary US Source (`SEC EDGAR`):** Queries SEC EDGAR (`data.sec.gov`) **strictly** for verified US registrants and dual-listed ADR issuers (e.g., Infosys ADR CIK 0001067491).
- **Strict Anti-Hallucination & Entity Guards:**
  - Indian domestic companies (e.g. TCS, Reliance Industries) are **never** queried against SEC company-name search, completely preventing false entity collisions (e.g., Reliance Industries matching *Reliance, Inc.* of Scottsdale, AZ).
  - Unverified or ambiguous entities return an empty evidence list (`[]`) rather than fabricated citations or speculative web snippets.
- **BSE Status Notice:** Direct automated retrieval from BSE is currently marked unsupported due to Akamai WAF access restrictions returning 403 Forbidden without authenticated enterprise feeds; NSE serves as the robust primary exchange disclosures source.

#### `POST /api/v1/evidence`
Manually records a verified evidence record.
- **Request Body:**
```json
{
  "title": "Quarterly Financial Statements - Q3 FY26",
  "document_title": "Audited Standalone and Consolidated Financial Results",
  "publisher": "NSE India Corporate Disclosures",
  "source_url": "https://nsearchives.nseindia.in/corporate/INFY_Q3_Results.pdf",
  "publication_date": "2026-10-15T14:30:00Z",
  "evidence_category": "COMPANY_DISCLOSURE",
  "company_identifier": "INFY",
  "company_symbol": "INFY",
  "company_isin": "INE009A01021",
  "source_jurisdiction": "IN",
  "exchange": "NSE",
  "content_summary": "Net profit increased 12% YoY, EBITDA margins held at 18.5%.",
  "provenance_status": "REAL"
}
```

#### `GET /api/v1/evidence/{claim_id}`
Retrieves all evidence associated with a claim.
- **Response:** `200 OK`

#### `POST /api/v1/evidence/{claim_id}/retrieve`
Triggers verifiable automated disclosure retrieval for the claim via NSE India (primary) and SEC EDGAR (for verified ADRs). Deduplicates identical URLs and handles missing publication dates gracefully.
- **Response:** `200 OK` (ClaimEvidenceListResponse).

---

### D. Decision Robustness Compiler & Analysis

#### `POST /api/v1/analysis/{claim_id}/run`
Triggers the multi-provider Decision Robustness Compiler workflow.
- **Response:** `200 OK` (AnalysisDetailedResponse).

#### `GET /api/v1/claims/{claim_id}/analysis`
Retrieves latest analysis for a claim.

#### `GET /api/v1/claims/{claim_id}/forks`
Retrieves generated interpretation forks for a claim.

---

### E. Virtual Decision Lab

#### `POST /api/v1/decisions`
Records the user's initial stance before seeing counter-evidence.
- **Request Body:**
```json
{
  "claim_id": "e7b0d91a-7b3b-4876-b608-8121f1d1f05e",
  "interpretation_id": "f1d4399b-3129-4110-824a-2fa942c7aa78",
  "initial_thesis": "Buying before breakout due to social media buzz.",
  "initial_confidence": 85.0,
  "initial_allocation": 30.0,
  "assumptions_evaluated": ["Momentum continues", "Retail volume holds"]
}
```

#### `PUT /api/v1/decisions/{decision_id}/revise`
Records revised thesis after exploring counter-evidence and interpretation forks.
- **Request Body:**
```json
{
  "revised_thesis": "Reducing position to defensive level; disclosures show rising debt and flat PAT.",
  "revised_confidence": 45.0,
  "revised_allocation": 5.0,
  "reason_for_change": "Audited disclosures contradicted viral post's claim of 'strong fundamentals'.",
  "assumptions_evaluated": ["Debt overhang risk", "Flat operating cash flow"]
}
```

---

### F. Investor Assessments & Scoring

#### Concept Note on Dimension 5: Confidence Justification & Epistemic Alignment
Dimension 5 is conceptually named **Confidence Justification & Epistemic Alignment** (internally stored under `score_confidence_calibration` for full backward compatibility). It measures whether the user's stated confidence logically connects to specific identified evidence, uncertainty awareness, risk recognition, and substantive reasoning.

The 20-point rubric comprises:
1. **Evidence-Confidence Connection (0–6 pts):** Evaluates whether stated confidence is supported by identifiable primary evidence.
2. **Uncertainty Awareness (0–5 pts):** Evaluates recognition of missing claim parameters and ambiguous interpretations.
3. **Risk-Confidence Relationship (0–5 pts):** Evaluates whether identified risks meaningfully influence confidence.
4. **Justification Quality (0–4 pts):** Evaluates logical coherence, specificity, and non-generic rationale.

#### `POST /api/v1/assessments`
Submits answers evaluated against the transparent 5-dimension deterministic rubric.
- **Request Body:**
```json
{
  "session_id": "user-session-101",
  "claim_id": "e7b0d91a-7b3b-4876-b608-8121f1d1f05e",
  "assessment_stage": "BASELINE",
  "identified_evidence_types": ["COMPANY_DISCLOSURE"],
  "distinguished_primary_sources": true,
  "identified_missing_specificity": ["time_horizon", "invalidation_condition"],
  "identified_risk_factors": ["Operational margin pressure"],
  "recognized_alternative_interpretations": true,
  "stated_confidence": 40.0,
  "evidence_backing_level": "LOW",
  "confidence_justification": "Maintained conservative 40% confidence because while Q2 revenue was audited, the claim omits an explicit invalidation condition and faces margin headwinds."
}
```
*Note:* `confidence_justification` is **optional**. Existing client payloads that omit this field continue to work seamlessly.

- **Response:** `201 Created`
```json
{
  "id": "a984023c-99a1-4328-8742-1c0989b5cfa1",
  "session_id": "user-session-101",
  "claim_id": "e7b0d91a-7b3b-4876-b608-8121f1d1f05e",
  "assessment_stage": "BASELINE",
  "score_evidence_eval": 12.5,
  "score_claim_specificity": 8.0,
  "score_risk_awareness": 5.0,
  "score_assumption_awareness": 20.0,
  "score_confidence_calibration": 17.5,
  "total_score": 63.0,
  "dimension_scores": {
    "evidence_evaluation": 12.5,
    "claim_specificity": 8.0,
    "risk_awareness": 5.0,
    "assumption_awareness": 20.0,
    "confidence_calibration": 17.5
  },
  "rubric_feedback": {
    "evidence_evaluation": "Scored 12.5/20. Correctly separated primary filings...",
    "claim_specificity": "Scored 8.0/20. Identified 2 unstated claim parameters...",
    "risk_awareness": "Scored 5.0/20. Articulated 1 distinct downside/uncertainty risk factors.",
    "assumption_awareness": "Scored 20.0/20. Demonstrated clear comprehension...",
    "confidence_calibration": "Confidence Justification & Epistemic Alignment: Scored 17.5/20. [Evidence-Confidence: 5.5/6, Uncertainty Awareness: 4.0/5, Risk Relationship: 4.0/5, Justification Quality: 4.0/4]. Substantive, coherent justification connecting confidence to evidence, uncertainty, and risks."
  },
  "created_at": "2026-11-20T14:26:00Z"
}
```

#### `GET /api/v1/assessments/compare/{session_id}`
Computes percentage-point improvement between baseline and independent transfer stages.
- **Response:** `200 OK`

---

### G. Dashboard

#### `GET /api/v1/dashboard/overview`
Provides high-level platform activity metrics and recent claims/decisions.

#### `GET /api/v1/dashboard/progress?session_id={session_id}`
Provides the user's progress through learning stages (`NOT_STARTED` -> `BASELINE_COMPLETED` -> `ASSESSMENT_COMPLETED`) with score breakdown and percentage-point delta.

#### `GET /api/v1/dashboard/history?session_id={session_id}`
Provides the complete assessment timeline for the session.

---

## 4. Instructions for AI Teammate (`venkat-ai`)

The backend AI orchestration layer is decoupled via the `BaseAIProvider` abstract class located in:
`backend/app/integrations/ai_client.py`

To integrate or customize model providers:
1. Implement `analyze_claim` and `review_analysis`.
2. Ensure your response returns a JSON dict conforming to expected keys (`direction`, `target`, `horizon`, `missing_fields`, `interpretation_summary`).
3. Set credentials in `backend/.env` using `GROQ_API_KEY` and `GEMINI_API_KEY`.
