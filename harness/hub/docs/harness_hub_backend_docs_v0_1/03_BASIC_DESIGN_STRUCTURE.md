# Harness Hub Backend — Basic Design Structure

```yaml
document_id: HH-BD-STRUCTURE-001
version: 0.1
status: Proposed structure for owner review
scope: Implementable Basic Design for local-first Harness Hub v1
source_of_truth: 00_INDEX.md, 01_OVERALL_ASSESSMENT.md, 02_REQUIREMENTS_BASELINE.md, design/D01-D08
```

## 1. Mục đích và ranh giới

Tài liệu này chỉ định **bộ khung và manifest** của Basic Design (BD). Nó không thay thế, không chép lại và không phải là nội dung BD hoàn chỉnh.

| Lớp | Trả lời câu hỏi | Mức chi tiết | Không làm |
|---|---|---|---|
| Requirements (`02_REQUIREMENTS_BASELINE.md`) | Hệ thống phải đạt gì, trạng thái nào, bằng chứng/acceptance nào? | REQ ID, priority/state, acceptance, refs, gate | Không quyết định module/class/file cụ thể |
| Basic Design (`BDxx`) | Các boundary, trách nhiệm, contract, luồng, persistence và failure behavior nào đủ để chia task implement? | Module ownership, interface/schema ở mức contract, sequence/state, mapping file/test, migration và gate | Không đặc tả từng hàm, câu lệnh, thuật toán nội bộ hay code |
| Detailed Design | Implement contract đó bằng cách nào trong code? | Class/function, data structure chi tiết, algorithm, query/file operation, error handling, test case implementation | Không tự đổi REQ, boundary, ADR hoặc security invariant |

BD chỉ bao phủ target local-v1 đã nêu trong Index: FastAPI modular monolith, một host/process, file-backed runtime, linear workflow, Gateway/Executor, SSE, approval/checkpoint/replay/artifact và các security/operation gate tương ứng. Database, queue, RBAC production, distributed/HA, parallel graph và remote/production sandbox chỉ xuất hiện như evolution boundary hoặc stop condition, không trở thành BD deliverable hiện tại.

## 2. Manifest bộ Basic Design

Tám file là đủ để bao phủ các boundary implementable mà không chia nhỏ theo endpoint hay từng service. Số BD có thể tăng chỉ khi có boundary ownership mới được owner duyệt.

| File | Mục tiêu và ranh giới nội dung | Requirement families / REQ IDs chính | Design source | Phụ thuộc / read order | Owner / review gate |
|---|---|---|---|---|---|
| `BD01_ARCHITECTURE_MODULES_AND_CONFIGURATION.md` | System context, module ownership, dependency direction, local-v1 topology, config/root boundary và ADR impact; không mô tả schema runtime chi tiết | `REQ-PLAT-01..04`, `REQ-NFR-04` | D01, D07 | 1; nền cho mọi BD | System Architecture + Backend; Gate A/B |
| `BD02_DOMAIN_WORKFLOW_AND_PROFILE.md` | Entity/aggregate ownership, workflow schema v1, linear validation, agent/profile snapshot, compatibility và domain error contract | `REQ-WF-01..07` | D02, D01 | 2; sau BD01 | Runtime; Gate B |
| `BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md` | Run/node/interrupt state machine, command/idempotency/version, transaction journal, checkpoint, derived event, restart/cancel/recovery | `REQ-RUN-01..09` | D03, D02, D05 | 3; sau BD02 | Runtime; Gate B/C |
| `BD04_GATEWAY_EXECUTOR_AND_PROVIDER_ADAPTERS.md` | ExecutionRequest/Event/Result/Error, routing/capability evidence, retry ownership, mock/API/CLI adapter lifecycle, provider conformance và Git-job execution boundary | `REQ-CHAT-01..06`, `REQ-GIT-01..04` | D04, D03, D06 | 4; sau BD03 | Execution Platform; Gate B/C, Gate D nếu CLI write |
| `BD05_API_AND_STREAMING.md` | API conventions, workflow/run commands, error/idempotency/concurrency, compatibility với `/api`, SSE cursor/replay/heartbeat và UI-facing contracts | `REQ-API-01..05` | D05, D03, D04, D06 | 5; sau BD03–04 | Backend; Gate B/C |
| `BD06_STORAGE_ARTIFACTS_AND_BACKUP.md` | File layout, canonical path resolver, immutable artifact manifest/hash/scan, evaluation evidence storage và backup/restore contract | `REQ-EVAL-01..04`, `REQ-ART-01..04`, `REQ-DATA-01..03` | D05, D02, D03, D07 | 6; sau BD03, tham chiếu BD05 | Backend + Runtime + Platform; Gate B/C |
| `BD07_SECURITY_GOVERNANCE_AND_CONTROLLED_EXECUTION.md` | Trust boundaries, classification/egress, secret/redaction, typed action/capability, approval/audit, child/skill/memory/MCP admission, CLI Gate D boundary | `REQ-GOV-01..07`, `REQ-SEC-01..08`, `REQ-OPS-01..02` | D06, D04, D01, D07 | 7; sau BD02, đọc cùng BD04/06 | Security + Execution Platform; Gate B/C; Gate D/E |
| `BD08_DEPLOYMENT_OPERATIONS_AND_VERIFICATION.md` | Supported topology/env/config, observability, quotas/degraded mode, durability/SLO objectives, retention lifecycle, release/migration gates và verification ownership | `REQ-OPS-03..05`, `REQ-DATA-04`, `REQ-NFR-01..03`, `REQ-NFR-05`, `REQ-MIG-01..05` | D07, D08, toàn bộ BD01–07 | 8; cuối read order | Platform + QA; Gate A/C/D/E |

