# Harness Hub Backend Documentation — System Architect Review

> Superseded by `../../01_OVERALL_ASSESSMENT.md`; retained as the original review.

**Reviewer role:** Principal / Lead System Architect  
**Reviewed set:** `harness_hub_backend_docs_v0_1`  
**Review version:** 0.1  
**Verdict:** **Conditionally approved as an architecture baseline; not yet approved as an implementation baseline.**

---

## 1. Executive assessment

Bộ tài liệu đã xác lập đúng “xương sống” kiến trúc:

- Orchestrator quyết định.
- Runtime quản lý vòng đời.
- Executor thực thi.
- Reviewer đánh giá.
- Artifact lưu kết quả có version.
- API và CLI được chuẩn hóa sau một executor contract.

Đây là hướng kiến trúc hợp lý cho một nền tảng agentic workflow đa model. Tuy nhiên, phần lớn tài liệu hiện mới ở mức **architecture note / design outline**, chưa đạt độ chi tiết tương ứng với nhãn `Basic Design` hoặc `Detailed Design`.

### Điểm đánh giá

| Hạng mục | Điểm | Nhận xét |
|---|---:|---|
| Tính nhất quán của ý tưởng kiến trúc | 8/10 | Phân tách trách nhiệm đúng |
| Khả năng giao tiếp với stakeholder | 8/10 | Dễ đọc, dễ hiểu |
| Độ đầy đủ của Basic Design | 5/10 | Thiếu state, sequence, policy precedence |
| Độ đầy đủ của Detailed Design | 3/10 | Chưa đủ schema/interface để code trực tiếp |
| Security và vận hành | 5/10 | Có nguyên tắc nhưng thiếu threat model và control cụ thể |
| Mức sẵn sàng cho coding agent | 4/10 | Agent vẫn phải tự suy diễn nhiều quyết định |

### Kết luận kiến trúc

**Có thể sử dụng bộ tài liệu hiện tại để:**

- Đồng thuận kiến trúc cấp cao.
- Thảo luận module boundary.
- Xây backlog POC.
- Tạo mockup và proof of concept.

**Chưa nên sử dụng trực tiếp để:**

- Giao toàn bộ backend cho coding agent tự implement.
- Chốt API liên module.
- Chốt database production.
- Xây runtime có khả năng phục hồi và chạy song song an toàn.
- Đưa CLI executor vào môi trường chứa dữ liệu thật.

---

## 2. Các blocker xuyên suốt bộ tài liệu

### B1. Chưa có source-of-truth hierarchy

Khi hai tài liệu mâu thuẫn, chưa định nghĩa tài liệu nào được ưu tiên. Cần quy định:

```text
Architecture Decision Record
    > Architecture Principles
    > Domain and Contract Specifications
    > Basic Design
    > Detailed Design
    > Implementation Plan
```

### B2. Chưa có glossary chuẩn

Các thuật ngữ sau có nguy cơ bị dùng lẫn:

- Reviewer Agent.
- Review Manager.
- Review Gate.
- Gate.
- Orchestrator node.
- Orchestrator Agent.
- Runtime event.
- Audit event.
- Workspace file.
- Artifact.
- Output.
- Skill.
- Tool.

Cần một tài liệu glossary có định nghĩa, ownership và lifecycle.

### B3. Runtime state machine chưa đủ để implement

Danh sách state không thay thế được transition specification. Cần bảng:

| Current state | Trigger | Guard | Action | Next state | Event |
|---|---|---|---|---|---|

Phải định nghĩa cả run-level, node-level và execution-level state machine.

### B4. Event và command contract chưa được chốt

Cần catalogue riêng cho:

- Event type.
- Command type.
- Schema version.
- Ordering.
- Delivery semantics.
- Deduplication.
- Retry.
- Correlation.
- Consumer ownership.

Nếu dùng queue theo cơ chế at-least-once, phải mô tả transactional outbox và idempotent consumer.

