# Digital Twin: Personalised Drug Behaviour Prediction

A digital twin for understanding how a drug might behave in a specific person, instead of relying only on what usually happens in an average patient.

People respond to medicines differently. Age, body weight, kidney and liver function, existing conditions, allergies, and other medicines can all affect how a drug behaves. This project brings those factors together and presents the results in a way that is easier to understand.

> **Research / educational tool only. Not a medical device.** Outputs are individualised PK-based risk estimates and must not replace clinical judgement.

## Team and institution

- **Team name:** `Yakult`
- **College / university:** `Jaypee Institute of Information Technology (JIIT), Noida`
- **Faculty mentor:** `Dr. Deeksha Pandey`
- **Team leader:** `Sudiksha Srivastav`
- **Team members:**
  - Sudiksha Srivastav: `Backend and PK engine, lab-report OCR, deployment`
  - Katya Chadha: `Frontend Developer`

## Project title

**Tally-Twin: Personalised Drug Behaviour Prediction**

## Problem statement

Most standard dosing guidelines are based on population averages. They are useful, but they may not fully reflect an individual patient's physiology.

- **Population-based dosing:** Standard guidelines may not account for an individual's physiological profile.
- **Limited access to modelling tools:** Some physiologically based pharmacokinetic (PBPK) platforms are designed for pharmaceutical companies and regulatory work, making them less accessible to students, researchers, and smaller institutions.
- **Narrow existing digital twins:** Some patient digital twins focus on specific diseases or remain at the research stage.
- **Limited transparency for new compounds:** When a drug has little supporting data, predictions can be difficult to interpret and uncertainty may be unclear.

This project explores how an accessible, patient-specific digital twin could bring patient information and drug information together to help explain possible drug behaviour.

## Healthcare use case

A user enters relevant patient details (manually or by uploading a lab report) and information about a medicine. The prototype generates a report with:

- A patient-adjusted concentration-time curve compared with an average adult
- Cmax, AUC, half-life and accumulation
- An exposure risk category (Safe / Caution / High Risk)
- Organ flags (kidney, liver, heart/QT)
- Allergy and condition contraindications
- Rule-based drug-drug interactions
- Dose assessment, explainability drivers, and a confidence score
- A downloadable PDF report for the chart or an MDT discussion

It is intended for research and development. It is **not** a replacement for a doctor, pharmacist, validated clinical decision-support system, or professional dosing guidance.

## How it works

1. **Drug parameters** (CL, Vd, F, ka, fe, therapeutic window) come from a built-in knowledge base, or safe defaults are used when the drug is unknown.
2. **Patient clearance factor** is derived from eGFR/CrCl (CKD-EPI 2021 and Cockcroft-Gault), liver capacity (Child-Pugh-style score), age, lifestyle, and DDI multipliers.
3. **fe-split:** renal fraction x renal factor + hepatic fraction x hepatic factor.
4. **1-compartment** oral or IV PK with patient weight scaling (IBW/ABW where relevant).
5. **Safety layer:** allergy cross-reactivity, condition rules (e.g. NSAID + CKD), organ flags, and a major-DDI list.
6. **Risk merge:** exposure risk x safety risk gives the overall Safe / Caution / High Risk label.
7. **Confidence** is computed from parameter provenance, missing labs, and a novel-compound flag.

The composition table is preferred for the active dose when it matches the named drug; otherwise the stated regimen dose is used, with a warning if the mismatch is more than 15%.

### Lab report auto-fill (OCR)

The Patient tab has an **Upload lab report (image / PDF)** option. The backend runs OCR (Tesseract) and regex extractors to pull age, sex, weight, height, creatinine/eGFR, ALT, AST, bilirubin and albumin, then fills the form. Extracted values are always shown for human review, because OCR can misread numbers or units (for example g/L vs g/dL).

## Inputs

### Patient information

| Category | Information |
| --- | --- |
| Demographics | Age, sex, weight, height (BMI is calculated) |
| Kidney function | Serum creatinine or eGFR |
| Liver function | ALT, AST, bilirubin, albumin |
| Existing conditions | Diabetes, hypertension, heart disease, kidney or liver disease, pregnancy |
| Current medicines | Name, dose, frequency |
| Allergies | Known drug allergies |
| Lifestyle | Smoking and alcohol use |
| Optional | Genetic data (CYP2D6, CYP2C19, CYP2C9) and ECG QTc |

### Drug information

- Drug name or SMILES string
- Composition (ingredient and strength), optionally pre-filled from a pack/label image
- Dose in mg, route (oral or IV), frequency, duration

## Technical stack

- **Frontend:** HTML, CSS and vanilla JavaScript, served by nginx
- **Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic
- **Database / storage:** PostgreSQL with SQLAlchemy and Alembic migrations
- **OCR and documents:** Tesseract (pytesseract), Pillow, pypdf
- **Molecular properties:** RDKit (optional; not installed in the default image, molecular properties are limited without it)
- **PK modelling:** In-house Python implementation (see "Model details")
- **Reports:** Server-side PDF generation
- **Security:** API-key auth on all patient-data routes, rate limiting, audit logging
- **Deployment:** Docker Compose locally; `[hosting platform, if deployed]`

