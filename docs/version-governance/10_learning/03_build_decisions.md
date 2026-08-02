# Version Governance — Build Decisions

> **Mục tiêu học:** Chốt rõ thành phần nào Harness Hub sẽ **Adopt**, **Extend** hoặc **Build** trước khi viết SDD.
>
> Tài liệu này không thay thế kiến trúc canonical tại `docs/40_architecture/`. Nó chuyển các bài học từ `01_core_concepts.md` và `02_reference_implementations.md` thành quyết định triển khai có thể dùng trực tiếp trong SDD.

---

## 1. Decision Framework

Mỗi capability được phân loại theo ba lựa chọn:

### Adopt

Sử dụng một nền tảng hoặc service hiện có làm system of record hoặc execution engine. Harness Hub chỉ tích hợp qua adapter hoặc API ổn định.

### Extend

Tái sử dụng nền tảng hiện có nhưng bổ sung metadata, workflow hoặc governance riêng trong Harness Hub.

### Build

Tự xây vì capability đó thuộc domain khác biệt cốt lõi của Harness Hub và không được các nền tảng tham chiếu giải quyết đầy đủ.

Quy tắc quyết định:

```text
Mature commodity capability
    -> Adopt

Mature capability nhưng thiếu business context
    -> Extend

Delivery-governance capability tạo khác biệt
    -> Build
```

---

## 2. Decision Principles

### 2.1 Không xây lại hạ tầng đã trưởng thành

Harness Hub không tự xây workflow engine, source control, object storage, trace backend hoặc prompt registry nếu giải pháp hiện có đáp ứng yêu cầu POC.

### 2.2 Một loại trạng thái chỉ có một system of record

Không lưu cùng một lifecycle độc lập trong Harness Hub, LangGraph và MLflow.

Ví dụ:

- Prompt version thuộc MLflow.
- Runtime checkpoint thuộc LangGraph.
- Workflow Release thuộc Harness Hub.
- Source commit thuộc Git.

### 2.3 Dependency phải replaceable

Domain model của Harness Hub không được phụ thuộc trực tiếp vào class, status hoặc persistence schema của LangGraph, MLflow hay object storage.

### 2.4 Sở hữu phần tạo khác biệt

Harness Hub phải sở hữu những capability giúp trả lời các câu hỏi delivery-level:

- Workflow state nào đã tạo output này?
- Output nào đang là approved baseline?
- Vì sao hai output khác nhau?
- Prompt, source, model hay input nào đã thay đổi?

---

## 3. Decision Summary

| Capability | Decision | System of record |
|---|---|---|
| Workflow execution | Adopt | LangGraph |
| Runtime checkpoint | Adopt | LangGraph |
| Human interrupt/resume | Adopt | LangGraph |
| Prompt versioning | Adopt | MLflow |
| Experiment and evaluation references | Adopt | MLflow |
| Execution trace | Adopt for POC | MLflow |
| Source version control | Adopt | Git |
| Binary artifact storage | Adopt | S3/MinIO or existing storage |
| Relational governance metadata | Adopt | PostgreSQL |
| Workflow Release | Build | Harness Hub |
| Environment-to-release mapping | Build | Harness Hub |
| Frozen Run Manifest | Build | Harness Hub |
| Artifact business identity | Build | Harness Hub |
| Artifact Revision chain | Build | Harness Hub |
| Approved Baseline | Build | Harness Hub |
| Delivery lineage | Extend | Harness Hub aggregating external references |
| Explain Difference | Build | Harness Hub |
| Runtime integration | Extend | Harness Hub runtime adapter |
| Prompt integration | Extend | Harness Hub MLflow adapter |

---

## 4. Adopt Decisions

## 4.1 Workflow Runtime — Adopt LangGraph

### Decision

LangGraph là workflow runtime đầu tiên của POC.

### Why

LangGraph đã giải quyết các vấn đề khó của agent execution:

- Graph execution.
- Stateful workflow.
- Conditional routing.
- Checkpoint.
- Interrupt và resume.
- Node retry.

Tự xây runtime không tạo ra khác biệt cho Version Governance và sẽ làm POC phình lớn.

### Harness boundary

Harness Hub không lưu toàn bộ internal graph state. Nó chỉ lưu:

