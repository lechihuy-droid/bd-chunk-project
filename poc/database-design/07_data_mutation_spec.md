# ReqKB Data Mutation Specification

**Status:** POC implementation contract  
**Audience:** Coding agent / backend developer  
**Scope:** Action nào đọc/ghi table nào, field nào lấy giá trị từ đâu, transaction boundary, state transition và failure behavior  
**Depends on:** `03_logical_data_model.md`, `04_physical_schema.md`, `05_implementation_guide.md`, `06_data_flow.md`  
**Field reference:** `08_data_dictionary.md`

---

## 1. Purpose

Tài liệu này trả lời câu hỏi mà ERD/DFD không trả lời đủ chi tiết:

> Khi một command/action xảy ra, application phải đọc table nào, ghi field nào, giá trị lấy từ đâu, transaction kết thúc ở đâu và failure để lại state gì?

Coding agent phải dùng tài liệu này cùng `04_physical_schema.md`.

```text
03 = entity / relationship truth
04 = physical table / constraint truth
06 = data movement
07 = mutation behavior
08 = field meaning / source / mutability
```

Không implement generic CRUD endpoint cho từng table nếu command cần bảo vệ invariant xuyên nhiều row.

---

## 2. Global mutation rules

### MR-01 — ID do application tạo trước persistence

Các business ID dùng opaque UUID-compatible string:

```text
workspace_id
source_asset_id
source_revision_id
processing_run_id
stage_execution_id
stage_input_id
output_slot_id
output_set_id
stored_object_id
baseline_selection_id
knowledge_space_id
publication_scope_id
publication_id
```

**Rationale:** ID phải usable xuyên Catalog DB, Object Store, runtime và Neo4j trước khi DB insert hoàn tất.

**Consequence:** retry cùng logical operation phải reuse cùng pre-generated ID khi cần idempotency; không generate ID mới ở mỗi retry.

---

### MR-02 — timestamp ghi UTC RFC3339

Application tạo timestamp canonical UTC cho `*_at` fields.

```text
2026-08-11T00:30:15.123Z
```

DB không tự suy diễn business ordering từ local timezone.

---

### MR-03 — SourceAsset không được đoán từ filename

**Context:** `SourceAsset` là stable business identity, trong khi filename/logical name có thể đổi hoặc trùng.

**Decision:**

- tạo source mới: client/application không truyền `source_asset_id` → tạo `SourceAsset` mới;
- tạo revision mới của source cũ: command **phải truyền exact `source_asset_id`**;
- không resolve SourceAsset chỉ bằng `logical_name` hoặc filename.

**Rationale:** tránh merge nhầm hai document khác nhau hoặc split revision history khi đổi tên file.

**Trade-off:** Web App phải giữ/hiển thị stable source identity khi user upload revision mới.

---

### MR-04 — OutputSet `resolved_hash` là deterministic bundle hash

`stage_input.resolved_hash` bắt buộc tồn tại cho cả SourceRevision và OutputSet.

Value source:

```text
SourceRevision input
→ source_revision.content_hash

OutputSet input
→ HASH(canonical ordered StoredObject members)
```

Canonical member tuple:

```text
(object_role, ordinal, content_hash)
```

Sort deterministic trước serialization/hash.

**Rationale:** `OutputSet` không có single payload hash column nhưng các StoredObject member immutable; bundle hash có thể recompute và dùng để chứng minh exact consumed content.

**Consequence:** hash representation nên có version/algorithm prefix nếu implementation có khả năng đổi algorithm, ví dụ `v1:sha256:...`. Database coi value là opaque canonical string.

---

### MR-05 — Runtime ref là provider-qualified opaque reference

```text
langgraph:<opaque-id>
prefect:<opaque-id>
```

Không parse runtime-specific internals ngoài runtime adapter.

---

### MR-06 — External store không nằm trong Catalog DB transaction

Không tạo distributed transaction giữa:

```text
Catalog DB
Object Store
Neo4j
LangGraph / Prefect
MLflow
```

Cross-store flow phải dùng:

```text
explicit status
+ deterministic/idempotent operation
+ verification
+ reconciliation
```

