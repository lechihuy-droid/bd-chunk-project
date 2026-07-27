# Harness Hub — Kiến trúc hệ thống

> Web UI (localhost) giám sát + điều khiển các AI agent: theo dõi usage/hành vi, chạy eval suites, quản lý git-jobs của Codex, và một cửa sổ Chat gắn NVIDIA.

- **Chạy:** `.ih\Scripts\python.exe harness\hub\server.py` → `http://127.0.0.1:8799`
- **Stack:** FastAPI + Uvicorn (backend) · SPA vanilla JS + CSS thuần (frontend). **Không** framework, **không** CDN, **không** build step.
- **Kiểm thử:** `.ih\Scripts\python.exe -m pytest harness/hub/tests -q` (~76+ test, provider luôn được mock).

---

## 1. Sơ đồ tầng

```
┌─────────────────────────────────────────────────────────────┐
│  Browser SPA  (web/index.html + app.js + charts.js + CSS)   │
│  HUD shell: topbar chips · sidebar nav · content zone        │
│  Hash-routing 12 trang · fetch JSON · SSE cho stream/chat    │
└───────────────┬─────────────────────────────────────────────┘
                │  HTTP / Server-Sent Events (text/event-stream)
┌───────────────▼─────────────────────────────────────────────┐
│  server.py  (FastAPI)                                        │
│  - REST /api/* + StaticFiles /static                         │
│  - startup: warm cache (usage + behavior) trên daemon thread │
└───────────────┬─────────────────────────────────────────────┘
                │  gọi trực tiếp (in-process)
┌───────────────▼─────────────────────────────────────────────┐
│  config.py            services/*            parsers/*        │
│  (paths, model        (business logic)      (đọc & chuẩn hoá │
│   catalog, tiers)                            log agent)      │
└───────────────┬─────────────────────────────────────────────┘
                │  đọc filesystem (append-only) + .cache/*.json
┌───────────────▼─────────────────────────────────────────────┐
│  Nguồn dữ liệu ngoài                                         │
│  ~/.claude/projects · ~/.codex/sessions · harness/inspect   │
│  harness/runs · harness/suites · NVIDIA API (chat)          │
└─────────────────────────────────────────────────────────────┘
```

Kiến trúc **monolith in-process**: server import thẳng module `services`, không có message queue hay DB — trạng thái nằm ở filesystem + cache JSON.

---

## 2. Backend — `server.py`

FastAPI app, mount `web/` tại `/static`, phục vụ SPA tại `/`. Nhóm endpoint chính:

| Nhóm | Endpoint | Service |
|---|---|---|
| Health | `GET /api/health` | (config) |
| **Chat** | `GET /api/chat/models`, `POST /api/chat` (SSE) | `chat` |
| Runs | `GET /api/runs`, `/api/runs/{id}`, `/artifact`, `/api/runs/compare` | `runs` |
| Trigger run | `POST /api/runs/trigger`, `GET /stream/{id}` (SSE), `/budget/{id}` | `trigger` |
| **Git-jobs** | `GET/POST /api/jobs`, `/{id}`, `/approve` `/accept` `/reject` `/rollback`, `/stream` (SSE), `/diff` | `gitjobs` |
| Suites | `GET /api/suites`, `/{id}`, `GET /api/integrity` | `suites`, `integrity` |
| Governance | `GET /api/governance` | `governance` |
| Usage | `GET /api/usage`, `/api/usage/rollup`, `/api/tools` | `usage`, `behavior` |
| Sessions | `GET /api/sessions`, `/loops`, `/entropy`, `/{id}/replay` | `replay`, `behavior` |
| Inspect | `GET /api/inspect/logs`, `/api/inspect/mep` | `inspect_evals` |
| Board | `GET /api/board` | `board` |

**Quy ước lỗi:** `_http_error()` map `PermissionError→403`, `FileNotFoundError→404`, còn lại `500`. Stream (SSE) không trả 500 — lỗi được bọc thành `event: error`.

