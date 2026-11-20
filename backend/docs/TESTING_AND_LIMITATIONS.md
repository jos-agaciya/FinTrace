# FinTrace — Testing, Verification & Known Limitations

This document reports the verified test suite results, breakdown of test modules, testing methodologies, known operational limitations, and production-readiness roadmap.

---

## 1. Test Environment Specification

- **Host Operating System:** Windows 10/11 x64
- **Python Version:** 3.11.6
- **Test Runner:** Pytest 9.1.1
- **Async Plugin:** AnyIO 4.14.2
- **Configuration File:** `backend/pytest.ini`
- **Database Engine for Tests:** SQLite in-memory with `StaticPool` (`sqlite:///:memory:`)
- **Isolation:** Fast, deterministic execution isolated from external state.

---

## 2. Test Execution Command & Verification Results

### Execution Command:
```powershell
python -m pytest backend/tests/ -v -c backend/pytest.ini
```

### Verified Test Run Summary (Fresh Execution):
- **Total Test Files:** 10
- **Total Test Cases:** **39**
- **Passed:** **39 (100%)**
- **Failed:** **0**
- **Skipped:** **0**
- **Warnings:** **0**
- **Total Execution Time:** **31.05 seconds**

---

## 3. Test Suite Breakdown by Module

| Test File | Test Case Name | Coverage Scope | Status |
|---|---|---|---|
| `test_claims.py` | `test_health_check` | Service readiness and API info verification | **PASSED** |
| `test_claims.py` | `test_claim_submission_and_null_preservation` | Unstated parameters preserved strictly as `null` | **PASSED** |
| `test_claims.py` | `test_ambiguous_company_detection` | Rule-based entity ambiguity flag detection | **PASSED** |
| `test_claims.py` | `test_claim_retrieval_and_deletion` | CRUD operations and soft/hard deletion | **PASSED** |
| `test_evidence.py` | `test_evidence_creation_and_retrieval` | Manual disclosure registration and indexing | **PASSED** |
| `test_evidence.py` | `test_claim_evidence_association_and_retrieval` | Many-to-many claim-to-evidence linkage | **PASSED** |
| `test_indian_evidence.py` | `test_nse_symbol_resolution` | INFY, TCS, RELIANCE resolve to verified ISINs | **PASSED** |
| `test_indian_evidence.py` | `test_unknown_symbol_returns_no_fabricated_evidence` | Unlisted entity returns 0 items without inventing data | **PASSED** |
| `test_indian_evidence.py` | `test_reliance_industries_never_matches_reliance_inc` | Reliance Industries barred from US SEC metals search | **PASSED** |
| `test_indian_evidence.py` | `test_tcs_does_not_produce_false_sec_results` | Domestic Indian TCS never queries SEC EDGAR | **PASSED** |
| `test_indian_evidence.py` | `test_infosys_adr_and_nse_jurisdictions_separated` | IN (NSE) and US (SEC) filings remain distinct | **PASSED** |
| `test_indian_evidence.py` | `test_nse_extraction_fields` | Accurate parsing of title, date, and archive PDF link | **PASSED** |
| `test_indian_evidence.py` | `test_nse_error_handling_403_429_timeout` | Safe recovery on 403, 429, timeouts, and bad JSON | **PASSED** |
| `test_indian_evidence.py` | `test_deduplication_and_missing_dates` | Duplicate URLs filtered; missing dates handled safely | **PASSED** |
| `test_indian_evidence.py` | `test_live_nse_announcements_retrieval` | Live HTTPS request to NSE India verifying real announcements | **PASSED** |
| `test_analysis.py` | `test_analysis_run_success` | Full multi-LLM analysis, statement categorization & forks | **PASSED** |
| `test_analysis.py` | `test_analysis_fallback_used` | Automatic fallback to secondary when primary fails | **PASSED** |
| `test_analysis.py` | `test_analysis_both_providers_unavailable` | Deterministic degradation when both LLMs unavailable | **PASSED** |
| `test_analysis.py` | `test_analysis_material_disagreement_needs_verification` | `NEEDS_VERIFICATION` flag when models conflict | **PASSED** |
| `test_decisions.py` | `test_decision_lifecycle_and_sensitivity_tracking` | Initial vs revised stance delta and shift type | **PASSED** |
| `test_assessments.py` | `test_deterministic_scoring_and_stage_comparison` | 5-dimension rubric scoring and baseline vs transfer delta | **PASSED** |
| `test_confidence_justification.py` | `test_low_confidence_without_reasoning_does_not_get_perfect_score` | Low confidence without justification penalized | **PASSED** |
| `test_confidence_justification.py` | `test_high_confidence_with_strong_evidence_can_receive_high_score` | High confidence supported by evidence rewarded | **PASSED** |
| `test_confidence_justification.py` | `test_high_confidence_with_contradictory_risks_and_no_evidence_receives_low_score` | High confidence ignoring risks penalized | **PASSED** |
| `test_confidence_justification.py` | `test_confidence_changes_not_automatically_rewarded_or_penalized` | Epistemic alignment evaluated on justification | **PASSED** |
| `test_confidence_justification.py` | `test_empty_or_missing_justification_handled_safely` | Backward compatibility when justification omitted | **PASSED** |
| `test_confidence_justification.py` | `test_irrelevant_generic_boilerplate_does_not_receive_full_points` | Generic filler text penalized | **PASSED** |
| `test_confidence_justification.py` | `test_rubric_components_independence` | 4 rubric sub-components evaluated independently | **PASSED** |
| `test_confidence_justification.py` | `test_scores_remain_within_strict_bounds` | Scores bounded strictly between 0.0 and 20.0 | **PASSED** |
| `test_dashboard.py` | `test_dashboard_overview_and_progress_flow` | Overview metrics and progress tracking queries | **PASSED** |
| `test_database.py` | `test_claim_model_preserves_null_fields` | SQLite schema preserves nulls across writes | **PASSED** |
| `test_database.py` | `test_relationships` | ORM back-populates and cascading deletes | **PASSED** |
| `test_stabilization.py` | `test_openapi_and_docs_endpoints` | `/docs`, `/redoc`, and `/api/v1/openapi.json` live | **PASSED** |
| `test_stabilization.py` | `test_input_validation_errors` | FastAPI returns 422 on invalid schema inputs | **PASSED** |
| `test_stabilization.py` | `test_missing_records_and_404_responses` | Returns 404 on nonexistent resource IDs | **PASSED** |
| `test_stabilization.py` | `test_missing_prerequisites_for_stage_comparison` | 400 Bad Request when comparison stages missing | **PASSED** |
| `test_stabilization.py` | `test_cascade_deletion` | Claim deletion cascades cleanly across all children | **PASSED** |
| `test_stabilization.py` | `test_real_sec_edgar_evidence_retrieval` | Live retrieval of genuine SEC EDGAR / NSE filings | **PASSED** |
| `test_stabilization.py` | `test_unknown_entity_evidence_retrieval_does_not_fabricate` | Fictitious entities return total: 0 | **PASSED** |

