# RD — Hub v2: LLM Command Center
**Date:** 2026-07-14 · **Status:** ✅ APPROVED 2026-07-14 (default all Q1–Q5 + 2 bổ sung: tái dùng chat UI v1, dashboard cockpit)
**Author:** Claude (Fable 5) — main session
**Upstream:** Harness Hub v1 (RD/SD/BD-harness-hub, đã ship). Đây là RD cho lớp mở rộng, thay thế phạm vi "Track B" trong TODO.md.

---

## 0. Problem Statement

**Vấn đề:** User vận hành nhiều LLM CLI (Claude Code, Codex, sắp tới Gemini CLI) nhưng
mỗi thứ một cửa sổ terminal, một chỗ config, một bộ skill riêng. Không có nơi nào:
(1) chat được với nhiều LLM cạnh nhau, (2) quản lý skill tập trung cho mọi CLI,
(3) thiết kế agent/workflow trực quan.

**Ràng buộc quyết định kiến trúc:** User **không có API key** (Anthropic/OpenAI/Google
API). Chỉ có **subscription qua app/CLI** (Claude Pro qua `claude`, ChatGPT plan qua
`codex`, Google account qua `gemini`). → Mọi lời gọi model phải đi qua **CLI headless
làm backend** ("CLI-as-API"), không phải REST API.

**Hiện trạng đã verify (2026-07-14):**
- `claude` 2.1.207 ✔ — hỗ trợ `claude -p --output-format stream-json`, `--resume`, `--permission-mode`
- `codex` 0.144.3 ✔ — `codex exec` (Hub đã dùng trong gitjobs); lưu ý: dùng bản pnpm, preamble "FRESH START", `</dev/null` (lesson đã ghi)
- `gemini` ✘ chưa cài — npm `@google/gemini-cli`, free tier với Google login
- NVIDIA chat (API key, free) đã có trong Hub v1 — giữ nguyên làm provider thứ 4

---

## 1. Usage — Người Dùng Dùng Thế Nào

### 1.1 User Profile
Không đổi so v1: HUY, solo, Windows 11, localhost, Chrome. Không code tay — giao Codex implement.

### 1.2 Typical Usage Flows

**Flow A — Multi-LLM chat:**
```
Bước 1: Mở #/chat → bấm "+ cửa sổ" → chọn provider (Claude / Codex / Gemini / NVIDIA)
Bước 2: Gõ câu hỏi vào 1 pane → CLI spawn headless, stream trả lời vào pane đó
Bước 3: (Tuỳ chọn) bật "broadcast" → 1 câu hỏi gửi cả 3 pane → so sánh câu trả lời
Bước 4: Hội thoại tiếp tục trong pane (CLI resume session), export markdown như v1
```

**Flow B — Skill library:**
```
Bước 1: Mở #/skills → thấy MỌI skill từ mọi nguồn (~/.claude/skills, project skills,
        ~/.codex skills) trong 1 bảng: tên, mô tả, nguồn, CLI nào đang có, lần dùng gần nhất
Bước 2: Click 1 skill → xem SKILL.md render + file đính kèm + usage telemetry
Bước 3: Bấm "Deploy" → copy skill sang CLI khác (vd skill Claude → thư mục skill Codex)
Bước 4: Tab "Drift" → những skill tồn tại ở 2 nơi nhưng nội dung lệch nhau → bấm sync
```

**Flow C — Agent + workflow:**
```
Bước 1: Mở #/agents → tạo agent profile bằng form: tên, CLI provider, system prompt,
        skill được gắn, quyền (read-only / write), budget (phút / lượt gọi)
Bước 2: Mở #/workflows → ghép agent thành pipeline (phase 1: form tuần tự;
        phase 2: canvas kéo-thả) → Save = sinh workflow.yaml
Bước 3: Bấm Run → runtime chạy từng node qua CLI provider, stream tiến trình,
        pause ở HITL gate chờ approve, artifact ghi vào blackboard
```

---

## 2. Tính khả thi (đánh giá trước khi chốt FR)

