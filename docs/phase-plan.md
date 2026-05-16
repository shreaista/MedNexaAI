# Phase Plan

## Phase 0 — Bootstrap (complete)

Monorepo layout, Postgres via Docker Compose, FastAPI skeleton with `/health`, Next.js + Tailwind + shadcn-style UI stubs, DDL and demo seed scaffolding.

## Phase 1 — Data access

Introduce SQLAlchemy 2 + async sessions in `app/db`, configuration via `app/core`, and migrations (e.g., Alembic) driven from DDL baselines.

## Phase 2 — AuthN / AuthZ

Tenant-scoped JWT or external IdP integration; middleware and dependency wrappers in FastAPI routes; guarded web session or BFF proxy pattern as needed.

## Phase 3 — Core features

Iterate by vertical slice per router: patients, encounters, billing batches, aligning Pydantic schemas with database constraints.

## Phase 4 — AI readiness

Implement `app/ai` adapters (batch + streaming interfaces), tracing into `ai.model_runs` / `ai.prompt_traces`, and policy controls (PII redaction, consent flags) before enabling production inference.
