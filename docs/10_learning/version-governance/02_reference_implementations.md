# Version Governance — Reference Implementations

**Status:** Learning document  
**Audience:** System architects, AI platform engineers, workflow engineers  
**Learning goal:** Hiểu các hệ thống tham chiếu đã giải quyết từng phần của Version Governance như thế nào, từ đó xác định rõ phần nào Harness Hub sử dụng, mở rộng hoặc tự xây trước khi viết SDD.

---

## 1. Mục tiêu của tài liệu

Tài liệu này không nhằm lập danh sách mọi công cụ AI trên thị trường. Nó trả lời bốn câu hỏi kiến trúc:

1. Version Governance gồm những capability kỹ thuật nào?
2. Hệ thống nào đang thực hiện tốt từng capability?
3. Quyền sở hữu dữ liệu và lifecycle nên nằm ở đâu?
4. Harness Hub phải tự xây phần nào để tạo ra giá trị khác biệt?

Nguyên tắc áp dụng:

> Học từ hệ thống đã được kiểm chứng. Tích hợp phần đã trưởng thành. Chỉ sở hữu phần tạo ra khác biệt cho AI Delivery Platform.

Kết quả của tài liệu này là đầu vào cho `03_build_decisions.md` và bộ SDD của Version Governance.

---

## 2. Bài toán cần được phân rã

Version Governance không phải một registry đơn lẻ. Nó là sự phối hợp giữa nhiều lớp có lifecycle khác nhau.

| Capability | Câu hỏi cần trả lời |
|---|---|
| Source control | Mã nguồn workflow, agent, tool và schema nằm ở commit nào? |
| Prompt lifecycle | Run đã dùng chính xác prompt version nào? |
| Workflow runtime | Workflow được thực thi, checkpoint và resume như thế nào? |
| Workflow release | Tổ hợp workflow nào đã được publish và promoted? |
| Frozen run state | Toàn bộ cấu hình nào đã được khóa trước khi chạy? |
| Trace and evaluation | Điều gì xảy ra trong run và chất lượng được đo như thế nào? |
| Artifact revision | Output nghiệp vụ nào được tạo, sửa, tái tạo hoặc import? |
| Baseline and approval | Revision nào là bản được phê duyệt hiện tại? |
| Delivery lineage | Input, release, run và output liên hệ với nhau thế nào? |
| Difference explanation | Vì sao hai output khác nhau? |

Không có một công cụ duy nhất sở hữu hợp lý toàn bộ các capability trên.

---

## 3. Bản đồ hệ thống tham chiếu

```text
                         Harness Hub
                 Version & Artifact Governance
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
 Workflow execution     AI lifecycle data       Engineering assets
       │                      │                      │
   LangGraph                MLflow                  Git
 state/checkpoint       prompt/trace/eval       source/commit
       │                      │                      │
       └──────────────┬───────┴──────────────┬───────┘
                      ▼                      ▼
                 PostgreSQL             S3 / MinIO
               business metadata       immutable blobs
```

Harness Hub không thay thế các hệ thống này. Harness Hub tạo lớp business governance liên kết chúng thành một chuỗi delivery có thể kiểm toán.

---

## 4. LangGraph — Reference cho workflow runtime

### 4.1 Vấn đề LangGraph giải quyết

LangGraph cung cấp mô hình thực thi workflow dạng graph có state. Các capability đáng chú ý đối với Version Governance gồm:

- Graph execution và conditional routing.
- State transition trong một run.
- Checkpoint và persistence của runtime state.
- Interrupt và resume cho human-in-the-loop.
- Retry và tiếp tục thực thi theo node.
- Runtime thread/run identifiers.

Mental model:

```text
Graph definition
    ↓
Runtime state
    ↓
Node execution
    ↓
Checkpoint
    ↓
Interrupt / Resume
```

### 4.2 LangGraph không nên sở hữu

LangGraph không phải business system of record cho:

- Workflow release đã publish.
- Environment promotion như DEV hoặc PROD.
- Prompt publication policy.
- Artifact business identity.
- Human-edited artifact revision.
- Approved delivery baseline.
- Project-level lineage xuyên nhiều hệ thống.

