-- ReqKB Catalog DB — SQLite initial migration
-- Version: 001
-- Source of truth: ../../04_physical_schema.md
-- Behavioral contract: ../../07_data_mutation_spec.md
--
-- Migration policy:
--   * apply once in order;
--   * do not edit after shared environments have applied it;
--   * later schema changes use 002_..., 003_..., ...;
--   * migration runner owns migration-version bookkeeping.
--
-- Connection bootstrap must also enforce these settings on application connections.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. Workspace / source identity
-- -----------------------------------------------------------------------------

CREATE TABLE workspace (
  workspace_id TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  created_at   TEXT NOT NULL
);

CREATE TABLE source_asset (
  source_asset_id TEXT PRIMARY KEY,
  workspace_id    TEXT NOT NULL REFERENCES workspace(workspace_id),
  logical_name    TEXT NOT NULL,
  created_at      TEXT NOT NULL,
  UNIQUE (source_asset_id, workspace_id)
);

CREATE TABLE source_revision (
  source_revision_id TEXT PRIMARY KEY,
  workspace_id       TEXT NOT NULL,
  source_asset_id    TEXT NOT NULL,
  content_hash       TEXT NOT NULL,
  raw_object_ref     TEXT NOT NULL,
  revision_reason    TEXT,
  created_at         TEXT NOT NULL,
  FOREIGN KEY (source_asset_id, workspace_id)
    REFERENCES source_asset(source_asset_id, workspace_id),
  UNIQUE (source_revision_id, workspace_id),
  UNIQUE (source_asset_id, content_hash)
);

-- -----------------------------------------------------------------------------
-- 2. Workflow execution correlation
-- -----------------------------------------------------------------------------

