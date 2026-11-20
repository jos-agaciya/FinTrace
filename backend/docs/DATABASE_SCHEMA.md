# FinTrace — Database Schema & Data Dictionary

This document details all relational models, column definitions, constraints, relationships, cascade rules, and indexing strategies implemented in FinTrace.

---

## 1. Entity-Relationship Overview

```mermaid
erDiagram
    CLAIMS ||--o{ INTERPRETATION_FORKS : "generates (1:N)"
    CLAIMS ||--o{ ANALYSES : "evaluates (1:N)"
    CLAIMS ||--o{ CLAIM_EVIDENCE : "associates (1:N)"
    EVIDENCE ||--o{ CLAIM_EVIDENCE : "linked to (1:N)"
    CLAIMS ||--o{ DECISIONS : "tracks (1:N)"
    INTERPRETATION_FORKS ||--o{ DECISIONS : "evaluates (0..1:N)"
    CLAIMS ||--o{ ASSESSMENTS : "grades (1:N)"

    CLAIMS {
        string id PK "UUID"
        text original_claim "Claim text"
        string company_name "Company name"
        string ticker "Exchange ticker"
        string exchange "Trading exchange"
        string claim_direction "BULLISH/BEARISH/NEUTRAL"
        float target_value "Target price / return"
        string target_unit "% / INR / USD"
        string time_horizon "Horizon"
        text invalidation_condition "Falsification bound"
        string provenance_status "USER_PROVIDED"
        boolean is_ambiguous_entity "Ambiguity flag"
        datetime submitted_at "Submission timestamp"
        datetime created_at "Created timestamp"
    }

    INTERPRETATION_FORKS {
        string id PK "UUID"
        string claim_id FK "Reference to claims.id"
        string title "Fork title"
        text description "Plausible reading"
        string ambiguous_phrase "Ambiguous phrase"
        text assumptions "JSON array"
        text information_required "Required filings"
        boolean is_ai_generated "AI generation flag"
        datetime created_at "Created timestamp"
    }

    EVIDENCE {
        string id PK "UUID"
        string title "Evidence title"
        string document_title "Filing document name"
        string publisher "Publisher / Exchange"
        string source_url "Original source URL"
        datetime publication_date "Filing date"
        datetime retrieval_timestamp "Retrieval date"
        string evidence_category "COMPANY_DISCLOSURE"
        string company_symbol "NSE Symbol"
        string company_isin "ISIN code"
        string source_jurisdiction "IN / US"
        string exchange "NSE / SEC"
        text content_summary "Extracted summary"
        string provenance_status "REAL"
        datetime created_at "Created timestamp"
    }

    CLAIM_EVIDENCE {
        string id PK "UUID"
        string claim_id FK "Reference to claims.id"
        string evidence_id FK "Reference to evidence.id"
        float relevance_score "Relevance weight (1.0)"
        text association_notes "Retrieval notes"
        datetime created_at "Created timestamp"
    }

    ANALYSES {
        string id PK "UUID"
        string claim_id FK "Reference to claims.id"
        string primary_provider "groq / gemini"
        string secondary_provider "gemini / groq"
        string provider_status "SUCCESS / FALLBACK_USED"
        float falsifiability_score "0 - 100"
        text missing_fields "JSON array"
        text categorized_statements "JSON object"
        string validation_status "PASSED / WARNING"
        text primary_output_summary "Raw summary"
        datetime created_at "Created timestamp"
    }

    DECISIONS {
        string id PK "UUID"
        string claim_id FK "Reference to claims.id"
        string interpretation_id FK "Reference to forks.id"
        text initial_thesis "Initial stance"
        float initial_confidence "0 - 100%"
        float initial_allocation "0 - 100%"
        text revised_thesis "Post-evidence stance"
        float revised_confidence "0 - 100%"
        float revised_allocation "0 - 100%"
        text reason_for_change "Revision rationale"
        datetime created_at "Created timestamp"
        datetime updated_at "Updated timestamp"
    }

    ASSESSMENTS {
        string id PK "UUID"
        string session_id "User session index"
        string claim_id FK "Reference to claims.id"
        string assessment_stage "BASELINE / TRANSFER"
        float score_evidence_eval "0 - 20"
        float score_claim_specificity "0 - 20"
        float score_risk_awareness "0 - 20"
        float score_assumption_awareness "0 - 20"
        float score_confidence_calibration "0 - 20"
        float total_score "0 - 100"
        text user_responses "JSON payload"
        text rubric_feedback "JSON feedback"
        datetime created_at "Created timestamp"
    }
```

