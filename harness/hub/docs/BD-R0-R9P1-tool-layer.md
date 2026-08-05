# BD — R0 (gỡ gemini) + R9 Phase 1 (lớp tool qua cờ CLI + audit)

Trạng thái: **Approved 2026-07-28** · Nguồn: [RD-hub-backend-v1.md](RD-hub-backend-v1.md) §R0, §R9
Phạm vi: backend `harness/hub` + phần frontend bắt buộc phải sửa theo.
Thi công: 2 lượt Codex tách rời — **Task A (R0)** xong và verify trước, rồi mới **Task B (R9-P1)**.

> **Task A: ĐÃ XONG 2026-07-28.** 231 test pass (1 fail là R15, bom hẹn giờ có sẵn, không liên quan), `tsc -b` pass, `vite build` pass, grep `gemini` trong source thực thi = 0. Server đang chạy cần restart mới phản ánh.
>
> **Task B đã mở rộng phạm vi** sau audit agent/skill/tool ngày 2026-07-28. Ngoài các mục 9-25 dưới đây, phải làm thêm — chi tiết trong RD §R10, §R14, §R15:
> - **R10** — thêm gate `risk_tier` vào `runtime_children.py::create_child_run` (hiện chỉ `workflow_exec.py:293-296` có; grep `risk_tier` trong `runtime_children.py` = 0 kết quả). Test cả hai đường spawn.
> - **R14** — thêm allowlist khoá vào `validate_agent_profile`; field ngoài danh sách phải báo lỗi thay vì im lặng ghi xuống YAML. **Đây là điều kiện cần của mục 23**: không có allowlist thì gõ sai `allowd_tools` sẽ tạo cảm giác đã đặt giới hạn trong khi không có gì áp dụng.
> - **R15** — sửa `tests/test_pricing.py::test_cockpit_quota_pct_and_zero_quota`: đang hardcode `ts: "2026-07-22T00:00:00Z"` rồi assert vào `stats["today"]`, fail từ 2026-07-23. Dùng ngày động.
>
> **Ràng buộc mới (RD §2b):** mục 23 chỉ được thêm `allowed_tools`/`allowed_paths` vào agent profile **cùng lượt** với mục 16-17 (nối vào call site). Không được thêm field trước rồi nối sau — đó chính là cách `agent.skills` trở thành field chết.

---

## 0. Hiện trạng đã kiểm chứng (đọc code, không suy đoán)

| Sự thật | Vị trí |
|---|---|
| `Provider.stream_chat` chỉ trả `reasoning \| delta \| done \| error` | `services/providers/base.py` — `ChatEvent` |
| Chữ ký: `stream_chat(messages, session_id=None, model=None, system_prompt=None)` | `base.py::Provider` |
| 3 call site duy nhất | `workflow_exec.py:104`, `workflow_exec.py:269`, `server.py:236` |
| claude CLI bị hardcode hạn chế | `claude_cli.py::_build_cmd` — `--permission-mode plan`, `--disallowed-tools Edit/Write/Bash` |
| codex CLI bị hardcode hạn chế | `codex_cli.py:34` — `options = ["-s", "read-only", "--skip-git-repo-check", "--json"]` |
| claude stream-json **có** phát `tool_use`, code **vứt bỏ** | `claude_cli.py::stream_chat` — nhánh `data_type == "assistant"` chỉ gọi `_text_from_assistant`, dòng `type:"user"` (tool_result) không có nhánh nào |
| Agent profile **không có** `allowed_tools`/`allowed_paths` | `runtime_agents.py::REQUIRED_FIELDS = ("id","provider","system_prompt","skills","permission","budget","risk_tier")` |
| `allowed_tools`/`allowed_paths` chỉ có ở payload run → run metadata | `runtime_pipeline.py:351` |
| Hai field đó **không được thực thi ở đâu cả** | grep toàn `services/` + `server.py`: chỉ xuất hiện ở `runtime_pipeline.py:351` và `runtime_children.py` |
| `_ensure_subset` bỏ qua kiểm tra khi parent rỗng | `runtime_children.py:16-21` — `if not parent: return` |
| gitjobs đã sinh `diff.patch` và có flow approve/accept | `gitjobs.py::_write_diff_patch` (dòng 293), route `/api/jobs/{id}/diff`, `/approve`, `/accept` |
| `agent["permission"]` (`read_only`\|`workspace_write`) hiện **không** ảnh hưởng cờ CLI nào | `_build_cmd` của cả 2 provider đều hardcode |

