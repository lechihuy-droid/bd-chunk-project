# ReqKB Ingestion Database Implementation Guide

**Status:** POC implementation baseline  
**Scope:** Application/service/repository structure để implement `04_physical_schema.md` trong Web App quản lý workflow  
**Depends on:** `01_design_methodology.md`, `02_storage_boundary.md`, `03_logical_data_model.md`, `04_physical_schema.md`  
**Related ADRs:** `adrs/ADR-001-publication-scope.md`, `adrs/ADR-002-stage-input-physical-reference.md`, `adrs/ADR-003-runtime-adapter-boundary.md`

---

## 1. Mục tiêu

Tài liệu này chốt cách triển khai database architecture trong application mà không làm persistence phụ thuộc trực tiếp vào workflow engine.

Current deployment context:

```text
User
  ↓
Web App
  ↓
Application API / Domain Services
  ├── Catalog DB
  ├── Object Store
  ├── ReqKB / Neo4j
  └── WorkflowRuntimePort
         └── LangGraph adapter   ← current POC
```

Future extension:

```text
WorkflowRuntimePort
  ├── LangGraph adapter
  └── Prefect adapter           ← optional replacement

ObservabilityPort
  └── MLflow adapter            ← future integration
```

Nguyên tắc chính:

> Web App và domain services quản lý business workflow state; LangGraph/Prefect quản lý execution runtime. MLflow quản lý experiment/trace/evaluation metadata. Không thành phần nào thay Catalog DB làm System of Record cho ingestion governance.

---

## 2. Implementation principles

### IP-01 — Web App là control plane

**Context:** user cần start workflow, xem progress, review artifact, approve baseline và publish từ một application thống nhất.

**Decision:** Web App gọi application commands; UI không gọi trực tiếp LangGraph, SQLite, Object Store hoặc Neo4j.

```text
UI
 ↓
Application Command
 ↓
Domain/Application Service
 ↓
Ports
 ├── CatalogRepository
 ├── ObjectStore
 ├── WorkflowRuntime
 └── KnowledgePublisher
```

**Rationale:** business invariant nằm một chỗ và không bị duplicate giữa UI, chatbot và runtime node.

**Trade-off:** thêm application/service layer nhưng giảm coupling đáng kể.

---

### IP-02 — Runtime framework nằm sau port

**Context:** POC dùng LangGraph nhưng main có thể dùng Prefect hoặc runtime khác nếu concurrency/operations requirement thay đổi.

**Decision:** application chỉ phụ thuộc `WorkflowRuntimePort`; LangGraph là adapter hiện tại.

**Rationale:** persistence và business command không phải rewrite khi đổi runtime.

**Trade-off:** chỉ expose common runtime capability; feature framework-specific không được leak vào domain API.

Decision chi tiết: `adrs/ADR-003-runtime-adapter-boundary.md`.

---

### IP-03 — MLflow là observability/evaluation integration

**Context:** AI stages sau này cần trace model/prompt/config, evaluation metrics và experiment comparison.

**Decision:** MLflow được tích hợp qua `ObservabilityPort`; Catalog DB vẫn giữ business provenance tối thiểu cần replay/audit.

Catalog DB giữ:

```text
model_ref
prompt_ref
ruleset_ref
configuration_hash
schema_contract_ref
trace_ref / experiment_ref
```

MLflow có thể giữ:

```text
trace spans
model parameters
prompt/model experiment metadata
evaluation metrics
artifact metrics
run comparison
```

**Rationale:** nếu MLflow bị xóa/rotate thì lineage, baseline và publication governance vẫn reconstruct được.

**Trade-off:** một số metadata tồn tại ở hai nơi dưới dạng reference; cần correlation ID chuẩn.

---

## 3. Recommended module structure

POC nên giữ code structure nhỏ nhưng ports rõ:

```text
app/
├── api/
│   ├── workflow_routes.py
│   ├── artifact_routes.py
│   └── review_routes.py
│
├── application/
│   ├── commands/
│   │   ├── start_processing.py
│   │   ├── register_output.py
│   │   ├── select_baseline.py
│   │   ├── resume_workflow.py
│   │   └── publish_output.py
│   └── queries/
│       ├── get_run.py
│       ├── get_lineage.py
│       ├── get_current_baseline.py
│       └── get_current_publication.py
│
├── domain/
│   ├── models.py
│   ├── invariants.py
│   └── errors.py
│
├── ports/
│   ├── catalog_repository.py
│   ├── object_store.py
│   ├── workflow_runtime.py
│   ├── knowledge_publisher.py
│   └── observability.py
│
├── adapters/
│   ├── persistence/
│   │   └── sqlite_catalog.py
│   ├── object_store/
│   │   └── filesystem_or_s3.py
│   ├── runtime/
│   │   └── langgraph_runtime.py
│   ├── knowledge/
│   │   └── neo4j_publisher.py
│   └── observability/
│       └── mlflow_adapter.py      # later
│
└── migrations/
    └── sqlite/
        └── 001_init.sql
```

Không cần chia thành microservice trong POC. Đây là **modular monolith boundary**, không phải distributed-service requirement.

---

## 4. CatalogRepository contract

Repository interface nên model business operation thay vì expose generic CRUD cho mọi table.

Ví dụ:

```python
class CatalogRepository(Protocol):
    def create_source_revision(...): ...
    def create_processing_run(...): ...
    def start_stage_execution(...): ...
    def record_stage_inputs(...): ...
    def register_output_set(...): ...
    def get_output_set(...): ...
    def select_baseline(...): ...
    def get_current_baseline(...): ...
    def create_publication(...): ...
    def activate_publication(...): ...
    def get_current_publication(...): ...
```

Không khuyến nghị:

```python
repo.insert(table, payload)
repo.update(table, payload)
```

vì business transaction như baseline CAS hoặc publication activation cần invariant vượt quá một row CRUD.

---

## 5. WorkflowRuntimePort

Application contract tối thiểu:

```python
class WorkflowRuntimePort(Protocol):
    def start(self, workflow_ref, input_ref, correlation_id): ...
    def resume(self, runtime_ref, command): ...
    def cancel(self, runtime_ref): ...
    def get_status(self, runtime_ref): ...
```

Optional capability chỉ thêm khi Web App thực sự cần:

```python
stream_events(...)
get_interrupt(...)
```

Không đưa vào port các concept framework-specific như:

```text
LangGraph StateGraph
LangGraph checkpoint tuple
Prefect Deployment
Prefect Work Pool
```

Các concept đó ở adapter/config layer.

---

## 6. LangGraph adapter — current POC

LangGraph là runtime hiện tại cho workflow execution và human interrupt/resume.

Mapping:

```text
Application concept       LangGraph
────────────────────────────────────────
ProcessingRun             graph invocation/thread
StageExecution            node/capability execution
runtime_ref               thread/run correlation
pause for review          interrupt()
resume                    graph resume
runtime checkpoint        checkpointer state
```

Quan trọng:

```text
LangGraph checkpoint ≠ Catalog DB business state
```

LangGraph node không được tự ý làm:

```text
UPDATE baseline_head
UPDATE publication_head
```

Node phải gọi application/domain command nếu cần thay governance state.

Ví dụ:

```text
LangGraph node completes parse
        ↓
RegisterOutputSet command
        ↓
CatalogRepository + ObjectStore
        ↓
returns output_set_id
        ↓
LangGraph state chỉ giữ reference
```

---

## 7. Prefect adapter — scale/operations option

Prefect chưa phải dependency bắt buộc của POC.

Nếu main cần switch:

```text
Web App
  ↓
WorkflowRuntimePort
  ↓
PrefectRuntimeAdapter
```

Database/domain contract không thay đổi:

```text
ProcessingRun
StageExecution
StageInput
OutputSet
Baseline
Publication
```

