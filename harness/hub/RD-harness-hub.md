# RD — Harness Hub (Cổng thông tin cho Opus Agent Harness)
**Date:** 2026-06-28
**Status:** 🟡 In Review
**Author:** Claude (Opus 4.8) — main session

---

## 0. Problem Statement

**Vấn đề:** Codex đã cài một local agent-harness (`ai-project-opus/harness/`) sinh ra nhiều artifact rời rạc — `runs/<ts>/summary.json`, `trace.jsonl`, `report.md`, `logs/`, Inspect `.eval` logs, MEP packet. Hiện **không có giao diện**: muốn xem kết quả phải mở từng file JSON/markdown thủ công, không thấy được trend, không so sánh được giữa các run, và **không có chỗ nào tổng hợp usage/cost của các model AI** (Opus / Sonnet / Haiku / Codex) tiêu tốn qua mỗi lệnh.

**Hiện trạng:** Harness chạy tốt qua CLI (`run_harness.py`, `ci-harness.ps1`, `run-inspect.ps1`) nhưng "đọc kết quả" là thao tác thủ công, rời rạc, không có lịch sử trực quan.

**Mục tiêu:** Một **web app FastAPI nhẹ** làm cổng thông tin (hub) duy nhất để: (1) xem trạng thái & lịch sử các run, (2) drill vào từng check/trace/log, (3) trigger chạy suite từ UI, (4) duyệt Inspect eval logs, và (5) **theo dõi usage/cost theo từng model AI qua mỗi lệnh**.

---

## 1. Usage — Người Dùng Dùng Thế Nào

> Viết TRƯỚC FR. Nếu không mô tả được usage cụ thể → requirements chưa đủ rõ.

### 1.1 User Profile

| Field | Giá trị |
|---|---|
| Người dùng | HUY (chủ workspace) — solo, tự vận hành harness |
| Device / môi trường | Windows 11, local `localhost`, mở bằng Chrome |
| Tần suất dùng | Mỗi khi chạy harness / kết thúc session / review tuần |
| Technical level | Cao — đọc được JSON/trace, hiểu cấu trúc harness |

### 1.2 Typical Usage Flow

```
Bước 1: User chạy `python harness\hub\server.py` (hoặc run-hub.ps1) → mở http://localhost:8799
Bước 2: Dashboard hiện status mới nhất mỗi suite (pass/fail), trend, tổng cost AI gần đây
Bước 3: User bấm vào 1 run → xem bảng checks, mở report.md render sẵn, xem trace/log
Bước 4: User bấm "Run suite" → hub gọi run_harness.py, stream tiến trình, refresh khi xong
Bước 5: User mở tab "AI Usage" → xem tokens/cost theo model, theo lệnh, theo ngày
Kết quả: Toàn bộ tình trạng harness + chi phí AI ở một màn hình, không phải mở file tay
```

### 1.3 Example Interactions

**Ví dụ 1 — Happy path (xem run):**
```
Input:  Mở /runs → click run "20260627-234104-workspace-smoke"
Output: Bảng 11 checks (pass/fail, duration, message, hint), link tới logs/*.txt,
        report.md đã render, nút "View trace.jsonl"
```

**Ví dụ 2 — Trigger run:**
```
Input:  /suites → chọn "boundary-compliance" → bấm "Run"
Output: Toast "Run started", panel stream stdout dòng-theo-dòng,
        khi exit → tự thêm run mới vào /runs với status
```

**Ví dụ 3 — AI usage (tính năng mới):**
```
Input:  /usage → filter model=claude-opus-4-8, range=7 ngày
Output: Bảng: timestamp · model · command/agent · input_tok · output_tok · cost_usd · source
        Biểu đồ cột cost theo model; tổng cost tuần
```

**Ví dụ 4 — Edge case (chưa có run nào):**
```
Input:  Mở dashboard khi runs/ rỗng
Output: Empty state "Chưa có run — chạy `python harness\run_harness.py --suite workspace-smoke`"
        (không crash)
```

---

