# ReqKB Data Dictionary

**Status:** POC implementation reference  
**Audience:** Coding agent / backend developer / reviewer  
**Scope:** Ý nghĩa field, nguồn giá trị, mutability và example cho physical schema trong `04_physical_schema.md`  
**Depends on:** `03_logical_data_model.md`, `04_physical_schema.md`, `07_data_mutation_spec.md`

---

## 1. Purpose

`04_physical_schema.md` là source of truth cho DDL/constraint. File này gom field semantics để coding agent không phải suy diễn từ nhiều tài liệu.

Notation:

```text
CREATE-ONLY  = không rewrite sau khi entity/fact được tạo hợp lệ
LIFECYCLE    = được update theo state transition đã định nghĩa
POINTER      = mutable current pointer, phải concurrency-protected
DISPLAY      = mutable/non-critical display metadata nếu application cho phép
```

Nếu dictionary và DDL conflict về type/nullability/constraint, **`04_physical_schema.md` + executable migration thắng**, sau đó dictionary phải được sửa cho đồng bộ.

---

## 2. Global conventions

| Convention | Contract |
|---|---|
| ID | Opaque application-generated UUID-compatible string stored as `TEXT` in SQLite |
| Timestamp | RFC3339 UTC `TEXT`; PostgreSQL main maps to `timestamptz` |
| Hash | Opaque canonical hash string; algorithm/version should be consistently encoded by application |
| Runtime ref | Provider-qualified opaque ref, e.g. `langgraph:<id>` / `prefect:<id>` |
| Workspace | Mandatory ownership/isolation root |
| History records | Append-only unless explicitly lifecycle state |
| Current pointer | `BaselineHead` / `PublicationHead`, never inferred from newest row |

---

# 3. `workspace`

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `workspace_id` | Yes | CREATE-ONLY | application ID generator | Isolation/project root ID |
| `name` | Yes | DISPLAY | user/application | Human-readable workspace name |
| `created_at` | Yes | CREATE-ONLY | application clock | Creation time |

---

# 4. `source_asset`

Stable business identity of a source/document across revisions.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `source_asset_id` | Yes | CREATE-ONLY | application ID generator | Stable source identity |
| `workspace_id` | Yes | CREATE-ONLY | command / workspace context | Owning workspace |
| `logical_name` | Yes | DISPLAY | user/application | Display name; **not identity / not unique resolver** |
| `created_at` | Yes | CREATE-ONLY | application clock | Creation time |

**Important:** revision upload for an existing source must use exact `source_asset_id`; do not infer by filename/logical name.

---

# 5. `source_revision`

Immutable content revision of one SourceAsset.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `source_revision_id` | Yes | CREATE-ONLY | application ID generator | Exact revision identity |
| `workspace_id` | Yes | CREATE-ONLY | SourceAsset.workspace_id | Ownership anchor |
| `source_asset_id` | Yes | CREATE-ONLY | exact selected SourceAsset | Parent stable source |
| `content_hash` | Yes | CREATE-ONLY | raw payload hash | Exact content identity |
| `raw_object_ref` | Yes | CREATE-ONLY | Object Store adapter | Canonical raw object location/reference |
| `revision_reason` | No | CREATE-ONLY | user/application | Why revision was registered |
| `created_at` | Yes | CREATE-ONLY | application clock | Registration time |

Uniqueness: same `source_asset_id + content_hash` is same content revision in current POC semantics.

---

# 6. `processing_run`

Workflow invocation/correlation container. Not artifact/baseline identity.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `processing_run_id` | Yes | CREATE-ONLY | application ID generator | Business run/correlation ID |
| `workspace_id` | Yes | CREATE-ONLY | command context | Owning workspace |
| `runtime_ref` | No | LIFECYCLE | WorkflowRuntimePort | Runtime correlation only |
| `status` | Yes | LIFECYCLE | application/runtime lifecycle | `PENDING/RUNNING/SUCCEEDED/FAILED/CANCELLED` |
| `started_at` | No | LIFECYCLE | application clock | Time runtime successfully starts |
| `completed_at` | No | LIFECYCLE | application clock | Terminal time |
| `created_at` | Yes | CREATE-ONLY | application clock | Record creation time |

