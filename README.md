# mednexa-ai

Enterprise-oriented monorepo for **MedNexa**: FastAPI backend, Next.js frontend, PostgreSQL data plane, AI-ready seams without vendor lock-in yet.

## Repository layout

| Path | Role |
|------|------|
| `apps/api` | FastAPI HTTP service (`uvicorn app.main:app`) |
| `apps/web` | Next.js UI (React, TypeScript, Tailwind, shadcn-style components) |
| `database/ddl` | Postgres schema fragments (numeric order matters) |
| `database/seed` | Demonstration inserts for local workstations |
| `docs` | Architecture, phased delivery notes, bootstrap test matrix |

## Prerequisites

- **Python** ≥ 3.11 for the API (on Windows without `python` on `PATH`, use `py -3`)
- **Node.js** ≥ 20 and npm for the web app
- **Docker** Desktop (or Compose plugin) for PostgreSQL

## Quick start

### 1. Start PostgreSQL

```bash
docker compose up -d
```

PostgreSQL listens on **`localhost:5432`** using credentials mirrored in `apps/api/.env.example`.

### 2. Apply database objects (manual for now)

```bash
# Bash-compatible shells
docker exec -i mednexa-postgres psql -U mednexa -d mednexa < database/ddl/001_core_schema.sql
docker exec -i mednexa-postgres psql -U mednexa -d mednexa < database/ddl/002_clinical_schema.sql
docker exec -i mednexa-postgres psql -U mednexa -d mednexa < database/ddl/003_billing_schema.sql
docker exec -i mednexa-postgres psql -U mednexa -d mednexa < database/ddl/004_ai_schema.sql
docker exec -i mednexa-postgres psql -U mednexa -d mednexa < database/ddl/005_phase1_api.sql
docker exec -i mednexa-postgres psql -U mednexa -d mednexa < database/seed/001_seed_demo_data.sql
```

PowerShell alternative (run from repo root):

```powershell
Get-Content database/ddl/001_core_schema.sql | docker exec -i mednexa-postgres psql -U mednexa -d mednexa
Get-Content database/ddl/002_clinical_schema.sql | docker exec -i mednexa-postgres psql -U mednexa -d mednexa
Get-Content database/ddl/003_billing_schema.sql | docker exec -i mednexa-postgres psql -U mednexa -d mednexa
Get-Content database/ddl/004_ai_schema.sql | docker exec -i mednexa-postgres psql -U mednexa -d mednexa
Get-Content database/ddl/005_phase1_api.sql | docker exec -i mednexa-postgres psql -U mednexa -d mednexa
Get-Content database/seed/001_seed_demo_data.sql | docker exec -i mednexa-postgres psql -U mednexa -d mednexa
```

Alternatively, use any SQL client pointing at `localhost:5432` with database `mednexa`, user `mednexa`, password `mednexa_local_dev`.

### 3. Backend (FastAPI)

```bash
cd apps/api
py -3 -m venv .venv   # substitute `python3`/`python` on POSIX
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # PowerShell; use cp on Unix
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Smoke test:

```bash
curl http://127.0.0.1:8000/health
```

Expected payload:

```json
{"status":"ok","service":"mednexa-api"}
```

Interactive docs live at `/docs`.

### Backend — Phase 1 APIs (SQLAlchemy + Postgres)

Read endpoints accept an optional `tenant_id` query parameter. When omitted, the API defaults to the seeded demo tenant `11111111-1111-1111-1111-111111111111`.

Stable demo identifiers from `database/seed/001_seed_demo_data.sql`:

| Role | UUID |
|------|------|
| Demo tenant | `11111111-1111-1111-1111-111111111111` |
| Demo user (`public.users`) | `22222222-2222-2222-2222-222222222222` (used when signing notes explicitly) |
| Demo patient (`public.patients`) | `33333333-3333-3333-3333-333333333333` |
| Demo facility (`public.facilities`) | `44444444-4444-4444-4444-444444444444` |

Ensure `provider_id` in `POST /visits`/`POST …/notes` matches a row in **`public.providers`** for the same tenant — it is **not** the same as `users.user_id` unless your seed links them intentionally.

Example flow (bash):

```bash
curl "http://127.0.0.1:8000/facilities"
curl "http://127.0.0.1:8000/facilities/44444444-4444-4444-4444-444444444444/census"
curl "http://127.0.0.1:8000/patients/33333333-3333-3333-3333-333333333333"

