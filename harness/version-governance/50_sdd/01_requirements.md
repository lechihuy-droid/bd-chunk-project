# RD — Version Governance POC (Harness Hub)

**Date:** 2026-08-02
**Status:** 🟢 Approved (v1.1 — sửa 5 lỗi từ review, xem §9)
**Author:** Claude (Opus 5)
**Phase gate:** GATE 1 — APPROVED 2026-08-02

**Nguồn requirement (chỉ 4 file này):**

- `../10_learning/01_core_concepts.md` — ký hiệu `[CC §x]`
- `../10_learning/03_build_decisions.md` — ký hiệu `[BD §x]`
- `../10_learning/04_poc_boundary.md` — ký hiệu `[PB §x]`
- `../00_foundation/03_adrs/ADR-009-workflow-centric-ux.md` — ký hiệu `[ADR-009]`

Mọi FR/NFR dưới đây đều có cột Trace. Không FR nào được thêm nếu không trace được về một mục cụ thể
trong 4 file trên.

---

## 0. Problem Statement

**Vấn đề:** Với một tài liệu Basic Design do AI sinh ra, hiện không trả lời được: workflow nào đã chạy,
prompt version chính xác nào đã dùng, input là revision nào, và vì sao output hôm nay khác hôm qua.
Git chỉ quản lý source; nó không biết alias prompt resolve thành version nào, model nào được chọn, hay
output nào đã được phê duyệt. `[CC §1, §2]`

**Hiện trạng:** Harness Hub local (`harness/hub`) đã có workflow YAML engine, run store, artifact
library, approval gate và audit hash-chain, nhưng hoàn toàn thiếu 6 thứ mà `[BD §12]` xếp vào nhóm
Build: Workflow Release, Environment Mapping, Frozen Run Manifest, Artifact Revision chain có content
hash, Approved Baseline, Explain Difference.

**Mục tiêu:** Chứng minh giả thuyết POC `[PB §2]` — nếu Harness Hub sở hữu Workflow Release, Frozen Run
Manifest và Artifact Revision, trong khi LangGraph lo execution và MLflow lo prompt/trace, thì hệ thống
tái hiện được provenance và giải thích được thay đổi giữa hai lần chạy mà không phải tự xây lại runtime
hay prompt registry.

**Phạm vi:** đúng một vertical slice RD → API Basic Design `[PB §3]`. Không mở sang Screen Design,
DB Design, Batch Design hay Coding.

---

## 1. Usage — Người dùng dùng thế nào

### 1.1 User Profile

| Field | Giá trị |
|---|---|
| Người dùng | Delivery engineer / BD author, reviewer, system architect |
| Device / môi trường | Trình duyệt desktop, UI Harness Hub tại `http://127.0.0.1:8799` |
| Tần suất dùng | Mỗi lần cần sinh hoặc tái sinh một API Basic Design từ RD |
| Technical level | Hiểu delivery process; **không** cần hiểu LangGraph, MLflow hay schema DB |

### 1.2 Typical Usage Flow

Theo `[ADR-009]` — người dùng đi theo trục workflow, không theo trục asset:

```
Bước 1: User mở Project → chọn Workflow "RD-to-BD API"
Bước 2: System hiển thị release đang trỏ ở DEV/PROD
Bước 3: User chọn RD input, bấm Run
Bước 4: System freeze manifest (resolve prompt alias → exact version) rồi mới execute
Bước 5: System hiển thị trạng thái run, kết thúc sinh ra Output revision
Bước 6: User mở Output → xem nội dung BD Markdown
Bước 7: User bấm "Vì sao khác?" → chọn một run/output khác để so sánh
Kết quả: System liệt kê đúng thành phần nào changed, thành phần nào unchanged
```

Version creation, manifest freezing, lineage registration, artifact revision creation diễn ra **tự động
phía sau** các thao tác thường. Publish release và promote environment là hành động **explicit**.
`[ADR-009 Decision]`

### 1.3 Example Interactions

**Ví dụ 1 — Happy path (kịch bản demo `[PB §9]`):**