Prefect-specific concepts chỉ map trong adapter, ví dụ:

```text
runtime_ref → Prefect flow_run_id
stage runtime ref → task_run_id
retry/cancel/status → Prefect runtime operations
```

### Trigger hợp lý để xem xét Prefect

Không switch chỉ vì “Prefect mạnh hơn”. Re-evaluate khi có requirement thực tế như:

- nhiều worker/process cần scheduler/worker operational model riêng;
- workload non-agentic/data-heavy lớn hơn;
- deployment/scheduling/backfill trở thành requirement chính;
- operational monitoring/retry policy cần orchestration control plane độc lập;
- LangGraph runtime semantics không còn fit workload chính.

Switch runtime phải review bằng ADR nếu ảnh hưởng execution semantics hoặc operational architecture.

---

## 8. MLflow integration — later

MLflow integration nên nằm ngoài critical transaction path của baseline/publication.

Recommended flow:

```text
StageExecution starts
   ↓
Catalog DB records execution identity
   ↓
Runtime executes AI capability
   ↓
ObservabilityPort emits trace/metrics → MLflow
   ↓
OutputSet registered in Catalog DB/Object Store
   ↓
Catalog DB stores mlflow_run_ref / trace_ref if available
```

Nếu MLflow unavailable:

```text
workflow may continue
```

trừ khi một future policy explicitly yêu cầu evaluation result từ MLflow trước baseline.

Không dùng MLflow run ID làm primary identity của `StageExecution`.

---

## 9. Application command flows

### 9.1 Start processing

```text
POST /workspaces/{id}/runs
        ↓
StartProcessing command
        ↓
Catalog: create ProcessingRun
        ↓
WorkflowRuntimePort.start()
        ↓
Catalog: attach runtime_ref
        ↓
return processing_run_id
```

Nếu runtime start fail:

```text
ProcessingRun → FAILED_TO_START / FAILED
```

hoặc giữ `PENDING` + error record theo state model implementation; không delete run record.

---

### 9.2 Stage produces artifact

```text
Runtime stage
   ↓
write immutable payload → Object Store
   ↓
verify hash/schema
   ↓
RegisterOutputSet command
   ↓
Catalog transaction
   ├── resolve deterministic OutputSlot
   ├── register OutputSet
   ├── register StoredObjects
   └── mark integrity/registration complete
```

Runtime state chỉ giữ IDs returned từ application layer.

---

### 9.3 Baseline selection

```text
Web App / AI recommendation / policy
        ↓
SelectBaseline command
        ↓
validate eligibility
validate expected lock_version
        ↓
Catalog transaction
 ├── append BaselineSelection
 └── move BaselineHead
        ↓
return new baseline + lock_version
```

Nếu conflict:

```text
409 BASELINE_CONFLICT
```

UI reload current baseline và yêu cầu user/agent decide lại; không retry blind.

---

### 9.4 Resume workflow after review

```text
SelectBaseline succeeds
        ↓
ResumeWorkflow command
        ↓
WorkflowRuntimePort.resume(runtime_ref, decision_ref)
```

Thứ tự này quan trọng:

> Governance decision commit trước; runtime resume sau.

Nếu resume fail, baseline vẫn là valid business fact. Runtime có thể retry resume bằng idempotent command.

---

### 9.5 Publication

```text
PublishOutput command
  ↓
Catalog: create Publication PENDING
  ↓
KnowledgePublisher.materialize_candidate()
  ↓
verify
  ↓
Catalog transaction: activate Publication + move PublicationHead
  ↓
return publication_id
```

Neo4j visibility strategy vẫn phải tuân `SB-07` và ADR riêng trước production-grade G3.

---

## 10. Transaction ownership

### Catalog DB transaction

Application service/repository layer là owner của transaction.

Không để:

```text
UI transaction
LangGraph transaction
MLflow transaction
```

bao Catalog DB business transaction.

