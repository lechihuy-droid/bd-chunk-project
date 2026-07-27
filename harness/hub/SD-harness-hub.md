# SD — Harness Hub (System Design)
**Date:** 2026-06-28 · **Status:** 🟡 In Review · **Author:** Claude (Opus 4.8)
**Upstream:** `RD-harness-hub.md` (approved scope, cost-tracking dropped → tokens/calls only)

---

## 1. Architecture Overview

```
Browser (Chrome, localhost:8799)
        │  HTTP (JSON + static)
        ▼
┌────────────────────────────────────────────┐
│ FastAPI app  (harness/hub/server.py)        │
│  • static SPA   (hub/web/*)                 │
│  • REST API     (/api/*)                     │
│  • run trigger  (subprocess + SSE stream)    │
├────────────────────────────────────────────┤
│ Service layer (hub/services/)               │
│  runs.py    suites.py   trigger.py          │
│  usage.py   inspect_evals.py   boundary.py  │
└───────────────┬─────────────────────────────┘
                │ read-only filesystem
   ┌────────────┼──────────────┬───────────────┐
   ▼            ▼              ▼               ▼
harness/runs/  harness/suites/  ~/.claude/projects/*  ~/.codex/sessions/*
*/summary.json  *.json           */*.jsonl (Claude)    *.jsonl (Codex)
*/report.md                      harness/inspect/logs/*.eval (Inspect)
*/trace.jsonl
*/logs/*.txt
```

Không DB. Không state nền. Server đọc filesystem mỗi request (có cache nhẹ TTL 5s cho list).

---

## 2. Module Layout (Codex tạo)

```
harness/hub/
  server.py              # FastAPI app + uvicorn entry (__main__)
  run-hub.ps1            # wrapper: .ih\Scripts\python.exe harness\hub\server.py
  config.py              # ROOT, HARNESS_DIR, RUNS_DIR, SUITES_DIR, PORT=8799, usage source paths
  services/
    __init__.py
    boundary.py          # resolve_in_root(path) -> Path | raise; tái dùng ý tưởng từ run_harness.py
    runs.py              # list_runs(), get_run(run_id), read_artifact(run_id, rel)
    suites.py            # list_suites(), get_suite(suite_id)
    trigger.py           # start_run(suite_id, check?) -> stream lines (subprocess)
    usage.py             # collect_usage() -> events[]; rollup(); parsers cho 3 nguồn
    inspect_evals.py     # list .eval logs + đọc MEP (gọi export_mep nếu có)
    board.py             # FR-014: đọc opus-animus/ai/status.md + handoff -> TaskBoard
    replay.py            # FR-015: parse 1 session jsonl -> 3-pane (outline/agent/monitor)
  parsers/
    claude_sessions.py   # parse ~/.claude/projects/*/*.jsonl
    codex_sessions.py    # parse ~/.codex/sessions + archived_sessions/*.jsonl
    inspect_eval.py      # parse harness/inspect/logs/*.eval (dùng inspect_ai.log nếu có, fallback zip)
  web/
    index.html           # SPA shell, <link> tới ../../html-kit/styles.css (copy vào hub/web/ nếu cần)
    app.js               # router + fetch + render (vanilla, no build)
    charts.js            # bar chart đơn giản (SVG, không thư viện)
    styles-hub.css       # phần override nhỏ riêng hub
  tests/
    test_runs.py  test_suites.py  test_usage_parsers.py  test_boundary.py  test_api.py
    fixtures/            # sample summary.json, *.jsonl claude/codex, suite json
```

**Quy tắc:** services trả về dict/list thuần Python (đã chuẩn hoá), `server.py` chỉ map sang JSON + lo HTTP. UI không tự parse file thô.

---

## 3. Data Contracts (chuẩn hoá — UI chỉ thấy những shape này)

### 3.1 RunSummary (list item)
```json
{ "run_id": "20260627-234104-workspace-smoke", "suite": "workspace-smoke",
  "suite_name": "Workspace Smoke Harness", "status": "pass",
  "passed": 11, "failed": 0, "total": 11,
  "started_at": "2026-06-27T14:41:04+00:00", "finished_at": "...",
  "duration_seconds": 2.77 }
```
Nguồn: `runs/<id>/summary.json` (đã có sẵn các field này). `duration_seconds` = sum check durations nếu thiếu.

