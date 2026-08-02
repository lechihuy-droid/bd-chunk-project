# Version Governance — Core Concepts

**Mục tiêu:** Nắm đủ các khái niệm cốt lõi để chuyển sang viết SDD cho module Version Governance.  
**Thời lượng đề xuất:** 45–60 phút.  
**Đối tượng:** System Architect, AI Engineer, Product Engineer, Coding Agent.  
**Phạm vi:** Harness Hub trong use case RD → BD.

---

## 1. Version Governance là gì?

Version Governance là khả năng kiểm soát, truy vết và giải thích toàn bộ trạng thái đã tạo ra một kết quả AI.

Với một tài liệu Basic Design, hệ thống cần trả lời được:

- Workflow nào đã chạy?
- Workflow đang ở release nào?
- Prompt chính xác nào đã được dùng?
- Agent, tool và model nào tham gia?
- Input RD là phiên bản nào?
- Output nào là bản AI sinh, bản con người chỉnh sửa và bản đã phê duyệt?
- Vì sao output hôm nay khác output hôm qua?

Version Governance không chỉ là đánh số `v1`, `v2`. Nó là cơ chế bảo đảm rằng một kết quả AI có thể được **tái hiện, so sánh, kiểm toán và phê duyệt**.

---

## 2. Vì sao Git chưa đủ?

Git quản lý tốt source code và file text. Tuy nhiên một lần chạy AI còn phụ thuộc vào trạng thái runtime:

```text
Git commit
+ Prompt version
+ Model profile
+ Tool version
+ Input snapshot
+ Runtime configuration
+ Human edits
= Output thực tế
```

Git không tự biết:

- alias prompt đã resolve thành version nào;
- model nào đã được gateway chọn;
- input nào được đưa vào run;
- LangGraph checkpoint nào được dùng;
- output nào trở thành baseline đã phê duyệt.

Do đó Git vẫn là system of record cho source, nhưng không phải toàn bộ system of record cho AI execution.

---

## 3. Ba lớp cần phân biệt

### 3.1 Definition

Mô tả thứ hệ thống có thể chạy:

- Prompt
- Agent
- Workflow
- Tool configuration

### 3.2 Execution

Mô tả một lần chạy cụ thể:

- Run
- Frozen Run Manifest
- Runtime state
- Trace
- Checkpoint

### 3.3 Delivery Output

Mô tả kết quả nghiệp vụ được tạo ra và quản trị:

- Artifact
- Artifact Revision
- Approval
- Baseline
- Lineage

Sai lầm phổ biến là trộn cả ba lớp vào một object `version` duy nhất.

---

# 4. Các khái niệm cốt lõi

## 4.1 Capability

### Là gì?

Capability là một năng lực nghiệp vụ hoặc delivery có thể tái sử dụng, độc lập với workflow cụ thể.

Ví dụ:

- Parse RD source.
- Generate API Basic Design.
- Review naming convention.
- Validate traceability.

### Giải quyết vấn đề gì?

Nếu chỉ tái sử dụng Agent hoặc Workflow, logic nghiệp vụ dễ bị khóa vào một implementation. Capability tạo một lớp ổn định hơn để mô tả **hệ thống làm được việc gì**.

### Ví dụ RD → BD

```text
Capability: Generate API Basic Design
Input: API requirement
Output: API design document
Quality criteria: complete sections, preserve traceability
```

### Không phải

Capability không phải một lần chạy và cũng không nhất thiết là một agent.

---

## 4.2 Prompt Version

### Là gì?

Prompt Version là một bản prompt bất biến đã được đăng ký và có định danh chính xác.

### Giải quyết vấn đề gì?

Một thay đổi nhỏ trong prompt có thể làm output thay đổi mạnh. Nếu chỉ lưu tên prompt hoặc alias như `production`, không thể tái hiện run cũ.

### Ví dụ RD → BD

```text
bd-api-drafting
- version 7: tạo API design cơ bản
- version 8: bổ sung naming rule và traceability
```

### Không phải

Alias không phải immutable version. Alias chỉ là con trỏ có thể thay đổi.