Checkpoint chỉ mô tả trạng thái runtime. Nó không thay thế Frozen Run Manifest hay Artifact Revision.

### 4.3 Điều Harness Hub học từ LangGraph

1. **State-driven execution:** workflow được mô hình hóa bằng state và transition rõ ràng.
2. **Durable execution:** trạng thái có thể được checkpoint để phục hồi.
3. **Interrupt là trạng thái hợp lệ:** human approval không phải exception mà là một bước trong lifecycle.
4. **Runtime identifiers phải được tham chiếu, không sao chép:** Harness Hub chỉ lưu liên kết đến runtime run và checkpoint.
5. **Adapter boundary:** domain của Harness Hub không được phụ thuộc trực tiếp vào class hoặc persistence schema của LangGraph.

### 4.4 Ownership decision

| Information | Owner |
|---|---|
| Graph execution state | LangGraph |
| Node progress | LangGraph |
| Checkpoint payload | LangGraph |
| Runtime thread/run ID | LangGraph |
| Workflow Release | Harness Hub |
| Frozen Run Manifest | Harness Hub |
| Artifact Revision | Harness Hub |

**Kết luận:** sử dụng LangGraph làm runtime qua `WorkflowRuntimePort` và `LangGraphRuntimeAdapter`; không biến LangGraph thành registry nghiệp vụ.

---

## 5. MLflow — Reference cho prompt, trace và evaluation lifecycle

### 5.1 Vấn đề MLflow giải quyết

MLflow cung cấp các pattern hữu ích cho AI lifecycle:

- Prompt Registry và immutable prompt versions.
- Alias hoặc reference thuận tiện trong giai đoạn authoring.
- Experiment runs.
- Traces và spans.
- Evaluation datasets, metrics và results.
- Model lifecycle khi cần.

Mental model:

```text
Prompt definition
    ↓ publish
Immutable prompt version
    ↓ resolve
Experiment / production run
    ↓ observe
Trace and evaluation result
```

### 5.2 MLflow không nên sở hữu

MLflow không phải business system of record cho:

- Capability composition của Harness Hub.
- Workflow Release gồm nhiều agent, prompt, tool và schema.
- Environment-to-release mapping của delivery platform.
- Frozen Run Manifest cấp toàn workflow.
- Artifact business identity như `API Design / Function F001`.
- Human revision chain của tài liệu thiết kế.
- Project baseline và approval record.

Một MLflow run hoặc trace có thể hỗ trợ provenance nhưng không đại diện cho toàn bộ lifecycle của delivery artifact.

### 5.3 Điều Harness Hub học từ MLflow

1. **Published version là immutable.**
2. **Alias là pointer, không phải runtime identity cuối cùng.**
3. **Run phải pin exact version trước khi thực thi.**
4. **Trace và evaluation là hệ thống chuyên biệt, không nên tự xây lại trong POC.**
5. **Metadata reference tốt hơn duplicate data:** Harness Hub lưu `mlflow_trace_id`, prompt version và evaluation reference thay vì sao chép toàn bộ trace.

### 5.4 Authoring alias và runtime pinning

Trong authoring, người dùng có thể chọn alias:

```text
prompt: bd-api-writer@candidate
```

Trước khi run bắt đầu, Harness Hub phải resolve thành version bất biến:

```text
prompt_name: bd-api-writer
prompt_version: 8
```

Frozen Run Manifest không được chỉ lưu alias `candidate`, vì alias có thể trỏ sang version khác sau đó.

### 5.5 Ownership decision

| Information | Owner |
|---|---|
| Prompt definition and version | MLflow |
| Prompt alias | MLflow |
| Trace and span | MLflow |
| Evaluation result | MLflow |
| Exact prompt reference used by a Harness run | Harness Hub Frozen Run Manifest |
| Workflow Release | Harness Hub |
| Delivery Artifact Revision | Harness Hub |

**Kết luận:** sử dụng MLflow cho prompt, trace và evaluation; Harness Hub sở hữu quan hệ business giữa những reference này với workflow, run và artifact.

---

## 6. Git — Reference cho source and review governance

### 6.1 Vấn đề Git giải quyết

