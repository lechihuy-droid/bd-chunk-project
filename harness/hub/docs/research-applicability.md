# Research Applicability — Deep-Research Report vs Harness Hub v2

**Nguồn:** `C:\Users\HUY\Downloads\deep-research-report (2).md` (283 dòng, kiến trúc chat đa model: hybrid CLI adapter + LLM gateway).
**Đối chiếu với:** ARCHITECTURE.md, RD/SD-hub-v2-command-center.md, BD-hub-v2-phaseC.md, `services/providers/*`, `config.py`, `web/workspace.js` — trạng thái tại 2026-07-17 (Phase A+B đã ship, Phase C đang build).
**Không sửa code** — tài liệu này chỉ đối chiếu và đề xuất.

---

## 1. Đã trùng khớp (report validate kiến trúc hiện tại)

Report đề xuất **hybrid: CLI adapter tự viết + gateway cho inference API**. Hub đã tự đi đến gần như đúng nửa "adapter" của kiến trúc này *trước khi đọc report* — vì user không có API key trả phí nên chỉ có nửa CLI, chưa cần nửa gateway. Cụ thể từng điểm report nêu mà Hub đã làm đúng:

| Report đề xuất | Hub đã có |
|---|---|
| CLI agent cần adapter riêng, không qua HTTP gateway (§ Antipattern, § Adapter cho Claude/Codex) | `services/providers/claude_cli.py`, `codex_cli.py` — spawn subprocess, `shell=False`, đúng pattern |
| Parse JSONL output → event chung | `_text_from_assistant` / `_text_from_line` chuẩn hoá về `ChatEvent {reasoning|delta|done|error}` — đúng "Unified Event Bus" report mô tả |
| Session resume (`claude --resume`, `codex exec resume`) | `claude_cli.py` dùng `-r <session_id>`; `codex_cli.py` dùng `exec ... resume <session_id>` (đã verify thứ tự tham số đúng clap grammar của codex 0.144.3) |
| Permission/sandbox cho CLI agent (§ An toàn) | `--permission-mode plan --disallowed-tools Edit/Write/Bash` (claude), `-s read-only` (codex) — khoá đúng theo FR-103 |
| Cancellation & Timeout, kill process khi shutdown (§ An toàn, § Kiến trúc MVP) | `services/providers/procs.py` — `ProcessRegistry`: timeout per-spawn, `kill_all()` cho lifespan shutdown, watcher thread |
| Max concurrent request cap | `MAX_CONCURRENT_CLI = 3` + `BusyError` → HTTP 429, đúng như report gợi ý |
| Health check per provider (§ Kiến trúc MVP) | `status()` mỗi provider, TTL cache 60s, dùng cho FR-131 Settings |
| Runtime Adapter Registry (§ Kiến trúc MVP) | `services/providers/__init__.py` — `get_provider()`/`list_providers()` |
| Model catalog tĩnh thay vì list-model động (report: "CLI không có lệnh liệt kê model") | `config.CHAT_MODEL_CATALOG` (21 model NVIDIA) — đúng hướng report khuyến nghị cho phần API |
| NVIDIA NIM tương thích OpenAI, dùng OpenAI SDK trỏ baseURL | `services/chat.py` dùng `OpenAI(base_url=NVIDIA_BASE_URL, ...)` — đúng pattern report mô tả |
| Gateway-first là antipattern khi cần CLI (report tự nói rõ) | Hub chưa từng thử gateway hoá CLI — validate quyết định đúng ngay từ RD |

**Kết luận phần 1:** kiến trúc adapter-first của Hub không lệch khỏi khuyến nghị report — report chỉ thêm phần gateway cho trường hợp Hub chưa cần (nhiều API provider trả phí).

---

## 2. Khoảng cách đáng giá (gap worth adopting) — xếp theo giá trị/công sức

### 2.1 Execution target `<runtime:model>` cho claude/codex — **giá trị cao, công sức thấp**
Report: model là alias (`sonnet`/`opus`/`haiku` cho Claude, `-m gpt-5` cho Codex) chọn được per-request. Hub hiện: `Provider.stream_chat(..., model=None)` nhận tham số `model` nhưng **claude_cli.py và codex_cli.py không hề dùng nó** — `_build_cmd()` không có flag model, luôn chạy model mặc định của CLI. Chỉ `nvidia_api.py` dùng `model`. Đây là gap thật: user điều phối theo CLAUDE.md ("Opus cho plan, Sonnet cho task thường") nhưng Hub chat pane không chọn được Opus/Sonnet — phải tự đổi ở terminal thật.
**Đáng làm ngay** vì effort nhỏ (thêm `--model <alias>` vào `_build_cmd` của claude_cli, `-m` cho codex_cli) và giá trị dùng hàng ngày cao.

