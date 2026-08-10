# ReqKB Ingestion Physical Schema

**Status:** POC implementation baseline  
**Scope:** SQLite-first physical schema cho durable core của ReqKB ingestion  
**Depends on:** `00_database_review_methodology.md`, `01_design_methodology.md`, `02_storage_boundary.md`, `03_logical_data_model.md`  
**Related ADRs:** `adrs/ADR-001-publication-scope.md`, `adrs/ADR-002-stage-input-physical-reference.md`

---

## 1. Mục tiêu

Tài liệu này chuyển logical model sang schema đủ nhỏ để implement nhanh trong POC nhưng không phá đường scale lên PostgreSQL/main.

Nguyên tắc:

```text
POC đơn giản ở implementation detail
≠
POC làm yếu identity / lineage / baseline / publication semantics
```

Engine POC:

```text
Catalog DB = SQLite
```

Main có thể chuyển sang PostgreSQL qua repository/domain contract giữ ổn định.

---

## 2. Physical-design decisions

### PD-01 — application-generated opaque IDs

**Context:** ID được tham chiếu qua DB, Object Store, runtime và Neo4j.

**Decision:** POC dùng application-generated UUID-compatible string, lưu `TEXT PRIMARY KEY` trong SQLite.

**Rationale:** identity không phụ thuộc một DB instance/sequence và dễ correlation cross-store.

**Trade-off:** PostgreSQL main có thể đổi physical type sang `UUID`; domain/API vẫn coi ID là opaque string.

### PD-02 — UTC timestamp dạng TEXT trong SQLite

**Decision:** lưu RFC3339 UTC, ví dụ `2026-08-10T15:00:00Z`.

**Rationale:** readable, sortable khi format canonical, dễ migrate sang PostgreSQL `timestamptz`.

### PD-03 — workspace_id denormalization có chủ đích

**Context:** nhiều relationship nối các aggregate khác nhau; main cần tenant/RLS filtering hiệu quả.

**Decision:** các table governance/cross-reference quan trọng giữ `workspace_id` trực tiếp dù có thể derive qua parent.

**Rationale:** giúp query/filter và cho phép composite FK/validation cross-workspace.

**Trade-off:** có duplicate ownership key; write path phải verify consistency. Main security/RLS strategy vẫn cần ADR riêng.

### PD-04 — SQLite dùng WAL + foreign keys

POC connection bootstrap bắt buộc:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

**Rationale:** FK mặc định cần bật explicit; WAL phù hợp read-heavy POC với một writer tại một thời điểm.

**Trade-off:** SQLite vẫn không phải target cho high-concurrency multi-worker write.

---

## 3. POC table set

Implement NOW:

```text
workspace
source_asset
source_revision
processing_run
stage_execution
stage_input
output_slot
output_slot_scope_member
output_set
stored_object
baseline_selection
baseline_head
knowledge_space
publication_scope
publication
publication_head
```

Conditional, chưa cần table ở POC đầu tiên:

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

---

## 4. Table shape và constraints

### 4.1 Workspace / source

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

`UNIQUE(source_asset_id, content_hash)` tránh duplicate revision khi upload lại cùng bytes. Nếu product sau này cần intentional duplicate revision cùng content nhưng metadata khác, rule này phải được review lại trước main.

---

### 4.2 ProcessingRun / StageExecution

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

---

### 4.3 OutputSlot / source scope

```sql
CREATE TABLE output_slot (
  output_slot_id   TEXT PRIMARY KEY,
  workspace_id     TEXT NOT NULL REFERENCES workspace(workspace_id),
  artifact_role    TEXT NOT NULL,
  scope_fingerprint TEXT NOT NULL,
  logical_name     TEXT,
  created_at       TEXT NOT NULL,
  UNIQUE (workspace_id, artifact_role, scope_fingerprint),
  UNIQUE (output_slot_id, workspace_id)
);

CREATE TABLE output_slot_scope_member (
  output_slot_id    TEXT NOT NULL,
  workspace_id      TEXT NOT NULL,
  source_revision_id TEXT NOT NULL,
  scope_role        TEXT NOT NULL,
  ordinal           INTEGER NOT NULL CHECK (ordinal >= 0),
  PRIMARY KEY (output_slot_id, scope_role, ordinal),
  FOREIGN KEY (output_slot_id, workspace_id)
    REFERENCES output_slot(output_slot_id, workspace_id),
  FOREIGN KEY (source_revision_id, workspace_id)
    REFERENCES source_revision(source_revision_id, workspace_id),
  UNIQUE (output_slot_id, source_revision_id, scope_role)
);
```

