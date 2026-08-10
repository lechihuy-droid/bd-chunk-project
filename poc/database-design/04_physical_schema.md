# ReqKB Ingestion Physical Schema

**Status:** POC implementation baseline  
**Scope:** SQLite-first physical schema cho durable core của ReqKB ingestion  
**Depends on:** `00_database_review_methodology.md`, `01_design_methodology.md`, `02_storage_boundary.md`, `03_logical_data_model.md`  
**Related ADRs:** `adrs/ADR-001-publication-scope.md`, `adrs/ADR-002-stage-input-physical-reference.md`

---

## 1. Mục tiêu

Chuyển logical model sang schema **implement nhanh cho POC nhưng không throw-away khi lên main**.

```text
POC đơn giản ở implementation detail
≠
làm yếu identity / lineage / baseline / publication semantics
```

POC dùng SQLite. Main có thể đổi PostgreSQL qua repository/domain contract ổn định.

### Physical decisions

**PD-01 — ID:** application-generated UUID-compatible string, SQLite lưu `TEXT PRIMARY KEY`.  
**Lý do:** ID phải correlation được giữa DB, Object Store, runtime và Neo4j; không phụ thuộc DB sequence.

**PD-02 — time:** RFC3339 UTC `TEXT`.  
**Lý do:** readable/sortable khi canonical; main map sang PostgreSQL `timestamptz`.

**PD-03 — workspace_id denormalization:** giữ `workspace_id` trên các table cross-reference quan trọng.  
**Lý do:** enforce cross-workspace relationship và chuẩn bị query/RLS main.  
**Trade-off:** write service phải bảo đảm ownership consistency.

**PD-04 — SQLite bootstrap:**

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

WAL phù hợp POC read-heavy/few writers; SQLite không phải target cho high-concurrency write.

---

## 2. POC table set

Implement NOW:

```text
workspace
source_asset
source_revision
processing_run
stage_execution
output_slot
output_slot_scope_member
output_set
stored_object
baseline_selection
stage_input
baseline_head
knowledge_space
publication_scope
publication
publication_head
```

Conditional:

```text
review_request
review_decision
```

Deferred:

```text
knowledge_release
resource_registry
staleness_projection
output_contract_registry
full IAM/RLS tables
```

Executable migration order phải theo dependency list trên; đặc biệt `baseline_selection` được tạo trước `stage_input` để composite FK baseline binding có thể khai báo ngay từ đầu.

---

## 3. Core DDL

### 3.1 Workspace / source

```sql
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
```

POC coi cùng bytes của cùng SourceAsset là cùng content revision. Nếu main cần intentional revision mới dù bytes giống nhau, review lại unique rule này.

### 3.2 ProcessingRun / StageExecution

```sql
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
  stage_execution_id TEXT PRIMARY KEY,
  workspace_id       TEXT NOT NULL,
  processing_run_id  TEXT NOT NULL,
  stage_type         TEXT NOT NULL,
  component_ref      TEXT NOT NULL,
  configuration_hash TEXT NOT NULL,
  schema_contract_ref TEXT,
  runtime_ref        TEXT,
  status             TEXT NOT NULL CHECK (status IN
                     ('PENDING','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
  model_ref          TEXT,
  prompt_ref         TEXT,
  ruleset_ref        TEXT,
  trace_ref          TEXT,
  started_at         TEXT,
  completed_at       TEXT,
  created_at         TEXT NOT NULL,
  FOREIGN KEY (processing_run_id, workspace_id)
    REFERENCES processing_run(processing_run_id, workspace_id),
  UNIQUE (stage_execution_id, workspace_id)
);
```

Không tạo table theo `CONVERT/PARSE/ONTOLOGY`; `stage_type` là data.

### 3.3 OutputSlot / source scope

```sql
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
```

`scope_fingerprint = HASH(canonical ordered scope members)` với tuple:

```text
(scope_role, source_revision_id, ordinal)
```

Rerun cùng logical scope phải resolve cùng OutputSlot.

### 3.4 OutputSet / StoredObject

```sql
CREATE TABLE output_set (
  output_set_id       TEXT PRIMARY KEY,
  workspace_id        TEXT NOT NULL,
  output_slot_id      TEXT NOT NULL,
  producer_execution_id TEXT NOT NULL,
  integrity_status    TEXT NOT NULL CHECK (integrity_status IN
                       ('REGISTERING','VERIFIED','INVALID')),
  schema_validation_status TEXT NOT NULL CHECK (schema_validation_status IN
                       ('PENDING','PASSED','FAILED')),
  schema_version      TEXT,
  registration_completed_at TEXT,
  created_at          TEXT NOT NULL,
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
```

Không giới hạn một file cho mỗi role; `ordinal` cho phép nhiều object cùng role nếu main cần.

Baseline eligibility là derived invariant, không lưu duplicate boolean:

```text
registration_completed_at IS NOT NULL
AND output_set.integrity_status = VERIFIED
AND schema_validation_status = PASSED
AND không có required StoredObject ngoài VERIFIED/AVAILABLE
```

