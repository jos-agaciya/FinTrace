# FinTrace AI Engine (`fintrace-ai-engine`)

**Role Lead:** AI Engineering Lead — Venkat Rajh P R
**Package Name:** `fintrace-ai-engine`
**Root Directory:** `ai-engine/`
**Branch:** `venky-ai`
**Milestone:** Phase 2 Consolidated — P0 Pipeline + P1 Educational Learning Loop & Data Provenance

---

## 1. Project Purpose & Architecture

The FinTrace AI Engine is an autonomous, domain-driven subsystem powering the **Investor Decision Intelligence and Learning Platform**. Its core innovation is the **Decision Robustness Compiler**.

The subsystem is responsible for:
1. **Claim Understanding & Falsifiability Compilation:** Transforming noisy, unstructured financial assertions into rigorous, testable hypotheses with concrete invalidation boundaries.
2. **Strict Anti-Hallucination & Null Preservation:** Enforcing that unstated claim details (targets, time horizons, entry/exit criteria) strictly remain `None` (JSON `null`), never invented.
3. **Deterministic Validation:** Applying mathematical, chronological, and provenance rules (non-LLM) to detect invalid numbers, future/past date inversions, and hallucinated figures.
4. **Interpretation Fork Engine:** Identifying semantic ambiguities and synthesizing distinct alternative readings labeled explicitly as *AI-generated hypotheses* with distinguishing evidence requirements and normalized plausibility weights ($\sum w_i \le 1.0$).
5. **Persuasion & Risk Indicator Extraction:** Detecting observable urgency language, guaranteed-return promises, unsupported certainty, and missing risk disclosures with strictly neutral review labels ("needs verification").
6. **Counterfactual Practice Claim Generation:** Producing isomorphic synthetic practice claims that preserve structural evaluation flaws without showing AI analysis or leaking answers.
7. **Decision Sensitivity Engine:** Comparing an investor's pre- and post-analysis reasoning, explaining which assumptions shifted without treating allocation reductions as normative "success".
8. **Independent Assessment Evaluation Support:** Providing structured evaluations across the 5 FinTrace rubric dimensions (Evidence evaluation, Claim specificity, Risk awareness, Assumption awareness, Confidence calibration) with transparent scoring anchors.
9. **Live Multi-Provider Resiliency:** High-throughput primary extraction via **Groq** (`GroqProvider`) backed by **Google Gemini** (`GeminiProvider`) with automatic failover and 3-state circuit breaker protection (`CLOSED`, `OPEN`, `HALF_OPEN`).
10. **Dual-Model Review & Independent Critique:** Coordinating primary extraction with an independent reviewer critique. Disagreements automatically spawn uncertainty interpretation forks.
11. **Mandatory Truth Warning:** Enforcing that two-model agreement is *never* treated as proof of truth.

---

## 2. Directory Layout & Module Responsibilities

The package follows a flat, modular architecture directly inside `ai-engine/` without nested roots:

```text
ai-engine/
├── .env.example                # Sample environment configuration template
├── .gitignore                  # Git exclusion rules (.env, .venv, cache)
├── claim_extraction/           # Claim understanding, compiler, risk indicators, and evidence
│   ├── __init__.py
│   ├── compiler.py             # FalsifiabilityCompiler (calculates objective score [0.0, 1.0])
│   ├── evidence_formatter.py   # Formats retrieved EvidenceItem bundles safely with truncation bounds
│   ├── extractor.py            # ClaimExtractor pipeline (orchestrates model extraction & null fidelity)
│   ├── risk_indicators.py      # RiskIndicatorExtractor (deterministic persuasion & risk detection)
│   └── schemas.py              # ExtractedClaim, RiskIndicator, InvalidationCriteria, EvidenceItem
├── interpretation/             # Ambiguity diagnostics, counterfactuals, and decision sensitivity
│   ├── __init__.py
│   ├── counterfactual.py       # CounterfactualClaimGenerator (generates synthetic practice claims)
│   ├── fork_engine.py          # InterpretationForkEngine (generates forks with immutable provenance)
│   ├── schemas.py              # InterpretationFork, ForkAnalysisResult (with weight normalization)
│   └── sensitivity.py          # DecisionSensitivityEngine (descriptive pre/post reasoning comparison)
├── assessment/                 # Independent assessment evaluation support
│   ├── __init__.py
│   ├── evaluator.py            # AssessmentEvaluator (evaluates user critique across 5 dimensions)
│   └── schemas.py              # UserAssessmentInput, AssessmentEvaluationOutput, DimensionEvaluationResult
├── providers/                  # Model provider abstraction, live clients, and offline harness
│   ├── __init__.py
│   ├── base.py                 # BaseLLMProvider (abstract async interface)
│   ├── groq_provider.py        # GroqProvider (AsyncGroq, JSON mode, 429/timeout error mapping)
│   ├── gemini_provider.py      # GeminiProvider (google.genai, schema mode, 429/timeout error mapping)
│   ├── mock_provider.py        # MockProvider (genuinely executable offline mock with fault injection)
│   └── schemas.py              # ProviderRequest, ProviderResponse, ProviderStatus, TokenUsage
├── orchestration/              # Dual-model coordination and independent reviewer critique
│   ├── __init__.py
│   ├── reviewer.py             # DualModelReviewer (consensus audit, disagreement forks, degraded flag)
│   └── schemas.py              # DualModelReviewInput, DualModelReviewOutput
├── validation/                 # Deterministic non-LLM validation and error hierarchy
│   ├── __init__.py
│   ├── deterministic.py        # DeterministicValidator (chronology, word/number grounding, null fidelity)
│   ├── errors.py               # AIEngineError hierarchy (RateLimit, CircuitBreaker, Auth, Timeout)
│   └── schemas.py              # ValidationResult, ValidationIssue, GroundingCheckResult, GroundingStatus
├── fallback/                   # Resiliency, retry, and circuit-breaker management
│   ├── __init__.py
│   ├── circuit_breaker.py      # CircuitBreaker (CLOSED, OPEN, HALF_OPEN state machine + atomic probe gate)
│   └── fallback_manager.py     # FallbackManager (Groq -> Gemini failover, AllProvidersFailedError)
├── scripts/                    # Operational and diagnostics scripts
│   └── smoke_test.py           # Standalone live CLI smoke test (masked credentials, zero secret leakage)
├── tests/                      # Automated test suite (100% offline, 101 unit & integration tests)
│   ├── conftest.py
│   ├── test_assessment_evaluator.py     # Tests 5-dimension rubric evaluation and scoring anchors
│   ├── test_audit_fixes.py             # Verifies H-2, M-1, and M-2 audit fixes
│   ├── test_circuit_breaker.py         # Tests state transitions and fast-fail behavior
│   ├── test_circuit_breaker_concurrency.py # Tests atomic probe gating in HALF_OPEN
│   ├── test_claim_extraction_pipeline.py # Tests complete and vague claims
│   ├── test_counterfactual_generator.py # Tests isomorphic practice claim synthesis
│   ├── test_credential_hygiene.py      # Tests key masking and gitignore
│   ├── test_decision_sensitivity.py    # Tests reasoning shift explanation
│   ├── test_deterministic_validation.py # Tests chronology and numeric grounding
│   ├── test_evidence_grounding_delivery.py # Tests evidence prompt delivery and truncation
│   ├── test_fallback_orchestration.py  # Tests Groq -> Gemini failover and breaker skips
│   ├── test_fork_semantics.py          # Tests ambiguity rules and telemetry survival
│   ├── test_gemini_provider.py         # Tests Gemini client with mock SDK
│   ├── test_groq_provider.py           # Tests Groq client with mock SDK
│   ├── test_interpretation_fork_engine.py # Tests scenario generation and weights
│   ├── test_mock_pipeline_and_degraded.py # Tests end-to-end pipeline execution
│   ├── test_packaging_and_contracts.py # Tests package imports and null fidelity
│   ├── test_risk_indicators.py         # Tests urgency, guarantees, and missing risk
│   ├── test_same_provider_review_integrity.py # Tests degraded same-provider self-review
│   └── test_telemetry_survival.py      # Tests telemetry survival across all stages
├── engine_interface.py         # Public facade DTOs and FinTraceAIEngineProtocol
├── facade.py                   # FinTraceAIEngine end-to-end implementation and from_env() factory
├── pyproject.toml              # Build metadata, discovery, pytest options
├── requirements.txt            # Core dependencies
└── README.md                   # System documentation
```

---

## 3. Data-Provenance Record (Report Appendix B)

The table below documents data classification, origin, provenance status, and permitted transformations across the FinTrace architecture:

| Dataset / Item | Status | Source / URL | Retrieved | Use / Notes |
|---|---|---|---|---|
| **Company filing** | `REAL` | Exact exchange/company URL (e.g. SEC EDGAR / NSE / BSE) | Verified retrieval timestamp | Primary-source document for factual grounding and financial figures. Passed into models as evidence. |
| **Historical price series** | `REAL` or `SYNTHETIC` | Exact permitted market-data API or controlled synthetic price generator | API query date | Used for chart context, volatility, and volume analysis. Never used by models to extrapolate guaranteed returns. |
| **Social-media claim** | `USER-PROVIDED` or `SYNTHETIC` | Original post URL, transcript, or marked demo payload | Submission timestamp | Parsed for testability and invalidation boundaries. Never treated as verified ground truth. |
| **AI interpretation** | `AI-GENERATED` | Groq / Gemini model output with model ID | Execution timestamp | Plausible reading labeled strictly as an AI hypothesis; never presented as confirmed author intent. |
| **Practice claim** | `SYNTHETIC` | Controlled template generator (`counterfactual.py`) | Generated dynamically | Purely fictional practice claims used to measure independent investor learning transfer. |
| **Persuasion / risk prompt** | `AI-GENERATED` / `DETERMINISTIC` | Regex extractor (`risk_indicators.py`) | Extraction timestamp | Neutral review prompts ("needs verification"). Never presented as proof of fraud or manipulation. |