```
Run A
Input:  RD revision 1, workflow release 1.0.0, PROD pointer
        prompt alias "production" của api-bd-generator
System: resolve alias → mlflow prompt api-bd-generator version 1
        freeze manifest, execute, sinh API Design F001 revision 1
Output: Artifact Revision A (content_hash sha256:..., storage_uri s3://vgov-artifacts/...)

Run B
Input:  RD revision 1 (y hệt), workflow release 1.0.0
        prompt alias "production" đã được trỏ sang version 2
Output: Artifact Revision B

Explain Difference (A vs B):
Changed
- Prompt version: 1 → 2
Unchanged
- RD input hash
- Workflow Release
- Git commit
- Model profile
- Tool configuration
- Runtime configuration
- Human edit: không có ở cả hai
```

**Ví dụ 2 — Nhiều thay đổi cùng lúc (Run C `[PB §9]`):**

```
Input:  RD revision 2, prompt version 2
Output: Explain Difference (A vs C) phải chỉ ra ĐỒNG THỜI:
Changed
- Input hash: sha256:aaa… → sha256:bbb…
- Prompt version: 1 → 2
Unchanged
- Workflow Release, Git commit, Model profile, Tool configuration
```

**Ví dụ 3 — Edge case, fail closed `[BD §10]`:**

```
Input:  Start run ở PROD nhưng prompt alias "production" không tồn tại trong MLflow
Output: HTTP 422, run status = FAILED_PRECONDITION
        KHÔNG tạo run_manifest, KHÔNG gọi LangGraph
        Message: "Cannot resolve prompt alias 'production' for api-bd-generator"
```

**Ví dụ 4 — Edge case, immutability:**

API **không hở** endpoint `PUT`/`DELETE` cho release, nên phải chứng minh ở tầng dữ liệu:

```
Input:  UPDATE workflow_release SET git_commit='...' WHERE id=<published>   (SQL trực tiếp)
Output: ERROR — trigger release_immutable, SQLSTATE VG409.
        Release history không đổi.
        Nếu lỗi này đi qua vgov-api thì map thành HTTP 409 IMMUTABLE_OBJECT.
```

**Ví dụ 5 — Rollback `[CC §4.5]`:**

```
Input:  PROD đang trỏ release 1.1.0, user rollback về 1.0.0
Output: environment_mapping.PROD → release 1.0.0
        Release 1.1.0 vẫn tồn tại nguyên vẹn, không bị xóa hay sửa
```

---

## 2. Functional Requirements

### 2.1 Workflow Release — Build `[BD §6.1]`, `[PB §4.1]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-REL-001 | System phải tạo được Workflow Release chứa: workflow_id, release version, git repository, commit SHA, graph entrypoint, state schema version, agent/node bindings, exact prompt reference hoặc quy tắc resolve, runtime adapter ID, model profile reference | P0 | `[PB §4.1]`, `[BD §6.1 Minimum data]` |
| FR-REL-002 | Workflow Release ở trạng thái published phải immutable — mọi UPDATE/DELETE bị từ chối | P0 | `[BD §6.1 Invariant]`, `[PB §11]` |
| FR-REL-003 | Muốn thay đổi một release đã publish, system chỉ cho phép tạo release mới | P0 | `[CC §10.2]` |
| FR-REL-004 | System phải list và get release theo workflow_id | P0 | `[PB §7]` |

### 2.2 Environment Mapping — Build `[BD §6.2]`, `[PB §4.1]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-ENV-001 | System phải lưu mutable pointer từ environment đến một Workflow Release immutable | P0 | `[BD §6.2]`, `[CC §4.5]` |
| FR-ENV-002 | POC chỉ hỗ trợ đúng hai environment: DEV và PROD | P0 | `[PB §4.1]` |
| FR-ENV-003 | Rollback phải chỉ di chuyển pointer, không sửa và không xóa release history | P0 | `[BD §6.2 Invariant]`, `[CC §4.5]` |
| FR-ENV-004 | Mỗi lần đổi pointer phải ghi audit: ai, khi nào, từ release nào sang release nào | P1 | **Suy ra** từ `[BD §6.2 Invariant]` + `[PB §11]` — xem ghi chú dưới |