- Harness run ID.
- Runtime provider.
- Runtime run/thread ID.
- Runtime status đã chuẩn hóa.
- Checkpoint reference khi cần.

### Risk

LangGraph status hoặc API có thể thay đổi.

### Mitigation

Tích hợp qua `WorkflowRuntimePort` và `LangGraphRuntimeAdapter`.

### Revisit when

- LangGraph không đáp ứng SLA hoặc security requirement.
- Cần runtime thứ hai.
- Runtime-specific behavior bị rò vào domain model.

---

## 4.2 Prompt Registry — Adopt MLflow

### Decision

MLflow là system of record cho prompt versions và prompt aliases trong POC.

### Why

MLflow đã cung cấp lifecycle phù hợp cho:

- Immutable prompt versions.
- Alias khi authoring.
- Trace và experiment linkage.
- Evaluation references.

Việc tự xây prompt registry sẽ tạo thêm UI, API, migration và lifecycle phải duy trì mà không làm tăng khác biệt business.

### Harness boundary

Harness Hub lưu exact prompt reference đã resolve trong Frozen Run Manifest:

```text
registry = mlflow
prompt_name = bd-api-writer
prompt_version = 7
```

Harness Hub không coi alias như runtime identity cuối cùng.

### Risk

MLflow object model có thể không phản ánh đầy đủ business naming của Harness Hub.

### Mitigation

Harness Hub lưu adapter metadata và business label riêng, nhưng không duplicate prompt content lifecycle.

### Revisit when

- MLflow không đáp ứng permission hoặc promotion model.
- Cần multi-registry.
- Prompt lifecycle trở thành capability khác biệt cốt lõi.

---

## 4.3 Source Control — Adopt Git

### Decision

Git là system of record cho workflow code, agent code, tool code, schemas và evaluator source.

### Why

Git giải quyết tốt:

- Immutable commit.
- Branching.
- Review.
- Merge history.
- Reproducible source reference.

### Harness boundary

Harness Hub lưu repository và exact commit SHA trong release hoặc manifest. Không copy source code vào database governance.

### Risk

Một commit có thể chứa nhiều thay đổi không liên quan.

### Mitigation

Workflow Release chỉ được publish sau validation và chỉ định rõ entrypoint, schema và binding.

---

## 4.4 Artifact Blob Storage — Adopt S3/MinIO

### Decision

File output được lưu trong existing S3-compatible object storage.

### Why

Database không phù hợp để lưu file lớn, Excel, PDF hoặc binary artifacts.

### Harness boundary

Harness Hub lưu:

- Storage URI.
- Content hash.
- MIME type.
- Size.
- Revision metadata.
- Provenance.

### Risk

Object bị thay thế hoặc xóa ngoài Harness Hub.

### Mitigation

- Immutable object key cho published revision.
- Content hash verification.
- Storage policy hạn chế overwrite.

---

## 5. Extend Decisions

## 5.1 Runtime Adapter — Extend LangGraph

### Decision

Harness Hub xây runtime-neutral port và adapter LangGraph.

### Why

Adopt LangGraph không có nghĩa domain của Harness Hub phụ thuộc vào LangGraph.

Canonical interface:

```python
class WorkflowRuntimePort(Protocol):
    async def start(self, request): ...
    async def resume(self, request): ...
    async def cancel(self, request): ...
    async def get_status(self, runtime_run_id): ...
```

### Harness-owned extension

- Canonical runtime status.
- Idempotency key.
- Harness run identity.
- Event normalization.
- Error mapping.

### Not included

- Generic plugin marketplace cho runtime.
- Runtime thứ hai trong POC.

---

## 5.2 Delivery Lineage — Extend External Metadata

### Decision

Harness Hub sở hữu delivery lineage graph logic nhưng tái sử dụng references từ Git, MLflow, LangGraph và object storage.

### Why

Không nền tảng riêng lẻ nào có toàn bộ chuỗi:

```text
RD input
-> workflow release
-> prompt version
-> source commit
-> runtime execution
-> artifact revision
-> approved baseline
```

### Harness-owned extension

- Stable business identifiers.
- Cross-system reference mapping.
- Upstream/downstream query.
- Comparison of run manifests.

### POC storage

PostgreSQL đủ cho adjacency query và indexed joins. Chưa cần graph database.

