# Lab Report Auto-Fill — Integration Guide

Adds **Upload lab report (image/PDF)** on the Patient tab. OCR + regex extract age, sex, weight, height, creatinine/eGFR, ALT, AST, bilirubin, albumin and fill the form.

PDF download after prediction was already present in the project (`/api/v1/simulations/{id}/pdf`).

---

## Files in this package

```
lab_report_autofill/
├── app/
│   ├── schemas/lab_report.py          # response models
│   ├── services/lab_report_parser.py  # OCR + regex extractors
│   └── api/v1/patients_parse_report.py  # POST /patients/parse-report
├── frontend/
│   ├── index_lab_upload_snippet.html  # HTML for Patient tab
│   ├── app_js_inline_snippet.js       # paste into app.js
│   └── lab_report_patch.js            # optional standalone script
└── docs/
    └── INTEGRATION.md                 # this file
```

---

## Backend install steps

### 1. Copy files into your repo

From project root `tally_twin/`:

```bash
# Schemas
cp lab_report_autofill/app/schemas/lab_report.py app/schemas/

# Service
cp lab_report_autofill/app/services/lab_report_parser.py app/services/

# API route module
cp lab_report_autofill/app/api/v1/patients_parse_report.py app/api/v1/
```

### 2. Register the router

**Option A** — include the new router in `app/api/v1/router.py`:

```python
from app.api.v1 import simulations, drugs, health, patients
from app.api.v1 import patients_parse_report  # NEW

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(patients.router)
api_router.include_router(patients_parse_report.router)  # NEW
api_router.include_router(simulations.router)
api_router.include_router(drugs.router)
```

**Option B** — merge the endpoint into existing `app/api/v1/patients.py` by copying the `parse_lab_report` function and imports into that file (same prefix `/patients`).

### 3. Optional system deps (Docker)

For better OCR inside the API container, extend `Dockerfile` runtime stage:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxrender1 libxext6 libsm6 curl \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
```

Optional Python packages (add to `requirements.txt` if you want PDF text / raster):

```
pytesseract>=0.3.10
# pypdf>=4.0.0
# pdf2image>=1.17.0   # also needs poppler-utils apt package
```

Pillow is already in requirements. Without Tesseract, the endpoint still responds safely with `source: none` and a clear message.

### 4. Rebuild API

```bash
docker compose up --build -d api
# or full stack:
docker compose up --build -d
```

Test:

```bash
curl -s -X POST http://localhost:8000/api/v1/patients/parse-report \
  -H "X-API-Key: dev-local-key-change-me" \
  -F "file=@/path/to/sample_lab.png"
```

---

## Frontend install steps

### 1. HTML — Patient tab upload UI

Open `frontend/index.html`. Inside `#tab-patient`, after the **Demographics** fieldset (or at the top of the patient panel), paste the contents of:

`frontend/index_lab_upload_snippet.html`

### 2. JS — wire the upload

**Preferred:** paste `frontend/app_js_inline_snippet.js` into `frontend/app.js` inside the main IIFE, after `COMP_OCR_URL` / API helpers and before the submit handler.

**Alternative:** add script tag before closing `</body>`:

```html
<script src="lab_report_patch.js"></script>
```

and copy `lab_report_patch.js` into `frontend/`.

### 3. Permissions + restart web

```bash
chmod -R a+rX frontend deploy
docker compose restart web
```

### 4. Browser

```js
localStorage.setItem('DT_API_KEY', 'dev-local-key-change-me');
location.reload();
```

1. Open http://localhost:8080  
2. Patient tab → **Upload lab report**  
3. Values that OCR found appear in the form  
4. Review → Drug tab → Run simulation  
5. **Download PDF report** on the report screen  

---

## PDF download (already in project)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/simulations/run?persist=true` | Run + save → returns `simulation_id` |
| `GET /api/v1/simulations/{id}/pdf` | Download clinician PDF |
| `POST /api/v1/simulations/run/pdf` | Run + PDF in one call |

Frontend button uses the stored `simulation_id` after a successful API run.

---

## Safety notes

- OCR misreads are common. Always show extracted values for **human review**.
- Do not treat auto-filled numbers as verified clinical data.
- Rate limit is tighter on this endpoint (15/min default in the route).
- PHI: API key required; audit event `lab_report_parse` is logged without storing the file.

---

## Quick checklist

- [ ] `lab_report.py` schema copied  
- [ ] `lab_report_parser.py` service copied  
- [ ] Route registered (`patients_parse_report` or merged into `patients.py`)  
- [ ] HTML snippet on Patient tab  
- [ ] JS snippet in `app.js` (or standalone script)  
- [ ] `chmod -R a+rX frontend` + restart web  
- [ ] API key in localStorage  
- [ ] Optional: `tesseract-ocr` in Docker image  
