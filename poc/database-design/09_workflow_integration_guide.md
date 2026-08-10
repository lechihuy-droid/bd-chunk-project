# ReqKB Database Integration Guide for a Real Workflow

**Status:** POC implementation handoff  
**Audience:** Coding agent / backend developer / workflow implementer / architect  
**Scope:** Cách áp dụng database design generic trong folder này vào **workflow và Web App thực tế nằm ở module/repo khác**  
**Depends on:** `02_storage_boundary.md`, `03_logical_data_model.md`, `04_physical_schema.md`, `05_implementation_guide.md`, `06_data_flow.md`, `07_data_mutation_spec.md`, `08_data_dictionary.md`

---

## 1. Mục tiêu

Database package này cố ý **không encode workflow business cụ thể**.

Các flow trong `06_data_flow.md` chỉ giải thích lifecycle tổng quát:

```text
SourceRevision
→ ProcessingRun
→ StageExecution
→ OutputSet candidate
→ BaselineSelection
→ Publication
```

Chúng **không phải** source of truth cho:

```text
node nào tồn tại
node chạy theo thứ tự nào
node nào parallel
node nào loop/retry
human gate nằm ở đâu
artifact thật tên gì
stage_type thật là gì
artifact_role thật là gì
API/UI action thật là gì
```

Các thông tin đó phải lấy từ **workflow/app thực tế**.

Tài liệu này hướng dẫn coding agent cách đi từ:

```text
REAL WORKFLOW / REAL APP
        ↓
workflow inventory
        ↓
database mapping
        ↓
gap analysis
        ↓
implementation contract
        ↓
code + migration only if required
```

---

## 2. Nguyên tắc quan trọng nhất

> Không sửa database để “giống workflow” trước khi chứng minh workflow thật không map được vào model generic hiện tại.

Database model hiện tại cố ý generic:

```text
stage name          → stage_execution.stage_type
runtime node id     → runtime_ref / component_ref as appropriate
artifact type       → output_slot.artifact_role
candidate revision  → output_set
artifact files      → stored_object
exact dependency    → stage_input
accepted candidate  → baseline_selection / baseline_head
published result    → publication / publication_head
```

Do đó khi workflow thật có node mới, **không tạo table mới theo node name**.

Ví dụ sai:

```text
parser_execution
validator_execution
ontology_execution
reviewer_execution
```

Mặc định đúng:

```text
stage_execution
  stage_type = <real capability type>
```

Chỉ thay logical/physical schema nếu có requirement mới mà model hiện tại không biểu diễn được mà không phá invariant.

---

## 3. Source-of-truth khi tích hợp workflow thật

Trước khi map database, coding agent phải xác định source thật của workflow/app.

Ưu tiên đọc theo thứ tự:

```text
1. executable workflow definition / graph / workflow config
2. application command/service code hoặc API contract đang được dùng
3. artifact/data contracts, Pydantic models, schemas
4. human review / approval / publish rules
5. runtime persistence / checkpoint configuration
6. workflow documentation
7. overview diagrams / presentation
```

Nếu overview trong database package mâu thuẫn với workflow executable:

```text
workflow executable wins for workflow behavior
```

Nhưng workflow code **không được tự thay đổi** database invariants như:

```text
latest != baseline
runtime state != governance SoR
historical lineage is immutable
publication candidate invisible before activation
```

Khi có conflict giữa workflow behavior và database invariant, coding agent phải ghi thành **gap** để architect resolve; không silently weaken schema.

---

# 4. Phase A — Discover the real workflow first

Không bắt đầu bằng ERD/table mapping.

Trước tiên lập inventory workflow thật.

## 4.1 Workflow inventory

Với mỗi node/capability/action, ghi:

| Field | Câu hỏi |
|---|---|
| `workflow_step` | Tên node/action thật là gì? |
| `trigger` | Cái gì làm step chạy? |
| `inputs` | Step đọc data/artifact nào? |
| `outputs` | Step tạo data/artifact nào? |
| `durable_output` | Output có cần tồn tại sau restart/replay không? |
| `business_significant` | Kết quả execution có cần audit/lineage không? |
| `parallelism` | Có chạy parallel với step khác không? |
| `retry` | Retry cùng execution hay tạo attempt mới? |
| `loop` | Có revision/rework loop không? |
| `interrupt` | Có human interrupt/review không? |
| `selection` | Có chọn một candidate làm accepted/current không? |
| `publication` | Có đưa result vào ReqKB/serving layer không? |

### Coding-agent output bắt buộc

Tạo một bảng `REAL WORKFLOW INVENTORY` trước khi đề xuất bất kỳ schema change nào.

---

## 4.2 Không phải mọi workflow node đều là StageExecution

Tạo `StageExecution` khi step là một **durable business-capability execution** mà provenance/result của nó cần được truy vết.

Thông thường **có StageExecution** nếu step:

```text
calls model/tool/parser/converter/validator
transforms governed data
produces candidate artifact
produces audit-relevant decision/evidence
must be replayed/traced to exact inputs
```

Thông thường **không cần StageExecution** nếu node chỉ:

```text
route conditional edge
fan-out/fan-in control only
format runtime-local value
copy runtime state without durable semantic effect
check whether another node should run
```

Decision rule:

```text
Nếu bỏ record execution này mà vẫn reconstruct được business lineage đầy đủ
→ có thể chỉ để runtime state.

Nếu bỏ record này làm mất khả năng biết ai/cái gì đã biến input nào thành output nào
→ cần StageExecution.
```

---

# 5. Phase B — Classify every real data object

Với mỗi object/value trong workflow thật, phân loại trước khi chọn table.

## 5.1 Classification rule

```text
Raw source uploaded/imported?
→ SourceAsset + SourceRevision + Object Store

Runtime-only temporary value?
→ runtime state only

Durable produced payload/evidence?
→ Object Store
→ register as StoredObject if part of governed OutputSet

Stable logical family of candidate artifacts?
→ OutputSlot

One produced candidate bundle/revision?
→ OutputSet

Exact durable input consumed by a business execution?
→ StageInput

Accepted/current candidate decision?
→ BaselineSelection + BaselineHead

Published semantic knowledge?
→ Publication + Neo4j

Trace/evaluation only?
→ MLflow later; keep minimum replay-critical references in Catalog DB
```

---

## 5.2 Ephemeral vs durable data

Không persist tất cả LangGraph state vào Catalog DB.

Ví dụ runtime-only:

```text
next_node
temporary routing flag
UI progress percentage
transient model scratch state
retry counter internal to runtime
```

Ví dụ durable/governed:

```text
exact source revision
normalized document artifact
validated requirement bundle
design candidate
review evidence required for governance
baseline decision
publication manifest
```

Rule:

> Persistence phải theo business recovery/audit requirement, không theo việc field đó có tồn tại trong runtime State hay không.

---

# 6. Phase C — Map the real workflow to the generic DB model

Sau inventory/classification mới lập mapping.

## 6.1 Core mapping table

| Real workflow concept | Generic database concept | Mapping rule |
|---|---|---|
| One user/system invocation of a workflow | `ProcessingRun` | Một correlation container cho invocation đó |
| Durable capability execution | `StageExecution` | Một execution fact; `stage_type` lấy từ workflow capability |
| Exact SourceRevision consumed | `StageInput` DIRECT | Pin exact `source_revision_id` + hash |
| Exact upstream candidate consumed directly | `StageInput` DIRECT | Pin exact `output_set_id` + deterministic bundle hash |
| Current accepted upstream candidate consumed | `StageInput` BASELINE | Pin cả `output_set_id` và `source_baseline_selection_id` |
| Stable artifact family for same source scope | `OutputSlot` | Deterministic identity by role + source scope |
| One result candidate / rerun result | `OutputSet` | New candidate in same slot |
| Files/JSON/Excel/evidence in candidate | `StoredObject` | Immutable object registry |
| User/policy selects accepted candidate | `BaselineSelection` | Append-only decision |
| Current accepted candidate pointer | `BaselineHead` | Mutable CAS pointer |
| Stable semantic publish stream | `PublicationScope` | KnowledgeSpace + SourceAsset + role |
| One publish attempt | `Publication` | Immutable-ish lifecycle record |
| Current active semantic version | `PublicationHead` | Mutable CAS pointer |
| Runtime checkpoint / interrupt | none in Catalog DB | Runtime owns it |

