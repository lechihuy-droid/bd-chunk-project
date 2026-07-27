# SD — UI v3 Rebuild ("đập đi xây lại")
**Date:** 2026-07-20 · **Status:** 🟢 U0–U3 shipped, U4 chưa làm (chi tiết §5.1) · **Author:** Claude (Fable 5)
**Quyết định gốc (user, 2026-07-20):** UI hiện tại không đáp ứng → rebuild toàn bộ frontend theo UI/UX của các harness tham chiếu **DeerFlow 2.0** và **OpenClaw Control UI**.
**Phạm vi:** CHỈ frontend. Backend FastAPI + toàn bộ `/api/*` + SSE contract giữ nguyên 100%.

---

## 1. Reference — lấy gì từ đâu

| Nguồn | Lấy | Bỏ |
|---|---|---|
| **DeerFlow 2.0** (Next.js, dark, chat-first) | Dual-column: hội thoại/timeline bên trái ↔ **Research/Artifact block** bên phải; stream tiến trình real-time vào timeline; artifact render markdown ngay cạnh | Next.js/SSR (không cần — localhost single-user), landing page |
| **OpenClaw Control UI** (Vite+Lit, gateway dashboard) | Sidebar agent-centric chia **zone** (Chat / Orchestrate / Govern / System); badge đếm việc chờ; workspace rail dockable; split-view chat panes; trang Approvals riêng; Usage với quota card | Multi-channel (WhatsApp/Telegram...), devices/nodes, terminal panel |

Điểm chung 2 reference: dark-first, chat/run là mặt tiền, mọi thứ khác là vệ tinh. UI v3 theo đúng triết lý đó — **run đang chạy là màn hình chính**, không phải dashboard số liệu.

## 2. Stack — supersede NFR-102

| | v1/v2 (cũ) | v3 (mới) |
|---|---|---|
| Frontend | Vanilla JS, no build, 1 file app.js 4.000 dòng | **Vite + React + Tailwind**, component tách file |
| Serve | FastAPI StaticFiles `web/` | FastAPI StaticFiles `web-v3/dist/` (build sẵn, commit dist) |
| Backend | FastAPI | **Không đổi** |

Lý do đổi: NFR-102 ("no build step") sinh ra app.js 4k dòng — chính là nguyên nhân UI không phát triển nổi thành control center như reference. Vite build 1 lần ra static dist, FastAPI serve như cũ — vẫn local-only, vẫn không cần server Node khi chạy. Codex là người build (user không đụng npm). Next.js bị loại: không cần SSR, thêm process thừa.

Legacy: `web/` cũ mount tại `/legacy` đến khi v3 đạt parity, sau đó xoá.

## 3. Design tokens

- **Nền:** `--ink #14161B` (slate đậm, không đen tuyệt đối) · panel `#1B1E25` · line `#2B303B`
- **Chữ:** text `#E8EAF0` · dim `#8B92A3` · Segoe UI Variable (native Win11) + Cascadia Code cho mono
- **Màu theo provider** (ngôn ngữ màu xuyên suốt — chip, dot, viền node):
  claude `#D97757` · codex `#A78BFA` · nvidia `#76B900` · gemini `#5B9CF5`
- **Gate/attention:** amber `#E4B15E` — chỉ dành cho việc chờ người quyết, không dùng trang trí
- **Signature element:** *run spine* — cột timeline dọc; node tròn = agent step, **gate = hình thoi amber**, node live có pulse (tôn trọng `prefers-reduced-motion`)

## 4. Page map — 12 trang cũ → 8 trang mới

