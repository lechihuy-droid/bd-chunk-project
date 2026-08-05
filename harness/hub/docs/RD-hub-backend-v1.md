# RD — Harness Hub backend v1

Trạng thái: **APPROVED 2026-07-28** — đây là doc chính của version này.
Ngày: 2026-07-28
Phạm vi: backend cần có để UI web-v3 (sau đợt apply wireframe) hết phải hiển thị `TODO(backend)`.

Bộ tài liệu version này gồm 3 file, đọc theo thứ tự:

| File | Vai trò |
|---|---|
| **`RD-hub-backend-v1.md`** (file này) | Doc chính — yêu cầu, quyết định, thứ tự thi công, trạng thái |
| [`SPEC-agent-skill-tool.md`](SPEC-agent-skill-tool.md) | Hợp đồng chi tiết cho `agent` / `skill` / `tool` + bảng enforcement từng field |
| [`BD-R0-R9P1-tool-layer.md`](BD-R0-R9P1-tool-layer.md) | Kế hoạch thi công cho R0 + R9 Phase 1 |

Khi 3 file mâu thuẫn: **RD thắng về phạm vi và thứ tự, SPEC thắng về schema/hành vi, BD thắng về từng bước code.**

Tài liệu này **không** thay `harness/hub/docs/harness_hub_backend_docs_v0_1/`. Quan hệ:
- Bộ `harness_hub_backend_docs_v0_1/` tầng `00_INDEX` + `02_REQUIREMENTS_BASELINE` + `04_IMPLEMENTATION_STATUS` là bản audit **chính xác** hiện trạng — dùng làm backlog.
- Tầng `basic-design/BD01-08` + `design/D01-08` mô tả hệ thống lớn hơn nhiều (Gateway/Executor Port, transaction journal, artifact manifest SHA-256, Windows sandbox có Job Object, MCP). Tự đánh dấu `In Review`, còn quyết định chủ dự án chưa chốt. **Ngoài phạm vi RD này.**
- `reference/legacy-v0.1/` giả định PostgreSQL + Redis + object storage + multi-tenant. Hub thật là 1 process FastAPI + file/JSONL. **Không dùng.**
- Bộ docs đó **không** có Hooks, Files, workspace, quota. Ba mục đó chỉ có trong RD này.

---

## 1. Hiện trạng đã kiểm chứng

Đọc code + gọi API thật lúc viết:

| Sự thật | Bằng chứng |
|---|---|
| Workflow bắt buộc là chuỗi tuyến tính đơn | `services/workflow.py` `_walk_chain` — in/out degree ≤ 1, 1 start 1 end |
| Cạnh workflow bắt buộc là tuple 2 phần tử `[from, to]` | `services/workflow.py::validate_workflow` |
| Node chỉ có `agent` \| `validate` | `services/workflow.py` |
| `provider` của agent có thể là id thật hoặc alias lớp model | `services/runtime_agents.py::resolve_provider`; `/api/model-classes` trả `cheap→nvidia, code→codex, smart→claude` |
| Artifact **có** lưu server-side, nhưng chỉ theo run của workflow, đặt tên theo node, không có version | `services/runtime_artifacts.py::write_node_artifact` → `run/<id>/artifacts/<node>.md` |
| Artifact sinh từ **chat** không được lưu server | ChatPage/ArtifactsPage đọc `localStorage['hub-v3-chats']` |
| Không có API hooks / files / workspace / quota | không có route nào trong `server.py` |
| `/api/runs` là log **self-test suite** của harness, khác `/api/agent/runs` (run thật) | curl cả hai; `src/lib/runsApi.ts` dùng `/api/agent/runs` |

### Đính chính về `allowed_paths` / `allowed_tools`

Bộ docs v0_1 nêu `REQ-GOV-02` "child scope rỗng có thể vượt lên unrestricted". Tôi đã đọc code và **kết luận khác**, nhẹ hơn về mức khai thác nhưng nặng hơn về thiết kế:

- `services/runtime_children.py::_ensure_subset` có `if not parent: return` — đúng là bỏ qua kiểm tra khi parent không khai báo scope.
- Nhưng `allowed_paths` / `allowed_tools` **chưa được thực thi ở bất kỳ đâu**. Grep toàn bộ `services/` + `server.py`: hai field này chỉ được copy vào metadata (`runtime_pipeline.py:351`) rồi so sánh subset trong `runtime_children.py`. Không có cổng filesystem hay tool nào đọc chúng.

→ Nên **không phải** lỗ đặc quyền đang bị khai thác được (không có đặc quyền nào để leo). Là **field trang trí**: UI/API nhận vào, lưu lại, không chặn gì. Đây là rủi ro thật vì tạo cảm giác an toàn giả. Xếp P0 về mặt thiết kế, không phải P0 khẩn cấp.

---

## 2. Yêu cầu

Ký hiệu: `[M]` bắt buộc v1, `[S]` nên có, `[C]` có thể hoãn.

### R1 — Hooks API `[M]`

UI `HooksPage.tsx` đã dựng khung, 0 dòng, control disabled.

- `GET /api/hooks` → danh sách hook: `id`, `name`, `event`, `trigger_point`, `enabled`, `executed_count`, `last_run_at`, `last_status`.
- `POST /api/hooks`, `PUT /api/hooks/{id}`, `DELETE /api/hooks/{id}`.
- `GET /api/hooks/events` → catalog event hợp lệ. **Phải lấy từ tập event SSE thật đang phát** (`services/runtime_events.py`), không tự nghĩ ra danh sách: `node_update`, `validation_fail`, `validation_pass`, `artifact_written`, `child_run`, `interrupt`, `done`, `error`.
- `GET /api/hooks/{id}/log` → lịch sử thực thi.
- Hành động hook v1: `webhook POST`, `ghi file log`, **và chạy shell command** (chủ dự án quyết 2026-07-28).
- Ràng buộc bắt buộc kèm theo: hook chạy shell **phải đi qua đúng đường gitjobs** — git worktree riêng + `shell=False` + lệnh cố định + cổng diff, giống `gitjobs.py::_spawn_agent`. **Không** spawn thẳng subprocess từ hook: đó sẽ là bề mặt thực thi mới không có lớp cách ly nào.
- **Phụ thuộc thứ tự:** hook chạy shell chỉ được bật **sau khi R9 Phase 1 xong**. Trước đó không có gì chặn tool/path, hook shell thành đường chạy code tuỳ ý.

