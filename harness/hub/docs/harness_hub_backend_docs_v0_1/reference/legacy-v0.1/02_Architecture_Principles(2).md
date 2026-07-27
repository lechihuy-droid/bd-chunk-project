# Architecture Principles

> Superseded by the normative documents in `../../design/`.

```yaml
document_id: HH-ARCH-002
document_type: Architecture Guideline
title: Architecture Principles
version: 0.2
status: In Review
owner: System Architecture
reviewers:
  - Backend Lead
  - Platform Lead
  - Security Lead
  - QA Lead
implementation_readiness: Architecture baseline only
depends_on:
  - 00_README.md
  - 01_System_Architecture_Overview.md
related_documents:
  - 03_Backend_Module_Map.md
  - 04_Domain_Model.md
  - 05_BD_Workflow_Runtime.md
  - 06_BD_Orchestrator_Agent.md
  - 07_DD_Executor_Contract.md
  - 13_Security_and_Governance.md
  - 14_Infrastructure_and_Deployment.md
  - 16_Test_Strategy_and_Acceptance.md
```

## 1. Mục đích

Tài liệu này định nghĩa các nguyên tắc kiến trúc bắt buộc cho Harness Hub Backend.

Mục tiêu là đảm bảo:

- Các module có trách nhiệm rõ ràng.
- Runtime hoạt động ổn định trong môi trường distributed.
- Agent và model không được phép kiểm soát trực tiếp state, security hoặc infrastructure.
- API Executor và CLI Executor có hành vi thống nhất.
- Hệ thống có thể mở rộng mà không phá vỡ contract hiện có.
- Coding agent không tự đưa ra quyết định kiến trúc ngoài phạm vi task.

Các nguyên tắc trong tài liệu này có mức ưu tiên cao hơn Basic Design, Detailed Design và Implementation Plan.

---

## 2. Quy tắc diễn giải

Các từ khóa mang ý nghĩa ràng buộc:

- **MUST:** bắt buộc.
- **MUST NOT:** không được phép.
- **SHOULD:** nên thực hiện, trừ khi có lý do kỹ thuật được ghi nhận.
- **MAY:** tùy chọn.

Khi tài liệu khác mâu thuẫn với nguyên tắc này:

1. Việc implement MUST dừng tại phạm vi bị ảnh hưởng.
2. Phải tạo Architecture Clarification Request.
3. Chỉ tiếp tục sau khi có quyết định hoặc ADR được phê duyệt.

---

# 3. Principle 1 — Separation of Responsibilities

Hệ thống MUST phân tách rõ:

```text
Orchestrator = ra quyết định
Runtime      = quản lý state và lifecycle
Executor     = thực thi API / CLI / Tool
Reviewer     = đánh giá output
Policy       = cho phép hoặc từ chối
Artifact     = lưu kết quả bền vững
```

## 3.1 Quy tắc bắt buộc

- Orchestrator MUST NOT cập nhật Runtime state trực tiếp.
- Runtime MUST NOT tự viết business instruction thay cho Orchestrator.
- Executor MUST NOT quyết định workflow route.
- Reviewer MUST NOT trực tiếp retry worker.
- Artifact Service MUST NOT điều khiển workflow.
- UI MUST NOT gọi provider hoặc CLI trực tiếp.
- Policy Engine MUST có quyền phủ quyết decision của Orchestrator.
- Registry module MUST chỉ quản lý definition và version, không thực thi.

## 3.2 Mục đích

Phân tách này giúp:

- Giảm coupling.
- Dễ audit.
- Dễ retry và recovery.
- Không để model probabilistic kiểm soát state deterministic.
- Thay provider hoặc executor mà không sửa Runtime Core.

---

# 4. Principle 2 — Contract-first Architecture

Mọi giao tiếp liên module MUST dựa trên contract versioned và machine-validatable.

## 4.1 Contract tối thiểu

Một contract MUST có:

- Contract ID.
- Version.
- Input schema.
- Output schema.
- Error schema.
- Correlation ID.
- Idempotency key.
- Security context.
- Timeout/deadline.
- Compatibility rule.
- Ownership.
- Deprecation policy.

## 4.2 Breaking change

Breaking change gồm:

- Xóa field bắt buộc.
- Đổi datatype.
- Đổi meaning của field.
- Đổi state transition.
- Đổi permission semantics.
- Đổi error handling semantics.
- Đổi delivery guarantee.

Breaking change MUST tạo major version mới hoặc ADR migration plan.

## 4.3 Machine-checkable specification

Các contract quan trọng SHOULD được biểu diễn bằng:

- JSON Schema.
- OpenAPI.
- AsyncAPI hoặc Event Catalogue.
- SQL DDL.
- Policy schema.
- State transition table.

Prose không được xem là đủ cho contract có ảnh hưởng đến code.

---

# 5. Principle 3 — Deterministic Core, Probabilistic Edge

Các phần liên quan đến state, security và lifecycle MUST deterministic.

## 5.1 Deterministic responsibilities

- State transition.
- Dependency resolution.
- Retry count.
- Timeout.
- Cancellation.
- Idempotency.
- Permission.
- Budget.
- File access.
- Artifact versioning.
- Audit recording.
- Queue lease.
- Concurrency.
- Human approval requirement.

## 5.2 Probabilistic responsibilities

LLM hoặc Agent MAY xử lý:

- Task decomposition.
- Instruction generation.
- Agent selection proposal.
- Repair strategy.
- Semantic review.
- Ambiguity detection.
- User clarification proposal.

## 5.3 Guardrail

LLM output MUST được validate bằng schema và policy trước khi ảnh hưởng đến Runtime.

LLM confidence MUST NOT được dùng như bằng chứng duy nhất cho:

- Security permission.
- Data classification.
- Budget approval.
- Artifact deletion.
- Production deployment.
- Cross-workspace access.

---

# 6. Principle 4 — Runtime is the Source of Truth

Workflow Runtime MUST là nguồn sự thật duy nhất cho:

- Workflow Run status.
- Node Run status.
- Node Attempt status.
- Current retry count.
- Active wait condition.
- Pause/resume state.
- Cancellation state.
- Execution lease.

Không module nào được cập nhật trực tiếp các trạng thái trên.

## 6.1 State mutation

Mọi state mutation MUST:

1. Validate current state.
2. Validate expected version.
3. Validate policy.
4. Persist transition.
5. Persist outbox event cùng transaction.
6. Publish event sau commit.

## 6.2 Optimistic concurrency

Các command ảnh hưởng đến state MUST chứa:

- `expected_version`, hoặc
- `expected_state`, hoặc
- tương đương concurrency token.

Nếu state đã thay đổi, command MUST bị từ chối với lỗi conflict thay vì ghi đè.

---

# 7. Principle 5 — Event-driven, At-least-once Delivery

Runtime event và command được thiết kế theo mô hình **at-least-once delivery**.

Hệ thống MUST NOT giả định message chỉ được giao một lần.

## 7.1 Hệ quả bắt buộc

Mỗi consumer MUST:

- Idempotent.
- Có deduplication key.
- Có retry policy.
- Có dead-letter handling.
- Có correlation metadata.
- Có ordering rule theo aggregate hoặc run.

## 7.2 Transactional outbox

State transition và outbox event MUST được persist trong cùng một database transaction.

```text
State changed
+ Outbox event appended
= One transaction
```

Publisher đọc outbox và gửi event ra stream/broker.

## 7.3 Event ordering

- Event ordering chỉ được đảm bảo trong phạm vi cùng một `run_id` hoặc aggregate key.
- Consumer MUST xử lý duplicate.
- Consumer MUST phát hiện out-of-order event.
- Event không hợp lệ theo current state phải bị reject hoặc defer theo rule được định nghĩa.

---

# 8. Principle 6 — Command and Event Separation

Command và Event là hai loại message khác nhau.

## 8.1 Command

Command thể hiện yêu cầu thực hiện:

```text
START_RUN
EXECUTE_NODE
RETRY_NODE
PAUSE_RUN
RESUME_RUN
CANCEL_RUN
APPROVE_REVIEW
```

Command:

- Có thể bị từ chối.
- Có target cụ thể.
- Phải validate permission và expected state.
- Không được xem là sự thật cho đến khi Runtime apply thành công.

## 8.2 Event

Event thể hiện sự việc đã xảy ra:

```text
RUN_STARTED
NODE_STARTED
NODE_COMPLETED
REVIEW_NO_GO
ARTIFACT_VERSION_CREATED
```