### 3.5 Baseline history

```sql
CREATE TABLE baseline_selection (
  baseline_selection_id TEXT PRIMARY KEY,
  workspace_id          TEXT NOT NULL,
  output_slot_id        TEXT NOT NULL,
  output_set_id         TEXT NOT NULL,
  previous_baseline_selection_id TEXT,
  selection_mode        TEXT NOT NULL CHECK (selection_mode IN
                        ('AUTO','AI_RECOMMEND','HUMAN')),
  review_decision_id    TEXT,
  selection_reason      TEXT,
  selected_by           TEXT NOT NULL,
  selected_at           TEXT NOT NULL,

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
```

`previous_baseline_selection_id` bị constrain cùng OutputSlot, tránh nối history chain sang artifact khác.

`review_decision_id` chưa có FK trong POC nếu Review capability chưa bật; khi tạo conditional tables phải thêm migration/verification tương ứng.

### 3.6 StageInput — controlled dual FK

Physical choice: `ADR-002-stage-input-physical-reference.md`.

```sql
CREATE TABLE stage_input (
  stage_input_id       TEXT PRIMARY KEY,
  workspace_id         TEXT NOT NULL,
  stage_execution_id   TEXT NOT NULL,
  input_role           TEXT NOT NULL,
  binding_mode         TEXT NOT NULL CHECK (binding_mode IN ('DIRECT','BASELINE')),
  source_revision_id   TEXT,
  output_set_id        TEXT,
  source_baseline_selection_id TEXT,
  resolved_hash        TEXT NOT NULL,
  ordinal              INTEGER NOT NULL CHECK (ordinal >= 0),

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
```

DB chứng minh baseline-bound input đã consume **đúng OutputSet được baseline đó chọn**.

### 3.7 BaselineHead

```sql
CREATE TABLE baseline_head (
  output_slot_id TEXT PRIMARY KEY,
  workspace_id   TEXT NOT NULL,
  current_baseline_selection_id TEXT NOT NULL,
  lock_version   INTEGER NOT NULL CHECK (lock_version >= 1),
  updated_at     TEXT NOT NULL,
  FOREIGN KEY (output_slot_id, workspace_id)
    REFERENCES output_slot(output_slot_id, workspace_id),
  FOREIGN KEY (current_baseline_selection_id, output_slot_id)
    REFERENCES baseline_selection(baseline_selection_id, output_slot_id)
);
```

### 3.8 KnowledgeSpace / PublicationScope

```sql
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
```

### 3.9 Publication history + head

```sql
CREATE TABLE publication (
  publication_id       TEXT PRIMARY KEY,
  workspace_id         TEXT NOT NULL,
  publication_scope_id TEXT NOT NULL,
  output_slot_id       TEXT NOT NULL,
  baseline_selection_id TEXT NOT NULL,
  output_set_id        TEXT NOT NULL,
  previous_publication_id TEXT,
  status               TEXT NOT NULL CHECK (status IN
                       ('PENDING','MATERIALIZING','VERIFIED','ACTIVE','FAILED','SUPERSEDED')),
  manifest_object_ref  TEXT,
  created_at           TEXT NOT NULL,
  activated_at         TEXT,

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
  publication_scope_id TEXT PRIMARY KEY,
  workspace_id         TEXT NOT NULL,
  current_publication_id TEXT NOT NULL,
  lock_version         INTEGER NOT NULL CHECK (lock_version >= 1),
  updated_at           TEXT NOT NULL,
  FOREIGN KEY (publication_scope_id, workspace_id)
    REFERENCES publication_scope(publication_scope_id, workspace_id),
  FOREIGN KEY (current_publication_id, publication_scope_id)
    REFERENCES publication(publication_id, publication_scope_id)
);
```

`previous_publication_id` bị constrain cùng PublicationScope. Partial unique index là safety net để không có hai `ACTIVE` publication trong cùng stable source stream.

Một invariant chưa thể encode gọn bằng FK: OutputSlot/OutputSet được publish phải thuộc SourceAsset của PublicationScope. Publication service bắt buộc verify qua `output_slot_scope_member → source_revision → source_asset` trước materialization/activation.

---

## 4. Critical transactions

### 4.1 Register OutputSet

```text
1. write payload Object Store
2. verify hash/schema
3. BEGIN IMMEDIATE
4. INSERT OutputSet REGISTERING
5. INSERT StoredObject rows
6. verify required objects
7. UPDATE OutputSet → VERIFIED + registration_completed_at
8. nếu đây là final intended outputs của execution: mark StageExecution SUCCEEDED
9. COMMIT
```

Nếu DB registration fail sau object write → orphan object để reconciliation/GC xử lý.

### 4.2 Select baseline — optimistic concurrency