Phân bổ trên là **owning allocation** của đủ 77 requirement ID: mỗi ID xuất hiện đúng một lần. BD khác có thể reference requirement liên quan nhưng không được nhận ownership thứ hai. `EVAL`, `GIT`, `CHAT` được map theo capability/domain sở hữu contract; không tạo BD riêng cho từng surface hiện có. Các endpoint/suite/job cụ thể chỉ là subsection hoặc implementation mapping trong BD05/06/04.

## 3. Read order và dependency rule

Read order implementable:

```text
00_INDEX → 01_OVERALL_ASSESSMENT → 02_REQUIREMENTS_BASELINE
  → BD01 → BD02 → BD03 → BD04 → BD05 → BD06 → BD07 → BD08
  → Detailed Design / implementation tasks
```

Quy tắc:

- BD01 khóa boundary và scope trước khi đọc contract chi tiết.
- BD02 khóa vocabulary/schema/immutable snapshot trước state machine.
- BD03 là authority cho state, recovery và command semantics; BD05 chỉ transport/mapping.
- BD04 là authority cho execution lifecycle/provider capability; Runtime không sở hữu provider protocol.
- BD06 là authority cho file/artifact/backup persistence; BD03 chỉ tham chiếu persistence transaction cần cho recovery.
- BD07 có quyền phủ security invariant; mọi BD khác phải link tới quyết định của BD07, không hạ policy.
- BD08 không định nghĩa lại contract; nó tổng hợp deliverable, evidence, test và release gate.
- Nếu thiếu/mâu thuẫn contract, owner decision/ADR, permission, dependency hoặc scope: dừng tại BD liên quan và tạo clarification; không tự suy diễn.

## 4. Template bắt buộc cho mỗi `BDxx`

Mỗi file phải có đúng các phần sau (có thể thêm subsection, không được bỏ phần):

1. **Document control:** `document_id`, version, status, owner, reviewers, last updated, `depends_on`, source D/REQ.
2. **Purpose and scope:** in-scope, out-of-scope, assumptions, Gate áp dụng.
3. **Context and boundary:** caller/callee, trust/data boundary, module owns / MUST NOT own.
4. **Design overview:** component/module map và một luồng chính; chỉ mức BD.
5. **Contract inventory:** input/output, schema/version, errors, state/side effects, idempotency/concurrency, security classification.
6. **Behavior flows:** happy path, validation/denial, failure, retry/cancel/recovery nếu thuộc boundary.
7. **Persistence/config/deployment impact:** file/API/config changes, compatibility, migration/rollback; ghi `N/A` có lý do nếu không áp dụng.
8. **Requirement traceability:** bảng `REQ/family → BD section → implementation owner → test/acceptance ID → gate/status`.
9. **Acceptance and verification:** observable acceptance, canonical/targeted test command, evidence artifact và reviewer.
10. **Open decisions and stop conditions:** OD/RD/ADR cần owner, unknowns, forbidden scope expansion.
11. **Change log and references:** link ngược tới baseline/D docs và link tới BD phụ thuộc.

Không đưa implementation-level class diagram, function pseudocode chi tiết, SQL/regex/file-loop cụ thể hoặc copy nguyên D01–D08 vào BD; các nội dung đó thuộc Detailed Design hoặc source contract tương ứng.

## 5. Traceability, acceptance và test mapping

Mỗi requirement chỉ có một **owning BD**; BD khác chỉ được reference. Bảng tối thiểu bắt buộc:

| REQ/family | State (`VERIFIED/TARGET/PROPOSED`) | BD section | D source / ADR | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| `WF-*`, `REQ-WF-*` | baseline state | `BD02 §...` | D02 | fixture/validator result | `WF-001/002`, contract | B/C | Runtime |
| `RUN-*`, `REQ-RUN-*` | baseline state | `BD03 §...` | D03 | transition/recovery/idempotency result | `ST-*`, `EV-*`, `DUR-*`, integration/recovery | C | Runtime |
| `API-*`, `REQ-API-*` | baseline state | `BD05 §...` | D05 | status/error/SSE compatibility | `API-*`, `E2E-001` | C | Backend |
| `SEC-*`, `REQ-SEC-*` | baseline state | `BD07 §...` | D06 | deny/redact/audit/escape result | `SEC-*`, `CAP-*`, `TOOL-*`, `WIN-*` | C/D | Security |

