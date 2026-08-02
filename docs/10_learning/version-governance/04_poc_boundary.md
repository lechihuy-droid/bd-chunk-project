# 04. POC Boundary — Version Governance

> **Mục tiêu học:** Khóa phạm vi POC đủ nhỏ để triển khai nhanh nhưng vẫn chứng minh được các khái niệm cốt lõi của Version Governance trong Harness Hub.

---

## 1. Vì sao cần khóa POC Boundary?

Version Governance có thể mở rộng thành một platform rất lớn, bao gồm prompt registry, agent registry, workflow release, policy, evaluation, lineage, audit, approval, rollback, artifact management và nhiều runtime adapter.

Nếu đưa tất cả vào POC, nhóm sẽ dành phần lớn thời gian xây platform infrastructure thay vì học và chứng minh vertical slice.

POC này chỉ nhằm trả lời bốn câu hỏi:

1. Có thể đóng băng chính xác cấu hình đã dùng cho một lần chạy hay không?
2. Có thể quản lý output AI thành các revision bất biến hay không?
3. Có thể giải thích vì sao hai output khác nhau hay không?
4. Có thể tích hợp LangGraph và MLflow vào Harness Hub mà không tạo control plane thứ hai hay không?

POC không nhằm chứng minh toàn bộ enterprise readiness.

---

## 2. POC Hypothesis

> Nếu Harness Hub quản lý Workflow Release, Frozen Run Manifest và Artifact Revision trong khi LangGraph phụ trách execution và MLflow phụ trách prompt/trace/evaluation, thì hệ thống có thể tái hiện provenance của output và giải thích thay đổi giữa hai lần chạy mà không phải tự xây lại runtime hoặc prompt registry.

Giả thuyết được coi là đúng khi demo end-to-end đáp ứng Definition of Done ở phần 10.

---

## 3. Vertical Slice duy nhất

POC chỉ triển khai một flow RD → API Basic Design:

```text
RD input
  ↓
Workflow Release
  ↓
Resolve exact MLflow Prompt Version
  ↓
Freeze Run Manifest
  ↓
Execute through LangGraph Runtime Adapter
  ↓
Generate API BD Markdown
  ↓
Register Artifact Revision
  ↓
Compare with another run/output
  ↓
Explain Difference
```

Không mở rộng sang Screen Design, DB Design, Batch Design hoặc Coding trong cùng POC.

---

## 4. Phạm vi Build

### 4.1 Workflow Release

Harness Hub phải tạo được một Workflow Release bất biến gồm tối thiểu:

- Workflow ID và release version.
- Git repository, commit SHA và graph entrypoint.
- State schema version.
- Agent hoặc node bindings cần thiết.
- Exact MLflow prompt references hoặc quy tắc resolve prompt.
- Runtime adapter ID.
- Model profile reference.

POC chỉ cần DEV và PROD environment pointer.

### 4.2 Execution Run

Harness Hub phải tạo một logical run trước khi gọi runtime.

Run tối thiểu lưu:

- Run ID.
- Project/workspace context từ Harness Hub.
- Workflow Release ID.
- Environment hoặc execution mode.
- Lifecycle status.
- LangGraph runtime run/thread reference.
- MLflow trace reference.
- Created/started/completed timestamps.

### 4.3 Frozen Run Manifest

Trước khi execution bắt đầu, Harness Hub phải resolve và lưu bất biến:

- Workflow Release.
- Git commit.
- Exact prompt version.
- Model profile hoặc resolved model identifier.
- Runtime configuration.
- Input source reference và input hash.
- Knowledge snapshot reference tối thiểu nếu có.
- Tool references cần thiết.

Run manifest không được thay đổi sau khi execution đã bắt đầu.

### 4.4 LangGraph Runtime Adapter

POC implement một adapter duy nhất:

```text
WorkflowRuntimePort
└── LangGraphRuntimeAdapter
```

Adapter tối thiểu hỗ trợ:

- Start run.
- Read status.
- Receive completion/failure result.
- Capture runtime identifiers.
- Return generated output reference hoặc payload.

Pause, resume, cancel và checkpoint inspection có thể được giữ trong interface nhưng không bắt buộc hoàn thiện ở POC đầu tiên.