Câu hỏi mở: hook chạy đồng bộ chặn run hay bắn nền? Đề xuất: **bắn nền, không chặn**, thất bại chỉ ghi log.

### R2 — Files API `[M]`

UI `FilesPage.tsx` đã dựng khung.

- `GET /api/files` → `name`, `type`, `size`, `updated_at`.
- `POST /api/files` (upload), `GET /api/files/{name}` (tải), `DELETE /api/files/{name}`.
- **Bắt buộc** đi qua `services/boundary.py::resolve_in_root` như `runtime_artifacts.py` đang làm — chống path traversal. Không tự viết logic chặn đường dẫn mới.
- Cần giới hạn dung lượng file + tổng thư mục, đặt trong `config.py`.

Lưu trữ: **theo từng run** (chủ dự án quyết 2026-07-28) — `runtime/run/<run_id>/files/`, cùng cây với `artifacts/` hiện có.

Hệ quả cho UI: trang Files hiện đặt ở cấp app và **không có chỗ chọn run**. Phải bổ sung bộ chọn run trên `FilesPage.tsx`, nếu không trang đó không biết đọc file của run nào.

### R3 — Skill CRUD `[M]`

Hiện chỉ đọc + deploy. Nút "New skill" trên UI đang chết.

- `POST /api/skill-library`, `PUT /api/skill-library/{id}`, `DELETE /api/skill-library/{id}`.
- Giữ nguyên cơ chế drift/deploy hiện có; skill mới ghi vào đúng `source` mà người dùng chọn.

### R4 — Artifact store cho chat `[S]`

Hiện artifact từ chat **chỉ nằm trong localStorage trình duyệt** — mất khi xoá cache, không chia sẻ được giữa máy.

- Mở rộng `runtime_artifacts.py` để nhận artifact không gắn với workflow run.
- `GET /api/artifacts`, `GET /api/artifacts/{id}`, `POST /api/artifacts`.
- Version: `v1, v2, …` cùng `created_at` và nguồn (`chat` \| `workflow_run`). UI đã có ô "Versions" và nút "v1 · hiện tại" đang là placeholder.
- **Quan hệ với localStorage (chốt 2026-07-28): server là nguồn thật, `localStorage['hub-v3-chats']` chỉ còn là cache.** UI đọc từ server; localStorage giữ bản tạm để còn dùng khi backend chưa chạy, và bị ghi đè khi server trả dữ liệu. Kéo theo phải sửa `ChatPage.tsx`, `ArtifactsPage.tsx` và mục `RECENT` trong `Sidebar.tsx` — cả ba hiện đọc thẳng localStorage.
- Nhờ đó các field đang là `—` trên ArtifactsPage (Workflow name, Run ID, Bắt đầu lúc, Hoàn thành lúc, Thời gian chạy) mới có nguồn.

### R5 — Run theo agent `[S]`

Tab `Activity` trong panel agent đang trống.

- `GET /api/agents/{id}/runs` — lọc `/api/agent/runs` theo agent.
- Hoặc thêm query param `?agent_id=` vào `/api/agent/runs`. Đề xuất cách 2, ít route hơn.

### R6 — Chạy thử agent `[S]`

Nút "Run test" đang là stub.

- `POST /api/agents/{id}/test` — gọi agent 1 lượt với prompt ngắn, trả kết quả + thời gian + token. Dùng lại `runtime_agents.resolve_provider`.
- Phải chịu `budget` của chính agent đó.

### R7 — Tìm kiếm toàn cục `[C]`

Ô search trên Topbar chưa nối.

- `GET /api/search?q=` gộp workflow + agent + skill + artifact. Ưu tiên thấp — mỗi trang đã có search riêng hoạt động.

### R8 — Field `kind`/`label` cho cạnh workflow `[S]`

Đã được duyệt hướng ở phiên trước, chưa làm.

- `services/workflow.py`: cho phép cạnh là `[from, to]` (như cũ) **hoặc** `{from, to, kind?, label?}`.
- `_walk_chain` / `build_ir` bỏ qua `kind`/`label` — chỉ để hiển thị, không đổi ngữ nghĩa thực thi.
- Bắt buộc tương thích ngược: 3 file `workflows/*.yaml` hiện có phải load được không sửa.

### R9 — Lớp tool cho harness `[M]`

**Quyết định chủ dự án (2026-07-28): thực thi thật, không gỡ. Làm trước các mục khác. Ghi cả hai phase.**

Yêu cầu gốc của chủ dự án: *"tôi cần lớp tool cho harness, không để các CLI tự chọn."*

#### Hiện trạng đã kiểm chứng

`Provider.stream_chat` (`services/providers/base.py`) chỉ trả `reasoning | delta | done | error`. **Không có event tool nào** — harness hoàn toàn mù về việc CLI gọi tool gì.

Nhưng CLI **có** cho phép hạn chế, và chi tiết hơn code đang dùng:

| Provider | Cờ có sẵn | Code hiện dùng |
|---|---|---|
| `claude_cli` | `--allowedTools`/`--disallowedTools` nhận pattern (`"Bash(git *)"`), `--add-dir` (allowlist thư mục), `--settings`, `--permission-mode` | cứng: `--permission-mode plan` + cấm `Edit`/`Write`/`Bash` |
| `codex_cli` | `-s/--sandbox`, `-c 'sandbox_permissions=[…]'`, `--profile` | cứng: `-s read-only` |
| `nvidia_api` | API thuần — cờ CLI không áp dụng | không có khái niệm tool |

Thêm: `claude -p --output-format stream-json` **có phát** block `tool_use` và dòng `type:"user"` (tool_result). `claude_cli.py::stream_chat` chỉ rút text qua `_text_from_assistant` rồi **vứt bỏ** phần còn lại. Harness đang nhận dữ liệu tool rồi ném đi.

#### Phase 1 — kiểm soát qua cờ CLI + audit `[M]`