**Startup:** hook `@app.on_event("startup")` chạy `usage.warm()` + `behavior.warm()` trên daemon thread → cache ấm sẵn để trang Dashboard load nhanh.

---

## 3. Services layer (`services/*.py`)

Mỗi service là logic thuần, đọc filesystem, không giữ state toàn cục ngoài cache đĩa.

| Service | Vai trò |
|---|---|
| `chat` | Client NVIDIA (OpenAI-compatible), stream reasoning/delta/done; cờ reasoning theo họ model; lỗi upstream → `ChatUpstreamError` |
| `usage` | Gộp token-usage từ Claude/Codex/Inspect; **cache incremental per-file** |
| `behavior` | Phân tích hành vi phiên: entropy, loop, rollup tool; **cache incremental per-session** |
| `runs` | Liệt kê/đọc kết quả run trong `harness/runs`, so sánh 2 run |
| `trigger` | Khởi chạy eval suite, stream tiến trình + trạng thái budget |
| `gitjobs` | Vòng đời git-job của Codex: create→approve→(stream)→accept/reject/rollback + diff |
| `suites` / `integrity` | Đọc định nghĩa suite + xác minh chữ ký HMAC (`.hmac_key`) |
| `governance` | Trạng thái governance/recovery |
| `replay` | Liệt kê phiên + replay từng bước |
| `inspect_evals` | Đọc log Inspect + bản MEP mới nhất |
| `board` | Bảng task (parse `status.md`) |
| `risk`, `boundary`, `inform`, `verify` | Phân tầng rủi ro, ranh giới, thông báo, kiểm định (dùng nội bộ) |

### Cache incremental (điểm hiệu năng cốt lõi)
`usage.py` và `behavior.py` cache kết quả parse theo **từng file**, key = `(path, mtime_ns, size)`, lưu ở `.cache/usage_files.json` / `.cache/behavior_files.json`. Chỉ file mới/đổi mới được parse lại → endpoint nặng từ **>45s xuống ~0.6s** warm.

---

## 4. Parsers (`parsers/*.py`)

Chuẩn hoá log agent thành event thống nhất. Mỗi parser expose `paths()` (liệt kê file nguồn) + `parse_file(path)` (để cache incremental gọi lại chọn lọc):

- `claude_sessions.py` — `~/.claude/projects/**/*.jsonl`
- `codex_sessions.py` — `~/.codex/sessions` + `archived_sessions`
- `inspect_eval.py` — `harness/inspect/logs/*.eval`
- `common.py` — tiện ích chung

---

## 5. Frontend (`web/`)

- `index.html` — HUD shell: **grid** `232px | 1fr` (sidebar tối + content sáng), topbar status chips. Sidebar nhóm nav: MONITOR / CONTROL / AI / SYSTEM.
- `app.js` — SPA: hash-routing 12 trang (`#/`, `#/runs`, `#/sessions`, `#/jobs`, `#/governance`, `#/violations`, `#/chat`, `#/usage`, `#/suites`, `#/tools`, `#/inspect`, `#/board`), fetch JSON, tiêu thụ SSE.
- `charts.js` — vẽ chart (SVG/canvas thuần).
- `styles-hub.css` — token HUD trong `:root` (`--hud-bg/-surface/-border/-text/-accent`, `--status-ok/warn/danger`, `--font-mono`). **Không sửa** `styles.css` (html-kit chung).
- `DESIGN.md` — hợp đồng thiết kế; đọc trước khi sửa UI.

