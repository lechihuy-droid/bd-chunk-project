# Harness Hub Backend Documentation Set

> Superseded by `../../00_INDEX.md`; retained for historical traceability.

| Thuộc tính | Giá trị |
|---|---|
| **Document ID** | HH-BE-DOC-INDEX |
| **Document type** | Documentation Governance / Index |
| **Version** | 0.3 |
| **Status** | In Review |
| **Owner** | System Architecture Owner |
| **Required reviewers** | Backend Lead, Platform Lead, Security Lead, QA Lead |
| **Implementation readiness** | Not Ready — từng tài liệu phải được phê duyệt riêng |
| **Supersedes** | `00_README.md` version 0.2 |
| **Last updated** | 2026-07-27 |

## 1. Mục đích

Bộ tài liệu này chuyển kiến trúc tổng quan của Harness Hub thành các đặc tả có thể kiểm tra, triển khai và truy vết. Đối tượng sử dụng gồm:

- System/Solution Architect.
- Backend và Platform Engineer.
- Security và QA Engineer.
- AI Coding Agent.
- Technical Product Owner.

Harness Hub là nền tảng điều phối workflow AI đa agent, đa model, hỗ trợ execution qua API và CLI. Hệ thống quản lý workflow definition, workflow run, Orchestrator Agent, specialist/reviewer agent, runtime state, artifact, human review, security, cost và audit.

## 2. Phạm vi của bộ tài liệu

Bộ tài liệu hiện tại bao phủ:

- Kiến trúc tổng quan và nguyên tắc thiết kế.
- Ranh giới module và domain model.
- Basic Design cho Workflow Runtime, Orchestrator Agent và Artifact Store.
- Detailed Design ban đầu cho Executor, API, CLI và database.
- Security, infrastructure, implementation plan và test strategy.

Bộ tài liệu **không được xem là implementation-ready chỉ vì đã tồn tại đầy đủ file**. Mỗi tài liệu phải đạt Definition of Ready tại Mục 8 trước khi được giao cho coding agent.

## 3. Danh mục tài liệu

| Thứ tự | File | Loại tài liệu | Mục đích | Trạng thái mục tiêu |
|---:|---|---|---|---|
| 00 | `00_README.md` | Documentation Governance | Danh mục, quy tắc và quy trình phê duyệt | Approved |
| 01 | `01_System_Architecture_Overview.md` | Architecture Guideline | Bức tranh tổng thể và system boundary | Approved for Architecture |
| 02 | `02_Architecture_Principles.md` | Architecture Guideline | Nguyên tắc bắt buộc | Approved for Architecture |
| 03 | `03_Backend_Module_Map.md` | Architecture Guideline | Ranh giới và ownership module | Approved for Architecture |
| 04 | `04_Domain_Model.md` | Architecture Guideline | Aggregate, entity, state và invariant | Approved for Basic Design |
| 05 | `05_BD_Workflow_Runtime.md` | Basic Design | Runtime, scheduler, state và recovery | Approved for Detailed Design |
| 06 | `06_BD_Orchestrator_Agent.md` | Basic Design | Orchestrator contract và decision flow | Approved for Detailed Design |
| 07 | `07_DD_Executor_Contract.md` | Detailed Design | Unified executor request/event/result/capability contract | Draft — merged, review required |
| 07A | `07A_DD_Runtime_Gateway_and_Routing.md` | Detailed Design | Gateway boundary, policy-aware routing và fallback ownership | Draft — merged, review required |
| 08 | `08_DD_API_Executor.md` | Detailed Design | HTTP provider adapter, streaming, retry và cancellation | Draft — merged, review required |
| 09 | `09_DD_CLI_Executor.md` | Detailed Design | CLI process, workspace, cancellation và sandbox | Draft — threat model required |
| 10 | `10_BD_Artifact_Store.md` | Basic Design | Artifact lifecycle, version và archive | Approved for Detailed Design |
| 11 | `11_DD_Backend_API_Spec.md` | Detailed Design | Backend/Gateway API, SSE, idempotency và concurrency | Draft — merged, review required |
| 12 | `12_DD_Database_Schema.md` | Detailed Design | Database schema và transaction rule | Approved for Coding |
| 13 | `13_Security_and_Governance.md` | Cross-cutting Design | Gateway/CLI trust boundaries, policy, secrets và audit | Draft — merged, review required |
| 14 | `14_Infrastructure_and_Deployment.md` | Cross-cutting Design | Hạ tầng, deployment và vận hành | Approved for Deployment |
| 15 | `15_Coding_Agent_Implementation_Plan.md` | Implementation Spec | Chia task cho coding agent | Approved for Execution |
| 16 | `16_Test_Strategy_and_Acceptance.md` | Test Specification | Gateway/executor conformance, recovery và security gates | Draft — merged, review required |
| R01 | `R01_RESEARCH_Runtime_Gateway_Multi_Model.md` | Research Source | Runtime Gateway, routing, reliability và observability research | Reference only |
| R02 | `R02_RESEARCH_Executor_Adapter_Layer.md` | Research Source | Executor adapter, capability, event, CLI lifecycle research | Reference only |

