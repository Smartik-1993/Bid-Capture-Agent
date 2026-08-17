# 🛰️ AI Bid Capture Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Google GenAI](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed-success.svg)](#-testing)

An autonomous AI-powered procurement intelligence agent designed to discover, parse, synthesize, and match **U.S. Federal (SAM.gov)** and **SLED (State, Local, and Education)** government contract opportunities (RFPs, RFQs, Solicitations) against specific corporate capability decks.

---

## 🌟 Key Features

- **🌐 Multi-Portal Ingestion**:
  - **Federal**: Real-time integration with SAM.gov API + simulated live generation when offline.
  - **SLED Portals**: Aggregators for Texas SmartBuy (ESBD), California Cal eProcure, New York State Contract Reporter (NYS CR), and Florida Vendor Information Portal (VIP).
- **🎯 Intelligent NAICS & Keyword Filtering**:
  - Target lookahead windowing for response deadlines (automatically filters out expired solicitations).
  - Multi-source deduplication and solicitation number indexing.
- **🤖 Gemini 2.5 Flash AI Extraction & Fit Scoring**:
  - Automatically synthesizes Executive Summaries, Statement of Work (SOW) key deliverables, mandatory qualifications, and evaluation factor weights.
  - Generates a **0–100 Capability Fit Score** and qualitative rationale tailored to the active company profile.
  - Rule-based heuristic fallback engine when running offline.
- **📄 Capability Deck Ingestion & Multi-Profile Deck Engine**:
  - Upload PDF or text company capability decks to auto-extract NAICS codes, core keywords, certifications, and clearances using AI.
  - Switch between capability profiles (e.g., *A11N Holdings LLC* and *PIScaleX*) with instantaneous pipeline re-scoring.
- **💬 Interactive RFP Chat Assistant**:
  - Chat in real time with Gemini about specific RFPs to uncover submission risks, mandatory personnel certifications, and compliance checklists.
- **📊 Pursuit Pipeline & Export**:
  - Track pursuit status across workflow stages (`NEW`, `REVIEWING`, `BID`, `NO_BID`, `ARCHIVED`).
  - Export filtered opportunities to CSV or JSON with one click.
- **🎨 Glassmorphism Web Dashboard**:
  - Fast, responsive vanilla HTML/CSS/JS frontend with live KPI cards, search debouncing, and rich RFP inspection modals.

---

## 🏗️ Architecture & Workflow

```
 ┌──────────────────────┐   ┌───────────────────────────────┐
 │   SAM.gov (Federal)  │   │  SLED Portals (TX, CA, NY, FL)│
 └──────────┬───────────┘   └───────────────┬───────────────┘
            │                               │
            ▼                               ▼
    ┌───────────────────────────────────────────────┐
    │          Bid Capture Pipeline                 │
    │  - NAICS Matching   - Deadline Filtering      │
    │  - Deduplication    - PDF Document Parsing    │
    └───────────────────────┬───────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────┐
    │         Gemini 2.5 Flash AI Engine            │
    │  - Structured SOW Extraction                  │
    │  - Mandatory Qualifications Breakdown         │
    │  - 0-100 Fit Score vs. Active Capability Deck │
    └───────────────────────┬───────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────┐
    │       FastAPI Backend & SQLite Database       │
    │  - Opportunities API     - Profile Switcher   │
    │  - Interactive AI Q&A    - CSV / JSON Export  │
    └───────────────────────┬───────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────┐
    │     Modern Dark Glassmorphism Dashboard       │
    │  - Real-time KPIs        - RFP Modal Inspector│
    │  - Filter Controls       - Embedded AI Chat   │
    └───────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
├── backend/
│   ├── api/
│   │   ├── main.py                  # FastAPI app entrypoint & static mounting
│   │   ├── routes_opportunities.py  # RFP listing, filtering, search, export & status
│   │   ├── routes_profile.py        # Profile management, deck upload & re-scoring
│   │   ├── routes_capture.py        # Ingestion trigger & execution run logs
│   │   └── routes_ai.py             # Gemini RFP Q&A and re-analysis
│   ├── extraction/
│   │   ├── ai_analyzer.py           # Gemini 2.5 Flash extraction & scoring engine
│   │   └── doc_parser.py            # PDF document & SOW/Section L/M parser
│   ├── ingestion/
│   │   ├── pipeline.py              # Ingestion orchestrator & deduplication
│   │   ├── sam_gov.py               # SAM.gov Federal connector
│   │   └── sled_scrapers.py         # SLED portal aggregators (TX, CA, NY, FL)
│   ├── config.py                    # App configuration & environment settings
│   ├── database.py                  # SQLAlchemy engine, session & profile seeding
│   └── models.py                    # SQLAlchemy ORM models & Pydantic schemas
├── frontend/
│   ├── index.html                   # Dashboard UI
│   ├── app.js                       # Client controller, search & interactive AI chat
│   └── styles.css                   # Responsive dark glassmorphism design system
├── tests/
│   ├── test_api.py                  # REST API & AI endpoints tests
│   ├── test_database.py             # DB schema & seeding verification
│   └── test_ingestion.py            # Ingestion connectors, deduplication & filtering
├── requirements.txt                 # Python dependencies
├── run.py                           # Server launcher script
├── .env.example                     # Environment template
└── .gitignore                       # Git ignore rules
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher installed on your system.

### 2. Clone Repository & Install Dependencies
```bash
git clone https://github.com/your-username/bid-capture-agent.git
cd bid-capture-agent

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and add your API keys:
```env
# Required for live Gemini analysis & AI Q&A:
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for live federal querying):
SAM_GOV_API_KEY=your_sam_gov_api_key_here
```
> *Note: If no API keys are provided, the agent runs seamlessly using built-in intelligent rule-based fallbacks and realistic live simulation data.*

