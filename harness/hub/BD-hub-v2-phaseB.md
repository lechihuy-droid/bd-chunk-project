# BD — Hub v2 Phase B (Build Plan)
**Date:** 2026-07-16 · **Status:** 🟢 Ready · **Author:** Claude (Fable 5)
**Upstream:** `SD-hub-v2-command-center.md` §11 Phase B · Phase A đã ship (`ab67ecb`, `f132c39`, `ddbd614`, 117 tests xanh).

---

## 0. Mô hình orchestra (áp dụng cả Phase B + C)

| Vai | Ai | Làm gì |
|---|---|---|
| **Orchestra** | Claude main session (Opus/Fable) | Viết brief từng step, giao việc, ghép file shared (`server.py`, `config.py`), browser-verify UI, commit |
| **Coder** | **Codex** (`codex exec`) | Mọi step gắn nhãn `[CODEX]` — code + test đi kèm |
| **Tester/Reviewer** | **Sonnet subagent** | Sau mỗi step `[CODEX]`: (1) chạy full pytest + báo kết quả, (2) review diff đối chiếu BD, một dòng/finding |

**⚠️ Cách chạy Codex (cập nhật 2026-07-16, user chốt):** Claude giao Codex **trực tiếp qua Bash tool**, KHÔNG bắt user dán lệnh. Điều kiện để không treo (lesson nested-sandbox): Bash tool phải chạy với sandbox ngoài TẮT (Codex tự có sandbox riêng — hai lớp sandbox lồng nhau là nguyên nhân treo lần trước). Quy trình:
1. Claude viết brief ra `harness/hub/briefs/<step>.txt`.
2. Claude chạy (Bash, no outer sandbox, background):
   ```bash
   export PATH="/c/Users/HUY/AppData/Local/pnpm:$PATH" && cd <repo> && \
   codex exec --skip-git-repo-check -m gpt-5.6-sol \
     "FRESH START, don't ask. Follow harness/hub/briefs/<step>.txt exactly." </dev/null
   ```
3. Nếu vẫn treo (log codex báo terminal hang): kill, fallback = đưa lệnh cho user dán terminal thật.
4. Codex xong → Sonnet test/review → pass thì Claude commit, fail thì brief sửa (lặp).

**Test gate mỗi step:** `.ih\Scripts\python.exe -m pytest harness/hub/tests -q` xanh 100% (117+ test). Sonnet chạy, không phải Codex tự khai.
**Fake CLI rule giữ nguyên:** test không gọi claude/codex/NVIDIA thật.

---

## 1. Tổng quan step Phase B

| Step | Nội dung | Executor | Size | Phụ thuộc |
|---|---|---|---|---|
| B0 | Fix codex provider detection | [CODEX] | S | — |
| B1 | Chat multi-pane grid (panes[] refactor) | [CODEX] | L | — (song song B0) |
| B2 | Broadcast mode | [CODEX] | M | B1 |
| B3 | Session resume bền vững | [CODEX] | M | B1 |
| B4 | Skill drift tab + deploy UX + deploy log | [CODEX] | S | — (song song B1) |
| B5 | Trang Settings providers + Gemini thật | [CODEX] + user cài CLI | M | B0 |
| B✔ | Browser-verify + DESIGN.md + commit mỗi step | Claude main | — | từng step |

---

## Step B0 — Codex detection fix `[CODEX]` (S)

**Hiện trạng:** `claude` online sau fix `.cmd` (`ddbd614`); `codex` vẫn `not_installed` dù binary có (pnpm 0.144.3).
**Việc:** sửa `services/providers/codex_cli.py::status()`:
- Chạy version check với `stdin=subprocess.DEVNULL` (codex treo đọc stdin — lesson đã ghi), timeout nâng 10s, dùng `procs.resolve_cmd` (đã có).
- Nếu vẫn fail: thử `[*base, "--version"]` qua `cmd /c` với `CREATE_NO_WINDOW`; log detail thật (stderr) thay vì nuốt thành "not_installed" — để debug được từ `/api/providers`.
**Test:** fake codex script + 1 test mới: status detail chứa stderr khi returncode≠0.
**DoD:** `/api/providers` → codex `available:true, version:"codex-cli 0.144.3"` trên máy thật (Claude main verify bằng curl).

## Step B1 — Provider chat trong Workspace UI `[CODEX]` (M) — ĐỔI HƯỚNG 2026-07-16

**Quyết định user:** KHÔNG làm multi-pane ở `#/chat` (bản Codex multi-pane đầu tiên đã revert, không commit). Thay vào đó gắn provider chat vào **Workspace UI có sẵn** (`web/workspace.js`, trang `#/workspace`) — nơi đã có chat window hoàn chỉnh: sidebar Chats list + New Chat + switch chat + artifacts. Mỗi chat trong list = 1 hội thoại độc lập → "nhiều LLM song song" = nhiều chat, tự nhiên hơn pane.