| Sidebar zone | Trang v3 | Gộp từ v1/v2 | Nội dung chính |
|---|---|---|---|
| TRÒ CHUYỆN | Chat đa cửa sổ | #/chat | Split panes, provider picker, broadcast, read-only badge |
| | Phiên đã lưu | #/sessions, loops, entropy | Replay + behavior |
| ĐIỀU PHỐI | Workflows | (mới C2a) | List + YAML detail + nút Run; canvas về sau |
| | **Runs** ★ màn hình chính | #/runs + C3 run view | Spine trái (node stream, gate card inline Approve/Reject) + artifact rail phải (tab Artifact/Trạng thái/Sự kiện) |
| | Agents | C1 | CRUD profile, tab kiểu OpenClaw (Overview/Skills/Budget) |
| | Skills | #/skills B4 | Index + detail + drift/deploy |
| GIÁM SÁT | Chờ duyệt | gitjobs + interrupts | MỘT chỗ cho mọi thứ cần quyết: git-job, HITL gate |
| | Usage & quota | dashboard, usage, tools, suites, inspect | Quota chip per provider + rollup; suites/inspect thu thành section phụ |
| HỆ THỐNG | Cài đặt | settings B5 | Provider health, model catalog, config |

Topbar: breadcrumb + trạng thái run + **quota chips** (claude 42/100 · codex 18/50 · nvidia free) — luôn hiển thị, NFR-105 lên mặt tiền.

## 5. Phasing (orchestra model như BD Phase B §0)

| Phase | Nội dung | Executor | Gate |
|---|---|---|---|
| U0 | Scaffold Vite+React+Tailwind trong `harness/hub/web-v3/`; tokens + shell (sidebar/topbar); FastAPI mount dist; `/legacy` giữ UI cũ | [CODEX] | Shell chạy tại :8799, legacy còn nguyên |
| U1 | Chat đa cửa sổ (SSE contract cũ `reasoning\|delta\|done\|error`) + Sessions | [CODEX] | Chat 3 provider hoạt động thật |
| U2 | **Runs workspace** (spine + gate card + artifact rail) — cần D1 artifacts backend | [CODEX] | Chạy 1 workflow thật, approve gate từ UI mới |
| U3 | Workflows · Agents · Skills | [CODEX] | CRUD đủ vòng |
| U4 | Chờ duyệt · Usage · Cài đặt · cutover (xoá `/legacy`) | [CODEX] | Parity checklist + user OK |

Mỗi phase: Codex code → Sonnet test/review → Claude browser-verify bằng screenshot → commit.

**Ghép với Phase D (BD-hub-v2-phaseD.md):** D1 (artifact workspace) + D3 (routing alias) là backend cho U2 — làm trước hoặc song song U0–U1. D2 (validation) hiện lên spine dạng node check. D5 canvas lùi sau U4.

## 5.1. Trạng thái thật (cập nhật 2026-07-25)

- **U0–U3: shipped**, verify bằng browser + test thật trong phiên làm việc 2026-07-25.
- **U1 lệch khỏi spec gốc:** "Chat đa cửa sổ" đã build đúng spec ban đầu, sau đó **user yêu cầu đổi hướng** sang một hội thoại chính (single-active-chat) theo layout kiểu Claude/ChatGPT — multi-pane giờ chỉ còn là chế độ "So sánh model" phụ, không phải hình dạng mặc định. Xem commit `aee9a88`.
- **U2, U3: shipped**, CRUD Agents/Workflows/Skills đã verify round-trip thật qua browser + curl.
- **U3 đang được mở rộng thêm** ngoài phạm vi gốc: "Workflow Canvas v2" — design import riêng (claude.ai/design), giao Codex code phần canvas nặng (free-edge draw + Run/Log gộp vào trang + honest Contracts/Runs/Alerts). Lần chạy đầu chết giữa chừng vì OpenAI 503 outage, đang chờ retry.
- **U4: chưa làm** — Chờ duyệt/Usage/Cài đặt còn ở dạng cũ, `/legacy` vẫn sống, chưa cutover.

## 6. Không làm

- Không đổi backend/API/SSE contract — frontend mới nói chuyện với API cũ.
- Không SSR, không server Node lúc runtime, không SaaS/analytics/CDN lúc chạy (npm chỉ lúc build).
- Không port lại 12 trang 1:1 — trang không gộp được vào map trên thì bỏ.
- Không canvas trước khi Runs workspace ổn.

---

*Mockup đã render 2 màn hình chính: `mockups/ui-v3-mockup.html` — mở bằng Chrome xem trực tiếp. Chờ APPROVE trước khi viết brief U0 giao Codex.*