`runtime_ref` is never the sole identity of business history.

---

# 7. `stage_execution`

One concrete execution attempt of one processing capability.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `stage_execution_id` | Yes | CREATE-ONLY | application ID generator | Execution-attempt ID |
| `workspace_id` | Yes | CREATE-ONLY | ProcessingRun.workspace_id | Ownership anchor |
| `processing_run_id` | Yes | CREATE-ONLY | command | Parent workflow run |
| `stage_type` | Yes | CREATE-ONLY | workflow/capability config | Capability type; data, not table name |
| `component_ref` | Yes | CREATE-ONLY | component registry/config | Exact implementation/component reference |
| `configuration_hash` | Yes | CREATE-ONLY | canonical runtime config | Reproducibility/config fingerprint |
| `schema_contract_ref` | No | CREATE-ONLY | capability config | Input/output contract reference |
| `runtime_ref` | No | LIFECYCLE | runtime adapter | Stage/runtime correlation ref |
| `status` | Yes | LIFECYCLE | application/runtime lifecycle | `PENDING/RUNNING/SUCCEEDED/FAILED/CANCELLED` |
| `model_ref` | No | CREATE-ONLY | AI stage config | Model/provider/version reference |
| `prompt_ref` | No | CREATE-ONLY | AI stage config | Prompt/template reference |
| `ruleset_ref` | No | CREATE-ONLY | rules/config | Rule set reference |
| `trace_ref` | No | LIFECYCLE | observability adapter | MLflow/trace reference if available |
| `started_at` | No | LIFECYCLE | application clock | Execution start |
| `completed_at` | No | LIFECYCLE | application clock | Terminal time |
| `created_at` | Yes | CREATE-ONLY | application clock | Record creation |

After execution starts, producer/config/input facts must not be rewritten to look like a different execution.

---

# 8. `stage_input`

Exact immutable input binding consumed by StageExecution.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `stage_input_id` | Yes | CREATE-ONLY | application ID generator | Binding ID |
| `workspace_id` | Yes | CREATE-ONLY | StageExecution.workspace_id | Ownership anchor |
| `stage_execution_id` | Yes | CREATE-ONLY | current execution | Consumer execution |
| `input_role` | Yes | CREATE-ONLY | capability contract | Semantic role, e.g. `PRIMARY_DOCUMENT` |
| `binding_mode` | Yes | CREATE-ONLY | input resolver | `DIRECT` or `BASELINE` |
| `source_revision_id` | Conditional | CREATE-ONLY | exact direct source input | Set only for SourceRevision target |
| `output_set_id` | Conditional | CREATE-ONLY | exact direct/baseline output | Set only for OutputSet target |
| `source_baseline_selection_id` | Conditional | CREATE-ONLY | Baseline resolver | Required when `binding_mode=BASELINE` |
| `resolved_hash` | Yes | CREATE-ONLY | input resolver | Exact consumed content hash |
| `ordinal` | Yes | CREATE-ONLY | capability resolver | Stable position within `input_role` |

Exactly one target:

```text
source_revision_id XOR output_set_id
```

For OutputSet `resolved_hash`, use deterministic bundle hash over ordered `(object_role, ordinal, content_hash)` members.

---

# 9. `output_slot`

Stable logical artifact series identity; reruns add candidates to same slot.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `output_slot_id` | Yes | CREATE-ONLY | application ID generator | Artifact-series ID |
| `workspace_id` | Yes | CREATE-ONLY | producer context | Owning workspace |
| `artifact_role` | Yes | CREATE-ONLY | capability/output contract | Logical artifact type/role |
| `scope_fingerprint` | Yes | CREATE-ONLY | scope resolver | Deterministic hash of canonical source scope |
| `logical_name` | No | DISPLAY | application | Human-readable label only |
| `created_at` | Yes | CREATE-ONLY | application clock | Creation time |