### Revisit when

- Lineage depth và traversal tăng mạnh.
- Cross-project graph trở thành use case chính.
- Relational query không đạt performance target.

---

## 5.3 Trace — Adopt First, Extend Only Through References

### Decision

POC dùng MLflow trace. Harness Hub không xây trace backend riêng.

### Harness-owned extension

Harness Hub chỉ cần:

- Trace ID.
- Trace provider.
- Link từ run hoặc artifact revision.
- High-level status và summary nếu cần hiển thị.

### Not included

Không duplicate every span, token event hoặc model call vào governance database.

---

## 6. Build Decisions

## 6.1 Workflow Release — Build

### Decision

Harness Hub xây Workflow Release như một immutable deployable business object.

### Why

Git commit không thể tự trả lời:

- Graph entrypoint nào được dùng?
- Agent/prompt versions nào được binding?
- State schema nào hợp lệ?
- Release nào đang chạy ở DEV hoặc PROD?

LangGraph quản lý execution, không quản lý enterprise release lifecycle.

### Minimum data

- Workflow ID.
- Release version.
- Status.
- Git repository và commit.
- Entrypoint.
- State schema version.
- Agent/capability bindings.
- Runtime configuration.
- Created/published metadata.

### Invariant

Published Workflow Release là immutable.

---

## 6.2 Environment Mapping — Build

### Decision

Harness Hub xây mutable pointer từ environment đến immutable Workflow Release.

```text
DEV  -> workflow release 1.4.0
PROD -> workflow release 1.3.0
```

### Why

Promotion và rollback là business deployment decision, không phải runtime checkpoint operation.

### Invariant

Rollback thay đổi pointer, không sửa hoặc xóa release history.

---

## 6.3 Frozen Run Manifest — Build

### Decision

Trước khi execute, Harness Hub resolve mọi mutable reference thành exact immutable values và đóng băng chúng trong Run Manifest.

### Why

Đây là nền tảng của reproducibility và Explain Difference.

### Minimum content

- Workflow Release.
- Git commit.
- Exact prompt versions.
- Agent/tool versions.
- Model profile.
- Input snapshot hoặc hash.
- Runtime adapter.
- Environment tại thời điểm start.

### Invariant

Manifest không thay đổi sau khi run bắt đầu.

### Anti-pattern

Không chỉ lưu `prompt_alias = production` hoặc `workflow = latest`.

---

## 6.4 Artifact and Artifact Revision — Build

### Decision

Harness Hub xây stable Artifact identity và immutable Artifact Revision chain.

### Why

Delivery artifact có business identity lâu dài, ví dụ:

```text
API Design / Customer Search
```

Nó có thể trải qua nhiều nguồn thay đổi:

- AI generated.
- Human edited.
- Regenerated.
- Imported.
- Transformed.

MLflow artifact không thay thế business revision lifecycle này.

### Invariants

- Artifact identity ổn định.
- Revision content immutable.
- Mỗi revision có provenance.
- Không overwrite approved revision.

---

## 6.5 Approved Baseline — Build

### Decision

Harness Hub xây mutable baseline pointer tới một immutable Artifact Revision.

### Why

"Revision mới nhất" không đồng nghĩa với "revision được phê duyệt".

### Invariant

Một artifact business key chỉ có một active baseline trong một scope xác định.

### Required audit

- Ai approve.
- Approve khi nào.
- Revision nào được chọn.
- Baseline cũ nào bị supersede.

---

## 6.6 Explain Difference — Build

### Decision

Harness Hub xây capability so sánh hai run hoặc output và giải thích nguyên nhân thay đổi.

### Why

Người dùng không hỏi "manifest JSON khác dòng nào". Họ hỏi:

> Vì sao output này khác output trước?

### POC classification

- Input changed.
- Workflow Release changed.
- Prompt changed.
- Agent/tool/model changed.
- Runtime configuration changed.
- Human edit occurred.

### POC implementation

Deterministic manifest comparison trước. Không yêu cầu LLM semantic explanation.

### Revisit when

Cần content-level semantic diff cho Excel, Markdown hoặc diagram.

---

## 7. Decisions Explicitly Deferred

Các capability sau không thuộc POC Version Governance:

- Multi-runtime orchestration.
- Generic capability marketplace.
- Graph database.
- Kafka/NATS event platform.
- Custom tracing backend.
- Custom evaluation engine.
- Generic policy engine.
- Cross-workspace sharing.
- Ontology governance.
- Semantic artifact diff bằng LLM.
- Bidirectional Git synchronization.

Nếu implementation cần một capability trong danh sách trên, phải tạo ADR mới thay vì đưa vào âm thầm.

---

## 8. Decision Dependencies

```text
Adopt Git
    -> Workflow Release pins commit

Adopt MLflow
    -> Frozen Run Manifest pins prompt version

Adopt LangGraph
    -> Runtime Adapter starts execution

Adopt S3/MinIO
    -> Artifact Revision points to immutable blob

Build Frozen Run Manifest
    -> Delivery Lineage becomes reproducible

Build Artifact Revision
    -> Approved Baseline becomes possible

Build Lineage
    -> Explain Difference becomes possible
```

Điểm quan trọng:

> Explain Difference không phải capability độc lập. Nó phụ thuộc vào exact version resolution và immutable provenance ở các bước trước.

---

## 9. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Duplicate lifecycle giữa Harness Hub và MLflow | Inconsistent state | Một system of record cho từng loại state |
| LangGraph-specific schema rò vào domain | Vendor lock-in | Runtime port và adapter |
| Alias được lưu thay exact version | Run không reproducible | Resolve và freeze trước execution |
| Artifact blob bị overwrite | Mất auditability | Immutable key và content hash |
| POC mở rộng thành platform chung | Trễ implementation | Deferred list và ADR gate |
| Lineage schema quá generic | Tăng độ phức tạp | Chỉ model vertical slice RD-to-BD |
| Explain Difference phụ thuộc LLM quá sớm | Kết quả khó kiểm chứng | Deterministic manifest diff trước |

---

## 10. Input for SDD

SDD phải mô tả chi tiết các thành phần Harness Hub sở hữu:

```text
Workflow Release
Environment Mapping
Execution Run
Frozen Run Manifest
Artifact
Artifact Revision
Approved Baseline
Delivery Lineage
Explain Difference
Runtime Adapter
MLflow Adapter
Object Storage Adapter
```

SDD không thiết kế lại internal implementation của:

```text
LangGraph
MLflow
Git
PostgreSQL
S3 / MinIO
```

### Requirement inputs

- Published objects immutable.
- Mutable pointers only target immutable records.
- Exact versions resolved before execution.
- One system of record per lifecycle.
- External dependencies accessed through adapters.
- Every artifact revision traceable to a frozen manifest or explicit human/import origin.
- Production execution fails closed when mandatory references cannot resolve.
- Explain Difference uses deterministic provenance comparison for the POC.

---

## 11. Learning Exit Checklist

Có thể chuyển sang `04_poc_boundary.md` khi trả lời được:

- [ ] Vì sao Workflow Release phải do Harness Hub sở hữu?
- [ ] Vì sao Runtime được Adopt nhưng Runtime Adapter phải Build?
- [ ] Vì sao Prompt alias không được lưu làm runtime identity cuối cùng?
- [ ] Frozen Run Manifest phải chứa những gì?
- [ ] Artifact Revision khác MLflow artifact ở điểm nào?
- [ ] Baseline là mutable hay immutable?
- [ ] Explain Difference phụ thuộc vào các capability nào?
- [ ] Vì sao PostgreSQL đủ cho POC lineage?
- [ ] Khi nào cần tạo ADR để thay đổi quyết định?
- [ ] Những capability nào bị defer khỏi POC?

---

## 12. Final Position

```text
Adopt
- LangGraph runtime
- MLflow prompt/trace/evaluation references
- Git source control
- PostgreSQL
- S3/MinIO

Extend
- Runtime integration
- Prompt integration
- Cross-system lineage
- Trace links

Build
- Workflow Release
- Environment mapping
- Frozen Run Manifest
- Artifact Revision
- Approved Baseline
- Explain Difference
```

Kết luận:

> Harness Hub không tạo khác biệt bằng cách xây lại runtime hoặc registry. Harness Hub tạo khác biệt bằng cách biến các version kỹ thuật rời rạc thành một delivery lineage có thể release, audit, approve, rollback và giải thích.