### B5. Workflow Definition chưa có schema

Canvas cần xuất ra một graph contract chính thức, bao gồm:

- Node schema.
- Typed ports.
- Edge condition.
- Join strategy.
- Error edge.
- Input binding.
- Output binding.
- Retry policy.
- Review policy.
- Timeout.
- Version compatibility.

### B6. API Specification chưa phải Detailed Design

Danh sách endpoint chưa đủ để coding agent triển khai đồng nhất. Cần OpenAPI hoặc schema tương đương với:

- Request body.
- Response body.
- Status code.
- Error code.
- Pagination.
- Filtering.
- Idempotency.
- ETag hoặc optimistic concurrency.
- Authorization.
- Async operation semantics.

### B7. Database Schema chưa phải schema hoàn chỉnh

Thiếu:

- Full DDL.
- Foreign key.
- Check constraint.
- Enum strategy.
- Optimistic locking.
- Tenant key.
- Outbox.
- Lease.
- Session.
- Policy.
- Folder/resource.
- Hook.
- Model registry.
- Secret reference.

### B8. Security mới ở mức principle

CLI executor là thành phần rủi ro cao nhưng chưa có:

- Threat model.
- Sandbox escape analysis.
- Image and dependency supply-chain control.
- Egress proxy design.
- Prompt injection and data-exfiltration control.
- DLP.
- Incident response.
- Audit immutability.

### B9. Không có NFR và SLO

Cần chốt tối thiểu:

- Availability.
- Maximum active runs.
- Queue latency.
- Event delivery latency.
- Artifact size.
- API latency.
- Recovery time.
- RPO/RTO.
- Cost ceiling.
- Data retention.

### B10. Coding agent chưa có đủ stop conditions

Task template cần chỉ rõ khi nào agent phải dừng thay vì tự quyết:

- Contract không tồn tại.
- Schema mâu thuẫn.
- Cần thêm dependency.
- Cần đổi database.
- Cần mở filesystem/network permission.
- Cần breaking API change.

---

# 3. Review từng tài liệu

## 00_README.md

**Đánh giá:** Cần bổ sung vừa phải  
**Mức sẵn sàng:** 65%

### Điểm tốt

- Danh mục rõ.
- Phân loại Architecture, Basic Design, Detailed Design và Test.
- Có quy ước MUST/MUST NOT.
- Hướng đến cả con người và coding agent.

### Vấn đề

- Chưa có owner của từng tài liệu.
- Chưa có trạng thái vòng đời: Draft, In Review, Approved, Superseded.
- Chưa có quy trình change control.
- Chưa có source-of-truth precedence.
- Chưa có glossary và ADR index.
- Chưa có dependency map giữa tài liệu.
- Không ghi prerequisite trước khi một tài liệu được “approved for coding”.

### Bổ sung bắt buộc

Thêm metadata chuẩn:

```yaml
document_id:
owner:
reviewers:
status:
version:
last_updated:
supersedes:
depends_on:
implementation_readiness:
```

Thêm:

- Documentation governance.
- Approval workflow.
- Traceability matrix.
- Definition of Ready cho coding.
- Definition of Done cho tài liệu.

---

## 01_System_Architecture_Overview.md

**Đánh giá:** Ý tưởng đúng, diagram chưa phản ánh đầy đủ execution path  
**Mức sẵn sàng:** 60%

### Điểm tốt

- Tách được Runtime, Orchestrator, Executor, Reviewer và Artifact Store.
- Luồng GO/NO-GO dễ hiểu.
- Ranh giới MVP hợp lý.

### Vấn đề

Sequence diagram đang thể hiện:

```text
Runtime → Agent
```

Trong khi nguyên tắc hệ thống là mọi execution phải qua:

```text
Runtime → Execution Router → Executor → Model/CLI
```

Điều này tạo mâu thuẫn kiến trúc. Ngoài ra diagram thiếu:

- Identity and workspace.
- Policy Engine.
- Secrets Broker.
- Queue.
- Model Registry.
- Object storage.
- Human review.
- External providers.
- Observability.
- Trust boundaries.

`Backend API` cũng đang gộp API Gateway và Application Backend thành một khối.

### Bổ sung bắt buộc

Tách thành ba diagram:

1. **C4 System Context:** User, external model providers, source control, storage.
2. **C4 Container:** API, Runtime Worker, Executors, DB, Queue, Object Storage.
3. **Runtime Sequence:** Runtime gọi executor, không gọi agent trực tiếp.

Chỉ rõ reviewer chạy theo một trong hai mô hình:

- Reviewer là Agent được thực thi qua Executor.
- Reviewer là deterministic validation service.

---

## 02_Architecture_Principles.md

**Đánh giá:** Nền tảng tốt nhưng còn thiếu nguyên tắc distributed system  
**Mức sẵn sàng:** 70%

### Điểm tốt

- Separation of concerns rất rõ.
- Contract-first đúng hướng.
- Deterministic core / probabilistic edge là nguyên tắc quan trọng.
- Safe-by-default và observable-by-default phù hợp.

### Vấn đề

Thiếu các nguyên tắc then chốt:

- At-least-once delivery.
- Transactional outbox.
- Idempotent consumer.
- Optimistic concurrency.
- Backward compatibility.
- Tenant isolation.
- Data residency.
- Fail-closed vs fail-open.
- Degraded mode.
- SLO-driven design.
- No shared mutable agent memory.
- Immutable execution provenance.

“Runtime SHOULD phát event” nên là **MUST** nếu event là contract chính với Orchestrator.

### Bổ sung bắt buộc

Thêm nguyên tắc:

- Runtime state transition và outbox event phải atomic.
- Mọi command phải có expected state/version.
- Provider failure không được làm mất run state.
- Policy decision phải fail-closed.
- Version đã dùng trong run phải immutable.
- Không dùng LLM confidence làm security decision.

---

## 03_Backend_Module_Map.md

**Đánh giá:** Danh sách module tốt, dependency map còn quá sơ lược  
**Mức sẵn sàng:** 55%

### Điểm tốt

- Module boundary tương đối hợp lý.
- Có dependency bị cấm.
- Repository layout phù hợp modular monolith.

### Vấn đề

Diagram không thể hiện nhiều module đã liệt kê:

- Identity & Workspace.
- Skill Registry.
- Model Registry.
- Policy Engine.
- Event Service.
- Secrets Broker.

Chưa chỉ ra:

- Module sở hữu table nào.
- Module publish event nào.
- Module consume event nào.
- Synchronous hay asynchronous call.
- Transaction boundary.
- Deployment boundary.
- Failure ownership.

`Event Service` và `Audit` cần phân biệt. Runtime event phục vụ control flow; audit event phục vụ compliance và không nên có cùng retention/immutability.

### Bổ sung bắt buộc

Tạo một bảng module contract:

| Module | Owns data | Exposes commands | Exposes queries | Publishes | Consumes |
|---|---|---|---|---|---|

Thêm dependency rule tự động kiểm tra trong codebase, ví dụ import boundary test.

---

## 04_Domain_Model.md

**Đánh giá:** Domain skeleton tốt, aggregate boundary và lifecycle còn thiếu  
**Mức sẵn sàng:** 50%

### Điểm tốt

- Có Definition/Version và Run/Attempt.
- Phân biệt Artifact và ArtifactVersion.
- Reviewer verdict và Orchestrator action được chuẩn hóa.
- Có invariants ban đầu.

### Vấn đề

Thiếu nhiều domain object quan trọng:

- WorkflowNodeDefinition.
- WorkflowEdgeDefinition.
- PortContract.
- InputBinding.
- ExecutionLease.
- HumanReviewTask.
- OrchestratorInstance.
- ModelDefinition.
- ProviderDefinition.
- ToolDefinition.
- PolicyBundle.
- Budget.
- WorkspaceFolder / Resource.
- HookDefinition.
- ExecutorSession.
- RuntimeCommand.
- RuntimeEvent.