**Việc (trong `workspace.js` + `styles-workspace.css` nếu cần):**
- State mỗi chat thêm `provider` (default "nvidia") + `sessionId` (null).
- Top-bar: thêm provider selector cạnh model selector hiện có (đọc `GET /api/providers`); model selector chỉ hiện khi provider = nvidia; provider CLI hiện badge `read-only` + version.
- New Chat → chọn provider cho chat đó (hoặc dropdown đổi provider khi chat còn rỗng; chat đã có message thì khoá provider).
- Send: `POST /api/chat` body `{provider, messages, model? (nvidia), session_id?}` + header `X-Hub-Client`; `done.session_id` → lưu vào chat đó.
- Persistence workspace hiện có (nếu lưu localStorage) mang theo provider/sessionId.
- `#/chat` cũ giữ nguyên (single-pane provider select đã hoạt động, commit f132c39).
**Ràng buộc:** chỉ sửa `web/workspace.js` (+ styles-workspace.css, docs/workspace.md); KHÔNG đụng app.js/backend/SSE contract.
**Test:** `node --check workspace.js`; backend suite xanh (không đổi backend).
**DoD:** browser-verify: New Chat → chọn Claude → chat thật trả lời + session resume lượt 2; chat khác chạy NVIDIA; switch qua lại không lẫn state.

## Step B2 — Broadcast chat trong Workspace `[CODEX]` (M, sau B3) — CHỐT UX 2026-07-17

**Quyết định user:** phương án B (broadcast chat) trong Workspace UI; **bỏ hẳn tab `#/chat`** (nav xoá, route redirect về `#/workspace`; code chat cũ trong app.js để nguyên như dead-code, dọn ở step riêng nếu cần).

**Việc (workspace.js):**
- Chat có thể là **broadcast chat**: `providers: [id...]` (thay vì 1 provider). Nút "Broadcast" cạnh New Chat → checkbox chọn provider (mặc định mọi provider online).
- Gửi 1 prompt → POST /api/chat song song mỗi provider; assistant row render **cột grid theo provider** (header: tên + LED trạng thái + tokens), mỗi cột stream độc lập, lỗi cột nào báo cột đó.
- `sessionId` per provider (map `{provider: sid}`) → lượt 2 tiếp tục đủ N session.
- Nút Stop all. Sidebar: badge "N⚡" cho broadcast chat.
- Nav: xoá link Chat; route `#/chat` → `location.hash = "#/workspace"`.
**DoD:** browser-verify: broadcast 2 provider (nvidia+claude) trả song song 2 cột; hỏi lượt 2 cả hai nhớ ngữ cảnh; #/chat redirect.

## Step B3 — Session resume bền vững `[CODEX]` (M, sau B1)

**Việc (FR-105):**
- Claude: đã có `-r <session_id>` — verify sau restart server vẫn resume (session của CLI, không phụ thuộc server).
- Codex: verify `codex exec resume <id>` trên 0.144.3 (Codex tự test bằng fake trước, Claude main verify thật). Không ổn → fallback nối transcript ≤4000 chars vào prompt, set capability `resume:false`.
- UI: pane hiện chip `session <id-8-chars>` khi có; nút "New chat" reset per-pane.
**Test:** fake CLI trả session_id → pane gửi lượt 2 kèm `-r`/`resume` đúng.
**DoD:** chat Claude 2 lượt — lượt 2 nhớ ngữ cảnh lượt 1 (Claude main verify thật, 1 lần, prompt rẻ).

## Step B4 — Skill drift tab + deploy UX `[CODEX]` (S, song song B1)

**Việc (FR-113 UI):** trang `#/skills-lib`:
- Tab "Drift": bảng DriftEntry (name, variants source+hash-8+mtime, nút "Sync →" chọn hướng = gọi deploy).
- Deploy: confirm dialog (from → to, cảnh báo backup tự tạo); hiện kết quả + link backup path.
- Panel "Deploy log": đọc `GET /api/skill-library/deploy-log` (endpoint MỚI — đọc `.cache/skill_deploy_log.jsonl`, 50 dòng cuối).
**Test:** endpoint deploy-log + fixture.
**DoD:** browser-verify drift tab hiện `opus-design-reviewer` (đang drift thật trên máy).

## Step B5 — Settings providers + Gemini `[CODEX]` (M, sau B0)

**Việc (FR-131 + Gemini):**
- Trang `#/settings`: bảng provider (id, version, available, detail, capabilities), nút Refresh; hint cài đặt khi offline (gemini: `npm i -g @google/gemini-cli`).
- `gemini_cli.py` thật: `gemini -p <prompt>` one-shot, history tự nối vào prompt (capability `resume:false`), parse stdout plain text → delta events; usage=0 nếu không có số liệu. status() qua `resolve_cmd`.
- **User action trước:** cài Gemini CLI + login Google ở terminal thật. Chưa cài → step vẫn merge được (stub logic giữ nguyên khi absent).
**Test:** fake gemini script.
**DoD:** settings page render 4 provider đúng trạng thái; nếu user đã cài gemini → chat được 1 lượt thật.

---

## 2. Quy trình lặp mỗi step (orchestra checklist)

```
1. Claude: viết harness/hub/briefs/<step>.txt (scope + file whitelist + test yêu cầu + DoD)
2. User: chạy lệnh codex exec (paste-ready, terminal thật)
3. Sonnet #1 (test-runner): full pytest + node --check; báo pass/fail + log lỗi
4. Sonnet #2 (reviewer): diff vs brief — scope creep? file ngoài whitelist? style? một dòng/finding
5. Claude: fix nhỏ trực tiếp (nếu finding S) hoặc brief sửa cho Codex (nếu M/L)
6. Claude: browser-verify UI step nào có UI + screenshot
7. Claude: commit theo format feat/fix(hub) + cập nhật TODO
```

**Definition of Done Phase B:** B0–B5 merge, suite xanh, codex+claude+nvidia (+gemini nếu cài) chat được thật từ UI, multi-pane + broadcast + resume hoạt động, drift/deploy UI chạy, settings page live.

*Hub v2 — BD Phase B | 2026-07-16*