VISIT_ID=$(curl -s -X POST "http://127.0.0.1:8000/visits" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"11111111-1111-1111-1111-111111111111","facility_id":"44444444-4444-4444-4444-444444444444","patient_id":"33333333-3333-3333-3333-333333333333","provider_id":"<REPLACE_WITH_providers.provider_id>","visit_type":"office","specialty":"internal_medicine","chief_complaint":"follow-up"}' \
  | jq -r '.id')

curl "http://127.0.0.1:8000/visits/$VISIT_ID"

NOTE_ID=$(curl -s -X POST "http://127.0.0.1:8000/visits/$VISIT_ID/notes" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"11111111-1111-1111-1111-111111111111","patient_id":"33333333-3333-3333-3333-333333333333","provider_id":"<REPLACE_WITH_providers.provider_id>","subjective":"feel well","objective":"vitals stable","assessment":"stable","plan":"recheck","full_note":"SOAP","ai_generated":false}' \
  | jq -r '.id')

# Sign with signing user UUID, OR use {"signer_provider_id":"<same provider_id>"} when providers.user_id is populated.
curl -X PUT "http://127.0.0.1:8000/notes/$NOTE_ID/sign" \
  -H "Content-Type: application/json" \
  -d '{"signed_by":"22222222-2222-2222-2222-222222222222"}'

curl -s -X POST "http://127.0.0.1:8000/visits/$VISIT_ID/diagnoses" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"11111111-1111-1111-1111-111111111111","icd10_code":"I10","description":"Essential hypertension","is_ai_suggested":false}'

curl -s -X POST "http://127.0.0.1:8000/visits/$VISIT_ID/procedures" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"11111111-1111-1111-1111-111111111111","cpt_code":"99213","description":"Office visit, level 3","units":"1"}'

curl -s -X POST "http://127.0.0.1:8000/visits/$VISIT_ID/charges" \
  -H "Content-Type: application/json" \
  -d '{}'

curl "http://127.0.0.1:8000/billing-queue"
```

Without `jq`, copy `id` fields from JSON responses manually. On Windows, `curl.exe` works the same way; `Invoke-RestMethod` is another option. **http://127.0.0.1:8000/docs** is usually the fastest way to exercise the full surface area with your locally generated UUIDs.

### 4. Frontend (Next.js)

```bash
cd apps/web
copy .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 .

### Phase 1 workflow test (UI)

1. Open **Dashboard**.
2. Open **Facilities** and pick a census for an active facility.
3. Choose **Open chart** next to any census row — this attaches `facilityId` to `/patients/...`.
4. On **Patient chart**, confirm payer, admission date, and facility attribution, then **Start new visit**.
5. Populate **Visit shell**, SOAP, ICD/CPT, and **Submit documentation & charge** (requires `NEXT_PUBLIC_PROVIDER_ID`; see `apps/web/.env.example`).
6. On **Billing queue**, confirm `GET /billing-queue` renders the newest row plus the transient **Charge captured** banner (`?charged=1` redirect).

Also keep Swagger (`/docs`) handy for diagnosing payload mismatches versus `apps/api/app/schemas`.

## Operational notes

- Set **`CORS_ALLOW_ORIGINS`** in `apps/api` (comma-separated) so browser-based Next.js callers at your staging domain can invoke the deployed API alongside local `localhost:3000` defaults.

- Keep secrets out of Git; populate `.env` / `.env.local` from `.env.example` files only.
- The `apps/api/app/ai` package is reserved for adapters, retrieval, orchestration — no third-party inference is wired in this scaffold.
- For production deployments, migrate from hand-run DDL toward a migration tool aligned with repository policy.

## License

Specify your organization’s license terms here.