---

## 2. Model Specifications

### 2.1 `claims` Table
Stores raw submitted claims and their structured parameters. Omitted parameters are strictly persisted as `NULL`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY, Indexed | UUID v4 string |
| `original_claim` | `TEXT` | NOT NULL | Full unmodified user submission text |
| `source_url` | `VARCHAR(512)` | NULLABLE | Original link where the claim appeared |
| `source_platform` | `VARCHAR(64)` | NULLABLE | Origin platform (Telegram, X, WhatsApp, etc.) |
| `submitted_at` | `DATETIME` | NOT NULL, UTC | Claim submission timestamp |
| `company_name` | `VARCHAR(255)` | NULLABLE | Resolved or user-stated company name |
| `ticker` | `VARCHAR(32)` | NULLABLE | Exchange ticker symbol (e.g., INFY, TCS) |
| `exchange` | `VARCHAR(32)` | NULLABLE | Listed exchange (NSE, BSE, NYSE) |
| `claim_direction` | `VARCHAR(32)` | NULLABLE | BULLISH, BEARISH, NEUTRAL, UNKNOWN |
| `target_value` | `FLOAT` | NULLABLE | Extracted numerical target |
| `target_unit` | `VARCHAR(32)` | NULLABLE | Unit (%, INR, USD) |
| `time_horizon` | `VARCHAR(128)` | NULLABLE | Stated horizon (e.g., 2 weeks, Q3 FY26) |
| `entry_condition` | `TEXT` | NULLABLE | Stated trigger or price for entry |
| `exit_condition` | `TEXT` | NULLABLE | Stated target price or profit-taking trigger |
| `invalidation_condition` | `TEXT` | NULLABLE | Stated condition that falsifies the claim |
| `evidence_or_rationale` | `TEXT` | NULLABLE | Rationale cited in original text |
| `provenance_status` | `VARCHAR(32)` | NOT NULL, Default: `'USER_PROVIDED'` | REAL, SYNTHETIC, USER_PROVIDED, AI_GENERATED |
| `is_ambiguous_entity` | `BOOLEAN` | NOT NULL, Default: `FALSE` | Flagged if company name/ticker is ambiguous |
| `entity_ambiguity_notes` | `TEXT` | NULLABLE | Explanation of entity ambiguity |
| `created_at` | `DATETIME` | NOT NULL, UTC | Record creation timestamp |

---

### 2.2 `interpretation_forks` Table
Stores counterfactual interpretations and diverging assumption trees.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY, Indexed | UUID v4 string |
| `claim_id` | `VARCHAR(36)` | FOREIGN KEY (`claims.id` ON DELETE CASCADE), NOT NULL, Indexed | Parent claim identifier |
| `title` | `VARCHAR(255)` | NOT NULL | Title of the interpretation fork |
| `description` | `TEXT` | NOT NULL | Explanation of the interpretation |
| `ambiguous_phrase` | `VARCHAR(255)` | NOT NULL | Extracted phrase triggering ambiguity |
| `assumptions` | `TEXT` | NOT NULL | JSON-encoded string array of key assumptions |
| `information_required` | `TEXT` | NOT NULL | Regulatory filings required to verify |
| `is_ai_generated` | `BOOLEAN` | NOT NULL, Default: `TRUE` | Explicit provenance flag |
| `created_at` | `DATETIME` | NOT NULL, UTC | Record creation timestamp |

---