---

## 3. Command summary matrix

| Command / event | Reads | Writes | External side effect |
|---|---|---|---|
| `RegisterSource` | workspace, optional source_asset | source_asset, source_revision | write raw Object Store payload |
| `StartProcessing` | workspace | processing_run | runtime start |
| `StartStageExecution` | processing_run, source_revision/output_set/baseline_head | stage_execution, stage_input | runtime/node execution |
| `RegisterOutputSet` | stage_execution, source_revision scope | output_slot, output_slot_scope_member, output_set, stored_object | write/verify Object Store payload |
| `CompleteStageExecution` | stage_execution, output_set | stage_execution | runtime correlation only |
| `FailStageExecution` | stage_execution | stage_execution | runtime correlation only |
| `SelectBaseline` | output_set, stored_object, baseline_head | baseline_selection, baseline_head | none |
| `ResumeWorkflow` | processing_run | none required | runtime resume |
| `CompleteProcessingRun` | stage_execution | processing_run | none |
| `CreatePublication` | baseline_head/selection, output_set, publication_scope/head | publication_scope, publication | none yet |
| `MaterializePublication` | publication, stored_object | publication status/ref fields | Object Store + Neo4j |
| `ActivatePublication` | publication, publication_head | publication, publication_head | visibility activation per Neo4j ADR |
| `FailPublication` | publication | publication | cleanup/reconciliation as needed |
| `ReconcileIntegrity` | stored_object/output_set/runtime/publication | affected status facts only | Object Store/runtime/Neo4j read/repair |

---

# 4. RegisterSource

## Trigger

User/application registers a new source or uploads a new revision of an existing source.

## Input

```text
workspace_id
source_asset_id?       # required for existing-source revision
logical_name?          # required when creating new SourceAsset
raw payload
revision_reason?
source_revision_id     # pre-generated
```

## Preconditions

- `workspace_id` exists.
- If `source_asset_id` supplied: SourceAsset exists and belongs to same Workspace.
- Raw payload can be hashed and written to Object Store.

## External write — before Catalog registration

```text
write immutable raw object
→ verify object exists
→ calculate content_hash
→ obtain raw_object_ref
```

If Object Store write fails: **do not create SourceRevision**.

## Catalog mutation

### Case A — new SourceAsset

Insert `source_asset`:

| Field | Value source |
|---|---|
| `source_asset_id` | application generated |
| `workspace_id` | command input |
| `logical_name` | command input |
| `created_at` | now UTC |

### Case B — existing SourceAsset

No SourceAsset mutation.

### Insert SourceRevision

| Field | Value source |
|---|---|
| `source_revision_id` | pre-generated command ID |
| `workspace_id` | SourceAsset.workspace_id |
| `source_asset_id` | created/provided exact SourceAsset |
| `content_hash` | raw payload hash |
| `raw_object_ref` | Object Store reference |
| `revision_reason` | command input nullable |
| `created_at` | now UTC |

## Transaction boundary

New SourceAsset + SourceRevision insert must be one Catalog DB transaction.

Object Store write is outside this transaction.

## Duplicate content

`UNIQUE(source_asset_id, content_hash)` protects duplicate revision content.

Recommended behavior:

```text
same SourceAsset + same content_hash
→ return existing SourceRevision as idempotent result
```

Do not create a second revision solely because upload was retried.

## Failure state

Object written but DB insert fails:

```text
orphan raw object
→ reconciliation / GC candidate
```

Do not overwrite another revision.

---

# 5. StartProcessing

## Trigger

Web App starts workflow processing.

## Input

```text
workspace_id
processing_run_id       # pre-generated
workflow_ref            # application/runtime config, not DB column
initial_input_ref       # used by runtime; exact lineage persisted at StageInput
```

## Step 1 — create run before runtime call

Insert `processing_run`:

| Field | Value |
|---|---|
| `processing_run_id` | command input/pre-generated |
| `workspace_id` | command input |
| `runtime_ref` | NULL |
| `status` | `PENDING` |
| `started_at` | NULL |
| `completed_at` | NULL |
| `created_at` | now UTC |