> **Ghi chú FR-ENV-004 — requirement duy nhất không trace trực tiếp 1-1.** `[BD §6.2]` chỉ có
> Required audit cho Baseline (§6.5), không cho Environment. Nhưng `[BD §6.2 Invariant]` nói
> "Rollback thay đổi pointer, **không sửa hoặc xóa release history**" — muốn có history của việc
> pointer đã đi đâu thì phải ghi lại, nếu không thì `environment_mapping` chỉ còn trạng thái hiện
> tại và câu hỏi "PROD từng chạy release nào?" không trả lời được. Giữ ở **P1**, không phải P0, và
> đánh dấu tường minh là suy ra chứ không phải copy từ spec.

### 2.3 Execution Run — Build `[PB §4.2]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-RUN-001 | System phải tạo logical run **trong Harness Hub trước khi** gọi runtime | P0 | `[PB §4.2]`, `[PB §10.2]` |
| FR-RUN-002 | Run phải lưu: run ID, project/workspace context, workflow release ID, environment hoặc execution mode, lifecycle status, LangGraph runtime run/thread reference, MLflow trace reference, timestamps created/started/completed | P0 | `[PB §4.2]` |
| FR-RUN-003 | Mỗi run phải có correlation ID xuyên Harness Hub, LangGraph và MLflow | P0 | `[PB §11]` |
| FR-RUN-004 | Runtime completion callback phải idempotent — nhận cùng một callback nhiều lần không tạo thêm revision hay đổi trạng thái sai | P0 | `[PB §11]` |

### 2.4 Frozen Run Manifest — Build `[BD §6.3]`, `[PB §4.3]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-MAN-001 | Trước khi execution bắt đầu, system phải resolve mọi mutable reference thành exact immutable value và ghi vào Run Manifest | P0 | `[BD §6.3]`, `[PB §4.3]` |
| FR-MAN-002 | Manifest phải chứa tối thiểu: workflow release, git commit, exact prompt version(s), agent/tool version, model profile, input source reference + input hash, runtime adapter, environment tại thời điểm start | P0 | `[PB §4.3]`, `[BD §6.3]` |
| FR-MAN-003 | Manifest không được thay đổi sau khi execution đã bắt đầu | P0 | `[PB §4.3]`, `[BD §6.3 Invariant]` |
| FR-MAN-004 | System **không** được lưu alias (`production`, `latest`) thay cho exact version trong manifest | P0 | `[PB §11]`, `[BD §6.3 Anti-pattern]`, `[CC §10.1]` |
| FR-MAN-005 | Nếu không resolve được một mandatory reference, production execution phải fail closed — không tạo manifest, không gọi runtime | P0 | `[BD §10 Requirement inputs]` |

### 2.5 Adapters — Extend `[BD §5.1, §5.3]`, `[PB §4.4, §4.5]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-ADP-001 | System phải định nghĩa `WorkflowRuntimePort` runtime-neutral với `start`, `resume`, `cancel`, `get_status` | P0 | `[BD §5.1]` |
| FR-ADP-002 | POC implement đúng **một** adapter: `LangGraphRuntimeAdapter`. Tối thiểu hỗ trợ start run, read status, nhận completion/failure, capture runtime identifiers, trả về output reference hoặc payload | P0 | `[PB §4.4]` |
| FR-ADP-003 | `resume`, `cancel`, checkpoint inspection được giữ trong interface nhưng **không bắt buộc** hoàn thiện ở POC đầu tiên | P1 | `[PB §4.4]` |
| FR-ADP-004 | Adapter phải chuẩn hóa runtime status về canonical status của Harness Hub, có idempotency key, error mapping và event normalization | P0 | `[BD §5.1 Harness-owned extension]` |
| FR-ADP-005 | System phải dùng MLflow để lookup prompt và resolve alias → exact prompt version. Harness Hub **không** tạo Prompt Registry riêng | P0 | `[PB §4.5]`, `[BD §4.2]` |
| FR-ADP-006 | System chỉ lưu trace reference (trace ID, provider, link), **không** duplicate span/token event vào governance DB | P0 | `[BD §5.3]` |
| FR-ADP-007 | Object storage phải truy cập qua `BlobStorePort`; Harness Hub chỉ lưu storage URI, content hash, MIME type, size, revision metadata, provenance | P0 | `[BD §4.4]` |
| FR-ADP-008 | Git commit SHA được resolve và pin tại thời điểm publish release; **không** copy source code vào governance DB | P0 | `[BD §4.3]` |