Git là system of record phù hợp cho:

- Workflow source code.
- Agent source code.
- Tool implementation.
- Schema và evaluator source.
- Commit history.
- Branch, review và merge workflow.

Một commit SHA là reference bất biến đến trạng thái source code.

### 6.2 Vì sao Git không đủ

Git không tự trả lời được:

- Prompt registry version nào được resolve tại runtime?
- Model profile và tool policy nào được sử dụng?
- Input RD snapshot nào được dùng?
- Runtime checkpoint nằm ở đâu?
- Output nào được AI tạo và output nào do người sửa?
- Revision nào là approved project baseline?
- Vì sao output A và B khác nhau khi cùng dùng một commit?

Hai run có thể dùng cùng Git commit nhưng khác prompt version, model, input snapshot hoặc runtime configuration.

### 6.3 Điều Harness Hub học từ Git

1. **Immutable content-addressed reference.**
2. **Mutable branch hoặc tag trỏ tới immutable commit.**
3. **Review trước khi merge hoặc publish.**
4. **History không bị rewrite trong governance lifecycle.**
5. **Diff phải chỉ ra thay đổi có ý nghĩa.**

### 6.4 Ownership decision

| Information | Owner |
|---|---|
| Source files and history | Git |
| Source commit used by a release | Harness Hub stores Git reference |
| Runtime configuration | Harness Hub |
| Prompt version | MLflow |
| Runtime state | LangGraph |
| Artifact revision | Harness Hub |

**Kết luận:** Git quản lý source; Harness Hub quản lý deployable composition và runtime provenance.

---

## 7. Object Storage — Reference cho immutable artifact blobs

### 7.1 Vấn đề S3 hoặc MinIO giải quyết

Object storage phù hợp với:

- File Markdown, Excel, PDF hoặc package có kích thước lớn.
- Immutable object blobs.
- Content-addressed hoặc versioned storage keys.
- Retention và lifecycle policy.

### 7.2 Phân chia metadata và content

Harness Hub không nên lưu toàn bộ binary content trong database nghiệp vụ.

```text
Harness Hub / PostgreSQL
- artifact_id
- revision_id
- business key
- content hash
- storage URI
- provenance
- approval state

S3 / MinIO
- immutable file bytes
```

### 7.3 Ownership decision

| Information | Owner |
|---|---|
| File bytes | S3 / MinIO |
| Artifact business identity | Harness Hub |
| Revision chain | Harness Hub |
| Content hash and storage reference | Harness Hub |
| Baseline pointer | Harness Hub |

**Kết luận:** borrow object storage; build artifact metadata và lifecycle trong Harness Hub.

---

## 8. PostgreSQL — Reference cho business governance metadata

### 8.1 Vì sao relational database phù hợp với POC

Version Governance cần:

- Transactional publication.
- Unique constraints cho version và baseline.
- Foreign-key consistency.
- Approval và audit records.
- Query upstream/downstream lineage ở quy mô POC.
- Outbox và idempotency.

Những yêu cầu này phù hợp với PostgreSQL hơn việc đưa graph database vào ngay từ đầu.

### 8.2 Không đồng nhất database với ownership

PostgreSQL là storage technology. Harness Hub mới là domain owner.

Ví dụ, LangGraph cũng có thể dùng PostgreSQL cho checkpoint, nhưng checkpoint schema vẫn thuộc LangGraph. Harness Hub không được query trực tiếp internal table của LangGraph như domain table của mình.

**Kết luận:** sử dụng PostgreSQL cho business metadata của Harness Hub; không dùng chung schema ownership giữa các subsystem.

---

## 9. OpenTelemetry và LangSmith — các reference bổ sung

### 9.1 OpenTelemetry

OpenTelemetry cung cấp chuẩn instrumentation cho traces, metrics và logs. Bài học chính:

- Dùng correlation identifiers xuyên hệ thống.
- Tách telemetry schema khỏi business domain model.
- Không biến observability backend thành system of record cho artifact governance.

Trong POC, OpenTelemetry không bắt buộc nếu MLflow trace và observability hiện tại đã đủ. Thiết kế không được ngăn việc tích hợp sau này.