CREATE TABLE processing_run (
  processing_run_id TEXT PRIMARY KEY,
  workspace_id      TEXT NOT NULL REFERENCES workspace(workspace_id),
  runtime_ref       TEXT,
  status            TEXT NOT NULL CHECK (status IN
                     ('PENDING','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
  started_at        TEXT,
  completed_at      TEXT,
  created_at        TEXT NOT NULL,
  UNIQUE (processing_run_id, workspace_id)
);

CREATE TABLE stage_execution (
  stage_execution_id  TEXT PRIMARY KEY,
  workspace_id        TEXT NOT NULL,
  processing_run_id   TEXT NOT NULL,
  stage_type          TEXT NOT NULL,
  component_ref       TEXT NOT NULL,
  configuration_hash  TEXT NOT NULL,
  schema_contract_ref TEXT,
  runtime_ref         TEXT,
  status              TEXT NOT NULL CHECK (status IN
                      ('PENDING','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
  model_ref           TEXT,
  prompt_ref          TEXT,
  ruleset_ref         TEXT,
  trace_ref           TEXT,
  started_at          TEXT,
  completed_at        TEXT,
  created_at          TEXT NOT NULL,
  FOREIGN KEY (processing_run_id, workspace_id)
    REFERENCES processing_run(processing_run_id, workspace_id),
  UNIQUE (stage_execution_id, workspace_id)
);

-- -----------------------------------------------------------------------------
-- 3. Stable artifact identity / source scope
-- -----------------------------------------------------------------------------

CREATE TABLE output_slot (
  output_slot_id    TEXT PRIMARY KEY,
  workspace_id      TEXT NOT NULL REFERENCES workspace(workspace_id),
  artifact_role     TEXT NOT NULL,
  scope_fingerprint TEXT NOT NULL,
  logical_name      TEXT,
  created_at        TEXT NOT NULL,
  UNIQUE (workspace_id, artifact_role, scope_fingerprint),
  UNIQUE (output_slot_id, workspace_id)
);

CREATE TABLE output_slot_scope_member (
  output_slot_id     TEXT NOT NULL,
  workspace_id       TEXT NOT NULL,
  source_revision_id TEXT NOT NULL,
  scope_role         TEXT NOT NULL,
  ordinal            INTEGER NOT NULL CHECK (ordinal >= 0),
  PRIMARY KEY (output_slot_id, scope_role, ordinal),
  FOREIGN KEY (output_slot_id, workspace_id)
    REFERENCES output_slot(output_slot_id, workspace_id),
  FOREIGN KEY (source_revision_id, workspace_id)
    REFERENCES source_revision(source_revision_id, workspace_id),
  UNIQUE (output_slot_id, source_revision_id, scope_role)
);

-- -----------------------------------------------------------------------------
-- 4. Candidate output / immutable object registry
-- -----------------------------------------------------------------------------

CREATE TABLE output_set (
  output_set_id                  TEXT PRIMARY KEY,
  workspace_id                   TEXT NOT NULL,
  output_slot_id                 TEXT NOT NULL,
  producer_execution_id          TEXT NOT NULL,
  integrity_status               TEXT NOT NULL CHECK (integrity_status IN
                                 ('REGISTERING','VERIFIED','INVALID')),
  schema_validation_status       TEXT NOT NULL CHECK (schema_validation_status IN
                                 ('PENDING','PASSED','FAILED')),
  schema_version                 TEXT,
  registration_completed_at      TEXT,
  created_at                     TEXT NOT NULL,
  FOREIGN KEY (output_slot_id, workspace_id)
    REFERENCES output_slot(output_slot_id, workspace_id),
  FOREIGN KEY (producer_execution_id, workspace_id)
    REFERENCES stage_execution(stage_execution_id, workspace_id),
  UNIQUE (output_set_id, output_slot_id),
  UNIQUE (output_set_id, workspace_id)
);

CREATE TABLE stored_object (
  stored_object_id TEXT PRIMARY KEY,
  workspace_id     TEXT NOT NULL,
  output_set_id    TEXT NOT NULL,
  object_role      TEXT NOT NULL,
  ordinal          INTEGER NOT NULL DEFAULT 0 CHECK (ordinal >= 0),
  object_uri       TEXT NOT NULL,
  content_hash     TEXT NOT NULL,
  schema_version   TEXT,
  media_type       TEXT,
  is_required      INTEGER NOT NULL CHECK (is_required IN (0,1)),
  integrity_status TEXT NOT NULL CHECK (integrity_status IN
                   ('WRITING','WRITTEN','VERIFIED','AVAILABLE','INVALID')),
  size_bytes       INTEGER CHECK (size_bytes IS NULL OR size_bytes >= 0),
  created_at       TEXT NOT NULL,
  FOREIGN KEY (output_set_id, workspace_id)
    REFERENCES output_set(output_set_id, workspace_id),
  UNIQUE (output_set_id, object_role, ordinal),
  UNIQUE (stored_object_id, workspace_id)
);

-- -----------------------------------------------------------------------------
-- 5. Baseline history — created before stage_input because BASELINE bindings
--    use a composite FK to baseline_selection + output_set.
-- -----------------------------------------------------------------------------

CREATE TABLE baseline_selection (
  baseline_selection_id          TEXT PRIMARY KEY,
  workspace_id                   TEXT NOT NULL,
  output_slot_id                 TEXT NOT NULL,
  output_set_id                  TEXT NOT NULL,
  previous_baseline_selection_id TEXT,
  selection_mode                 TEXT NOT NULL CHECK (selection_mode IN
                                 ('AUTO','AI_RECOMMEND','HUMAN')),
  review_decision_id             TEXT,
  selection_reason               TEXT,
  selected_by                    TEXT NOT NULL,
  selected_at                    TEXT NOT NULL,
  FOREIGN KEY (output_slot_id, workspace_id)
    REFERENCES output_slot(output_slot_id, workspace_id),
  FOREIGN KEY (output_set_id, output_slot_id)
    REFERENCES output_set(output_set_id, output_slot_id),
  FOREIGN KEY (previous_baseline_selection_id, output_slot_id)
    REFERENCES baseline_selection(baseline_selection_id, output_slot_id),
  UNIQUE (baseline_selection_id, output_slot_id),
  UNIQUE (baseline_selection_id, output_set_id),
  UNIQUE (baseline_selection_id, output_set_id, output_slot_id),
  UNIQUE (baseline_selection_id, workspace_id)
);

CREATE TABLE stage_input (
  stage_input_id                  TEXT PRIMARY KEY,
  workspace_id                    TEXT NOT NULL,
  stage_execution_id              TEXT NOT NULL,
  input_role                      TEXT NOT NULL,
  binding_mode                    TEXT NOT NULL CHECK (binding_mode IN ('DIRECT','BASELINE')),
  source_revision_id              TEXT,
  output_set_id                   TEXT,
  source_baseline_selection_id    TEXT,
  resolved_hash                   TEXT NOT NULL,
  ordinal                         INTEGER NOT NULL CHECK (ordinal >= 0),
  FOREIGN KEY (stage_execution_id, workspace_id)
    REFERENCES stage_execution(stage_execution_id, workspace_id),
  FOREIGN KEY (source_revision_id, workspace_id)
    REFERENCES source_revision(source_revision_id, workspace_id),
  FOREIGN KEY (output_set_id, workspace_id)
    REFERENCES output_set(output_set_id, workspace_id),
  FOREIGN KEY (source_baseline_selection_id, output_set_id)
    REFERENCES baseline_selection(baseline_selection_id, output_set_id),
  CHECK ((source_revision_id IS NOT NULL) <> (output_set_id IS NOT NULL)),
  CHECK (
    (binding_mode = 'DIRECT' AND source_baseline_selection_id IS NULL)
    OR
    (binding_mode = 'BASELINE' AND output_set_id IS NOT NULL
       AND source_baseline_selection_id IS NOT NULL)
  ),
  UNIQUE (stage_execution_id, input_role, ordinal)
);

CREATE TABLE baseline_head (
  output_slot_id                 TEXT PRIMARY KEY,
  workspace_id                   TEXT NOT NULL,
  current_baseline_selection_id  TEXT NOT NULL,
  lock_version                   INTEGER NOT NULL CHECK (lock_version >= 1),
  updated_at                     TEXT NOT NULL,
  FOREIGN KEY (output_slot_id, workspace_id)
    REFERENCES output_slot(output_slot_id, workspace_id),
  FOREIGN KEY (current_baseline_selection_id, output_slot_id)
    REFERENCES baseline_selection(baseline_selection_id, output_slot_id)
);

-- -----------------------------------------------------------------------------
-- 6. Knowledge publication governance
-- -----------------------------------------------------------------------------

CREATE TABLE knowledge_space (
  knowledge_space_id TEXT PRIMARY KEY,
  workspace_id       TEXT NOT NULL REFERENCES workspace(workspace_id),
  name               TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('ACTIVE','DISABLED')),
  created_at         TEXT NOT NULL,
  UNIQUE (knowledge_space_id, workspace_id)
);

CREATE TABLE publication_scope (
  publication_scope_id TEXT PRIMARY KEY,
  workspace_id         TEXT NOT NULL,
  knowledge_space_id   TEXT NOT NULL,
  source_asset_id      TEXT NOT NULL,
  publication_role     TEXT NOT NULL,
  scope_key            TEXT,
  created_at           TEXT NOT NULL,
  FOREIGN KEY (knowledge_space_id, workspace_id)
    REFERENCES knowledge_space(knowledge_space_id, workspace_id),
  FOREIGN KEY (source_asset_id, workspace_id)
    REFERENCES source_asset(source_asset_id, workspace_id),
  UNIQUE (knowledge_space_id, source_asset_id, publication_role),
  UNIQUE (publication_scope_id, workspace_id)
);

CREATE TABLE publication (
  publication_id          TEXT PRIMARY KEY,
  workspace_id            TEXT NOT NULL,
  publication_scope_id    TEXT NOT NULL,
  output_slot_id          TEXT NOT NULL,
  baseline_selection_id   TEXT NOT NULL,
  output_set_id           TEXT NOT NULL,
  previous_publication_id TEXT,
  status                  TEXT NOT NULL CHECK (status IN
                          ('PENDING','MATERIALIZING','VERIFIED','ACTIVE','FAILED','SUPERSEDED')),
  manifest_object_ref     TEXT,
  created_at              TEXT NOT NULL,
  activated_at            TEXT,
  FOREIGN KEY (publication_scope_id, workspace_id)
    REFERENCES publication_scope(publication_scope_id, workspace_id),
  FOREIGN KEY (baseline_selection_id, output_set_id, output_slot_id)
    REFERENCES baseline_selection(baseline_selection_id, output_set_id, output_slot_id),
  FOREIGN KEY (previous_publication_id, publication_scope_id)
    REFERENCES publication(publication_id, publication_scope_id),
  UNIQUE (publication_id, publication_scope_id),
  UNIQUE (publication_id, workspace_id)
);

CREATE UNIQUE INDEX uq_publication_one_active
  ON publication(publication_scope_id)
  WHERE status = 'ACTIVE';

CREATE TABLE publication_head (
  publication_scope_id  TEXT PRIMARY KEY,
  workspace_id          TEXT NOT NULL,
  current_publication_id TEXT NOT NULL,
  lock_version          INTEGER NOT NULL CHECK (lock_version >= 1),
  updated_at            TEXT NOT NULL,
  FOREIGN KEY (publication_scope_id, workspace_id)
    REFERENCES publication_scope(publication_scope_id, workspace_id),
  FOREIGN KEY (current_publication_id, publication_scope_id)
    REFERENCES publication(publication_id, publication_scope_id)
);

-- -----------------------------------------------------------------------------
-- 7. Query-path / FK-supporting indexes
-- -----------------------------------------------------------------------------

CREATE INDEX ix_source_revision_asset
  ON source_revision(source_asset_id, created_at);

CREATE INDEX ix_stage_execution_run
  ON stage_execution(processing_run_id, created_at);

CREATE INDEX ix_stage_input_execution
  ON stage_input(stage_execution_id, ordinal);

CREATE INDEX ix_stage_input_output
  ON stage_input(output_set_id);

CREATE INDEX ix_stage_input_source_revision
  ON stage_input(source_revision_id);

CREATE INDEX ix_stage_input_baseline
  ON stage_input(source_baseline_selection_id);

CREATE INDEX ix_scope_member_revision
  ON output_slot_scope_member(source_revision_id);

CREATE INDEX ix_output_set_slot
  ON output_set(output_slot_id, created_at);

CREATE INDEX ix_output_set_execution
  ON output_set(producer_execution_id);

CREATE INDEX ix_stored_object_output
  ON stored_object(output_set_id, is_required, integrity_status);

CREATE INDEX ix_baseline_selection_slot
  ON baseline_selection(output_slot_id, selected_at);

CREATE INDEX ix_baseline_selection_output
  ON baseline_selection(output_set_id);

CREATE INDEX ix_publication_scope_source
  ON publication_scope(source_asset_id, knowledge_space_id);

CREATE INDEX ix_publication_scope_history
  ON publication(publication_scope_id, created_at);

CREATE INDEX ix_publication_output
  ON publication(output_set_id);

COMMIT;
