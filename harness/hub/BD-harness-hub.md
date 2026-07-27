# BD — Harness Hub (Build Plan, giao Codex)
**Date:** 2026-06-28 · **Status:** 🟡 In Review · **Author:** Claude (Opus 4.8)
**Upstream:** `RD-harness-hub.md`, `SD-harness-hub.md`
**Thực thi:** Codex (`codex exec`) — implement + test. Claude review.

> **FRESH START, don't ask.** Codex: làm theo các step dưới đây, không hỏi lại Session-Start.
> Mọi đường dẫn tương đối tính từ project root `C:\Users\HUY\workspace\ai-project-opus`.
> Python để chạy/test: `.ih\Scripts\python.exe` (đã có FastAPI/uvicorn/inspect-ai).

---

## Nguyên tắc chung
- Surgical, tối giản (theo CLAUDE.md). Không thêm gói nếu `.ih` đã có.
- Service trả dict/list thuần; `server.py` chỉ lo HTTP. UI không parse file thô.
- Mỗi step có **verify** — không qua verify thì không sang step sau.
- Không tự ý gọi LLM. Không bind ra ngoài 127.0.0.1.

---

## Phase 1 — Read-only core (P0)

**Step 1 — Scaffold + config**
- Tạo `hub/config.py`: `ROOT`, `HARNESS_DIR`, `RUNS_DIR`, `SUITES_DIR`, `PORT=8799`,
  `USAGE_SOURCES = {claude: ~/.claude/projects, codex: [~/.codex/sessions, ~/.codex/archived_sessions], inspect: harness/inspect/logs}` (dùng `Path.home()`).
- **Module = chạy script trực tiếp, KHÔNG import dạng `harness.hub.*`** (harness/ không phải package; tránh phụ thuộc namespace-package). `server.py` thêm `sys.path.insert(0, str(Path(__file__).parent))` rồi `import config`, `from services import runs` (import phẳng trong hub/).
- Tạo `hub/services/__init__.py`, `hub/parsers/__init__.py`, `hub/tests/__init__.py` (KHÔNG cần `harness/__init__.py`).
- → verify: `.ih\Scripts\python.exe harness\hub\config.py` (thêm khối `if __name__=="__main__": print(ROOT)`) in ra ROOT đúng, không lỗi.

**Step 2 — boundary.py**
- `resolve_in_root(p, base=ROOT) -> Path`: resolve, đảm bảo nằm dưới base, else raise `PermissionError`.
- → verify: `test_boundary.py` — path trong root pass; `..\..\windows` raise.

**Step 3 — runs.py**
- `list_runs()`: glob `RUNS_DIR/*/summary.json`, đọc, map → RunSummary (SD §3.1), sort time desc. Cache TTL 5s.
- `get_run(run_id)`: đọc summary + report.md (raw) + liệt kê artifacts + gắn `logs[]` cho mỗi check từ evidence. → RunDetail (SD §3.2).
- `read_artifact(run_id, rel)`: boundary-check trong run dir, trả text.
- → verify: `test_runs.py` chạy trên `fixtures/` (copy 1 summary.json thật) → đúng count, status, 404 khi run_id sai.

**Step 4 — suites.py**
- `list_suites()` / `get_suite(id)`: parse `SUITES_DIR/*.json` (bỏ thư mục `probes/` hoặc gộm tuỳ, nhưng list được file probes nếu là .json). → Suite (SD §3.3).
- → verify: `test_suites.py` — workspace-smoke có ≥ 11 checks, mỗi check có id/type.

**Step 5 — server.py (read-only endpoints) + SPA shell**
- FastAPI app, mount static `hub/web/`, endpoints: health, runs, runs/{id}, artifact, suites, suites/{id} (SD §5).
- `__main__`: `uvicorn.run(app, host="127.0.0.1", port=PORT)`.
- `hub/web/index.html` + `app.js`: router cho `#/`, `#/runs`, `#/runs/:id`, `#/suites`; render bảng checks + report.md (mini markdown JS) + xem artifact.
- Copy `html-kit/styles.css` vào `hub/web/` (hoặc symlink path) để self-contained.
- `run-hub.ps1`: gọi `.ih\Scripts\python.exe harness\hub\server.py`.
- → verify: chạy `run-hub.ps1`, `curl http://127.0.0.1:8799/api/runs` trả JSON; mở trình duyệt thấy list run + click vào xem được report.

**Phase 1 DONE khi:** dashboard + runs list/detail + suites view hoạt động trên dữ liệu thật trong `harness/runs/`.

---

## Phase 2 — Control plane + AI Usage (P0)

**Step 6 — trigger.py + SSE**
- `start_run(suite, check?)`: validate `suite ∈ list_suites()`; spawn `{py311} harness/run_harness.py --suite {suite} [--check {check}] --json`, cwd=ROOT, stream stdout/stderr.
- Endpoints `POST /api/runs/trigger` → stream_id; `GET /api/runs/stream/{id}` SSE (event `line`/`exit{code,run_id}`).
- UI: trang Suites có nút "Run" → panel stream → khi exit refetch runs.
- → verify: bấm Run `workspace-smoke` từ UI → thấy stdout chạy dòng-dòng → run mới xuất hiện ở /runs. Test: `test_api.py` mock subprocess, assert suite lạ bị 400.