Rẻ, không đổi kiến trúc. Sau phase này `allowed_tools`/`allowed_paths` hết là field trang trí.

1. Đọc `allowed_tools` / `allowed_paths` của agent, dịch sang cờ:
   - claude: `--allowedTools <pattern…>`, `--add-dir <path…>`
   - codex: `-s` + `-c sandbox_permissions=[…]`
   - gemini: không còn — xem R0, provider bị gỡ hẳn
2. Ngừng vứt event tool. Thêm `tool_call` / `tool_result` vào `ChatEvent` trong `base.py`, parse block `tool_use` trong `claude_cli.py`, ghi log, phát lên SSE để UI hiển thị.
3. Sửa `_ensure_subset` (`runtime_children.py:17`): parent scope rỗng nghĩa là **cấm mở rộng**, không phải bỏ qua kiểm tra.
4. `allowed_paths` kiểm ở cổng diff của gitjobs: job không được accept nếu `diff.patch` chạm path ngoài danh sách. Dùng lại `_write_diff_patch` (dòng 293) + flow `/api/jobs/{id}/diff` → `/approve` → `/accept` đã có.

Giới hạn phải ghi rõ trên UI: **chặn nằm ở CLI vendor, không phải harness**. Harness chỉ khai báo và ghi nhật ký, không tự kiểm chứng được.

#### Phase 2 — harness sở hữu vòng lặp tool `[S]`

Chỉ đây mới là "không để CLI tự chọn" theo đúng nghĩa.

```
harness gửi messages + tools=[schema]
  → model trả tool_call
  → HARNESS thực thi  ← cổng chặn thật: allowed_tools + allowed_paths
  → gửi tool_result về
  → lặp
```

Việc phải làm:
1. **Tool registry** — schema từng tool (`read_file`, `write_file`, `grep`, `run_command`…)
2. **Dispatcher** — thực thi tool; đây là điểm chặn thật, path đi qua `boundary.resolve_in_root`
3. Mở rộng contract `base.py`: nhận `tool_result` làm đầu vào, không chỉ phát `tool_call`
4. Chuyển vòng lặp từ trong CLI ra runtime

Áp dụng được cho provider **API** (`nvidia_api` ngay được; Claude/OpenAI cần chuyển từ CLI sang API). Provider CLI agentic không dùng được đường này — vòng lặp nằm bên trong nó.

**Khởi động (chốt 2026-07-28): `nvidia_api` + 2-3 tool chỉ-đọc** (`read_file`, `grep`, `list_dir`) — không tool nào ghi file. Chứng minh vòng lặp chạy trước, rồi mới mở rộng sang tool ghi và sang provider khác.

Quy mô: Phase 1 nhỏ–vừa, Phase 2 lớn.

Lưu ý quan hệ với `BD04` (Gateway/Executor Port): **BD04 không giải quyết việc này.** BD04 chuẩn hoá lời gọi provider, và tự ghi rõ request *"does not carry an untrusted executable command"*, tool có quyền/ghi/mạng *"stay denied pending BD07 gates"*. Xây BD04 để có `allowed_tools` là đi nhầm cửa.

### R10 — Gate `risk_tier` thiếu ở đường spawn thứ hai `[M]`

Phát hiện từ audit 2026-07-28, đã tự kiểm chứng bằng grep.

`workflow_exec.py:293-296` có gate: lấy `spawn_agent["risk_tier"]`, đối chiếu `governance.effective_blocked_tiers()`, chặn + `record_denial` nếu bị block.

`runtime_children.py::create_child_run` (đường spawn còn lại) **không có gate này** — grep `risk_tier` trong file đó ra 0 kết quả. Nó chỉ kiểm `agent_id != "lead"`, giới hạn số child, và subset path/tool.

→ Cùng một agent bị governance chặn ở đường workflow vẫn spawn được qua đường child-run. Đây là lỗ thật, rẻ để vá.

Việc: thêm đúng gate đó vào `create_child_run`, dùng lại `governance.effective_blocked_tiers()` + `record_denial`. Viết test cho cả hai đường.

### R11 — `agent.skills` đang là field chết `[M]`

Xem [`SPEC-agent-skill-tool.md`](SPEC-agent-skill-tool.md) §2.2. Tóm tắt: `agent.skills` được validate chặt (`runtime_agents.py:41-48`, mỗi phần tử phải có trong `skill_library.list_skill_names()`) rồi **không bao giờ được đọc lại**. `workflow_exec.py` dựng message chỉ từ `agent['system_prompt']`.

Kênh duy nhất skill content thật tới model là `server.py::api_chat` → `_chat_skills(payload.get("skills"))` — đọc từ **payload request**, không từ agent profile. Hai thứ trùng tên, không liên thông. Người dùng tick skill ở tab Agents → không có tác dụng gì.

Phải chọn một, **không để nửa vời**:
- **(a)** Nối thật: `workflow_exec` đọc `agent['skills']`, nạp nội dung qua `skill_library.read_skill_content()`, ghép vào system prompt giống `_system_prompt_with_skills` đang làm cho chat.
- **(b)** Bỏ `skills` khỏi agent profile, và bỏ ô chọn skill khỏi `AgentsPage.tsx`.

Đề xuất **(a)** — UI đã có ô chọn, người dùng đang tưởng nó có tác dụng.

### R12 — Hai index skill song song `[S]`

`skill_library.py` (id `"{source}/{dirname}"`, route `/api/skill-library*`, nhận cả file `.md` đứng riêng, dùng để validate `agent.skills` và nạp content cho chat) và `runtime_skills.py` (id slug hoá từ `name`, route `/api/skills*`, chỉ quét `SKILL.md`) cùng tồn tại, cùng chạy, không doc nào giải thích cái nào là nguồn thật.

Việc: quyết một cái là nguồn thật, cái kia thành lớp mỏng đọc lại — hoặc ghi rõ trong SPEC vì sao phải tách. Không được để nguyên trạng không giải thích.

### R13 — `/api/tools` đặt tên gây hiểu nhầm `[C]`

