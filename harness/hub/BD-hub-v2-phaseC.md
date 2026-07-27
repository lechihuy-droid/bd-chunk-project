# BD — Hub v2 Phase C (Build Plan)
**Date:** 2026-07-16 · **Status:** 🟡 Ready sau khi Phase B xong · **Author:** Claude (Fable 5)
**Upstream:** `SD-hub-v2-command-center.md` §11 Phase C + ARCHITECTURE.md §9 (nguyên tắc Super Agent) + RD FR-121→124.
**Mô hình orchestra:** như BD Phase B §0 (Claude điều phối · Codex code `[CODEX]` · Sonnet test/review). Codex chạy từ terminal thật của user — KHÔNG spawn từ Bash tool.

---

## 0. Mục tiêu Phase C

Track B thật: Hub **chạy agent của riêng mình** qua CLI provider layer — workflow khai báo YAML, agent profile có quản trị, HITL gate, canvas cuối cùng. Nguyên tắc khoá (ARCHITECTURE.md §9):
- Config-first: YAML là chân lý, canvas chỉ là editor.
- Sub-agent không tự spawn — đi qua child task packet + governance check.
- Node LLM = gọi CLI provider (không API key), budget cap bắt buộc.
- Blackboard append-only, replay được.

| Step | Nội dung | Executor | Size | Phụ thuộc |
|---|---|---|---|---|
| C1 | Agent profile schema + CRUD | [CODEX] | M | — |
| C2a | Workflow schema + validate + IR | [CODEX] | M | — (song song C1) |
| C2b | Executor: LLM node qua provider layer + budget | [CODEX] | L | C1, C2a |
| C2c | Child-run (sub-agent packet + governance) | [CODEX] | M | C2b |
| C3 | Workflow run view UI (stream + HITL gate) | [CODEX] | M | C2b |
| C4 | Canvas SVG editor | [CODEX] | L | C2, C3 ổn định |
| C✔ | Verify + commit từng step | Claude main + Sonnet | — | từng step |

---

## Step C1 — Agent profiles `[CODEX]` (M)

**Files:** `services/runtime_agents.py` (mở rộng — hiện chỉ list tĩnh), thư mục mới `harness/hub/agents/*.agent.yaml`.
**Schema `<name>.agent.yaml`:**
```yaml
id: reviewer
provider: claude          # claude|codex|nvidia|gemini
model: null               # chỉ nvidia dùng
system_prompt: |
  You are a strict reviewer...
skills: [opus-design-reviewer]     # id từ skill_library
permission: read_only              # read_only|workspace_write (chỉ ảnh hưởng cờ CLI)
budget: {seconds: 900, max_calls: 5}
risk_tier: read_only
```
**Việc:** parse+validate (thiếu field → lỗi rõ; provider phải ∈ registry; skill id phải tồn tại trong skill_library); API: `GET /api/agents` (đọc yaml thật), `POST /api/agents` (create/update, validate trước ghi), `DELETE /api/agents/{id}`. PyYAML có trong `.ih` — verify, nếu thiếu ghi `requirements-hub.txt`.
**Test:** fixtures yaml hợp lệ/hỏng; validate reject provider lạ, skill không tồn tại, budget âm.
**DoD:** tạo `reviewer.agent.yaml` mẫu qua API, GET trả đúng.

## Step C2a — Workflow schema + IR `[CODEX]` (M, song song C1)

**Files:** `services/workflow.py` (MỚI), `harness/hub/workflows/*.workflow.yaml`.
**Schema:**
```yaml
id: review-ui
nodes:
  - id: plan
    agent: reviewer          # ref agent profile
    prompt: "Plan review for: {{objective}}"
    gate: none               # none|approval  (HITL trước khi chạy node)
  - id: act
    agent: reviewer
    prompt: "Execute: {{plan_output}}"
    gate: approval
edges: [[plan, act]]         # tuần tự (Q5: chưa rẽ nhánh)
stop: {max_nodes: 10, max_seconds: 1800}
```
**Việc:** parse → validate (agent tồn tại, edges tạo chuỗi tuần tự không vòng, stop caps bắt buộc) → build IR (list node đã resolve agent profile + template slot). API: `GET /api/workflows`, `POST /api/workflows/validate`.
**Test:** yaml hợp lệ/vòng lặp/agent thiếu/thiếu stop caps.
**DoD:** validate endpoint trả lỗi cụ thể từng trường hợp.

## Step C2b — Executor LLM node `[CODEX]` (L — bước rủi ro nhất)