### 3.2 RunDetail
```json
{ "summary": RunSummary,
  "checks": [ { "id","type","status","severity","message","hint",
                "duration_seconds","evidence": {...},
                "logs": ["logs/recall-tests.stdout.txt", ...] } ],
  "report_md": "<raw markdown of report.md>",
  "artifacts": ["summary.json","trace.jsonl","report.md","logs/..."] }
```

### 3.3 Suite
```json
{ "id","name","description",
  "checks": [ { "id","type","hint","raw": {<nguyên check json>} } ],
  "check_count": 11, "path": "harness/suites/workspace-smoke.json" }
```

### 3.4 UsageEvent (CHUẨN HOÁ — mọi nguồn map về đây; KHÔNG có field tiền)
```json
{ "ts": "2026-06-27T14:41:04+00:00",   // ISO; nếu nguồn thiếu → mtime file
  "source": "claude" | "codex" | "inspect",
  "model": "claude-opus-4-8" | "gpt-5-codex" | ...,   // BẮT BUỘC model thật, không fallback "codex"/"claude"
  "session": "<file stem / session id>",
  "command": "<best-effort: suite id / agent / cwd>",   // có thể null
  "input_tokens": 4378,
  "output_tokens": 290,
  "cache_read_tokens": 13340,        // 0 nếu nguồn không có
  "cache_creation_tokens": 4547,     // 0 nếu nguồn không có
  "total_tokens": 22555,             // CÔNG THỨC CHỐT (áp cho CẢ 3 nguồn):
                                     //   input + output + cache_read + cache_creation
                                     //   = mọi token thật đã tiêu. KHÔNG có biến thể.
  "calls": 1 }                       // = số lần model được gọi (model invocation)
```
**`calls` — định nghĩa thống nhất = số lần model được gọi:**
- Claude: mỗi assistant message (sau dedup theo message.id) = 1 call.
- Codex: mỗi event `token_count` = 1 call.
- Inspect: mỗi sample/turn có model_usage = 1 call.
> Cùng đơn vị "model invocation" → `by_model.calls` so sánh được giữa nguồn. UI có thể chú thích nguồn nếu cần.

### 3.5 UsageRollup
```json
{ "by_model":  [ { "model","calls","input_tokens","output_tokens","total_tokens" } ],
  "by_day":    [ { "day":"2026-06-27","calls","input_tokens","output_tokens","total_tokens" } ],
  "by_source": [ { "source","calls","total_tokens" } ],
  "totals":    { "calls","input_tokens","output_tokens","total_tokens" } }
```

---

## 4. Usage Parsers — spec cụ thể (đã verify trên máy)

### 4.1 Claude (`parsers/claude_sessions.py`)
- Đường dẫn: `~/.claude/projects/*/*.jsonl` (glob mọi project dir). Mỗi dòng = 1 JSON object.
- Lọc dòng `type == "assistant"` có `message.usage`. Lấy:
  `model = message.model`; `usage = message.usage`.
- Map: `input_tokens=usage.input_tokens`, `output_tokens=usage.output_tokens`,
  `cache_read_tokens=usage.cache_read_input_tokens`, `cache_creation_tokens=usage.cache_creation_input_tokens`.
- `ts = object.timestamp` (nếu có) else file mtime. `session = file stem`.
  `command` = tên project dir decode (vd `C--Users-HUY-workspace`). `calls=1`.
- Dedupe theo `message.id` (mỗi message log nhiều lần do streaming) → giữ 1.

### 4.2 Codex (`parsers/codex_sessions.py`)
- Đường dẫn: `~/.codex/sessions/*.jsonl` + `~/.codex/archived_sessions/*.jsonl`.
- Lọc event `type == "token_count"` (có `token_usage{input_tokens,output_tokens,total_tokens}`).
  Lưu ý: codex thường log usage **luỹ kế** → lấy giá trị **cuối cùng (last) mỗi session** làm tổng.
  Emit 1 UsageEvent/session; `calls` = số event `token_count` trong session (model invocation).