Identity uniqueness:

```text
workspace_id + artifact_role + scope_fingerprint
```

---

# 10. `output_slot_scope_member`

Exact SourceRevision membership defining OutputSlot source scope.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `output_slot_id` | Yes | CREATE-ONLY | resolved OutputSlot | Parent artifact series |
| `workspace_id` | Yes | CREATE-ONLY | OutputSlot.workspace_id | Ownership anchor |
| `source_revision_id` | Yes | CREATE-ONLY | producer source scope | Exact source revision member |
| `scope_role` | Yes | CREATE-ONLY | capability/output scope contract | Semantic role of source member |
| `ordinal` | Yes | CREATE-ONLY | normalized scope | Stable ordering/discriminator |

These rows freeze with OutputSlot identity.

---

# 11. `output_set`

One candidate coherent result produced by one StageExecution for one OutputSlot.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `output_set_id` | Yes | CREATE-ONLY | application ID generator | Candidate result ID |
| `workspace_id` | Yes | CREATE-ONLY | producer workspace | Ownership anchor |
| `output_slot_id` | Yes | CREATE-ONLY | deterministic slot resolver | Artifact series |
| `producer_execution_id` | Yes | CREATE-ONLY | StageExecution | Exact producer |
| `integrity_status` | Yes | LIFECYCLE | registration/integrity service | `REGISTERING/VERIFIED/INVALID` |
| `schema_validation_status` | Yes | LIFECYCLE | schema validator | `PENDING/PASSED/FAILED` |
| `schema_version` | No | CREATE-ONLY | output contract/artifact | Logical schema version |
| `registration_completed_at` | No | LIFECYCLE | registration service | Registration terminal time |
| `created_at` | Yes | CREATE-ONLY | application clock | Candidate creation time |

No `is_baseline`, `latest`, or `final` column. Baseline is separate governance state.

---

# 12. `stored_object`

Registry for immutable payload held in Object Store.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `stored_object_id` | Yes | CREATE-ONLY | application ID generator | Registry object ID |
| `workspace_id` | Yes | CREATE-ONLY | OutputSet.workspace_id | Ownership anchor |
| `output_set_id` | Yes | CREATE-ONLY | current OutputSet | Parent bundle |
| `object_role` | Yes | CREATE-ONLY | output contract/config | Semantic file/object role |
| `ordinal` | Yes | CREATE-ONLY | producer/contract | Allows multiple objects per role |
| `object_uri` | Yes | CREATE-ONLY after registration | Object Store adapter | Immutable payload reference |
| `content_hash` | Yes | CREATE-ONLY after registration | integrity service | Exact object hash |
| `schema_version` | No | CREATE-ONLY | artifact/contract | Object schema version |
| `media_type` | No | CREATE-ONLY | producer/object metadata | MIME/media type |
| `is_required` | Yes | CREATE-ONLY | current application output contract | Whether object blocks OutputSet eligibility |
| `integrity_status` | Yes | LIFECYCLE | integrity service | `WRITING/WRITTEN/VERIFIED/AVAILABLE/INVALID` |
| `size_bytes` | No | CREATE-ONLY after verification | Object Store metadata | Payload size |
| `created_at` | Yes | CREATE-ONLY | application clock | Registry creation time |

Current POC normally registers after object verification and therefore commonly inserts status `AVAILABLE`.

---

# 13. `baseline_selection`