### 9.2 LangSmith

LangSmith là reference mạnh cho debugging, trace và evaluation trong hệ sinh thái LangChain/LangGraph. Tuy nhiên, architecture baseline hiện chọn MLflow cho prompt lifecycle, traces và evaluation references.

LangSmith có thể được benchmark hoặc thay thế sau này thông qua integration boundary. Harness Hub không được phụ thuộc domain vào identifier hoặc data model độc quyền của một observability vendor.

**Kết luận:** học pattern observability; không thêm một lifecycle owner thứ hai trong POC.

---

## 10. Capability ownership matrix

| Capability | Primary owner | Harness Hub responsibility |
|---|---|---|
| Workflow source | Git | Lưu exact commit reference |
| Agent/tool/schema source | Git | Lưu exact commit reference |
| Workflow execution | LangGraph | Gọi qua runtime adapter |
| Runtime checkpoint | LangGraph | Lưu checkpoint reference |
| Prompt versions | MLflow | Resolve và pin exact version |
| Experiment/trace/evaluation | MLflow | Lưu external references và gate result |
| File blobs | S3 / MinIO | Lưu URI và content hash |
| Business metadata | Harness Hub / PostgreSQL | Sở hữu domain lifecycle |
| Capability Version | Harness Hub | Build |
| Agent Version | Harness Hub | Build |
| Workflow Release | Harness Hub | Build |
| Environment mapping | Harness Hub | Build |
| Frozen Run Manifest | Harness Hub | Build |
| Artifact Revision | Harness Hub | Build |
| Approval and baseline | Harness Hub | Build |
| Delivery lineage | Harness Hub | Build bằng cross-system references |
| Explain Difference | Harness Hub | Build từ manifest và revision metadata |

Nguyên tắc: **mỗi loại state có một owner chính**. Không duy trì song song cùng một lifecycle ở Harness Hub, LangGraph và MLflow.

---

## 11. Adopt, Extend, Build

### 11.1 Adopt

Sử dụng capability hiện có gần như nguyên trạng, chỉ qua adapter hoặc client:

| Capability | Reference implementation |
|---|---|
| Workflow runtime | LangGraph |
| Prompt Registry | MLflow |
| Trace and evaluation | MLflow |
| Source control | Git |
| Object storage | S3 / MinIO |
| Relational storage | PostgreSQL |

### 11.2 Extend

Kết hợp metadata từ hệ thống chuyên biệt vào business context của Harness Hub:

| Capability | Extension |
|---|---|
| Runtime provenance | Liên kết Harness run với LangGraph run/checkpoint |
| Prompt provenance | Pin MLflow prompt version trong Frozen Run Manifest |
| Evaluation gate | Liên kết result với release hoặc run decision |
| Delivery lineage | Kết nối Git, MLflow, LangGraph, input snapshot và artifact |

### 11.3 Build

Tự xây vì đây là business differentiator của Harness Hub:

| Capability | Lý do |
|---|---|
| Workflow Release | Biểu diễn deployable composition cấp delivery platform |
| Frozen Run Manifest | Khóa exact configuration xuyên nhiều hệ thống |
| Artifact Revision | Quản lý output AI và human edit theo business identity |
| Approval and Baseline | Thể hiện delivery governance của dự án |
| Explain Difference | Trả lời nguyên nhân output thay đổi trong business terms |
| Cross-system lineage | Tạo một chuỗi provenance thống nhất cho RD-to-BD |

---

## 12. Các anti-pattern cần tránh

### 12.1 Dùng Git commit làm toàn bộ run manifest

Git commit chỉ đại diện source code; nó không chứa prompt resolution, model profile, input snapshot hoặc runtime identifiers.

### 12.2 Dùng LangGraph checkpoint làm artifact history

Checkpoint là runtime state. Artifact Revision là immutable delivery output có business identity và approval lifecycle.

### 12.3 Sao chép Prompt Registry vào Harness Hub

Việc duy trì prompt version ở cả MLflow và Harness Hub tạo dual source of truth. Harness Hub chỉ lưu exact external reference đã dùng.

### 12.4 Dùng MLflow run làm project baseline

