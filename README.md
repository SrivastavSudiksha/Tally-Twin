# Digital Twin — Individualized PK Risk Estimator

**Research / educational tool only. Not a medical device.**  
Outputs are individualized PK-based risk estimates and must not replace clinical judgement.

## Vision (for clinicians)

Like a digital twin of the patient:

1. Enter **patient health data** (age, sex, weight, kidney/liver labs, conditions, allergies, current medicines, optional genetics/QTc).
2. Enter **drug** (name or SMILES) + **composition** (ingredient strengths) + regimen (dose, route, frequency, duration).
3. The engine predicts:
   - Patient-adjusted concentration–time curve vs average adult  
   - Cmax, AUC, half-life, accumulation  
   - Exposure risk (Safe / Caution / High Risk)  
   - Organ flags (kidney, liver, heart/QT)  
   - Allergy / condition contraindications  
   - Rule-based drug–drug interactions  
   - Dose assessment and explainability drivers  
4. **Download a PDF report** for the chart or MDT discussion.

## Quick start (Docker)

```bash
cp .env.example .env
# edit SECRET_KEY and API_KEYS for anything beyond local demo

docker compose up --build
```

- **UI:** http://localhost:8080  
- **API docs:** http://localhost:8000/docs  
- **Health:** http://localhost:8000/api/v1/health  

Default API key (development only):  
`f1c11af3ceb90166b6ea2c5fe83e79cc116efd6b1c5de0f8c0e45ea6c4ecdecb`  
Send as header: `X-API-Key: <key>`

## Main API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/simulations/run?persist=true` | Run simulation, optionally save |
| GET | `/api/v1/simulations/{id}` | Full stored report (JSON) |
| GET | `/api/v1/simulations/{id}/pdf` | **Download clinician PDF** |
| POST | `/api/v1/simulations/run/pdf` | Run + return PDF in one call |
| POST | `/api/v1/patients` | Create patient profile |
| POST | `/api/v1/drugs/lookup` | Molecular properties + basic knowledge |
| GET | `/api/v1/health` | Liveness + DB readiness |

## How the engine works (clinician summary)

1. **Drug parameters** from knowledge base (CL, Vd, F, ka, fe, therapeutic window) or safe defaults if unknown.  
2. **Patient clearance factor** from eGFR/CrCl (CKD-EPI 2021 + Cockcroft–Gault), liver capacity / Child–Pugh-style score, age, lifestyle, and DDI multipliers.  
3. **fe-split:** renal fraction × renal factor + hepatic fraction × hepatic factor.  
4. **1-compartment** oral or IV PK with patient weight scaling (IBW/ABW when relevant).  
5. **Safety layer:** allergy cross-reactivity, condition rules (e.g. NSAID + CKD), organ flags, major DDI list.  
6. **Risk merge:** exposure risk × safety risk → overall Safe / Caution / High Risk.  
7. **Confidence** from parameter provenance, missing labs, novel compound flag.

Composition table is preferred for active dose when it matches the named drug; otherwise stated regimen dose is used (with a warning if mismatch >15%).

## Production checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Strong `SECRET_KEY` (not the default)
- [ ] `API_KEYS` non-empty; disable empty-key access
- [ ] `DATABASE_URL` must be PostgreSQL
- [ ] `CORS_ORIGINS` explicit (no `*`)
- [ ] `ALLOW_DEMO_FALLBACK=false`
- [ ] `ENABLE_DOCS=false` if you do not want public Swagger
- [ ] TLS termination (reverse proxy / load balancer)
- [ ] Back up `pgdata` volume
- [ ] Monitor `/api/v1/health` and audit log lines (`app.audit`)

## Local development without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:////tmp/digital_twin.db
export API_KEYS=dev-key
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Serve `frontend/` with any static server and set:

```js
window.DT_API_URL = 'http://localhost:8000';
window.DT_API_KEY = 'dev-key';
```

## Tests

```bash
pytest tests/ -q
```


## Security (loopholes closed)

- **All PHI routes require `X-API-Key`**: patients, simulations (run/list/get/pdf), drugs lookup & image upload.
- **Health/ready** remain public for load balancers.
- **Production startup refuses**: weak SECRET_KEY, empty API_KEYS, CORS `*`, Postgres missing, ALLOW_DEMO_FALLBACK=true.
- **Frontend**: no hardcoded API key. Set via:
  ```js
  localStorage.setItem('DT_API_KEY', 'your-key');
  // optional demo only (never clinical):
  localStorage.setItem('DT_ALLOW_DEMO', 'true');
  ```
- **Demo mode is OFF by default** — API failure does not silently invent clinical-looking numbers.
- **Rate limiting** on patients, drugs, simulations (stricter on image upload).
- **Audit events** on patient create/delete and simulation run/read/pdf.
- **Image upload**: type + size + resolution limits.

Still recommended before hospital use: Redis rate limit, per-org scoping (IDOR beyond shared API key), TLS, key rotation, JWT/user auth.

## Disclaimer

This product is an **in-silico individualized PK risk estimator**.  
It is **not** a medical device, does **not** provide treatment recommendations as clinical standard of care, and must always be interpreted by a qualified clinician with full access to the patient record, guidelines, and TDM where appropriate.
