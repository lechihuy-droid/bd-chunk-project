# BD — Hub v2 Phase A (Build Plan)
**Date:** 2026-07-14 · **Status:** 🟢 Ready to build · **Author:** Claude (Opus 4.8)
**Upstream:** `SD-hub-v2-command-center.md` §11 Phase A (✅ approved). Giao **Codex** implement; Claude review+verify.

**Mục tiêu Phase A:** CSRF guard + fix orphan → CLI Provider Layer (claude/codex/nvidia) → Chat multi-pane (tái dùng UI v1) → Skill library index/detail → Cockpit dashboard.

**Cờ CLI đã verify trên máy (2026-07-14) — dùng CHÍNH XÁC:**
- claude 2.1.207: `-p`, `--output-format stream-json`, `--verbose` (BẮT BUỘC kèm stream-json), `--permission-mode plan` (choice hợp lệ), `--disallowed-tools <tools...>`, `-r/--resume [id]`
- codex 0.144.3: `exec -s read-only`, `--skip-git-repo-check`, `--json` (JSONL ra stdout), subcommand `resume`

---

## Nguyên tắc (theo CLAUDE.md)
- Surgical: KHÔNG sửa `services/chat.py`, KHÔNG đổi contract SSE v1 (`reasoning|delta|done|error`).
- Mọi test dùng **fake CLI** (script python in JSONL giả) — TUYỆT ĐỐI không gọi claude/codex thật trong test.
- Chạy test: `.ih\Scripts\python.exe -m pytest harness/hub/tests -q` phải xanh sau mỗi step.

---

## Step 1 — CSRF middleware + lifespan (NFR-106, NFR-104)
**File:** `server.py`, `tests/test_csrf.py`
1. Middleware `@app.middleware("http")`: với method ∈ {POST, PUT, DELETE, PATCH}:
   - Nếu có `Origin` hoặc `Referer` header → phải bắt đầu bằng `http://127.0.0.1:8799` hoặc `http://localhost:8799`; sai → 403 JSON `{"detail":"cross-origin blocked"}`.
   - Bắt buộc header `X-Hub-Client: harness-hub`; thiếu → 403.
   - GET/HEAD bỏ qua (SSE stream GET không vướng).
2. Chuyển `@app.on_event("startup")` → `lifespan` context manager. Trong startup: giữ warm cache v1 + gọi `gitjobs.reconcile_orphans()` (Step mới, xem 1b).
3. Shutdown: gọi `procs.kill_all()` (Step 2).

**Step 1b — orphan reconcile:** `gitjobs.py` thêm `reconcile_orphans()`: quét job `status=="running"` mà `job_id not in _STREAMS` → set `status="failed"`, `error="orphaned by restart"`, `finished_at=now`.

**Verify:** test_csrf matrix (POST no-header→403; POST bad Origin→403; POST đúng→pass; GET no-header→200). Test reconcile: tạo job giả running → reconcile → failed.

---

## Step 2 — Process Registry (`services/providers/procs.py`)
1. `ProcessRegistry`: dict `{proc_id: entry}`, lock. `spawn(cmd, cwd, env, timeout) -> proc_id` (shell=False, pattern trigger.py). Đếm live; vượt `config.MAX_CONCURRENT_CLI=3` → raise `BusyError`.
2. Watcher thread mỗi proc: quá `timeout` (config `CHAT_CLI_TIMEOUT=300`) → kill + đánh dấu timed_out.
3. `kill_all()` cho lifespan shutdown. `unregister` khi proc kết thúc.
4. Config thêm: `MAX_CONCURRENT_CLI`, `CHAT_CLI_TIMEOUT`, `QUOTA_WARN_PER_DAY=200`.

**Verify:** test spawn fake sleeper vượt timeout → killed; spawn thứ 4 → BusyError.

---

## Step 3 — Provider base + registry (`services/providers/base.py`, `__init__.py`)
1. `base.py`: TypedDict `ProviderStatus`, `ChatEvent`; Protocol `Provider` (`status()`, `stream_chat(messages, session_id, model)`).
2. `__init__.py`: registry dict → `get_provider(id)`, `list_providers()` trả `[ProviderStatus]`. Provider chưa impl → status available=False.

---

