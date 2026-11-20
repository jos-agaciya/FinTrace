# FinTrace — Setup and Configuration Guide

This guide details the complete procedure for configuring, installing, initializing, and running the FinTrace backend service on Windows PowerShell and macOS/Linux environments.

---

## 1. Prerequisites

Before setting up FinTrace, ensure your workstation meets the following requirements:
- **Operating System:** Windows 10/11, macOS Sonoma/Sequoia, or Ubuntu 22.04/24.04 LTS.
- **Python:** Python 3.11.x (verified on Python 3.11.6). Python 3.10+ is supported; Python 3.11+ is recommended.
- **Git:** Version 2.30+ for branch and version management.
- **Network Access:** Unrestricted HTTPS outbound access to:
  - `https://www.nseindia.com` (for live Indian corporate announcements)
  - `https://nsearchives.nseindia.in` (for live PDF circulars)
  - `https://data.sec.gov` (for SEC EDGAR filings)
  - `https://api.groq.com` (if running live Groq LLM queries)
  - `https://generativelanguage.googleapis.com` (if running live Gemini LLM queries)

---

## 2. Environment Preparation

### Windows PowerShell

1. Open PowerShell and navigate to the project root:
   ```powershell
   cd C:\Projects\FinTrace\FinTrace
   ```

2. Confirm active Git branch:
   ```powershell
   git branch --show-current
   # Output must be: jos-backend
   ```

3. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *Note: If script execution is restricted, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the current terminal session.*

4. Upgrade `pip` and install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

---

### macOS / Linux

1. Open Terminal and navigate to the project directory:
   ```bash
   cd /path/to/FinTrace
   ```

2. Confirm active branch:
   ```bash
   git branch --show-current
   # Output must be: jos-backend
   ```

3. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

---

## 3. Configuration & Environment Variables

Copy the provided `.env.example` template to `.env`:

### Windows PowerShell:
```powershell
Copy-Item backend/.env.example backend/.env
```

### macOS / Linux:
```bash
cp backend/.env.example backend/.env
```

### Environment Variable Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `APP_NAME` | String | `"FinTrace API"` | Application identifier string |
| `APP_ENV` | String | `"development"` | Environment mode (`development`, `testing`, `production`) |
| `DEBUG` | Boolean | `true` | Enables SQLAlchemy SQL echo and verbose error logs in development |
| `API_V1_PREFIX` | String | `"/api/v1"` | Base URL prefix for all API routes |
| `DATABASE_URL` | String | `"sqlite:///./fintrace.db"` | Database connection string. SQLite default; PostgreSQL-ready |
| `GROQ_API_KEY` | String | `None` | API key for Groq Cloud (`gsk_...`). Optional for tests |
| `GEMINI_API_KEY` | String | `None` | API key for Google Gemini API (`AIzaSy...`). Optional for tests |
| `PRIMARY_AI_PROVIDER` | String | `"groq"` | Name of primary LLM provider (`groq` or `gemini`) |
| `SECONDARY_AI_PROVIDER` | String | `"gemini"` | Name of secondary review/fallback LLM provider (`gemini` or `groq`) |
| `AI_REQUEST_TIMEOUT_SECONDS` | Float | `15.0` | Timeout threshold for external LLM requests before failover |
| `AI_MAX_RETRIES` | Integer | `2` | Number of retry attempts on transient network faults |
| `CORS_ORIGINS` | Comma-separated | `"http://localhost:3000,http://localhost:5173"` | Permitted frontend origins for CORS |

---

## 4. Database Initialization & Migrations

FinTrace includes an automatic database initialization and non-destructive column migration routine executed on FastAPI startup.

### How it works:
1. `init_db()` is invoked during application lifespan startup (`backend/app/main.py`).
2. SQLAlchemy creates all tables (`claims`, `interpretation_forks`, `evidence`, `claim_evidence`, `analyses`, `decisions`, `assessments`) if they do not exist.
3. For existing SQLite databases, `PRAGMA table_info(evidence)` checks for newly introduced columns (`document_title`, `company_symbol`, `company_isin`, `source_jurisdiction`, `exchange`) and applies non-destructive `ALTER TABLE` statements dynamically without losing data.

### Manual Initialization (Optional):
You can verify database creation without launching the HTTP server:
```powershell
python -c "from backend.app.core.database import init_db; init_db(); print('Database tables verified.')"
```

---

## 5. Application Startup

Run the development server using Uvicorn with auto-reload:

### Windows PowerShell:
```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### macOS / Linux:
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Verification Endpoints:
- **API Base:** `http://localhost:8000/api/v1`
- **Health Check:** `http://localhost:8000/api/v1/health`
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **ReDoc Technical Docs:** `http://localhost:8000/redoc`
- **OpenAPI Schema JSON:** `http://localhost:8000/api/v1/openapi.json`

---

## 6. Troubleshooting

### Port 8000 Already in Use
If another process is bound to port 8000:
- **Windows:** Check and terminate the conflicting process:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
  Stop-Process -Id <PID> -Force
  ```
- **macOS / Linux:**
  ```bash
  lsof -i :8000
  kill -9 <PID>
  ```
- Alternatively, launch on a different port:
  ```powershell
  uvicorn backend.app.main:app --reload --port 8080
  ```

### SQLite `OperationalError: database is locked`
- Cause: Multiple concurrent processes writing simultaneously without connection pooling.
- Solution: `backend/app/core/database.py` sets `connect_args={"check_same_thread": False}`. Ensure external SQLite viewer tools (e.g. DB Browser for SQLite) are closed while running write-heavy tests.

### Missing API Keys
- If `GROQ_API_KEY` or `GEMINI_API_KEY` are unset, the system does **not** crash or fabricate output. When `POST /api/v1/analysis/{claim_id}/run` is called, it gracefully tags `provider_status="PROVIDER_UNAVAILABLE"` and executes deterministic falsifiability and statement categorization rules without throwing uncaught exceptions.