### 4. Run the Agent
```bash
python run.py
```

- **Dashboard UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Reference**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Testing

Run the automated test suite with pytest:
```bash
python -m pytest
```

All 16 test cases validate:
- Ingestion connectors (SAM.gov & SLED scrapers)
- Multi-source filtering & deduplication
- Database seeding with corporate capability profiles
- Opportunity detail inspection, status updates (`BID`, `NO_BID`), and CSV/JSON export
- Interactive AI Q&A and pipeline re-scoring
- Capability deck upload & profile switching

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/opportunities` | Search, filter, and sort RFPs across Federal and SLED sources |
| `GET` | `/api/opportunities/{id}` | Retrieve complete RFP record with SOW deliverables and compliance checklist |
| `PATCH` | `/api/opportunities/{id}/status` | Update pursuit workflow status (`NEW`, `REVIEWING`, `BID`, `NO_BID`) |
| `GET` | `/api/opportunities/stats` | Dashboard KPI metrics and fit score analytics |
| `GET` | `/api/opportunities/export` | Export filtered opportunities as CSV or JSON |
| `POST` | `/api/capture/run` | Execute on-demand bid capture across portals |
| `GET` | `/api/capture/logs` | View history and execution logs of capture runs |
| `GET` | `/api/profile` | Get active capability deck and targeting rules |
| `GET` | `/api/profile/all` | List all available capability profiles |
| `POST` | `/api/profile/switch/{id}` | Switch active capability deck and re-score pipeline |
| `POST` | `/api/profile/upload-deck` | Upload and parse new capability deck (PDF/text) with AI |
| `POST` | `/api/profile/rescore-pipeline` | Re-score all captured RFPs against active capability profile |
| `POST` | `/api/ai/ask/{id}` | Interactive Gemini Q&A on specific RFP requirements |
| `POST` | `/api/ai/reanalyze/{id}` | Re-evaluate RFP match against active capability profile |

---

## 🚢 Deployment Guide

The application is container-ready and can be deployed in minutes to any cloud hosting provider.

### Option 1: Render (Recommended & Easiest)
1. Sign up/log in at [render.com](https://render.com/).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository `bid-capture-agent`.
4. Configure the settings:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `SAM_GOV_API_KEY`: *(Optional)* Your SAM.gov API key
6. Click **Deploy Web Service**.

### Option 2: Railway
1. Go to [railway.app](https://railway.app/) and create a new project.
2. Select **Deploy from GitHub repo** and choose your repository.
3. In **Variables**, add `GEMINI_API_KEY` (and optional `SAM_GOV_API_KEY`).
4. Railway will automatically detect the `Dockerfile` or `Procfile` and deploy your service.

### Option 3: Google Cloud Run (Serverless)
```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

# Build & Deploy directly from source
gcloud run deploy bid-capture-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your_api_key_here"
```

### Option 4: Docker / VPS Self-Hosting
```bash
# Build Docker image
docker build -t bid-capture-agent .

# Run container
docker run -d -p 8000:8000 \
  -e GEMINI_API_KEY="your_gemini_api_key_here" \
  -v $(pwd)/data:/app/data \
  --name bid-capture-agent \
  bid-capture-agent
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