## Step 4 — nvidia_api.py (dễ nhất, làm trước để nối UI sớm)
- Adapter mỏng: `stream_chat` gọi `chat.stream_chat()` hiện có, map ra ChatEvent (đã cùng shape). `status()`: available = có `NVIDIA_API_KEY`; capabilities `{stream:true, resume:false, models: config.CHAT_MODELS}`.
- `done` event thêm `session_id: None`.

**Verify:** test mock chat.stream_chat → nvidia provider yield đúng events.

---

## Step 5 — claude_cli.py
- `_build_cmd(prompt, session_id)`: `[claude_bin, "-p", prompt, "--output-format","stream-json","--verbose","--permission-mode","plan","--disallowed-tools","Edit","--disallowed-tools","Write","--disallowed-tools","Bash"]` + `["-r", session_id]` nếu có. (Verify lúc code: nếu `--disallowed-tools "*"` chặn-tất hoạt động thì dùng; nếu không, list rõ Edit/Write/Bash/NotebookEdit. Plan mode đã chặn ghi — đây là lớp 2.)
- Spawn qua procs; parse stdout từng dòng JSON: `type=="assistant"`→ delta (content text); `type=="result"`→ done với usage (`input_tokens`,`output_tokens`) + `session_id` (từ field `session_id`). Dòng lỗi JSON → skip.
- `status()`: chạy `claude --version` (timeout 5s, cache 60s) → available + version; capabilities `{stream:true, resume:true, models:None}`.
- Append usage vào `.cache/chat_usage.jsonl` với `source:"chat"`, `model:"cli:claude"`.

**Verify:** fake `claude` script (config trỏ tới) in JSONL giả 2 dòng assistant + 1 result → parse ra delta×2 + done có session_id + usage.

---

## Step 6 — codex_cli.py
- `_build_cmd(prompt, session_id)`: bản pnpm (config `PROVIDERS["codex"]["cmd"]`), `["exec","-s","read-only","--skip-git-repo-check","--json", full_prompt]`; full_prompt = preamble "FRESH START\n\n" + prompt (lesson). session_id có → `["exec","resume",session_id,...]` (verify resume hoạt động; không thì fallback: nối transcript ≤4000 ký tự cuối vào prompt, capability resume=false).
- Spawn qua procs với `stdin=DEVNULL`. Parse `--json` JSONL: event có delta text → delta; token count event → gom usage; kết thúc → done + session_id (nếu codex in ra).
- `status()`: `codex --version` → available + version; capabilities `{stream:true, resume: <verify>, models:None}`.
- Usage append `model:"cli:codex"`.

**Verify:** fake `codex` script in JSONL giả → parse delta + done.

---

## Step 7 — gemini_cli.py stub + /api/providers
- `gemini_cli.py`: `status()` → available=False, detail="not_installed", hint cài `@google/gemini-cli`. `stream_chat` → yield 1 error event "Gemini chưa cài".
- `server.py`: `GET /api/providers` → `list_providers()`.
- Sửa `POST /api/chat`: đọc `payload["provider"]` (default `"nvidia"` — back-compat v1), validate ∈ registry & available; route sang provider tương ứng. Giữ nguyên `_chat_messages` validate. `session_id` optional passthrough.

**Verify:** test_api `/api/providers` trả 4 dòng; `/api/chat` không có provider → vẫn chạy nvidia (back-compat); provider không available → 400.

---

## Step 8 — skill_library.py + endpoints
- Config `SKILL_SOURCES = {"claude_user": ~/.claude/skills, "claude_project": ROOT/.claude/skills, "codex_user": ~/.codex/skills}`.
- `list_skills()`: scan mỗi nguồn (thư mục có SKILL.md, hoặc file .md đơn ở codex); parse frontmatter name/description; id=`<source>/<name>`; `content_hash` (sha256 các file sort); `coverage` = nguồn khác có cùng name; telemetry qua behavior parser (`last_used`, `use_count_30d`) best-effort. Cache mtime.
- `get_skill(id)`: lookup theo index (KHÔNG dùng id làm path) → render SKILL.md raw + list file.
- `drift()`: nhóm theo name, so hash.
- `deploy(id, target)`: copy đệ quy source→target dir; target tồn tại → backup `<name>.bak-<ts>` rồi ghi đè; append `.cache/skill_deploy_log.jsonl`. Chỉ target ∈ SKILL_SOURCES.
- Endpoints: `GET /api/skill-library`, `/api/skill-library/drift`, `/api/skill-library/{id}`, `POST /api/skill-library/{id}/deploy`.

