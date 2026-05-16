-- MedNexa: core tenancy, identity, and audit primitives
-- Target: PostgreSQL 16+

CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.tenants (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug         VARCHAR(128) NOT NULL UNIQUE,
    display_name VARCHAR(256) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES core.tenants (id) ON DELETE CASCADE,
    email       VARCHAR(320) NOT NULL,
    role        VARCHAR(64) NOT NULL DEFAULT 'member',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);

CREATE INDEX IF NOT EXISTS ix_users_tenant ON core.users (tenant_id);

CREATE TABLE IF NOT EXISTS core.audit_events (
    id          BIGSERIAL PRIMARY KEY,
    tenant_id   UUID REFERENCES core.tenants (id) ON DELETE SET NULL,
    actor_id    UUID REFERENCES core.users (id) ON DELETE SET NULL,
    action      VARCHAR(128) NOT NULL,
    payload     JSONB NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_audit_tenant_time ON core.audit_events (tenant_id, occurred_at DESC);