Đặt `ORCHESTRATOR` là node type có thể mâu thuẫn với mô hình “Orchestrator nằm trên workflow”. Cần chọn rõ:

- Orchestrator là control-plane actor của run; hoặc
- Orchestrator là executable node trong graph.

Có thể hỗ trợ cả hai, nhưng phải đặt tên khác nhau.

Danh sách state chưa có transition và terminal-state rule.

### Bổ sung bắt buộc

- Aggregate boundary.
- Entity identifiers.
- State transition tables.
- Optimistic version field.
- Domain events.
- Policy precedence.
- Relationship giữa Workspace File và Artifact.

---

## 05_BD_Workflow_Runtime.md

**Đánh giá:** Là tài liệu quan trọng nhất nhưng hiện chưa đủ Basic Design  
**Mức sẵn sàng:** 40%

### Điểm tốt

- Trách nhiệm Runtime được xác định đúng.
- Runtime loop có lock, transition và persistence.
- Có recovery, retry và GO/NO-GO.
- Acceptance nhắm đúng golden path.

### Vấn đề nghiêm trọng

Thiếu:

- Run state machine đầy đủ.
- Node state machine đầy đủ.
- Execution state machine đầy đủ.
- Graph validation.
- Fan-out/fan-in semantics.
- Join strategy: ALL, ANY, QUORUM.
- Conditional edge.
- Cancellation propagation.
- Node timeout vs run timeout.
- Lease/heartbeat schema.
- Queue delivery semantics.
- Out-of-order event handling.
- Duplicate result handling.
- Compensation/rollback.
- Partial failure trong parallel branch.
- Dynamic rerouting.
- Human task lifecycle.
- Transactional outbox.
- Scheduler fairness và concurrency limit.

“Persist state và event cùng transaction” chỉ đúng nếu event nằm trong outbox/database. Nếu publish trực tiếp ra broker thì không atomic.

### Bổ sung bắt buộc

Tách thêm tài liệu:

- Runtime State Transition Specification.
- Scheduler and Dependency Resolution.
- Event/Command Processing.
- Recovery and Lease Management.

Thêm pseudo-code cho:

- Mark node ready.
- Claim node.
- Complete attempt.
- Apply reviewer verdict.
- Apply orchestrator decision.
- Cancel run.

---

## 06_BD_Orchestrator_Agent.md

**Đánh giá:** Concept hợp lý, contract quyết định còn thiếu safety và concurrency  
**Mức sẵn sàng:** 50%

### Điểm tốt

- Phân biệt template và project instance.
- Orchestrator không thực thi process.
- Có action allow-list.
- Không phụ thuộc private chain-of-thought.

### Vấn đề

Thiếu:

- Khi nào Runtime gọi Orchestrator.
- Khi nào deterministic routing đủ và không cần Orchestrator.
- Timeout cho decision.
- Fallback khi model unavailable.
- Prompt/version provenance.
- Context assembly và token budget.
- Stale decision prevention.
- Policy precedence giữa template, project, workflow và run.
- Decision approval.
- Nested workflow/subworkflow.
- Maximum decision loop.
- Model selection cho chính Orchestrator.
- Memory isolation.

`confidence` do model tự khai báo không đáng tin để quyết định routing hoặc security.

Decision cần chứa:

```text
expected_run_version
trigger_event_id
policy_evaluation_id
expires_at
```

Nếu state đã thay đổi, Runtime phải từ chối stale decision.

### Bổ sung bắt buộc

- Decision state diagram.
- Orchestrator invocation matrix.
- Deterministic fallback.
- Maximum orchestration loop.
- Prompt contract.
- Context redaction.
- Human escalation criteria.

---

## 07_DD_Executor_Contract.md