### 2.6 Artifact và Artifact Revision — Build `[BD §6.4]`, `[PB §4.6]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-ART-001 | System phải phân biệt Artifact (business identity ổn định) và Artifact Revision (nội dung bất biến tại một thời điểm) | P0 | `[PB §4.6]`, `[CC §4.9, §4.10]` |
| FR-ART-002 | Revision phải lưu: artifact ID + business key, revision number hoặc immutable revision ID, source run ID, origin type, content hash, storage URI, created time | P0 | `[PB §4.6]` |
| FR-ART-003 | Mọi artifact revision phải có content hash | P0 | `[PB §11]` |
| FR-ART-004 | Revision đã tạo không được sửa trực tiếp — mọi thay đổi tạo revision mới | P0 | `[CC §4.10]`, `[BD §6.4 Invariants]` |
| FR-ART-005 | POC hỗ trợ origin type `AI_GENERATED` và `HUMAN_EDITED` (đủ để Explain Difference phát hiện human edit) | P0 | `[PB §4.8]`, `[BD §6.6]` |
| FR-ART-006 | Không lưu binary artifact lớn trực tiếp trong metadata table | P0 | `[PB §11]`, `[BD §4.4]` |
| FR-ART-007 | Mọi artifact revision phải traceable về một frozen manifest, hoặc về một origin human/import tường minh | P0 | `[BD §10 Requirement inputs]` |

### 2.7 Approved Baseline — Build `[BD §6.5]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-BASE-001 | System phải có mutable baseline pointer trỏ tới một immutable Artifact Revision | P0 | `[BD §6.5]`, `[CC §4.11]` |
| FR-BASE-002 | Một artifact business key chỉ có đúng một active baseline trong một scope xác định | P0 | `[BD §6.5 Invariant]` |
| FR-BASE-003 | System không được tự lấy latest revision làm baseline | P0 | `[CC §10.3]` |
| FR-BASE-004 | Mỗi lần approve phải ghi audit: ai approve, khi nào, revision nào, baseline cũ nào bị supersede | P0 | `[BD §6.5 Required audit]` |
| FR-BASE-005 | Không được overwrite một approved revision | P0 | `[BD §6.4 Invariants]` |

### 2.8 Delivery Lineage — Extend `[BD §5.2]`, `[PB §4.7]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-LIN-001 | System phải truy vấn được upstream chain: Artifact Revision → Execution Run → Frozen Run Manifest → Workflow Release → Prompt Version → Git Commit → Input Hash | P0 | `[PB §4.7]` |
| FR-LIN-002 | Lineage lưu bằng quan hệ PostgreSQL / adjacency table; **không** dùng graph database ở POC | P0 | `[PB §4.7]`, `[CC §10.6]`, `[BD §5.2 POC storage]` |
| FR-LIN-003 | System chỉ lưu reference và metadata cần cho business governance, không copy toàn bộ state nội bộ của LangGraph/MLflow | P0 | `[CC §10.5]`, `[BD §5.3]` |

### 2.9 Explain Difference — Build `[BD §6.6]`, `[PB §4.8]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-DIF-001 | System phải so sánh hai Run Manifest hoặc hai Artifact Revision | P0 | `[PB §4.8]` |
| FR-DIF-002 | Kết quả phải phân loại đúng **7** nhóm changed/unchanged: input, workflow release, prompt, model profile, tool configuration, **runtime configuration**, human edit present/not present | P0 | `[PB §4.8]` (6 nhóm) **hợp** `[BD §6.6 POC classification]` (có thêm "Runtime configuration changed") |
| FR-DIF-003 | So sánh phải là deterministic structural comparison; **không** dùng LLM để sinh giải thích ở POC | P0 | `[PB §4.8]`, `[BD §6.6]`, `[BD §9 Risk]` |
| FR-DIF-004 | Với kịch bản demo `[PB §9]`, kết quả phải xác định chính xác prompt là nguyên nhân thay đổi và **6 nhóm còn lại** unchanged | P0 | `[PB §10.9]` |

