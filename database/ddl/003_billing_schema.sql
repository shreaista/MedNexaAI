-- MedNexa: billing (claims, placeholders)

CREATE SCHEMA IF NOT EXISTS billing;

CREATE TABLE IF NOT EXISTS billing.claim_batches (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    status      VARCHAR(32) NOT NULL DEFAULT 'draft',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    submitted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_claim_batches_tenant ON billing.claim_batches (tenant_id);

CREATE TABLE IF NOT EXISTS billing.line_items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    batch_id    UUID REFERENCES billing.claim_batches (id) ON DELETE CASCADE,
    cpt_code    VARCHAR(16),
    amount_cents BIGINT NOT NULL DEFAULT 0,
    narrative   VARCHAR(1024)
);

CREATE INDEX IF NOT EXISTS ix_line_items_batch ON billing.line_items (batch_id);
