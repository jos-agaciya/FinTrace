# FinTrace — Team Integration Checklist & Handover

This checklist delineates completed backend capabilities from pending frontend (`nakul-frontend`) and AI engine (`venkat-ai`) integration tasks for Team AetherCoders.

---

## 1. Backend Readiness (Completed by Jos)

- [x] **FastAPI Application & Lifespan:** Server operational with CORS middleware for `localhost:3000` and `localhost:5173`.
- [x] **Data Models & Migration:** 7 relational tables with UUID keys, UTC timestamps, cascade delete rules, and dynamic SQLite column migration.
- [x] **Claims Management API:** Submissions, listing, retrieval, cascade deletion, and entity ambiguity detection (`is_ambiguous_entity`).
- [x] **Strict Null Preservation:** Omitted claim fields preserved strictly as `null` (zero hallucination of unstated targets or bounds).
- [x] **Primary Indian Evidence Retrieval:** Real-time statutory corporate announcements and PDF circular retrieval from NSE India.
- [x] **Supplementary US Evidence Retrieval:** SEC EDGAR filings for verified dual-listed ADR issuers (e.g. Infosys).
- [x] **Strict Entity Resolution Guards:** Reliance Industries protected against SEC "Reliance, Inc. Arizona" collision; domestic-only TCS barred from SEC.
- [x] **Duplicate Elimination & Safe Datetime:** Automatic URL deduplication and timezone-aware date parsing.
- [x] **Decision Robustness Compiler:** Multi-provider Groq & Gemini orchestration, timeout failover, material disagreement detection, and interpretation fork generation.
- [x] **Deterministic Falsifiability & Statement Tagging:** Falsifiability scoring (0–100) and categorization into `SOURCE_FACT`, `AI_INTERPRETATION`, `USER_ASSUMPTION`, and `UNRESOLVED_QUESTION`.
- [x] **Virtual Decision Lab:** Stance tracking, post-evidence revision, conviction drift delta, and behavioral shift categorization.
- [x] **5-Dimension Rubric Scorer:** Deterministic evaluation including the 4-component **Confidence Justification & Epistemic Alignment** rubric.
- [x] **Stage Comparison Engine:** Baseline vs Independent Transfer learning delta calculation (`percentage_point_delta`).
- [x] **Dashboard Metrics:** Platform overview, user progress status, and chronological evaluation timeline.
- [x] **Comprehensive Automated Test Suite:** 39 test scenarios passing with 100% success rate and 0 warnings.
- [x] **API & Technical Documentation:** Complete guides in `backend/docs/` and updated `API_CONTRACT.md`.

---

## 2. Frontend Integration Tasks (For Nakul — `nakul-frontend`)

- [ ] **API Client Setup:** Configure Axios or Fetch wrapper pointing to `http://localhost:8000/api/v1`.
- [ ] **Session Identifier Persistence:** Generate and persist a client `session_id` in `localStorage` across page reloads.
- [ ] **Claim Submission Form:**
  - Input form for raw claim text, ticker, company name, exchange, and platform.
  - Render entity ambiguity alert banner if `claim.is_ambiguous_entity === true`.
- [ ] **Evidence & Provenance Card Display:**
  - Render retrieved filings with distinct badges for `provenance_status` (`REAL`), `exchange` (`NSE` / `SEC`), and `source_jurisdiction` (`IN` / `US`).
  - Add clickable links to direct archive PDFs (`evidence.source_url`).
- [ ] **Robustness Compiler View:**
  - Display gauge chart for `falsifiability_score` (0–100%).
  - Display 4-column statement categorization grid (`SOURCE_FACT`, `AI_INTERPRETATION`, `USER_ASSUMPTION`, `UNRESOLVED_QUESTION`).
  - Display counterfactual interpretation fork cards.
  - Handle provider status badges (`SUCCESS`, `FALLBACK_USED`, `NEEDS_VERIFICATION`, `PROVIDER_UNAVAILABLE`).