### 2.3 `evidence` Table
Global registry of corporate disclosures and market records.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY, Indexed | UUID v4 string |
| `title` | `VARCHAR(512)` | NOT NULL | Descriptive title of filing |
| `document_title` | `VARCHAR(512)` | NULLABLE | Official document name |
| `publisher` | `VARCHAR(255)` | NOT NULL | Publisher (NSE India, SEC EDGAR Disclosures) |
| `source_url` | `VARCHAR(1024)` | NOT NULL | Direct link to filing / archive PDF |
| `publication_date` | `DATETIME` | NULLABLE, UTC | Filing date reported by the exchange |
| `retrieval_timestamp` | `DATETIME` | NOT NULL, UTC | Timestamp when FinTrace fetched record |
| `evidence_category` | `VARCHAR(64)` | NOT NULL | COMPANY_DISCLOSURE, MARKET_DATA, etc. |
| `company_identifier` | `VARCHAR(64)` | NULLABLE, Indexed | Symbol or name |
| `company_symbol` | `VARCHAR(32)` | NULLABLE, Indexed | Verified NSE ticker (e.g., INFY) |
| `company_isin` | `VARCHAR(32)` | NULLABLE, Indexed | International Securities Identification Number |
| `source_jurisdiction` | `VARCHAR(16)` | NOT NULL, Default: `'IN'` | Origin country code (IN, US) |
| `exchange` | `VARCHAR(32)` | NOT NULL, Default: `'NSE'` | Exchange (NSE, SEC, BSE) |
| `content_summary` | `TEXT` | NOT NULL | Extracted summary of the disclosure |
| `provenance_status` | `VARCHAR(32)` | NOT NULL, Default: `'REAL'` | REAL, SYNTHETIC, USER_PROVIDED, AI_GENERATED |
| `raw_payload` | `TEXT` | NULLABLE | Raw JSON response payload |
| `created_at` | `DATETIME` | NOT NULL, UTC | Record creation timestamp |

---

### 2.4 `claim_evidence` Table
Many-to-many association linking claims to relevant evidence records.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY, Indexed | UUID v4 string |
| `claim_id` | `VARCHAR(36)` | FOREIGN KEY (`claims.id` ON DELETE CASCADE), NOT NULL, Indexed | Claim reference |
| `evidence_id` | `VARCHAR(36)` | FOREIGN KEY (`evidence.id` ON DELETE CASCADE), NOT NULL, Indexed | Evidence reference |
| `relevance_score` | `FLOAT` | NOT NULL, Default: `1.0` | Algorithmic relevance weight |
| `association_notes` | `TEXT` | NULLABLE | Notes describing connection |
| `created_at` | `DATETIME` | NOT NULL, UTC | Association timestamp |

---

### 2.5 `analyses` Table
Stores execution results from the Decision Robustness Compiler.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY, Indexed | UUID v4 string |
| `claim_id` | `VARCHAR(36)` | FOREIGN KEY (`claims.id` ON DELETE CASCADE), NOT NULL, Indexed | Evaluated claim |
| `primary_provider` | `VARCHAR(32)` | NOT NULL | Primary LLM provider (groq) |
| `secondary_provider` | `VARCHAR(32)` | NOT NULL | Secondary review LLM provider (gemini) |
| `provider_status` | `VARCHAR(32)` | NOT NULL | SUCCESS, FALLBACK_USED, NEEDS_VERIFICATION, PROVIDER_UNAVAILABLE |
| `fallback_reason` | `TEXT` | NULLABLE | Reason if fallback was triggered |
| `falsifiability_score` | `FLOAT` | NOT NULL | Deterministic testability score (0–100) |
| `missing_fields` | `TEXT` | NOT NULL | JSON list of omitted parameters |
| `testability_explanation` | `TEXT` | NOT NULL | Detailed testability evaluation |
| `categorized_statements` | `TEXT` | NOT NULL | JSON map: SOURCE_FACT, AI_INTERPRETATION, USER_ASSUMPTION, UNRESOLVED_QUESTION |
| `validation_status` | `VARCHAR(32)` | NOT NULL | PASSED, WARNING, FAILED |
| `validation_notes` | `TEXT` | NULLABLE | JSON list of validation warnings |
| `primary_output_summary` | `TEXT` | NULLABLE | Summary from primary provider |
| `secondary_output_summary` | `TEXT` | NULLABLE | Summary from secondary provider |
| `created_at` | `DATETIME` | NOT NULL, UTC | Analysis creation timestamp |

---