**Đánh giá:** Hướng abstraction đúng, chưa đủ “unified contract” production-grade  
**Mức sẵn sàng:** 45%

### Điểm tốt

- Request/result thống nhất cho API và CLI.
- Có idempotency.
- Có status, usage và error category.
- Có cancel và stream.

### Vấn đề

ExecutionRequest thiếu hoặc chưa chốt:

- Contract schema version.
- Correlation/trace ID.
- Deadline.
- Workspace mount policy.
- Security principal.
- Data classification.
- Tool permission.
- Session mode.
- Capability requirement.
- Prompt and agent provenance.
- Output path policy.
- Cancellation token.
- Expected artifact type.

ExecutionResult thiếu:

- Provider request/session ID.
- Finish reason.
- Partial output.
- Raw response reference.
- File diff reference.
- Output contract validation result.
- Cost currency.
- Retry-after.
- Resource usage.
- Security scan result.

`max_cost_jpy` làm contract bị khóa vào một currency. Nên dùng:

```json
{"amount_minor": 500, "currency": "JPY"}
```

### Bổ sung bắt buộc

- JSON Schema chính thức.
- Error code catalogue.
- Event sequence contract.
- Exactly-once không nên cam kết; dùng idempotency trên at-least-once.
- Compatibility and version negotiation.
- Conformance test suite cho mọi executor adapter.

---

## 08_DD_API_Executor.md

**Đánh giá:** Pipeline đúng, provider behavior còn thiếu  
**Mức sẵn sàng:** 45%

### Điểm tốt

- Tách Provider Adapter.
- Retry transport error ở executor, business retry ở Runtime.
- Tool call không được adapter tự chạy.
- Security handling đúng hướng.

### Vấn đề

Thiếu:

- Provider rate-limit coordinator.
- Circuit breaker.
- Per-workspace quota.
- Request normalization.
- Response normalization.
- Token counting strategy.
- Streaming backpressure.
- Streaming reconnect.
- Partial response persistence.
- Provider timeout matrix.
- Cancellation capability matrix.
- Safety parameter mapping.
- Data residency and endpoint selection.
- Credential per tenant.
- Tool-call loop ownership chi tiết.
- Provider-specific error map.
- Model capability validation.

### Bổ sung bắt buộc

Tạo `Provider Capability Matrix`:

| Provider | Streaming | Tools | JSON mode | Cancel | Max context | Residency |
|---|---|---|---|---|---|---|

Thêm conformance tests để hai provider trả cùng internal result contract.

---

## 09_DD_CLI_Executor.md

**Đánh giá:** Nền tảng tốt, nhưng chưa đủ cho thành phần có rủi ro cao nhất  
**Mức sẵn sàng:** 35%

### Điểm tốt

- Stateless mặc định là lựa chọn đúng.
- Có process supervisor, timeout và kill tree.
- Có workspace layout và file diff.
- Network deny-by-default hợp lý.

### Vấn đề nghiêm trọng

Chưa quyết định:

- Container runtime hay OS sandbox.
- Rootless mode.
- Seccomp/AppArmor/SELinux.
- Filesystem snapshot/copy-on-write.
- Git clone, branch và patch strategy.
- Network egress implementation.
- DNS control.
- Interactive CLI prompt handling.
- Terminal/PTY protocol.
- Command injection prevention.
- Environment variable allow-list.
- Stdout/stderr size limit.
- File count/size limit.
- Malware/secret scan.
- Binary output policy.
- Sandbox image lifecycle.
- Session recovery.
- Host failure.
- Windows worker support.
- CLI version pinning.

### Bổ sung bắt buộc

- Threat model riêng cho CLI Executor.
- Sandbox architecture.
- Command adapter schema.
- Workspace snapshot and patch model.
- Egress proxy.
- Resource quota.
- Image signing and SBOM.
- Escape detection and incident response.

Không nên cho CLI Executor tiếp cận dữ liệu thật trước khi các mục này được chốt.

---

## 10_BD_Artifact_Store.md

