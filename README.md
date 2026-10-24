# Tally Twin: Drug Behaviour Prediction

A digital twin prototype that explores how a drug might behave in a specific person by combining patient factors (age, weight, kidney/liver function, co-medications, allergies, etc.) with drug information.

> **Important:** This is a research & educational prototype only. It is **not** a medical device, clinical decision-support system, or substitute for professional medical advice.

## Team and Institution

- **Team name:** Yakult
- **College / University:** Jaypee Institute of Information Technology, Noida
- **Team members:** Sudiksha Srivastav, Katya Chadha
- **Faculty Mentor:** Dr. Deeksha Pandey
- **Team leader:** Sudiksha Srivastav

## Problem Statement

Standard dosing guidelines are largely based on population averages. Individual factors such as age, body composition, renal/hepatic function, co-medications and genetics can significantly alter drug exposure and risk.

Accessible, transparent tools that let students and researchers explore these patient-specific effects are still limited. Tally Twin is an attempt to build a lightweight, open prototype that brings patient data and drug data together and surfaces both predictions and their limitations.

## Healthcare Use Case

A user enters patient details and a medicine (dose, route, frequency). The system generates a structured report containing:

- Patient & drug profile summary
- Basic pharmacokinetic estimates (where data allows)
- Interaction & contraindication flags
- Risk indicators and confidence notes
- Factors that most influenced the result

The output is intended for exploration and learning, not for clinical decision making.

## How the Prototype Works

1. User fills the patient form (demographics, labs, conditions, current medicines, allergies).
2. User enters drug name / dose / route / frequency (or uploads a pack image for composition).
3. Backend combines the inputs with available knowledge bases and simple models.
4. A structured report is returned.
5. User can download the report as PDF.

## Technical Stack (Actual Implementation)

| Layer              | Technology                                                     |
|--------------------|----------------------------------------------------------------|
| Frontend           | Vanilla HTML + CSS + JavaScript (static files served by nginx) |
| Backend            | Python 3.11, FastAPI, Uvicorn                                  |
| Database           | PostgreSQL 15 (via Docker) + Alembic migrations                |
| Authentication     | Simple API-key based (`API_KEYS` env var)                      |
| Containerisation   | Docker + Docker Compose                                        |
| PDF generation     | Backend endpoint that returns PDF report                       |
| Optional chemistry | RDKit (not installed in current image → molecular properties limited) |

### What is currently implemented

- Patient + Drug input forms
- Simulation / report generation endpoint
- PDF download of the simulation report
- Health check endpoint (`/api/v1/health`)
- Basic drug composition extraction from pack/label images
- Demo fallback mode when external data is unavailable
- CORS, rate limiting, environment-based configuration

### What is **not** yet fully implemented / limited

- Full lab-report OCR → auto-fill (partial work started, not production-ready)
- Advanced PBPK or machine-learning models
- Genetic (CYP) data handling beyond simple flags
- Concentration–time curve visualisation with real PK parameters for every drug
- Production-grade uncertainty quantification

## Architecture (High-level)

```text
Browser (localhost:8080)
        │
        ▼
nginx (static frontend)
        │
        ▼  /api/*
FastAPI (port 8000)
        │
        ├── PostgreSQL
        ├── Simple rule / lookup engines
        └── PDF generator
```

## Running the Prototype Locally

```bash
# 1. Clone / open the project
cd tally_twin

# 2. Create environment file
cp .env.example .env   # or create manually (see values below)

# 3. Make frontend readable (Mac / Docker Desktop sometimes needs this)
chmod -R a+rX frontend deploy

# 4. Start everything
docker compose up --build -d
```

Then open:

- **UI:** http://localhost:8080
- **API docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/api/v1/health

### Recommended `.env` (development)

```env
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg2://digitaltwin:digitaltwin_secret@db:5432/digital_twin
POSTGRES_PASSWORD=digitaltwin_secret
SECRET_KEY=dev-only-insecure-secret-key-change-me
API_KEYS=dev-local-key-change-me
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
ALLOW_DEMO_FALLBACK=true
RATE_LIMIT_PER_MINUTE=60
ENABLE_DOCS=true
```

### Set the API key in the browser

In the browser console (once):

```javascript
localStorage.setItem('DT_API_KEY', 'dev-local-key-change-me');
location.reload();
```

## Outcome & Current Status

**What works:** End-to-end flow from form → report → PDF download. Health checks, Docker Compose setup, basic composition OCR, and demo mode.

**What was evaluated:** Manual end-to-end testing with common drugs (e.g. ibuprofen, metformin) and various patient profiles.

**Known limitations:**

- Molecular property calculation is limited when RDKit is absent.
- Lab-report auto-fill is incomplete.
- PK predictions rely on simplified models / lookup data and should not be treated as clinically accurate.
- No formal clinical validation has been performed.

**Next steps (realistic):**

- Complete and harden lab-report OCR + auto-fill.
- Improve PK parameter coverage and transparency of assumptions.
- Add better uncertainty communication in the report.
- Add unit / integration tests.
- Prepare architecture diagram and 20+ minute walkthrough video for submission.

## Safety Note

This project is for research, education and demonstration purposes only.

Its outputs must not be used to choose, change or stop any medicine or dose.

Drug-response predictions can be wrong, especially when patient data is incomplete or evidence is limited. Any future clinical use would require rigorous validation, regulatory review and clinical oversight.

## Youtube Video Link 
`https://youtu.be/njjgWnlQdoI`

## Licence

Proposed: Apache License 2.0 (subject to final team decision).

A root-level `LICENSE` file should be added once the choice is confirmed.
