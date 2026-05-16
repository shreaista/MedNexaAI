# MedNexa API (FastAPI)

Backend for **MedNexa AI**, designed to run against **Azure Database for PostgreSQL Flexible Server** with existing tables in the **`public`** schema.

## Prerequisites

- Python **3.11+**
- Network access to your Azure PostgreSQL instance
- `DATABASE_URL` with appropriate SSL settings (typically `sslmode=require`)

## Configure environment

From `apps/api`:

1. Copy the example env file:

   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` and set **`DATABASE_URL`** to your Azure connection string, for example:

   ```env
   DATABASE_URL=postgresql://USER:PASSWORD@HOST.postgres.database.azure.com:5432/DBNAME?sslmode=require
   ```

The application loads `.env` automatically via `python-dotenv` and `pydantic-settings`.

## Install dependencies

```powershell
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the server

From `apps/api` (virtual environment activated):

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Smoke test

In another terminal:

```powershell
curl http://127.0.0.1:8000/health
```

Expected JSON:

```json
{"status":"ok","service":"mednexa-api"}
```

Interactive docs: **http://127.0.0.1:8000/docs**

## Notes

- **ORM models** assume snake_case columns as mapped in `app/models/`. If your Azure schema differs (extra columns, renamed fields, or different defaults), adjust the models—**do not** run `create_all` against production.
- Database errors return **HTTP 500** with a truncated driver message for troubleshooting.
- Missing entities return **HTTP 404** with a short `detail` string.