Commit before calling runtime.

**Rationale:** even runtime-start failure must leave an auditable business run record.

## Step 2 — start runtime

```text
WorkflowRuntimePort.start(..., correlation_id=processing_run_id)
```

### On success

Update `processing_run`:

| Field | Value |
|---|---|
| `runtime_ref` | provider-qualified runtime ref |
| `status` | `RUNNING` |
| `started_at` | now UTC |

### On failure

Update:

```text
status       = FAILED
completed_at = now UTC
runtime_ref  = NULL unless provider returned a durable ref
```

Return `RUNTIME_START_FAILED`.

Do not delete ProcessingRun.

---

# 6. StartStageExecution and bind exact inputs

## Trigger

Runtime/application is ready to execute one processing capability.

## Input

```text
stage_execution_id
processing_run_id
stage_type
component_ref
configuration_hash
schema_contract_ref?
model_ref?
prompt_ref?
ruleset_ref?
input bindings[]
```

## Preconditions

- ProcessingRun exists in same Workspace and is not terminal.
- Every input target exists in same Workspace.
- Baseline binding resolves to exact current BaselineSelection before execution starts.

## Transaction

Create StageExecution and all StageInput rows in one Catalog transaction.

### Insert `stage_execution`

| Field | Value source |
|---|---|
| `stage_execution_id` | pre-generated |
| `workspace_id` | ProcessingRun.workspace_id |
| `processing_run_id` | command input |
| `stage_type` | workflow/capability config |
| `component_ref` | implementation/component ref |
| `configuration_hash` | canonical execution config hash |
| `schema_contract_ref` | config nullable |
| `runtime_ref` | nullable; attach when stage runtime ref exists |
| `status` | `PENDING` initially |
| `model_ref` | AI config nullable |
| `prompt_ref` | AI config nullable |
| `ruleset_ref` | rules/config nullable |
| `trace_ref` | NULL initially unless trace created synchronously |
| `started_at` | NULL initially |
| `completed_at` | NULL |
| `created_at` | now UTC |

### Input type A — direct SourceRevision

Insert `stage_input`:

```text
binding_mode                       = DIRECT
source_revision_id                  = exact revision
output_set_id                       = NULL
source_baseline_selection_id        = NULL
resolved_hash                       = source_revision.content_hash
```

### Input type B — direct OutputSet

```text
binding_mode                       = DIRECT
source_revision_id                  = NULL
output_set_id                       = exact output set
source_baseline_selection_id        = NULL
resolved_hash                       = deterministic OutputSet bundle hash
```

### Input type C — resolve current baseline

Resolution must happen **before** execution:

```text
OutputSlot
→ BaselineHead.current_baseline_selection_id
→ BaselineSelection.output_set_id
```

Persist:

```text
binding_mode                       = BASELINE
source_revision_id                  = NULL
output_set_id                       = resolved exact OutputSet
source_baseline_selection_id        = resolved exact BaselineSelection
resolved_hash                       = deterministic OutputSet bundle hash
```

Other fields:

| Field | Value |
|---|---|
| `stage_input_id` | pre-generated |
| `workspace_id` | StageExecution.workspace_id |
| `stage_execution_id` | new execution |
| `input_role` | capability input role |
| `ordinal` | deterministic position within role |

## Start execution

After StageExecution + StageInput commit:

```text
stage_execution.status     = RUNNING
stage_execution.started_at = now UTC
```

If runtime provides stage-level ref, update `runtime_ref` at same transition.

## Freeze rule

Once status reaches `RUNNING`, do not rewrite:

```text
processing_run_id
stage_type
component_ref
configuration_hash
schema_contract_ref
StageInput targets
StageInput resolved_hash
```

Retry execution creates a new StageExecution unless runtime retry semantics explicitly represent the same execution attempt.

---

# 7. RegisterOutputSet

## Trigger

Stage capability has produced one coherent logical result.

## Input

```text
output_set_id
producer_execution_id
artifact_role
source scope members[]
logical_name?
schema_version?
stored objects[]
```