---

## 4. Distinction Between Actual and Mocked Testing

1. **Unit & Failure Injection Tests (Mocked):**
   - HTTP requests are mocked with `unittest.mock.patch("httpx.AsyncClient.get")` or `patch.object(...)` to simulate network partitions, HTTP 403 Forbidden, HTTP 429 Too Many Requests, socket timeouts, and malformed JSON without burdening exchange infrastructure.
   - LLM provider calls in `test_analysis.py` are mocked with mock providers to test failover logic deterministically without consuming token quota or requiring live API keys.
2. **Integration & Live Network Tests (Unmocked):**
   - `test_live_nse_announcements_retrieval`: Dispatches real HTTPS requests to `https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=INFY` to verify that real NSE corporate announcements with working archive PDF links are retrieved and parsed correctly.
   - `test_real_sec_edgar_evidence_retrieval`: Queries live filings to verify real disclosure ingestion.

---

## 5. Known Operational Limitations

1. **BSE India Automated Retrieval:**
   - Directly requesting `api.bseindia.com` or `bseindia.com` returns `HTTP 403 Forbidden` (`<TITLE>Access Denied</TITLE>`) enforced by Akamai Web Application Firewall.
   - FinTrace strictly complies with security rules and does not bypass WAF gates. Direct BSE automated retrieval is currently unsupported until authorized enterprise market data feeds are provisioned.
2. **Entity Registry Scope:**
   - The verified Indian equity registry (`VERIFIED_NSE_REGISTRY`) currently has pre-mapped symbols and ISINs for 5 major market-cap leaders (`INFY`, `TCS`, `RELIANCE`, `HDFCBANK`, `WIPRO`). Additional equities can be resolved via symbol or registered directly into the dictionary.
3. **Database Concurrency in SQLite:**
   - Default SQLite database uses file-level locking. Under heavy multi-threaded concurrent write loads, transactions may queue. For production deployment, configure `DATABASE_URL` to point to PostgreSQL.
4. **LLM Provider Availability:**
   - When API keys (`GROQ_API_KEY`, `GEMINI_API_KEY`) are unset or rate-limited, FinTrace seamlessly degrades to `PROVIDER_UNAVAILABLE` mode. Falsifiability scoring, statement classification, and interpretation fork generation run using deterministic rule heuristics without failing the request.

---

## 6. Production-Readiness Gaps

To advance from Hackathon MVP to enterprise production:
- [ ] **Database Migration:** Transition from SQLite to PostgreSQL with Alembic migration versioning.
- [ ] **Caching Layer:** Deploy Redis for caching frequently requested NSE announcements (e.g., 5-minute TTL).
- [ ] **Background Job Queue:** Integrate Celery or ARQ for asynchronous background disclosure indexing.
- [ ] **Authorized Market Data Feeds:** Partner with exchange data distributors (NSE Data & Analytics, BSE India Market Data) for direct authorized API access.
- [ ] **Authentication & RBAC:** Implement JWT or OAuth2 authentication with role-based access control.