---

## 4. Architectural Boundaries: AI Engine vs. Backend / Frontend

To preserve strict separation of concerns across team ownership:

### AI Engine Responsibilities (Venkat)
- Structured claim extraction, null preservation, and falsifiability scoring.
- Deterministic chronology, numerical grounding, and consistency validation.
- Interpretation fork generation with bounded plausibility weights.
- Persuasion and risk indicator extraction.
- Counterfactual practice claim generation for independent evaluation.
- Decision sensitivity explanation generation.
- Structured assessment evaluation across the 5 FinTrace rubric dimensions.
- Dual-model orchestration, Groq $\to$ Gemini fallback, and concurrency-safe circuit breaking.

### Backend Responsibilities (Jos)
- **Live Evidence Retrieval:** Querying SEBI/EDGAR filings, news APIs, and market data (`evidence-engine/retrieval/`).
- **Entity Resolution:** Interactive dropdown prompts asking users to disambiguate company tickers (`evidence-engine/sources/`).
- **Persistence:** Storing claims, user accounts, virtual decision records, and assessment histories in database tables (`database/`, `backend/app/models/`).
- **Analytics:** Computing longitudinal Decision Evaluation Scores (0–100) and tracking session trends (`decision-engine/scoring/`).
- **Web APIs:** FastAPI endpoints, routing, and authentication (`backend/app/api/`).

### Frontend Responsibilities (Nakul)
- Interactive claim submission, report views, and PDF export (`frontend/src/`).
- Virtual Decision Lab sliders, confidence toggles, and dual-rationale input forms.
- Investor Decision Intelligence Dashboard charts and progression metrics.

---

## 5. Environment Setup & Configuration

A project-local Python virtual environment is located at `ai-engine/.venv/`.

### Activating the Environment (Windows PowerShell)
```powershell
cd ai-engine
.\.venv\Scripts\Activate.ps1
```

### Installing Dependencies
```powershell
pip install -r requirements.txt
pip install -e .
```

### Setting Up Credentials
Copy `.env.example` to `.env` and fill in your API credentials:
```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SECONDS=60.0
AI_ENGINE_REQUEST_TIMEOUT_SECONDS=15.0
```

> [!NOTE]
> `.env` is explicitly Git-ignored and will never be committed to version control.

---

## 6. Test Suite Coverage (101 Passing Tests, 0 Failures)

The automated test suite runs completely offline with **zero network access** and **zero API credit requirements**:

```powershell
cd ai-engine
.\.venv\Scripts\pytest -v tests
```