## 4. Thứ tự đọc và dependency

```text
01 System Overview
    ↓
02 Architecture Principles
    ↓
03 Module Map
    ↓
04 Domain Model
    ↓
05 Runtime ───────→ 06 Orchestrator
    ↓                    ↓
07 Executor Contract ────┘
    ↓
07A Runtime Gateway & Routing
    ├──→ 08 API Executor
    └──→ 09 CLI Executor

04 Domain Model ───→ 10 Artifact Store
03–10 + 07A ───────→ 11 Backend API
04–11 ─────────────→ 12 Database Schema
01–12 ─────────────→ 13 Security
01–13 ─────────────→ 14 Infrastructure
05–14 ─────────────→ 15 Implementation Plan
05–15 ─────────────→ 16 Test Strategy

R01 ──research evidence──→ 07A, 11, 13, 16
R02 ──research evidence──→ 07, 08, 09, 13, 16
```

Một tài liệu downstream MUST NOT được phê duyệt nếu tài liệu dependency trực tiếp chưa được phê duyệt hoặc chưa có waiver được ghi nhận.

## 5. Thứ tự ưu tiên khi tài liệu mâu thuẫn

Khi có mâu thuẫn, áp dụng thứ tự ưu tiên sau:

1. Architecture Decision đã được phê duyệt.
2. Architecture Principles.
3. Domain và Contract Specification.
4. Basic Design.
5. Detailed Design.
6. Implementation Plan.
7. Code hiện tại.

Code hiện tại không tự động trở thành source of truth. Nếu code khác tài liệu đã phê duyệt, phải tạo change request hoặc sửa code.

## 6. Trạng thái tài liệu

Mỗi tài liệu MUST có một trong các trạng thái:

| Trạng thái | Ý nghĩa |
|---|---|
| `Draft` | Đang soạn, chưa sẵn sàng review |
| `In Review` | Đang được reviewer đánh giá |
| `Changes Requested` | Chưa đạt, cần sửa |
| `Approved` | Được phê duyệt cho mục đích ghi trong metadata |
| `Superseded` | Đã có version thay thế |
| `Archived` | Không còn dùng cho dự án đang hoạt động |

Không được dùng từ “Approved” mà không ghi rõ phạm vi, ví dụ:

- Approved for Architecture.
- Approved for Detailed Design.
- Approved for Coding.
- Approved for Production.

## 7. Metadata bắt buộc cho từng tài liệu

Mỗi file MUST bắt đầu bằng metadata tương đương:

```markdown
| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-BE-... |
| Document type | Architecture / Basic Design / Detailed Design / ... |
| Version | x.y |
| Status | Draft / In Review / Approved / ... |
| Owner | Role hoặc team sở hữu |
| Required reviewers | Danh sách role |
| Implementation readiness | Not Ready / Conditional / Ready |
| Supersedes | Document/version trước đó |
| Depends on | Document ID/version |
| Last updated | YYYY-MM-DD |
```

Từng tài liệu SHOULD có thêm:

- Mục tiêu.
- Phạm vi và ngoài phạm vi.
- Assumption.
- Quyết định kiến trúc.
- Contract/interface.
- Failure và recovery.
- Security consideration.
- Observability.
- Acceptance criteria.
- Open issues.

## 8. Definition of Ready cho coding

Một tài liệu hoặc task chỉ được giao cho coding agent khi đáp ứng toàn bộ điều kiện:

- [ ] Mục tiêu và phạm vi rõ ràng.
- [ ] Dependency đã được phê duyệt.
- [ ] Interface/schema liên quan đã có version.
- [ ] State transition hoặc lifecycle đã được định nghĩa.
- [ ] Error model đã được định nghĩa.
- [ ] Security và permission đã được xác định.
- [ ] Acceptance criteria có thể kiểm tra.
- [ ] Test case tối thiểu đã được liệt kê.
- [ ] Allowed files/module được chỉ rõ.
- [ ] Breaking change policy được xác định.
- [ ] Không còn open issue mức Blocker.

Nếu thiếu một điều kiện, trạng thái implementation readiness phải là `Not Ready` hoặc `Conditional`.