- `model`: **BẮT BUỘC lấy model thật** từ session — đọc event cấu hình đầu session (vd `session_meta`/`turn_context`/dòng có field `model`) trong cùng file rollout. Nếu một session thật sự không có field model nào → emit `model = "codex:unknown"` (để lộ thiếu sót, KHÔNG gộp chung thành `"codex"` làm mất tách model). `total_tokens` tính lại theo công thức §3.4 (đừng tin `total_tokens` luỹ kế của codex nếu nó chỉ là input+output).
- `ts` từ tên file rollout hoặc mtime.

### 4.3 Inspect (`parsers/inspect_eval.py`)
- `harness/inspect/logs/*.eval`. Ưu tiên `from inspect_ai.log import read_eval_log` (có trong `.ih`).
  Lấy `log.stats.model_usage` → mỗi model: input/output/total tokens.
- Fallback nếu import lỗi: `.eval` là zip → đọc `header.json`/`reductions` tìm `model_usage`. Nếu vẫn fail → skip file, log warning, không crash.
- `source="inspect"`, `command = task name`, `session = log filename`.

> Tất cả parser: lỗi 1 file → skip + ghi `warnings[]`, KHÔNG làm hỏng toàn bộ collect (NFR-002).

### 3.6 TaskBoard (FR-014)
```json
{ "objective": "<từ status.md Current objective>",
  "owner": "claude|codex", "updated": "2026-06-..",
  "sub_systems": [ { "name","status","note" } ],
  "next_step": "<từ Claude handoff nếu có, nếu không từ status.md>",
  "source_files": ["opus-animus/ai/status.md","opus-animus/ai/handoff-claude.md"] }
```
Parser best-effort theo heading markdown; thiếu field → null, không crash.

### 3.7 SessionReplay (FR-015) — 3-pane từ 1 session jsonl
```json
{ "session": "<file stem>", "source": "claude|codex",
  "outline":  [ { "ts","kind":"plan|todo|step","text" } ],           // pane 1
  "agent":    [ { "ts","role":"assistant","text","tool_calls":[ {"name","input"} ] } ], // pane 2 (chain-of-thought + tool args)
  "monitor":  [ { "ts","kind":"tool_result|file|error","tool","summary" } ] }            // pane 3 (env/kết quả)
```
- Claude: dòng `type=assistant` → agent (content text + `tool_use` blocks → tool_calls); `type=user`/`tool_result` → monitor; TodoWrite/plan → outline.
- Codex: map tương tự từ event rollout. Replay tĩnh (không live).

### 3.8 BudgetStatus (FR-016) — chỉ cho run hub-trigger
```json
{ "stream_id","suite","steps_done","steps_total",
  "step_cap": 50, "warn": false,        // warn=true khi steps_done > 80% step_cap
  "tokens_used": null, "token_cap": null }  // null = N/A: mọi suite hiện tại tất định, không gọi LLM
```
- **MVP chỉ làm step-budget** (`steps_done/steps_total` so với `step_cap`). Bar đổi màu khi `warn`.
- `tokens_used`/`token_cap` = `null` cho tới khi có suite gọi LLM (chưa tồn tại). UI ẩn phần token khi null — KHÔNG vẽ thanh token 0/∞ gây hiểu nhầm.
- `step_cap` từ `config.py`.

---

## 5. REST API