---

# TASK A — R0: gỡ provider gemini

Lý do: chủ dự án loại khỏi scope; CLI `gemini` cũng không có trên máy (`which gemini` → không tìm thấy), nên provider này hiện không dùng được.

## A1. Backend

1. Xoá file `services/providers/gemini_cli.py`.
2. `services/providers/__init__.py` — bỏ `gemini_cli` khỏi import và khỏi `registry`.
3. `config.py:372` — bỏ mục `"gemini": {"cmd": ["gemini"]}` khỏi `PROVIDERS`.
4. `services/usage.py:363-364` — bỏ nhánh `if model == "cli:gemini": return "gemini"`.
5. `tests/test_providers.py` — xoá import `gemini_cli`, xoá toàn bộ khối stub gemini (khoảng dòng 292-343: `fake_gemini_cli`, `test_gemini_status_parses_version`, `test_gemini_stream_chat_yields_delta_done_and_transcript`, `test_gemini_cli_nonzero_returncode_emits_error_without_usage`), và sửa dòng 417 thành `assert {item["id"] for item in statuses} == {"nvidia", "claude", "codex"}`.

## A2. Frontend `web-v3`

Danh sách provider trên UI đọc từ `/api/providers` nên tự cập nhật. Chỗ phải sửa tay là union type hardcode:

6. `src/lib/ui.tsx` — `ProviderDot`: bỏ `'gemini'` khỏi union và bỏ nhánh màu tương ứng.
7. `src/components/RunSpine.tsx`, `src/pages/ChatPage.tsx`, `src/pages/ArtifactsPage.tsx`, `src/pages/SettingsPage.tsx` — bỏ `'gemini'` khỏi mọi union `'claude' | 'codex' | 'nvidia' | 'gemini'` và mọi map/nhánh gemini.
8. `src/index.css` — bỏ token `--color-gemini` khỏi khối `@theme`.

## A3. Kiểm

- `python -m pytest tests -q` — pass, không còn test gemini.
- `curl -s http://127.0.0.1:8799/api/providers` — trả đúng 3 provider.
- `npx tsc -b` và `npx vite build` — pass.
- Grep `gemini` toàn repo `harness/hub` (trừ `__pycache__`, `dist/`, `node_modules/`, và trừ thư mục docs) → **0 kết quả**.

---

# TASK B — R9 Phase 1: kiểm soát tool qua cờ CLI + audit

Mục tiêu: `allowed_tools` / `allowed_paths` / `permission` hết là field trang trí, và harness **nhìn thấy** agent gọi tool gì.

Giới hạn phải giữ trung thực xuyên suốt: **việc chặn nằm ở CLI vendor, không phải harness.** Harness khai báo cờ và ghi nhật ký; harness không tự kiểm chứng được là CLI có tuân thủ hay không. Mọi text hiển thị cho người dùng phải nói đúng điều đó — không được viết như thể harness đang chặn.

## B1. Mở rộng contract `services/providers/base.py`

9. Thêm 2 giá trị cho `ChatEvent["type"]`: `"tool_call"` và `"tool_result"`. Thêm các key tuỳ chọn:
   - `tool_call`: `tool_name: str`, `tool_input: dict`, `tool_use_id: str`
   - `tool_result`: `tool_use_id: str`, `is_error: bool`, `text: str`
   Giữ nguyên các type cũ — **không** đổi shape của `delta`/`reasoning`/`done`/`error`, vì SSE và UI hiện đang phụ thuộc.

10. Thêm tham số **tuỳ chọn, có mặc định** vào `Provider.stream_chat`:
    ```python
    tool_policy: ToolPolicy | None = None
    ```
    với
    ```python
    class ToolPolicy(TypedDict, total=False):
        permission: str        # "read_only" | "workspace_write"
        allowed_tools: list[str]
        allowed_paths: list[str]
    ```
    Mặc định `None` = giữ nguyên hành vi hardcode hiện tại. Bắt buộc để không phá 3 call site cùng lúc.

## B2. `claude_cli.py`