## 9. Definition of Done cho tài liệu

Một tài liệu được xem là hoàn thành khi:

- Đã được owner và required reviewers phê duyệt.
- Không mâu thuẫn với tài liệu có priority cao hơn.
- Diagram, schema và ví dụ khớp nhau.
- Requirement quan trọng được map tới acceptance criteria.
- Các open issue còn lại có owner và deadline.
- Version và changelog được cập nhật.
- Tài liệu downstream bị ảnh hưởng đã được xác định.

## 10. Quy ước từ khóa

- **MUST:** bắt buộc để hệ thống đúng hoặc an toàn.
- **MUST NOT:** hành vi bị cấm.
- **SHOULD:** khuyến nghị mạnh; ngoại lệ phải có lý do được ghi nhận.
- **SHOULD NOT:** không nên thực hiện; ngoại lệ phải có lý do.
- **MAY:** tùy chọn.

Các từ “có thể”, “thường”, “hợp lý” không được dùng thay cho contract bắt buộc trong Detailed Design.

## 11. Quy tắc thay đổi tài liệu

Mọi thay đổi ảnh hưởng contract, state, security hoặc data model MUST:

1. Ghi rõ lý do thay đổi.
2. Xác định tài liệu và module bị ảnh hưởng.
3. Phân loại backward-compatible hoặc breaking.
4. Cập nhật version.
5. Có reviewer phù hợp.
6. Cập nhật acceptance test.

Quy tắc version:

- **Patch:** sửa lỗi diễn đạt, không đổi hành vi.
- **Minor:** bổ sung backward-compatible.
- **Major:** breaking change hoặc thay đổi trách nhiệm module.

## 12. Quy tắc sử dụng với AI coding agent

Mỗi coding task MUST bao gồm:

- Objective.
- Documents và version phải đọc.
- Contract/schema phải tuân thủ.
- Module/file được phép sửa.
- Hành vi bị cấm.
- Acceptance criteria.
- Test command.
- Expected deliverables.
- Stop conditions.

Coding agent MUST dừng và tạo `Architecture Clarification Request` khi:

- Hai tài liệu mâu thuẫn.
- Contract hoặc schema bị thiếu.
- Task yêu cầu breaking change nhưng không được cho phép.
- Cần thêm dependency hoặc hạ tầng mới.
- Cần mở rộng filesystem, network hoặc secret permission.
- Acceptance criteria không thể kiểm tra.
- Cần thay đổi module ngoài allowed scope.

Coding agent MUST NOT tự thay đổi contract liên module, database strategy, security boundary hoặc API public để “làm cho code chạy”.

## 13. Traceability tối thiểu

Các tài liệu implementation SHOULD duy trì chuỗi truy vết:

```text
Business/Platform Requirement
→ Architecture Decision
→ Module/Domain Responsibility
→ Interface or Data Contract
→ Coding Task
→ Test Case
→ Runtime Evidence
```

Mỗi acceptance criterion quan trọng phải có test ID hoặc kế hoạch test tương ứng.

## 14. Quy trình review từng tài liệu

Bộ tài liệu này được sửa và phê duyệt theo thứ tự `00 → 16`.

Với mỗi tài liệu:

1. System Architect sửa nội dung.
2. User/Owner review và xác nhận.
3. File được đánh dấu `Approved` hoặc `Changes Requested`.
4. Chỉ sau khi tài liệu hiện tại được chấp thuận mới chuyển sang tài liệu tiếp theo.
5. Không tạo tài liệu mới cho tới khi toàn bộ tài liệu hiện hữu đã được xử lý, trừ khi một blocker bắt buộc phải có contract độc lập.

## 15. Open issues của tài liệu này

| ID | Vấn đề | Mức độ | Owner | Trạng thái |
|---|---|---|---|---|
| DOC-001 | Chưa xác định tên cá nhân/team owner cho từng tài liệu | Medium | Project Owner | Open |
| DOC-002 | Chưa xác định công cụ quản lý approval/changelog | Low | Platform Owner | Open |
| DOC-003 | Chưa có repository path và naming convention chính thức | Medium | Backend Lead | Open |

## 16. Acceptance criteria

Tài liệu này đạt khi:

- Danh mục phản ánh đúng toàn bộ file 00–16, tài liệu bổ sung 07A và research sources R01–R02.
- Có lifecycle và approval scope rõ ràng.
- Có precedence khi tài liệu mâu thuẫn.
- Có Definition of Ready và Definition of Done.
- Có stop conditions cho coding agent.
- Có quy trình sửa từng tài liệu trước khi tạo tài liệu mới.
- Có traceability từ R01/R02 tới các tài liệu normative đã merge.
