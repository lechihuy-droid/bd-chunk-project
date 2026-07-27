# SD — Hub v2: LLM Command Center (System Design)
**Date:** 2026-07-14 · **Status:** 🟡 In Review · **Author:** Claude (Fable 5)
**Upstream:** `RD-hub-v2-command-center.md` (✅ approved 2026-07-14, default all + tái dùng chat UI + cockpit dashboard)

---

## 1. Architecture Overview

```
Browser SPA (tái dùng web/ hiện có)
  #/chat  → multi-pane (nhân bản chat component v1)
  #/skills-lib → skill library đa CLI
  #/      → Dashboard + cockpit token gauges
        │ HTTP JSON + SSE   (+ header X-Hub-Client — CSRF guard mới)
        ▼
FastAPI server.py (v1 giữ nguyên, thêm routes)
        │
┌───────┴────────────────────────────────────────────┐
│ services/providers/   ← LỚP MỚI TRUNG TÂM          │
│   base.py      Provider protocol + registry        │
│   claude_cli.py  spawn `claude -p` stream-json     │
│   codex_cli.py   spawn `codex exec` (pattern       │
│                  gitjobs, read-only)               │
│   nvidia_api.py  wrap services/chat.py hiện có     │
│   gemini_cli.py  (Phase B — stub trả unavailable)  │
│   procs.py     process registry: timeout, kill,    │
│                cleanup on shutdown, max concurrent │
├────────────────────────────────────────────────────┤
│ services/skill_library.py  ← MỚI (tách khỏi        │
│                              runtime_skills)       │
│ services/usage.py          ← SỬA: thêm nguồn chat  │
└────────────────────────────────────────────────────┘
        │ filesystem
~/.claude/skills · <project>/.claude/skills · ~/.codex/skills
~/.claude/projects (session logs — telemetry) · .cache/chat_usage.jsonl
```

Giữ nguyên triết lý v1: monolith in-process, file là chân lý, không DB, vanilla JS, không CDN/build step.

---

## 2. Module Layout (mới/sửa)

```
harness/hub/
  server.py                    # +routes providers/chat v2/skill-library; +CSRF middleware; on_event→lifespan
  config.py                    # +PROVIDERS config, SKILL_SOURCES, QUOTA_WARN_PER_DAY, CHAT_CLI_TIMEOUT
  services/
    providers/
      __init__.py              # registry: get_provider(id), list_providers()
      base.py                  # ProviderStatus, ChatEvent, Provider protocol
      claude_cli.py
      codex_cli.py
      nvidia_api.py
      gemini_cli.py            # stub: status=not_installed + install hint
      procs.py                 # ProcessRegistry (spawn/track/timeout/kill-all)
    skill_library.py
    usage.py                   # SỬA: + parser nguồn "chat" (.cache/chat_usage.jsonl)
  web/
    app.js                     # chat multi-pane (refactor chatState→panes[]), trang skills-lib, cockpit
    charts.js                  # +renderGauge (SVG arc), +renderCounter
    styles-hub.css             # +cockpit tokens (gauge, seven-seg counter, LED)
  tests/
    test_providers.py          # fake CLI script làm subprocess giả — KHÔNG gọi CLI thật
    test_skill_library.py      # fixtures 3 nguồn skill
    test_csrf.py
```

**Quy tắc giữ nguyên v1:** services trả dict/list thuần; server.py chỉ map HTTP; UI không parse file thô. KHÔNG sửa `services/chat.py` hiện có (nvidia_api.py chỉ wrap nó).

---

## 3. CLI Provider Layer

### 3.1 Contract

```python
class ProviderStatus(TypedDict):
    id: str            # "claude" | "codex" | "gemini" | "nvidia"
    available: bool
    version: str | None
    detail: str        # "ok" | "not_installed" | "not_logged_in" | hint
    capabilities: dict # {"stream": bool, "resume": bool, "models": [..] | None}

# Mỗi provider expose:
def status() -> ProviderStatus
def stream_chat(messages, session_id=None, model=None) -> Iterator[ChatEvent]
# ChatEvent = {"type": "reasoning"|"delta"|"done"|"error", ...}
# "done" mang {"usage": {input_tokens,output_tokens,total_tokens}, "session_id": str|None}
```

SSE event ra ngoài **giữ nguyên format v1** (`reasoning|delta|done|error`) → UI chat v1 tái dùng không đổi contract; chỉ thêm field `session_id` trong `done`.

### 3.2 claude_cli.py

- Lệnh: `claude -p <prompt> --output-format stream-json --verbose --permission-mode plan --disallowedTools "*"`; lượt sau thêm `--resume <session_id>`.
- Chỉ gửi **message mới nhất** làm prompt; lịch sử do CLI tự giữ qua session (capability `resume: true`).
- Parse stdout: mỗi dòng 1 JSON — `type:"assistant"` → delta text; `type:"result"` → usage + session_id.
- Khoá tool 2 lớp: permission-mode plan + disallowedTools (RD FR-103). Badge "read-only" do UI render từ capability.
- BD phải verify cờ chính xác trên claude 2.1.207 trước khi code (flag có thể khác giữa version).

