# AI Workspace — Global Rules

Parent-level context for all projects under `C:/Users/HUY/workspace/ai-project-opus/`.

---

## SDD — Spec-Driven Development (chỉ cho project lớn)

**Khi nào dùng full SDD (RD → SD → BD, mỗi bước chờ APPROVE):** project mới từ đầu, feature lớn nhiều tuần, hoặc thay đổi kiến trúc. Task thông thường KHÔNG cần RD/SD — chỉ cần plan/BD ngắn rồi giao Codex (xem Workflow Orchestration bên dưới).

**Toolkit:** `C:/Users/HUY/workspace/ai-project-opus/SDD-toolkit/`
- Process: `SDD-toolkit/workflow/sdd-process.md`
- Checklist: `SDD-toolkit/workflow/checklist.md`
- Templates: `SDD-toolkit/templates/` (RD, SD, BD, BACKLOG)
- Bootstrap new project: `python SDD-toolkit/scripts/scaffold.py`

**Phase gates (khi dùng full SDD):**
1. **RD** (Requirements Doc) — usage-first, functional reqs, open questions → APPROVE before design
2. **SD** (System Design) — architecture, interface contracts → APPROVE before build
3. **BD** (Build Plan) — step-by-step, test plan → APPROVE before code
4. **Implementation** — follow BD, no scope creep
5. **Review** — test checklist pass → Done

---

## Workflow Orchestration

### Plan Mode
- Task with 3+ steps → enter plan mode first (`/plan`), write spec, wait for approval
- If going off-track mid-task → STOP, re-plan immediately, do not continue
- Simple bug report → fix directly, no plan needed

### Subagent Strategy
- Use subagents to keep the main context window clean
- One subagent = one specific task, never vague multi-purpose tasks
- Complex problems: break into pieces + throw more compute, don't cram into one conversation

### Self-Improvement Loop
- After any correction: write a new rule into `tasks/lessons.md` (if file exists)
- Rules must be specific enough to prevent that exact mistake — no generic platitudes
- Re-read `lessons.md` at session start if the file exists

### Verification Before Done
- Never mark a task complete without proving it works
- Self-check: "Would a staff engineer approve this?" — if not, fix it first
- Run tests, check logs, demonstrate correctness — never assume

### Model & Agent Routing
Phân tuyến công việc theo loại task:

| Loại task | Thực thi bằng |
|---|---|
| Plan, kiến trúc, SDD docs (RD/SD/BD/CR), review, quyết định trade-off | **Opus 4.7** — main session |
| Task thông thường (search, đọc, verify, sửa nhỏ, status, giải thích) | **Sonnet** |
| Coding (implement) + viết test | **Codex** (`codex exec`) — Claude viết BD/brief rồi giao, KHÔNG tự code |

- Main session chạy MỘT model tại một thời điểm — user đổi bằng `/model`. Claude không tự đổi được.
- Đầu mỗi task lớn, Claude báo task thuộc tuyến nào để user `/model` cho đúng.
- Coding/test: luôn giao Codex; Claude chỉ viết spec/BD và review kết quả — không code trực tiếp trừ khi user yêu cầu.
- Routine fan-out lớn (search rộng, verify hàng loạt) có thể tách ra Sonnet subagent để khỏi tốn Opus.

---

## Coding Behavior (Karpathy Principles)

**Tradeoff:** These rules prioritize correctness over speed. Use judgment for simple tasks.

### 1. Think Before Coding
- State assumptions explicitly before coding. If unsure, ask.
- If a request has multiple interpretations, present all of them — never silently pick one.
- If there's a simpler approach, say so. Push back when warranted.

### 2. Simplicity First
- Write the minimum code that correctly solves the problem. No unrequested features.
- No abstractions for single-use code. No "flexibility" or "configurability" nobody asked for.
- No error handling for scenarios that cannot happen.
- Ask: "Would a senior engineer call this overcomplicated?" — if yes, rewrite.

### 3. Surgical Changes
- Only touch code directly related to the request. Do not "improve" surrounding code.
- Do not refactor what isn't broken. Preserve existing style.
- If unrelated dead code is spotted — mention it, do not delete it.
- Every changed line must be traceable to the user's request.

### 4. Goal-Driven Execution
- Convert vague tasks into concrete, verifiable criteria before starting.
- For multi-step tasks, state the plan as: `[Step] → verify: [check]`
- For bugs: write a test that reproduces the bug first, then fix.

---

## Python

- Python 3.11: `C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe`
- Use `.env` for credentials, never hardcode
- Do not modify files in `raw/` — immutable sources

## Shell / Scheduler

- Use Windows Task Scheduler instead of cron
- Bash tool: use `cmd //c "schtasks ..."` for Task Scheduler commands
- **Response language: Vietnamese** — keep responses concise

## Git & Data Safety

User không rành git — AI tự thực hiện toàn bộ quy trình git, không yêu cầu user gõ lệnh.

- **Trước mọi `git push`:** tự động `git fetch origin` + `git merge origin/main` rồi mới push — remote thường đi trước local (autosync từ máy khác + PR từ cloud agent). Không cần hỏi user trước khi merge.
- **Conflict:** tự resolve phần rõ ràng; chỉ khi hai bên sửa cùng nội dung mới hỏi user bằng câu đơn giản ("bên A viết X, bên B viết Y — giữ cái nào?"), không bắt user đụng lệnh git.
- **Pull Request:** KHÔNG cài đặt/auth `gh` CLI — đưa GitHub compare link để user bấm tạo PR.
- **Dữ liệu nhạy cảm — cấm commit/push:** dữ liệu tài chính thật (`opus-animus/opus-actio/finance.db`, `data/_local/`), dữ liệu sức khỏe cá nhân, thông tin user profile. Không chép số liệu thật vào docs/report sẽ được push lên GitHub.

---

## Projects

Root chứa nhiều project con (`opus-animus/`, `SDD-toolkit/`, `html-kit/`, `viet-japan-app/`, `health-app/`, `bd-ai-workflow/`, ...) — dùng `ls` để xem cấu trúc hiện tại thay vì bảng cứng dễ lỗi thời.

---

## HTML Output Kit

**Rule:** Khi tạo documentation, report, diagram, comparison, hoặc bất kỳ structured output — ưu tiên single self-contained HTML file thay vì markdown. Link `styles.css`/`diagram.js` externally (không inline) để tiết kiệm tokens.

**Kit location + chi tiết (classes, JSON diagram schema, khi nào dùng gì):** `C:/Users/HUY/workspace/ai-project-opus/html-kit/README.md`

**Slash command:** `/html [mô tả]` — available in Claude Code

---

## Session Behavior

- Start from the user's latest request.
- Treat that request as the active task.
- Read project state files only when the user explicitly asks to resume prior state or the task depends on current project status.
- Do not run or require a status checkpoint flow unless the user explicitly asks for one.

## CLI — Use terminal instead of sidebar for long sessions

```
claude --resume      # resume most recent session
claude --continue    # same
```
Sidebar extension may lose history index. Terminal is more stable for long-running work.
