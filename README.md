# 🇮🇳 Adhikar Saathi (ಅಧಿಕಾರ ಸಾಥಿ / अधिकार साथी)
### *Multilingual Policy, Rights & Welfare Scheme Explainer for Karnataka & India*

> **IDEA//FORGE Online Hackathon** — Track 1, Problem 1:  
> *"An AI that reads government notices, welfare schemes, and local laws, explaining them in simple language and regional languages. It helps people check scheme eligibility, understand their rights, and answers by voice."*

---

## 🌟 Key Features

1. **Deterministic Rules Engine (Zero Hallucination)**:
   - Eligibility verdicts (`Eligible`, `Not eligible`, `Maybe`) are computed **strictly by deterministic mathematical and logical rule evaluation** over structured schema JSON—never by LLM guessing.
   - The LLM's role is restricted to translating and summarizing verdicts in simple 6th-grade regional prose.
2. **Three-Tier Knowledge Base**:
   - **Tier 1 (Verified)**: Hand-curated and audited scheme rules (`/data/schemes_verified.json`).
   - **Tier 2 (Extracted)**: Pipeline-extracted from `/data/raw/` with confidence scores; verdicts capped at "Likely/Maybe" with explicit verification advisories.
   - **Tier 3 (Link-Out)**: Queries for unlisted or non-existent schemes trigger verified government portal link-outs (`myscheme.gov.in`, `karnataka.gov.in`) with disclaimers.
3. **Multilingual Voice & Chat (`kn`, `hi`, `en`)**:
   - Spoken interactions in Kannada, Hindi, and English.
   - Dual-layer speech engine: High-performance browser Web Speech API on the client with backend Gnani API integration interface and fallback.
4. **Notice Scanner (Gemini Vision OCR)**:
   - Upload or photograph official notices/tax demands/summons.
   - Extracts: Summary, Action Demanded, Exact Deadlines, Urgency Rating, and Next Steps.