Each stored object input contains at least:

```text
stored_object_id
object_role
ordinal
payload/object ref
schema_version?
media_type?
is_required
```

## Preconditions

- Producer StageExecution exists and belongs to same Workspace.
- Source scope members are exact SourceRevisions in same Workspace.
- Artifact payloads are written immutably to Object Store.
- Hash/schema verification has completed before OutputSet becomes eligible.

## Step 1 — write/verify Object Store outside DB transaction

For each payload:

```text
write immutable object
verify existence
calculate content_hash
capture object_uri + size_bytes
validate schema when required
```

## Step 2 — resolve deterministic OutputSlot

Canonical scope input:

```text
(scope_role, source_revision_id, ordinal)
```

Normalize/sort deterministically, serialize canonically, then compute `scope_fingerprint`.

Lookup:

```text
(workspace_id, artifact_role, scope_fingerprint)
```

If found → reuse OutputSlot.

If not found → insert:

| Field | Value |
|---|---|
| `output_slot_id` | pre-generated candidate slot ID |
| `workspace_id` | producer workspace |
| `artifact_role` | command input |
| `scope_fingerprint` | deterministic computed value |
| `logical_name` | display value nullable |
| `created_at` | now UTC |

Then insert all `output_slot_scope_member` rows.

Concurrent insert losing unique race must query/reuse the winning existing OutputSlot; do not create duplicate artifact series.

## Step 3 — register candidate

Within one Catalog transaction:

Insert `output_set` initially:

```text
output_set_id                 = pre-generated stable retry ID
workspace_id                  = producer workspace
output_slot_id                = resolved slot
producer_execution_id         = exact producer
integrity_status              = REGISTERING
schema_validation_status      = PENDING
schema_version                = command value
registration_completed_at     = NULL
created_at                    = now UTC
```

Insert `stored_object` rows:

| Field | Value |
|---|---|
| `stored_object_id` | pre-generated stable retry ID |
| `workspace_id` | producer workspace |
| `output_set_id` | current OutputSet |
| `object_role` | artifact contract/config |
| `ordinal` | deterministic role-local order |
| `object_uri` | verified Object Store ref |
| `content_hash` | verified object hash |
| `schema_version` | object schema version nullable |
| `media_type` | known media type nullable |
| `is_required` | resolved from current application output contract/config |
| `integrity_status` | normally `AVAILABLE` in current POC post-write registration path |
| `size_bytes` | verified object size nullable |
| `created_at` | now UTC |

Current POC writes objects before DB registration, therefore transient `WRITING/WRITTEN` StoredObject states are not normally persisted. They remain valid states if future implementation registers before upload completes.

## Step 4 — close registration

Verify within service:

```text
all required StoredObjects exist
AND required object integrity in VERIFIED/AVAILABLE
AND required schema validation passed
```

Then update `output_set`:

```text
integrity_status             = VERIFIED
schema_validation_status     = PASSED
registration_completed_at    = now UTC
```

If validation fails:

```text
integrity_status             = INVALID
schema_validation_status     = FAILED when schema is the cause
registration_completed_at    = now UTC or NULL per failure phase
```

Invalid OutputSet never becomes baseline eligible.

## Important

RegisterOutputSet **does not** change BaselineHead.

```text
successful output != accepted output
```

---

# 8. CompleteStageExecution / FailStageExecution

## CompleteStageExecution

Preconditions:

- execution currently `RUNNING` or valid non-terminal state;
- all output registrations required by that stage contract are complete;
- zero-output success is allowed only when the capability contract allows it.

Update:

```text
stage_execution.status       = SUCCEEDED
stage_execution.completed_at = now UTC
```

Optional `trace_ref` may be attached before terminalization if available.

## FailStageExecution

Update:

```text
stage_execution.status       = FAILED
stage_execution.completed_at = now UTC
```

Historical StageInput and any already registered OutputSet remain unchanged.

A failed new execution never changes existing BaselineHead.

---

# 9. SelectBaseline

## Trigger

Human, AI recommendation workflow or policy selects one candidate OutputSet for an OutputSlot.