---

## 4.3 Agent Version

### Là gì?

Agent Version là một cấu hình thực thi bất biến, kết hợp:

- capability mà agent hiện thực;
- source-code commit;
- prompt versions;
- tool versions;
- model profile;
- runtime limits;
- input/output schema.

### Giải quyết vấn đề gì?

Tên agent như `BD Writer` không đủ để biết agent thực tế đã chạy với prompt, model và tool nào.

### Ví dụ RD → BD

```text
BD API Writer 1.2.0
- prompt drafting v8
- tool rd-reader 1.0.0
- model profile high-accuracy-design v1
```

### Không phải

Agent Version không phải runtime state và không lưu checkpoint.

---

## 4.4 Workflow Release

### Là gì?

Workflow Release là một package bất biến có thể triển khai, mô tả topology và các binding chính xác giữa capability, agent và runtime configuration.

### Giải quyết vấn đề gì?

Workflow draft thay đổi liên tục. Production cần một trạng thái đã được kiểm tra, phê duyệt và có thể rollback.

### Ví dụ RD → BD

```text
RD-to-BD API release 1.3.0
- parse_rd → RD Parser 1.1.0
- generate_bd → BD API Writer 1.2.0
- review_bd → BD Reviewer 1.0.0
```

### Không phải

Workflow Release không phải một lần chạy. Một release có thể tạo ra nhiều run.

---

## 4.5 Environment Pointer

### Là gì?

Environment Pointer là con trỏ từ môi trường đến một Workflow Release bất biến.

```text
DEV  → release 1.4.0
PROD → release 1.3.0
```

### Giải quyết vấn đề gì?

Cho phép promote và rollback mà không sửa hoặc xóa release cũ.

### Không phải

Rollback không tạo lại lịch sử. Nó chỉ di chuyển con trỏ đến target cũ.

---

## 4.6 Run

### Là gì?

Run là một lần thực thi cụ thể của workflow với input và cấu hình đã resolve.

### Giải quyết vấn đề gì?

Một Workflow Release có thể chạy nhiều lần với input khác nhau. Mỗi lần cần status, trace, output và provenance riêng.

### Ví dụ RD → BD

```text
Run R-1024
- workflow release: 1.3.0
- input: RD revision 12
- status: SUCCEEDED
- output: API Design F001 revision 3
```

### Không phải

Run không phải Workflow Release. Release là definition; Run là execution.

---

## 4.7 Frozen Run Manifest

### Là gì?

Frozen Run Manifest là snapshot bất biến được tạo trước khi run bắt đầu. Nó chứa tất cả reference đã resolve thành version chính xác.

Ví dụ:

```json
{
  "workflow_release": "1.3.0",
  "prompt_version": 8,
  "agent_version": "1.2.0",
  "model_profile": "high-accuracy-design@1",
  "input_hash": "sha256:...",
  "git_commit": "a8c917f"
}
```

### Giải quyết vấn đề gì?

Nếu alias, environment hoặc model routing thay đổi sau đó, run cũ vẫn giữ nguyên provenance.

### Không phải

Manifest không phải log toàn bộ execution. Trace và checkpoint vẫn thuộc execution/observability layer.

---

## 4.8 Checkpoint

### Là gì?

Checkpoint là trạng thái trung gian của workflow runtime, cho phép resume hoặc tiếp tục sau human interrupt.

### Giải quyết vấn đề gì?

Workflow dài hoặc có human-in-the-loop không nên chạy lại từ đầu sau khi dừng.

### Ví dụ RD → BD

```text
Generate draft
→ WAITING_APPROVAL
→ reviewer approves
→ resume from checkpoint
→ package final output
```

### Không phải

Checkpoint không phải business version của output. Nó là runtime state.

---

## 4.9 Artifact

### Là gì?

Artifact là định danh nghiệp vụ ổn định của một output.

Ví dụ:

```text
API Design / Function F001
```

### Giải quyết vấn đề gì?

Cùng một đối tượng nghiệp vụ có thể có nhiều revision theo thời gian nhưng vẫn cần một identity thống nhất.