## 2. Functional Requirements

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-001 | Dashboard hiển thị status mới nhất mỗi suite + pass/fail trend (N run gần nhất) | P0 | Đọc `runs/*/summary.json` |
| FR-002 | Trang Runs: list mọi run (id, suite, time, pass/fail), sort theo thời gian | P0 | |
| FR-003 | Run detail: bảng checks từ summary.json + render report.md + link logs | P0 | |
| FR-004 | Xem nội dung `trace.jsonl` và file trong `logs/` (stdout/stderr) | P0 | Read-only, trong boundary |
| FR-005 | Trang Suites: list suite + checks + hint (parse `suites/*.json`) | P0 | |
| FR-006 | Trigger chạy 1 suite từ UI → subprocess `run_harness.py`, stream output | P0 | Full control plane |
| FR-007 | Compare 2 run cùng suite: diff check nào đổi pass↔fail | P1 | |
| FR-008 | Trang Inspect Evals: list `.eval` logs + hiển thị MEP packet | P1 | Dùng inspect view/export_mep |
| FR-013 | _(đã bỏ — pricing/cost; thay bằng track tokens thật)_ | — | Giữ số để khỏi lệch đánh số |
| FR-009 | **AI Usage: thu thập & hiển thị số usage thật (tokens/calls) theo model, theo lệnh, theo ngày** | P0 | Token/đếm thật, KHÔNG quy ra tiền. Nguồn: §6 + Q1 |
| FR-010 | Usage detail: bảng event (time, model, command/agent, input_tok, output_tok, total_tok, source) + filter | P0 | |
| FR-011 | Usage rollup: tổng tokens & số call theo model & theo ngày + biểu đồ | P1 | |
| FR-012 | Auto-refresh / nút refresh để thấy run mới mà không restart server | P1 | |
| FR-014 | **Task Board (Hermes-style):** panel mục tiêu/sub-system/owner từ `opus-animus/ai/status.md` + handoff | P1 | Read-only replay, không phải live orchestration |
| FR-015 | **Session Replay 3-pane:** chọn 1 session Claude/Codex → Outline (plan/todos) · Agent (assistant text + tool args) · Monitor (tool_result/env) | P1 | Replay từ log jsonl, KHÔNG live |
| FR-016 | **Step-budget bar:** cho run do hub trigger — progress checks done/total so với `step_cap`, cảnh báo khi gần cap | P1 | Cap trong `hub/config.py`. Token-budget HOÃN: mọi suite hiện tại tất định, không gọi LLM → chỉ kích hoạt phần token khi có suite gọi model |

**Priority:** P0 = blocker · P1 = important, có workaround · P2 = nice-to-have

---

## 3. Non-Functional Requirements

| ID | Requirement | Metric | Priority |
|---|---|---|---|
| NFR-001 | Performance | Trang load < 1s với ≤ 500 run (đọc filesystem, không DB) | P0 |
| NFR-002 | Reliability | File hỏng/thiếu → skip gracefully, không crash server | P0 |
| NFR-003 | Boundary | Mọi đọc file giới hạn trong `{root}` — tái dùng policy của harness | P0 |
| NFR-004 | Lightweight | Không service nền, không DB ngoài; chạy bằng `.ih` venv có sẵn | P0 |
| NFR-005 | Local-only | Bind `127.0.0.1`, không expose ra mạng | P0 |
| NFR-006 | Cost của hub | Hub **không** tự gọi LLM nào (chỉ đọc/tính) → cost = 0 | P0 |

---

## 4. Explicit Exclusions

- **Không** dùng database (SQLite/Postgres) cho MVP — đọc trực tiếp filesystem; chỉ thêm SQLite nếu usage event vượt ~10k dòng (để sau).
- **Không** auth / multi-user — local-only, một người dùng.
- **Không** expose ra internet / không deploy cloud.
- **Không** chỉnh sửa nội dung suite trong UI ở MVP (chỉ xem) — edit suite để phase sau.
- **Không** tự ý gọi model AI để "phân tích" run — hub thuần đọc & tổng hợp.
- **Không** thay thế CLI — hub bổ sung, `run_harness.py` vẫn là nguồn chân lý.
- **Không** làm Governance lớp G trên Claude Code/Codex: KHÔNG có HITL gate chặn từng tool-call, KHÔNG hot-swap quyền, KHÔNG rollback checkpoint — vì các agent đó chạy ngoài runtime của hub, chỉ quan sát được qua log. (Lớp G thật cần orchestrator riêng = "Track B / Opus Runtime", RD khác.)
- **Không** dùng SaaS observability (Helicone/Langfuse/Opik) hay OTel/LangGraph — trái triết lý local-only, no-key, lightweight.
- Session Replay (FR-015) là **replay từ log đã ghi**, KHÔNG phải stream live của session bạn đang gõ ở terminal khác (hub không hook được vào đó). Live stream chỉ có cho run **do hub trigger**.