- [ ] **Virtual Decision Lab Stepper:**
  - Step 1: Input initial thesis, confidence slider (0–100%), and allocation slider (0–100%).
  - Step 2: Present counter-evidence and interpretation forks.
  - Step 3: Input revised thesis, confidence slider, allocation slider, and reason for change.
  - Step 4: Display sensitivity summary card (`confidence_delta_points`, `shift_explanation`).
- [ ] **Assessment & Progress Dashboard:**
  - Interactive evaluation questionnaire for `BASELINE`, `ASSISTED_PRACTICE`, and `INDEPENDENT_TRANSFER`.
  - Optional `confidence_justification` text area.
  - Radar or horizontal bar chart displaying the 5 rubric dimension scores.
  - Progress chart displaying baseline vs transfer percentage point delta from `GET /api/v1/assessments/compare/{session_id}`.

---

## 3. AI Integration Tasks (For Venkat — `venkat-ai`)

- [ ] **Evaluate Implemented Backend Adapters:**
  - Review `backend/app/integrations/ai_client.py` (`GroqProvider` and `GeminiProvider`).
  - Verify prompt templates for claim analysis and secondary review.
- [ ] **Domain Model Tuning / Custom Engine:**
  - If integrating a specialized local model or custom multi-agent pipeline, implement the `BaseAIProvider` interface (`analyze_claim` and `review_analysis`).
  - Register custom provider class in `get_ai_provider()` factory.
- [ ] **Prompt Enhancement:**
  - Optimize system prompts to output strict JSON matching the required schema: `direction`, `target`, `horizon`, `missing_fields`, `interpretation_summary`.
  - Ensure unstated parameters are returned strictly as `null` or listed in `missing_fields`.
- [ ] **Secondary Review Tuning:**
  - Refine contradiction detection criteria to identify material financial conflicts between primary analysis and audited disclosures.

---

## 4. Environment & Team Configuration

- [ ] **Obtain API Keys:**
  - Secure Groq API key (`GROQ_API_KEY`) from Groq Cloud Console.
  - Secure Google Gemini API key (`GEMINI_API_KEY`) from Google AI Studio.
- [ ] **Environment Template Setup:**
  - Copy `.env.example` to `.env` in the backend root.
  - Set `GROQ_API_KEY` and `GEMINI_API_KEY`.
- [ ] **Network Verification:**
  - Test connectivity to `https://www.nseindia.com` and `https://data.sec.gov`.

---

## 5. End-to-End Integration Verification

- [ ] **E2E Smoke Test 1: Full Claim Lifecycle:**
  - Submit claim via frontend $\rightarrow$ Retrieve NSE evidence $\rightarrow$ Run Decision Robustness Compiler $\rightarrow$ Verify statement grid renders.
- [ ] **E2E Smoke Test 2: Decision Lab Stance Shift:**
  - Submit initial 80% confidence $\rightarrow$ Review counter-evidence $\rightarrow$ Revise to 35% $\rightarrow$ Verify sensitivity summary shows `-45.0` points with `REDUCED_EXPOSURE`.
- [ ] **E2E Smoke Test 3: Learning Assessment & Progress Delta:**
  - Complete Baseline assessment $\rightarrow$ Complete Transfer assessment $\rightarrow$ Check progress dashboard for percentage-point growth delta.

---

## 6. Final Demo Readiness

- [ ] Prepare 3 golden demonstration claims:
  1. **Infosys (INFY):** Dual-listed disclosure showcase with authentic Q2 NSE announcement PDF and SEC Form 6-K.
  2. **Reliance Industries (RELIANCE):** Entity disambiguation and anti-collision demonstration (showing zero false matches with US Reliance, Inc.).
  3. **High-Hype Viral Post:** Demonstration of low falsifiability score, missing invalidation bounds, and conviction adjustment in the Decision Lab.