### 2.10 UI tối thiểu `[PB §7]`, `[ADR-009]`

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-UX-001 | UI phải cho phép chọn hoặc publish Workflow Release | P0 | `[PB §7]` |
| FR-UX-002 | UI phải cho phép start run | P0 | `[PB §7]` |
| FR-UX-003 | UI phải hiển thị output revision | P0 | `[PB §7]` |
| FR-UX-004 | UI phải hiển thị provenance của một revision | P0 | `[PB §7]` |
| FR-UX-005 | UI phải cho chọn hai output để Explain Difference | P0 | `[PB §7]` |
| FR-UX-006 | Điều hướng chính theo trục Project → Workflow → Run → Output → History/Compare/Approve. Capability, Agent, Prompt, Release, Manifest, Artifact chỉ lộ ra qua progressive disclosure từ ngữ cảnh workflow/run/output | P0 | `[ADR-009 Decision]` |
| FR-UX-007 | Không xây Registry UI riêng và không tạo control-plane frontend độc lập | P0 | `[PB §7]`, `[PB §10.11]` |
| FR-UX-008 | User không phải thực hiện cùng một version/publish action ở cả Harness Hub và MLflow | P0 | `[PB §10.10]` |

---

## 3. Non-Functional Requirements

| ID | Requirement | Metric | Priority | Trace |
|---|---|---|---|---|
| NFR-001 | Immutability enforce ở tầng dữ liệu, không chỉ ở application code | UPDATE/DELETE lên published release và run_manifest bị DB từ chối | P0 | `[PB §11]` |
| NFR-002 | Idempotency của runtime event/completion callback | Gửi lặp cùng correlation ID → cùng kết quả, không tạo revision trùng | P0 | `[PB §11]` |
| NFR-003 | Fail closed | Không resolve được mandatory reference → không tạo manifest, không execute | P0 | `[BD §10]` |
| NFR-004 | Không rò vendor object vào domain | Package `domain/` không import langgraph, mlflow, boto3, psycopg | P0 | `[BD §2.3]`, `[PB §11]`, `[CC §3.5 Philosophy]` |
| NFR-005 | Một loại state chỉ một system of record | Đối chiếu đúng bảng `[BD §3]`; không lưu song song lifecycle | P0 | `[BD §2.2]` |
| NFR-006 | Reproducibility của demo | Chạy lại cùng workflow release + prompt version cho ra manifest tương đương | P0 | `[PB §10.12]` |
| NFR-007 | Code-size guardrail | Backend domain/API 4.000–7.000; adapters 2.000–4.000; UI 1.500–3.000; migration/config 500–1.500. Tổng 8.000–15.500 LOC | P1 | `[PB §12]` |
| NFR-008 | Không fork hoặc sửa lõi LangGraph/MLflow | Chỉ dùng qua API/SDK public | P0 | `[PB §5]` |
| NFR-009 | Blob immutable | Object key của published revision không cho overwrite; verify bằng content hash | P0 | `[BD §4.4 Mitigation]` |

---

## 4. Explicit Exclusions

Danh sách này copy nguyên từ `[PB §6]` và `[BD §7]`. **Không** implement, kể cả khi "dễ thêm vào":

- **Không** Generic Capability Registry đầy đủ
- **Không** multi-agent marketplace
- **Không** multi-runtime support ngoài LangGraph
- **Không** custom workflow runtime
- **Không** custom Prompt Registry
- **Không** custom trace backend
- **Không** custom evaluation engine
- **Không** policy hierarchy nhiều cấp / generic policy engine
- **Không** cross-workspace sharing
- **Không** enterprise multi-tenancy hardening
- **Không** graph database
- **Không** Kafka/NATS/event streaming platform
- **Không** bidirectional Git synchronization
- **Không** embedded Excel/PDF editor
- **Không** semantic diff bằng LLM
- **Không** full human approval workflow (nhiều bước review) — chỉ baseline pointer + audit
- **Không** legal hold và advanced retention
- **Không** advanced ontology/vector/graph snapshot governance
- **Không** automatic rollback dựa trên evaluation score
- **Không** production-grade disaster recovery và multi-region
- **Không** generic `asset` framework `[PB §8]`
- **Không** mở rộng sang Screen Design, DB Design, Batch Design, Coding `[PB §3]`
- **Không** visual workflow editor mới `[PB §7]`

Muốn thêm bất kỳ mục nào ở trên → **phải viết ADR mới**, không đưa vào âm thầm. `[PB §6]`, `[BD §7]`

---

## 5. Open Questions

