# Test Plan — Bootstrap Release

## API

| Case | Steps | Expected |
|------|--------|----------|
| Health OK | `GET /health` (no auth) | `200`; JSON `{"status":"ok","service":"mednexa-api"}` |
| OpenAPI present | Navigate to `/docs` | Interactive Swagger loads |

## Frontend

| Case | Steps | Expected |
|------|--------|----------|
| Home renders | `npm run dev` → open `/` | Page loads without console errors |
| Styles active | Inspect heading / button | Tailwind utility classes applied |

## Database

| Case | Steps | Expected |
|------|--------|----------|
| Postgres up | `docker compose up -d`; `docker compose ps` | `healthy` status |
| DDL applies | Apply `database/ddl/*.sql` in order | No errors; schemas `core`, `clinical`, `billing`, `ai` exist |
| Seed idempotent | Run `database/seed/001_seed_demo_data.sql` twice | Second run does not violate constraints |

## Future automation

Add CI jobs for pytest (API), Playwright or Jest/RTL smoke (web), and `sqlflint`/`sqlparser` sanity on DDL changes.
