# FinTrace — Backend Engine

> **AI-Powered Investor Decision Intelligence & Decision Robustness Compiler**  
> Developed by **Team AetherCoders** for *The Big Hack 2.0*.

FinTrace empowers retail investors to deconstruct viral, unverified financial claims circulating on social media and messaging channels through deterministic epistemological statement classification, authentic multi-exchange regulatory evidence retrieval, counterfactual stance tracking, and rubric-driven learning assessments.

---

## 1. Feature Summary

- **Deterministic Claim Extraction & Parameter Integrity:** Deconstructs claims into structured targets, horizons, and entry/exit/invalidation conditions. Omitted parameters are preserved strictly as `null`—never fabricated.
- **Decision Robustness Compiler:** Multi-model orchestration (Groq Llama 3.3 70B & Google Gemini 2.5 Flash) featuring automatic timeout failover, independent cross-review, and material disagreement detection.
- **Epistemic Statement Classification:** Categorizes statements into `SOURCE_FACT`, `AI_INTERPRETATION`, `USER_ASSUMPTION`, and `UNRESOLVED_QUESTION`.
- **Primary Indian & US Evidence Retrieval:** Real-time retrieval of statutory corporate announcements and direct PDF circulars from NSE India, alongside SEC EDGAR filings for verified US ADR issuers.
- **Strict Entity Resolution & Anti-Collision Guards:** Prevents misleading matches (e.g. Reliance Industries vs. Reliance, Inc. of Scottsdale, AZ); domestic Indian entities are barred from false SEC searches.
- **Virtual Decision Lab:** Counterfactual decision recording before and after viewing counter-evidence, computing quantitative conviction deltas and behavioral shifts.
- **5-Dimension Rubric & Epistemic Alignment Engine:** Evaluates user critical analysis capabilities across Baseline, Assisted Practice, and Independent Transfer stages using a 100-point deterministic rubric.

---

## 2. Technology Stack

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Language Runtime** | Python | 3.11+ (Verified on 3.11.6) | Core backend runtime |
| **Web Framework** | FastAPI | >= 0.115.0 | Async REST API & OpenAPI specification |
| **Validation & Settings** | Pydantic v2 / Settings | >= 2.10.0 | Request/response schemas & configuration |
| **Database & ORM** | SQLAlchemy | >= 2.0.0 | Declarative ORM & session management |
| **Database Engine** | SQLite (PostgreSQL-ready) | Default hackathon engine | Persistent relational storage |
| **Async HTTP Client** | HTTPX | >= 0.28.0 | Exchange scraping & LLM provider requests |
| **Testing Framework** | Pytest & AnyIO | Pytest 9.1.1, AnyIO 4.14.2 | 39 automated regression & integration tests |

---

## 3. Quick Setup & Startup

### A. Environment Configuration
```bash
# Windows PowerShell
Copy-Item backend/.env.example backend/.env

# macOS / Linux
cp backend/.env.example backend/.env
```

### B. Dependency Installation
```bash
pip install -r backend/requirements.txt
```

### C. Run Development Server
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

- **API Base:** `http://localhost:8000/api/v1`
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/api/v1/openapi.json`

---

## 4. Automated Testing

Execute the complete 39-test automated test suite:
```bash
python -m pytest backend/tests/ -v -c backend/pytest.ini
```

**Verified Test Status:** `39 passed in 31.05s` (100% pass rate, 0 failures, 0 warnings).

---

## 5. Documentation Index

Comprehensive technical documentation and teammate handover packages are organized within [`backend/docs/`](file:///c:/Projects/FinTrace/FinTrace/backend/docs/):

1. [**BACKEND_ARCHITECTURE.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/BACKEND_ARCHITECTURE.md)  
   *System architecture, directory structure, module responsibilities, request lifecycle, Mermaid architecture diagram, and claim analysis sequence flow.*

2. [**API_REFERENCE.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/API_REFERENCE.md)  
   *Complete documentation for all 25+ implemented endpoints, request/response schemas, validation rules, status codes, and example payloads.*

3. [**SETUP_AND_CONFIGURATION.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/SETUP_AND_CONFIGURATION.md)  
   *Step-by-step setup guide for Windows PowerShell and macOS/Linux, virtual environments, environment variable reference, SQLite migration behavior, and troubleshooting.*

4. [**DATABASE_SCHEMA.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/DATABASE_SCHEMA.md)  
   *Entity-relationship diagram, complete data dictionary for all 7 tables, foreign keys, cascade deletion rules, indexing, and PostgreSQL migration guidelines.*

5. [**AI_INTEGRATION_GUIDE.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/AI_INTEGRATION_GUIDE.md)  
   *Handover guide for Venkat (`venkat-ai`): provider abstraction interface, expected input/output schemas, primary/secondary review flow, fallback state machine, and custom AI engine hookups.*

6. [**FRONTEND_INTEGRATION_GUIDE.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/FRONTEND_INTEGRATION_GUIDE.md)  
   *Handover guide for Nakul (`nakul-frontend`): UI flows, claim ambiguity banners, evidence provenance cards, Decision Lab step-by-step flow, assessment radar charts, and error states.*

7. [**EVIDENCE_AND_PROVENANCE.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/EVIDENCE_AND_PROVENANCE.md)  
   *Detailed documentation of NSE corporate announcements retrieval, SEC EDGAR supplementary ADR ingestion, entity resolution registry, anti-collision guards, and BSE Akamai 403 status.*

8. [**TESTING_AND_LIMITATIONS.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/TESTING_AND_LIMITATIONS.md)  
   *Test environment specification, full 39-test breakdown, unit vs live integration distinctions, known operational limitations, and production-readiness gaps.*

9. [**TEAM_INTEGRATION_CHECKLIST.md**](file:///c:/Projects/FinTrace/FinTrace/backend/docs/TEAM_INTEGRATION_CHECKLIST.md)  
   *Master integration checklist separating completed backend features from frontend and AI teammate responsibilities, including end-to-end smoke test scripts and demo scenarios.*

10. [**API_CONTRACT.md**](file:///c:/Projects/FinTrace/FinTrace/backend/API_CONTRACT.md)  
    *Complete, unified contract specification detailing endpoint signatures, payload schemas, and example JSON responses.*