## AI/ML model and framework details

- **What it calculates:** Individualised concentration-time profiles, exposure metrics (Cmax, AUC, half-life, accumulation), and a merged risk category with confidence.
- **Approach:** A mechanistic, rule-based pharmacokinetic engine (1-compartment oral/IV model, with a two-compartment module in the codebase) with patient-specific clearance adjustment. It is **not** a trained machine-learning model. Drug-interaction and contraindication checks are rule-based.
- **Lab-report extraction:** Tesseract OCR plus regex-based field extraction (pretrained OCR engine, no custom training).
- **Data:** Drug parameters come from a curated in-repo knowledge base. `[Add sources and references for the parameters, with attribution and licence notes.]`
- **Validation:** Unit tests for PK math, simulation, and validation anchors are in `tests/`. `[Describe which reference drugs or published values were used as anchors, and the results.]`
- **Limitations and uncertainty:** Drugs not in the knowledge base use default parameters and are flagged as lower confidence. Missing labs reduce the confidence score. Outputs are indicative only.

## Architecture

**Architecture diagram (PDF/PPT):** `[Add link, e.g. architecture/architecture-diagram.pdf]`

Components: browser frontend, nginx (static files and reverse proxy), FastAPI service (patients, drugs, simulations, lab-report parsing), PK and safety engine, PostgreSQL, Tesseract OCR, PDF report generator.

## Prototype walkthrough video

**Video (15-20 minutes, unlisted YouTube):** `[Add link]`

Suggested walkthrough: problem and use case, architecture and stack, modelling approach, live demo with example inputs and outputs, what is implemented and what is not, limitations, and future work.

## Project presentation

**Presentation (PDF/PPT):** `[Add link, e.g. presentation/project-presentation.pdf]`

## Quick start (Docker)

```bash
cp .env.example .env
# fill in SECRET_KEY and API_KEYS (use long random values)

docker compose up --build
```

- **UI:** http://localhost:8080
- **Health:** http://localhost:8080/api/v1/health

Generate a key with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Send it as the header `X-API-Key: <key>`. In the browser, set it once from the console:

```js
localStorage.setItem('DT_API_KEY', 'your-key');
```

### Main API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/simulations/run?persist=true` | Run a simulation, optionally save it |
| GET | `/api/v1/simulations/{id}` | Full stored report (JSON) |
| GET | `/api/v1/simulations/{id}/pdf` | Download the PDF report |
| POST | `/api/v1/simulations/run/pdf` | Run and return a PDF in one call |
| POST | `/api/v1/patients` | Create a patient profile |
| POST | `/api/v1/patients/parse-report` | Upload a lab report and extract fields |
| POST | `/api/v1/drugs/lookup` | Molecular properties and basic knowledge |
| GET | `/api/v1/health` | Liveness and DB readiness |

### Tests

```bash
docker compose exec api pytest -q
```

## Outcome and current status

- **What currently works:** Patient and drug input, composition table, simulation with PK curves and risk categories, interaction and contraindication checks, PDF report, lab-report OCR auto-fill, Dockerised deployment.
- **What was evaluated:** `[Describe tests, reference-drug checks, and example runs.]`
- **Results / outcome:** `[Add observed results. Avoid unsupported accuracy or impact claims.]`
- **Known limitations:** Parameter coverage is limited to the knowledge base. OCR can misread values. No clinical validation has been done. RDKit is optional and not in the default image.
- **Next steps:** Wider drug coverage, PBPK extension, stronger validation against published data, per-user authentication.

## Security notes

- All patient-data routes require `X-API-Key`; health endpoints stay public.
- Production startup refuses a weak `SECRET_KEY`, empty `API_KEYS`, wildcard CORS, a non-Postgres database, and `ALLOW_DEMO_FALLBACK=true`.
- Demo mode is off by default, so an API failure never invents clinical-looking numbers.
- Rate limiting on patients, drugs, simulations, and uploads; audit events on patient and simulation actions.
- **Do not upload real patient reports to any public deployment.** Use dummy data only.

## Open-source licence

This project is licensed under the **Apache License 2.0**. See the [`LICENSE`](LICENSE) file.

## Repository structure

```text
Tally-Twin/
├── README.md
├── LICENSE
├── app/              # FastAPI backend (api, core, db, models, schemas, services, utils)
├── alembic/          # Database migrations
├── frontend/         # Web UI
├── deploy/           # nginx config
├── tests/            # Unit tests
├── docs/             # Integration notes
├── architecture/     # Architecture diagram (PDF/PPT)
├── presentation/     # Project presentation (PDF/PPT)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Safety note

This project is for research and development. Its outputs must not be treated as medical advice or used on their own to choose, change, or stop a medicine or dose. Drug-response predictions can be wrong, particularly when patient information is incomplete or evidence is limited. Any clinical use would require appropriate validation, clinical oversight, and safeguards. A confidence score alone does not prove that a prediction is safe or accurate.