### 2.2 Model registry file (YAML/JSON riêng) — **giá trị thấp, không cần tách file mới**
Report gợi ý registry tĩnh vì CLI không list được model — đúng, nhưng Hub **đã có** registry tĩnh (`config.CHAT_MODEL_CATALOG` trong `config.py`). Không cần externalize sang YAML: `config.py` chính là "file chân lý" theo triết lý RD (NFR-102). Việc cần làm không phải "thêm registry" mà là **mở rộng registry hiện có** để bao gồm alias của claude/codex (gắn liền với 2.1), không phải tạo format file mới.

### 2.3 Gateway (LiteLLM/Bifrost/AISIX) — **over-engineering ở thời điểm này, có ngưỡng bật lại rõ**
Report tự thừa nhận Kong/Envoy quá nặng cho MVP; đánh giá thẳng cho Hub: **kể cả Bifrost/AISIX (nhẹ nhất) cũng thừa** vì Hub hiện chỉ có **một** API provider thật (NVIDIA, free key) — routing/load-balance/caching giữa nhiều provider API là bài toán report giải, không phải bài toán Hub có. Gateway đáng cân nhắc **chỉ khi** cả 3 điều kiện sau xảy ra: (a) user có ≥2 API key trả phí (OpenAI/Anthropic Messages API) cần so sánh/route, (b) cần caching/retry chung nhiều provider, (c) traffic đủ lớn để lo về latency/consistency giữa nhiều SDK client. Hiện tại không điều nào đúng.

### 2.4 Context handoff khi đổi model giữa chừng — **giá trị trung bình, có sẵn giải pháp rẻ hơn**
Report đề xuất 3 chiến lược, chọn "gửi recent history + summary" cho MVP. Hub hiện **khoá cứng provider sau tin nhắn đầu** (`workspace.js:555` `providerLocked = Boolean(chat?.messages.length)`, tooltip "provider locked after first message"). Đây là thiết kế có chủ đích, không phải thiếu sót — và Hub **đã có** cơ chế khác giải quyết đúng nhu cầu "so sánh model" mà report nhắm tới: **broadcast mode** (1 prompt → N pane provider khác nhau cùng lúc, `sessionIds` per-provider). Đổi provider giữa chừng một cuộc hội thoại đơn *có* giá trị nhỏ (đỡ phải mở pane mới) nhưng không cấp thiết — xếp Phase D, effort M vì cần: UI cho phép mở khoá + logic seed lịch sử ngắn vào prompt đầu của runtime mới (không dùng full-history theo đúng cảnh báo antipattern của report — tốn token).

### 2.5 SQLite cho registry + chat history — **bác bỏ ở quy mô hiện tại, nhưng có một khoảng xám**
RD NFR-102 chốt triết lý "file là chân lý, không DB" — nhất quán với toàn bộ Hub v1 (append-only JSON/JSONL). Report đề xuất SQLite cho **multi-user MVP** (Phase 2 trong roadmap report) — Hub là **solo, local, single-user**, đúng điều kiện report tự liệt là "không cần" (§ Chống pattern: "Ứng dụng chỉ đơn giản, không cần chọn model/user... thì không cần gateway/DB phức tạp"). Khoảng xám duy nhất: chat history hiện chỉ sống trong `localStorage` (client-side, mất khi đổi máy/xoá cache) — nếu cần bền hơn, giải pháp rẻ hơn SQLite là ghi thêm JSONL append-only (đã có pattern `chat_usage.jsonl`) chứ không cần DB engine mới.

### 2.6 Event schema mở rộng (tool calls, file.changed, command.output) — **giá trị cao cho Phase C, chưa cần cho Chat**
Chat mode hiện đúng ý đồ chỉ có text (`reasoning|delta|done|error`) vì FR-103 khoá tool hoàn toàn ở chat — không cần event tool/file. Nhưng **Phase C** (BD-hub-v2-phaseC.md, agent profile có `permission: workspace_write`) sẽ có node LLM chạy CLI với quyền ghi, và `gate: approval` cần user xem **cái gì sẽ chạy** trước khi approve — event schema hiện tại (`assistant_delta, node_update, state_snapshot, done|error` theo BD C2b) chưa có `tool.started`/`command.output`/`file.changed` như report đề xuất. Đây là gap thật và đúng lúc — Phase C đang build executor (C2b/C3), nên mở rộng `ChatEvent`/event bus ngay trong bước này rẻ hơn nhiều so với thêm sau khi UI run-view đã cứng hình.

### 2.7 NIM `max_tokens` bug (Llama 3.1) — **đã xử lý, không còn thiếu gì**
Kiểm tra `services/chat.py:187-195`: mọi request gửi lên NIM **luôn** set `"max_tokens": max_tokens` (giá trị `config.CHAT_MAX_TOKENS = 16384`) không điều kiện theo model — tức bug report nêu (Llama 3.1 cần `max_tokens` bắt buộc) không thể xảy ra ở Hub vì tham số này không bao giờ bị bỏ qua. Không cần sửa gì; chỉ đáng thêm 1 test hồi quy đảm bảo refactor sau này không vô tình biến `max_tokens` thành optional.

