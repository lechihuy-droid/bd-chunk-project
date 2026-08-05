"""initial version governance schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-02
"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TYPE release_status AS ENUM ('DRAFT','PUBLISHED');
    CREATE TYPE environment_name AS ENUM ('DEV','PROD');
    CREATE TYPE run_status AS ENUM ('CREATED','MANIFEST_FROZEN','RUNNING','SUCCEEDED','FAILED','FAILED_PRECONDITION','CANCELLED');
    CREATE TYPE component_kind AS ENUM ('PROMPT','AGENT','TOOL','MODEL');
    CREATE TYPE origin_type AS ENUM ('AI_GENERATED','HUMAN_EDITED','IMPORTED');

    CREATE FUNCTION trg_block_write() RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION '% is immutable (%)', TG_TABLE_NAME, TG_OP USING ERRCODE = 'VG409';
    END $$ LANGUAGE plpgsql;

    CREATE TABLE workflow_release (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), workflow_id text NOT NULL,
      release_version text NOT NULL, status release_status NOT NULL DEFAULT 'DRAFT',
      git_repo text NOT NULL, git_ref text NOT NULL, git_commit char(40), entrypoint text NOT NULL,
      state_schema_version text NOT NULL, bindings jsonb NOT NULL, runtime_adapter_id text NOT NULL,
      model_profile text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), created_by text NOT NULL,
      published_at timestamptz, published_by text,
      CONSTRAINT uq_release UNIQUE (workflow_id, release_version),
      CONSTRAINT ck_published_complete CHECK (status = 'DRAFT' OR (git_commit IS NOT NULL AND published_at IS NOT NULL))
    );
    CREATE TABLE environment_mapping (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), environment environment_name NOT NULL,
      workflow_id text NOT NULL, workflow_release_id uuid NOT NULL REFERENCES workflow_release(id),
      updated_at timestamptz NOT NULL DEFAULT now(), updated_by text NOT NULL,
      CONSTRAINT uq_env UNIQUE (environment, workflow_id)
    );
    CREATE TABLE environment_mapping_audit (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), environment environment_name NOT NULL,
      workflow_id text NOT NULL, from_release_id uuid REFERENCES workflow_release(id),
      to_release_id uuid NOT NULL REFERENCES workflow_release(id), actor text NOT NULL, reason text,
      at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE execution_run (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_key text NOT NULL, workflow_id text NOT NULL,
      workflow_release_id uuid REFERENCES workflow_release(id), output_business_key text NOT NULL,
      output_artifact_type text NOT NULL DEFAULT 'API_BASIC_DESIGN', environment environment_name,
      execution_mode text NOT NULL DEFAULT 'ENVIRONMENT', status run_status NOT NULL DEFAULT 'CREATED',
      correlation_id uuid NOT NULL UNIQUE, runtime_provider text, runtime_run_id text, runtime_thread_id text,
      trace_provider text, trace_id text, error_code text, error_message text,
      created_at timestamptz NOT NULL DEFAULT now(), started_at timestamptz, completed_at timestamptz,
      CONSTRAINT ck_release_required CHECK (status IN ('CREATED','FAILED_PRECONDITION') OR workflow_release_id IS NOT NULL)
    );
    CREATE INDEX ix_run_project ON execution_run (project_key, created_at DESC);
    CREATE TABLE run_manifest (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), run_id uuid NOT NULL UNIQUE REFERENCES execution_run(id),
      workflow_release_id uuid NOT NULL REFERENCES workflow_release(id), git_repo text NOT NULL,
      git_commit char(40) NOT NULL, model_profile text NOT NULL, runtime_adapter_id text NOT NULL,
      environment environment_name, input_source_ref text NOT NULL, input_hash char(71) NOT NULL,
      manifest_hash char(71) NOT NULL, frozen_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT ck_input_hash CHECK (input_hash ~ '^sha256:[0-9a-f]{64}$')
    );
    CREATE TABLE run_component (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), manifest_id uuid NOT NULL REFERENCES run_manifest(id),
      kind component_kind NOT NULL, ref text NOT NULL, exact_version text NOT NULL,
      extra jsonb NOT NULL DEFAULT '{}'::jsonb,
      CONSTRAINT uq_component UNIQUE (manifest_id, kind, ref),
      CONSTRAINT ck_no_alias CHECK (lower(exact_version) NOT IN ('production','prod','latest','staging','champion','current')),
      CONSTRAINT ck_prompt_numeric CHECK (kind <> 'PROMPT' OR exact_version ~ '^[0-9]+$')
    );
    CREATE TABLE artifact (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_key text NOT NULL, artifact_type text NOT NULL,
      business_key text NOT NULL, display_name text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT uq_artifact UNIQUE (project_key, artifact_type, business_key)
    );
    CREATE TABLE artifact_revision (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), artifact_id uuid NOT NULL REFERENCES artifact(id),
      revision_no int NOT NULL, origin origin_type NOT NULL, source_run_id uuid REFERENCES execution_run(id),
      parent_revision_id uuid REFERENCES artifact_revision(id), content_hash char(71) NOT NULL,
      storage_uri text NOT NULL, mime_type text NOT NULL, size_bytes bigint NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(), created_by text NOT NULL,
      CONSTRAINT uq_revision UNIQUE (artifact_id, revision_no),
      CONSTRAINT ck_content_hash CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
      CONSTRAINT ck_provenance CHECK (
        (origin = 'AI_GENERATED' AND source_run_id IS NOT NULL) OR
        (origin = 'HUMAN_EDITED' AND parent_revision_id IS NOT NULL) OR
        (origin = 'IMPORTED' AND source_run_id IS NULL))
    );
    CREATE TABLE approved_baseline (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), artifact_id uuid NOT NULL REFERENCES artifact(id),
      scope text NOT NULL DEFAULT 'default', artifact_revision_id uuid NOT NULL REFERENCES artifact_revision(id),
      approved_by text NOT NULL, approved_at timestamptz NOT NULL DEFAULT now(),
      superseded_baseline_id uuid REFERENCES approved_baseline(id), active boolean NOT NULL DEFAULT true
    );
    CREATE UNIQUE INDEX uq_baseline_active ON approved_baseline (artifact_id, scope) WHERE active;
    CREATE TABLE runtime_callback (
      correlation_id uuid PRIMARY KEY REFERENCES execution_run(correlation_id),
      received_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz, response_body jsonb
    );

    CREATE FUNCTION trg_release_immutable() RETURNS trigger AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN
        IF OLD.status = 'PUBLISHED' THEN RAISE EXCEPTION 'workflow_release % is PUBLISHED and immutable', OLD.id USING ERRCODE = 'VG409'; END IF;
        RETURN OLD;
      END IF;
      IF OLD.status = 'PUBLISHED' THEN RAISE EXCEPTION 'workflow_release % is PUBLISHED and immutable', OLD.id USING ERRCODE = 'VG409'; END IF;
      IF NEW.workflow_id IS DISTINCT FROM OLD.workflow_id OR NEW.release_version IS DISTINCT FROM OLD.release_version
         OR NEW.git_repo IS DISTINCT FROM OLD.git_repo OR NEW.entrypoint IS DISTINCT FROM OLD.entrypoint
         OR NEW.state_schema_version IS DISTINCT FROM OLD.state_schema_version OR NEW.bindings IS DISTINCT FROM OLD.bindings
         OR NEW.runtime_adapter_id IS DISTINCT FROM OLD.runtime_adapter_id OR NEW.model_profile IS DISTINCT FROM OLD.model_profile THEN
        RAISE EXCEPTION 'workflow_release definition columns are not updatable' USING ERRCODE = 'VG409';
      END IF;
      RETURN NEW;
    END $$ LANGUAGE plpgsql;
    CREATE FUNCTION trg_baseline_pointer_only() RETURNS trigger AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'approved_baseline % cannot be deleted', OLD.id USING ERRCODE = 'VG409'; END IF;
      IF NEW.artifact_id IS DISTINCT FROM OLD.artifact_id OR NEW.scope IS DISTINCT FROM OLD.scope
         OR NEW.artifact_revision_id IS DISTINCT FROM OLD.artifact_revision_id OR NEW.approved_by IS DISTINCT FROM OLD.approved_by
         OR NEW.approved_at IS DISTINCT FROM OLD.approved_at OR NEW.superseded_baseline_id IS DISTINCT FROM OLD.superseded_baseline_id THEN
        RAISE EXCEPTION 'approved_baseline: only the active flag is updatable' USING ERRCODE = 'VG409';
      END IF;
      IF NOT (OLD.active AND NOT NEW.active) THEN RAISE EXCEPTION 'approved_baseline.active may only go true -> false' USING ERRCODE = 'VG409'; END IF;
      RETURN NEW;
    END $$ LANGUAGE plpgsql;

    CREATE TRIGGER release_immutable BEFORE UPDATE OR DELETE ON workflow_release FOR EACH ROW EXECUTE FUNCTION trg_release_immutable();
    CREATE TRIGGER env_audit_append_only BEFORE UPDATE OR DELETE ON environment_mapping_audit FOR EACH ROW EXECUTE FUNCTION trg_block_write();
    CREATE TRIGGER manifest_immutable BEFORE UPDATE OR DELETE ON run_manifest FOR EACH ROW EXECUTE FUNCTION trg_block_write();
    CREATE TRIGGER component_immutable BEFORE UPDATE OR DELETE ON run_component FOR EACH ROW EXECUTE FUNCTION trg_block_write();
    CREATE TRIGGER revision_immutable BEFORE UPDATE OR DELETE ON artifact_revision FOR EACH ROW EXECUTE FUNCTION trg_block_write();
    CREATE TRIGGER baseline_pointer_only BEFORE UPDATE OR DELETE ON approved_baseline FOR EACH ROW EXECUTE FUNCTION trg_baseline_pointer_only();
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE runtime_callback;
    DROP TABLE approved_baseline;
    DROP TABLE artifact_revision;
    DROP TABLE artifact;
    DROP TABLE run_component;
    DROP TABLE run_manifest;
    DROP TABLE execution_run;
    DROP TABLE environment_mapping_audit;
    DROP TABLE environment_mapping;
    DROP TABLE workflow_release;
    DROP FUNCTION trg_baseline_pointer_only();
    DROP FUNCTION trg_release_immutable();
    DROP FUNCTION trg_block_write();
    DROP TYPE origin_type;
    DROP TYPE component_kind;
    DROP TYPE run_status;
    DROP TYPE environment_name;
    DROP TYPE release_status;
    """)