Event:

- Là immutable record.
- Không được sửa.
- Có sequence.
- Có source.
- Có occurred-at time.

---

# 9. Principle 7 — Idempotency Everywhere

Các operation có thể được gửi lại do timeout, reconnect hoặc worker recovery.

## 9.1 Bắt buộc áp dụng

Idempotency MUST được hỗ trợ cho:

- Create Workflow Run.
- Submit Execution.
- Complete Execution.
- Create Artifact Version.
- Submit Review Result.
- Apply Orchestrator Decision.
- Pause/Resume/Cancel.
- Human approval.

## 9.2 Idempotency record

Idempotency record SHOULD lưu:

- Idempotency key.
- Request hash.
- Result reference.
- Creation time.
- Expiration time.
- Actor.
- Workspace.

Cùng key nhưng request khác MUST bị từ chối.

---

# 10. Principle 8 — Immutable Definitions and Provenance

Mọi version đã được một run sử dụng MUST immutable.

Các đối tượng MUST versioned:

- Workflow Definition.
- Agent Definition.
- Skill Definition.
- Prompt/instruction bundle.
- Contract.
- Policy bundle.
- Model routing policy.
- Artifact.
- Reviewer configuration.

Workflow Run MUST lưu reference chính xác đến các version đã dùng.

## 10.1 Provenance tối thiểu

Mỗi output MUST truy vết được:

```text
Workspace
→ Workflow Version
→ Run
→ Node
→ Attempt
→ Agent Version
→ Skill Versions
→ Model / Provider
→ Input References
→ Review Result
→ Artifact Version
```

---

# 11. Principle 9 — Safe-by-default and Fail-closed

Security và policy check MUST fail-closed.

Nếu không xác định được permission, hệ thống MUST từ chối execution thay vì cho phép.

## 11.1 Default deny

Default deny áp dụng cho:

- Filesystem.
- Network egress.
- Tool access.
- Provider access.
- Secret access.
- Cross-workspace resource.
- Artifact publication.
- Production-affecting action.

## 11.2 Secret handling

- Secret material MUST NOT được lưu trong prompt.
- Secret MUST NOT xuất hiện trong artifact.
- Secret MUST NOT xuất hiện trong log.
- Database nghiệp vụ chỉ lưu secret reference.
- Credential SHOULD là short-lived nếu executor hỗ trợ.
- Secret resolution MUST được audit.

## 11.3 Untrusted output

Các nguồn sau MUST được xem là untrusted:

- Model response.
- Tool response.
- CLI output.
- Generated file.
- User-supplied file.
- External webhook payload.

Untrusted output phải được validate, scan và policy-check trước khi publish hoặc dùng làm command.

---

# 12. Principle 10 — Workspace and Tenant Isolation

Mọi resource MUST thuộc về một workspace hoặc tenant context rõ ràng.

## 12.1 Isolation requirements

- Query MUST filter theo workspace.
- Authorization MUST kiểm tra membership và role.
- Cross-workspace reference mặc định bị cấm.
- CLI workspace MUST chỉ mount resource được cấp.
- Artifact content access MUST kiểm tra workspace và classification.
- Cache key MUST chứa workspace scope.
- Queue message MUST chứa workspace scope.
- Audit event MUST chứa workspace scope.

## 12.2 Shared infrastructure

Có thể dùng chung database, queue hoặc object storage, nhưng logical isolation MUST được thực thi và kiểm thử.

Nếu dùng Row-Level Security hoặc schema-per-tenant, quyết định phải được ghi trong ADR.

---

# 13. Principle 11 — Policy Precedence is Explicit

Policy có thể đến từ nhiều cấp:

```text
Platform
→ Workspace
→ Project / Orchestrator Instance
→ Workflow
→ Run
→ Node
```

## 13.1 Quy tắc

- Policy precedence MUST được định nghĩa rõ.
- Lower level MAY siết chặt hơn.
- Lower level MUST NOT nới lỏng hard platform policy.
- Conflict phải fail-closed.
- Policy version phải được lưu trong Run provenance.

## 13.2 Hard và soft policy

### Hard policy

Không được override:

- Security boundary.
- Data residency.
- Provider ban.
- Max production permission.
- Secret scope.

### Soft policy

Có thể override trong giới hạn:

- Preferred model.
- Retry count.
- Timeout.
- Cost warning.
- Review threshold.

---

# 14. Principle 12 — Bounded Retry, Timeout and Cancellation

Không được retry vô hạn.

## 14.1 Retry classification

Runtime MUST phân biệt:

- Provider transient error.
- Network error.
- Contract failure.
- Review NO-GO.
- Security denial.
- Missing user input.
- Internal bug.

## 14.2 Retry ownership

- Executor retry transport-level transient error trong giới hạn.
- Runtime retry node-level execution.
- Orchestrator đề xuất repair/reroute.
- Reviewer không tự retry.
- Security denial không tự retry.

## 14.3 Cancellation

Cancellation MUST propagate đến:

- Queue lease.
- Executor.
- API stream.
- CLI process tree.
- Tool execution.
- Child node chưa chạy.

Cancellation không được xóa lịch sử attempt đã có.

---

# 15. Principle 13 — Backward Compatibility and Deprecation

Contract được publish MUST có deprecation policy.

## 15.1 Compatibility

- Add optional field: thường backward-compatible.
- Add required field: breaking.
- Remove field: breaking.
- Change enum semantics: breaking.
- Change error behavior: breaking.
- Change state transition: breaking.

## 15.2 Deprecation

Deprecated version phải có:

- Deprecation date.
- Replacement version.
- Migration guide.
- End-of-support date.
- List workflow/run còn phụ thuộc.

Run đang chạy MUST tiếp tục dùng version đã pin.

---

# 16. Principle 14 — No Shared Mutable Agent Memory

Agent memory không được dùng làm nguồn sự thật cho workflow.

## 16.1 Quy tắc

- Run context phải được persist ngoài agent process.
- Agent session mất đi không được làm mất workflow state.
- Sticky session chỉ là optimization, không phải source of truth.
- Agent memory không được chia sẻ giữa workspace nếu không có policy rõ.
- Context cần thiết để retry phải tái tạo được từ persisted references.

---

# 17. Principle 15 — Observable-by-default

Mỗi operation quan trọng MUST có:

- Correlation ID.
- Trace ID.
- Run ID.
- Node ID.
- Attempt ID.
- Actor.
- Workspace.
- Duration.
- Status.
- Error code.
- Provider/model/executor.
- Usage and cost.
- Artifact references.

## 17.1 Telemetry separation

- Operational log phục vụ debug.
- Metric phục vụ monitoring.
- Trace phục vụ distributed execution.
- Audit event phục vụ compliance.

Không được dùng operational log như audit source duy nhất.

## 17.2 Redaction

Telemetry pipeline MUST redact:

- Credential.
- Authorization header.
- Secret value.
- Sensitive file content.
- Restricted prompt fragment theo policy.

---

# 18. Principle 16 — SLO-driven Design

Các subsystem MUST có SLO và error budget trước production.

Ví dụ quality attributes cần chốt:

- API availability.
- Run command latency.
- Event stream latency.
- Queue wait time.
- Recovery time.
- Maximum active runs.
- Artifact durability.
- Provider failure tolerance.
- RPO/RTO.

Không được microservice hóa hoặc scale phức tạp nếu chưa có SLO hoặc capacity evidence.

---

# 19. Principle 17 — Graceful Degradation

Hệ thống SHOULD có degraded mode thay vì fail toàn bộ khi một dependency không sẵn sàng.

Ví dụ:

- Provider A unavailable → Router MAY chọn provider B nếu policy cho phép.
- Event stream UI lỗi → Runtime vẫn tiếp tục chạy.
- Reviewer Agent unavailable → Runtime MAY pause và yêu cầu human review.
- Artifact preview lỗi → Artifact content vẫn phải tải được.
- Metrics backend lỗi → execution không bị dừng, nhưng audit bắt buộc không được mất.

Security, state persistence và audit-critical path không được fail-open.

---

# 20. Principle 18 — Portability Before Premature Optimization

MVP SHOULD dùng modular monolith và worker pool với boundary rõ.

## 20.1 Không khóa cứng

Business/domain code MUST NOT phụ thuộc trực tiếp:

- Cloud-specific SDK.
- Provider-specific SDK.
- Queue product API.
- Object storage product API.
- Secret manager product API.

Phụ thuộc infrastructure phải qua ports/adapters.