### Trang Chat (`#/chat`)
- Chọn model qua **selector tùy biến** (dropdown ngắn + filter category + ô search + panel chi tiết + nút copy ID) đọc từ `chatState.modelCatalog`.
- Stream: hiển thị plain text khi đang chạy, **render Markdown an toàn** (escape-first + whitelist, link chỉ http/https, code block có nút Copy) chỉ khi `done`.
- Tính năng: New chat, Export **Markdown/JSON** + Copy transcript (dùng text gốc), copy/regenerate mỗi message, Stop khi đang stream, autoscroll + jump-to-latest, Enter/Shift+Enter, lưu `localStorage` (`harness-hub-chat`), show/hide "thinking".
- Model EOL trả **HTTP 410** → error event mang `{message, code:410}`, frontend đánh dấu row `unavailable` (session-only) và chuyển về model default.

---

## 6. Cấu hình (`config.py`)

Nguồn chân lý cho path và model:

- **Paths:** `ROOT`, `RUNS_DIR`, `SUITES_DIR`, `JOBS_DIR`, `USAGE_SOURCES` (claude/codex/inspect), `INSPECT_MEP_DIR`.
- **Chat:** `CHAT_MODEL_CATALOG` (21 model NVIDIA có rank/category/bestFor/strengths/weaknesses), `CHAT_MODELS` (derive từ catalog), `CHAT_DEFAULT_MODEL = nvidia/nemotron-3-super-120b-a12b`, `CHAT_MAX_TOKENS = 16384`, `CHAT_REASONING` (cờ reasoning theo prefix họ model).
- **Guardrails job:** `STEP_CAP=50`, `JOB_TIME_CAP_SECONDS=1800`, `JOB_MAX_RUNS=3`, `JOB_BLOCKED_TIERS=[destructive]`, `JOB_ALLOW_AGENTS={codex}`, `JOB_TTL_SECONDS=3600`.
- **Behavior thresholds:** `LOOP_CONSECUTIVE_THRESHOLD=12`, `ENTROPY_WINDOW=20`, `ENTROPY_THRESHOLD=0.3`.
- `risk_tiers.json` + `load_risk_tiers()` — phân tầng tool/command/network/destructive.

---

## 7. Dữ liệu & bảo mật

- **Append-only, không DB:** trạng thái là file JSON/JSONL log + cache `.cache/*.json` (đều gitignore).
- **NVIDIA key:** đọc từ env `NVIDIA_API_KEY`. `config.py` tự `load_dotenv()` từ `.env` gốc repo lúc import (không override nếu env đã set sẵn). Key **không bao giờ** log/hardcode.
- **Chữ ký suite:** HMAC với `.hmac_key` → `integrity.verify_suites()`.
- **Git-jobs của Codex:** tách branch riêng `opus-job/<id>`, có approve gate + rollback, chặn tier `destructive`.

---

## 8. Luồng tiêu biểu

**Chat:** browser `POST /api/chat {model, messages}` → `chat.stream_chat()` gọi NVIDIA → yield reasoning/delta/done → `_sse()` → SPA render (Markdown khi done) + append usage vào `.cache/chat_usage.jsonl`.

**Dashboard:** render card nhanh ngay, 2 card nặng (Usage 7d, High Entropy) load hoãn với skeleton; `usage`/`behavior` trả từ cache incremental → ~0.6s warm.

**Git-job:** `POST /api/jobs {brief, agent=codex}` → tạo branch + chạy Codex, `GET /stream` theo dõi, review `diff`, rồi `accept` (merge) / `reject` / `rollback`.

---

## 9. Mở rộng: Super Agent Harness

Harness Hub hiện là **control-plane**: giám sát, chat, usage, replay, suites,
governance và git-jobs. Lớp mở rộng tiếp theo là **orchestration-plane** cho
workflow khai báo, thư viện skill, và sub-agent có quản trị. Mục tiêu là giữ
kiến trúc ghép nối lỏng: UI, cấu hình, runtime và execution backend tách nhau
bằng file/schema rõ ràng.

### Nguyên tắc kiến trúc

- **Config-first, không framework-first.** Source of truth là file của Harness
  (`workflow.yaml`, `agent.yaml`, `SKILL.md`, blackboard artifacts). LangGraph,
  nếu dùng, chỉ là executor adapter phía sau, không phải format lõi.