## Input

```text
baseline_selection_id
output_slot_id
output_set_id
expected_lock_version?       # required when head already exists
selection_mode               # AUTO | AI_RECOMMEND | HUMAN
selected_by
selection_reason?
review_decision_id?
```

## Preconditions

1. OutputSet exists and belongs to same OutputSlot.
2. OutputSet is baseline eligible:

```text
registration_completed_at IS NOT NULL
integrity_status = VERIFIED
schema_validation_status = PASSED
no required StoredObject outside VERIFIED/AVAILABLE
```

3. Workspace ownership matches.
4. If Review Inbox enabled, review decision must refer to same OutputSlot/candidate.

## Transaction

Use `BEGIN IMMEDIATE` in SQLite POC.

### Existing BaselineHead

Read:

```text
current_baseline_selection_id
lock_version
```

Require:

```text
lock_version == expected_lock_version
```

Insert `baseline_selection`:

| Field | Value |
|---|---|
| `baseline_selection_id` | pre-generated |
| `workspace_id` | OutputSlot.workspace_id |
| `output_slot_id` | command input |
| `output_set_id` | selected candidate |
| `previous_baseline_selection_id` | current head selection |
| `selection_mode` | command input |
| `review_decision_id` | command input nullable |
| `selection_reason` | command input nullable |
| `selected_by` | actor/policy reference |
| `selected_at` | now UTC |

CAS update:

```sql
UPDATE baseline_head
SET current_baseline_selection_id = :new_selection_id,
    lock_version = lock_version + 1,
    updated_at = :now
WHERE output_slot_id = :output_slot_id
  AND lock_version = :expected_lock_version;
```

Require affected rows = 1.

### Initial baseline — no head exists

Insert BaselineSelection with:

```text
previous_baseline_selection_id = NULL
```

Then insert `baseline_head`:

```text
output_slot_id                 = slot
workspace_id                   = slot workspace
current_baseline_selection_id  = new selection
lock_version                   = 1
updated_at                     = now UTC
```

All in one transaction.

## Conflict

If CAS fails:

```text
ROLLBACK
→ BASELINE_CONFLICT
```

Do not blind retry with stale user/agent decision.

---

# 10. ResumeWorkflow

## Trigger

A durable governance decision (for example baseline selection) has committed and workflow may continue.

## Ordering rule

```text
1. commit governance decision
2. call WorkflowRuntimePort.resume(...)
```

Do not resume first.

## Catalog mutation

No baseline/publication mutation.

Runtime status correlation may later update ProcessingRun/StageExecution through their own lifecycle handlers.

## Failure

If resume fails:

```text
committed BaselineSelection remains valid
runtime resume can retry idempotently
```

Do not roll back BaselineHead.

---

# 11. CompleteProcessingRun / CancelProcessingRun

## CompleteProcessingRun

When workflow reaches terminal success and required StageExecutions are complete:

```text
processing_run.status       = SUCCEEDED
processing_run.completed_at = now UTC
```

## FailProcessingRun

When workflow cannot continue per application policy:

```text
processing_run.status       = FAILED
processing_run.completed_at = now UTC
```

## CancelProcessingRun

After/while requesting runtime cancellation:

```text
processing_run.status       = CANCELLED
processing_run.completed_at = now UTC
```

Cancellation does not delete StageExecution/OutputSet history and does not change baseline/publication automatically.

---

# 12. CreatePublication

## Trigger

User/policy requests publication of an accepted baseline into a KnowledgeSpace.

## Input

```text
publication_id
knowledge_space_id
source_asset_id
publication_role
output_slot_id
baseline_selection_id
output_set_id
scope_key?
```

## Preconditions

- KnowledgeSpace and SourceAsset belong to same Workspace.
- BaselineSelection selects the exact supplied OutputSet in supplied OutputSlot.
- OutputSet is still registered/integrity-valid.
- OutputSlot source membership resolves to the SourceAsset of PublicationScope.
- Non-ACTIVE publication is not treated as visible knowledge.

## Resolve/create PublicationScope

Lookup exact unique key:

```text
knowledge_space_id
+ source_asset_id
+ publication_role
```

If absent insert:

| Field | Value |
|---|---|
| `publication_scope_id` | pre-generated |
| `workspace_id` | KnowledgeSpace.workspace_id |
| `knowledge_space_id` | command input |
| `source_asset_id` | command input |
| `publication_role` | command input |
| `scope_key` | optional display/integration key |
| `created_at` | now UTC |

Concurrent duplicate create → reuse winning PublicationScope.

## Resolve previous publication

If PublicationHead exists:

```text
previous_publication_id = publication_head.current_publication_id
expected publication_head.lock_version captured for later activation
```

Else previous is NULL.

## Insert Publication

```text
publication_id          = pre-generated stable retry ID
workspace_id            = scope workspace
publication_scope_id    = resolved scope
output_slot_id           = exact accepted slot
baseline_selection_id    = exact accepted selection
output_set_id            = exact selected output
previous_publication_id  = current active publication or NULL
status                   = PENDING
manifest_object_ref      = NULL
created_at               = now UTC
activated_at             = NULL
```

Commit before Neo4j materialization.

---

# 13. MaterializePublication

## Preconditions

Publication status is `PENDING`, or retry policy allows resuming same publication ID.

## Step 1 — mark materializing

```text
publication.status = MATERIALIZING
```

## Step 2 — resolve canonical payload

Use Publication → exact OutputSet → StoredObject registry → Object Store.

Do not query latest/baseline again to change publication input.

## Step 3 — materialize candidate in Neo4j invisibly

Physical invisibility strategy is governed by separate publication ADR when chosen.

Operation must be idempotent by `publication_id`.

## Step 4 — verify candidate

If verification succeeds, write immutable publication manifest to Object Store.

Manifest should include exact references sufficient to audit/reconcile, including at least:

```text
publication_id
publication_scope_id
baseline_selection_id
output_set_id
source object hashes / semantic materialization reference
```

Update Catalog:

```text
publication.manifest_object_ref = manifest Object Store ref
publication.status              = VERIFIED
```

No PublicationHead move yet.

## Failure

If materialization/verification fails before activation:

```text
publication.status = FAILED
```

Previous PublicationHead remains unchanged.

---

# 14. ActivatePublication

## Preconditions

- New Publication status = `VERIFIED`.
- Manifest exists.
- Candidate semantic state verified.
- Current PublicationHead still matches the concurrency state captured/expected by caller.

## Catalog transaction

SQLite POC: `BEGIN IMMEDIATE`.

### Existing head

1. Re-read PublicationHead and verify expected `lock_version` / expected current publication.
2. Update previous current publication:

```text
status = SUPERSEDED
```

3. Update new publication:

```text
status       = ACTIVE
activated_at = now UTC
```

4. CAS move PublicationHead:

```text
current_publication_id = new publication
lock_version           = lock_version + 1
updated_at             = now UTC
```

### Initial head

Set new Publication `ACTIVE`, then insert:

```text
publication_scope_id
workspace_id
current_publication_id = new publication
lock_version           = 1
updated_at             = now UTC
```

All Catalog mutations above occur in one transaction.

## Why supersede before activate inside same transaction?

`uq_publication_one_active` allows max one `ACTIVE` row per PublicationScope. Same transaction prevents externally visible Catalog state with two active publications.

## Conflict

If PublicationHead changed since candidate was prepared:

```text
ROLLBACK
→ PUBLICATION_CONFLICT
```

Do not overwrite the newer active publication.

New candidate may remain `VERIFIED` for explicit retry/reconciliation; do not silently rebase it onto a different previous publication.

---

# 15. FailPublication

Before ACTIVE:

```text
publication.status = FAILED
```

Do not change:

```text
previous active Publication
PublicationHead
historical baseline
```

After ACTIVE, failures in downstream consumers do not rewrite publication history; handle them as operational incidents/reconciliation.

---

# 16. ReconcileIntegrity

Reconciliation may detect cross-store divergence but must not invent governance decisions.

## Case A — StoredObject registry points to missing/corrupt object