### 2.6 `decisions` Table
Tracks user stances in the Virtual Decision Lab before and after reviewing evidence.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY, Indexed | UUID v4 string |
| `claim_id` | `VARCHAR(36)` | FOREIGN KEY (`claims.id` ON DELETE CASCADE), NOT NULL, Indexed | Evaluated claim |
| `interpretation_id` | `VARCHAR(36)` | FOREIGN KEY (`interpretation_forks.id` ON DELETE SET NULL), NULLABLE, Indexed | Selected fork (if any) |
| `initial_thesis` | `TEXT` | NOT NULL | Stance prior to counter-evidence |
| `initial_confidence` | `FLOAT` | NOT NULL | Stated confidence 0–100% |
| `initial_allocation` | `FLOAT` | NOT NULL | Hypothetical allocation 0–100% |
| `revised_thesis` | `TEXT` | NULLABLE | Revised stance after counter-evidence |
| `revised_confidence` | `FLOAT` | NULLABLE | Revised confidence 0–100% |
| `revised_allocation` | `FLOAT` | NULLABLE | Revised allocation 0–100% |
| `reason_for_change` | `TEXT` | NULLABLE | Explanation for stance shift |
| `assumptions_evaluated` | `TEXT` | NULLABLE | JSON string list of tested assumptions |
| `created_at` | `DATETIME` | NOT NULL, UTC | Initial stance timestamp |
| `updated_at` | `DATETIME` | NOT NULL, UTC | Revision timestamp |

---

### 2.7 `assessments` Table
Evaluates user critical thinking ability across 5 rubric dimensions.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY, Indexed | UUID v4 string |
| `session_id` | `VARCHAR(64)` | NOT NULL, Indexed | User session index |
| `claim_id` | `VARCHAR(36)` | FOREIGN KEY (`claims.id` ON DELETE CASCADE), NOT NULL, Indexed | Evaluated claim |
| `assessment_stage` | `VARCHAR(32)` | NOT NULL | BASELINE, ASSISTED_PRACTICE, INDEPENDENT_TRANSFER |
| `score_evidence_eval` | `FLOAT` | NOT NULL | Evidence evaluation score (0–20) |
| `score_claim_specificity` | `FLOAT` | NOT NULL | Claim specificity score (0–20) |
| `score_risk_awareness` | `FLOAT` | NOT NULL | Risk awareness score (0–20) |
| `score_assumption_awareness` | `FLOAT` | NOT NULL | Assumption awareness score (0–20) |
| `score_confidence_calibration` | `FLOAT` | NOT NULL | Confidence Justification & Epistemic Alignment score (0–20) |
| `total_score` | `FLOAT` | NOT NULL | Composite evaluation score (0–100) |
| `user_responses` | `TEXT` | NOT NULL | JSON serialization of user answers |
| `rubric_feedback` | `TEXT` | NOT NULL | JSON serialization of dimension feedback |
| `created_at` | `DATETIME` | NOT NULL, UTC | Assessment completion timestamp |

---

## 3. Cascade Rules & Deletion Behavior

- **Deleting a Claim (`DELETE /api/v1/claims/{claim_id}`):**
  - Triggers cascade deletion of all child `interpretation_forks`, `analyses`, `claim_evidence` associations, `decisions`, and `assessments`.
  - Global `evidence` master records are preserved to prevent redownloading identical filings.
- **Deleting an Interpretation Fork:**
  - `decisions.interpretation_id` uses `ON DELETE SET NULL`. The decision record is preserved with its thesis and allocation intact, while the foreign key is set to `NULL`.

---

## 4. SQLite Configuration & PostgreSQL Readiness

1. **SQLite Default:**
   - Configured with `connect_args={"check_same_thread": False}` in `database.py`.
   - Thread-safe for multi-worker FastAPI requests.
   - Dynamic schema migration via `PRAGMA table_info` and non-destructive `ALTER TABLE ADD COLUMN`.
2. **PostgreSQL Compatibility:**
   - All models use standard ANSI SQL column types (`VARCHAR`, `TEXT`, `FLOAT`, `BOOLEAN`, `DATETIME`).
   - Primary keys use standard 36-character UUID strings, which directly map to `UUID` or `VARCHAR(36)` in PostgreSQL.
   - Structured JSON arrays and objects are stored as `TEXT` in SQLite; to migrate to PostgreSQL, configure `DATABASE_URL=postgresql://user:password@localhost:5432/fintrace` and optionally swap `Column(Text)` with `sqlalchemy.dialects.postgresql.JSONB`.