### 3.3 codex_cli.py

- Lệnh: `codex exec -s read-only --skip-git-repo-check <prompt>` với **preamble "FRESH START"** + stdin đóng (`stdin=DEVNULL`) — theo lesson đã ghi; binary: bản **pnpm**, path đặt trong `config.PROVIDERS["codex"]["cmd"]`, KHÔNG hardcode npm wrapper.
- Resume: thử `codex exec resume <session_id>`; nếu 0.144.3 không hỗ trợ ổn → fallback nối lịch sử vào prompt (transcript ≤ N ký tự cuối). Quyết định chốt ở BD sau khi verify.
- Usage: codex exec in token count ra stderr/log — parse best-effort, thiếu thì usage=0 (không chặn).

### 3.4 nvidia_api.py + gemini_cli.py

- nvidia: adapter mỏng gọi `chat.stream_chat()` hiện có; capability `models: CHAT_MODELS`.
- gemini: Phase A chỉ trả `status: not_installed` + hint cài đặt. Phase B: `gemini -p` one-shot, lịch sử tự nối vào prompt (capability `resume: false`).

### 3.5 procs.py — Process Registry (NFR-104)

- Bảng `{proc_id: {popen, provider, started, timeout}}`; mọi provider CLI spawn qua đây.
- Timeout mỗi lượt chat: `CHAT_CLI_TIMEOUT = 300s` → kill + event `error`.
- Max concurrent CLI: 3 (config) → vượt thì trả 429 "busy".
- FastAPI `lifespan` shutdown: kill toàn bộ process còn sống. **Đồng thời fix orphan của v1**: startup quét jobs `status=running` không có stream → đánh dấu `failed (orphaned)`.

---

## 4. REST API (mới/sửa)

| Method | Path | Trả về | Ghi chú |
|---|---|---|---|
| GET | `/api/providers` | `[ProviderStatus]` | FR-131 |
| POST | `/api/chat` | SSE (giữ format v1) | body thêm `provider` (default `"nvidia"` — back-compat), `session_id?`. Validate: provider ∈ registry, available |
| GET | `/api/skill-library` | `[SkillEntry]` | FR-111 |
| GET | `/api/skill-library/{id}` | `SkillDetail` | FR-112. `{id}` lookup theo index, không dùng làm path (chống traversal — pattern v1) |
| POST | `/api/skill-library/{id}/deploy` | `{ok, target, path}` | FR-113. body `{target: "claude_user"\|"codex_user"\|...}` |
| GET | `/api/skill-library/drift` | `[DriftEntry]` | FR-113 |
| GET | `/api/usage/cockpit` | `CockpitStats` | FR-132 — rollup gọn cho dashboard |

### Data contracts

```json
// SkillEntry
{ "id": "claude_user/skillspector", "name": "skillspector",
  "description": "<từ frontmatter SKILL.md>",
  "source": "claude_user|claude_project|codex_user",
  "path": "...", "content_hash": "sha256:...",
  "coverage": ["claude_user", "codex_user"],       // các nguồn có skill cùng tên
  "last_used": "2026-07-12T...|null", "use_count_30d": 4 }

// DriftEntry
{ "name": "skillspector", "variants": [ {"source","path","content_hash","mtime"} ],
  "in_sync": false }

// CockpitStats (FR-132)
{ "today":  { "by_provider": [ {"provider","calls","total_tokens"} ], "calls", "total_tokens" },
  "week7d": { "by_provider": [...], "calls", "total_tokens" },
  "quota_warn_per_day": 200, "warn": false,
  "providers_online": [ {"id","available"} ] }
```

---

## 5. Skill Library (`services/skill_library.py`)

- **Nguồn** (config `SKILL_SOURCES`): `claude_user: ~/.claude/skills` · `claude_project: <ROOT>/.claude/skills` · `codex_user: ~/.codex/skills`. Mỗi skill = thư mục chứa `SKILL.md` (hoặc file `.md` đơn với codex).
- **Index:** scan → parse frontmatter (name, description); id = `<source>/<dirname>`; hash nội dung toàn thư mục (sha256 từng file, sort) để so drift. Cache theo mtime như pattern usage v1.
- **Telemetry:** tái dùng behavior parser — đếm event Skill-tool trong `~/.claude/projects/**/*.jsonl` khớp tên skill → `last_used`, `use_count_30d`. Codex session: best-effort, thiếu thì null.
- **Deploy:** copy đệ quy source→target; nếu target đã tồn tại → backup `<name>.bak-<ts>/` cạnh đó rồi ghi đè; ghi 1 dòng vào `.cache/skill_deploy_log.jsonl` (audit). KHÔNG symlink (Windows cần quyền admin).
- **Drift:** nhóm theo `name`, so `content_hash` giữa các nguồn.
- Ngoài scope: convert format Claude↔Codex tự động (deploy = copy nguyên trạng; codex 0.144 đọc được SKILL.md — verify ở BD).