---

## 5. Open Questions

| # | Câu hỏi | Default nếu không confirm |
|---|---|---|
| Q1 | **Nguồn dữ liệu usage AI lấy từ đâu?** (a) parse Inspect `.eval` logs, (b) log Claude Code dưới `~/.claude/projects/...`, (c) Codex exec logs, (d) wrapper tự ghi `usage.jsonl` khi gọi model | Bắt đầu với (a) Inspect `.eval` (đã có token usage chuẩn) + (d) một `usage.jsonl` schema chung để các nguồn khác append dần |
| Q2 | ~~Giá model để tính cost~~ | **CHỐT: bỏ cost/USD.** Chỉ track số usage thật (input/output/total tokens, số call) của Claude & Codex. Không cần `pricing.json` |
| Q3 | Port cố định? | `8799` (tránh đụng homepage 8765) |
| Q4 | Trigger run có cho chọn `--check` đơn lẻ không? | Có — MVP cho chạy full suite + optional single check |
| Q5 | Hub nằm trong repo `ai-project-opus` hay tách riêng? | Trong `ai-project-opus/harness/hub/` (đi cùng harness) |

---

## 6. Design Decisions

| Quyết định | Lý do | Đã cân nhắc thay thế |
|---|---|---|
| FastAPI + uvicorn từ `.ih` venv | Đã cài sẵn, không thêm dependency; async stream được output khi trigger run | Flask: ít sẵn hơn; Node: thêm toolchain mới |
| Frontend = SPA tĩnh dùng `html-kit/styles.css` | Đồng bộ look McKinsey-style của workspace, tiết kiệm token, không cần build step | React/Vite: overkill cho 1 người + scope này |
| Đọc filesystem trực tiếp, không DB | Harness "lightweight, file là chân lý"; ≤ vài trăm run đọc đủ nhanh | SQLite: thêm phức tạp, chưa cần ở scale này |
| Usage = `usage.jsonl` (event log) + parser cho Inspect `.eval` + Claude Code session logs | Một schema thống nhất, mọi nguồn (Inspect/Codex/Claude) chỉ cần append; tách parser khỏi UI | Nhồi usage vào trace.jsonl: trộn concern, khó tổng hợp |
| Chỉ track tokens/calls thật, KHÔNG quy ra USD | User chốt; tránh phải bảo trì bảng giá đổi liên tục, số token là sự thật khách quan | Tính cost: thêm pricing.json phải sửa tay mỗi lần đổi giá |
| Tái dùng boundary policy của `run_harness.py` | Không phát minh lại bảo mật path; nhất quán với harness | Tự viết check path: rủi ro sót |

---

## 7. Đề xuất phân phase (để lập BD sau khi RD duyệt)

- **Phase 1 (P0 read-only core):** server FastAPI + Dashboard + Runs list/detail + Suites view + xem trace/log. → Giá trị ngay, rủi ro thấp.
- **Phase 2 (P0 control + usage):** Trigger run (stream), AI Usage (Inspect parser + usage.jsonl + pricing.json + bảng/filter).
- **Phase 3 (P1):** Compare runs, Inspect evals + MEP view, usage rollup/biểu đồ, auto-refresh.

---

## 8. Routing (theo CLAUDE.md)

- RD/SD/BD + review: **Opus main session** (đang dùng).
- Implement + test: giao **Codex** (`codex exec`) — Claude viết BD/brief rồi giao, không tự code.
- Search/verify rộng: tách **Sonnet subagent**.

---

*Harness Hub — RD v1 | 2026-06-28*