`scope_fingerprint` được application tính từ canonical ordered scope members:

```text
(scope_role, source_revision_id, ordinal)
```

Rerun cùng scope phải resolve cùng OutputSlot, không tạo slot mới.

---

### 4.4 OutputSet / StoredObject

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
  UNIQUE (output_set_id, object_role),
  UNIQUE (stored_object_id, workspace_id)
);
```

POC baseline eligibility không cần một column `baseline_eligible` riêng.

Derived rule:

```text
registration_completed_at IS NOT NULL
AND output_set.integrity_status = VERIFIED
AND schema_validation_status = PASSED
AND không có required StoredObject nào ngoài VERIFIED/AVAILABLE
```

---

### 4.5 StageInput — controlled dual FK

Physical choice được chốt trong `ADR-002-stage-input-physical-reference.md`.

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

FK từ `source_baseline_selection_id` tới exact baseline/output được thêm sau khi `baseline_selection` được tạo; xem section 4.6.

---

### 4.6 Baseline history + head

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
  FOREIGN KEY (previous_baseline_selection_id)
    REFERENCES baseline_selection(baseline_selection_id),

  UNIQUE (baseline_selection_id, output_slot_id),
  UNIQUE (baseline_selection_id, output_set_id, output_slot_id),
  UNIQUE (baseline_selection_id, workspace_id)
);

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

Sau `baseline_selection` tạo thêm composite FK cho StageInput bằng migration/schema order phù hợp:

```text
(stage_input.source_baseline_selection_id, stage_input.output_set_id)
→ baseline_selection(baseline_selection_id, output_set_id)
```

SQLite không hỗ trợ `ALTER TABLE ... ADD CONSTRAINT` linh hoạt như PostgreSQL; vì vậy executable migration nên tạo `baseline_selection` trước `stage_input`, dù tài liệu trình bày StageInput trước vì dễ đọc.

---

### 4.7 KnowledgeSpace / PublicationScope

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

---

### 4.8 Publication history + head

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
  FOREIGN KEY (previous_publication_id)
    REFERENCES publication(publication_id),

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

`publication_head` là concurrency/current pointer; partial unique index là safety net để không có hai row `ACTIVE` trong cùng PublicationScope.

---

## 5. Critical write transactions

### 5.1 Register OutputSet

```text
1. write payload vào Object Store
2. verify hash/schema
3. BEGIN IMMEDIATE
4. INSERT output_set REGISTERING
5. INSERT stored_object rows
6. verify required objects
7. UPDATE output_set → VERIFIED + registration_completed_at
8. COMMIT
```

Nếu DB fail sau object write → orphan object để reconciliation/GC xử lý.

### 5.2 Select baseline — optimistic concurrency

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

Initial selection tạo BaselineSelection rồi INSERT BaselineHead `lock_version = 1` trong cùng transaction.

### 5.3 Activate publication

Cross-store flow:

```text
DB: create Publication PENDING
↓
Neo4j: materialize candidate invisibly
↓
verify
↓
DB transaction:
  verify PublicationHead lock_version
  mark publication VERIFIED/ACTIVE
  mark previous ACTIVE → SUPERSEDED
  move PublicationHead
↓
commit
```

Cách Neo4j giữ candidate invisible trước activation **chưa chốt trong 04**; bắt buộc ADR riêng trước implementation G3 cuối cùng.

---

## 6. Required indexes for POC

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

Không thêm index “cho chắc”. Mọi index mới phải gắn với query path/volume đo được.

---

## 7. Representative queries

### Current baseline

```sql
SELECT bs.*
FROM baseline_head bh
JOIN baseline_selection bs
  ON bs.baseline_selection_id = bh.current_baseline_selection_id