MLflow run không đại diện cho human-edited revision hoặc approved delivery baseline.

### 12.5 Tạo graph database trước khi có nhu cầu

POC cần transactional integrity và lineage query cơ bản. PostgreSQL đủ cho vertical slice đầu tiên.

### 12.6 Để alias tồn tại trong Frozen Run Manifest

Alias là mutable pointer. Manifest phải lưu exact immutable target.

---

## 13. Ví dụ end-to-end RD-to-BD

```text
Git
- workflow commit: a8c917f

MLflow
- system prompt: version 4
- drafting prompt: version 8

Harness Hub
- workflow release: rd-to-bd-api@1.3.0
- environment: DEV -> release 1.3.0
- knowledge snapshot: rd-revision-13
- frozen run manifest: manifest-101

LangGraph
- runtime run: lg-run-550
- checkpoint: cp-18

S3 / MinIO
- output blob: api-design-f001-rev3.md

Harness Hub
- artifact: API Design / F001
- artifact revision: 3
- origin: AI_GENERATED
- active baseline: revision 4 after reviewer edit
```

Sau đó prompt đổi từ version 8 sang 9 và tạo revision mới. `Explain Difference` có thể báo:

```text
Changed
- Drafting prompt: 8 -> 9

Unchanged
- Workflow source commit: a8c917f
- Workflow topology: 1.3.0
- RD snapshot: revision 13
- Model profile: high-accuracy-design@1

Human changes
- Baseline revision 4 contains reviewer edits after generation
```

Không hệ thống chuyên biệt nào tự cung cấp toàn bộ câu trả lời này. Đây là giá trị của Harness Hub Version Governance.

---

## 14. Đầu vào cho SDD

Bộ SDD phải coi các quyết định sau là baseline:

```text
LangGraph
- owns workflow runtime and checkpoints

MLflow
- owns prompt versions, traces and evaluation references

Git
- owns source code and immutable commits

S3 / MinIO
- owns immutable file blobs

Harness Hub
- owns releases, frozen manifests, artifact revisions,
  approvals, baselines, delivery lineage and Explain Difference
```

Các domain object cần được đặc tả trong SDD:

1. Capability Version.
2. Agent Version.
3. Workflow Release.
4. Environment Mapping.
5. Execution Run.
6. Frozen Run Manifest.
7. Knowledge Snapshot reference.
8. Artifact.
9. Artifact Revision.
10. Approval Record.
11. Baseline Pointer.
12. Lineage Reference.

Các integration port cần được đặc tả:

1. `WorkflowRuntimePort`.
2. `PromptRegistryPort` hoặc MLflow integration client.
3. `TraceEvaluationPort` hoặc MLflow reference client.
4. `ObjectStoragePort`.
5. Git source reference contract.

---

## 15. Learning exit checklist

Có thể chuyển sang `03_build_decisions.md` khi giải thích được các câu sau mà không nhìn tài liệu:

- Vì sao Git commit không thay thế Frozen Run Manifest?
- Checkpoint khác Artifact Revision ở điểm nào?
- Vì sao prompt alias không được lưu như runtime identity cuối cùng?
- LangGraph sở hữu state nào và Harness Hub sở hữu state nào?
- MLflow cung cấp lineage gì và Harness Hub phải bổ sung lineage gì?
- Vì sao Artifact Revision cần business identity độc lập với MLflow run?
- Vì sao PostgreSQL đủ cho lineage POC?
- Capability nào được Adopt, capability nào được Extend, capability nào phải Build?
- Hệ thống nào là source of truth cho từng state category?
- `Explain Difference` cần dữ liệu từ những hệ thống nào?

---

## 16. Kết luận

Reference architecture của Version Governance không phải là chọn một sản phẩm duy nhất. Nó là thiết lập ranh giới ownership đúng:

```text
LangGraph executes.
MLflow records AI lifecycle data.
Git versions source.
Object storage keeps immutable bytes.
Harness Hub governs delivery meaning.
```

Harness Hub chỉ nên tự xây phần nối execution technology với business delivery governance. Đây là ranh giới tạo ra khác biệt và cũng là ranh giới cần được chuyển thành SDD.