---

## 6.2 Do not create baseline for every stage automatically

`Baseline` là governance concept, không phải synonym của “latest output”.

Một OutputSlot cần Baseline khi downstream/business cần biết:

> Trong nhiều candidate của artifact này, candidate nào đang được chấp nhận làm current input/truth?

Không bắt buộc baseline nếu output:

```text
pure technical intermediate
single-use ephemeral transform
never independently selected/reviewed
never acts as governed current input
```

Nếu workflow thật tự động chạy A → B và A không có selection semantics, B có thể consume exact `OutputSet` bằng DIRECT binding.

Nếu user/reviewer/policy phải chọn candidate A trước khi B chạy, B nên dùng BASELINE binding.

---

## 6.3 Do not create OutputSlot per execution

Workflow node name hoặc execution ID không phải OutputSlot identity.

Correct question:

> Các rerun này có đang tạo candidate mới cho cùng một logical artifact scope không?

Nếu có:

```text
same OutputSlot
new OutputSet
```

Nếu source scope hoặc artifact role thực sự đổi:

```text
new OutputSlot
```

---

# 7. Phase D — Build a workflow-specific integration map

Workflow-specific mapping **nên nằm cạnh workflow/app thật**, không nhét stage names vào generic database package.

Recommended file:

```text
<real-workflow-or-app>/docs/database_integration.md
```

Tài liệu đó phải có tối thiểu 4 bảng dưới đây.

---

## 7.1 Table A — Workflow Step Mapping

Template:

| Real step/node | Persist execution? | `stage_type` | Inputs | Output artifact role | Baseline required? | Publish? |
|---|---:|---|---|---|---:|---:|
| `<real node>` | Yes/No | `<value>` | `<exact types>` | `<artifact_role>` | Yes/No | Yes/No |

Rules:

- dùng **real node/capability names** từ workflow source;
- `stage_type` là controlled application value, không phải table name;
- nếu `Persist execution = No`, ghi lý do;
- không invent baseline/pub gate nếu workflow thật không có.

---

## 7.2 Table B — Artifact Registry

Template:

| `artifact_role` | Produced by | Source scope | Stored objects | Schema contract | Candidate semantics | Baseline? |
|---|---|---|---|---|---|---:|
| `<role>` | `<step>` | `<SourceRevision(s)>` | `<roles/files>` | `<schema ref>` | `<what makes reruns same series>` | Yes/No |

Phải định nghĩa rõ:

```text
artifact_role
canonical source scope
scope member ordering
required StoredObject roles
schema/version validation
```

Đây là input để implement deterministic `OutputSlot.scope_fingerprint`.

---

## 7.3 Table C — Real Action → Database Command Mapping

Template:

| Real app/workflow event | Application command | Reads | Writes | External side effect |
|---|---|---|---|---|
| User uploads revision | `RegisterSource` | source identity | SourceRevision | Object Store write |
| Workflow starts | `StartProcessing` | SourceRevision | ProcessingRun | runtime start |
| Capability begins | `StartStageExecution` | run + exact inputs | StageExecution + StageInput | runtime correlation |
| Capability finishes | `RegisterOutputSet` | execution + artifact contract | OutputSlot/OutputSet/StoredObject | Object Store |
| Accepted candidate chosen | `SelectBaseline` | OutputSet + BaselineHead | BaselineSelection/Head | none |
| Approved semantic result published | `PublishOutput` | baseline/publication scope | Publication/Head | Neo4j |

