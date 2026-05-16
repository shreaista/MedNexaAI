-- MedNexa: AI pipeline metadata (structures only — no inference tables populated yet)

CREATE SCHEMA IF NOT EXISTS ai;

CREATE TABLE IF NOT EXISTS ai.model_runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    UUID REFERENCES core.tenants (id) ON DELETE SET NULL,
    model_family VARCHAR(64) NOT NULL,
    correlation_id UUID,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    outcome      VARCHAR(16) DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS ix_model_runs_tenant ON ai.model_runs (tenant_id);

CREATE TABLE IF NOT EXISTS ai.prompt_traces (
    id          BIGSERIAL PRIMARY KEY,
    run_id      UUID REFERENCES ai.model_runs (id) ON DELETE CASCADE,
    step_label  VARCHAR(128) NOT NULL,
    blob_ref    VARCHAR(512),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_prompt_traces_run ON ai.prompt_traces (run_id);