**Đánh giá:** Product flow tốt, domain/storage design còn thiếu  
**Mức sẵn sàng:** 50%

### Điểm tốt

- Phân biệt Workspace View và Generated View.
- Version immutable.
- Edit qua chat tạo version mới.
- Archive không xóa.
- Có lineage và review flow.

### Vấn đề

`Workspace View` và `Generated View` là UI projection; tài liệu BD backend cần định nghĩa model nguồn:

- WorkspaceFolder.
- WorkspaceFile.
- Artifact.
- ArtifactVersion.
- ArtifactPlacement hoặc ResourceLink.

Chưa rõ file do user upload có phải artifact không. Chưa có:

- Content type.
- Object key strategy.
- Upload protocol.
- Large file handling.
- Checksum/dedup.
- Permission inheritance.
- Concurrent version creation.
- Optimistic lock.
- Current version race.
- Retention.
- Malware scan.
- Encryption.
- Preview generation.
- Full-text indexing.
- Reference integrity.
- Delete/purge policy.

### Bổ sung bắt buộc

- Resource taxonomy.
- Artifact lifecycle state machine.
- Version command contract.
- Archive/restore semantics.
- Lineage schema.
- Object storage layout.
- Content access authorization.

---

## 11_DD_Backend_API_Spec.md

**Đánh giá:** Đây mới là API inventory, chưa phải Detailed Design  
**Mức sẵn sàng:** 25%

### Điểm tốt

- Resource grouping hợp lý.
- Có workspace, correlation và idempotency header.
- Có run stream.
- Có artifact view filter.

### Vấn đề nghiêm trọng

Thiếu toàn bộ:

- Request schema.
- Response schema.
- HTTP status.
- Error code.
- Pagination.
- Sorting.
- Filtering semantics.
- Authentication protocol.
- Authorization matrix.
- ETag/If-Match.
- Async operation response.
- Idempotency response behavior.
- SSE reconnect and Last-Event-ID.
- Rate limit.
- File upload/download.
- Content negotiation.
- API version compatibility.

`POST /runs/{id}/pause` cần chỉ rõ synchronous command accepted hay run đã paused.

### Bổ sung bắt buộc

Tạo OpenAPI 3.1. Tách thêm AsyncAPI hoặc Event Catalogue cho SSE/broker events. Sinh contract tests từ spec.

---

## 12_DD_Database_Schema.md

**Đánh giá:** Chưa đạt Detailed Design  
**Mức sẵn sàng:** 25%

### Điểm tốt

- Chọn PostgreSQL hợp lý.
- Có run/node/attempt và artifact version.
- Atomicity rule đúng hướng.
- Có index gợi ý.

### Vấn đề nghiêm trọng

Chưa có full DDL và nhiều table bắt buộc:

- workspace_memberships.
- workflow_nodes/edges hoặc graph schema strategy.
- orchestrator_instances.
- agent_version_skills.
- model_definitions/providers.
- policy_bundles.
- budgets.
- execution_leases.
- executor_sessions.
- human_review_tasks.
- workspace_folders/files.
- artifact_lineage.
- outbox_events.
- audit_events.
- hooks.
- secret_refs.
- idempotency response record.

Thiếu:

- Foreign key đầy đủ.
- NOT NULL.
- Check constraint.
- Enum/check strategy.
- Tenant isolation.
- Row-level security decision.
- Optimistic version.
- Soft delete.
- Partitioning.
- Retention.
- Migration and rollback.
- Backup/restore consistency.

### Bổ sung bắt buộc

Tạo ERD đầy đủ và migration-ready DDL. Chốt:

- UUID generation.
- Timestamp convention.
- JSONB usage rule.
- Event table partition.
- Outbox.
- Lease expiration.
- Locking strategy.

---

## 13_Security_and_Governance.md

**Đánh giá:** Baseline tốt, chưa đủ security architecture  
**Mức sẵn sàng:** 45%

