# Harness Hub Backend — Documentation Index

```yaml
document_id: HH-DOC-INDEX
version: 1.4
status: Approved as documentation baseline
owner: Harness Hub
last_updated: 2026-07-27
scope: local-first Harness Hub backend
```

## 1. Mục đích

Đây là điểm vào duy nhất của bộ thiết kế backend Harness Hub. Bộ tài liệu mô tả ba lớp riêng biệt:

- **As-is:** hành vi đang có trong `harness/hub`.
- **Target v1:** contract cần đạt trong kiến trúc local-first, file-backed, modular monolith.
- **Evolution:** điều kiện để chuyển sang database, queue, multi-user hoặc distributed deployment; không phải requirement hiện tại.

Coding agent MUST bắt đầu từ `02_REQUIREMENTS_BASELINE.md`, rồi dùng tài liệu sở hữu contract trong `design/` để triển khai và giải quyết chi tiết. Requirements baseline đang `In Review` nên chưa tự mở rộng scope hoặc thay thế owner approval. Nội dung trong `reference/` chỉ là lịch sử và nghiên cứu, không được dùng để tự mở rộng scope.

## 2. Danh mục chính thức

| ID | Tài liệu | Vai trò | Trạng thái |
|---|---|---|---|
| IDX | `00_INDEX.md` | Index, governance, precedence | Approved |
| REV | `01_OVERALL_ASSESSMENT.md` | Đánh giá tổng, gap và go/no-go | In Review |
| REQ | `02_REQUIREMENTS_BASELINE.md` | Product/system requirements, acceptance và traceability toàn Hub | In Review — owner confirmation required |
| BDS | `03_BASIC_DESIGN_STRUCTURE.md` | Manifest, ownership và QA contract cho bộ Basic Design | In Review — structure verified |
| AUD | `04_BASIC_DESIGN_IMPLEMENTATION_STATUS.md` | Audit as-is implementation theo 77 requirement ID | Audited 2026-07-28 |
| D01 | `design/D01_ARCHITECTURE_AND_SCOPE.md` | Scope, C4, module boundary, ADR | In Review |
| D02 | `design/D02_DOMAIN_AND_WORKFLOW_CONTRACTS.md` | Ubiquitous language, domain và workflow schema | In Review |
| D03 | `design/D03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md` | State machine, transaction journal, recovery | In Review — R03/R07 merged |
| D04 | `design/D04_GATEWAY_EXECUTOR_AND_PROVIDERS.md` | Gateway, executor, provider/tool capabilities | In Review — R04–R07 merged |
| D05 | `design/D05_API_AND_STORAGE_CONTRACTS.md` | HTTP/SSE API, file transaction, artifact contract | In Review — R03/R07 merged |
| D06 | `design/D06_SECURITY_AND_GOVERNANCE.md` | Policy, Windows CLI, child/tool/skill/memory/MCP | In Review — R04/R06/R07 merged |
| D07 | `design/D07_DEPLOYMENT_SLO_AND_OPERATIONS.md` | Deployment, durability envelope, controlled executor | In Review — R03/R04/R07 merged |
| D08 | `design/D08_TEST_AND_IMPLEMENTATION_PLAN.md` | Research-grounded tests, gates và phases | In Review — R03–R07 merged |
| BD01 | `basic-design/BD01_ARCHITECTURE_MODULES_AND_CONFIGURATION.md` | Architecture, module ownership và configuration boundary | In Review |
| BD02 | `basic-design/BD02_DOMAIN_WORKFLOW_AND_PROFILE.md` | Domain, workflow schema và profile snapshot | In Review |
| BD03 | `basic-design/BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md` | Runtime state, journal, event và recovery | In Review |
| BD04 | `basic-design/BD04_GATEWAY_EXECUTOR_AND_PROVIDER_ADAPTERS.md` | Gateway, Executor Port, provider và Git execution boundary | In Review |
| BD05 | `basic-design/BD05_API_AND_STREAMING.md` | HTTP/API compatibility và SSE contract | In Review |
| BD06 | `basic-design/BD06_STORAGE_ARTIFACTS_AND_BACKUP.md` | Storage, evaluation evidence, artifact và backup | In Review |
| BD07 | `basic-design/BD07_SECURITY_GOVERNANCE_AND_CONTROLLED_EXECUTION.md` | Security, governance, trust và controlled execution | In Review |
| BD08 | `basic-design/BD08_DEPLOYMENT_OPERATIONS_AND_VERIFICATION.md` | Deployment, operations, migration và verification gates | In Review |

## 3. Source-of-truth precedence

Khi có mâu thuẫn:

```text
Approved ADR trong D01
  > Security invariants trong D06
  > Approved requirements baseline
  > Domain/state/contract trong D02–D05
  > Operations/SLO trong D07
  > Test và implementation plan trong D08
  > Approved Basic Design trong basic-design/
  > Overall assessment
  > reference/research
  > reference/legacy-v0.1
```