---

## 6. Chat multi-pane (tái dùng UI v1 — FR-133)

- **Refactor state:** `chatState` (object đơn) → `chatPanes: [paneState]`; paneState = shape cũ + `{provider, sessionId}`. Migration localStorage: đọc `harness-hub-chat` cũ → pane[0] provider nvidia; key mới `harness-hub-chat-v2`.
- **Provider picker:** tái dùng component model-picker hiện có — cấp 1 chọn provider (Claude/Codex/NVIDIA/Gemini-disabled), cấp 2 (chỉ nvidia) chọn model từ catalog cũ. Provider CLI hiện badge `read-only` + version từ `/api/providers`.
- **Layout:** grid 1–3 cột (`repeat(auto-fit, minmax(360px, 1fr))`); nút "+ Pane" (max 3), nút đóng pane. Mobile: 1 cột stack.
- **Giữ nguyên:** markdown renderer an toàn, export MD/JSON, copy/regenerate, stop, autoscroll, thinking toggle — mỗi pane một instance.
- Broadcast (FR-104, Phase B): input chung phía trên, gửi đồng thời mọi pane active.

---

## 7. Cockpit Dashboard (FR-132)

- **Data:** `usage.py` thêm nguồn `"chat"` đọc `.cache/chat_usage.jsonl` (đã có sẵn format UsageEvent v1 — chỉ việc khai báo nguồn); provider CLI cũng append vào file này với `source: "chat"`, `model: "cli:claude"|"cli:codex"|...`. `/api/usage/cockpit` rollup today + 7d.
- **UI:** hàng cockpit trên Dashboard, style HUD sẵn có của styles-hub.css:
  - **Arc gauge SVG** mỗi provider: tokens hôm nay / ngưỡng cảnh báo (`QUOTA_WARN_PER_DAY` calls — đổi màu `--status-warn` khi >80%, `--status-danger` khi vượt) — vẽ trong charts.js, không thư viện.
  - **Counter kiểu seven-segment** (font-mono, chữ to): tổng calls + tokens hôm nay.
  - **LED status** mỗi provider (chấm tròn ok/offline) từ `/api/providers`.
- Cập nhật `web/DESIGN.md` (hợp đồng thiết kế) trước khi code UI — quy trình v1.

---

## 8. Security

- **CSRF guard (NFR-106, làm ĐẦU TIÊN):** middleware trên mọi request non-GET:
  1. Nếu có header `Origin`/`Referer` → phải là `http://127.0.0.1:8799` hoặc `http://localhost:8799`, sai → 403.
  2. Yêu cầu header `X-Hub-Client: harness-hub` trên mọi `fetch` của SPA (custom header → cross-origin bắt buộc preflight → bị chặn). Thiếu → 403.
  - Test: POST không header → 403; POST Origin lạ → 403; GET không ảnh hưởng.
- Provider/prompt validate như v1 (whitelist provider, prompt là string, không nhận path/arg tuỳ ý từ client). CLI spawn `shell=False` (pattern v1).
- Skill deploy chỉ cho phép giữa các nguồn khai báo trong `SKILL_SOURCES` — không nhận path từ client.

---

## 9. Performance & Reliability

- First token CLI ~2–8s (cold start) — UI hiện trạng thái "starting <provider>…" trong pane (skeleton v1).
- Skill index < 1s: quét ~10 skill, cache mtime.
- Parser/file lỗi → skip + warning, không crash (NFR-002 v1 giữ nguyên).

## 10. Test Plan (khung — BD chi tiết hoá)

- `test_providers.py`: fake CLI = script python in stream-json giả → verify parse delta/done/session_id/usage; timeout → kill + error event; max-concurrent → 429.
- `test_skill_library.py`: fixtures 3 nguồn → index/coverage/drift/deploy (backup tồn tại, log ghi).
- `test_csrf.py`: matrix Origin × header.
- `test_api.py` mở rộng: `/api/chat` back-compat không có `provider`.
- KHÔNG test nào gọi CLI/API thật.

## 11. Phasing (khớp RD §7)

- **Phase A** (BD-A): CSRF middleware + lifespan/orphan fix → providers layer (claude, codex, nvidia, procs) → chat multi-pane → skill index/detail → cockpit dashboard.
- **Phase B** (BD-B): broadcast · resume bền vững · skill deploy/drift · trang Settings providers · cài + bật Gemini.
- **Phase C** (BD-C): agent profiles → workflow headless (executor = provider layer, HITL = runtime_interrupts) → canvas SVG (cuối cùng).

---

*Hub v2 — SD v1 | 2026-07-14 | chờ APPROVE trước khi viết BD-A*
