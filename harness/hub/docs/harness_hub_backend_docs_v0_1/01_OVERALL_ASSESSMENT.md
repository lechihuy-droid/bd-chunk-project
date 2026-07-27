# Harness Hub Backend — Overall Assessment

```yaml
document_id: HH-REVIEW-001
version: 1.2
status: In Review
review_date: 2026-07-27
evaluated_target: C:\Users\HUY\workspace\ai-project-opus\harness\hub
verdict: GO for contract-first local-v1 hardening; NO-GO for Gate C/D claims until research gates pass
```

## 1. Kết luận

Kiến trúc cốt lõi đúng hướng và implementation đã có nhiều substrate quan trọng: FastAPI, workflow tuyến tính, agent profiles, provider adapters, interrupt/resume, checkpoint, runtime event JSONL, artifacts, child-run governance, SSE và test suite. Không cần thay framework hay xây lại Hub.

Deep research R03–R07 xác nhận điểm lệch lớn nhất vẫn là **Runtime đang gọi provider trực tiếp trong `workflow_exec.py`**. Ngoài ra, file replace chưa phải durability protocol; current Windows CLI wrapper không tạo isolation boundary; provider capability chưa phản ánh exact tested behavior; child/tool/skill/memory scopes chưa complete-mediate action.

`02_REQUIREMENTS_BASELINE.md` hiện đã gom toàn bộ bề mặt Hub thành 77 requirement ID ổn định, tách `VERIFIED`/`TARGET`/`PROPOSED`, kèm acceptance, design/test reference, release gate và owner decision. Bộ tài liệu vì vậy đã đủ để lập backlog requirement-driven; chưa đủ để tự động coi mọi requirement là implementation contract cho đến khi owner duyệt các contract và quyết định mở.

## 2. Đánh giá theo lĩnh vực

| Lĩnh vực | As-is | Target v1 | Readiness |
|---|---|---|---:|
| Scope và architecture | Modular monolith rõ; tài liệu cũ trộn production scope | Local-first boundary + evolution gate | 80% |
| Workflow contract | YAML, validation, linear chain | Versioned schema + compatibility fixtures | 70% |
| Runtime state | Run/thread/checkpoint tồn tại | Transition + projection/transaction-journal authority | 40% |
| Event/replay | JSONL + SSE; invalid rows có thể bị bỏ qua | Derived event timeline + torn-tail repair | 45% |
| Executor abstraction | Provider registry/chat façade tồn tại | Unified port và Gateway ở trước provider | 35% |
| API | Endpoint hoạt động, SSE có | Version/error/idempotency/concurrency contract | 55% |
| Artifact | File output và boundary guard | Immutable manifest/version/lineage/hash | 50% |
| Security | Path guard/risk/approval; scope chủ yếu metadata | Typed action/capability + controlled Windows executor | 35% |
| Operations | Local run script, logs, tests | Qualified durability envelope + controlled executor ops | 45% |
| Testing | Coverage rộng, provider mock | R03–R06 crash/provider/security gates | 55% |

**Tổng hợp sau research:** documentation/research baseline khoảng 85%; implementation readiness khoảng 45–50% cho Gate C và dưới 25% cho Gate D. Việc giảm điểm là do evidence mới loại bỏ các guarantee chưa được chứng minh.

## 3. Điểm mạnh đã kiểm chứng từ repository

- `services/workflow.py` validate required fields, node type, agent reference, stop caps và bắt graph là một linear chain.
- `services/runtime_state.py` giới hạn ID/path, ghi JSON bằng temp file rồi replace.
- `runtime_events`, `runtime_checkpoint`, `runtime_interrupts` cung cấp event, checkpoint và HITL substrate.
- `services/providers/*` đã tách provider-specific transport.
- `workflow_exec.py` có budget, validation node, approval gate, child-run isolation và SSE.
- Tests đã bao phủ workflow, provider failure, approval/resume, runtime, artifacts, child-run, governance và API.

## 4. Blocker cần xử lý

### P0 — trước khi coi contract là code-ready

