-- Phase 1: facilities, enriched patients, visits, documentation, diagnoses/procedures,
-- charges, billing queue, claim readiness (PostgreSQL 16+)

CREATE TABLE IF NOT EXISTS core.facilities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    code        VARCHAR(64) NOT NULL,
    name        VARCHAR(256) NOT NULL,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_facilities_tenant ON core.facilities (tenant_id);

ALTER TABLE clinical.patients ADD COLUMN IF NOT EXISTS gender VARCHAR(32);
ALTER TABLE clinical.patients ADD COLUMN IF NOT EXISTS facility_id UUID REFERENCES core.facilities (id);
ALTER TABLE clinical.patients ADD COLUMN IF NOT EXISTS first_name VARCHAR(128);
ALTER TABLE clinical.patients ADD COLUMN IF NOT EXISTS last_name VARCHAR(128);
ALTER TABLE clinical.patients ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS ix_patients_facility ON clinical.patients (facility_id);

CREATE TABLE IF NOT EXISTS clinical.visits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    facility_id     UUID NOT NULL REFERENCES core.facilities (id) ON DELETE RESTRICT,
    patient_id      UUID NOT NULL REFERENCES clinical.patients (id) ON DELETE CASCADE,
    provider_id     UUID NOT NULL REFERENCES core.users (id) ON DELETE RESTRICT,
    visit_type      VARCHAR(64) NOT NULL,
    specialty       VARCHAR(128) NOT NULL,
    chief_complaint TEXT,
    status          VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_visits_tenant ON clinical.visits (tenant_id);
CREATE INDEX IF NOT EXISTS ix_visits_facility ON clinical.visits (facility_id);
CREATE INDEX IF NOT EXISTS ix_visits_patient ON clinical.visits (patient_id);

CREATE TABLE IF NOT EXISTS clinical.visit_notes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    visit_id    UUID NOT NULL REFERENCES clinical.visits (id) ON DELETE CASCADE,
    subjective  TEXT,
    objective   TEXT,
    assessment  TEXT,
    plan        TEXT,
    full_note   TEXT NOT NULL DEFAULT '',
    ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    note_status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    signed_at   TIMESTAMPTZ,
    signed_by   UUID REFERENCES core.users (id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_visit_notes_visit ON clinical.visit_notes (visit_id);

CREATE TABLE IF NOT EXISTS clinical.visit_diagnoses (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visit_id    UUID NOT NULL REFERENCES clinical.visits (id) ON DELETE CASCADE,
    icd10_code  VARCHAR(16) NOT NULL,
    description VARCHAR(512) NOT NULL DEFAULT '',
    is_primary  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_visit_diagnoses_visit ON clinical.visit_diagnoses (visit_id);

CREATE TABLE IF NOT EXISTS clinical.visit_procedures (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visit_id    UUID NOT NULL REFERENCES clinical.visits (id) ON DELETE CASCADE,
    cpt_code    VARCHAR(16) NOT NULL,
    description VARCHAR(512) NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_visit_procedures_visit ON clinical.visit_procedures (visit_id);

CREATE TABLE IF NOT EXISTS billing.charges (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    visit_id      UUID NOT NULL REFERENCES clinical.visits (id) ON DELETE CASCADE,
    facility_id   UUID NOT NULL REFERENCES core.facilities (id) ON DELETE RESTRICT,
    patient_id    UUID NOT NULL REFERENCES clinical.patients (id) ON DELETE CASCADE,
    diagnosis_id  UUID REFERENCES clinical.visit_diagnoses (id) ON DELETE SET NULL,
    procedure_id  UUID REFERENCES clinical.visit_procedures (id) ON DELETE SET NULL,
    amount_cents  BIGINT NOT NULL DEFAULT 0,
    charge_status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_charges_visit ON billing.charges (visit_id);
CREATE INDEX IF NOT EXISTS ix_charges_tenant ON billing.charges (tenant_id);

CREATE TABLE IF NOT EXISTS billing.billing_queue (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    charge_id     UUID NOT NULL REFERENCES billing.charges (id) ON DELETE CASCADE,
    queue_status  VARCHAR(32) NOT NULL DEFAULT 'NEW',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (charge_id)
);

CREATE INDEX IF NOT EXISTS ix_billing_queue_tenant ON billing.billing_queue (tenant_id);

CREATE TABLE IF NOT EXISTS billing.claim_readiness (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    charge_id        UUID NOT NULL REFERENCES billing.charges (id) ON DELETE CASCADE,
    readiness_score  NUMERIC(5, 2) NOT NULL DEFAULT 0,
    status           VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (charge_id)
);

CREATE INDEX IF NOT EXISTS ix_claim_readiness_charge ON billing.claim_readiness (charge_id);