- **Markdown cho policy, YAML cho topology.** NLAH-style Markdown phù hợp cho
  phase rules, verification rules, recovery rules và stopping conditions. Graph
  node/edge/handoff nên là YAML/JSON có schema để validate, diff và test được.
- **Sub-agent không spawn tự do.** Lead agent chỉ gửi child task request. Harness
  chọn agent profile, scope, tool/skill allowlist, timeout, budget và risk tier.
  Backend nên tái dùng substrate `gitjobs`/managed runner hiện có thay vì cho
  agent tự chạy terminal process không kiểm soát.
- **Skill read-only by default.** Skill package là source artifact. Agent được
  đề xuất patch qua git-job/review flow; không tự mutate `SKILL.md` trực tiếp
  khi gặp lỗi.
- **Blackboard có schema, append-only.** Sub-agent phối hợp qua file chung có
  cấu trúc, không chat trực tiếp với nhau và không ghi đè state quan trọng.

### Substrate đề xuất

```
harness/hub/
├─ workflows/
│  ├─ code-agent.workflow.yaml   # graph: nodes, edges, handoff, stop rules
│  └─ code-agent.policy.md       # NLAH rules: verify/recover/HITL
├─ agents/
│  └─ reviewer.agent.yaml        # model, tools, skills, budget, scope
├─ skills/
│  └─ <skill-name>/SKILL.md      # skill package + scripts/references
├─ blackboard/
│  └─ <run_id>/
│     ├─ state.json              # typed shared state
│     ├─ events.jsonl            # append-only timeline
│     ├─ claims.jsonl            # findings/claims with provenance
│     ├─ decisions.md            # human/agent decisions
│     └─ artifacts/              # diffs, reports, generated files
└─ services/
   ├─ workflow.py                # parse/validate/execute workflow IR
   ├─ agents.py                  # agent profiles + child task packets
   ├─ skills.py                  # metadata index + progressive disclosure
   ├─ orchestrator.py            # node execution + handoff + HITL gates
   └─ blackboard.py              # append/read state/events/artifacts
```

Các thư mục trên là extension target, không thay thế `runs/`, `jobs/`,
`.cache/` hay `services/*` hiện có. Runtime vẫn có thể chạy in-process trong
FastAPI ở phase đầu.

### Workflow customization

Workflow không nên hardcode bằng vòng lặp Python. Runtime đọc workflow spec rồi
chuyển thành một IR nhỏ:

```
workflow.yaml + policy.md
  -> validate graph/schema/risk
  -> build execution plan
  -> execute node
  -> write blackboard
  -> verify / handoff / HITL
```

Endpoint tương lai:

| Nhóm | Endpoint | Vai trò |
|---|---|---|
| Workflows | `GET /api/workflows`, `POST /api/workflows/validate` | đọc/validate workflow |
| Workflow runs | `POST /api/workflows/{id}/runs`, `GET /api/workflows/runs/{id}/stream` | chạy + SSE |
| Blackboard | `GET /api/blackboard/{run_id}` | đọc state/events/artifacts |

LangGraph có thể được thêm sau như `services/langgraph_adapter.py`, nhận IR đã
validate từ `workflow.py`. Không để UI hoặc config phụ thuộc trực tiếp vào
LangGraph-specific object.

### Skill Library

Skill là package tái sử dụng, không chỉ là prompt:

- `SKILL.md` chứa metadata, trigger rules, usage instructions, scripts và
  references.
- `skills.py` tạo index nhẹ: name, description, path, required tools, risk tier.
- Progressive disclosure: prompt ban đầu chỉ thấy metadata. Khi workflow/agent
  chọn skill, runtime mới đọc full `SKILL.md` và các resource cần thiết.
- Telemetry: mỗi skill call ghi result/failure vào blackboard hoặc usage log.
- Evolution: failure-mode patch phải đi qua proposed diff/git-job/review, không
  auto-edit skill package.

