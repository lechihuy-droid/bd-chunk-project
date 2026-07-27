# Harness Hub — Backend Documentation Adaptation v0.1

> Superseded by `../../00_INDEX.md` and `../../01_OVERALL_ASSESSMENT.md`.

> Bản này là executive baseline. Báo cáo phân tích đầy đủ đã được mở rộng tại
> `harness-hub-backend-full-analysis-v0_1.html`.

| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-ADAPT-001 |
| Status | Proposed — cần owner duyệt trước khi đổi contract/runtime |
| Scope | `harness/hub` local-first modular monolith |
| Source evaluated | `C:\Users\HUY\Downloads\harness_hub_backend_docs_v0_1` (2026-07-25) |
| Last updated | 2026-07-25 |

## 1. Quyết định

Áp dụng bộ tài liệu nguồn như **architecture baseline**, không như specification để triển khai nguyên trạng. Điều này khớp với `Harness_Hub_System_Architect_Review_v0_1.md`: bộ docs được conditionally approved cho kiến trúc nhưng chưa implementation-ready.

Giữ định hướng hiện hữu: Hub là local-first, file-backed runtime và FastAPI modular monolith. Không thêm database, queue, container sandbox, multi-tenant identity hay distributed outbox trong đợt này. Những khái niệm đó chỉ được đưa vào khi có requirement production tương ứng.

## 2. Hiện trạng đã phù hợp

| Contract nguồn | Bằng chứng trong Hub | Đánh giá |
|---|---|---|
| Runtime sở hữu lifecycle, executor chỉ thực thi | `services/workflow_exec.py`, `runtime_state.py` | Có, nhưng provider vẫn được gọi trực tiếp từ workflow executor. |
| Workflow/agent definition validation | `services/workflow.py`, `runtime_agents.py` | Có; graph hiện chỉ là linear chain. |
| Event, checkpoint, replay | `runtime_events.py`, `runtime_checkpoint.py`, SSE API | Có, file-backed. |
| Human approval / pause-resume | `runtime_interrupts.py`, workflow approval gate | Có. |
| Artifact có boundary guard | `runtime_artifacts.py` | Có; hiện là node output mutable theo tên. |
| Child-run governance | `runtime_children.py`, `governance.py` | Có các cap/path/tool constraints. |
| Test-driven runtime | `tests/test_runtime.py`, `tests/test_workflow_exec.py` | Có golden linear flow, budget, approval, provider error. |

## 3. Gap cần xử lý theo thứ tự

### P0 — contract trước code

1. **Workflow contract v1:** đóng băng schema YAML hiện tại (linear `agent`/`validate` nodes), JSON Schema, schema version, compatibility rule. Chưa thêm branch/fan-out/fan-in cho đến khi có semantics join/error edge rõ ràng.
2. **Runtime state transition v1:** bảng transition run/node/interrupt; terminal states; guard/action/event; contract cancellation. Chuyển status string hiện tại thành allow-listed transitions, không đổi persistence trong bước này.
3. **Event/command catalogue v1:** định nghĩa schema version, event id, run/thread correlation, ordering theo run, replay và deduplication scope. File JSONL hiện tại là append-only local event log, không được quảng cáo at-least-once hoặc transactional outbox.
4. **Executor port v1:** tách `workflow_exec` khỏi `get_provider(...).stream_chat` qua interface request/result/stream/error nội bộ. API provider là adapter đầu tiên; CLI adapter chỉ bắt đầu sau threat model riêng.
5. **Artifact manifest v1:** immutable manifest cho mỗi output gồm `artifact_id`, `version`, `producer_run/node`, content hash, media type, created_at, lineage. Vẫn có thể lưu file local; chưa cần object storage/database.

### P1 — sau P0 được duyệt

1. Idempotency key và expected state/version cho resume/cancel/command; test duplicate command không chạy node hai lần.
2. Retry policy tách transport retry (executor) với workflow retry (runtime), attempt record và timeout matrix.
3. OpenAPI có request/response/error/status code cho workflow, run, artifact, interrupt APIs; thêm optimistic concurrency cho save workflow.
4. Provider capability matrix và conformance tests cho ít nhất hai provider/mock adapter.
5. CLI executor threat model: workspace mount, allowlisted executable, kill process tree, egress, secret redaction, artifact/diff collection. Không tái sử dụng `gitjobs` như executor cho workflow nếu chưa có contract này.

### Không áp dụng trong local MVP hiện tại

- Tenant/workspace identity, RBAC nhiều người dùng.
- PostgreSQL DDL, queue, lease, transactional outbox và HA/DR.
- Parallel graph, dynamic orchestrator reroute, agent-managed mutation của workflow.
- Production SLO/backup/retention cho hệ phân tán.

## 4. Ranh giới kiến trúc được chốt cho Hub

```text
FastAPI routes
  → application/runtime services
  → workflow state machine + policy/interrupt/artifact services
  → executor port
  → API-provider adapter | (future) CLI adapter
```

Quy tắc bắt buộc:

- API/UI không gọi provider trực tiếp.
- Executor không tự ghi workflow state; chỉ trả result/event stream cho runtime.
- Runtime là nơi duy nhất đổi run/node state và ghi event.
- Policy/approval được kiểm tra trước executor launch; fail closed.
- Workflow definition và agent profile được snapshot/provenance vào run trước khi thực thi.
- Mọi thay đổi public API/schema/state đều có version, migration/compatibility note và test.

## 5. Build plan đề xuất

| Step | Deliverable | Allowed area | Verify |
|---|---|---|---|
| A | `workflow.schema.json` + validator parity tests | `services/workflow.py`, `tests/` | valid/invalid fixtures match schema. |
| B | state-transition table + pure transition function | `services/runtime_*`, `tests/` | every valid/invalid transition covered. |
| C | versioned event/command schemas + replay/dedup tests | `runtime_events.py`, `runtime_interrupts.py`, `tests/` | duplicate command safe; replay ordered. |
| D | `ExecutionRequest/Result` port + mock adapter | `services/`, `tests/` | golden workflow passes without provider internals. |
| E | artifact manifest/version/lineage | `runtime_artifacts.py`, `tests/` | prior artifact remains readable and hash-stable. |
| F | API contract + idempotency/concurrency | `server.py`, `tests/` | OpenAPI/API tests and stale-write rejection. |

Stop conditions: nếu một step cần database, queue, container/network permission, breaking API, branch semantics hoặc CLI execution, tạo Architecture Clarification Request thay vì tự mở rộng scope.

## 6. Acceptance gate cho đợt kế tiếp

- Golden flow: input → agent → validation/review → approval/resume → artifact → completed.
- Provider failure, duplicate resume, stale state update, timeout và cancel không tạo execution/artifact trùng.
- Event replay tái tạo đúng trạng thái cuối của run trong phạm vi local file store.
- Artifact lineage không bị ghi đè; secret scan không xuất hiện trong event/artifact log.
- Full `pytest harness/hub/tests -q` xanh trước và sau từng step.

## 7. Câu hỏi kiến trúc cần owner chốt trước Step A

1. Hub vẫn ưu tiên local single-user/file-backed trong 1–2 phase tới, hay đã cần multi-user/persistent DB?
2. Workflow v1 có được giới hạn linear chain không, hay phải có branch/fan-out ngay?
3. CLI executor có nằm trong scope runtime gần nhất không? Nếu có, cần phê duyệt threat model trước Step D/E.