**Step 7 — parsers usage (3 nguồn)** — theo SD §4
- `parsers/claude_sessions.py`, `codex_sessions.py`, `inspect_eval.py`. Mỗi cái: `collect() -> (events[], warnings[])`.
- Dedupe Claude theo message.id; Codex lấy last/max per session; Inspect dùng `read_eval_log`.
- → verify: `test_usage_parsers.py` trên fixtures jsonl thật (copy nhỏ): ra UsageEvent đúng field, file hỏng → warning không crash.

**Step 8 — usage.py service + endpoints**
- `collect_usage(filters)`: gọi 3 parser, gộp, sort time desc, cache TTL 30s.
- `rollup(events)` → UsageRollup (by_model/by_day/by_source/totals).
- Endpoints `/api/usage`, `/api/usage/rollup` (filter `source,model,since`).
- UI trang `#/usage`: bảng event + filter + bar chart (charts.js) tokens theo model & ngày. Card tổng trên dashboard.
- → verify: `/api/usage/rollup` trả tổng tokens > 0 từ data thật; UI vẽ được chart; filter model lọc đúng.

**Phase 2 DONE khi:** trigger run từ UI + trang AI Usage hiển thị tokens/calls thật theo model/ngày (KHÔNG có cột tiền).

---

## Phase 3 — P1 (làm sau khi P0 xanh)
- **Step 9** compare runs `/api/runs/compare` + UI diff pass↔fail.
- **Step 10** inspect evals page + MEP view.
- **Step 11** auto-refresh (poll 10s) + usage rollup charts nâng cao.

### Hermes-style (P1) — dựng từ log/dữ liệu có sẵn, KHÔNG live orchestration
- **Step 12 — Task Board (FR-014):** `services/board.py` parse `opus-animus/ai/status.md`; nếu Claude là owner thì đọc thêm `handoff-claude.md` → TaskBoard (SD §3.6). Endpoint `/api/board`. UI card trên dashboard + trang `#/board`.
  → verify: board hiện objective + sub-systems + next_step thật; file thiếu heading → field null, không crash.
- **Step 13 — Session Replay 3-pane (FR-015):** `services/replay.py` parse 1 session jsonl (Claude + Codex) → outline/agent/monitor (SD §3.7). Endpoints `/api/sessions`, `/api/sessions/{id}/replay`. UI 3 cột cuộn đồng bộ theo ts.
  → verify: chọn 1 session Claude thật → pane Agent thấy assistant text + tool args; pane Monitor thấy tool_result; replay tĩnh, không gọi LLM. Boundary: chỉ đọc trong `USAGE_SOURCES`, không nhận path tuỳ ý từ client.
- **Step 14 — Step-budget bar (FR-016):** `BudgetStatus` (SD §3.8) gắn vào trigger stream; `step_cap` trong `config.py`. UI progress bar **checks done/total**, đổi màu khi >80% `step_cap`. `tokens_used/token_cap` = null → UI ẩn phần token (chưa có suite gọi LLM).
  → verify: trigger `workspace-smoke` → bar đếm checks done/total; đặt `step_cap` nhỏ → `warn=true` hiện cảnh báo; phần token không render.

> **Ranh giới rõ:** KHÔNG implement HITL gate chặn tool-call / hot-swap quyền / rollback checkpoint cho Claude/Codex — ngoài tầm harness (xem RD Exclusions). Nếu cần → mở "Track B / Opus Runtime" RD riêng.

---

## Test Plan (tổng)

| Loại | Phạm vi | Lệnh |
|---|---|---|
| Unit | boundary, runs, suites, usage parsers | `.ih\Scripts\python.exe -m pytest harness/hub/tests -q` |
| API | endpoints qua `fastapi.testclient.TestClient` | trong `test_api.py` |
| Smoke thủ công | chạy `run-hub.ps1`, click 5 trang | checklist dưới |
| Boundary | request artifact ngoài run dir → 403 | `test_api.py` |
| No-crash | xoá/hỏng 1 file fixture → vẫn trả kết quả + warning | parser tests |

**Manual smoke checklist (Claude review chạy):**
1. `run-hub.ps1` → mở `http://127.0.0.1:8799` không lỗi console.
2. Dashboard thấy ≥ 1 suite card + usage card.
3. /runs → click run thật → bảng checks + report render đúng.
4. /suites → Run `workspace-smoke` → stream chạy → run mới hiện.
5. /usage → có event Claude + Codex, filter model hoạt động, chart hiển thị.
6. `curl '/api/runs/<id>/artifact?rel=../../../etc'` → 403.

**Definition of Done:** pytest xanh + 6 mục smoke pass + không gói mới ngoài `.ih` (hoặc đã ghi `requirements-hub.txt`).

---

## Brief giao Codex (copy nguyên văn khi exec)

> FRESH START, don't ask. Đọc `harness/hub/SD-harness-hub.md` + `BD-harness-hub.md`.
> Implement Phase 1 → Phase 2 theo đúng module layout (SD §2) và data contract (SD §3).
> Python chạy/test: `.ih\Scripts\python.exe`, cwd = project root. Bind 127.0.0.1:8799.
> Sau mỗi Phase: chạy `pytest harness/hub/tests -q` và báo kết quả. KHÔNG thêm gói mới nếu `.ih` đã có; nếu buộc phải thì ghi `requirements-hub.txt` và nêu lý do. Không sửa file ngoài `harness/hub/`. Không gọi LLM.

---

*Harness Hub — BD v1 | 2026-06-28*