Route này trả `behavior.tool_rollup()` — thống kê lịch sử tool-call moi từ log phiên Claude/Codex (`by_tool`, `count`, `sessions`, `models`). **Không phải** registry tool, không liên quan cấp quyền.

Việc: đổi tên thành `/api/tools/usage` (giữ route cũ redirect để không phá gì), hoặc ít nhất ghi rõ trong SPEC. Quan trọng vì R9 Phase 2 sẽ cần một registry tool thật và tên `/api/tools` sẽ bị tranh chấp.

### R14 — Agent profile nhận field lạ không cảnh báo `[S]`

`validate_agent_profile` không có allowlist khoá. Gõ sai `allowd_tools` → qua validate, `yaml.safe_dump` ghi thẳng xuống file, không log, không cảnh báo (`runtime_agents.py::create_or_update_agent`).

Nguy hiểm hơn sau R9 Phase 1: người dùng gõ sai tên field bảo mật sẽ tưởng đã đặt giới hạn trong khi không có gì áp dụng.

Việc: thêm allowlist khoá; field ngoài danh sách → lỗi validate rõ ràng, không im lặng chấp nhận.

### R15 — Test bom hẹn giờ `[M]`

`tests/test_pricing.py::test_cockpit_quota_pct_and_zero_quota` hardcode `ts: "2026-07-22T00:00:00Z"` rồi assert vào `stats["today"]`. Bucket "today" rỗng từ 2026-07-23 → `IndexError: list index out of range` tại dòng 66. Đã fail liên tục từ hôm đó, không liên quan thay đổi nào gần đây.

Việc: dùng ngày động (`now_iso()` hoặc freeze time), không hardcode.

### R16 — `ARCHITECTURE.md` lạc hậu `[M]` — **làm dở**

Commit `0e67e3c` (2026-07-28) đã sửa **một phần**: dòng 122 và 373 nay ghi đúng là `web/` vanilla-JS đã gỡ, server chỉ phục vụ `web-v3/dist`.

**Còn lại chưa sửa:**
- Dòng 238-239: `orchestrator.py`, `blackboard.py` — **không tồn tại**
- Dòng 190, 319-320: route `POST /api/agents/runs`, `GET /api/agents/runs/{id}/stream`, `/api/blackboard/{run_id}` — route thật là `POST /api/agent/runs` (số ít), không có blackboard
- Mô tả governance kiểm `risk_tier` + HITL trước khi launch child run — R10 chứng minh `create_child_run` **không** kiểm `risk_tier`

Việc: sửa nốt §9 theo hiện trạng.

### R17 — `ArtifactsPage.tsx` ép kiểu provider không kiểm `[S]`

Từ review code 2026-07-28. `ArtifactsPage.tsx` có 2 chỗ `provider as 'claude' | 'codex' | 'nvidia'` — ép kiểu thẳng một chuỗi đọc từ `localStorage`, không chuẩn hoá.

`ChatPage.tsx:30` có sẵn guard `asKind()` (giá trị lạ → `'nvidia'`), `SettingsPage.tsx` có helper tương đương. `ArtifactsPage.tsx` là chỗ duy nhất bỏ qua.

Hậu quả sau R0: chat cũ lưu `provider: "gemini"` sẽ index vào `providerDotClass['gemini']` = `undefined`. `cx()` lọc falsy nên không crash, chỉ là chấm nhận diện mất màu. Sẽ tái diễn với mọi provider bị gỡ/đổi tên sau này.

Việc: dùng lại `asKind` thay vì ép kiểu.

### R18 — `web-v3/dist/` đang bị track trong git `[C]`

`.gitignore` của `web-v3` loại `dist-ssr` nhưng **không** loại `dist`. Mỗi lần build sinh diff minified vô nghĩa, và có nguy cơ commit bundle cũ lệch với source.

Việc: gitignore `web-v3/dist`, build lúc deploy.

---

## 2b. Luật rút ra — bắt buộc áp dụng cho mọi field mới

R11 và R9 cùng một bệnh: **field được nhận và validate nhưng không có đường tiêu thụ hay điểm thực thi.**

Từ nay, không thêm field nào vào agent profile / payload run / API nếu chưa trả lời được cả 3:

1. **Ai đọc nó?** — chỉ ra `file:line` sẽ tiêu thụ giá trị này.
2. **Điểm thực thi ở đâu?** — hoặc chỉ ra chỗ chặn thật, hoặc ghi rõ `KHÔNG ENFORCE` ngay trong UI và trong SPEC.
3. **Gõ sai tên field thì sao?** — phải báo lỗi, không im lặng nhận (xem R14).

Áp dụng ngay cho `allowed_tools`/`allowed_paths` trong BD mục 23: chỉ được thêm vào agent profile **cùng lượt** với mục B5 (nối vào 3 call site) — không tách ra làm trước.

---

## 3. Không làm trong v1

- Gateway / Executor Port, transaction journal, idempotency ledger, artifact manifest SHA-256, SSE resume `Last-Event-ID`, Windows sandbox có Job Object, MCP. → nằm ở `basic-design/BD01-08`, là rewrite nhiều tuần, chưa được duyệt.
- Workspace switcher, storage quota. → wireframe có nhưng là dữ liệu bịa của bản mockup; backend không có khái niệm; thêm vào chỉ để trưng bày.

---

## 4. Việc cần làm trước khi code

1. Sửa test đang fail: `tests/test_pricing.py::test_cockpit_quota_pct_and_zero_quota` (nêu trong `04_IMPLEMENTATION_STATUS.md`, đã xác nhận hàm tồn tại).
2. `harness/hub/ARCHITECTURE.md` đã lạc hậu — §9 mô tả `services/orchestrator.py`, `blackboard.py`, `skills.py` (không tồn tại) và vẫn coi SPA `web/` vanilla-JS là hiện hành, trong khi thực tế là `web-v3` React. Cần cập nhật, nếu không mọi tài liệu sau đều neo sai.

---

## 5. Quyết định đã chốt (2026-07-28)

