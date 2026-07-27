# BD — Harness ver2 · Phase D (Personal Harness Completion)
**Date:** 2026-07-20 · **Status:** ✅ D1–D4 shipped (verify 2026-07-25: `runtime_artifacts.py`, `runtime_validate.py`, `MODEL_CLASS_ROUTING` trong `config.py`, 4 workflow mẫu trong `workflows/*.workflow.yaml`) · D5 (canvas) không theo spec SVG cũ nữa — thay bằng "Workflow Canvas v2" (design import riêng, đang giao Codex, xem `WorkflowsPage.tsx`) · **Author:** Claude (Fable 5)
**Upstream:** Hub v2 đã ship Phase A + B + C1–C3 + Cx (162 tests xanh, verify 2026-07-20).
**Nguồn thiết kế:** repo `bd-chunk-project` (github lechihuy-droid) — lấy 4 ý tưởng tốt nhất:
artifact workspace (ai-harness/detail.md), validation layer (architect.md §7),
routing policy theo chi phí (Tối Ưu Token Cho Harness.md), workflow template library.

---

## 0. Kết luận audit — tận dụng gì từ harness hiện tại

**Quyết định kiến trúc: KHÔNG tạo repo/folder mới. Harness ver2 = Hub hiện tại + Phase D.**
Lý do: Hub v2 đã có sẵn ~80% kiến trúc 5 lớp mà plan personal-harness đề ra.
Fork ra folder mới = duplicate 15k dòng đang chạy tốt + 162 test — chống lại nguyên tắc Simplicity First.

| Lớp (plan personal-harness) | Hub đã có (tái dùng nguyên trạng) | Trạng thái |
|---|---|---|
| 1. Web app | SPA vanilla JS, 12 trang, chat multi-pane, cockpit, run view (C3), skill library UI | ✅ ship |
| 2. Declarative config | `workflows/*.workflow.yaml` (schema+IR C2a), `agents/*.agent.yaml` (C1), SKILL.md index (B4) | ✅ ship |
| 3. Runtime + adapters | `workflow_exec` (C2b), provider layer claude/codex/gemini/nvidia (A), child-run governance (C2c), budget cap, model alias (Cx) | ✅ ship |
| 4. Substrate | `runtime/runs/<id>/events.jsonl` + `threads/checkpoints` append-only | ✅ ship — thiếu artifacts/ |
| 5. Governance | HITL gate (runtime_interrupts + UI approve/reject), risk tiers, CSRF, governance check | ✅ ship — thiếu validation engine |

**Phần còn thiếu để thành "personal harness ver2" hoàn chỉnh → Phase D bên dưới.**
C4 canvas (BD Phase C) giữ nguyên spec cũ, xếp cuối cùng.

---

## 1. Mô hình orchestra

Như BD Phase B §0: Claude main viết brief + ghép file shared + verify UI + commit ·
Codex (`codex exec`, bản pnpm, preamble FRESH START, `</dev/null`, model gpt-5.6-sol) code các step `[CODEX]` ·
Sonnet subagent chạy full pytest + review diff sau mỗi step.

**Test gate:** `.ih\Scripts\python.exe -m pytest harness/hub/tests -q` xanh 100% (162+) sau mỗi step.
**Fake CLI rule:** test không gọi claude/codex/NVIDIA thật.

---

## 2. Các step Phase D

| Step | Nội dung | Executor | Size | Phụ thuộc |
|---|---|---|---|---|
| D1 | Artifact workspace per run | [CODEX] | S | — |
| D2 | Validation node (eval checks) | [CODEX] | M | D1 |
| D3 | Routing policy alias (cheap/code/smart) | [CODEX] | S | — (song song D1) |
| D4 | Workflow template library (3 workflow mẫu) | Claude main | S | D2, D3 |
| D5 | C4 canvas SVG (spec ở BD Phase C) | [CODEX] | L | D4 ổn định |
| D✔ | Verify + commit từng step | Claude + Sonnet | — | từng step |

### Step D1 — Artifact workspace `[CODEX]` (S)

Node output hiện chỉ nằm trong `state.json` (string). Ver2: mỗi run có thư mục artifact.

**Files:** `services/runtime_state.py` (mở rộng), `services/workflow_exec.py`, `tests/test_workflow_exec.py`.