### Không phải

Artifact không phải file blob cụ thể. File cụ thể thuộc Artifact Revision.

---

## 4.10 Artifact Revision

### Là gì?

Artifact Revision là một bản nội dung bất biến của Artifact.

Nguồn tạo revision có thể là:

- AI-generated;
- human-edited;
- AI-regenerated;
- imported;
- transformed.

### Ví dụ RD → BD

```text
API Design F001
- revision 1: AI generated
- revision 2: reviewer edited
- revision 3: regenerated from updated RD
```

### Không phải

Không sửa trực tiếp revision đã có. Mỗi thay đổi tạo revision mới.

---

## 4.11 Approved Baseline

### Là gì?

Approved Baseline là con trỏ đến Artifact Revision hiện được công nhận là bản chuẩn của project.

```text
API Design F001 baseline → revision 2
```

### Giải quyết vấn đề gì?

`Latest revision` không đồng nghĩa với `approved revision`. Revision mới hơn có thể vẫn đang review.

### Không phải

Baseline không copy nội dung và không xóa revision khác. Nó chỉ trỏ đến một revision đã phê duyệt.

---

## 4.12 Lineage

### Là gì?

Lineage là chuỗi quan hệ giải thích output được tạo ra từ đâu và bằng cấu hình nào.

```text
RD revision
→ Run Manifest
→ Workflow Release
→ Agent/Prompt/Tool versions
→ Run
→ Artifact Revision
→ Approved Baseline
```

### Giải quyết vấn đề gì?

Lineage giúp truy vết, kiểm toán và trả lời câu hỏi `vì sao output thay đổi?`.

### Không phải

Lineage không nhất thiết cần graph database. POC có thể lưu bằng PostgreSQL và foreign keys.

---

# 5. Immutable target và mutable pointer

Đây là nguyên lý quan trọng nhất của Version Governance.

## Immutable target

Sau khi publish hoặc tạo revision:

- Prompt Version không đổi.
- Agent Version không đổi.
- Workflow Release không đổi.
- Frozen Run Manifest không đổi.
- Artifact Revision không đổi.

## Mutable pointer

Những thứ được phép di chuyển:

- Prompt alias.
- DEV/PROD environment pointer.
- Approved baseline pointer.

```text
Mutable pointer → Immutable target
```

Nhờ đó hệ thống vừa thay đổi được trạng thái hiện hành, vừa bảo toàn lịch sử.

---

# 6. Concept Map

```text
Capability
    │ implemented by
    ▼
Agent Version ───────→ Prompt Version
    │                 Tool Version
    │                 Model Profile
    ▼
Workflow Release
    │ selected by
    ▼
Environment Pointer
    │ resolve before run
    ▼
Frozen Run Manifest
    │ executed as
    ▼
Run ────────────────→ Checkpoint / Trace
    │ produces
    ▼
Artifact
    │
    └── Artifact Revision
            │
            └── Approved Baseline Pointer
```

---

# 7. User mental model và system model

## Người dùng thường nghĩ

```text
Project
→ Workflow
→ Run
→ Output
→ History / Compare / Approve
```

## Hệ thống cần lưu

```text
Capability
Agent Version
Prompt Version
Workflow Release
Frozen Run Manifest
Artifact Revision
Baseline
Lineage
```

UX không nên buộc user quản lý tất cả object kỹ thuật thủ công. Version Governance hoạt động phía sau các thao tác tự nhiên:

```text
Save     → lưu draft history
Publish  → tạo immutable release
Run      → freeze manifest
Generate → tạo artifact revision
Approve  → cập nhật baseline pointer
```

---

# 8. Ai sở hữu khái niệm nào?

## LangGraph

- Graph execution.
- Runtime state.
- Checkpoint.
- Interrupt/resume.
- Node routing và retry.

## MLflow

- Prompt versions và aliases.
- Experiment.
- Trace và span.
- Evaluation references/results.

## Git

- Workflow, agent, tool và evaluator source code.
- Schema và configuration source.

## Harness Hub