| # | Câu hỏi | Quyết định |
|---|---|---|
| Q1 | Hook v1 có được chạy shell không? | **Có** — nhưng bắt buộc qua đường gitjobs (worktree + diff gate), và chỉ bật sau R9 Phase 1 |
| Q2 | Files dùng chung hay theo run? | **Theo từng run** — kéo theo phải thêm bộ chọn run vào `FilesPage.tsx` |
| Q3 | `allowed_paths`/`allowed_tools`: thực thi hay gỡ? | **Thực thi thật**, ghi cả Phase 1 (cờ CLI + audit) lẫn Phase 2 (vòng lặp tool trong harness) |
| Q5 | Thứ tự làm | **R9 trước**, rồi mới R1+R2 |

| Q4 | Artifact chat lưu server thay hẳn localStorage hay song song? | **Server là nguồn thật, localStorage chỉ là cache** |
| Q6 | Phase 2 khởi động từ đâu? | **`nvidia_api` + 2-3 tool chỉ-đọc** |
| Q7 | Xử lý `gemini_cli` thế nào? | **Gỡ hẳn provider gemini** |

### R0 — Gỡ provider gemini `[M]`

Quyết định 2026-07-28. CLI cũng chưa cài trên máy nên hiện không dùng được.

File phải sửa (đã grep):
- Backend: `config.py`, `services/providers/gemini_cli.py` (xoá), `services/providers/__init__.py`, `services/usage.py`, `tests/test_providers.py`
- Frontend: `web-v3/src/lib/ui.tsx` (`ProviderDot`), `components/RunSpine.tsx`, `pages/ChatPage.tsx`, `pages/ArtifactsPage.tsx`, `pages/SettingsPage.tsx`
- Token màu `--color-gemini` trong `index.css`

Danh sách provider trên UI đọc từ `/api/providers` nên tự cập nhật; chỗ cần sửa tay là các union type `'claude' | 'codex' | 'nvidia' | 'gemini'` hardcode trong TS.

Làm cùng lượt với R9 Phase 1 — chạm cùng vùng code provider.

---

## 6. Trạng thái và thứ tự thi công

| # | Yêu cầu | Mức | Trạng thái |
|---|---|---|---|
| R0 | Gỡ provider gemini | M | **XONG** |
| R15 | Sửa test bom hẹn giờ | M | **XONG** |
| R10 | Gate `risk_tier` thiếu ở `create_child_run` | M | **XONG** |
| R14 | Allowlist khoá cho agent profile | S | **XONG** |
| R9 P1 | Lớp tool: cờ CLI + audit event | M | **XONG** |
| R11 | Nối `agent.skills` vào run (hoặc bỏ hẳn) | M | **XONG** |
| R16 | Viết lại `ARCHITECTURE.md` | M | **XONG** |
| R17 | `ArtifactsPage.tsx` ép kiểu provider không kiểm | S | **XONG** |
| R18 | Gitignore `web-v3/dist` | C | **XONG** |
| R1 | Hooks API | M | **XONG** |
| R2 | Files API | M | **XONG** |
| R3 | Skill CRUD | M | **XONG** |
| R12 | Hợp nhất 2 index skill | S | **XONG** |
| R4 | Artifact store cho chat | S | **XONG** |
| R5 | Run theo agent | S | **XONG** |
| R6 | Chạy thử agent | S | **XONG** |
| R8 | Edge `kind`/`label` | S | **XONG** |
| R13 | Đổi tên `/api/tools` | C | **XONG** |
| R7 | Tìm kiếm toàn cục | C | **XONG** |
| R9 P2 | Vòng lặp tool trong harness | S | Chưa |

**Thứ tự:**

1. ~~R0~~ (xong)
2. **Task B** = R9 P1 + R10 + R14 + R15 — cùng lượt vì đều chạm vùng provider/agent/governance, và R14 là điều kiện cần để R9 không lặp lại lỗi field chết
3. R11 (sau khi chốt (a) hay (b)) + R16
4. R1 + R2 → R3 → R12
5. R4 → R5 → R6 → R8
6. R13 → R9 P2 → R7

**Đang treo, cần chủ dự án quyết:** R11 chọn (a) nối `agent.skills` vào run, hay (b) bỏ field khỏi profile và khỏi UI.

---

## 7. Bổ sung — mô hình agent/skill/tool rộng hơn §R9 (audit 2026-07-28)

§R9 ở trên chỉ nói về `allowed_tools`/`allowed_paths`. Một audit riêng cho câu hỏi "mô hình agent/skill/tool đã được đặc tả đầy đủ chưa" tìm thêm 2 khoảng trống **không** nằm trong §R9, đã viết chi tiết ở [`SPEC-agent-skill-tool.md`](SPEC-agent-skill-tool.md):

- **`agent.skills` được validate nhưng không bao giờ được dùng.** `workflow_exec.py` build message chỉ từ `agent['system_prompt']`, không đụng `agent['skills']` một lần nào. Kênh duy nhất skill content thật sự tới model — `server.py::api_chat` qua `_chat_skills(payload.get("skills"))` — đọc tên skill từ **payload của request chat**, không phải từ agent profile. Hai kênh cùng tên `skills`, không liên thông.
- **`skill_library.py` và `runtime_skills.py` là hai index song song, không hợp nhất** — khác id scheme, khác route (`/api/skill-library` vs `/api/skills`), không tài liệu nào giải thích quan hệ giữa chúng.
- **`/api/tools` không phải registry** — nó là `behavior.tool_rollup()`, rollup lịch sử tool-call từ log phiên Claude/Codex, dùng để gắn tier telemetry qua `risk.classify_tool`. Tên route dễ khiến người đọc tưởng đây là danh sách tool hệ thống cấp quyền.

Xem `SPEC-agent-skill-tool.md` để có bảng enforcement đầy đủ theo từng field (`permission`, `risk_tier`, `budget`, `skills`, `allowed_tools`/`allowed_paths`) và kết luận: đây là **nhiều mảnh capability chồng lấn, không phải một mô hình thống nhất**.

---

## 8. Quan hệ với bộ `harness_hub_backend_docs_v0_1` — sau audit traceability (2026-07-28)