## 20.2 Khi nào tách service

Chỉ tách module thành service độc lập khi có ít nhất một lý do:

- Scaling profile khác biệt.
- Security boundary khác biệt.
- Availability requirement khác biệt.
- Deployment cadence khác biệt.
- Team ownership rõ.
- Resource isolation cần thiết.

CLI Executor là ứng viên tách sớm vì security và resource profile riêng.

---

# 21. Principle 19 — Human Accountability

Hệ thống không được làm mờ trách nhiệm con người trong quyết định có rủi ro.

Human approval MUST được yêu cầu khi:

- Xóa hoặc ghi đè dữ liệu quan trọng.
- Deploy production.
- Vượt hard budget.
- Gửi restricted data ra provider không phù hợp.
- Cấp thêm tool/filesystem/network permission.
- Reviewer trả blocking conflict.
- Orchestrator không có action hợp lệ.
- Decision có tác động vượt phạm vi workflow.

Human decision phải có:

- Actor.
- Timestamp.
- Scope.
- Before/after state.
- Reason.
- Correlation.
- Audit event.

---

# 22. Principle 20 — Coding Agent Must Not Invent Architecture

Coding agent MUST dừng và yêu cầu clarification khi:

- Contract chưa tồn tại.
- Hai tài liệu mâu thuẫn.
- Cần breaking change.
- Cần thêm infrastructure dependency.
- Cần mở permission mới.
- Cần đổi database schema ngoài task.
- Cần đổi policy precedence.
- Cần chọn cloud/product chưa được quyết định.
- Cần nới lỏng sandbox hoặc network rule.

Coding agent MAY:

- Đề xuất phương án.
- Tạo ADR draft.
- Tạo clarification request.
- Implement trong contract hiện có.

Coding agent MUST NOT tự phê duyệt đề xuất của chính nó.

---

# 23. Architectural conformance checks

Các nguyên tắc nên được kiểm tra tự động bằng:

- Import boundary test.
- API contract test.
- JSON Schema validation.
- State-machine property test.
- Idempotency integration test.
- Security policy test.
- Secret scan.
- Cross-workspace isolation test.
- Executor conformance test.
- Artifact immutability test.
- Event ordering/deduplication test.

---

# 24. Quyết định đã chốt trong tài liệu này

1. Runtime event dùng at-least-once delivery.
2. Consumer phải idempotent.
3. Transactional outbox là pattern mặc định cho Runtime event.
4. Runtime state có optimistic concurrency.
5. Policy fail-closed.
6. Workspace isolation áp dụng trên toàn bộ data, queue, cache và executor.
7. Runtime event và audit event tách biệt.
8. LLM confidence không phải security control.
9. Sticky session không phải source of truth.
10. Version đã được run sử dụng là immutable.
11. Coding agent không được tự quyết architecture.
12. Modular monolith là lựa chọn mặc định cho MVP.

---

# 25. Open decisions

Các điểm sau chưa được chốt:

- Công nghệ queue/broker.
- Cách implement transactional outbox.
- Row-Level Security hay application-enforced tenancy.
- Policy engine/library.
- Exact SLO values.
- Audit storage technology.
- Retention period.
- Data residency configuration model.
- Circuit breaker library.
- Cache/lock implementation.

Các quyết định này phải được ghi trong ADR trước khi trở thành dependency production.

---

# 26. Acceptance criteria của tài liệu

Tài liệu được duyệt khi:

- Backend Lead xác nhận các boundary có thể enforce trong code.
- Platform Lead xác nhận event, queue và outbox model khả thi.
- Security Lead xác nhận fail-closed, isolation và secret principles.
- QA Lead xác nhận các nguyên tắc có thể chuyển thành conformance test.
- Không còn module nào được phép bypass Runtime, Policy hoặc Executor contract.
- Basic Design và Detailed Design tiếp theo reference rõ các principle liên quan.

---

# 27. Change log

| Version | Thay đổi |
|---|---|
| 0.1 | Nguyên tắc kiến trúc ban đầu |
| 0.2 | Bổ sung at-least-once delivery, transactional outbox, optimistic concurrency, tenant isolation, policy precedence, fail-closed, backward compatibility, SLO, degraded mode, immutable provenance, no shared mutable agent memory và coding-agent stop conditions |