Các atomic transaction bắt buộc:

```text
BaselineSelection + BaselineHead CAS
Publication activation + PublicationHead CAS
OutputSet registration state
```

Object Store/Neo4j nằm ngoài relational transaction và dùng idempotency + reconciliation theo `02`.

---

## 11. Idempotency

Web App/runtime retry là bình thường. Write command quan trọng phải có idempotency key hoặc deterministic identity.

Suggested keys:

```text
StartProcessing
= client_operation_id

RegisterOutputSet
= stage_execution_id + output_slot_id + output_registration_key

SelectBaseline
= selection_request_id

PublishOutput
= publication_request_id
```

POC có thể implement một lightweight operation-key column/table khi duplicate retries xuất hiện; không cần generic distributed idempotency platform từ đầu.

Tối thiểu command phải detect duplicate business identity và trả existing result thay vì tạo duplicate OutputSlot/PublicationScope.

---

## 12. Correlation IDs

Một execution nên trace được xuyên hệ thống:

```text
processing_run_id
stage_execution_id
runtime_ref
output_set_id
publication_id
mlflow_trace_ref        # later
```

Structured log phải luôn include ít nhất:

```text
workspace_id
processing_run_id
stage_execution_id
```

nếu context có sẵn.

Không dùng runtime ID làm sole correlation ID vì runtime có thể đổi từ LangGraph sang Prefect.

---

## 13. SQLite bootstrap

Mỗi application process mở SQLite phải enforce:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

Recommended POC rule:

```text
one Web App backend service
few concurrent writers
short DB transactions
no network filesystem SQLite file
```

Nếu write concurrency/HA requirement vượt profile này, migrate Catalog DB sang PostgreSQL thay vì cố tune SQLite thành production cluster.

---

## 14. Migration runner

Repository structure:

```text
poc/database-design/schema/
└── sqlite/
    ├── 001_init.sql
    └── 002_...
```

Application bootstrap:

```text
start
 ↓
open DB
 ↓
apply pending migrations
 ↓
verify schema version
 ↓
serve traffic
```

Shared environment không edit migration đã apply.

Main/CI sau này có thể dùng Atlas để:

```text
inspect
schema diff
migration lint
drift detection
```

Atlas là verification/migration tooling, không phải runtime persistence owner.

---

## 15. Reconciliation jobs

POC tối thiểu cần command/job có thể chạy thủ công:

### Object Store reconciliation

```text
find StoredObject registry → object missing/hash mismatch
find orphan object → chưa có registry
```

### Runtime reconciliation

```text
Catalog StageExecution RUNNING
but runtime says terminal
→ reconcile lifecycle/status evidence
```

Runtime reconciliation **không** được tự sửa baseline/publication.

### Publication reconciliation

```text
Publication MATERIALIZING/VERIFIED quá lâu
→ inspect Neo4j candidate
→ retry/mark FAILED theo policy
```

---

## 16. Error model

Application-level errors nên stable dù runtime thay đổi:

```text
SOURCE_NOT_FOUND
OUTPUT_NOT_ELIGIBLE
BASELINE_CONFLICT
INVALID_STAGE_INPUT
OUTPUT_REGISTRATION_FAILED
PUBLICATION_CONFLICT
RUNTIME_START_FAILED
RUNTIME_RESUME_FAILED
KNOWLEDGE_PUBLICATION_FAILED
```

Không expose thẳng exception class của LangGraph/Prefect/SQLite ra UI contract.

---

## 17. Testing strategy

### Tier 1 — domain invariant tests

Không cần real runtime:

```text
OutputSlot deterministic identity
StageInput XOR target
baseline candidate same slot
baseline CAS conflict
PublicationScope replacement
cross-workspace rejection
```

### Tier 2 — SQLite repository integration

Chạy real SQLite file/temp DB với FK ON:

```text
migration apply
FK/CHECK/UNIQUE enforcement
baseline transaction
publication transaction
indexes/query behavior
```

