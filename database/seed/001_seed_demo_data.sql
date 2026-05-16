-- Demo seed for local environments only (adjust UUIDs when replaying migrations)

BEGIN;

INSERT INTO core.tenants (id, slug, display_name)
VALUES (
    '11111111-1111-1111-1111-111111111111'::uuid,
    'demo-org',
    'Demo Organization'
) ON CONFLICT (slug) DO NOTHING;

INSERT INTO core.users (id, tenant_id, email, role)
VALUES (
    '22222222-2222-2222-2222-222222222222'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    'demo@mednexa.local',
    'admin'
) ON CONFLICT (tenant_id, email) DO NOTHING;

INSERT INTO core.facilities (id, tenant_id, code, name, active)
VALUES (
    '44444444-4444-4444-4444-444444444444'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    'DEMO-FAC-1',
    'Demo Medical Center',
    TRUE
) ON CONFLICT (tenant_id, code) DO NOTHING;

INSERT INTO clinical.patients (id, tenant_id, external_id, birth_date, gender, facility_id, first_name, last_name, active)
VALUES (
    '33333333-3333-3333-3333-333333333333'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    'DEMO-P1',
    '1984-06-01',
    'unspecified',
    '44444444-4444-4444-4444-444444444444'::uuid,
    'Demo',
    'Patient',
    TRUE
) ON CONFLICT (tenant_id, external_id) DO NOTHING;

UPDATE clinical.patients
SET facility_id = '44444444-4444-4444-4444-444444444444'::uuid,
    first_name = 'Demo',
    last_name = 'Patient',
    gender = COALESCE(gender, 'unspecified'),
    active = TRUE
WHERE id = '33333333-3333-3333-3333-333333333333'::uuid;

COMMIT;