1. Đóng băng `workflow_version: 1` và schema tương thích với validator.
2. Thêm transition function duy nhất cho run/node/interrupt; từ chối transition không hợp lệ.
3. Tạo projection + immutable transaction-journal authority; event chỉ là derived timeline.
4. Thêm state version, per-run lock, idempotency ledger và crash/torn-tail recovery.
5. Tạo `ExecutionRequest/Event/Result/Error` và Executor Port.
6. Chuyển provider call khỏi Runtime sang Gateway/Executor.
7. Provider status phải báo configured/resolved executable, candidate/exact tested version.
8. Đóng empty child capability bypass: missing/empty = none.
9. Thêm artifact manifest immutable và content hash.
10. Chuẩn hóa API error, idempotency cho command và stale-write protection.

### P1 — trước CLI executor có quyền ghi workspace

1. Controlled Windows executor milestone: Job supervisor, restricted identity, disposable workspace.
2. WFP admin pre-provisioning/authenticated broker hoặc isolated worker; Hub không elevated.
3. Hard quota storage boundary; watcher không được coi là enforcement.
4. Minimal env, exact known-secret redaction và incident cleanup.
5. Typed tool request + deterministic policy + action-bound approval.
6. Skill hash pinning, memory provenance và MCP admission/auth tests.

### P2 — chỉ khi chuyển production/multi-user

- Identity/RBAC, database/queue/outbox, lease phân tán.
- Object storage, retention/privacy, HA/DR.
- Parallel workflow semantics.
- Remote isolated CLI workers.

## 5. Quyết định đã chốt

- Target v1 giữ FastAPI modular monolith và file store.
- Workflow v1 chỉ linear; branch bị reject thay vì đoán semantics.
- Runtime là nơi duy nhất đổi run/node state.
- Gateway quyết định route nhưng không sở hữu workflow retry/state.
- Adapter chỉ retry lỗi transport tạm thời trên cùng provider.
- Security denial, auth, validation, capability và contract error không fallback.
- SSE là transport stream v1; WebSocket ngoài scope.
- Research docs là tham khảo, không override security hoặc local scope.
- Proposed ADR trong R07 chưa approved cho đến khi owner chốt RD-01–RD-07.

## 6. Open decisions có owner

| ID | Quyết định | Owner | Deadline/gate |
|---|---|---|---|
| OD-01 | Có cần API prefix `/api/v1` ngay hay giữ `/api` + media schema version | Backend owner | Trước P0 API |
| OD-02 | Optimistic version là integer trong `run.json` hay command ledger riêng | Runtime owner | Trước transition refactor |
| OD-03 | CLI v1 dùng provider CLI hiện hữu hay executor workspace-writing riêng | Security + Runtime | Trước Gate D |
| OD-04 | Artifact manifest per-run hay central content-addressed index | Artifact owner | Trước artifact migration |
| OD-05 | Thời hạn giữ runtime/events/artifacts local | Product + Security | Trước release local v1 |
| RD-01 | Approve projection+journal làm recovery authority | Runtime | Trước Phase 2 |
| RD-02 | Accepted Windows/NTFS durability và RPO envelope | Runtime + Product | Trước Gate C |
| RD-03 | Provider set chính thức cho Gate C | Product + Runtime | Trước provider migration |
| RD-04 | Có đầu tư controlled Windows executor không | Product + Security | Trước Gate D |
| RD-05 | WFP broker/pre-provision hay Gate E isolated worker | Security + Platform | Trước egress claim |
| RD-06 | MCP có trong roadmap gần không | Product + Security | Trước typed MCP design |

Coding agent không tự chốt các quyết định này.

## 7. Go/No-Go

- **GO:** close empty-scope bypass, transaction-journal prototype, mock Executor Port, exact provider capability fixtures và typed read-only tool kernel.
- **CONDITIONAL GO:** NVIDIA/Claude read-only trong low-assurance non-sensitive profile với capability truth rõ.
- **NO-GO:** Codex adapter theo config hiện tại; Gemini adapter; privileged tool/MCP/child write-network; mọi CLI workspace-write trước Gate D.
- **NO-GO:** multi-tenant, distributed reliability, production sandbox, power-loss zero-loss hoặc exactly-once khi chưa có evidence/ADR tương ứng.