### 4.5 MLflow Integration

POC dùng MLflow cho:

- Prompt version lookup.
- Exact prompt-version resolution.
- Trace ID hoặc experiment/run reference.
- Evaluation reference nếu có.

Harness Hub không tạo một Prompt Registry riêng.

### 4.6 Artifact và Artifact Revision

POC cần phân biệt:

```text
Artifact
= business identity ổn định

Artifact Revision
= nội dung bất biến tại một thời điểm
```

Ví dụ:

```text
Artifact: API Design / Function F001

Revision 1: AI generated from Run A
Revision 2: AI generated from Run B
```

Metadata tối thiểu:

- Artifact ID và business key.
- Revision number hoặc immutable revision ID.
- Source run ID.
- Origin type.
- Content hash.
- Storage URI.
- Created time.

### 4.7 Basic Lineage

Lineage POC chỉ cần hỗ trợ upstream chain:

```text
Artifact Revision
  → Execution Run
  → Frozen Run Manifest
  → Workflow Release
  → Prompt Version
  → Git Commit
  → Input Hash
```

Không cần graph database. PostgreSQL relations hoặc adjacency table là đủ.

### 4.8 Explain Difference

POC phải so sánh được hai Run Manifest hoặc hai Artifact Revision và phân loại:

- Input changed/unchanged.
- Workflow Release changed/unchanged.
- Prompt changed/unchanged.
- Model profile changed/unchanged.
- Tool configuration changed/unchanged.
- Human edit present/not present.

POC dùng deterministic structural comparison. Không bắt buộc LLM-generated semantic explanation.

---

## 5. Thành phần Adopt/Extend trong POC

| Capability | Cách dùng trong POC |
|---|---|
| LangGraph | Adopt làm execution engine |
| MLflow | Adopt Prompt Registry và trace/evaluation reference |
| Git | Adopt làm source-control system of record |
| PostgreSQL | Adopt làm metadata và lineage store |
| S3/MinIO hoặc storage hiện hữu | Adopt làm binary artifact store |
| Harness Hub | Extend bằng Version Governance bounded module |

Không fork hoặc sửa lõi LangGraph/MLflow trong POC.

---

## 6. Ngoài phạm vi POC

Các capability sau bị loại khỏi POC đầu tiên:

- Generic Capability Registry đầy đủ.
- Multi-agent marketplace.
- Multi-runtime support ngoài LangGraph.
- Custom workflow runtime.
- Custom Prompt Registry.
- Custom trace backend.
- Custom evaluation engine.
- Policy hierarchy nhiều cấp.
- Cross-workspace sharing.
- Enterprise multi-tenancy hardening.
- Graph database.
- Kafka/NATS/event streaming platform.
- Bidirectional Git synchronization.
- Embedded Excel/PDF editor.
- Semantic diff bằng LLM.
- Full human approval workflow.
- Legal hold và advanced retention.
- Advanced ontology/vector/graph snapshot governance.
- Automatic rollback based on evaluation score.
- Production-grade disaster recovery và multi-region.

Những mục này chỉ được bổ sung khi có ADR và thay đổi scope rõ ràng.

---

## 7. Giới hạn UI

POC không xây một Registry UI riêng.

Có thể sử dụng:

- Existing Harness Hub page.
- Swagger/OpenAPI.
- CLI hoặc debug page.
- Một màn hình tối thiểu cho Run, Output và Explain Difference.

UX tối thiểu cần chứng minh:

1. Chọn hoặc publish Workflow Release.
2. Start run.
3. Xem output revision.
4. Xem provenance.
5. Chọn hai output để Explain Difference.

Không cần visual workflow editor mới nếu Harness Hub đã có canvas hoặc configuration surface.

---

## 8. Minimal Data Boundary

POC có thể bắt đầu với các entity/bảng sau:

```text
workflow_release
execution_run
run_manifest
run_component
artifact
artifact_revision
```

Có thể bổ sung `environment_mapping` nếu DEV/PROD chưa được lưu trong Harness Hub.

Không tạo generic `asset` framework trong POC.

---

## 9. Demo Scenario