Append-only decision selecting exact OutputSet for one OutputSlot.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `baseline_selection_id` | Yes | CREATE-ONLY | application ID generator | Selection event ID |
| `workspace_id` | Yes | CREATE-ONLY | OutputSlot.workspace_id | Ownership anchor |
| `output_slot_id` | Yes | CREATE-ONLY | command | Governed artifact series |
| `output_set_id` | Yes | CREATE-ONLY | command | Exact selected candidate |
| `previous_baseline_selection_id` | No | CREATE-ONLY | current BaselineHead at selection time | History chain |
| `selection_mode` | Yes | CREATE-ONLY | command/policy | `AUTO/AI_RECOMMEND/HUMAN` |
| `review_decision_id` | No | CREATE-ONLY | optional Review capability | Review evidence reference |
| `selection_reason` | No | CREATE-ONLY | actor/policy | Human/policy rationale |
| `selected_by` | Yes | CREATE-ONLY | actor/policy reference | Who/what selected candidate |
| `selected_at` | Yes | CREATE-ONLY | application clock | Decision time |

Never update old selection to represent current baseline.

---

# 14. `baseline_head`

Current baseline pointer and optimistic concurrency anchor.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `output_slot_id` | Yes | CREATE-ONLY key | governed OutputSlot | One head per slot |
| `workspace_id` | Yes | CREATE-ONLY | OutputSlot.workspace_id | Ownership anchor |
| `current_baseline_selection_id` | Yes | POINTER | SelectBaseline transaction | Current selection |
| `lock_version` | Yes | POINTER | DB/application CAS | Optimistic concurrency version, starts at 1 |
| `updated_at` | Yes | POINTER | application clock | Last pointer change |

Only SelectBaseline transaction may move this pointer.

---

# 15. `knowledge_space`

Logical ReqKB publication target.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `knowledge_space_id` | Yes | CREATE-ONLY | application ID generator | Knowledge target ID |
| `workspace_id` | Yes | CREATE-ONLY | workspace context | Owner |
| `name` | Yes | DISPLAY | user/application | Display name |
| `status` | Yes | LIFECYCLE | application/admin | `ACTIVE/DISABLED` |
| `created_at` | Yes | CREATE-ONLY | application clock | Creation time |

---

# 16. `publication_scope`

Stable publication stream across SourceRevision changes.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `publication_scope_id` | Yes | CREATE-ONLY | application ID generator | Stable publication stream ID |
| `workspace_id` | Yes | CREATE-ONLY | KnowledgeSpace.workspace_id | Ownership anchor |
| `knowledge_space_id` | Yes | CREATE-ONLY | Publish command | Target knowledge space |
| `source_asset_id` | Yes | CREATE-ONLY | Publish command | Stable source identity |
| `publication_role` | Yes | CREATE-ONLY | publication policy/config | Semantic publication role |
| `scope_key` | No | DISPLAY/CREATE-ONLY by app policy | application | Optional integration/display key |
| `created_at` | Yes | CREATE-ONLY | application clock | Creation time |

Unique business stream:

```text
knowledge_space_id + source_asset_id + publication_role
```

---

# 17. `publication`

Publication attempt/history for one exact accepted OutputSet.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `publication_id` | Yes | CREATE-ONLY | application ID generator | Publication attempt ID |
| `workspace_id` | Yes | CREATE-ONLY | PublicationScope.workspace_id | Ownership anchor |
| `publication_scope_id` | Yes | CREATE-ONLY | resolved scope | Stable publication stream |
| `output_slot_id` | Yes | CREATE-ONLY | accepted baseline | Exact artifact series |
| `baseline_selection_id` | Yes | CREATE-ONLY | accepted baseline | Exact governance decision |
| `output_set_id` | Yes | CREATE-ONLY | BaselineSelection | Exact selected candidate |
| `previous_publication_id` | No | CREATE-ONLY | current PublicationHead at creation | Prior active publication in same scope |
| `status` | Yes | LIFECYCLE | PublicationService | `PENDING/MATERIALIZING/VERIFIED/ACTIVE/FAILED/SUPERSEDED` |
| `manifest_object_ref` | No | LIFECYCLE then freeze | Object Store | Immutable publication manifest ref |
| `created_at` | Yes | CREATE-ONLY | application clock | Publication attempt creation |
| `activated_at` | No | LIFECYCLE then freeze | activation transaction clock | Time it became active |

