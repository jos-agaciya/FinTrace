# FinTrace Full-Stack Architecture & Integration Specification

This document provides the complete technical specification for the integrated FinTrace full-stack system, unifying:
- **`backend/`** — FastAPI asynchronous backend (developed on `jos-backend`)
- **`frontend/`** — React 18, Vite 6, Tailwind CSS frontend (developed on `nakul-frontend`)
- **`ai-engine/`** — Autonomous AI Decision Robustness Compiler (developed on `venky-ai`)

---

## 1. System Architecture Overview

```mermaid
flowchart TD
    subgraph Client["Frontend Application (React 18 / Vite)"]
        UI_Claim["Claim Ingestion & Breakdown (AnalyseClaim.jsx)"]
        UI_Report["Compiled Robustness Report (ClaimAnalysisReport.jsx)"]
        UI_Evidence["Evidence Centre (EvidenceCentre.jsx)"]
        UI_DecisionLab["Virtual Decision Lab (VirtualDecisionLab.jsx)"]
        UI_Dashboard["Investor Intelligence Dashboard (InvestorDashboard.jsx)"]
        Client_API["API Client (services/api.js)"]
    end

    subgraph Backend["FastAPI Backend (/api/v1 & /api)"]
        API_Gateway["Dual Prefix Gateway (/api/v1 & /api)"]
        Route_Auth["Auth Router (/auth/login, /auth/register, /auth/me)"]
        Route_Claims["Claims Router (POST /claims, /claims/analyze)"]
        Route_Evidence["Evidence Router (GET /evidence, POST /evidence/{id}/retrieve)"]
        Route_Decisions["Decision Router (/decisions, /decision-lab/calibrate)"]
        Route_Dashboard["Dashboard Router (/dashboard/overview)"]
        
        Svc_Claims["ClaimService & ClaimValidator"]
        Svc_Evidence["EvidenceService (NSE & SEC Disclosures)"]
        Svc_Orchestrator["AnalysisOrchestrator"]
        Svc_Decisions["DecisionService (Conviction Shift Tracker)"]
    end

    subgraph AIEngine["Autonomous AI Engine (ai-engine/)"]
        AI_Adapter["AIEngineAdapter (ai_engine_adapter.py)"]
        AI_Facade["FinTraceAIEngine Facade (facade.py)"]
        AI_Pipeline["Decision Robustness Compiler"]
        AI_DualReview["DualModelReviewer (Groq & Gemini Cross-Audit)"]
        AI_Forks["InterpretationForkEngine"]
        AI_Sensitivity["DecisionSensitivityEngine"]
        AI_Fallback["CircuitBreakers & FallbackManager"]
    end

    subgraph ExternalSources["Verifiable Financial Data Sources"]
        NSE["NSE India Corporate Disclosures (real HTTP/JSON)"]
        SEC["SEC EDGAR Submissions API (real CIK lookup)"]
    end

    UI_Claim --> Client_API
    UI_Report --> Client_API
    UI_Evidence --> Client_API
    UI_DecisionLab --> Client_API
    UI_Dashboard --> Client_API

    Client_API -->|HTTP / JSON| API_Gateway
    API_Gateway --> Route_Auth
    API_Gateway --> Route_Claims
    API_Gateway --> Route_Evidence
    API_Gateway --> Route_Decisions
    API_Gateway --> Route_Dashboard

    Route_Claims --> Svc_Claims
    Route_Claims --> Svc_Orchestrator
    Route_Evidence --> Svc_Evidence
    Route_Decisions --> Svc_Decisions

    Svc_Evidence --> NSE
    Svc_Evidence --> SEC

    Svc_Orchestrator --> AI_Adapter
    Svc_Decisions --> AI_Adapter
    AI_Adapter --> AI_Facade
    AI_Facade --> AI_Pipeline
    AI_Pipeline --> AI_DualReview
    AI_Pipeline --> AI_Forks
    AI_Pipeline --> AI_Sensitivity
    AI_Pipeline --> AI_Fallback
```

---

## 2. Component Integration Details

