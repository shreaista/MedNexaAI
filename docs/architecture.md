# MedNexa AI — Architecture

## Overview

The **mednexa-ai** monorepo separates user-facing surfaces, HTTP APIs, and relational data. The layout favors clear boundaries today while leaving room for event-driven workflows, background jobs, and model hosting without refactoring core packages.

```
┌────────────────┐       ┌─────────────────┐       ┌──────────────────┐
│ Next.js web    │  HTTP │ FastAPI (`api`) │  SQL   │ PostgreSQL       │
│ (apps/web)     ├──────►│ (apps/api)       ├───────►│ (docker-compose) │
└────────────────┘       └────────┬────────┘       └──────────────────┘
                                  │
                          reserved: AI services
                                  (apps/api/app/ai)
```

## Applications

### Web (`apps/web`)

- Next.js App Router with TypeScript and Tailwind CSS.
- Presentation components mirror **shadcn/ui** ergonomics (`components/ui`) without requiring the CLI scaffold in this bootstrap phase.

### API (`apps/api`)

- FastAPI application package under `app/`.
- **`routers`**: thin HTTP adapters.
- **`services`**: orchestration (to be populated per feature slice).
- **`models` / `schemas`**: persistence and API contracts respectively.
- **`db`**: future session/engine wiring.
- **`ai`**: reserved for embeddings, adapters, prompts, evaluation — intentionally empty beyond package markers.

### Data (`database`)

- DDL is split into numbered files by bounded context: core, clinical, billing, AI metadata.
- Seeds are environment-scoped demos; avoid shipping them unchanged to production tenants.

## Non-goals (bootstrap)

- No authentication issuer, SSO, or fine-grained RBAC enforcement yet.
- No message bus, cache, or object storage integration yet.
- No third-party inference providers configured in code.

These can be layered without breaking the proposed package boundaries.

## Configuration

- **Backend**: `.env.example` defines `DATABASE_URL` aligned with Docker Compose defaults.
- **Frontend**: `.env.example` documents the browser-facing API origin for future fetch calls.

## Deployment posture (intent)

Keep processes stateless beyond database connections; store secrets outside the repo; rotate database credentials per environment.
