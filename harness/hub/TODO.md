# TODO — Harness Hub

Backlog cho project build Hub (cổng thông tin cho Opus Agent Harness).
SDD: `RD-harness-hub.md` → `SD-harness-hub.md` → `BD-harness-hub.md`.

---

## Trạng thái
- [x] RD (cost dropped → tokens/calls; thêm FR-014/015/016 Hermes-style)
- [x] SD (kiến trúc FastAPI + parsers + contracts + endpoints)
- [x] BD (Step 1–14, test plan, brief giao Codex)
- [x] Duyệt SD/BD → giao Codex (full-auto flow 2026-06-28)

## Build (theo BD) — DONE (Codex code+test, Claude review+fix)
- [x] Phase 1 — read-only core: Dashboard · Runs · Suites (Step 1–5) — 12 tests pass
- [x] Phase 2 — control + usage: Trigger+SSE · AI Usage (Step 6–8) — 18 tests pass
- [x] Phase 3 — P1: Compare (9) · Inspect evals (10) · auto-refresh (11)
- [x] Phase 3 Hermes-style: Task Board (12) · Session Replay 3-pane (13) · Budget bar (14) — 27 tests pass
- [x] Claude fix: usage disk-cache + startup warm (rollup timeout → 0.23s steady-state)

**Chạy app:** `.\harness\hub\run-hub.ps1` → http://127.0.0.1:8799

### Known limitation
- `/api/usage/rollup` cold ~6–11s khi có agent session đang ghi log (fingerprint max-mtime đổi liên tục → rebuild). Steady-state (không ghi mới) ~0.23s nhờ disk cache. Tối ưu sâu (incremental per-file parse) = future nếu cần.

---

## Track B — Opus Runtime: kế hoạch gốc lỗi thời, một phần đã build ngay trong Hub

> **Cập nhật 2026-07-25:** kế hoạch gốc bên dưới (2026-06-28) nói Track B phải tách repo/RD
> riêng, KHÔNG nhét vào Hub. Thực tế đã đi ngược lại: phần lõi của lớp G (HITL gate,
> checkpoint, child-run) được build thẳng vào Hub qua BD Phase D + `plans/super-agent-runtime/`
> (`services/workflow_exec.py`, `runtime_state.py`, `runtime_interrupts.py`,
> `runtime_checkpoint.py`, `runtime_children.py`) — không phải orchestrator LangGraph tách
> biệt như dự tính, mà là substrate file-backed tự viết (xem `docs/super-agent-runtime.md`
> v0.2, "does not depend on langgraph").
>
> Đã có thật: HITL approval gate (`gate: approval` + `runtime_interrupts`), checkpoint mỗi
> node, validate node có thể chặn/tạm dừng run (`runtime_validate` + Phase D2), live stream
> qua SSE (không phải replay).
>
> Chưa có (vẫn đúng như lo ngại gốc): hot-swap quyền công cụ giữa lúc đang chạy, rollback về
> checkpoint an toàn trước đó (checkpoint mới ghi, chưa có API restore), và runtime này vẫn
> chỉ điều phối agent CLI của chính Hub — không giám sát được tool-call của Claude Code/Codex
> chạy ngoài phiên hub (đúng giới hạn lớp O nêu ở kế hoạch gốc).

<details>
<summary>Kế hoạch gốc (2026-06-28) — giữ lại để đối chiếu, không còn là hướng đi hiện tại</summary>

> Lý do tách: Hub chỉ là lớp **O (Observability)** — quan sát Claude Code/Codex qua log,
> không cầm cương được từng tool-call vì chúng chạy ngoài runtime của hub.
> Lớp **G (Governance)** thật cần Hub LÀ orchestrator chạy agent của riêng mình.

- [ ] **Track B — Opus Runtime (deferred):** xây/dùng một orchestrator (ứng viên: **LangGraph** — state graph + `interrupt()` để pause chờ lệnh) chạy **agent riêng** qua đó. Khi đó mới có lớp G đúng nghĩa:
  - HITL gate: pause trước tool-call rủi ro cao → Approve / Reject / Edit tham số
  - Hot-swap quyền công cụ (read-only / write / network) lúc đang chạy
  - Rollback về checkpoint trạng thái an toàn gần nhất
  - Live stream chain-of-thought + tool args (không phải replay)
  - **Điều kiện:** mở RD riêng `Opus Runtime`; KHÔNG giám sát Claude Code/Codex hiện có mà chạy agent mới trong runtime này.
  - **Ràng buộc giữ triết lý workspace:** ưu tiên local-only, no API key bắt buộc, không SaaS observability (Helicone/Langfuse/Opik) — cân nhắc kỹ trước khi kéo OTel/LangGraph vào.
  - Khi làm: Hub (Track A) trở thành frontend đọc state của Runtime → tái dùng được phần lớn UI.

</details>

---

*Cập nhật: 2026-07-25*
