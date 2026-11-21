# ⚡ Adhikar Saathi — Operational & Developer Command Manual

Comprehensive command cheat-sheet for running, developing, testing, and deploying **Adhikar Saathi** on Windows (PowerShell) and Linux/macOS (Bash).

---

## 📋 Table of Contents
1. [Prerequisites & Initial Setup](#1-prerequisites--initial-setup)
2. [Running the Application](#2-running-the-application)
3. [Running Tests & Quality Assurance](#3-running-tests--quality-assurance)
4. [Data Ingestion & Pipeline Tools](#4-data-ingestion--pipeline-tools)
5. [Database & Governance (DBControl)](#5-database--governance-dbcontrol)
6. [API Probing (PowerShell & cURL)](#6-api-probing-powershell--curl)
7. [Frontend Build & Deployment](#7-frontend-build--deployment)

---

## 1. Prerequisites & Initial Setup

### Clone & Configure Environment
```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit .env and insert your GEMINI_API_KEY
# Ensure DEMO_MODE=true for testing or false for production
```

### Install Backend Dependencies
```powershell
# From project root
cd backend
pip install -r requirements.txt
cd ..
```

### Install Frontend Dependencies
```powershell
# From project root
cd frontend
npm install
cd ..
```

---

## 2. Running the Application

### Option A: Running Backend & Frontend in Separate Terminals (Recommended for Dev)

**Terminal 1 — Backend (FastAPI + Uvicorn)**
```powershell
# Run from repository root
$env:PYTHONPATH="."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
* Backend API: `http://localhost:8000`
* Interactive API Docs (Swagger): `http://localhost:8000/docs`
* DBControl Admin Console: `http://localhost:8000/admin`

**Terminal 2 — Frontend (Vite + React)**
```powershell
# Run from frontend directory
cd frontend
npm run dev
```
* Citizen Client UI: `http://localhost:5173`

---

## 3. Running Tests & Quality Assurance

All 94 backend tests (Rules Engine, Chat, Validator, Ingestion Pipeline, Notice Scanner, Speech Routes, and 30-Question Benchmark):

### Run All Tests
```powershell
# Set PYTHONPATH to root and run pytest
$env:PYTHONPATH="."
pytest backend/tests -v
```

### Run Specific Test Modules
```powershell
# 1. Deterministic Eligibility Rules Engine (23 tests)
$env:PYTHONPATH="."; pytest backend/tests/test_rules_engine.py -v

# 2. 30-Question Multilingual Benchmark (10 en, 10 kn, 10 hi)
$env:PYTHONPATH="."; pytest backend/tests/test_evaluation_benchmark.py -v

# 3. Document Ingestion Pipeline & Deduplication
$env:PYTHONPATH="."; pytest backend/tests/test_pipeline.py -v

# 4. Notice Scanner (Gemini Vision OCR)
$env:PYTHONPATH="."; pytest backend/tests/test_notice_scanner.py -v

# 5. Speech & Indian Accent Voice Endpoints
$env:PYTHONPATH="."; pytest backend/tests/test_speech.py -v

# 6. DBControl & Admin Review Promotion
$env:PYTHONPATH="."; pytest backend/tests/test_dbcontrol.py -v

# 7. Tier 3 Zero-Hallucination Portal Link-out
$env:PYTHONPATH="."; pytest backend/tests/test_tier3.py -v
```

---

## 4. Data Ingestion & Pipeline Tools

### Ingesting Raw Government Scheme Documents
Place raw PDF or text files in `data/raw/` and trigger the ingestion pipeline:

```powershell
# Ingest local file using Python runner
python -c "from backend.app.pipeline.ingest import run_ingestion_pipeline; run_ingestion_pipeline('data/samples/sample_test_scheme.pdf')"
```

Or trigger ingestion via the Admin API:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/admin/ingest" `
  -Method POST `
  -Headers @{ "X-Admin-Password" = "change_this_admin_password_in_production" } `
  -ContentType "application/json" `
  -Body '{"file_path": "data/samples/sample_test_scheme.pdf"}'
```

---

## 5. Database & Governance (DBControl)

### Access the Administrative Console
Open your browser and navigate to:
```
http://localhost:8000/admin
```
Default master password configured in `.env`: `123456` (or whatever `ADMIN_PASSWORD` is set to).

### Managing Registered Users & Sessions
```powershell
# Clean or reset test users
python scripts/clean_users.py
```

### Inspect SQLite Database Tables
```powershell
# Query user counts & cached responses
sqlite3 data/adhikar_saathi.db "SELECT count(*) FROM users;"
sqlite3 data/adhikar_saathi.db "SELECT count(*) FROM response_cache;"
```

---

## 6. API Probing (PowerShell & cURL)

### 1. Healthcheck
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET
```

### 2. Live Scheme Counts (Verified vs. Extracted)
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/stats" -Method GET
```

### 3. Evaluate Eligibility Deterministically (Farmer Profile)
```powershell
$body = @{
  profile = @{
    age = 42
    state = "Karnataka"
    occupation = "farmer"
    annual_income = 80000
    owns_land = $true
    land_acres = 2.0
  }
  language = "kn"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/eligibility" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### 4. Multilingual Chat Inquiry (Kannada)
```powershell
$body = @{
  message = "ರೈತ ಸಿರಿ ಯೋಜನೆಯ ವಿವರ ತಿಳಿಸಿ"
  language = "kn"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### 5. Check Speech Engine Status & Indian Voices
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/speech/providers" -Method GET
```

---

## 7. Frontend Build & Deployment

### Build Frontend for Production (Vite)
```powershell
cd frontend
npm run build
```
Generates production assets into `frontend/dist/`.

### Preview Production Build Locally
```powershell
cd frontend
npm run preview
```
Runs production preview on `http://localhost:4173`.

### Cloud Deployment
* **Vercel (Frontend)**:
  ```bash
  vercel --prod
  ```
  *(Uses configuration in `vercel.json`)*

* **Render (Backend API)**:
  Connect your GitHub repository to Render using `render.yaml`.
  Set `GEMINI_API_KEY` in Render environment settings.