---

## 3. Bác bỏ có lý do

| Report item | Lý do bác bỏ cho Hub |
|---|---|
| Gateway (LiteLLM/Bifrost/AISIX/Kong/Envoy/Cloudflare) | Chỉ 1 provider API thật (NVIDIA free) — không có bài toán multi-provider-routing để giải (xem 2.3) |
| PostgreSQL, multi-user auth, quota per-user | Hub explicit solo/localhost (RD §1.1, Explicit Exclusions "Không multi-user / expose internet") |
| Worker isolation qua BullMQ/Redis job queue | Không có concurrency đa-user; `ProcessRegistry` (max 3 concurrent, threading.Lock) đã đủ cho 1 user |
| Load balancer, nhiều instance service | Localhost single process — không có traffic để cân bằng |
| Prometheus/Grafana, ElasticSearch tracing | Overkill cho 1 user; usage/behavior cache JSON hiện tại đủ quan sát |
| Vault/AWS Secrets Manager | 1 API key (NVIDIA) qua env var đã là baseline bảo mật report tự đề xuất cho MVP ("không cần vault cao cấp") |
| Docker/cgroup sandbox cho CLI subprocess | User tin cậy chính mình trên máy mình, không multi-tenant; `shell=False` + timeout + kill_all là đủ tầng phòng vệ hiện tại |
| Full-history replay khi đổi model | Report tự gọi đây là chống pattern (tốn token, trả lời trùng lặp) — nếu làm 2.4, chọn "recent + summary", không phải full |
| LangGraph / framework orchestration cho workflow | ARCHITECTURE.md §9 đã tự chốt: framework nếu dùng chỉ là executor adapter thêm sau, YAML là chân lý — đúng tinh thần "config-first" mà report cũng ngầm đồng ý khi nói CLI/gateway không nên là nguồn chân lý |
| Rate-limit 429 kiểu API gateway (theo request/user) | Đã có tương đương đúng quy mô: `MAX_CONCURRENT_CLI` cap → 429 "busy", không cần policy engine riêng |

---

## 4. Đề xuất hành động (tối đa 5)

| # | Việc | Effort | Phase | File đụng tới |
|---|---|---|---|---|
| 1 | Thêm alias model cho claude/codex vào execution target: `--model <alias>` (claude), `-m <alias>` (codex); mở rộng `PROVIDERS` trong `config.py` với danh sách alias hợp lệ mỗi CLI; provider picker Chat UI hiện dropdown model khi provider là claude/codex (hiện chỉ nvidia có) | S | C (hiện tại) | `services/providers/claude_cli.py` (`_build_cmd`), `services/providers/codex_cli.py` (`_build_cmd`), `config.py` (`PROVIDERS`), `web/workspace.js` (model picker cho CLI provider) |
| 2 | Mở rộng `ChatEvent`/event bus thêm `tool.started`/`command.output`/`file.changed` cho node executor Phase C (chỉ khi `agent.permission == workspace_write`), phục vụ HITL gate review trước approve | M | C (C2b/C3 đang build) | `services/providers/base.py` (`ChatEvent` type), `services/runtime_pipeline.py` / `services/workflow_exec.py` (mới), `web/workspace.js` (run-view render event mới) |
| 3 | Thêm test hồi quy khẳng định `max_tokens` luôn có mặt trong mọi request NVIDIA (chống regression về bug NIM/Llama 3.1 report nêu) | S | C (hiện tại) | `harness/hub/tests/test_chat.py` (test mới hoặc bổ sung case) |
| 4 | Cho phép đổi provider giữa chừng 1 conversation (mở khoá `providerLocked`), seed runtime mới bằng N tin nhắn gần nhất thay vì full history — chỉ làm sau khi nhu cầu thực tế xuất hiện (broadcast mode đang thay thế tốt) | M | D (tương lai) | `web/workspace.js` (`providerLocked` logic), `services/providers/*` (nhận `seed_messages` khi tạo session mới) |
| 5 | Health/Settings page hiển thị rõ `capabilities.models` (alias khả dụng) mỗi CLI provider — tận dụng `status()` TTL-cache đã có, khớp FR-131 chưa làm | S | C→D | `server.py` (route `/api/providers` đã có, chỉ cần trả thêm field), `web/workspace.js` hoặc trang Settings mới |

**Verdict gateway (1 câu):** Với Hub hiện tại — solo, local, chỉ một provider API thật (NVIDIA free), không API key trả phí — thêm gateway (kể cả Bifrost/AISIX nhẹ nhất) là over-engineering; chỉ cân nhắc lại khi có ≥2 API provider trả phí cần routing/caching chung.