### Test Suite Modules
1. `tests/test_assessment_evaluator.py` (6 tests): Evaluates all 5 rubric dimensions, recognizes structural flaws, scores confidence calibration, handles empty critique safely, and ensures no penalization of contrarian opinions.
2. `tests/test_audit_fixes.py` (3 tests): Weight normalization, expanded chronology regex, number word equivalence.
3. `tests/test_circuit_breaker.py` (6 tests): CLOSED state, CLOSED $\to$ OPEN on threshold, fast-fail OPEN, OPEN $\to$ HALF_OPEN on cooldown, HALF_OPEN $\to$ CLOSED recovery, HALF_OPEN $\to$ OPEN re-trip, manual reset.
4. `tests/test_circuit_breaker_concurrency.py` (3 tests): Concurrency-safe atomic single-probe gating under simultaneous requests, probe failure re-trip, probe cancellation.
5. `tests/test_claim_extraction_pipeline.py` (4 tests): Complete claims, vague claims, ambiguous company names (null ticker), falsifiability compiler score computation.
6. `tests/test_counterfactual_generator.py` (8 tests): Preserves vague timeframes, missing targets, missing invalidations, and hyperbolic certainty; F&O claim generation; zero answer leakage; strictly synthetic entities.
7. `tests/test_credential_hygiene.py` (2 tests): Zero partial key leakage in diagnostics and logs (`_mask_key` never returns credential substrings).
8. `tests/test_decision_sensitivity.py` (6 tests): Detects confidence and allocation deltas, correlates interpretation forks, never treats allocation reduction as success, flags unexplained variance on missing rationales.
9. `tests/test_deterministic_validation.py` (7 tests): Chronology inversions, hallucinated numerics, negative price targets, falsifiability contradictions, evidence grounding.
10. `tests/test_evidence_grounding_delivery.py` (5 tests): Formatted evidence delivery to primary extractor and reviewer models, observable bundle truncation, honest empty evidence handling.
11. `tests/test_fallback_orchestration.py` (7 tests): Primary success, 429 rate-limit failover, timeout failover, structured failover, circuit breaker skip, all-providers failure, end-to-end resilient engine.
12. `tests/test_fork_semantics.py` (2 tests): Semantic ambiguity boundary verification, telemetry survival on `ForkAnalysisResult`.
13. `tests/test_gemini_provider.py` (6 tests): Gemini text generation, structured JSON extraction, 429 rate limit mapping, timeout mapping, schema validation errors, missing auth.
14. `tests/test_groq_provider.py` (6 tests): Groq text generation, structured JSON extraction, 429 rate limit mapping, timeout mapping, schema validation errors, missing auth.
15. `tests/test_interpretation_fork_engine.py` (1 test): Ambiguity detection, scenario synthesis, distinguishing evidence checklist, immutable provenance label.
16. `tests/test_mock_pipeline_and_degraded.py` (5 tests): End-to-end pipeline execution, dual-model disagreement forks, degraded single-provider mode.
17. `tests/test_packaging_and_contracts.py` (9 tests): Packaging imports, null preservation in Python/JSON, frozen field immutability, provider telemetry, error hierarchy.
18. `tests/test_risk_indicators.py` (9 tests): Urgency wording, guaranteed return language, unsupported certainty, missing risk disclosure, case-insensitivity, no false positives on factual text, zero accusatory terms.
19. `tests/test_same_provider_review_integrity.py` (4 tests): Detection of same-provider self-review (`DEGRADED_SAME_PROVIDER`), invalidation of independent consensus claim, distinct-provider review validation.
20. `tests/test_telemetry_survival.py` (2 tests): Provider provenance and fallback execution telemetry survival across extraction, review, and `FullPipelineAnalysisResult`.

---

## 7. Public Integration Interface & End-to-End Usage

The AI Engine exposes a single, strongly-typed facade `FinTraceAIEngine`:

```python
import asyncio
from datetime import datetime, timezone
from engine_interface import (
    ClaimExtractionInput,
    DecisionRecord,
    DecisionSensitivityInput,
    UserAssessmentInput,
)
from claim_extraction.schemas import EvidenceItem, SourceTypeEnum
from facade import FinTraceAIEngine

async def main():
    # Factory auto-detects .env credentials and wires Groq + Gemini + FallbackManager
    engine = FinTraceAIEngine.from_env()

    # 1. Execute full claim analysis pipeline (P0)
    input_data = ClaimExtractionInput(
        raw_text="Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling. Buy before it's too late!",
        source_url="https://x.com/analyst/status/123",
        published_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
        retrieved_evidence=[
            EvidenceItem(
                source_name="SEC 10-K",
                source_url="https://sec.gov/tsla-10k",
                source_type=SourceTypeEnum.SEC_FILING,
                text_content="Tesla reported automotive revenues and target metrics for $400 scaling.",
            )
        ],
    )
    result = await engine.analyze_end_to_end(input_data)
    print("Claim:", result.claim.claim_summary)
    print("Falsifiability Score:", result.claim.falsifiability_score)
    print("Risk Indicators Found:", len(result.claim.risk_indicators))

    # 2. Generate a counterfactual practice claim for independent evaluation (P1)
    practice = engine.generate_practice_claim(result.claim)
    print("Practice Claim for User:", practice.practice_claim.claim_text)

    # 3. Explain decision sensitivity across pre/post user decisions (P1)
    sensitivity = engine.explain_sensitivity(
        DecisionSensitivityInput(
            initial_decision=DecisionRecord(
                confidence_level=4.0,
                hypothetical_allocation_pct=50.0,
                written_rationale="Autonomous scaling looks inevitable.",
            ),
            revised_decision=DecisionRecord(
                confidence_level=2.5,
                hypothetical_allocation_pct=20.0,
                written_rationale="After reviewing the 10-K and interpretation forks, regulatory credits represent a major unstated risk.",
            ),
            selected_interpretation_forks=result.fork_analysis.forks,
        )
    )
    print("Sensitivity Summary:", sensitivity.summary_of_change)

    # 4. Evaluate independent user assessment critique (P1)
    assessment = engine.evaluate_assessment(
        UserAssessmentInput(
            claim=result.claim,
            user_critique_text="The claim provides no explicit invalidation condition or stop loss, and the SEC filing shows risk in credit sales.",
            user_confidence=2.0,
        )
    )
    print("Total Assessment Score:", assessment.total_suggested_score)

asyncio.run(main())
```