| # | Câu hỏi | Default nếu không confirm |
|---|---|---|
| Q1 | RD input đến từ đâu: upload file, hay tham chiếu một artifact_revision có sẵn, hay path trong Git? | Upload file → tính sha256 → lưu như một artifact_revision origin `IMPORTED`. Cho phép chọn lại revision đã import ở run sau (cần thiết để Run A và Run B dùng **cùng một** input hash). |
| Q2 | "Project" là entity riêng của vgov hay reuse project/board của hub? | Cột `project_key` dạng string trên artifact và run. Không tạo bảng project riêng ở POC. |
| Q3 | Pin MLflow version nào? Prompt Registry API của MLflow đổi giữa các major version. | Pin exact version trong compose + requirements, cô lập trong `MLflowPromptAdapter`. Version cụ thể chốt ở SD sau khi verify API thực tế. |
| Q4 | Workflow source code (LangGraph graph) nằm ở repo nào để pin commit? | Chính repo `ai-project-opus`, thư mục `harness/version-governance/runtime/`. Publish release resolve HEAD SHA tại thời điểm publish. |
| Q5 | Approved Baseline ở POC sâu tới đâu? `[PB §6]` loại "full human approval workflow" nhưng `[BD §6.5]` yêu cầu Baseline. | Một bước: `POST /baseline` chọn revision → cập nhật pointer + ghi audit + supersede bản cũ. Không có review chain, không có multi-approver. |
| Q6 | Identity của người approve lấy từ đâu (POC chưa có auth)? | Header `X-Actor`; nếu thiếu thì `local-user`. Không làm auth thật (nằm trong exclusion multi-tenancy hardening). |
| Q7 | Model profile map tới model nào? | Một profile duy nhất `design-accurate@v1` → model NVIDIA OpenAI-compatible đã dùng trong hub, pin tên model trong config của release. |
| Q8 | Human edit được nhập vào hệ thống bằng cách nào để FR-DIF-002 phát hiện được? | UI cho phép edit nội dung revision → tạo revision mới origin `HUMAN_EDITED`. Explain Difference đọc origin_type, không diff nội dung. |
| Q9 | ~~Docker Desktop chưa chạy~~ | ✅ **Đã đóng** — verified 2026-08-02: server 29.6.1, compose v5.2.0, linux/overlayfs. |
| Q10 | `business_key` của output artifact (vd `F001`) do ai quyết định? | ✅ **Đã đóng** — user cung cấp qua `output_business_key` ở `POST /runs`. Runtime không được tự đặt: identity nghiệp vụ thuộc Harness Hub `[CC §4.9]`, nếu runtime tự đặt thì cùng một artifact bị tách thành nhiều identity giữa các run, phá revision chain. |

---

## 6. Design Decisions

| Quyết định | Lý do | Đã cân nhắc thay thế |
|---|---|---|
| `vgov` là backend service riêng trong Docker, UI mount vào `harness/hub/web-v3` | Hub đang zero-DB và chạy trên host; kéo psycopg/mlflow/langgraph vào hub làm hỏng env của toàn bộ test suite hiện có và khiến hub phụ thuộc Docker. Tái dùng web-v3 tiết kiệm phần đắt nhất là UI, đồng thời giữ đúng `[PB §10.11]` "không tạo control-plane frontend độc lập" | Nhét in-process vào hub: chậm hơn và coupling nặng. Core lib import vào hub: cùng vấn đề dependency, thêm một lớp boundary |
| Immutability enforce bằng DB trigger, không chỉ bằng code | `[BD §6.1/§6.3 Invariant]` là invariant nghiệp vụ, không phải quy ước. Code path có thể bị bypass qua migration hay script | Chỉ check ở service layer: rẻ hơn nhưng không bảo đảm |
| Harness Hub resolve prompt **trước**, truyền prompt text đã resolve vào LangGraph runtime | Nếu runtime tự tra MLflow thì alias có thể resolve khác với thứ đã ghi trong manifest → phá vỡ FR-MAN-004 và reproducibility | Runtime tự tra MLflow: ít code hơn nhưng manifest hết đáng tin |
| Explain Difference dùng deterministic manifest diff, không LLM | `[BD §9 Risk]` — kết quả LLM khó kiểm chứng; và Explain Difference không phải capability độc lập, nó phụ thuộc exact version resolution ở bước trước `[BD §8]` | LLM semantic explanation: hoãn tới khi cần content-level diff `[BD §6.6 Revisit when]` |
| Lineage bằng PostgreSQL relations + indexed FK | `[CC §10.6]`, `[BD §5.2]` — POC chưa đủ depth để cần graph DB | Neo4j: nằm trong exclusion list |
| Baseline là pointer + audit một bước | `[PB §6]` loại full approval workflow, nhưng `[BD §6.5]` bắt buộc có Baseline. Lấy giao của hai ràng buộc | Approval workflow đầy đủ: vi phạm exclusion |
| Giữ `resume`/`cancel` trong port nhưng không implement đầy đủ | `[PB §4.4]` cho phép; giữ signature để adapter thứ hai sau này không phải đổi port | Bỏ hẳn khỏi port: sẽ phải đổi interface sau, vi phạm tinh thần `[BD §2.3]` |