Tên event bên trái phải thay bằng **event thật của app**.

Mutation behavior chi tiết không copy lại; reference `07_data_mutation_spec.md`.

---

## 7.4 Table D — Gap / Extension Register

Mỗi concept không map sạch vào schema hiện tại phải ghi:

| Gap | Why current model cannot express it | POC blocker? | Proposed change | ADR? |
|---|---|---:|---|---:|
| `<gap>` | `<reason>` | Yes/No | `<change>` | Yes/No |

Không sửa DDL trước khi bảng này được review.

---

# 8. Phase E — Gap analysis: when is a schema change justified?

Dùng decision tree này.

```text
Can real workflow concept map to existing entity/field without changing meaning?
  ├─ YES → map it; no schema change
  │
  └─ NO
      ↓
Is it runtime-only / UI-only / observability-only?
  ├─ YES → keep outside Catalog DB
  │
  └─ NO
      ↓
Is it a new durable business identity, lineage relation, governance state,
or publication consistency requirement?
  ├─ NO → application/config change may be enough
  │
  └─ YES
      ↓
Document gap → review Gate A/B/C → migration → ADR if hard-to-reverse
```

---

## 8.1 Known extension triggers already anticipated

### New durable StageInput target types

Current POC supports:

```text
SourceRevision
OutputSet
```

If workflow thật needs 3–4+ durable resource types repeatedly, revisit ADR-002 and consider resource supertype/registry.

### Review Inbox / assignment workflow

If app thật has persisted review queue, assignment, SLA, escalation:

```text
ReviewRequest
ReviewDecision
```

may move from conditional to implemented tables.

### Whole-KB reproducible release

If publication must atomically represent a snapshot across many SourceAssets:

```text
KnowledgeRelease
```

may become required. Current `PublicationScope` is per stable source stream, not whole-KB release.

### High concurrency / multi-writer

If real app exceeds SQLite assumptions:

```text
few concurrent writers
short transactions
single backend-ish POC
```

migrate CatalogRepository to PostgreSQL; do not redesign domain identity just because storage engine changes.

### Multiple runtime providers simultaneously

Provider-qualified `runtime_ref` is sufficient for simple switching.

If real app must query/filter/manage hybrid LangGraph + Prefect providers concurrently at scale, consider materialized runtime-provider metadata via migration/ADR.

---

# 9. Example mapping — illustrative only, not the real workflow spec

Ví dụ giả định workflow thật có:

```text
extract
→ quality_check
→ human approve
→ semantic_publish
```

Đây chỉ minh họa cách map.

| Real step | DB mapping | Why |
|---|---|---|
| `extract` | StageExecution + OutputSet | transforms source into durable candidate |
| pure route after extract | runtime only | no independent business lineage |
| `quality_check` | StageExecution if result/evidence needs trace | capability execution is audit-relevant |
| human approve | BaselineSelection / BaselineHead | chooses accepted candidate; not merely runtime success |
| `semantic_publish` | Publication + Neo4j materialization | changes published semantic serving state |

Nếu workflow thật không có `human approve`, không thêm gate này chỉ vì example có.

---

# 10. Runtime-specific implementation without database coupling

## 10.1 LangGraph current POC

Workflow-specific adapter có thể map:

```text
LangGraph graph invocation
→ ProcessingRun.runtime_ref

business-capability node execution
→ StageExecution

interrupt for human decision
→ runtime checkpoint/interrupt

committed governance decision
→ Catalog DB BaselineSelection/Publication
```

Important ordering khi human decision có business effect:

```text
1. commit governance decision in Catalog DB
2. then resume LangGraph
```

Nếu resume fail, governance fact không rollback.

---

## 10.2 Prefect later

Khi swap runtime:

```text
real workflow mapping
→ same ProcessingRun / StageExecution / StageInput / OutputSet model
```

Chỉ runtime adapter/config thay nếu business semantics không đổi.

Nếu Prefect migration làm đổi retry/attempt semantics theo cách ảnh hưởng provenance, ghi gap và review trước.