11. `_build_cmd` nhận thêm `tool_policy`. Quy tắc dịch:
    - `tool_policy is None` → giữ y nguyên cờ hiện tại (`--permission-mode plan`, cấm `Edit`/`Write`/`Bash`).
    - `permission == "read_only"` → `--permission-mode plan` + `--disallowedTools Edit Write Bash` (như cũ).
    - `permission == "workspace_write"` → **không** tự nâng quyền. Vẫn cần `allowed_tools` khai báo tường minh mới cấp; không có `allowed_tools` thì rơi về read_only.
    - `allowed_tools` không rỗng → `--allowedTools <từng phần tử>`. Giữ nguyên chuỗi pattern người dùng nhập (ví dụ `Bash(git *)`), **không** tự parse/chuẩn hoá.
    - `allowed_paths` không rỗng → mỗi path một `--add-dir <path>`. Mỗi path phải qua `boundary.resolve_in_root` trước; path nào ném `PermissionError` thì **bỏ cả lượt gọi** và trả `{"type":"error"}` — không âm thầm bỏ path đó rồi chạy tiếp.

12. Parse event tool trong `stream_chat`. Trong nhánh `data_type == "assistant"`, ngoài text còn phải duyệt `data["message"]["content"]`; block nào có `type == "tool_use"` thì `yield {"type":"tool_call", "tool_name": block["name"], "tool_input": block.get("input") or {}, "tool_use_id": block.get("id") or ""}`. Thêm nhánh `data_type == "user"`: block `type == "tool_result"` → `yield {"type":"tool_result", ...}`.
    **Trước khi code, chạy thật một lệnh claude nhỏ có dùng tool và xem JSON thực tế** — dùng shape quan sát được, không dùng shape phỏng đoán. Nếu shape khác mô tả trên thì theo shape thật và ghi lại trong báo cáo.

## B3. `codex_cli.py`

13. `options` (dòng 34) đang hardcode `["-s", "read-only", ...]`. Cho nhận `tool_policy`:
    - `None` hoặc `permission == "read_only"` → `-s read-only` (như cũ).
    - `permission == "workspace_write"` **và** có `allowed_paths` → `-s workspace-write`. Không có `allowed_paths` thì giữ `read-only`.
    - `allowed_paths` → truyền qua `-c` theo đúng khoá config mà bản codex đang cài hỗ trợ. **Chạy `codex exec --help` và kiểm `~/.codex/config.toml` để lấy tên khoá thật**; nếu bản này không có khoá tương ứng thì **không bịa cờ** — ghi rõ trong báo cáo là codex chưa hỗ trợ giới hạn path theo danh sách, và chỉ áp `-s`.
14. Kiểm output `--json` của codex xem có event tool không. Có thì map sang `tool_call`/`tool_result`. Không có thì ghi rõ trong báo cáo, **không** giả lập.

## B4. `nvidia_api.py`

15. Nhận `tool_policy` nhưng không dùng được (API thuần, chưa có vòng lặp tool — đó là Phase 2). Xử lý **tường minh**: nếu `tool_policy` có `allowed_tools` không rỗng thì `yield {"type":"error", "message":"Provider nvidia chưa hỗ trợ tool — allowed_tools không áp dụng được"}` rồi dừng. Tuyệt đối **không** im lặng bỏ qua: im lặng bỏ qua chính là cái làm field thành trang trí.

## B5. Nối 3 call site

16. `services/workflow_exec.py:104` và `:269` — dựng `tool_policy` rồi truyền vào `stream_chat`:
    - `permission` lấy từ `agent["permission"]`.
    - `allowed_tools` / `allowed_paths` lấy từ metadata của run đang chạy (`runtime_state.read_run(run_id)["metadata"]`), là nơi `runtime_pipeline.py:351` đã ghi vào.
    - Không có thì truyền `tool_policy=None`.
17. `server.py:236` — chat có `agent` thì thêm `tool_policy` vào `stream_kwargs` với `permission` từ agent; `allowed_tools`/`allowed_paths` lấy từ payload nếu có.
18. Ở cả 3 chỗ, event `tool_call`/`tool_result` phải được phát tiếp ra ngoài:
    - `workflow_exec`: thêm event SSE mới `tool_call` / `tool_result` qua `_yield_event`, cùng cách các event hiện có.
    - `server.py` chat: thêm `_sse("tool_call", …)` / `_sse("tool_result", …)`.
    - Ghi vào event log của run để có audit trail.