**Verify:** fixtures 3 nguồn (skill trùng tên khác hash) → index coverage đúng, drift phát hiện, deploy tạo backup + log.

---

## Step 9 — usage.py thêm nguồn chat (vá gap v1)
- `USAGE_SOURCES` thêm `"chat": HUB_DIR/".cache"/"chat_usage.jsonl"`; parser đọc JSONL (đã đúng shape UsageEvent). Rollup by_model/by_source tự gộp.
- `GET /api/usage/cockpit`: rollup today + 7d, group by provider (map model `cli:claude`→provider claude, `nvidia/*`→nvidia...), kèm `providers_online` từ list_providers, `quota_warn_per_day`.

**Verify:** fixture chat_usage.jsonl → cockpit trả today/week7d đúng tổng.

---

## Step 10 — Frontend: chat multi-pane (tái dùng v1 — FR-133)
- Refactor `chatState`→`chatPanes[]` (mảng paneState = shape cũ + `provider`,`sessionId`). Migration: đọc `harness-hub-chat` cũ → panes[0] nvidia; lưu key mới `harness-hub-chat-v2`.
- Provider picker cấp 1 (tái dùng component model-picker); NVIDIA hiện thêm model catalog cũ; CLI hiện badge `read-only`+version.
- Layout grid `repeat(auto-fit,minmax(360px,1fr))`, nút +Pane (max 3) / đóng pane. Mọi tính năng v1 (markdown, export, stop, regenerate, thinking) per-pane.
- `fetch` mọi nơi thêm header `X-Hub-Client: harness-hub` (kể cả v1 calls) — nếu không sẽ bị CSRF chặn.

**Verify (Claude, browser tools):** mở #/chat, 2 pane (nvidia + claude), gửi tin → stream về đúng pane; screenshot desktop+mobile.

---

## Step 11 — Frontend: skill library + cockpit
- Trang `#/skills-lib`: bảng SkillEntry (name, source, coverage chips, last_used, use_count); tab Drift; click → detail render SKILL.md; nút Deploy (chọn target).
- Dashboard: hàng cockpit — `charts.js` thêm `renderGauge` (SVG arc, đổi màu warn/danger theo QUOTA_WARN) + `renderCounter` (seven-seg font-mono); LED provider từ /api/providers. Cập nhật `web/DESIGN.md` trước.
- Thêm nav items MONITOR/AI group.

**Verify (Claude, browser tools):** screenshot cockpit + skills-lib desktop+mobile; đối chiếu DESIGN.md.

---

## Test checklist tổng (Definition of Done Phase A)
- [ ] pytest xanh toàn bộ (v1 cũ không vỡ + test mới providers/skill/csrf/cockpit)
- [ ] CSRF: request thiếu header → 403; SPA vẫn hoạt động (đã thêm header)
- [ ] Chat 3 provider (nvidia/claude/codex) stream được, read-only badge đúng
- [ ] Không zombie process sau khi tắt server (kiểm bằng tasklist)
- [ ] Skill library liệt kê đủ 3 nguồn, deploy tạo backup + log
- [ ] Cockpit hiển thị token/call today+7d, chat usage đã được gộp
- [ ] Claude verify UI qua browser (desktop+mobile), khớp DESIGN.md

---

## Brief giao Codex (copy vào codex exec)
```
FRESH START. Implement Phase A theo harness/hub/BD-hub-v2-phaseA.md, tuần tự Step 1→11.
Sau mỗi step chạy: .ih\Scripts\python.exe -m pytest harness/hub/tests -q (phải xanh).
KHÔNG sửa services/chat.py. KHÔNG đổi contract SSE v1. Test dùng fake CLI, không gọi
claude/codex thật. Dùng đúng cờ CLI đã verify ghi trong BD. Frontend giữ vanilla JS,
không CDN, không build step. Báo lại từng step + kết quả test.
```

*Hub v2 — BD Phase A | 2026-07-14*