### Điểm tốt

- Có role, classification, secrets, filesystem/network và audit.
- Human approval target đúng.
- Restricted data được xem xét.

### Vấn đề

Thiếu:

- Threat model STRIDE hoặc tương đương.
- Trust boundary diagram.
- Authentication protocol.
- RBAC permission matrix.
- Workspace isolation implementation.
- Encryption at rest/in transit.
- Key management and rotation.
- Audit immutability.
- Prompt injection.
- Tool injection.
- Data exfiltration.
- DLP.
- Supply-chain security.
- Container image signing.
- Dependency scanning.
- Vulnerability management.
- Incident response.
- Break-glass access.
- Data residency.
- Privacy deletion.
- Backup access control.

### Bổ sung bắt buộc

Tạo các tài liệu riêng:

- Threat Model.
- Access Control Matrix.
- CLI Sandbox Security.
- Provider Data Governance.
- Audit and Retention Policy.
- Incident Response Runbook.

---

## 14_Infrastructure_and_Deployment.md

**Đánh giá:** Sơ đồ khởi đầu tốt, chưa đủ để platform engineer triển khai  
**Mức sẵn sàng:** 40%

### Điểm tốt

- Tách MVP và production.
- Chọn PostgreSQL, queue, worker và object storage hợp lý.
- Phân biệt API worker và CLI worker.
- Có environments.

### Vấn đề

Thiếu:

- Network topology.
- Public/private subnet.
- Security group/firewall.
- Service discovery.
- Ingress/auth.
- Container orchestration decision.
- Queue product và delivery semantics.
- Worker autoscaling.
- CLI worker host isolation.
- GPU/local model path.
- Multi-AZ.
- Backup/restore.
- RPO/RTO.
- IaC.
- CI/CD.
- Release strategy.
- Secret manager.
- Observability concrete stack.
- Capacity model.
- SLO.
- Cost model.
- Region/data residency.

Production diagram cũng thiếu:

- Orchestrator Bridge.
- Policy Engine.
- Model Registry.
- Secrets Broker.
- Review Manager.
- Artifact processing.
- Event/audit pipeline.

### Bổ sung bắt buộc

Tạo:

- Deployment topology.
- Network/security zones.
- Environment sizing.
- Scaling policy.
- Disaster recovery.
- IaC module map.
- Operational runbook.

---

## 15_Coding_Agent_Implementation_Plan.md

**Đánh giá:** Cấu trúc task tốt, thứ tự và governance cần siết lại  
**Mức sẵn sàng:** 60%

### Điểm tốt

- Chia phase rõ.
- Có allowed files và forbidden changes.
- Dùng mock executor trước.
- Có golden workflow.
- Chứng minh abstraction bằng hai provider.

### Vấn đề

Security và observability đặt quá muộn. Hai yếu tố này phải được cài từ Phase 0:

- Structured logging.
- Correlation.
- Secret abstraction.
- Permission boundary.
- Audit skeleton.

Thiếu:

- Architecture gate giữa phase.
- Dependency graph.
- Deliverable cụ thể.
- Estimate.
- Human reviewer.
- ADR trigger.
- Migration requirement.
- Rollback.
- Test command.
- Coverage target.
- Stop conditions.
- Definition of Ready.
- Definition of Done.
- Branch/commit convention.

### Khuyến nghị thứ tự

Ưu tiên vertical slice:

```text
Workflow schema
→ Runtime state machine
→ Mock executor
→ Reviewer GO/NO-GO
→ Artifact version
→ API endpoint
→ UI event stream
```

Sau khi golden slice chạy được mới mở rộng API/CLI provider.

---

## 16_Test_Strategy_and_Acceptance.md

**Đánh giá:** Golden scenarios đúng nhưng coverage chưa đủ cho distributed runtime  
**Mức sẵn sàng:** 55%

### Điểm tốt

- Có unit, integration và E2E.
- Golden workflow phản ánh đúng sản phẩm.
- Có restart recovery, timeout và security test.
- Release gate rõ.

