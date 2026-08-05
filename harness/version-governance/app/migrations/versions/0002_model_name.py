"""add pinned model name to workflow releases

Revision ID: 0002_model_name
Revises: 0001_initial
Create Date: 2026-08-03
"""

from alembic import op

revision = "0002_model_name"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE workflow_release ADD COLUMN model_name text")
    op.execute("""
    DO $$
    BEGIN
      ALTER TABLE workflow_release DISABLE TRIGGER release_immutable;
      BEGIN
        UPDATE workflow_release SET model_name = model_profile WHERE model_name IS NULL;
      EXCEPTION WHEN OTHERS THEN
        ALTER TABLE workflow_release ENABLE TRIGGER release_immutable;
        RAISE;
      END;
      ALTER TABLE workflow_release ENABLE TRIGGER release_immutable;
    END $$;
    """)
    op.execute("ALTER TABLE workflow_release ALTER COLUMN model_name SET NOT NULL")
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_release_immutable() RETURNS trigger AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN
        IF OLD.status = 'PUBLISHED' THEN RAISE EXCEPTION 'workflow_release % is PUBLISHED and immutable', OLD.id USING ERRCODE = 'VG409'; END IF;
        RETURN OLD;
      END IF;
      IF OLD.status = 'PUBLISHED' THEN RAISE EXCEPTION 'workflow_release % is PUBLISHED and immutable', OLD.id USING ERRCODE = 'VG409'; END IF;
      IF NEW.workflow_id IS DISTINCT FROM OLD.workflow_id OR NEW.release_version IS DISTINCT FROM OLD.release_version
         OR NEW.git_repo IS DISTINCT FROM OLD.git_repo OR NEW.entrypoint IS DISTINCT FROM OLD.entrypoint
         OR NEW.state_schema_version IS DISTINCT FROM OLD.state_schema_version OR NEW.bindings IS DISTINCT FROM OLD.bindings
         OR NEW.runtime_adapter_id IS DISTINCT FROM OLD.runtime_adapter_id OR NEW.model_profile IS DISTINCT FROM OLD.model_profile
         OR NEW.model_name IS DISTINCT FROM OLD.model_name THEN
        RAISE EXCEPTION 'workflow_release definition columns are not updatable' USING ERRCODE = 'VG409';
      END IF;
      RETURN NEW;
    END $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_release_immutable() RETURNS trigger AS $$
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
    """)
    op.execute("ALTER TABLE workflow_release DROP COLUMN model_name")