| Method | Path | Trả về | Ghi chú |
|---|---|---|---|
| GET | `/api/health` | `{ok, root, runs_dir, port}` | |
| GET | `/api/runs` | `[RunSummary]` desc theo time | cache 5s |
| GET | `/api/runs/{run_id}` | `RunDetail` | 404 nếu không thấy/ngoài root |
| GET | `/api/runs/{run_id}/artifact?rel=logs/x.txt` | text/plain | boundary-checked, chỉ trong run dir |
| GET | `/api/runs/compare?a=&b=` | `{added,removed,changed[]}` | FR-007 (P1) |
| GET | `/api/suites` | `[Suite]` | |
| GET | `/api/suites/{suite_id}` | `Suite` | |
| POST | `/api/runs/trigger` | body `{suite, check?}` → `{stream_id}` | spawn subprocess |
| GET | `/api/runs/stream/{stream_id}` | `text/event-stream` (SSE) | dòng stdout/stderr realtime + exit |
| GET | `/api/usage` | `[UsageEvent]` (+ `?source=&model=&since=`) | |
| GET | `/api/usage/rollup` | `UsageRollup` (+ filter giống trên) | |
| GET | `/api/inspect/logs` | `[{name,task,model_usage,ts}]` | FR-008 (P1) |
| GET | `/api/inspect/mep` | MEP packet mới nhất | gọi export_mep nếu cần |
| GET | `/api/board` | `TaskBoard` | FR-014 |
| GET | `/api/sessions` | `[{session,source,ts,project}]` | list session cho replay |
| GET | `/api/sessions/{session}/replay` | `SessionReplay` | FR-015. `{session}` PHẢI khớp 1 phần tử do `/api/sessions` liệt kê (lookup theo id → path nội bộ); TUYỆT ĐỐI không dùng `{session}` làm path/filename trực tiếp → chống traversal |
| GET | `/api/runs/budget/{stream_id}` | `BudgetStatus` | FR-016, kèm SSE stream |
| GET | `/` , `/static/*` | SPA | |

### Trigger contract (FR-006)
- `start_run`: spawn `{py311} harness/run_harness.py --suite {suite} [--check {check}] --json`,
  `cwd = ROOT`. Validate `suite` ∈ list_suites() (chống injection). Không cho arg tuỳ ý.
- SSE event: `{ "type":"line"|"exit", "data": "<text>"|{"code":0,"run_id":"..."} }`.
  Khi exit: client refetch `/api/runs`.

---

## 6. Boundary & Security (NFR-003/005)

- `boundary.resolve_in_root(p)`: `Path(p).resolve()` phải nằm dưới `ROOT.resolve()`, else `PermissionError` → HTTP 403.
- Mọi endpoint nhận path (`artifact?rel=`) đi qua hàm này; chỉ cho phép trong **run dir tương ứng**.
- Usage parsers đọc NGOÀI root (`~/.claude`, `~/.codex`) — đây là ngoại lệ **chủ ý, read-only**, khai báo tường minh trong `config.py` (`USAGE_SOURCES`), không nhận path từ client.
- uvicorn bind `127.0.0.1:8799`. Không CORS mở. Trigger chỉ chạy `run_harness.py` với suite đã whitelist.

---

## 7. Frontend (vanilla SPA, no build)

- Hash router: `#/` dashboard · `#/runs` · `#/runs/:id` · `#/suites` · `#/suites/:id` · `#/usage` · `#/inspect` · `#/board` · `#/sessions` · `#/sessions/:id` (3-pane replay).
- Dashboard tích hợp Task Board card (FR-014) + budget bar khi có run đang chạy (FR-016).
- Trang `#/sessions/:id`: layout 3 cột (Outline · Agent · Monitor) theo SessionReplay (SD §3.7), cuộn đồng bộ theo `ts`.
- Fetch JSON từ `/api/*`, render bằng template string. Dùng `html-kit/styles.css` (badge/card/table/diff/callout).
- `charts.js`: vẽ bar chart SVG thuần (tokens theo model/ngày) — không thêm Chart.js.
- Dashboard: card mỗi suite (status badge + sparkline pass/fail) + card "AI usage 7 ngày" (tổng tokens/calls theo model).
- Render `report.md`: **server trả `report_md` raw**, client render bằng 1 markdown mini-renderer thuần JS (chỉ heading/table/code/link) — không server-side, không thư viện ngoài.

---

## 8. Performance (NFR-001)

- `list_runs`: chỉ đọc `summary.json` (không đọc trace/report) → nhanh. Cache TTL 5s.
- `usage`: glob + stream đọc jsonl, cache TTL 30s (file lớn). Có `?since=` để giới hạn.
- Mục tiêu: dashboard < 1s với ≤ 500 run.

---

## 9. Dependencies

- Dùng `.ih` venv: FastAPI, uvicorn, (markdown-it nếu có). Không cài thêm gói mới nếu tránh được.
- Nếu thiếu gói: ghi vào `requirements-hub.txt`, cài vào `.ih` (không tạo venv mới).

---

*Harness Hub — SD v1 | 2026-06-28*
