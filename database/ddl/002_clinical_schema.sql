-- MedNexa: clinical artifacts (minimal placeholders for phased delivery)

CREATE SCHEMA IF NOT EXISTS clinical;

CREATE TABLE IF NOT EXISTS clinical.patients (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    external_id VARCHAR(128),
    birth_date  DATE,
    gender      VARCHAR(32),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, external_id)
);

CREATE INDEX IF NOT EXISTS ix_patients_tenant ON clinical.patients (tenant_id);

CREATE TABLE IF NOT EXISTS clinical.encounters (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    patient_id  UUID NOT NULL REFERENCES clinical.patients (id) ON DELETE CASCADE,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at    TIMESTAMPTZ,
    chief_complaint VARCHAR(512)
);

CREATE INDEX IF NOT EXISTS ix_encounters_patient ON clinical.encounters (patient_id);