### Tier 3 — runtime contract tests

Dùng fake runtime adapter để test application layer:

```text
start
resume
cancel
failure
idempotent retry
```

Sau đó chạy cùng contract tests cho:

```text
LangGraphRuntimeAdapter
PrefectRuntimeAdapter   # when implemented
```

### Tier 4 — end-to-end POC

```text
Web App
→ LangGraph
→ Object Store
→ SQLite Catalog
→ baseline selection
→ resume
→ publication
→ Neo4j
```

MLflow integration test được thêm khi adapter được bật; không blocker cho core ingestion test.

---

## 18. POC implementation order

Khuyến nghị coding agent làm theo thứ tự:

```text
1. SQLite migration 001_init.sql
2. SQLiteCatalogRepository
3. ObjectStore adapter
4. Domain/application commands
5. FakeWorkflowRuntime adapter
6. LangGraphRuntimeAdapter
7. Web API endpoints
8. baseline UI flow
9. Neo4j publication adapter
10. reconciliation commands
11. MLflow adapter later
12. Prefect adapter only when trigger exists
```

Lý do dùng FakeRuntime trước LangGraph:

> verify application/database contract độc lập trước, tránh debug DB invariant và orchestration framework cùng lúc.

---

## 19. Main scale path

POC → main không phải rewrite domain.

```text
SQLiteCatalogRepository
      ↓ replace
PostgresCatalogRepository

LangGraphRuntimeAdapter
      ↓ optional replace
PrefectRuntimeAdapter

NoOpObservabilityAdapter
      ↓ replace/add
MLflowObservabilityAdapter
```

Các interface/application command giữ nguyên nếu requirement không thay semantics.

Main có thể bổ sung:

```text
PostgreSQL RLS
worker concurrency
materialized staleness projection
Review Inbox
MLflow evaluation gates
KnowledgeRelease
production Neo4j publication isolation
```

Mỗi capability chỉ được promote vào core khi requirement thực tế xuất hiện.

---

## 20. Implementation review checklist

### Application boundary

- [ ] UI chỉ gọi application API/commands.
- [ ] LangGraph node không mutate governance table trực tiếp.
- [ ] runtime-specific object không leak vào domain entity/API.
- [ ] Catalog DB vẫn là SoR cho lineage/baseline/publication.

### Runtime portability

- [ ] application phụ thuộc `WorkflowRuntimePort`.
- [ ] `runtime_ref` chỉ là correlation reference.
- [ ] fake runtime contract tests pass.
- [ ] LangGraph adapter pass cùng runtime contract.
- [ ] Prefect chưa được kéo vào dependency nếu chưa có trigger.

### MLflow boundary

- [ ] MLflow không giữ sole copy của business provenance.
- [ ] workflow không fail chỉ vì optional telemetry fail, trừ policy explicit.
- [ ] trace/experiment ref được correlation về StageExecution.

### Persistence

- [ ] migration source-of-truth rõ.
- [ ] SQLite FK bootstrap luôn bật.
- [ ] critical transactions nằm trong repository/application layer.
- [ ] reconciliation path tồn tại cho cross-store failure.

---

## 21. Definition of Done cho database POC

Database implementation có thể coi là POC-ready khi:

```text
1. ingest một SourceRevision
2. run cùng stage nhiều lần
3. tạo nhiều candidate OutputSet trong cùng deterministic OutputSlot
4. chọn/switch baseline có history + concurrency control
5. next StageExecution pin exact input/baseline
6. restart Web App/LangGraph mà governance state không mất
7. trace output → execution → input → source
8. publish revision mới và supersede đúng publication cũ theo PublicationScope
9. failed runtime/telemetry không làm corrupt baseline/publication
10. SQLite implementation có test chứng minh migration path về domain contract, không phụ thuộc LangGraph
```

Đạt 10 điều trên quan trọng hơn việc POC có nhiều framework/integration.