### Vấn đề

Thiếu:

- Contract tests.
- Property-based state machine tests.
- Duplicate event.
- Out-of-order event.
- Queue redelivery.
- Concurrent command.
- Stale orchestrator decision.
- Partial streaming.
- Provider returns malformed output.
- Object corruption.
- Concurrent artifact version.
- Two reviewers decide simultaneously.
- Chaos test.
- Load/soak test.
- Backup restore theo RPO/RTO.
- Sandbox escape test.
- DLP/data exfiltration test.
- Deterministic replay.
- Test data management.
- Environment matrix.
- Requirement traceability.

### Bổ sung bắt buộc

Mỗi acceptance criterion phải map tới test ID. Tạo test matrix:

| Requirement | Test ID | Level | Environment | Expected |
|---|---|---|---|---|

---

# 4. Các tài liệu còn thiếu nên bổ sung

## Ưu tiên P0 — trước khi coding runtime thật

1. `17_Glossary_and_Ubiquitous_Language.md`
2. `18_Architecture_Decision_Records_Index.md`
3. `19_Workflow_Definition_Schema.md`
4. `20_Runtime_State_Transition_Spec.md`
5. `21_Runtime_Event_and_Command_Catalogue.md`
6. `22_Policy_and_Budget_Model.md`
7. `23_Review_and_Human_Task_Design.md`

## Ưu tiên P1 — trước API/CLI production

8. `24_Model_Tool_and_Provider_Registry.md`
9. `25_Workspace_File_and_Resource_Model.md`
10. `26_CLI_Sandbox_Threat_Model.md`
11. `27_Observability_SLO_and_Alerting.md`
12. `28_OpenAPI_Specification.yaml`
13. `29_Async_Event_Specification.yaml`
14. `30_Full_Database_DDL.sql`

## Ưu tiên P2 — trước production release

15. `31_Deployment_Topology_and_Network.md`
16. `32_Backup_DR_and_Recovery_Runbook.md`
17. `33_Incident_Response_Runbook.md`
18. `34_Data_Retention_and_Privacy.md`
19. `35_Capacity_and_Cost_Model.md`
20. `36_Release_and_Migration_Strategy.md`

---

# 5. Kế hoạch nâng bộ tài liệu lên mức code-ready

## Gate A — Architecture Approved

Phải hoàn thành:

- Glossary.
- C4 diagrams.
- Module ownership.
- ADRs.
- NFR/SLO.
- Security trust boundaries.

## Gate B — Runtime Contract Approved

Phải hoàn thành:

- Workflow graph schema.
- State transition tables.
- Event and command schemas.
- Executor contract schema.
- Review contract.
- Policy precedence.

## Gate C — Implementation Ready

Phải hoàn thành:

- OpenAPI.
- Full DDL.
- Error catalogue.
- Sequence diagrams.
- Acceptance-test traceability.
- Coding tasks có file scope và stop conditions.

## Gate D — Production Ready

Phải hoàn thành:

- Threat model.
- Sandbox security.
- HA/DR.
- Observability.
- Load test.
- Backup restore.
- Incident runbook.

---

# 6. Final recommendation

Giữ nguyên kiến trúc cốt lõi. Không cần đổi hướng hệ thống.

Việc cần làm tiếp theo không phải viết thêm prose tổng quan, mà là chuyển các quyết định quan trọng thành **machine-checkable contracts**:

- JSON Schema cho workflow, event, command và executor.
- OpenAPI cho backend.
- SQL migration cho database.
- Transition table cho runtime.
- Policy schema.
- Conformance test cho executor.
- Traceability từ requirement đến acceptance test.

Khi hoàn thành các mục P0, bộ tài liệu có thể trở thành **Basic Design chính thức**. Khi hoàn thành P1, coding agent mới có thể triển khai backend với mức tự suy diễn thấp và độ nhất quán cao.
