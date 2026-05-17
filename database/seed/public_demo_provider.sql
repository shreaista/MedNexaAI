-- Optional one-off DATA seed for `public` schema (not a DDL migration).
-- Run against PostgreSQL after core tables exist. Requires at least one `tenants` row.
-- Creates a user with users.full_name = 'Demo Provider' and a linked ACTIVE provider row
-- so GET /providers returns "Demo Provider" when joined on providers.user_id = users.user_id.

INSERT INTO users (
    user_id,
    tenant_id,
    email,
    full_name
)
SELECT
    '22222222-2222-2222-2222-222222222222'::uuid,
    t.tenant_id,
    'demo.provider.seed@mednexa.local',
    'Demo Provider'
FROM tenants AS t
ORDER BY t.created_at ASC
LIMIT 1
ON CONFLICT (user_id) DO UPDATE SET
    full_name = EXCLUDED.full_name;

INSERT INTO providers (
    provider_id,
    tenant_id,
    user_id,
    npi,
    specialty,
    provider_type,
    status,
    full_name
)
SELECT
    '33333333-3333-3333-3333-333333333333'::uuid,
    u.tenant_id,
    u.user_id,
    NULL,
    'Internal Medicine',
    'MD',
    'ACTIVE',
    'Demo Provider'
FROM users AS u
WHERE u.user_id = '22222222-2222-2222-2222-222222222222'::uuid
ON CONFLICT (provider_id) DO UPDATE SET
    user_id = EXCLUDED.user_id,
    status = EXCLUDED.status;