5. **Citizen Rights & Legal Grievance Explainer**:
   - Answers rights inquiries (unpaid MGNREGA wages, RTI filing, consumer protection, women's helpline) grounded in `data/rights_kb.json`.
6. **Data Ingestion Pipeline & DBControl Admin Console**:
   - Converts raw government PDFs/documents into structured schema records.
   - Includes `/admin` web console to review, approve, and promote extracted Tier 2 records to Tier 1 verified status.
7. **Rigorous 30-Question Multilingual Benchmark**:
   - Full evaluation dataset (`/data/evaluation_set_30.json`) across all 3 languages tested with automated continuous verification.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    User["👤 Citizen (Farmer / Student / Worker)"] --> UI["🖥️ React + Vite PWA (Mobile-First)"]
    UI -->|Voice / Text (kn, hi, en)| API["⚡ FastAPI Gateway"]
    
    subgraph Core Engine
        API --> Engine["⚙️ Deterministic Rules Engine"]
        API --> Selector["❓ Next-Question Selector"]
        API --> NoticeService["👁️ Gemini Vision Notice Scanner"]
        API --> LinkOut["🔗 Tier 3 Link-Out Service"]
        API --> IngestPipeline["📥 Document Ingestion Pipeline"]
    end

    subgraph Data Layer
        Engine --> T1[("Tier 1: Verified Schemes (JSON)")]
        IngestPipeline --> T2[("Tier 2: Extracted Schemes (JSON)")]
        NoticeService --> Gemini["Gemini 2.5 Flash"]
        API --> SQLite[("SQLite: Cache, Users & Audit Logs")]
        API --> RightsKB[("Rights Knowledge Base")]
    end

    subgraph Governance
        Admin["👮 Admin Reviewer"] --> DBControl["🛡️ DBControl Web Console (/admin)"]
        DBControl -->|Approve & Promote| T1
    end
```

---

## 💻 Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, Web Speech API (PWA Ready).
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2.
- **AI & OCR**: Google Gemini API (`gemini-2.5-flash`), Gemini Structured Output & Multimodal Vision.
- **Speech**: Client-side Web Speech API + backend Gnani API provider interface.
- **Data & Storage**: SQLite (`adhikar_saathi.db`), JSON Schemas, PDFPlumber document parsing.
- **Testing**: Pytest, Pytest-Asyncio (90+ unit and integration tests).

---

## 📂 Repository Structure

```
adhikar-saathi/
├── backend/
│   ├── app/
│   │   ├── engine/          # Deterministic rules engine, validator, loader, question selector
│   │   ├── models/          # Pydantic schemas (Scheme, Profile, Rights, Notice, Verdict)
│   │   ├── pipeline/        # Ingestion pipeline (extractor, reader, embeddings, deduplicator)
│   │   ├── prompts/v1/      # Versioned prompts (notice scanner, explainer, rights)
│   │   ├── routes/          # API routers (admin, chat, notice, speech)
│   │   ├── services/        # Business logic (retrieval, cache, notice, speech, linkout)
│   │   ├── auth.py          # Session auth & admin verification
│   │   ├── config.py        # Settings & environment validation
│   │   ├── db.py            # SQLite database initialization
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # Complete unit, integration, and benchmark test suite
│   └── requirements.txt     # Python dependencies
├── data/
│   ├── evaluation_set_30.json # 30-Question Multilingual Benchmark Set
│   ├── rights_kb.json         # Grounded rights & grievance knowledge base
│   ├── schemes_verified.json  # Tier 1 verified schemes
│   └── schemes_extracted.json # Tier 2 auto-extracted schemes
├── DBControl/               # Static administrative management console
├── docs/
│   ├── MASTER_PROMPT- PART 1.md # Master architectural blueprint
│   ├── MASTER_PROMPT_2.json     # Schema specification
│   └── DEMO_SCRIPT.md           # 5-minute hackathon judge presentation script
├── frontend/                # React + Vite client
├── render.yaml              # Render backend cloud deployment config
├── vercel.json              # Vercel frontend cloud deployment config
├── .env.example             # Environment template
└── README.md                # Project documentation
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
# From repository root
cd backend
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit ../.env to add your GEMINI_API_KEY

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/docs`  
DBControl Admin Console will be live at: `http://localhost:8000/admin`

### 3. Frontend Setup
```bash
# In a new terminal window
cd frontend
npm install
npm run dev
```
Client UI will be live at: `http://localhost:5173`

---

## 🧪 Testing & Verification

Run the complete test suite (Rules Engine, Validator, Chat, Notice Scanner, Speech Routes, and the 30-Question Benchmark):

```powershell
# Set PYTHONPATH and run all tests
$env:PYTHONPATH="."
pytest backend/tests -v
```

All **90+ unit tests** will execute and report passing status.

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Healthcheck and demo mode status |
| `GET` | `/api/stats` | Real-time counts of verified vs. extracted schemes |
| `GET` | `/api/schemes` | Filterable list of all schemes by category, group, tier |
| `POST` | `/api/eligibility` | Evaluates user profile deterministically and suggests next question |
| `POST` | `/api/chat` | Multilingual citizen inquiry chat with grounded citations |
| `POST` | `/api/notice/scan` | Gemini Vision analysis of uploaded notice photos/PDFs |
| `POST` | `/api/stt` | Speech-to-text with Gnani/Web Speech fallback |
| `POST` | `/api/tts` | Text-to-speech audio synthesis / browser instruction |
| `GET` | `/api/speech/providers` | Status and language capabilities of speech engines |
| `POST` | `/api/admin/ingest` | Triggers document ingestion pipeline from `/data/raw/` |
| `GET` | `/api/admin/review` | Lists unverified Tier 2 schemes for review |
| `POST` | `/api/admin/review/{id}` | Approves & promotes scheme to Tier 1 or rejects |

---

## ☁️ Deployment

- **Frontend (Vercel)**:
  - Configured via [`vercel.json`](file:///d:/Projects/adhikar-saathi/vercel.json).
  - Simply import the Git repository into Vercel, set the Root Directory to `frontend`, and deploy.
- **Backend (Render)**:
  - Configured via [`render.yaml`](file:///d:/Projects/adhikar-saathi/render.yaml).
  - Deploy using Render Blueprint with `GEMINI_API_KEY` set in the environment variables.

---

## 📜 Credits & Attributions

In compliance with open-source licenses and academic integrity guidelines, the following tools, libraries, and open datasets were used in the development of **Adhikar Saathi**:

- **AI & Vision Foundation**: Google Gemini API (`gemini-2.5-flash`) for multimodal document OCR and plain-language summarization.
- **Backend & Schemas**: Python 3, FastAPI, Pydantic v2, Uvicorn, PDFPlumber, and Pytest.
- **Frontend & UI**: React 18, Vite, Tailwind CSS, and Lucide React.
- **Speech Synthesis & Recognition**: W3C Web Speech API (configured for `en-IN`, `kn-IN`, and `hi-IN` regional cadences) and Gnani speech interface.
- **Public Datasets & Statutory Law**:
  - **India Code**: Central and state statutes (MGNREGA 2005, RTI 2005, Consumer Protection 2019, Senior Citizens Act 2007, DV Act 2005).
  - **Mahiti Kanaja**: Government of Karnataka public welfare portal data (via UrbanMorph open data archives).
  - **Open Government Data (OGD) Platform India**: `data.gov.in` public domain welfare scheme datasets.

---

## ⚖️ Disclaimer
*Adhikar Saathi is an AI-powered informational tool built for hackathon demonstration. It does not constitute formal legal advice. Citizens are always directed to verify findings at the respective official government portals and taluk offices.*