Implementation hiện tại là bằng chứng **as-is**, không tự động ghi đè target contract. Nếu code và target khác nhau, phải mở task migration hoặc Architecture Clarification Request.

Khi `02_REQUIREMENTS_BASELINE.md` còn `Draft` hoặc `In Review`, nó là bản đồ requirement/acceptance/traceability để lập kế hoạch, chưa phải quyền tự quyết các mục `PROPOSED` hay owner decision.

## 4. Baseline và non-goals

Target v1:

- FastAPI modular monolith, chạy local trên một host.
- File-backed runtime store; atomic replace cho JSON và append-only JSONL cho event.
- Workflow v1 là một linear chain, node `agent` hoặc `validate`.
- Human approval/interrupt, checkpoint, replay và immutable artifact manifest.
- Runtime Gateway nội bộ trước provider adapter; API và CLI cùng executor contract.
- SSE cho stream backend → UI.
- Single trusted operator; workspace/path boundary vẫn bắt buộc.

Không thuộc target v1:

- PostgreSQL, broker queue, transactional outbox.
- Multi-tenant identity/RBAC production.
- Parallel graph, fan-out/fan-in, dynamic graph mutation.
- Remote CLI worker hoặc sandbox được quảng cáo production-safe.
- Multi-region, HA, active-active.

Những mục trên chỉ được đưa vào scope bằng ADR mới kèm migration, security review và test gate.

## 5. Quy tắc thay đổi

Mọi thay đổi contract public, schema, state hoặc security boundary MUST:

1. cập nhật tài liệu sở hữu contract;
2. tăng schema/API version khi breaking;
3. có compatibility hoặc migration note;
4. map sang test ID trong D08;
5. được owner review trước khi coding agent mở rộng quyền, dependency hoặc storage.

Trạng thái tài liệu:

- `Draft`: chưa dùng để code.
- `In Review`: có thể tạo prototype có kiểm soát; không tự quyết open issue.
- `Approved`: được dùng làm implementation contract.
- `Superseded`: chỉ giữ để truy vết.
- `Reference only`: không normative.

## 6. Definition of Ready cho implementation task

Task chỉ ready khi có:

- requirement và contract ID;
- as-is/target được phân biệt;
- allowed files và forbidden changes;
- input/output/error/state rõ;
- security/data classification;
- test command và acceptance test ID;
- rollback/compatibility note nếu sửa dữ liệu hoặc API.

Coding agent MUST dừng và tạo Architecture Clarification Request nếu:

- contract thiếu hoặc mâu thuẫn;
- cần database/queue/network permission/dependency mới;
- cần mở filesystem scope hay raw secret;
- cần breaking API/schema/state;
- cần hỗ trợ graph song song hoặc remote CLI;
- test yêu cầu thay đổi ngoài allowed scope.

## 7. Traceability nguồn

| Nguồn | Vị trí | Cách dùng |
|---|---|---|
| Review kiến trúc v0.1 | `reference/legacy-v0.1/Harness_Hub_System_Architect_Review_v0_1.md` | Danh sách blocker ban đầu |
| Adaptation theo code Hub | `reference/legacy-v0.1/harness-hub-backend-adaptation-v0_1.md` | Baseline local-first |
| Runtime Gateway research | `reference/research/R01_RESEARCH_Runtime_Gateway_Multi_Model.md` | Ý tưởng Gateway/routing |
| Executor Adapter research | `reference/research/R02_RESEARCH_Executor_Adapter_Layer.md` | Contract/capability/error |
| File-backed durability | `reference/research/R03_RESEARCH_File_Backed_Runtime_Correctness.md` | Transaction journal, crash matrix, recovery |
| Windows CLI security | `reference/research/R04_RESEARCH_Windows_CLI_Execution_Security.md` | Process/workspace/egress threat model |
| Provider capability | `reference/research/R05_RESEARCH_Provider_Capability_Lifecycle_Matrix.md` | Versioned provider evidence/conformance |
| Agent/tool/MCP security | `reference/research/R06_RESEARCH_Agent_Tool_MCP_Security.md` | Capability, approval, skill/memory/MCP |
| Research synthesis | `reference/research/R07_RESEARCH_Synthesis_and_ADR_Recommendations.md` | Cross-report verdict và proposed ADR |
| Implementation | `harness/hub/services`, `server.py`, `tests` | Bằng chứng as-is |

## 8. Approval gates

| Gate | Điều kiện |
|---|---|
| A — Documentation baseline | D01–D08 nhất quán, không link hỏng, open issue có owner |
| B — Contract ready | Workflow/state/event/executor/API/artifact schema được duyệt |
| C — Local v1 ready | Golden flow, duplicate/stale/cancel/recovery/security tests xanh |
| D — CLI controlled | Threat model, executable/path/env/egress controls và escape tests xanh |
| E — Production evolution | ADR storage/queue/identity, migration, SLO/DR/security review hoàn tất |