Ma trận đầy đủ phải phủ các family `PLAT`, `CHAT`, `EVAL`, `GIT`, `WF`, `RUN`, `GOV`, `ART`, `API`, `DATA`, `SEC`, `NFR`, `MIG`; không coi test ID là xanh chỉ vì đã được liệt kê. Test target phải map tới acceptance behavior và evidence thực tế. D08 là nguồn canonical cho test ID, level, phase và release gate; lệnh regression vẫn là `python -m pytest tests -q`, real provider chỉ opt-in.

## 6. Owner và review gates

Mỗi BD có một owner chịu trách nhiệm contract và một reviewer độc lập của boundary liên quan. Gate tối thiểu:

- **Gate A — Documentation baseline:** manifest, links, dependency, scope và open issues có owner.
- **Gate B — Contract ready:** domain/state/event/executor/API/artifact/security contract được owner duyệt; REQ mapping 100% cho scope.
- **Gate C — Local v1:** golden flow, regression, state/event/recovery, executor, API/SSE, artifact, security và backup/restore evidence xanh trong durability envelope được duyệt.
- **Gate D — Controlled CLI:** chỉ BD04/BD07/BD08 mở rộng sang workspace-write sau controlled Windows executor, threat/escape/quota/egress tests và ADR.
- **Gate E — Production evolution:** thay đổi database/queue/identity/remote/HA chỉ sau ADR, migration/rollback, load/chaos/security và SLO/DR sign-off.

Owner không được biến `TARGET` hoặc `PROPOSED` thành `VERIFIED` bằng cách sửa tài liệu; implementation/as-is deviation phải thành task hoặc clarification.

## 7. Rule tránh trùng D01–D08

- D01–D08 là **design baseline/contract, decision, research synthesis và test/implementation plan**; BD là lớp nối contract đó thành package implementable theo module boundary.
- BD phải trích dẫn D section/ADR và REQ ID, không sao chép narrative, diagram hoặc acceptance list đầy đủ của D.
- Nếu D đã là authority cho một contract (ví dụ D03 state/recovery, D04 executor, D05 API/storage, D06 security), BD chỉ phân rã ownership, sequence implementable, file impact và traceability; thay đổi contract phải sửa D owner trước.
- Không tạo BD theo từng D, endpoint, provider, test suite hoặc legacy document. Một BD chỉ được tách khi có owner, boundary, dependency và acceptance gate độc lập.
- `reference/` và current code/tests chỉ cung cấp evidence được baseline dẫn; không tự mở rộng target scope.
- Không dùng BD để chốt OD/RD/ADR đang mở; phải ghi open decision và stop condition.

## 8. Deliverables của bộ BD

Sau khi hoàn tất cấu trúc này, bộ tài liệu cần tạo đúng manifest trên và tối thiểu cung cấp:

- một boundary/module map và dependency graph;
- contract inventory cho domain, state, event, execution, API/SSE, storage/artifact và security;
- implementation task seams: allowed files, forbidden changes, owner, input/output/error/state;
- migration/compatibility/rollback note cho mọi persisted/API/schema/security change;
- REQ-to-BD-to-test-to-gate matrix và evidence index;
- open-decision register không tự quyết định;
- release/QA evidence package theo D08 và Gate C/D/E.

## 9. QA checklist trước khi approve từng BD và toàn bộ bộ BD

- [ ] YAML document control hợp lệ; status/owner/reviewer/dependency rõ.
- [ ] Scope khớp Index; không lẫn as-is, TARGET và PROPOSED.
- [ ] Module ownership và MUST NOT boundary không mâu thuẫn D01.
- [ ] Schema/state/error/idempotency/concurrency có version và acceptance observable.
- [ ] Mọi input path/secret/provider/tool được phân loại và có policy reference.
- [ ] Mỗi REQ family và REQ ID trong scope có đúng một owning BD.
- [ ] Mỗi acceptance map tới test ID D08, test level, command và gate; không claim xanh khi chưa có evidence.
- [ ] Migration, compatibility, rollback và backup impact được ghi hoặc nêu rõ `N/A`.
- [ ] Không có direct Runtime→provider, policy bypass, silent fallback, multi-worker/file-store claim hoặc production sandbox claim ngoài gate.
- [ ] Không duplicate nội dung authority của D01–D08; link/reference đầy đủ.
- [ ] Open OD/RD/ADR có owner và stop condition; không tự mở rộng database/queue/network/secret/filesystem scope.
- [ ] Links, filenames, manifest, dependency/read order và canonical regression command kiểm tra được.
- [ ] Review gate đúng owner; unrelated code/repository changes không được đưa vào BD scope.