Một audit riêng đối chiếu 3 file này (`RD`/`SPEC`/`BD-R0-R9P1`) với `02_REQUIREMENTS_BASELINE.md` (77 REQ-ID) + `04_BASIC_DESIGN_IMPLEMENTATION_STATUS.md` cho kết quả: **hai bộ được viết độc lập**, không phải RD retrofit từ REQ-ID. Bằng chứng: cả 3 file chỉ trích `REQ-GOV-02` đúng **một lần** (§1, để phản bác mức nghiêm trọng, không phải để kế thừa), trích `BD04`/`BD02` đúng **hai lần** (để loại trừ phạm vi, §R9), và **không** trích bất kỳ REQ-ID nào khác trong 77 mục. Nguồn thật của RD/SPEC/BD là **đọc code + gọi API thật** (RD §1), không phải đọc baseline rồi diễn giải lại.

**Quyết định: giữ hai bộ tách biệt, không map từng R# sang REQ-ID.** Lý do:

1. **Không gian tên gần như không chồng lấn.** R1/R2/R6/R7/R13/R14/R17/R18 (Hooks, Files, run-test, search, đổi tên `/api/tools`, allowlist field, ép kiểu FE, gitignore) không có REQ-ID tương ứng vì baseline **không có khái niệm** Hooks/Files/workspace/quota, và không audit từng bug FE cụ thể. R0 (gỡ gemini) là quyết định phạm vi, không phải requirement bên baseline.
2. **Ép map sẽ neo sai kiến trúc.** Baseline còn `In Review`, tự treo owner decision (OD-01..05, RD-01..08), và tầng BD/D mô tả hệ thống lớn hơn nhiều (Gateway/Executor Port, transaction journal, artifact manifest SHA-256, Windows sandbox Job Object, MCP) — RD §3 đã loại khỏi scope v1 một cách tường minh. Map R9 vào REQ-CHAT-02/REQ-SEC-04..06 sẽ ngầm cam kết theo kiến trúc đó dù chưa được duyệt.
3. **Một mapping table cho 19 mục mà phần lớn ra "—" là chi phí bảo trì không ai cập nhật** — đúng rủi ro mà chính audit này được yêu cầu cân nhắc.
4. **Baseline cũng có blind spot mà RD tự phát hiện, không phải ngược lại:** R10 (thiếu gate `risk_tier` ở `create_child_run`) không nằm trong bất kỳ REQ-ID nào của baseline (baseline chỉ nói tới lỗ `allowed_paths`/`allowed_tools` ở `REQ-GOV-02`, không nói tới đường spawn thứ hai thiếu gate `risk_tier`) — dù audit `04_STATUS` chạy cùng ngày 2026-07-28. Điều này củng cố: đọc code trực tiếp ở đây bắt được thứ mà bộ audit 77-REQ-ID kia bỏ sót.

**Khi hai bộ cùng nói về một hành vi và khác nhau về mức độ (ví dụ `REQ-GOV-02` gọi lỗ trống parent là "có thể vượt lên unrestricted"):** ưu tiên bằng chứng grep/test mới nhất trong RD/SPEC, nhưng **không tự sửa** trạng thái bên baseline — đó là tài liệu ngoài, chủ dự án/owner của bộ đó phải tự cập nhật nếu đồng ý.

### 8.1 Lỗ hổng thật — baseline có yêu cầu MUST, RD chưa nói tới

Khác với các cụm ở §3 (đã loại tường minh, có lý do), những mục dưới đây **không được nhắc, không được loại, chỉ đơn giản là thiếu**. Ghi ra đây để thành thiếu-có-ý-thức thay vì thiếu-âm-thầm. Chưa mục nào được lên lịch.

| Cụm | REQ-ID | Nội dung | Ghi chú |
|---|---|---|---|
| API envelope | `REQ-API-02` | schema version, correlation ID, `Idempotency-Key`, `If-Match`, error shape chuẩn | Route hiện trả dict thô + `HTTPException` |
| An ninh nền | `REQ-SEC-01/02/03/07/08` | CSRF/loopback hardening, phân loại dữ liệu, che secret trong log, audit trail, cấm tự nhận là "an toàn production" | R9 chỉ chạm `SEC-04/05` (giới hạn tool/CLI). Phần còn lại của cụm chưa đụng |
| Snapshot bất biến | `REQ-WF-04`, `REQ-WF-06` | đóng băng hash của definition/profile/route/skill lúc tạo run; skill drift phải làm run cũ mất hiệu lực | **Đã nặng hơn sau R11**: skill nay thật sự vào prompt, nên drift skill giờ đổi được hành vi run mà không ai biết |
| Duyệt & audit | `REQ-GOV-04/05` | approval gắn với hash hành động canonical + hạn dùng + dùng một lần; log audit chống sửa | R1 (Hooks) có log thực thi nhưng không chống sửa, không gắn approval |
| Memory | `REQ-OPS-02` | nguồn gốc / hạn / thu hồi cho memory candidate | Chưa đụng |

Chưa đề xuất đưa cụm nào vào v1 — cần chủ dự án quyết. Ưu tiên cao nhất theo tôi là `REQ-WF-06` (skill drift), vì R11 vừa biến nó từ lý thuyết thành có thật.

---

## 9. Bug frontend từ review đúng phạm vi commit `37c8bee..0e67e3c` (2026-07-28)

Đợt UI này đã vào `main` qua 5 commit mà chưa từng qua review. Review lại đúng khoảng commit tìm ra:

### R19 — `ChatPage.tsx` hỏng nội dung khi gửi chồng `[M]` — BLOCKER

Đã tự kiểm chứng.

- `ChatPage.tsx:381` — `<textarea onKeyDown>` gọi `onSubmit()` khi Enter, **không kiểm `streaming`**. Nút gửi thì có đổi thành nút Dừng khi đang stream, nhưng phím Enter đi vòng qua nó.
- `ChatPage.tsx:118` — `patchLast` luôn sửa `messages[messages.length - 1]`, không sửa message đã chốt lúc gửi.

→ Đang stream mà gõ tin nhắn thứ hai rồi Enter: placeholder mới được đẩy vào cuối, `delta`/`reasoning` của **stream thứ nhất** đổ vào **message thứ hai**. Nội dung lẫn lộn thấy rõ.