WHERE bh.output_slot_id = ?;
```

### Candidate history

```sql
SELECT *
FROM output_set
WHERE output_slot_id = ?
ORDER BY created_at DESC;
```

### Current published revision của stable source

```sql
SELECT p.*
FROM publication_scope ps
JOIN publication_head ph
  ON ph.publication_scope_id = ps.publication_scope_id
JOIN publication p
  ON p.publication_id = ph.current_publication_id
WHERE ps.knowledge_space_id = ?
  AND ps.source_asset_id = ?
  AND ps.publication_role = ?;
```

### Stale derived output

Không lưu canonical `is_stale`; derive từ StageInput baseline binding so với current upstream BaselineHead. Nếu main cần query thường xuyên, thêm rebuildable projection sau.

---

## 8. SQLite → PostgreSQL scale path

Giữ nguyên domain/entity contract; thay physical implementation nơi cần.

| Concern | SQLite POC | PostgreSQL main |
|---|---|---|
| ID | UUID string `TEXT` | `UUID` |
| Time | RFC3339 UTC `TEXT` | `timestamptz` |
| Status | `TEXT + CHECK` | `TEXT + CHECK` hoặc enum/domain sau review |
| Writer concurrency | single/few writers + WAL | MVCC / nhiều writers |
| Baseline CAS | `BEGIN IMMEDIATE` + lock_version | row-level lock hoặc optimistic update |
| Workspace security | application scoping | RLS + role policy nếu ADR chọn |
| JSON metadata | TEXT nếu cần | `jsonb` khi có query semantics |
| Partial unique index | supported | supported |
| Migration | rebuild table khi cần | richer ALTER, online migration strategy |

Không coi migration SQLite→PostgreSQL là chỉ đổi connection string. Cần migration test cho types, constraints, transaction/isolation và indexes.

---

## 9. Schema migration strategy

POC source of truth:

```text
schema/sqlite/
  001_init.sql
  002_...
```

Rules:

- migration append-only sau khi đã dùng chung;
- không sửa migration đã apply ở shared environment;
- mỗi change schema phải map tới logical invariant/decision;
- destructive change phải có data migration/backfill plan;
- khi physical schema ổn định, dùng Atlas inspect/diff/lint để machine-check drift/migration safety.

Bytebase chỉ cần khi project cần approval/change-management layer lớn hơn; không đưa vào runtime POC.

---

## 10. Gate D review checklist

Trước implementation:

- [ ] `PRAGMA foreign_keys = ON` được enforce ở connection bootstrap.
- [ ] OutputSlot uniqueness enforce bằng `(workspace, artifact_role, scope_fingerprint)`.
- [ ] StageInput exactly-one-target được CHECK/FK bảo vệ.
- [ ] BaselineSelection không thể chọn OutputSet của slot khác.
- [ ] BaselineHead chỉ trỏ selection của cùng slot.
- [ ] Baseline update dùng CAS/atomic transaction.
- [ ] Required StoredObject integrity đủ để derive eligibility.
- [ ] PublicationScope unique theo stable source/role.
- [ ] Publication pin exact baseline/output set.
- [ ] Tối đa một ACTIVE publication mỗi PublicationScope.
- [ ] PublicationHead dùng CAS khi activation.
- [ ] FK/query-path indexes tối thiểu đã có.
- [ ] Không hard-code table theo workflow step.
- [ ] Schema migration source-of-truth rõ ràng.

---

## 11. Open decisions trước G3 production-grade

Chưa chốt:

```text
Neo4j publication visibility strategy
Workspace/RLS security strategy cho PostgreSQL main
Whole-KB KnowledgeRelease semantics
```

Không blocker cho ingestion persistence POC; riêng Neo4j visibility phải được resolve bằng ADR trước khi G3 được coi production-safe.

---

## 12. Handoff

Sau `04`, implementation guide phải tập trung:

```text
Repository interfaces
SQLite connection/bootstrap
migration runner
transaction services
Object Store adapter
reconciliation tests
SQLite → PostgreSQL compatibility tests
```

Không thêm abstraction mới nếu chưa có query/lifecycle requirement chứng minh cần thiết.