**Files:** `services/runtime_pipeline.py` (mở rộng — thay node deterministic bằng node chạy IR), `services/workflow_exec.py` (MỚI nếu tách gọn hơn).
**Việc:**
- `POST /api/workflows/{id}/runs {objective}` → tạo run (tái dùng `runtime_state`), execute node tuần tự: render prompt template (`{{objective}}`, `{{<node>_output}}`) → gọi `get_provider(agent.provider).stream_chat()` (system_prompt + prompt; skill nội dung inject progressive: chỉ metadata, full SKILL.md khi agent profile khai skill) → output ghi vào state + `artifacts/` (blackboard, append-only qua `runtime_events`).
- `gate: approval` → tạo interrupt qua `runtime_interrupts` (đã có), dừng stream; resume qua endpoint sẵn có.
- **Budget enforcement:** đếm calls + elapsed vs `agent.budget` và `workflow.stop`; vượt → run `failed(budget_exceeded)` + kill process qua `procs`.
- SSE: tái dùng event format runtime hiện có (`assistant_delta`, `node_update`, `state_snapshot`, `done|error`).
- Checkpoint mỗi node (`runtime_checkpoint` đã có) → resume sau restart.
**Test (fake provider):** monkeypatch provider registry → fake stream; test: chuỗi 2 node chạy đủ, gate dừng + resume tiếp, budget calls vượt → failed, checkpoint ghi mỗi node. KHÔNG gọi CLI thật.
**DoD:** workflow 2-node chạy headless bằng fake trong test; Claude main chạy 1 run thật nhỏ (nvidia, 1 node, prompt rẻ) verify end-to-end.

## Step C2c — Child-run / sub-agent `[CODEX]` (M)

**Việc:** node có `spawn:` → child task packet đúng ARCHITECTURE.md §9 (`agent_profile`, `allowed_paths`, `allowed_tools`, `budget`, `handoff_contract`); `runtime_children` (đã có khung) + **governance check trước launch**: risk_tier của agent profile vs `governance.effective_blocked_tiers()`, blocked → deny + record_denial. Child output ghi blackboard `claims.jsonl`, parent đọc tổng hợp.
**Test:** blocked tier bị chặn; child chạy fake provider ghi claims; parent state nhận kết quả.
**DoD:** workflow cha spawn 1 child reviewer (fake) end-to-end trong test.

## Step C3 — Run view UI `[CODEX]` (M, sau C2b)

**Việc:** trang `#/workflows`: list workflow + nút Run (nhập objective); trang run: timeline node (badge trạng thái), stream output (tái dùng SSE consumer pattern gitjobs), **HITL gate panel**: Approve / Reject (+ ô edit payload) gọi resume endpoint; artifact list link đọc blackboard; budget bar (tái dùng component budget). Nav: CONTROL → "Workflows".
**DoD:** browser-verify: chạy workflow mẫu, gate hiện panel, approve → chạy tiếp, artifact xem được.

## Step C4 — Canvas editor `[CODEX]` (L — CHỈ sau C2/C3 ổn định)

**Việc (FR-124, nguyên tắc: canvas = editor, YAML = chân lý):**
- `web/canvas.js` (MỚI, vanilla SVG, không lib): node = agent box (kéo thả vị trí — vị trí chỉ là metadata hiển thị, lưu `ui:` section trong yaml), edge = mũi tên nối tuần tự, click node → side panel sửa prompt/agent/gate.
- Save → generate YAML → `POST /api/workflows/validate` → hiện diff YAML cũ/mới → user confirm mới ghi.
- Run từ canvas → gọi API run như C3.
**Test:** round-trip yaml → canvas model → yaml không mất field.
**DoD:** browser-verify: mở workflow mẫu trên canvas, sửa 1 prompt, save ra diff đúng, chạy được.

---

## 1. Rủi ro & guard

| Rủi ro | Guard |
|---|---|
| Executor gọi CLI thật đốt quota khi test | Fake provider trong test; run thật chỉ Claude main verify 1 lần/step, ưu tiên nvidia (free) |
| Workflow treo (CLI hang) | procs timeout + `stop.max_seconds` + kill_all shutdown (đã có) |
| Scope creep C4 (canvas phình) | C4 chỉ bắt đầu khi C2/C3 committed + user OK; timebox: chỉ node/edge/save/diff, không minimap/zoom/undo |
| Codex nested-sandbox hang | Luôn chạy từ terminal user (BD Phase B §0) |
| PyYAML thiếu | C1 verify import trước, ghi requirements-hub.txt |

**Definition of Done Phase C:** agent profile CRUD + workflow YAML validate/run headless với HITL + budget + child-run có governance + run view UI + canvas editor; suite xanh toàn bộ; 1 workflow demo thật (nvidia) chạy end-to-end từ canvas.

*Hub v2 — BD Phase C | 2026-07-16*