---

## 7. Acceptance Criteria — Definition of Done

POC được coi là xong khi **cả 12 mục** `[PB §10]` pass:

| # | Tiêu chí | FR liên quan |
|---|---|---|
| 1 | Workflow Release có exact source reference và immutable definition | FR-REL-001, FR-REL-002 |
| 2 | Run được tạo trong Harness Hub trước khi LangGraph execution bắt đầu | FR-RUN-001 |
| 3 | Prompt alias được resolve thành exact MLflow prompt version | FR-ADP-005, FR-MAN-004 |
| 4 | Frozen Run Manifest được lưu trước execution và không bị mutation | FR-MAN-001, FR-MAN-003 |
| 5 | LangGraph execution tạo được API BD Markdown | FR-ADP-002 |
| 6 | Output được lưu thành Artifact Revision với content hash và source Run ID | FR-ART-002, FR-ART-003 |
| 7 | Mở một Artifact Revision và xem được upstream provenance | FR-LIN-001, FR-UX-004 |
| 8 | Chạy được cùng input với hai prompt version khác nhau | FR-RUN-002, FR-ADP-005 |
| 9 | Explain Difference xác định chính xác prompt là nguyên nhân, các component khác không đổi | FR-DIF-002, FR-DIF-004 |
| 10 | Không yêu cầu user làm cùng một version/publish action ở cả Harness Hub và MLflow | FR-UX-008 |
| 11 | Không tạo thêm control-plane app hoặc registry frontend độc lập | FR-UX-007 |
| 12 | Demo chạy lặp lại được với cùng workflow release và prompt version | NFR-006 |

---

## 8. Bước tiếp theo

Sau khi RD này được APPROVE:

```text
harness/version-governance/50_sdd/02_system_design.md
```

SD chỉ specification các thành phần Harness Hub sở hữu `[BD §10]`: Workflow Release, Environment
Mapping, Execution Run, Frozen Run Manifest, Artifact, Artifact Revision, Approved Baseline, Delivery
Lineage, Explain Difference, Runtime Adapter, MLflow Adapter, Object Storage Adapter.

SD **không** thiết kế lại internal implementation của LangGraph, MLflow, Git, PostgreSQL, S3/MinIO.

---

## 9. Changelog

**v1.1 — 2026-08-02, sửa theo review độc lập:**

- Ví dụ 4 (§1.3): bỏ `PUT /releases/{id}` — endpoint đó không tồn tại trong SD, request thật sẽ trả
  404/405 và không bao giờ chạm trigger. Đổi thành SQL trực tiếp, đúng cách `test_immutability` kiểm.
- FR-DIF-002: 6 → **7 nhóm**, thêm runtime configuration. `[BD §6.6]` có nhóm này mà v1 bỏ sót.
- FR-ENV-004: sửa trace sai (`[BD §6.2]` không có yêu cầu audit), đánh dấu tường minh là requirement
  **suy ra**, kèm lý do.
- Q9 đóng (Docker verified). Thêm Q10 về `output_business_key` — v1 không nguồn nào cấp business key
  cho artifact, làm DoD #6 không thể pass.
- Bỏ con số cứng "235 test" của hub — số thật khác; dùng "toàn bộ test suite hiện có".

---

*Version Governance POC — RD v1.1 | 2026-08-02*