---

# 11. Integration implementation order for a real app

Coding agent nên thực hiện theo thứ tự:

```text
STEP 1  Locate real workflow + app sources
STEP 2  Produce REAL WORKFLOW INVENTORY
STEP 3  Classify every durable vs runtime-only object
STEP 4  Produce Workflow Step Mapping
STEP 5  Produce Artifact Registry
STEP 6  Produce Real Action → DB Command Mapping
STEP 7  Produce Gap / Extension Register
STEP 8  Architect resolves only genuine gaps
STEP 9  Apply existing 001 schema or new migration if approved
STEP 10 Implement repository/application commands
STEP 11 Wire real workflow nodes through application commands
STEP 12 Run acceptance scenarios on actual workflow
```

Do not start STEP 9 before STEP 7 is empty or explicitly resolved.

---

# 12. Workflow-specific acceptance tests

Sau khi map workflow thật, ít nhất verify:

### Traceability

Từ một output trong app phải trace được:

```text
OutputSet
→ producer StageExecution
→ exact StageInput(s)
→ upstream OutputSet / SourceRevision
```

### Rerun

Rerun cùng real artifact scope:

```text
same OutputSlot
new OutputSet
old OutputSet preserved
```

### Parallel execution

Hai real workflow steps chạy parallel không overwrite candidate/history của nhau.

### Retry

Retry behavior phải rõ:

```text
same StageExecution retry internally?
or new StageExecution attempt?
```

Chọn rule theo workflow requirement và document trong workflow-specific mapping; không để runtime default vô tình định nghĩa business provenance.

### Human gate

Nếu có approval:

```text
runtime interrupt != approval truth
```

Approval truth phải ở Catalog governance record tương ứng.

### Restart/recovery

Restart Web App/runtime không làm mất:

```text
source identity
artifact registry
exact lineage
baseline history
publication history
```

### Publication failure

Failure khi materialize real Neo4j candidate phải giữ previous active publication.

---

# 13. What must remain generic vs workflow-specific

## Keep in `poc/database-design/`

```text
entity model
physical schema
storage ownership
mutation semantics
field semantics
generic data lifecycle
runtime adapter boundary
migration rules
```

## Keep beside the real workflow/app

```text
real node names
real graph edges
parallel/loop topology
real stage_type registry
artifact_role registry
artifact schema contracts
which stages require baseline
human gate positions
real API/UI events
workflow-specific retry semantics
workflow-specific mapping tables
```

Reason:

> Database design should survive workflow refactoring; workflow integration mapping should change when the actual graph changes.

---

# 14. Coding-agent checklist before implementation

- [ ] I read the executable/actual workflow, not only `06_data_flow.md`.
- [ ] I identified control-only nodes vs durable business-capability executions.
- [ ] I classified runtime-only values separately from durable governed artifacts.
- [ ] Every persisted StageExecution has exact StageInputs.
- [ ] I defined stable `artifact_role` and source scope for each governed artifact family.
- [ ] Reruns reuse OutputSlot when logical scope is unchanged.
- [ ] I did not add BaselineHead simply to represent “latest”.
- [ ] Human/policy selection semantics are explicit where baseline is used.
- [ ] Publication points come from the real business workflow.
- [ ] I created a Gap Register before proposing schema changes.
- [ ] New schema changes include migration and rationale; ADR only when decision threshold is met.
- [ ] Workflow-specific names/config stay outside the generic DB model.

---

# 15. Final rule

When integrating a new real workflow, ask in this order:

```text
What does the real workflow actually do?
        ↓
Which executions/data are business-significant and durable?
        ↓
How do they map to existing generic entities?
        ↓
What exact commands mutate the database?
        ↓
Is there any genuine model gap?
        ↓
Only then change schema/code.
```

Do **not** ask:

```text
“How do I make the database look like this graph?”
```

The target is:

```text
workflow-specific execution
        +
stable workflow-agnostic governance model
```

not a database schema that mirrors the current graph topology.