→ Kèm theo: `controllers.current.set(chat.id, ...)` bị ghi đè, stream đầu **không còn cách dừng** từ UI.

Việc: chặn Enter khi `streaming`, hoặc cho `patchLast` nhắm theo id message chốt lúc gửi thay vì theo độ dài mảng. Cách hai đúng hơn.

### R20 — `WorkflowsPage.tsx` nút "Dừng" là đồ giả `[M]`

- `:71` — `<Button onClick={start} disabled={busy}>{busy ? 'Dừng' : 'Chạy'}</Button>`. Đang chạy thì đổi chữ thành "Dừng" nhưng vẫn `disabled` → **không bấm được**. `controller.current.abort()` chỉ được gọi ở cleanup lúc unmount (`:32`). Không có cách nào huỷ run từ UI.
- `:42` — nhận event `interrupt` thì `busy` về `false` trong `finally`, mở lại nút "Chạy". Mà `run`/`logs`/`interrupt` là state cấp trang, **không khoá theo `run_id`** → chạy run mới sẽ đè mất run đang dừng ở gate. Gate vẫn mở phía server, nhưng UI không còn đường tới.

Việc: nút Dừng thật (gọi `abort`), và chặn chạy run mới khi còn interrupt chưa xử lý.

### R21 — Canvas workflow chỉ dùng được bằng chuột `[S]`

`:81` — node là `<div>` chỉ có `onPointerDown`, không `role`/`tabIndex`/`onKeyDown`. Không chọn/kéo/mở Inspector bằng bàn phím được. Port vẽ cạnh là `<button>` thật có nhãn, nhưng chỉ nối `onPointerDown`/`onPointerUp` — Enter/Space không làm gì.

### R22 — Dọn dẹp `[C]`

- `index.css:92-102,109-110` — `.chat-grid`/`.panes-1..4`, `.chat-layout*`, `.pane`/`.pane > .msgs` **0 nơi dùng** (grep toàn `.tsx`), là rác từ đợt viết lại ChatPage sang `.chat-workspace`/`cw-*`.
- Token thêm trong chính khoảng commit này mà không ai dùng: `--hub-size-drawer`/`--spacing-context-strip`, `--hub-size-pane-header`/`--spacing-pane-header`.
- `WorkflowsPage.tsx:71` — badge "Nhà cung cấp" in thẳng `agent.provider`, hiện `"smart, code"` thay vì provider thật. `AgentsPage.tsx` đã có `resolveProvider()` qua `/api/model-classes` trong cùng khoảng commit này nhưng không áp sang.
- `WorkflowsPage.tsx:20` — `chain()` dựng `new Map(edges.map(e => [e[0], e[1]]))`, node có fan-out thì **âm thầm chỉ giữ cạnh cuối**. Inspector hiển thị sai so với `edges` thật, không cảnh báo. Không tới được backend (`POST /api/workflows/validate` từ chối đúng), nhưng UI nói dối trước khi Save.
- `WorkflowsPage.tsx:87` — `// @ts-ignore` chặn cả dòng chỉ để giữ tham số `update` không dùng. Đổi thành `_update`.

### Đã kiểm, KHÔNG có vấn đề

- **An ninh**: không `dangerouslySetInnerHTML` ở đâu trong `web-v3/src`; `lib/markdown.tsx` dựng JSX text node nên React tự escape output của model.
- **Dữ liệu bịa**: không có. Mọi tính năng chưa nối đều ghi rõ `chưa nối backend`/`TODO(backend)` hoặc `—`.
- **Đại số pan/zoom/drag** của canvas (`toWorld`, drag handler, `fit()`): truy tay đúng, không tái hiện được lệch.
- **Hợp đồng backend**: curl đủ 9 endpoint, tên field khớp. Cạnh vẽ tự do **không** làm backend chạy sai — `validate` từ chối đúng với fan-out.

---

## 10. Chốt review `02_REQUIREMENTS_BASELINE.md` (2026-07-28)

Đã đọc toàn bộ 425 dòng / 77 REQ-ID.

### 10.1 Kết luận: **nhận làm bản đồ requirement chính thức**

Chất lượng cao và trung thực hơn mức thường thấy:

- Mỗi REQ có ID ổn định, priority (`MUST`/`SHOULD`/`MAY`), **state tách riêng** (`VERIFIED` = quan sát được trong code/test, `TARGET` = hợp đồng chưa đạt, `PROPOSED` = cần owner duyệt), acceptance criteria, và ref tới **file test có thật**.
- §1 nói thẳng: *"a `TARGET MUST` is not evidence that the current code satisfies it"* — đúng ranh giới mà hầu hết doc hay nhập nhèm.
- Có 2 mục `VERIFIED gap` (`REQ-RUN-06`, `REQ-SEC-08`) mà nội dung là **"không được tuyên bố hành vi hiện tại là an toàn production"**. Đây là requirement cấm-nói-quá — hiếm và đáng giữ.
- Header tự ghi `implementation_status: Current implementation is not Gate C/D qualified`.

### 10.2 Ba điểm đã lệch so với code, cần ghi delta (không sửa file gốc — đó là drop read-only)

| Chỗ | Baseline ghi | Thực tế sau 2026-07-28 |
|---|---|---|
| §5.3 dòng 121 | *"Provider modules exist for NVIDIA API, Claude CLI, Codex CLI and Gemini CLI"* | Gemini **đã gỡ** (R0, commit `c7960be`) |
| `REQ-WF-05` (`SHOULD / VERIFIED`) | *"chat only activates known names"* — chỉ nói tới chat | R11 (`642e467`) đã nối `agent.skills` vào **workflow run**. Mô tả cũ không sai, nhưng **thiếu** |
| `REQ-GOV-02` | *"child scope rỗng có thể vượt lên unrestricted"* | Đúng có bug `_ensure_subset`, nhưng chưa field nào được enforce ở điểm gọi → chưa có đặc quyền để leo. Xem §1 "Đính chính" |

Và một điểm **nặng lên vì R11**: `REQ-WF-06` (`MUST / TARGET` — ghim skill theo `{source,name,content_hash}`, drift phải fail-closed). Trước R11 `agent.skills` là field chết nên drift vô hại. Nay skill thật sự vào prompt → **sửa file skill là đổi hành vi run mà không ai biết**. Chuyển thành ưu tiên cao.