| Chức năng | Khả thi | Cơ chế | Rủi ro chính |
|---|---|---|---|
| Chat Claude không API key | **Cao** ✅ | `claude -p --output-format stream-json --resume <id>` chạy bằng subscription | Cold-start ~2-5s/message; quota subscription dùng chung với session làm việc |
| Chat Codex không API key | **Cao** ✅ | `codex exec` (pattern gitjobs đã có); resume qua `codex exec resume` | Lesson cũ: npm wrapper hỏng → phải gọi bản pnpm; preamble FRESH START |
| Chat Gemini không API key | **Trung bình** ⚠️ | Cài `@google/gemini-cli` (free); `gemini -p` one-shot | Headless multi-turn yếu hơn — có thể phải tự nối lịch sử hội thoại vào prompt mỗi lượt |
| Skill library đa CLI | **Cao nhất** ✅ | Thuần đọc/ghi filesystem — sở trường của Hub; `/api/skills` đã có khung | Codex/Gemini chưa có chuẩn skill giống Claude → cần lớp "mapping" khi deploy |
| Agent profiles + workflow headless | **Cao** ✅ | `runtime_pipeline` đã có checkpoint/interrupt/child-run; executor node = CLI provider | Chạy agent thật = đốt quota; CLI fail giữa chừng cần retry/timeout (pattern đã có) |
| Canvas kéo-thả | **Có điều kiện** ⚠️ | SVG thuần vanilla JS (không CDN) — làm được nhưng đắt nhất | Chỉ làm SAU khi workflow chạy được bằng YAML; canvas là editor, YAML là chân lý |

**Điểm nghẽn chung:** cả 3 chức năng đứng trên cùng một nền — **CLI Provider Layer**
(spawn/stream/resume/khoá quyền cho từng CLI). Đây là hạng mục P0 nền móng, làm trước tiên.

**An toàn:** các CLI này là *agent* (có thể chạy tool, sửa file), không phải chatbot.
Chat mode mặc định phải khoá: Claude `--permission-mode plan` hoặc disallow tools;
Codex `-s read-only`; Gemini sandbox. Chỉ agent trong workflow (Flow C) mới được cấp
quyền write, qua approve gate như gitjobs.

---

## 3. Functional Requirements

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-101 | **CLI Provider Layer**: service thống nhất spawn/stream/resume/kill cho claude/codex/gemini; mỗi provider khai báo capability (streaming? resume? permission flags?) | P0 | Nền của mọi FR khác. Tái dùng pattern trigger/gitjobs |
| FR-102 | Chat multi-window: N pane song song, mỗi pane 1 provider + 1 session; stream SSE; lịch sử localStorage như v1 | P0 | Claude + Codex + NVIDIA trước; Gemini sau khi cài |
| FR-103 | Chat mode = read-only bắt buộc (permission flags per provider); hiển thị rõ badge "read-only" trên pane | P0 | An toàn — CLI là agent, không phải chatbot |
| FR-104 | Broadcast mode: 1 prompt → nhiều pane cùng lúc, xem trả lời song song | P1 | Compare model |
| FR-105 | Session resume: đóng Hub mở lại vẫn tiếp tục được hội thoại CLI (map pane ↔ CLI session id) | P1 | Gemini có thể fallback nối-lịch-sử |
| FR-111 | **Skill index đa nguồn**: quét `~/.claude/skills`, `<project>/.claude/skills`, thư mục skill Codex; bảng hợp nhất: tên, mô tả, nguồn, CLI coverage | P0 | Thuần đọc, ship nhanh nhất |
| FR-112 | Skill detail: render SKILL.md + list file đính kèm + telemetry (đếm lần dùng từ session logs — tái dùng behavior parser) | P0 | |
| FR-113 | Skill deploy/sync: copy skill giữa các CLI target; phát hiện drift (cùng tên khác nội dung) + nút đồng bộ | P1 | User sửa trực tiếp OK (user là chủ); agent sửa vẫn phải qua git-job |
| FR-114 | Skill edit trong UI (textarea + preview) với backup trước khi ghi | P2 | |
| FR-121 | **Agent profiles**: CRUD qua form → lưu `agents/*.agent.yaml` (provider, system prompt, skills, permission, budget) | P1 | Schema theo ARCHITECTURE.md §9 |
| FR-122 | Workflow chạy headless: `workflow.yaml` tuần tự/rẽ nhánh đơn giản; node = agent profile; executor = CLI Provider Layer; HITL gate tái dùng runtime_interrupts | P1 | Track B đúng nghĩa — agent chạy TRONG runtime của Hub |
| FR-123 | Workflow run view: stream tiến trình từng node, artifact blackboard, nút approve/reject tại gate | P1 | Tái dùng UI pattern gitjobs stream |
| FR-124 | Canvas kéo-thả: SVG thuần; node = agent, edge = handoff; Save = generate/patch YAML + validate + show diff | P2 | CHỈ sau khi FR-122 chạy ổn. Canvas là editor, không phải nguồn chân lý |
| FR-131 | Cài đặt provider: trang Settings hiển thị CLI nào có mặt/version/login status; hướng dẫn cài Gemini CLI | P1 | Health check per provider |
| FR-132 | **Cockpit dashboard**: đếm token/call theo provider (hôm nay + 7 ngày) hiển thị style cockpit (gauge/counter/LED status) trên Dashboard; gộp chat_usage vào rollup chung (vá gap v1) | P0 | Bổ sung khi approve |
| FR-133 | Chat UI: **tái dùng** component chat v1 (model picker, markdown renderer, export, stop/regenerate) — đa cửa sổ = nhân bản pane, không viết chat UI mới | P0 | Constraint khi approve |