Pinned source references must not change after materialization starts.

---

# 18. `publication_head`

Current active publication pointer for one PublicationScope.

| Field | Required | Mutability | Source | Meaning |
|---|---:|---|---|---|
| `publication_scope_id` | Yes | CREATE-ONLY key | PublicationScope | One head per stable stream |
| `workspace_id` | Yes | CREATE-ONLY | PublicationScope.workspace_id | Ownership anchor |
| `current_publication_id` | Yes | POINTER | activation transaction | Current active Publication |
| `lock_version` | Yes | POINTER | DB/application CAS | Optimistic concurrency version |
| `updated_at` | Yes | POINTER | application clock | Last activation change |

Only publication activation flow may move this pointer.

---

# 19. Derived values — not canonical columns

Do **not** add these as mutable source-of-truth fields in POC:

### Current baseline

Derived by:

```text
BaselineHead
→ BaselineSelection
→ OutputSet
```

### OutputSet baseline eligibility

Derived from:

```text
registration_completed_at
+ output_set.integrity_status
+ schema_validation_status
+ required StoredObject integrity
```

### Stale downstream artifact

Derived by comparing:

```text
StageInput.source_baseline_selection_id
vs
current upstream BaselineHead.current_baseline_selection_id
```

### Current publication

Derived by:

```text
PublicationScope
→ PublicationHead
→ ACTIVE Publication
```

### OutputSet resolved hash

Derived from immutable StoredObject members:

```text
HASH(sorted(object_role, ordinal, content_hash))
```

---

# 20. Status transition reference

## ProcessingRun / StageExecution

```text
PENDING → RUNNING → SUCCEEDED
                  ↘ FAILED
                  ↘ CANCELLED
```

## StoredObject

```text
WRITING → WRITTEN → VERIFIED → AVAILABLE
                    ↘ INVALID
```

## OutputSet

```text
REGISTERING → VERIFIED
           ↘ INVALID
```

Schema validation:

```text
PENDING → PASSED
       ↘ FAILED
```

## Publication

```text
PENDING → MATERIALIZING → VERIFIED → ACTIVE → SUPERSEDED
                       ↘ FAILED
```

A failed publication before ACTIVE must not move PublicationHead.

---

# 21. Fields coding agent must never infer incorrectly

| Field | Wrong inference | Correct source |
|---|---|---|
| `source_asset_id` | filename/logical_name | exact existing source ID or new ID |
| `output_slot_id` | current run ID | deterministic slot lookup by workspace + artifact_role + scope_fingerprint |
| `output_set_id` baseline input | newest output | exact BaselineSelection output |
| `source_baseline_selection_id` | current head after execution | selection resolved before execution begins |
| `resolved_hash` | arbitrary runtime state hash | exact SourceRevision content hash or deterministic OutputSet bundle hash |
| `current_baseline_selection_id` | max(selected_at) | BaselineHead pointer |
| `previous_publication_id` | newest Publication row | current PublicationHead at publication creation |
| `current_publication_id` | newest/VERIFIED publication | PublicationHead after successful activation |
| `runtime_ref` | business ID | runtime-only correlation ref |

---

# 22. Review rule

When a new field is proposed, review in this order:

```text
1. What business/runtime fact does it represent?
2. Who is canonical owner?
3. Is it immutable fact, lifecycle status, projection or current pointer?
4. Can it already be derived from canonical data?
5. Which command writes it?
6. Which invariant/constraint protects it?
7. Does adding it require logical-model/ADR change?
```

Do not add convenience columns that silently create a second source of truth.