### Run A

```text
Input: RD revision 1
Workflow Release: 1.0.0
Prompt: api-bd-generator version 1
Model profile: design-accurate v1
Output: Artifact Revision A
```

### Run B

```text
Input: RD revision 1
Workflow Release: 1.0.0
Prompt: api-bd-generator version 2
Model profile: design-accurate v1
Output: Artifact Revision B
```

### Expected comparison

```text
Output B differs from Output A because:

Changed
- Prompt version: 1 → 2

Unchanged
- RD input hash
- Workflow Release
- Git commit
- Model profile
- Tool configuration
```

### Optional Run C

Run C dùng RD revision 2 và Prompt version 2 để chứng minh hệ thống có thể chỉ ra đồng thời thay đổi input và prompt.

---

## 10. Definition of Done

POC được coi là hoàn thành khi:

1. Workflow Release có exact source reference và immutable definition.
2. Run được tạo trong Harness Hub trước khi LangGraph execution bắt đầu.
3. Prompt alias được resolve thành exact MLflow prompt version.
4. Frozen Run Manifest được lưu trước execution và không bị mutation.
5. LangGraph execution tạo được API BD Markdown.
6. Output được lưu thành Artifact Revision với content hash và source Run ID.
7. Có thể mở một Artifact Revision và xem upstream provenance.
8. Có thể chạy cùng input với hai prompt version khác nhau.
9. Explain Difference xác định chính xác prompt là nguyên nhân thay đổi và các component khác không đổi.
10. Không yêu cầu người dùng thực hiện cùng một version/publish action ở cả Harness Hub và MLflow.
11. Không tạo thêm control-plane app hoặc registry frontend độc lập.
12. Demo có thể chạy lặp lại với cùng workflow release và prompt version.

---

## 11. Quality Guardrails

Dù là POC, các nguyên tắc sau không được bỏ qua:

- Published release và frozen manifest là immutable.
- Runtime events hoặc completion callbacks phải idempotent ở mức tối thiểu.
- Không lưu binary artifact lớn trực tiếp trong metadata table.
- Không lưu alias thay cho exact prompt version trong run manifest.
- Không để LangGraph-specific object trở thành domain entity của Harness Hub.
- Mọi artifact revision phải có content hash.
- Mọi run phải có correlation ID xuyên Harness Hub, LangGraph và MLflow.

Các yêu cầu hardening khác được hoãn sang pilot/production.

---

## 12. Code-size Guardrail

Incremental production code mục tiêu:

| Phần | LOC mục tiêu |
|---|---:|
| Backend domain/API | 4.000–7.000 |
| Runtime/MLflow/storage adapters | 2.000–4.000 |
| Minimal UI/debug surface | 1.500–3.000 |
| Migration/configuration | 500–1.500 |
| **Tổng production code** | **8.000–15.500** |

Nếu estimate vượt đáng kể giới hạn này, phải xem lại scope trước khi coding.

---

## 13. Learning Exit Criteria

Sau tài liệu này, người đọc phải trả lời được:

- Vertical slice duy nhất của POC là gì?
- Tại sao Workflow Release và Frozen Run Manifest thuộc Harness Hub?
- Tại sao prompt version thuộc MLflow?
- Tại sao execution state thuộc LangGraph?
- Artifact và Artifact Revision khác nhau thế nào?
- Explain Difference dựa trên dữ liệu nào?
- Những capability nào bị loại khỏi POC?
- Khi nào cần ADR để mở rộng scope?

Nếu trả lời được các câu hỏi trên, Learning Package kết thúc và chuyển sang SDD.

---

## 14. Input trực tiếp cho SDD

SDD Version Governance sẽ chỉ specification các phạm vi sau:

```text
Workflow Release
Execution Run
Frozen Run Manifest
LangGraph Runtime Adapter contract
MLflow Prompt/Trace Adapter contract
Artifact and Artifact Revision
Basic Lineage
Explain Difference
```

Tài liệu SDD đầu tiên cần viết:

```text
docs/50_sdd/version-governance/01_requirements.md
```

Requirement không được tự mở rộng sang các capability đã liệt kê trong phần ngoài phạm vi.