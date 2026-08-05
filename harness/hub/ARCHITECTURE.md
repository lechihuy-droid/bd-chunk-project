# Harness Hub — Kiến trúc hệ thống

> Web UI (localhost) giám sát + điều khiển các AI agent: theo dõi usage/hành vi, chạy eval suites, quản lý git-jobs của Codex, và một cửa sổ Chat gắn NVIDIA.

- **Chạy:** `.ih\Scripts\python.exe harness\hub\server.py` → `http://127.0.0.1:8799`
- **Stack:** FastAPI + Uvicorn (backend) · React 19 + TypeScript + Vite 6 + Tailwind v4 (frontend `web-v3/`). Có build step; server phục vụ bundle đã build trong `web-v3/dist`.
- **Build frontend:** `cd harness/hub/web-v3 && pnpm build` (= check-encoding → `tsc -b` → `vite build`). Lint: `pnpm lint` (**oxlint**, không phải eslint).
- **Kiểm thử backend:** `.ih\Scripts\python.exe -m pytest harness/hub/tests -q` (235 test, provider luôn được mock).

---

## 1. Sơ đồ tầng

```
┌─────────────────────────────────────────────────────────────┐
│  Browser SPA  (web-v3/dist — React 19 + Vite + Tailwind v4) │
│  Shell: sidebar zones · topbar tab nav · content zone        │
│  HashRouter · fetch JSON · SSE cho stream/chat/workflow run  │
└───────────────┬─────────────────────────────────────────────┘
                │  HTTP / Server-Sent Events (text/event-stream)
┌───────────────▼─────────────────────────────────────────────┐
│  server.py  (FastAPI)                                        │
│  - REST /api/* + StaticFiles /assets (bundle Vite)           │
│  - GET / → FileResponse(web-v3/dist/index.html)              │
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

FastAPI app, mount `web-v3/dist/assets` tại `/assets`, phục vụ SPA tại `/`. Nhóm endpoint chính:

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
| **Workflows** | `GET /api/workflows`, `/{id}/source`, `/{id}/layout`; `PUT /{id}`, `/{id}/model`, `/{id}/layout`; `POST /api/workflows/validate` | `workflow` |
| **Workflow runs** | `POST /api/workflows/{id}/runs` (SSE), `GET /api/workflows/runs/{id}/artifacts[/{name}]`, `POST .../interrupts/{id}/resume` | `workflow_exec`, `runtime_*` |
| **Agent runs** | `GET/POST /api/agent/runs`, `/{id}`, `/{id}/events`, `POST /{id}/interrupts/{id}/resume` | `runtime_pipeline`, `runtime_children` |
| **Agents** | `GET/POST /api/agents`, `DELETE /api/agents/{id}` | `runtime_agents` |
| **Providers** | `GET /api/providers`, `/api/model-classes`, `/api/risk-tiers` | `services/providers/*`, `config` |
| **Skills** | `GET /api/skills`, `/names`, `/{id}`, `/{id}/usage` | `runtime_skills` |
| **Skill library** | `GET /api/skill-library`, `/drift`, `/deploy-log`, `/{id}`; `POST /{id}/deploy` | `skill_library` |
| **Memory** | `GET /api/memory`, `/candidates`; `POST /candidates/{id}/accept|reject` | `runtime_memory` |
| **Guardrails** | `GET /api/guardrails/decisions`, `POST /api/guardrails/decisions/command` | `runtime_policy` |
| Usage cockpit | `GET /api/usage/cockpit` | `usage`, `pricing` |

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
| `workflow` | Parse/validate `workflows/*.yaml` → IR. **Ràng buộc thật:** chỉ chấp nhận **một chuỗi tuyến tính** (`_walk_chain` bắt in/out-degree ≤ 1, đúng 1 start + 1 end); edge là tuple 2 phần tử `[from, to]`, không có field phụ; node type chỉ `agent` \| `validate` |
| `workflow_exec` | Chạy IR, phát SSE (`debug`, `assistant_delta`, `reasoning`, `node_update`, `validation_pass/fail`, `artifact_written`, `child_run`, `interrupt`, `state_snapshot`, `done`, `error`). `gate: approval` tạo interrupt và **dừng trước** khi node đó chạy |
| `runtime_*` (13 module) | Nền runtime: `agents` (profile + resolve provider/model-class), `pipeline`, `state`, `checkpoint`, `events`, `interrupts`, `children`, `skills`, `memory`, `policy`, `reducers`, `validate`, `artifacts` |
| `skill_library` | Index skill đa nguồn (`claude_project`/`claude_user`/`codex_user`), phát hiện drift giữa các bản sao, deploy sang target + deploy-log |
| `providers/` | Adapter thực thi: `claude_cli`, `codex_cli`, `gemini_cli`, `nvidia_api` (+ `base`, `procs`). `provider` của agent có thể là id thật hoặc alias model-class (`cheap`/`code`/`smart`) — resolve phía server |
| `pricing` | Quy đổi token → chi phí cho usage cockpit |
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

## 5. Frontend (`web-v3/`)

SPA React 19 + TypeScript, build bằng Vite 6, style bằng Tailwind v4. Thư mục `web/` (SPA vanilla JS cũ) **đã bị gỡ bỏ**; server chỉ phục vụ `web-v3/dist`.

```
web-v3/
├─ src/main.tsx          # HashRouter + mount
├─ src/index.css         # @theme Tailwind v4 — nguồn token đang dùng thật
├─ src/styles/tokens.css # bảng token --hub-* (chưa import)
├─ src/components/       # Layout, Sidebar, Topbar, RunSpine, GateCard, ArtifactRail
├─ src/lib/              # api.ts, sse.ts, runsApi.ts, artifact.ts, markdown.tsx, ui.tsx, Table, Chart
├─ src/pages/            # 14 trang + index.tsx (bảng route)
├─ scripts/              # check-encoding.mjs (chặn mojibake tiếng Việt lúc build)
└─ dist/                 # bundle server phục vụ — phải build lại sau khi sửa src
```

- **Shell** (`components/Layout.tsx`): sidebar zone (`TỔNG QUAN` / `TRÒ CHUYỆN` / `ĐIỀU PHỐI` / `GIÁM SÁT` / `HỆ THỐNG`) + mục `RECENT` (artifact thật đọc từ `localStorage['hub-v3-chats']`) · topbar breadcrumb + tab nav ngang + popover search/provider-status.
- **Route** (`pages/index.tsx`): `overview`, `chat`, `sessions`, `workflows`, `runs`, `artifacts`, `agents`, `skills`, `hooks`, `files`, `approvals`, `usage`, `settings`.
- **`lib/ui.tsx`** — primitive dùng chung: `Button`, `IconButton`, `Input`, `Select`, `Textarea`, `Chip`, `Status`, `ProviderDot`, `EmptyState`, `Popover`. UI mới phải tái dùng, không tự dựng biến thể riêng.
- **`web-v3/DESIGN.md`** — hợp đồng thiết kế (dark technical workbench: 4 tầng bề mặt, accent tím duy nhất, màu provider chỉ dùng cho chấm 6-8px). Đọc trước khi sửa UI.
- **Quy ước dữ liệu:** mọi số/hàng hiển thị phải đến từ API thật; thiếu nguồn thì hiện `—` hoặc empty-state ghi rõ `TODO(backend)`. Không dựng dữ liệu mẫu trông-như-thật.

### Trang chưa có backend
`hooks` và `files` hiện chỉ là vỏ giao diện (bảng 0 dòng + control disabled + empty-state `TODO(backend)`) — chưa có `/api/hooks` hay `/api/files`. Hub cũng **không có** khái niệm workspace hay storage-quota.

### Trang Chat (`#/chat`)
- Layout 3 panel: sidebar (Chats/Files/Artifacts) · khung hội thoại · panel artifact; có Focus mode ẩn panel giữa.
- Chọn model qua `ModelSelector` đọc `/api/chat/models` + `/api/providers`.
- Stream SSE: plain text khi đang chạy, render Markdown khi `done`; lưu `localStorage` (`hub-v3-chats`).
- Panel artifact: chọn vùng văn bản → toolbar nổi (Hỏi AI / Viết lại / Rút gọn / Comment / Copy); toggle nạp artifact vào bối cảnh prompt.

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

> **Trạng thái:** orchestration-plane đã chạy in-process trong FastAPI. Mã runtime
> nằm ở `services/workflow.py`, `services/workflow_exec.py` và các module
> `services/runtime_*.py`; endpoint thật được liệt kê dưới đây. Không có module
> `orchestrator.py`, `blackboard.py`, `agents.py`, `skills.py`, hay route
> `/api/blackboard/{run_id}`.

Harness Hub khởi đầu là **control-plane**: giám sát, chat, usage, replay, suites,
governance và git-jobs. Lớp mở rộng là **orchestration-plane** cho
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
├─ runtime/
│  └─ runs/<run_id>/
│     ├─ state.json              # runtime state
│     ├─ events.jsonl            # append-only runtime events
│     └─ artifacts/              # task packets and generated artifacts
└─ services/
   ├─ workflow.py                # parse/validate workflow model
   ├─ workflow_exec.py           # workflow node execution + handoff + gates
   ├─ runtime_agents.py          # agent profiles + provider resolution
   ├─ runtime_skills.py          # skill metadata and usage
   ├─ runtime_children.py        # child task packets and child-run lifecycle
   └─ runtime_state/events/artifacts.py # persisted state, events, artifacts
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
| Workflow runs | `POST /api/workflows/{id}/runs` | chạy, trả SSE response |
| Workflow artifacts | `GET /api/workflows/runs/{id}/artifacts` | liệt kê artifacts |
| Workflow gate | `POST /api/workflows/runs/{id}/interrupts/{interrupt_id}/resume` | resume/approve gate |

LangGraph có thể được thêm sau như `services/langgraph_adapter.py`, nhận IR đã
validate từ `workflow.py`. Không để UI hoặc config phụ thuộc trực tiếp vào
LangGraph-specific object.

### Skill Library

Skill là package tái sử dụng, không chỉ là prompt:

- `SKILL.md` chứa metadata, trigger rules, usage instructions, scripts và
  references.
- `runtime_skills.py` tạo index nhẹ: name, description, path và usage.
- Progressive disclosure: prompt ban đầu chỉ thấy metadata. Khi workflow/agent
  chọn skill, runtime mới đọc full `SKILL.md` và các resource cần thiết.
- Telemetry: usage được đọc qua runtime skill usage log.
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

`runtime_children.create_child_run` chỉ cho lead runtime spawn, giới hạn số child
run, yêu cầu objective và chặn child mở rộng `allowed_paths`/`allowed_tools` so
với parent. Hàm này **không** kiểm tra `risk_tier` hoặc HITL trước khi launch.
Child ghi task packet, state, events và artifacts vào runtime; parent tổng hợp
child summary/artifacts qua `runtime_state` và `runtime_events`.

Endpoint tương lai:

| Nhóm | Endpoint | Vai trò |
|---|---|---|
| Agents | `GET /api/agents` | agent profiles |
| Child/agent run | `POST /api/agent/runs` | tạo managed runtime, trả SSE response |
| Run detail/events | `GET /api/agent/runs/{id}`, `GET /api/agent/runs/{id}/events` | state và event history |
| Resume gate | `POST /api/agent/runs/{id}/interrupts/{interrupt_id}/resume` | tiếp tục runtime interrupt |

### Visual Workflow Builder

Canvas kéo-thả là editor/visualizer cho file cấu hình, không phải nguồn chân lý.

- Agent node -> `agents/*.yaml` reference.
- Skill node gắn vào agent -> thêm skill id/path vào `skills:` của agent node.
- Edge -> handoff logic trong `workflow.yaml`.
- Save -> generate/patch YAML + validate schema + show diff.
- Run -> gọi workflow run API.

**Đã ship** trong `web-v3/src/pages/WorkflowsPage.tsx`: canvas pan/zoom + kéo-thả
node + nối edge port-to-port, viết bằng React/SVG thuần — không thêm thư viện đồ
thị nào. Save gọi `PUT /{id}/model` + `PUT /{id}/layout`, validate gọi
`POST /api/workflows/validate`, run gọi `POST /api/workflows/{id}/runs` và gate
dùng route resume workflow.
Lưu ý: UI cho phép vẽ tự do nhưng backend vẫn chỉ nhận **chuỗi tuyến tính** —
đồ thị rẽ nhánh sẽ bị `validate_workflow` từ chối.

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
│  │                    #        gitjobs, suites, integrity, governance,
│  │                    #        replay, inspect_evals, board, pricing, risk...
│  ├─ workflow.py       # parse/validate/IR (chuỗi tuyến tính)
│  ├─ workflow_exec.py  # thực thi + SSE
│  ├─ runtime_*.py      # state, checkpoint, events, interrupts, children,
│  │                    # agents, skills, memory, policy, reducers, validate...
│  ├─ skill_library.py  # index + drift + deploy
│  └─ providers/        # claude_cli, codex_cli, gemini_cli, nvidia_api, base, procs
├─ parsers/             # claude_sessions, codex_sessions, inspect_eval, common
├─ web-v3/              # frontend React/Vite (src/, dist/, DESIGN.md) — `web/` cũ đã gỡ
├─ workflows/           # *.yaml + *.layout.json
├─ agents/              # agent profile
├─ runtime/             # state/events/artifact của agent + workflow run
├─ tests/               # pytest 235 test (provider mock, không gọi API thật)
├─ docs/                # chat.md, safeharness-*.md, harness_hub_backend_docs_v0_1/
├─ jobs/                # git-job state (runtime)
└─ .cache/              # cache incremental + usage chat (gitignore)
```

*(SDD docs của Hub: `RD-harness-hub.md`, `SD-harness-hub.md`, `BD-harness-hub.md`.)*