### 10.3 Phương án (b) đã chốt — khung governance, không nhận scope

Nhận từ `00_INDEX`:
- §3 chuỗi ưu tiên nguồn sự thật
- §5 vòng đời trạng thái tài liệu (`Draft`/`In Review`/`Approved`/`Superseded`/`Reference only`)
- §6 Definition of Ready + điều kiện dừng tạo Architecture Clarification Request
- §8 Gate A–E

**Không** nhận §4 "Target v1" nguyên văn — RD giữ scope hẹp của mình. Đây là **biến thể có chủ đích**, không phải bỏ sót.

RD hạ cấp: từ đây RD là **lớp kế hoạch thi công**, không phải doc requirement song song. Requirement chính thức tra ở `02_REQUIREMENTS_BASELINE`; R0–R22 là hạng mục công việc, không phải requirement cạnh tranh.

### 10.4 "Đủ layer enterprise dù thử nghiệm" — 77 REQ chính là bản đồ layer

Đối chiếu từng lớp với code thật:

| Lớp | REQ family | Hiện trạng |
|---|---|---|
| API / contract | `REQ-API` (5) | Route + SSE có. Envelope, schema version, correlation ID, `Idempotency-Key`, SSE resume — **chưa** |
| Domain | `REQ-WF` (7) | Linear chain + validate có. Snapshot bất biến, ghim hash skill — **chưa** |
| Runtime / state | `REQ-RUN` (9) | Run/thread/checkpoint/event/interrupt có. Journal, state version, idempotency ledger — **chưa** |
| **Execution** | `REQ-CHAT` (6) | **Lớp DUY NHẤT vắng hoàn toàn** — `workflow_exec.py` gọi thẳng `get_provider()`, không có Gateway/Executor Port |
| Security | `REQ-SEC` (8) | Loopback/CSRF/path boundary có. Classification, secret broker, typed tool request — chưa |
| Governance | `REQ-GOV` (7) | Risk tier + guardrail decision có. Capability intersection, approval binding, audit tách khỏi event — chưa |
| Data / artifact | `REQ-DATA` + `REQ-ART` (8) | File-backed có. UTC/version, backup, manifest content-addressed — chưa |
| Observability | `REQ-OPS` (5) | Usage/session/replay/memory có. Degraded state, correlation xuyên suốt — chưa |
| QA | `REQ-NFR` (5) | Test deterministic có (234 pass). SLO, degradation envelope — chưa |
| Migration | `REQ-MIG` (5) | Chưa |
| Git job | `REQ-GIT` (4) | Có, và baseline cố ý giữ tách khỏi Executor |
| Eval / suite | `REQ-EVAL` (4) | Có |

**Kết luận đảo lại đề xuất trước của tôi:** mọi lớp đều đã tồn tại ở dạng mỏng, **trừ lớp Execution — vắng hẳn**. Nếu tiêu chí là "đủ layer, dù mỏng", thì một **Gateway/Executor Port tối giản** phải vào scope, không phải bị loại.

Loại ≠ mỏng. Trước tôi đề xuất loại BD04 vì nhìn nó như công trình nhiều tuần. Nhưng BD04 §7 có lộ trình chia nhỏ: `fixtures → mock port → nối Runtime → 1 API adapter → conformance → CLI`. Dừng ở **bước 3** là đủ để lớp Execution tồn tại: có `ExecutionRequest`/`Event`/`Result`/`Error`, `workflow_exec` không còn gọi `get_provider()` trực tiếp. Đó là `REQ-CHAT-02` — không kèm capability pinning (`REQ-CHAT-03`), không kèm controlled executor (`REQ-SEC-06`, Gate D).

**Đề xuất bổ sung R23** — Gateway/Executor Port tối giản, phạm vi đúng `REQ-CHAT-02`, dừng trước `REQ-CHAT-03`/`REQ-SEC-06`. Xếp sau R9 Phase 1, vì R9 P1 chạm cùng vùng `providers/base.py` và sẽ tự nhiên định hình `ExecutionRequest`.

---

## 11. Kết thúc đợt build (2026-07-28)

R0–R23 đã build và merge hết, trừ **R9 Phase 2** (harness tự chạy vòng lặp tool) — cố ý để sau, vì nó dựng trên seam R23 vừa có và là hạng mục riêng.

Trạng thái cuối: **264 test pass**, `tsc -b` pass, `vite build` pass.

### Ba việc phát sinh trong lúc build, cần biết

1. **Merge làm gãy tiêu chí nghiệm thu của R23.** `POST /api/agents/{id}/test` (R6) viết trước khi `services/execution.py` tồn tại nên gọi thẳng `get_provider(...).stream_chat(...)`, đi vòng qua seam. Test grep trong `test_execution.py` bắt được đúng lúc merge. Không có test đó thì lớp Execution đã thủng ngay ngày đầu.
2. **Seam R23 ban đầu không inject được.** `resolver: ProviderResolver = get_provider` là default argument, bind lúc import — test chỉ patch được bản sao cũ chứ không phải đường production chạy. Đã đổi sang resolve lúc gọi.
3. **R18 kéo theo hệ quả:** untrack `web-v3/dist` khiến `tests/test_ui_v3.py` fail trên mọi clone/worktree sạch cho tới khi chạy `npx vite build`. Không phải bug, nhưng phải ghi vào hướng dẫn chạy test.

### Còn nợ, chưa lên lịch

- **R9 Phase 2** — vòng lặp tool trong harness. Chỉ đây mới là "không để CLI tự chọn tool" theo đúng nghĩa; Phase 1 vẫn là uỷ quyền cho vendor CLI.
- **§8.1** — cụm REQ-ID `MUST` của baseline chưa đụng: `REQ-API-02`, `REQ-SEC-01/02/03/07/08`, `REQ-WF-04/06`, `REQ-GOV-04/05`, `REQ-OPS-02`. Ưu tiên cao nhất là `REQ-WF-06` (ghim hash skill), vì R11 đã biến skill drift từ vô hại thành đổi được hành vi run.