### A. Backend ↔ AI Engine (`backend/app/integrations/ai_engine_adapter.py`)
- **Direct Python Inter-process Invocations:** Backend imports `FinTraceAIEngine` from `ai-engine/facade.py` without network hops or mock intermediaries.
- **Provider Orchestration:** The backend's `AnalysisOrchestrator` uses `AIEngineProvider(BaseAIProvider)` to invoke the 4-stage Decision Robustness Compiler:
  1. *Claim Extraction & Fact Structuring*
  2. *Deterministic Falsifiability & Parameter Validation*
  3. *Independent Cross-Provider Review (`DualModelReviewer`)*
  4. *Multi-Angle Interpretation Fork Generation (`InterpretationForkEngine`)*
- **Conviction Sensitivity:** When an investor revises their thesis in `VirtualDecisionLab`, `DecisionService` calls `AIEngineAdapter.explain_decision_sensitivity(...)` to quantify delta shifts and generate qualitative explanations.
- **Circuit Breakers & Telemetry:** If external AI providers (Groq/Gemini) fail, `FallbackManager` safely degrades to deterministic heuristic rule sets without failing the request or fabricating evidence.

### B. Frontend ↔ Backend Integration (`frontend/src/services/api.js`)
- **Dual Prefix Resolution:** In `backend/app/main.py`, routers are mounted under both `/api/v1` and `/api`.
- **Response Format Normalization:** Frontend client `api.js` automatically detects array payloads vs. `{ total: N, items: [...] }` envelopes, normalizing claims, evidence, and assessment data.
- **Resilient Fallback Design:** In the event the backend is unreachable during an offline demonstration, `api.js` gracefully falls back to synthetic mock data (`SYNTHETIC_CLAIMS`, `SYNTHETIC_EVIDENCE`), guaranteeing 100% UI stability.
- **Convenience Endpoint (`POST /api/v1/claims/analyze`):** Chains ingestion $\rightarrow$ statutory evidence retrieval $\rightarrow$ robustness compilation into a single request, returning an enriched report ready for `ClaimAnalysisReport.jsx`.

### C. Evidence Retrieval & Provenance Tracking
- **NSE Corporate Disclosures:** Real HTTP queries to `www.nseindia.com` fetch legitimate Indian statutory announcements for NSE-listed equities.
- **SEC EDGAR Submissions:** Strict entity resolution queries SEC EDGAR only for verified US registrants or ADRs (e.g. Infosys `INFY`).
- **Strict Anti-Fabrication Boundary:** Unverified or ambiguous entities (e.g., bare "Tata" without specific subsidiary) return zero fabricated disclosures and flag ambiguity warnings.

---

## 3. End-to-End API Contracts

| Method | Endpoint | Description | Request Body | Response Body |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Authenticate user session | `{ email, password }` | `{ success, token, user }` |
| `POST` | `/api/v1/auth/register` | Register new user account | `{ name, email, password }` | `{ success, token, user }` |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user | None | `AuthUser` |
| `GET` | `/api/v1/claims` | List submitted claims | None (query params: `skip, limit`) | `ClaimListResponse` (or Array) |
| `GET` | `/api/v1/claims/{id}` | Get individual claim report | None | `ClaimResponse` |
| `POST` | `/api/v1/claims/analyze` | Compile claim robustness end-to-end | `{ statement, ticker, company, horizon, sourceUrl }` | Enriched `ClaimResponse` |
| `GET` | `/api/v1/evidence` | List all verified disclosures | Query param: `?q=<term>` | `List[EvidenceResponse]` |
| `POST` | `/decision-lab/calibrate` | Virtual Decision Lab calibration | `{ initialStance, initialConfidence, revisedStance, revisedConfidence, refutedAssumptions }` | `DecisionCalibrationResponse` |
| `GET` | `/api/v1/dashboard/overview` | Investor dashboard summary | None | `DashboardOverviewResponse` |
| `GET` | `/api/v1/health` | System & AI Engine health | None | `HealthResponse` |

---

## 4. Verification & Testing Evidence

All three subsystems have passed automated testing and build validation:

```bash
# Backend test suite (45 tests)
python -m pytest backend/tests/ -v -c backend/pytest.ini
# Result: 45 passed in 9.59s

# AI Engine test suite (101 tests)
cd ai-engine && python -m pytest tests/ -q
# Result: 101 passed in 2.05s

# Frontend compilation
cd frontend && npm run build
# Result: built in 2.04s, 0 errors, production bundle ready
```