Endpoint tương lai:

| Nhóm | Endpoint | Vai trò |
|---|---|---|
| Skills | `GET /api/skills` | metadata index |
| Skill detail | `GET /api/skills/{id}` | read full package detail theo quyền |
| Skill telemetry | `GET /api/skills/{id}/usage` | lỗi, success rate, recent runs |

### Sub-agent orchestration

Sub-agent được tạo từ **child task packet**:

```json
{
  "parent_run_id": "run-...",
  "objective": "Review UI drift against DESIGN.md",
  "agent_profile": "reviewer",
  "allowed_paths": ["harness/hub/web"],
  "allowed_tools": ["read", "test", "screenshot"],
  "skills": ["opus-design-reviewer"],
  "budget": {"seconds": 900, "steps": 30},
  "handoff_contract": "write findings to blackboard/claims.jsonl"
}
```

Lead agent không tự cấp quyền mới cho child agent. `governance` kiểm tra
profile, risk tier, blocked tiers, path scope và HITL trước khi launch. Child
agent báo cáo bằng blackboard artifacts/events; parent tổng hợp từ đó.

Endpoint tương lai:

| Nhóm | Endpoint | Vai trò |
|---|---|---|
| Agents | `GET /api/agents` | agent profiles |
| Child run | `POST /api/agents/runs` | tạo sub-agent managed run |
| Child stream | `GET /api/agents/runs/{id}/stream` | SSE tiến trình |

### Visual Workflow Builder

Canvas kéo-thả là editor/visualizer cho file cấu hình, không phải nguồn chân lý.

- Agent node -> `agents/*.yaml` reference.
- Skill node gắn vào agent -> thêm skill id/path vào `skills:` của agent node.
- Edge -> handoff logic trong `workflow.yaml`.
- Save -> generate/patch YAML + validate schema + show diff.
- Run -> gọi workflow run API.

Frontend nên thêm sau khi headless runtime chạy ổn. Với constraint hiện tại
(vanilla JS, không CDN/build step), phase đầu có thể dùng SVG/HTML thuần cho
canvas đơn giản; không đưa dependency đồ thị nặng vào Hub.

### Roadmap khuyến nghị

1. **Declarative Core:** thêm schema + parser cho workflow/agent/skill index;
   chạy workflow headless qua API; test parse/validate/handoff.
2. **Managed Sub-agents:** tái dùng `gitjobs`/managed runner, child task packet,
   blackboard append-only, replay được full chain.
3. **Skill Library:** metadata index, progressive disclosure, telemetry, proposed
   patch flow.
4. **Visual Builder:** canvas edit YAML, validate trước khi save/run, git diff
   đọc được bằng mắt.

Go/no-go: **Go với scope cắt nhỏ.** Không build toàn bộ Super Agent Harness một
lần. Build Declarative Harness Core trước; khi core chạy được bằng file + tests
+ replay, mới thêm visual builder và executor adapter.

---

## 10. Bản đồ file nhanh

```
harness/hub/
├─ server.py            # FastAPI app + routes + startup warm
├─ config.py            # paths, CHAT_MODEL_CATALOG, guardrails
├─ risk_tiers.json      # phân tầng rủi ro
├─ services/            # logic: chat, usage, behavior, runs, trigger,
│                       #        gitjobs, suites, integrity, governance,
│                       #        replay, inspect_evals, board, risk...
├─ parsers/             # claude_sessions, codex_sessions, inspect_eval, common
├─ web/                 # index.html, app.js, charts.js, styles-hub.css, DESIGN.md
├─ tests/               # pytest (provider mock, không gọi API thật)
├─ docs/                # chat.md, safeharness-*.md
├─ jobs/                # git-job state (runtime)
└─ .cache/              # cache incremental + usage chat (gitignore)
```

*(SDD docs của Hub: `RD-harness-hub.md`, `SD-harness-hub.md`, `BD-harness-hub.md`.)*