## B6. Sửa `_ensure_subset`

19. `services/runtime_children.py:16-21`. Hiện tại:
    ```python
    if not parent:
        return
    ```
    Đổi ngữ nghĩa: parent scope rỗng = **cấm mở rộng**, tức child cũng phải rỗng. Nếu `not parent and child` → raise `ValueError` như nhánh mở rộng hiện có.
    Viết test cho đúng trường hợp này trước khi sửa.

## B7. Cổng diff cho `allowed_paths`

20. `services/gitjobs.py`: trước khi một job được accept/approve, đọc `diff.patch` (`_job_diff_path`), rút danh sách path bị chạm, đối chiếu với `allowed_paths` của job. Có path ngoài danh sách → chặn, trả lỗi nêu rõ path vi phạm.
    - `allowed_paths` rỗng/không có → giữ hành vi hiện tại (không chặn), nhưng ghi log.
    - So sánh path phải chuẩn hoá qua `boundary.resolve_in_root`, không so chuỗi thô.
    - Đây là chỗ **harness thật sự chặn được**, khác với cờ CLI. Nói đúng như vậy trong thông báo lỗi.

## B8. Frontend

21. `ChatPage.tsx` — hiển thị event `tool_call`/`tool_result` trong luồng tin nhắn: tên tool + input rút gọn, và trạng thái lỗi nếu `is_error`. Dùng token/`Chip` sẵn có, không thêm màu mới.
22. `AgentsPage.tsx` — tab `Settings`: thêm ô nhập `allowed_tools` và `allowed_paths` (mỗi dòng một mục). **Kèm dòng chú thích cố định**: `Giới hạn này được truyền xuống CLI của provider. Harness khai báo và ghi log, không tự kiểm chứng.`
23. Hai field này **chưa** thuộc agent profile (`REQUIRED_FIELDS` không có). Nên hoặc (a) thêm vào profile schema `runtime_agents.py` dưới dạng **tuỳ chọn** (không thêm vào `REQUIRED_FIELDS`, agent cũ không có vẫn hợp lệ), hoặc (b) chỉ nhận ở payload run. **Chọn (a)** — để cấu hình được một lần theo agent thay vì nhập lại mỗi run. Nhớ cập nhật `validate_agent_profile` để kiểm kiểu list-of-string, và **không** làm hỏng 4 agent yaml hiện có.

## B9. Test

24. `tests/` — thêm:
    - `_build_cmd` của claude sinh đúng cờ cho từng `tool_policy` (None / read_only / workspace_write có allowed_tools / có allowed_paths).
    - path ngoài root trong `allowed_paths` → lỗi, không sinh lệnh.
    - claude stream có `tool_use` → phát `tool_call` đúng.
    - `nvidia_api` nhận `allowed_tools` → phát `error`, không im lặng.
    - `_ensure_subset`: parent rỗng + child không rỗng → raise.
    - gitjobs: diff chạm path ngoài `allowed_paths` → bị chặn.
25. Toàn bộ test cũ phải vẫn pass: `python -m pytest tests -q`.

---

## Ràng buộc chung cho cả 2 task

- **Không** `git add`, **không** `git commit`. Để cây làm việc bẩn.
- **Không** thêm dependency mới.
- Giữ style code xung quanh.
- Không đụng `harness/hub/docs/harness_hub_backend_docs_v0_1/`.
- Không sửa `ChatPage.tsx`/`WorkflowsPage.tsx`/`ArtifactsPage.tsx` ngoài phần được nêu — các file này có thay đổi chưa commit từ đợt trước.
- Chỗ nào không làm được thì **báo rõ là không làm được**, không được thay bằng giả lập trông giống thật.

## Definition of done

1. `python -m pytest tests -q` pass.
2. `npx tsc -b` và `npx vite build` pass.
3. Grep `gemini` (Task A) → 0 kết quả ngoài docs.
4. Báo cáo theo từng số mục 1–25: xong / không xong + lý do.
5. Nêu rõ mục nào là **harness chặn thật** (B7) và mục nào là **uỷ quyền cho CLI vendor** (B2, B3).
