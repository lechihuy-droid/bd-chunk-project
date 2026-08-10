# ADR-003 — Workflow Runtime Adapter Boundary

**Status:** Accepted for POC implementation  
**Scope:** Web App ↔ workflow runtime integration  
**Related:** `../02_storage_boundary.md`, `../05_implementation_guide.md`

---

## Context

ReqKB ingestion được điều khiển qua Web App. POC hiện dùng LangGraph để thực thi workflow, checkpoint và human interrupt/resume.

Tuy nhiên runtime requirement có thể thay đổi khi main scale. Prefect là một option có thể phù hợp hơn nếu workload trở nên scheduler/worker/data-pipeline heavy hoặc cần operational control plane khác.

Song song đó, MLflow dự kiến được tích hợp sau để phục vụ trace, experiment tracking và evaluation.

Problem cần giải quyết:

> Làm sao dùng LangGraph nhanh trong POC nhưng không để database/domain/application contract bị khóa vào LangGraph, đồng thời không over-engineer một generic orchestration platform?

---

## Options considered

### Option A — Web App gọi trực tiếp LangGraph API/object

```text
Web App → LangGraph → DB
```

**Ưu:** code ban đầu ít nhất.

**Nhược:** UI/application contract phụ thuộc checkpoint/thread/state semantics của LangGraph; switch runtime sẽ lan sang API, service và test.

**Rejected because:** coupling vượt quá runtime boundary đã chốt ở `SB-09`.

### Option B — Generic orchestration abstraction rất rộng

Expose common model cho scheduling, workers, deployments, checkpoints, events, retries, queues, artifacts...

**Ưu:** lý thuyết có thể map nhiều orchestrator.

**Nhược:** abstraction lớn hơn requirement; dễ tạo lowest-common-denominator hoặc framework riêng phải maintain.

**Rejected because:** over-engineering cho POC và chưa có evidence về requirement của Prefect/main.

### Option C — Minimal `WorkflowRuntimePort`

Application chỉ phụ thuộc capability Web App thực sự cần:

```text
start
resume
cancel
get_status
(optional stream_events / get_interrupt)
```

LangGraph-specific và Prefect-specific semantics nằm trong adapter.

---

## Decision

Chọn **Option C — minimal WorkflowRuntimePort**.

Current:

```text
Web App
  ↓
Application Commands
  ↓
WorkflowRuntimePort
  ↓
LangGraphRuntimeAdapter
```

Future if requirement warrants:

```text
WorkflowRuntimePort
  ↓
PrefectRuntimeAdapter
```

Business persistence không đổi:

```text
Catalog DB
= execution identity + lineage + baseline + publication
```

Runtime chỉ giữ execution mechanics:

```text
checkpoint
pause/resume
retry
runtime status
```

---

## Rationale

Decision này cân bằng hai mục tiêu:

```text
POC speed
+
runtime portability
```

LangGraph vẫn được dùng trực tiếp bên trong adapter, nên không mất capability quan trọng cho agentic/human-in-the-loop workflow.

Application/domain chỉ biết một contract nhỏ, do đó:

- database design không phụ thuộc runtime framework;
- Web App API ổn định hơn;
- có thể contract-test runtime adapter;
- Prefect chỉ được thêm khi có trigger thực tế;
- không phải xây một orchestrator abstraction mới.

---

## MLflow relationship

MLflow **không nằm trong WorkflowRuntimePort**.

```text
Application/StageExecution
  ├── WorkflowRuntimePort → LangGraph/Prefect
  └── ObservabilityPort   → MLflow
```

Lý do tách:

- runtime quyết định execution mechanics;
- MLflow phục vụ trace/evaluation/experiment;
- hai lifecycle và failure semantics khác nhau.

MLflow outage mặc định không được làm mất governance state hoặc trở thành sole owner của replay provenance.

---

## Consequences / Trade-offs

### Positive

- POC dùng LangGraph ngay không cần chờ platform abstraction lớn;
- switch sang Prefect có boundary rõ;
- runtime framework không trở thành System of Record;
- test application/database không cần real LangGraph;
- MLflow được tích hợp độc lập.

### Cost

- thêm adapter/interface layer;
- framework-specific feature muốn expose ra Web App phải review xem có thực sự là application capability hay chỉ runtime detail;
- switch runtime không bao giờ là “zero cost”: execution semantics, retries, deployment và operational behavior vẫn phải test lại.

---

## Runtime switch trigger

Không switch chỉ vì preference hoặc benchmark chung.

Revisit LangGraph vs Prefect khi có evidence như:

```text
high worker concurrency
scheduler/backfill trở thành primary requirement
non-agentic/data workflow chiếm tỷ trọng lớn
operational deployment model cần Prefect-style workers/control plane
LangGraph interrupt/checkpoint model không fit workflow chính
```

Nếu switch ảnh hưởng execution semantics, retry/guarantee hoặc deployment topology, tạo ADR mới ghi Context, Options, Decision, Rationale và migration plan.

---

## Migration implication

Để thêm Prefect:

1. implement `PrefectRuntimeAdapter` theo cùng port;
2. pass runtime contract test suite;
3. map `runtime_ref` sang Prefect flow/task run IDs;
4. test resume/cancel/retry semantics;
5. run side-by-side on non-critical workflows nếu cần;
6. migrate workflow configuration, không migrate baseline/publication history sang runtime store.

Historical Catalog DB records vẫn valid vì runtime IDs chỉ là correlation references.