- Capability Versions.
- Agent Versions ở cấp governance.
- Workflow Releases.
- Environment mappings.
- Frozen Run Manifests.
- Artifact và Artifact Revisions.
- Approval, Baseline và cross-system Lineage.

Harness Hub hợp nhất trải nghiệm nhưng không sao chép toàn bộ state nội bộ của LangGraph hoặc MLflow.

---

# 9. Ví dụ hoàn chỉnh RD → BD

```text
1. Prompt `bd-api-drafting` version 8 được publish trong MLflow.

2. Agent Version `BD API Writer 1.2.0` pin prompt version 8.

3. Workflow Release `RD-to-BD API 1.3.0` pin Agent Version 1.2.0.

4. PROD pointer được chuyển đến release 1.3.0.

5. User chạy workflow với RD revision 12.

6. Harness Hub tạo Frozen Run Manifest:
   - release 1.3.0
   - prompt v8
   - agent 1.2.0
   - input hash của RD revision 12

7. LangGraph thực thi và MLflow ghi trace.

8. Run tạo `API Design F001 revision 1`.

9. Reviewer chỉnh nội dung, tạo revision 2.

10. Revision 2 được approve và baseline pointer chuyển đến revision 2.
```

Sau đó, nếu prompt chuyển từ v8 sang v9 và output mới khác đi, hệ thống có thể giải thích phần thay đổi dựa trên hai Frozen Run Manifest.

---

# 10. Các anti-pattern cần tránh

## 10.1 Lưu alias thay vì exact version

Sai:

```text
prompt = production
```

Đúng:

```text
prompt = bd-api-drafting version 8
```

## 10.2 Sửa release đã publish

Release đã publish phải bất biến. Muốn thay đổi thì tạo release mới.

## 10.3 Dùng latest revision làm baseline tự động

Latest chưa chắc đã approved.

## 10.4 Trộn checkpoint với artifact revision

Checkpoint là runtime state; Artifact Revision là delivery output.

## 10.5 Copy toàn bộ LangGraph/MLflow state vào Harness Hub

Harness Hub chỉ lưu reference và metadata cần cho business governance.

## 10.6 Xây graph database quá sớm

POC lineage có thể được giải quyết bằng relational model và indexed foreign keys.

---

# 11. Checklist tự kiểm tra

Bạn đã sẵn sàng chuyển sang SDD khi có thể trả lời phần lớn câu hỏi sau:

- [ ] Vì sao Git không đủ cho AI execution provenance?
- [ ] Definition, Execution và Delivery Output khác nhau thế nào?
- [ ] Capability khác Agent Version ở đâu?
- [ ] Workflow Release khác Run ở đâu?
- [ ] Vì sao alias không được dùng làm runtime reference cuối cùng?
- [ ] Frozen Run Manifest được tạo lúc nào?
- [ ] Checkpoint khác Artifact Revision thế nào?
- [ ] Artifact khác Artifact Revision thế nào?
- [ ] Latest revision khác Approved Baseline thế nào?
- [ ] Rollback thực chất thay đổi object nào?
- [ ] Thành phần nào phải immutable?
- [ ] Thành phần nào được phép là mutable pointer?
- [ ] LangGraph sở hữu state nào?
- [ ] MLflow sở hữu state nào?
- [ ] Harness Hub phải tự xây phần nào?
- [ ] Lineage trả lời câu hỏi nghiệp vụ nào?
- [ ] Vì sao POC chưa cần graph database?

**Exit criteria:** trả lời được tối thiểu 14/17 câu mà không cần mở lại phần định nghĩa.

---

# 12. Đầu vào cho tài liệu tiếp theo

Sau tài liệu này, bước học tiếp theo là:

```text
02_solution_landscape.md
```

Tài liệu đó chỉ cần trả lời ba câu hỏi:

1. LangGraph, MLflow, Git và Harness Hub đang giải quyết phần nào?
2. Thiết kế nào nên mượn?
3. Phần nào Harness Hub phải tự xây?

Không mở rộng thêm scope trước khi hoàn tất SDD cho vertical slice Version Governance.