Allowed mutation:

```text
stored_object.integrity_status = INVALID
output_set.integrity_status    = INVALID when required member invalidates bundle
```

If invalid OutputSet is current baseline:

```text
raise/record operational alert
DO NOT auto-select another baseline
```

Historical BaselineSelection remains unchanged.

## Case B — orphan Object Store object

No Catalog mutation required unless adopted by an explicit registration command.

Otherwise GC/retention handles it.

## Case C — Catalog StageExecution says RUNNING but runtime terminal

Application may update StageExecution/ProcessingRun lifecycle status when runtime evidence and policy are sufficient.

It must not change BaselineHead/PublicationHead.

## Case D — Publication stuck MATERIALIZING/VERIFIED

Inspect candidate by same `publication_id`.

Allowed outcomes:

```text
retry idempotently
mark FAILED per policy
activate only after normal preconditions + concurrency check
```

---

# 17. Field mutability by lifecycle

## Immutable after creation/registration

```text
SourceRevision.content_hash
SourceRevision.raw_object_ref
StageInput target refs
StageInput.resolved_hash
OutputSlot identity fields
OutputSlotScopeMember membership
OutputSet.output_slot_id
OutputSet.producer_execution_id
StoredObject object_uri/content_hash/role/ordinal after registration
BaselineSelection fields
Publication pinned source refs after materialization starts
```

## Mutable lifecycle/status fields

```text
ProcessingRun.runtime_ref/status/started_at/completed_at
StageExecution.runtime_ref/status/trace_ref/started_at/completed_at
OutputSet.integrity_status/schema_validation_status/registration_completed_at
StoredObject.integrity_status during integrity lifecycle
KnowledgeSpace.status
Publication.status/manifest_object_ref/activated_at
```

## Mutable current pointers — concurrency protected

```text
BaselineHead.current_baseline_selection_id
BaselineHead.lock_version
PublicationHead.current_publication_id
PublicationHead.lock_version
```

---

# 18. Transaction map

| Transaction | Must be atomic inside Catalog DB |
|---|---|
| Register new source identity | SourceAsset + SourceRevision |
| Start StageExecution | StageExecution + all initial StageInput bindings |
| Register OutputSet | OutputSet + StoredObject registry + final registration state |
| Select baseline | append BaselineSelection + move BaselineHead CAS |
| Activate publication | supersede previous + activate new + move PublicationHead CAS |

External writes happen outside these relational transactions.

---

# 19. Coding-agent anti-patterns

Do not implement:

```text
SELECT latest output → treat as baseline
filename → infer SourceAsset identity
LangGraph state → authoritative baseline/publication
UPDATE historical StageInput after upstream baseline changes
overwrite Object Store path named /latest or /final
free-form StageInput type + string ID without FK
publish Neo4j candidate visibly before activation
last-write-wins BaselineHead / PublicationHead
runtime failure → delete business history
```

---

# 20. Acceptance test for mutation behavior

Implementation is mutation-contract compliant when this scenario passes:

```text
1. Create SOURCE-001 + REV-001.
2. Start RUN-001; runtime_ref attached after start.
3. Start PARSE execution and pin REV-001 exact hash.
4. Register OUTSET-A in deterministic SLOT-CHUNK-REV001.
5. Rerun parse → OUTSET-B in same OutputSlot.
6. Select OUTSET-B → BASELINE-001 / head lock_version=1.
7. Start downstream execution using BASELINE binding.
   StageInput pins BASELINE-001 + OUTSET-B + bundle resolved_hash.
8. Select OUTSET-A → BASELINE-002 / head lock_version=2.
9. Historical downstream StageInput remains unchanged and is now stale relative to head.
10. Create PUB-001 from accepted exact baseline/output.
11. Materialize + verify + activate PUB-001.
12. New SourceRevision publishes PUB-002 in same PublicationScope.
13. PUB-002 ACTIVE; PUB-001 SUPERSEDED.
14. Failed new execution/publication never destroys previous baseline/publication history.
```

If a service cannot state exactly which mutation in this document it performs, its database responsibility is not yet sufficiently defined.