1. Tạo `runtime/runs/<run_id>/artifacts/` khi run start.
2. Sau mỗi node LLM: ghi output đầy đủ ra `artifacts/<node_id>.md` (state.json chỉ giữ 2000 char đầu + đường dẫn artifact — giảm phình state).
3. Endpoint `GET /api/workflows/runs/{id}/artifacts` (list) + `/artifacts/{name}` (đọc, chặn path traversal — reuse pattern `runs.py`).
4. Run view UI (app.js): tab Artifacts trong run detail, render markdown bằng renderer sẵn có của chat.
5. Tests: artifact ghi đúng file, state giữ preview + path, path traversal bị chặn 403.

### Step D2 — Validation node `[CODEX]` (M)

Từ architect.md §7: kiểm tra output trước khi cho qua gate — bắt lỗi rẻ hơn người review.

**Files:** `services/workflow.py` (schema), `services/workflow_exec.py`, mới `services/runtime_validate.py`, `tests/test_runtime_validate.py`.

1. Node type mới `validate` trong workflow schema:
   ```yaml
   - id: check_draft
     type: validate
     target: draft            # node id có output cần kiểm
     checks:
       - {kind: min_length, value: 200}
       - {kind: must_include, values: ["## Kết luận", "nguồn"]}
       - {kind: must_not_include, values: ["TODO", "PLACEHOLDER"]}
       - {kind: json_parseable}          # optional
     on_fail: interrupt       # interrupt (chờ người quyết) | fail (dừng run)
   ```
2. `runtime_validate.run_checks(text, checks) -> list[Violation]` — thuần, không LLM.
3. Executor: node validate đọc artifact của `target`, chạy checks; fail → theo `on_fail`
   (reuse `runtime_interrupts` — hiện trên run view như HITL gate kèm danh sách violation).
4. Kết quả validation ghi vào `events.jsonl` (`validation_pass` / `validation_fail` + violations).
5. Tests: từng kind check, on_fail cả 2 nhánh, violation hiển thị trong state.

### Step D3 — Routing policy alias `[CODEX]` (S)

Từ nghiên cứu token-optimization: việc rẻ/volume đẩy NVIDIA free, code đẩy Codex, việc khó đẩy Claude.

**Files:** `config.py`, `services/runtime_agents.py`, `services/workflow_exec.py`, `tests/test_runtime_agents.py`.

1. `config.py` thêm:
   ```python
   MODEL_CLASS_ROUTING = {
       "cheap": {"provider": "nvidia", "model": None},   # default catalog model
       "code":  {"provider": "codex",  "model": None},
       "smart": {"provider": "claude", "model": None},
   }
   ```
2. `agent.yaml` chấp nhận `provider: cheap|code|smart` (model class) bên cạnh id provider thật;
   loader resolve qua `MODEL_CLASS_ROUTING` trước khi `get_provider()`. Provider id thật vẫn dùng được như cũ (backward compatible — agent hiện có không đổi).
3. Run view + Settings hiển thị provider đã resolve (badge "cheap→nvidia").
4. Tests: resolve đúng, id thật pass-through, class không tồn tại → lỗi validate rõ ràng.

### Step D4 — Workflow template library (Claude main, S)

3 workflow mẫu dùng thật hằng ngày, đặt tại `workflows/`:

1. `research-draft-review.workflow.yaml` — NVIDIA draft (cheap) → validate → Claude refine (smart) → gate approval → artifact.
2. `code-task.workflow.yaml` — Claude viết brief (smart) → gate approval → Codex implement (code) → Claude review (smart).
3. `doc-pipeline.workflow.yaml` — ingest file trong workspace → NVIDIA summarize từng phần (cheap) → validate must_include → Claude tổng hợp (smart) → gate.

Mỗi file kèm comment header giải thích khi nào dùng. Chạy thử end-to-end bằng fake provider trong test + 1 lần chạy thật để verify.

### Step D5 — Canvas `[CODEX]` (L)

Giữ nguyên spec BD Phase C step C4. Chỉ bắt đầu khi D1–D4 chạy ổn ≥ 1 tuần dùng thật.

---

## 3. Không làm (giữ triết lý)

- Không LangGraph / framework orchestration — runtime tự có đủ.
- Không DB — file là chân lý.
- Không API key bắt buộc — CLI subscription + NVIDIA free.
- Không cho agent tự sửa SKILL.md — mutation qua git-job review.
- Không port ontology/RKB/BD-mapping của bd-chunk-project — đó là nghiệp vụ BD doanh nghiệp, không phải personal harness.

---

*Phase D — chờ APPROVE trước khi viết brief giao Codex.*