## 4. Non-Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-101 | Không API key bắt buộc; mọi model call qua CLI subscription hoặc NVIDIA free key hiện có | P0 |
| NFR-102 | Giữ stack v1: FastAPI + vanilla JS, không CDN, không build step; file là chân lý, không DB | P0 |
| NFR-103 | Chat first-token < 8s (chấp nhận cold-start CLI); skill index < 1s | P1 |
| NFR-104 | Mọi spawn process có timeout + kill; không zombie process khi đóng Hub (fix luôn orphan-stream của v1) | P0 |
| NFR-105 | Quota guard: đếm lượt gọi CLI/ngày hiển thị trên topbar; cảnh báo khi vượt ngưỡng tự đặt | P1 |
| NFR-106 | Vá CSRF của v1 (Origin check / token) TRƯỚC khi thêm khả năng spawn CLI từ UI | P0 |

## 5. Explicit Exclusions

- **Không** reverse-engineer app desktop/web của ChatGPT/Gemini/Claude — chỉ dùng CLI chính chủ (đúng ToS).
- **Không** multi-user / expose internet / deploy cloud.
- **Không** LangGraph hay framework orchestration ở phase này — runtime_pipeline tự có đủ cho workflow tuần tự + gate (đúng nguyên tắc §9: framework nếu có chỉ là executor adapter, thêm sau).
- **Không** viết canvas trước khi workflow chạy được bằng YAML + test.
- **Không** để agent tự sửa skill — mọi mutation từ agent đi qua git-job review (nguyên tắc v1 giữ nguyên).
- **Không** thay thế terminal — Hub bổ sung; CLI vẫn dùng trực tiếp được như cũ.

## 6. Open Questions — ĐÃ CHỐT 2026-07-14 (default all)

| # | Câu hỏi | Quyết định |
|---|---|---|
| Q1 | Cài Gemini CLI ngay hay để phase sau? | ✅ Phase sau — ship Claude+Codex+NVIDIA trước |
| Q2 | Chat Claude cho dùng tool đọc-file hay khoá sạch? | ✅ Khoá sạch ở MVP; toggle "cho đọc workspace" để sau |
| Q3 | Quota hard-limit hay chỉ đếm? | ✅ Chỉ hiển thị đếm + cảnh báo (NFR-105) |
| Q4 | Thư mục skill Codex? | ✅ ĐÃ VERIFY: `~/.codex/skills/` (4 skill đang có); Claude: `~/.claude/skills/` + `<project>/.claude/skills/` |
| Q5 | Workflow MVP rẽ nhánh? | ✅ Tuần tự + gate là đủ; rẽ nhánh để phase sau |

## 7. Phasing đề xuất

- **Phase A (P0):** NFR-106 vá CSRF → FR-101 CLI Provider Layer → FR-102/103 Chat multi-window (Claude, Codex, NVIDIA) → FR-111/112 Skill index + detail. *Mỗi bước ship được độc lập.*
- **Phase B (P1):** FR-104/105 broadcast + resume · FR-113 skill deploy/drift · FR-131 provider settings (+ cài Gemini) · FR-121 agent profiles.
- **Phase C (P1→P2):** FR-122/123 workflow headless + run view → FR-124 canvas (cuối cùng).

## 8. Routing (theo CLAUDE.md)

RD/SD/BD + review: Opus/Fable main session. Implement + test: giao Codex theo BD từng phase. Verify UI: Claude screenshot qua browser tools.

---

*Hub v2 — RD draft | 2026-07-14 | chờ APPROVE trước khi viết SD*