```text
BEGIN IMMEDIATE
read BaselineHead(lock_version)
verify candidate eligibility
verify expected lock_version
INSERT BaselineSelection
UPDATE BaselineHead
  SET current_baseline_selection_id = :new,
      lock_version = lock_version + 1
  WHERE output_slot_id = :slot
    AND lock_version = :expected
require affected_rows = 1
COMMIT
```

Initial selection tạo BaselineSelection + BaselineHead(`lock_version=1`) trong cùng transaction.

### 4.3 Activate publication

```text
DB: create Publication PENDING
↓
verify PublicationScope ↔ SourceAsset ↔ OutputSlot provenance
↓
Neo4j: materialize candidate invisibly
↓
verify materialization
↓
BEGIN Catalog DB transaction
  verify PublicationHead lock_version
  previous ACTIVE → SUPERSEDED
  new Publication → ACTIVE
  move PublicationHead + increment lock_version
COMMIT
```

Cách Neo4j giữ candidate invisible trước activation **chưa chốt**; cần ADR riêng trước khi G3 production-safe.

---

## 5. Required indexes

SQLite không tự tạo index cho mọi FK/query path. Tối thiểu:

```sql
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
```

Không thêm index “cho chắc”; index mới phải gắn với query path/volume đo được.

---

## 6. Representative query paths

```text
Q1 current baseline
BaselineHead → BaselineSelection

Q2 candidate history
OutputSlot → OutputSet ORDER BY created_at

Q3 execution lineage
StageExecution → StageInput → SourceRevision/OutputSet

Q4 current published source
PublicationScope → PublicationHead → Publication

Q5 stale output
StageInput.source_baseline_selection_id
vs current upstream BaselineHead
```

`is_stale` không là canonical column; main có thể materialize rebuildable projection nếu query cost trở thành vấn đề.

---

## 7. SQLite → PostgreSQL scale path

| Concern | SQLite POC | PostgreSQL main |
|---|---|---|
| ID | UUID string `TEXT` | `UUID` |
| Time | RFC3339 UTC `TEXT` | `timestamptz` |
| Status | `TEXT + CHECK` | `TEXT + CHECK` hoặc enum/domain sau review |
| Writer concurrency | few writers + WAL | MVCC / nhiều writers |
| CAS | `BEGIN IMMEDIATE` + lock_version | optimistic update hoặc row lock |
| Workspace security | application scope | RLS nếu ADR chọn |
| JSON extension | TEXT khi thực sự cần | `jsonb` theo query semantics |
| Partial unique index | supported | supported |
| Migration | rebuild table khi cần | richer ALTER / online strategy |

Không coi SQLite→PostgreSQL là đổi connection string. Phải test lại type mapping, constraints, transaction/isolation và indexes.

---

## 8. Migration strategy

Schema source of truth:

```text
schema/sqlite/
  001_init.sql
  002_...
```

Rules:

- migration append-only sau khi shared environment đã apply;
- mỗi change map tới logical invariant/decision;
- destructive change cần backfill/migration plan;
- không sửa migration history đã apply;
- khi schema ổn định, dùng Atlas inspect/diff/lint để check drift/migration safety.

Bytebase chỉ cần khi cần approval/change-management layer lớn hơn; không đưa vào runtime POC.

---

## 9. Gate D review checklist

- [ ] `foreign_keys=ON`, WAL, busy timeout nằm trong connection bootstrap.
- [ ] OutputSlot uniqueness enforce bằng `(workspace, artifact_role, scope_fingerprint)`.
- [ ] StageInput exactly-one-target có FK + XOR CHECK.
- [ ] BASELINE StageInput pin đúng BaselineSelection + OutputSet.
- [ ] BaselineSelection không chọn OutputSet của slot khác.
- [ ] Previous baseline nằm cùng OutputSlot.
- [ ] BaselineHead chỉ trỏ selection của cùng slot và update bằng CAS.
- [ ] Required StoredObject integrity derive được baseline eligibility.
- [ ] PublicationScope unique theo stable SourceAsset/role.
- [ ] Publication pin exact baseline/output set.
- [ ] Previous publication nằm cùng PublicationScope.
- [ ] Publication service verify OutputSlot thuộc SourceAsset của PublicationScope.
- [ ] Tối đa một ACTIVE publication mỗi PublicationScope.
- [ ] PublicationHead update bằng CAS.
- [ ] FK/query-path indexes tối thiểu đã có.
- [ ] Không hard-code table theo workflow step.
- [ ] Migration source-of-truth rõ ràng.

---

## 10. Open decisions

Không blocker cho Catalog DB POC:

```text
Workspace/RLS strategy cho PostgreSQL main
Whole-KB KnowledgeRelease semantics
```

Blocker trước G3 production-safe:

```text
Neo4j publication visibility strategy
```

---

## 11. Handoff

Implementation guide tiếp theo tập trung:

```text
Repository interfaces
SQLite connection/bootstrap
migration runner
Baseline/Publication transaction services
Object Store adapter
reconciliation tests
SQLite → PostgreSQL compatibility tests
```

Không thêm abstraction mới nếu chưa có lifecycle/query requirement chứng minh cần thiết.
