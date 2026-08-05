# BD — Build Plan: Version Governance POC (Harness Hub)

**Date:** 2026-08-02
**Status:** 🟢 Done — 2026-08-03. `verify_dod.py` **12/12 PASS**, vgov **42 test pass**,
hub **334 test pass** (không hồi quy), `pnpm --dir harness/hub/web-v3 build` + `oxlint` pass.
Số liệu cập nhật sau vòng code review + security review + ADR-010.
**Ref:** [`01_requirements.md`](01_requirements.md) v1.1 🟢, [`02_system_design.md`](02_system_design.md) v1.1 🟢
**Estimate:** ~34,5 giờ làm việc thực (không tính thời gian chờ review)
**Người thực thi:** Codex (`codex exec`) cho Step A1–F1. Claude viết brief + review từng phase.

---

## Prerequisites

- [x] RD approved (Gate 1)
- [x] SD approved (Gate 2)
- [x] Docker Desktop chạy — verified: server 29.6.1, compose v5.2.0, linux/overlayfs
- [x] Python 3.11 tại `C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe`
- [ ] `NVIDIA_API_KEY` có trong `.env` repo-root (hub đang dùng — xác nhận lại trước Step B1)
- [ ] Port trống: 8810 (vgov-api), 8811 (vgov-runtime), 8812 (mlflow), 5433 (postgres), 9000/9001 (minio)

---

## Ngân sách LOC — đối chiếu `[PB §12]`

| Phần | Guardrail | BD ước tính | **Thực tế đo sau khi xong** |
|---|---:|---:|---:|
| Backend domain/API + adapters + migration | 4.000–7.000 | 4.400 | **2.273** |
| Runtime | 2.000–4.000 | 1.650 | **172** |
| Minimal UI/debug surface | 1.500–3.000 | 1.960 | **94** |
| Scripts + verify_dod | 500–1.500 | 1.350 | **473** |
| **Tổng production code** | **8.000–15.500** | 9.360 | **3.012** |

Test: **865 LOC**, không tính vào production `[PB §12]`.

> **Ước tính của BD sai gấp ~3 lần theo hướng thừa.** Vertical slice thật gọn hơn nhiều so với dự
> đoán: chỉ một runtime adapter, lineage là FK traversal không cần bảng riêng, Explain Difference là
> so sánh cấu trúc thuần, và UI tái dùng gần như toàn bộ component có sẵn của `web-v3`.
> Guardrail `[PB §12]` là **trần cảnh báo scope creep**, không phải hạn mức phải tiêu — dưới band
> nghĩa là scope được giữ chặt, không phải thiếu chức năng: `verify_dod.py` đạt **12/12**.
> Không thêm code đệm để chạm số.

Ước tính cộng dồn theo step (giữ lại để đối chiếu độ chính xác của việc ước lượng):

| Bucket | Các step |
|---|---|
| Backend 4.400 | A2 450 · A3 800 · B3 900 · B4 250 · C2 700 · C3 400 · D1 400 · D2 500 |
| Adapters 1.650 | A3 150 · B1 600 · B2 700 · C1 200 |
| UI 1.960 | E1 60 · E2 1.750 · E3 150 |
| Migration/config 1.350 | A1 300 · A2 500 · B3 150 · C2 150 · F1 250 |

---

## Build Steps

### Phase A — Infra + Workflow Release (8h)

#### Step A0 — Spike: verify giả định vendor ⚠️ BẮT BUỘC TRƯỚC KHI CODE

**Mục tiêu:** Đóng 3 rủi ro ở `[SD §11]` trước khi viết adapter và compose thật.

**Files:** `scratch/` (không commit)

**Việc làm:**
- [ ] `pip install mlflow==3.15.0` vào venv tạm, chạy MLflow server local (sqlite backend)
- [ ] Verify `mlflow.genai.register_prompt(...)` rồi `load_prompt("prompts:/x@production")` — in
      `type(p)`, `p.name`, `p.version`, `p.template`. Xác nhận `version` là int hoặc str số
- [ ] **Verify image mlflow:** build `FROM ghcr.io/mlflow/mlflow:v3.15.0` + `pip install
      psycopg2-binary boto3`, chạy `mlflow server --backend-store-uri postgresql://...` trong
      container. Image gốc **không** có driver Postgres và boto3 — nếu không cài thêm thì Step A1 sẽ
      không lên healthy
- [ ] `pip install langgraph==1.2.10`, build StateGraph 3 node, invoke thử
- [ ] Verify `mlflow.langchain.autolog()` có bắt trace của LangGraph 1.2 không

**Smoke test:**
```bash
python scratch/spike_mlflow.py
```
→ expected: in ra `name=api-bd-generator version=2 template=<str>`, không exception; container mlflow
kết nối được Postgres

**Nếu fail:** báo lại — có thể phải đổi cách resolve (`MlflowClient` thay `mlflow.genai`) hoặc dùng
fallback trace ở `[SD §11]`. **Không tự đổi thiết kế.**

**Estimate:** 60 min · **LOC production:** 0

---

#### Step A1 — Docker compose + skeleton service

**Mục tiêu:** 5 service lên xanh, `/health` trả 200.

**Files — tạo mới:**
- `deploy/docker-compose.yml`, `deploy/.env.example`, `deploy/init-minio.sh`
- `deploy/mlflow.Dockerfile` — image dẫn xuất, cài `psycopg2-binary` + `boto3` `[SD §8]`
- `app/Dockerfile`, `app/requirements.txt`
- `runtime/Dockerfile`, `runtime/requirements.txt`
- `app/config.py`, `app/main.py`, `app/api/health.py`

**Việc làm:**
- [ ] compose đúng `[SD §8]`: postgres (2 DB `vgov` + `mlflow`), minio + minio-init (2 bucket, bật
      versioning cho `vgov-artifacts`), mlflow **build từ `mlflow.Dockerfile`**, vgov-api, vgov-runtime
- [ ] Healthcheck cho cả 5 service; `depends_on: condition: service_healthy`
- [ ] Bind-mount repo read-only vào vgov-api tại `/repo`; set `git config --global --add
      safe.directory /repo` trong Dockerfile
- [ ] `config.py` đọc toàn bộ biến ở bảng `[SD §8]`, **không hardcode credential**
- [ ] `GET /health` kiểm tra từng dependency (postgres, minio, mlflow, runtime), trả trạng thái từng cái

**Smoke test:**
```bash
docker compose -f harness/version-governance/deploy/docker-compose.yml up -d --build
```
→ expected: `docker compose ps` — 5 service `healthy`; `curl localhost:8810/health` → 200, mọi
dependency `"ok"`

**Estimate:** 90 min · **LOC:** 300 (config)

---

#### Step A2 — Schema + migration + trigger

**Mục tiêu:** Toàn bộ `[SD §2]` tồn tại trong DB, invariant enforce ở tầng dữ liệu.

**Files — tạo mới:**
- `app/persistence/models.py` — SQLAlchemy 2.x
- `app/persistence/session.py`
- `app/migrations/env.py`, `app/alembic.ini`
- `app/migrations/versions/0001_initial.py`

**Việc làm:**
- [ ] Model đúng DDL `[SD §2.2–2.7]`, không bịa thêm cột. Chú ý `execution_run.workflow_release_id`
      là **nullable** + `ck_release_required`; `runtime_callback.response_body` **nullable**
- [ ] **Thứ tự migration bắt buộc** `[SD §2.1]`: enum → `trg_block_write()` → bảng → trigger.
      Postgres yêu cầu function tồn tại trước `CREATE TRIGGER`
- [ ] `component_kind` chỉ 4 giá trị: `PROMPT`, `AGENT`, `TOOL`, `MODEL`
- [ ] Trigger dùng SQLSTATE **`VG409`**, không dùng `23514` (`[SD §2.8]` — nếu dùng chung thì lỗi
      CHECK bị map nhầm thành 409)
- [ ] Migration chứa đủ: 5 enum, 10 bảng, `trg_block_write()`, `trg_release_immutable()`,
      `trg_baseline_pointer_only()`, mọi CHECK (`ck_no_alias`, `ck_prompt_numeric`, `ck_provenance`,
      `ck_content_hash`, `ck_input_hash`, `ck_published_complete`, `ck_release_required`),
      `uq_baseline_active` partial index
- [ ] `alembic upgrade head` chạy tự động trong entrypoint của vgov-api

**Smoke test:**
```bash
docker compose exec postgres psql -U vgov -d vgov -c "\dt"
```
→ expected: 10 bảng. Và:
```bash
docker compose exec postgres psql -U vgov -d vgov -c "INSERT INTO run_component (manifest_id,kind,ref,exact_version) VALUES (gen_random_uuid(),'PROMPT','x','production');"
```
→ expected: `ERROR: ... violates check constraint "ck_no_alias"`

**Estimate:** 120 min · **LOC:** 450 backend + 500 migration

---

#### Step A3 — Domain Release/Environment + SourceControlPort + test

**Files — tạo mới:**
- `app/domain/release.py`, `app/domain/environment.py`
- `app/ports/source_control.py`, `app/adapters/git_source.py`
- `app/persistence/repositories.py` (phần release + environment)
- `app/services/release_service.py`
- `app/api/releases.py`, `app/api/environments.py`
- `app/errors.py` — map SQLSTATE theo bảng `[SD §2.8]`: `VG409`→409, `23514`→422, `23505`→409
- **Test:** `app/tests/conftest.py`, `app/tests/test_immutability.py`, `app/tests/test_rollback.py`

**Việc làm:**
- [ ] `POST /releases` tạo DRAFT; `POST /releases/{id}/publish` resolve `git_ref` → 40-hex SHA rồi set
      PUBLISHED (FR-REL-001)
- [ ] **Không** tạo endpoint `PUT`/`DELETE` cho release `[SD §6]`
- [ ] `PUT /environments/{env}` — từ chối release `DRAFT` (422 `RELEASE_NOT_PUBLISHED`), ghi
      `environment_mapping_audit` trong cùng transaction (FR-ENV-004)
- [ ] Promote và rollback dùng **chung** endpoint (FR-ENV-003)
- [ ] `conftest.py` dùng DB `vgov_test` trong compose (không thêm dependency `testcontainers`)
- [ ] Test immutability gọi **SQL trực tiếp** — API không hở đường sửa nên không test qua HTTP được

**Smoke test:**
```bash
pytest harness/version-governance/app/tests/test_immutability.py harness/version-governance/app/tests/test_rollback.py -q
```
→ expected: pass. Publish rồi `UPDATE ... SET git_commit` → SQLSTATE `VG409`; rollback PROD về release
cũ → release mới vẫn tồn tại nguyên vẹn.

**Estimate:** 180 min · **LOC:** 800 backend + 150 adapter (+400 test)

---

#### Step A4 — Boundary guard

**Files — tạo mới:** `app/tests/test_boundaries.py`

**Việc làm:**
- [ ] Parse AST mọi file trong `app/domain/` và `app/ports/`; fail nếu import
      `langgraph|mlflow|boto3|sqlalchemy|psycopg|fastapi` (NFR-004)
- [ ] Chạy được kể cả khi thư mục còn ít file — nó là hàng rào cho toàn bộ phase sau

**Smoke test:** `pytest app/tests/test_boundaries.py -q` → expected: pass

**Estimate:** 30 min · **LOC:** 0 production (+100 test)

---

### Phase B — Run + Frozen Manifest + LangGraph (8,5h)

#### Step B1 — vgov-runtime: LangGraph graph + server

**Files — tạo mới:** `runtime/graph.py`, `runtime/server.py`

**Việc làm:**
- [ ] StateGraph 3 node `parse_rd → generate_bd → review_bd` đúng `[SD §7]`
- [ ] Prompt template lấy **từ `StartRunRequest`**; runtime **tuyệt đối không** gọi MLflow Prompt Registry
- [ ] `StartRunRequest` **không có** `business_key` — runtime chỉ trả nội dung `[SD §3.1]`
- [ ] `POST /runs` sinh `runtime_run_id`, chạy background, trả handle ngay; `GET /runs/{id}` trả status
- [ ] Khi xong `POST {callback_url}` kèm header `Idempotency-Key: {correlation_id}`, retry backoff 3
      lần; nhận 409 `CALLBACK_IN_PROGRESS` thì retry, nhận 200 thì dừng
- [ ] LLM qua NVIDIA OpenAI-compatible endpoint, model name lấy từ request

**Smoke test:**
```bash
curl -X POST localhost:8811/runs -H 'Content-Type: application/json' -d @scratch/start_req.json
```
→ expected: 202 + `runtime_run_id`; sau ~30s callback tới vgov-api với BD Markdown không rỗng

**Estimate:** 150 min · **LOC:** 600 adapter

---

#### Step B2 — Ports + LangGraphRuntimeAdapter + MLflowPromptAdapter

**Files — tạo mới:**
- `app/ports/runtime.py`, `app/ports/prompt_registry.py`
- `app/adapters/langgraph_runtime.py`, `app/adapters/mlflow_prompt.py`
- **Test:** `app/tests/test_adapters.py`

**Việc làm:**
- [ ] Port đúng signature `[SD §3.1–3.2]`, DTO thuần dataclass
- [ ] `resume`/`cancel` raise `RuntimeCapabilityNotSupported` (FR-ADP-003)
- [ ] `get_status()` implement thật — cần cho reconciliation `[SD §4.1]`, không phải trang trí
- [ ] Status mapping đúng bảng `[SD §3.1]`; status lạ → FAILED + `error_code=RUNTIME_STATUS_UNKNOWN`
- [ ] `MLflowPromptAdapter.resolve()` trả `version: int`; không resolve được → `PromptResolutionError`

**Smoke test:** `pytest app/tests/test_adapters.py -q` → expected: resolve alias `production` trả
`version=1` dạng int; runtime status `error` map thành `FAILED`; `resume()` raise đúng exception

**Estimate:** 90 min · **LOC:** 700 adapter (+150 test)

---

#### Step B3 — Run service: freeze-then-execute

**Files — tạo mới:**
- `app/domain/run.py`, `app/domain/manifest.py`, `app/services/run_service.py`, `app/api/runs.py`
- `scripts/demo_seed.py` — seed MLflow prompt v1/v2 + publish release + trỏ PROD + upload RD rev 1/2
- **Test:** `app/tests/test_freeze_order.py`, `test_fail_closed.py`, `test_no_alias.py`

**Files — sửa:** `app/persistence/repositories.py`

**Việc làm:**
- [ ] Implement đúng 13 bước `[SD §4]`, **không đảo thứ tự**
- [ ] `POST /runs` nhận `output_business_key` từ client, lưu vào `execution_run` `[SD §2.4]`
- [ ] `manifest_hash` = sha256 của JSON canonical (`sort_keys=True`, `separators=(',',':')`, UTF-8)
      gồm release_id, git_commit, model_profile, runtime_adapter_id, input_hash + component đã sort
      theo `(kind, ref)`
- [ ] Phân định status lỗi đúng bảng `[SD §4]`: bước 2–7 fail → `FAILED_PRECONDITION` không manifest;
      bước 8 fail → `FAILED` **giữ** manifest
- [ ] `POST /inputs` upload RD → sha256 → `artifact_revision` origin `IMPORTED` (Q1)
- [ ] `demo_seed.py` chạy được độc lập, idempotent (chạy 2 lần không tạo trùng)

**Smoke test:**
```bash
python harness/version-governance/scripts/demo_seed.py && pytest harness/version-governance/app/tests/test_freeze_order.py harness/version-governance/app/tests/test_fail_closed.py harness/version-governance/app/tests/test_no_alias.py -q
```
→ expected: pass. `test_freeze_order` dùng spy adapter assert `run_manifest` đã tồn tại trong DB
**trước** khi `start()` được gọi (DoD #2, #4). `test_no_alias` assert không component nào có
`exact_version` chứa alias.

**Estimate:** 180 min · **LOC:** 900 backend + 150 script (+350 test)

---

#### Step B4 — Callback idempotent + reconciliation

**Files — sửa:** `app/services/run_service.py`, `app/api/runs.py`
**Files — tạo mới:** `app/tests/test_callback_idempotent.py`, `app/tests/test_reconcile.py`

**Việc làm:**
- [ ] Thứ tự 4 bước `[SD §4.2]`: **claim trước, xử lý sau, ghi response cuối**. Claim phải là bước
      đầu tiên — nếu claim ở cuối thì hai callback song song đều chạy hết phần xử lý rồi mới phát
      hiện trùng, chống trùng vô tác dụng
- [ ] `rowcount == 0` + `response_body IS NULL` → 409 `CALLBACK_IN_PROGRESS`; có response → 200 trả
      lại bản cũ
- [ ] `GET /runs/{id}` khi status `RUNNING` → gọi `get_status()`, terminal mà chưa có callback thì
      đóng run với `error_code=CALLBACK_LOST` `[SD §4.1]`
- [ ] Toàn bộ callback trong **một** transaction

**Smoke test:**
```bash
pytest harness/version-governance/app/tests/test_callback_idempotent.py harness/version-governance/app/tests/test_reconcile.py -q
```
→ expected: gửi callback 3 lần → đúng 1 `artifact_revision`; 2 callback song song → 1 thành công + 1
nhận 409; run `RUNNING` không callback → `GET` đóng nó với `CALLBACK_LOST`

**Estimate:** 90 min · **LOC:** 250 backend (+250 test)

---

### Phase C — Artifact + Revision + MinIO (5h) → **demo chạy được lần đầu**

#### Step C1 — BlobStorePort + MinioBlobAdapter

**Files — tạo mới:** `app/ports/blob_store.py`, `app/adapters/minio_blob.py`, `app/tests/test_blob.py`

**Việc làm:**
- [ ] Key content-addressed `{project_key}/{artifact_type}/{business_key}/{sha256}.md`
- [ ] `put_immutable` gọi `exists()` trước; key đã có → trả `BlobRef` cũ, **không ghi đè** (NFR-009)

**Smoke test:** `pytest app/tests/test_blob.py -q` → expected: put 2 lần cùng nội dung → 1 object,
cùng URI

**Estimate:** 60 min · **LOC:** 200 adapter (+100 test)

---

#### Step C2 — Artifact service + revision chain

**Files — tạo mới:**
- `app/domain/artifact.py`, `app/services/artifact_service.py`, `app/api/artifacts.py`
- `scripts/demo_run.py` — chạy 1 scenario end-to-end qua REST API
- **Test:** `app/tests/test_revision_race.py`

**Việc làm:**
- [ ] Callback thành công → `put_immutable` → INSERT `artifact` (theo
      `execution_run.output_business_key`, không phải từ payload runtime) + `artifact_revision`
      origin `AI_GENERATED`
- [ ] `revision_no` cấp theo `[SD §4.3]`: `SELECT ... FOR UPDATE` trên row `artifact` rồi mới
      `max+1`; dính `23505` thì retry tối đa 3 lần
- [ ] `POST /revisions/{id}/edit` → revision mới origin `HUMAN_EDITED`, `parent_revision_id` trỏ bản
      cũ (FR-ART-005)
- [ ] `GET /revisions/{id}/content` stream từ MinIO

**Smoke test:**
```bash
python harness/version-governance/scripts/demo_run.py --scenario A
```
→ expected: file BD Markdown thật trong MinIO; `content_hash` trong DB khớp sha256 của nội dung tải
về. Và `pytest app/tests/test_revision_race.py -q` → 2 callback đồng thời cho `revision_no` 1 và 2.

> `demo_seed.py` đã có từ Step B3 — chạy nó trước `demo_run.py`.

**Estimate:** 150 min · **LOC:** 700 backend + 150 script (+150 test)

---

#### Step C3 — Approved Baseline

**Files — tạo mới:** `app/domain/baseline.py`, `app/services/baseline_service.py`,
`app/api/baselines.py`, `app/tests/test_baseline.py`

**Việc làm:**
- [ ] `POST /baselines` trong **một** transaction: `UPDATE ... SET active=false` row cũ → INSERT row
      mới với `superseded_baseline_id` trỏ row cũ (FR-BASE-004)
- [ ] Trigger `trg_baseline_pointer_only` chỉ cho `active` đi `true → false`; mọi cột khác bất biến
- [ ] Không code path nào tự set baseline từ latest revision (FR-BASE-003)

**Smoke test:** `pytest app/tests/test_baseline.py -q` → expected: ép 2 active baseline cùng
`(artifact, scope)` → `uq_baseline_active` reject; sửa `artifact_revision_id` của baseline cũ → `VG409`

**Estimate:** 90 min · **LOC:** 400 backend (+150 test)

---

### Phase D — Lineage + Explain Difference (4h)

#### Step D1 — Lineage query

**Files — tạo mới:** `app/domain/lineage.py`, `app/services/lineage_service.py`,
`app/api/lineage.py`, `app/tests/test_lineage.py`

**Việc làm:**
- [ ] Một query JOIN trả upstream chain `[SD §2.9]`; đệ quy chỉ khi đi ngược `parent_revision_id`
- [ ] **Không** tạo bảng lineage (FR-LIN-002)

**Smoke test:** `pytest app/tests/test_lineage.py -q` → expected: từ revision lấy được đủ run →
manifest → release → prompt version → git commit → input hash

**Estimate:** 90 min · **LOC:** 400 backend (+150 test)

---

#### Step D2 — Explain Difference

**Files — tạo mới:** `app/domain/difference.py`, `app/services/difference_service.py`,
`app/api/difference.py`, `app/tests/test_difference.py`

**Việc làm:**
- [ ] Thuật toán 6 bước `[SD §5.2]` với **7 category** (thêm `RUNTIME`), output đúng schema `[SD §5.3]`
- [ ] Revision `HUMAN_EDITED` → đi ngược tới tổ tiên `AI_GENERATED` gần nhất, set `human_edit=True`.
      Đi hết chuỗi mà gốc là `IMPORTED` → 422 `NO_MANIFEST_FOR_REVISION`
- [ ] Revision `IMPORTED` → 422 `NO_MANIFEST_FOR_REVISION`
- [ ] Output có `artifact_id` mỗi bên + cờ `same_artifact`
- [ ] Deterministic tuyệt đối: sort cố định, không wall-clock, không random, **không LLM** (FR-DIF-003)

**Smoke test:**
```bash
pytest harness/version-governance/app/tests/test_difference.py -q
```
→ expected: kịch bản `[PB §9]` — A vs B chỉ `PROMPT` changed (`1 → 2`), 6 category còn lại unchanged;
A vs C có **đồng thời** `INPUT` và `PROMPT` changed. Gọi 2 lần cho ra byte-identical output.

**Estimate:** 150 min · **LOC:** 500 backend (+300 test)

---

### Phase E — UI trong web-v3 (7h)

#### Step E1 — Hub proxy

**Files — sửa:** `harness/hub/server.py`, `harness/hub/config.py`, `harness/hub/requirements-hub.txt`
**Files — tạo mới:** `harness/hub/tests/test_vgov_proxy.py`

**Việc làm:**
- [ ] Thêm `httpx` vào `requirements-hub.txt` — **chỉ** dependency này, không psycopg/mlflow/langgraph
- [ ] `@app.api_route("/api/vgov/{path:path}", methods=["GET","POST","PUT","DELETE"])` đặt sau nhóm
      artifacts (~line 1302), theo đúng pattern `@app.<verb>` phẳng hiện có
- [ ] `VGOV_BASE_URL` trong `config.py`, default `http://127.0.0.1:8810`
- [ ] vgov down → trả 502 `RUNTIME_UNAVAILABLE`, hub **không** crash

**Smoke test:**
```bash
pytest harness/hub/tests -q
```
→ expected: **toàn bộ test suite hiện có của hub vẫn pass** + test proxy mới. Tắt compose →
`curl localhost:8799/api/vgov/health` → 502, hub vẫn sống.

**Estimate:** 60 min · **LOC:** 60 UI (+80 test)

---

#### Step E2 — API client + 5 page

**Files — tạo mới:** `harness/hub/web-v3/src/lib/vgovApi.ts`, `src/pages/VgovReleasesPage.tsx`,
`VgovRunPage.tsx`, `VgovOutputPage.tsx`, `VgovProvenancePage.tsx`, `VgovComparePage.tsx`
**Files — sửa:** `src/pages/index.tsx` (đăng ký route), `src/components/Sidebar.tsx` (nav)

**Việc làm:**
- [ ] Dùng lại `lib/api.ts`, `lib/sse.ts`, `styles/tokens.css` — **không** thêm dependency npm mới
- [ ] Điều hướng theo `[ADR-009]`: Project → Workflow → Run → Output → History/Compare/Approve.
      Release/Manifest/Component chỉ hiện ở màn Provenance qua progressive disclosure (FR-UX-006)
- [ ] Màn Run: chọn RD input đã import + chọn environment + **nhập `output_business_key`**, bấm Run,
      poll status
- [ ] Màn Compare: chọn 2 output, render bảng Changed/Unchanged 7 category đúng dạng `[PB §9]`

**Smoke test:**
```bash
pnpm --dir harness/hub/web-v3 build
```
→ expected: build pass (gồm `check-encoding.mjs` + `tsc -b`). Mở `localhost:8799`, chạy đủ 5 bước UX
`[PB §7]` không cần Swagger.

**Estimate:** 300 min · **LOC:** 1.750 UI

---

#### Step E3 — Human edit trên UI

**Files — sửa:** `VgovOutputPage.tsx`

**Việc làm:**
- [ ] Edit nội dung revision → `POST /revisions/{id}/edit` → revision mới `HUMAN_EDITED` (Q8)
- [ ] Nút Approve → `POST /baselines`

**Smoke test:** edit output, mở Compare giữa revision AI và revision human → category `HUMAN_EDIT`
báo changed

**Estimate:** 60 min · **LOC:** 150 UI

---

### Phase F — Integration Test + DoD (2h)

#### Step F1 — verify_dod

**Files — tạo mới:** `harness/version-governance/verify_dod.py`

**Việc làm:**
- [ ] Chạy tự động 12 mục `[PB §10]`, in bảng pass/fail
- [ ] Dùng lại `scripts/demo_seed.py` (Step B3) và `scripts/demo_run.py` (Step C2), không viết lại

**Test cases:**
- [ ] Happy path: `python verify_dod.py` → 12/12 pass
- [ ] Edge case: xóa alias `production` trong MLflow rồi start run → 422 `PROMPT_UNRESOLVED`,
      **không** có row `run_manifest`
- [ ] Error case: `docker compose stop vgov-runtime` rồi start run → run `FAILED` với
      `error_code=RUNTIME_UNAVAILABLE`, manifest **vẫn tồn tại** — đã freeze trước khi gọi runtime,
      đây là hành vi đúng thiết kế `[SD §4]`, không phải rác
- [ ] Callback lost: kill vgov-runtime giữa chừng → `GET /runs/{id}` đóng run với `CALLBACK_LOST`
- [ ] Reproducibility: chạy Run A hai lần → hai `manifest_hash` bằng nhau (NFR-006, DoD #12)

**Estimate:** 120 min · **LOC:** 250 script

---

## Thứ tự phụ thuộc

```text
A0 → A1 → A2 → A3 → A4
                 ↓
           B1 → B2 → B3 → B4
                          ↓
                    C1 → C2 → C3        ← demo chạy được lần đầu
                              ↓
                        D1 → D2
                              ↓
                    E1 → E2 → E3
                              ↓
                             F1
```

**Đã kiểm chứng: không step nào dùng output của step sau.** Cụ thể:

| Tài nguyên | Tạo ở | Dùng lần đầu ở |
|---|---|---|
| `conftest.py`, `test_immutability.py`, `test_rollback.py` | A3 | A3 |
| `test_boundaries.py` | A4 | A4 |
| `scripts/demo_seed.py` | B3 | B3 |
| `scripts/demo_run.py` | C2 | C2 |
| `verify_dod.py` | F1 | F1 |

Mỗi step chỉ chạy smoke test trên file do **chính nó hoặc step trước** tạo ra.

---

## Rollback Plan

| Fail ở | Rollback |
|---|---|
| Phase A | `docker compose down -v` (xóa volume). Xóa `harness/version-governance/{app,runtime,deploy,scripts}`. Không đụng gì của hub. |
| Phase B–D | `alembic downgrade -1`, `docker compose restart vgov-api`. Code trong git branch riêng. |
| Phase E | Revert `harness/hub/server.py`, `config.py`, `requirements-hub.txt`; xóa page mới + entry trong `pages/index.tsx`, `Sidebar.tsx`, `tests/test_vgov_proxy.py`. **Đây là các file duy nhất của hub bị đụng** — rollback sạch. |

Toàn bộ công việc nằm trên branch riêng, không merge vào `main` cho tới khi F1 pass.

---

## Kết quả chạy thật — 2026-08-03

```text
Definition of Done
 1. PASS  Release exact 40-hex + immutable
 2. PASS  Run persisted before runtime start
 3. PASS  PROMPT component pins numeric exact version
 4. PASS  Manifest frozen before start + immutable
 5. PASS  Output BD Markdown non-empty
 6. PASS  Revision hash matches content + source run
 7. PASS  Lineage reaches input hash
 8. PASS  Same input runs prompt v1 and v2
 9. PASS  A vs B only changes PROMPT
10. PASS  No prompt-publishing endpoint in vgov
11. PASS  No standalone governance frontend
12. PASS  Repeated Run A has identical manifest hash

12/12 PASS

Error cases (informational)
- alias removed: HTTP 422, code=PROMPT_UNRESOLVED, manifests=0
- runtime stopped: HTTP 502, code=RUNTIME_UNAVAILABLE, run=FAILED:RUNTIME_UNAVAILABLE, manifests=1
- callback lost: covered by tests/test_reconcile.py
```

### Bug thật tìm được khi chạy, không phải khi viết test

| # | Bug | Hệ quả nếu bỏ sót |
|---|---|---|
| 1 | `mlflow.genai.load_prompt` **cache alias trong process** | vgov-api sống lâu → Frozen Run Manifest ghi **sai** prompt version mỗi khi alias bị di chuyển từ ngoài. Hỏng **âm thầm**: manifest vẫn hợp lệ schema. Phá FR-MAN-001 + DoD #3 — tức phá luận điểm trung tâm của POC. Sửa: dùng `MlflowClient.get_prompt_version_by_alias` |
| 2 | `httpx` mặc định timeout 5s, `start()` lần đầu vượt ngưỡng | run bị đánh `FAILED`, runtime vẫn chạy tiếp rồi callback ghi đè `SUCCEEDED` — cửa sổ race thật. Sửa: timeout tường minh 60s |
| 3 | Thiếu env `MLFLOW_TRACKING_URI` (chỉ có `VGOV_MLFLOW_TRACKING_URI`) | `mlflow.set_experiment` ghi vào `./mlruns` trong container, `trace_id` trỏ vào hư không — DoD về trace reference đỗ giả |
| 4 | `artifact_service(session: Session)` dùng làm `Depends` mà không có `Depends(get_session)` | FastAPI crash lúc khởi động |
| 5 | minio healthcheck dùng `wget` (image chỉ có `curl`) | cả chain `depends_on` không bao giờ khởi động |
| 6 | mlflow `start_period: 10s` < ~2 phút boot | container bị đánh `unhealthy` trước khi kịp sẵn sàng |
| 7 | Thiếu `ENV PYTHONPATH=/app` | alembic `ModuleNotFoundError: persistence` |
| 8 | Image mlflow gốc thiếu `psycopg2-binary` + `boto3` | mlflow crash với backend Postgres + artifact S3 |

Bug #1 chỉ lộ ra vì chạy demo scenario B **thật** rồi đối chiếu DB — không test nào bắt được, vì test
dùng fake adapter.

---

## Checklist trước khi Done

- [x] Tất cả smoke test từng step pass
- [x] **52 FR** trong RD đều có implementation (REL 4 · ENV 4 · RUN 4 · MAN 5 · ADP 8 · ART 7 ·
      BASE 5 · LIN 3 · DIF 4 · UX 8) — đối chiếu từng ID
- [x] 9 NFR không cái nào bị vi phạm — đặc biệt NFR-004 (`test_boundaries.py` xanh)
- [x] `verify_dod.py` 12/12 pass
- [x] Toàn bộ test suite hiện có của hub vẫn pass
- [x] Không hardcoded credential — mọi secret qua `.env`, `.env` không commit
- [x] Đếm LOC production, đối chiếu 8.000–15.500 `[PB §12]`
- [x] Không capability nào trong `[RD §4 Explicit Exclusions]` bị implement lén
- [x] BD doc updated — các step marked ✅

---

## Nguyên tắc cho Codex khi implement

1. **Không tự đổi thiết kế.** Gặp blocker kỹ thuật → báo lại, không tự quyết scope change.
2. **Không thêm capability ngoài RD.** Danh sách cấm ở `[RD §4]`. Muốn thêm → phải có ADR mới.
3. **Không sửa file của hub ngoài Step E1–E2** (`server.py`, `config.py`, `requirements-hub.txt`,
   `pages/index.tsx`, `Sidebar.tsx`, `tests/test_vgov_proxy.py` và các page mới).
4. **Không import vendor SDK ngoài `app/adapters/`.** `test_boundaries.py` sẽ fail.
5. **Không lưu alias vào manifest.** DB constraint sẽ reject, nhưng đừng để tới đó mới biết.
6. **Viết test cùng lúc với code** — mọi step đều đã liệt kê file test của nó trong "Files — tạo mới".

---

## Changelog

**v1.1 — 2026-08-02, sửa theo review độc lập:**

| # | Sửa |
|---|---|
| 1 | **Vi phạm thứ tự phụ thuộc:** A3 chạy `test_immutability.py`/`test_rollback.py` do A4 tạo; C2 chạy `demo_run.py` do F1 tạo. Chuyển test về A3, `demo_seed.py` về B3, `demo_run.py` về C2. Thêm bảng kiểm chứng "tạo ở đâu / dùng ở đâu" |
| 2 | **Mọi step giờ liệt kê file test của nó.** v1 tham chiếu 6 file test (`test_adapters`, `test_callback_idempotent`, `test_blob`, `test_baseline`, `test_lineage`, `test_difference`) mà không step nào tạo — mâu thuẫn nguyên tắc #6 |
| 3 | **Số học LOC sai:** A2 ghi "~600 (500 + 450)"; bucket migration/config 900 nhưng step cộng ra 1.200; UI 1.810 nhưng step cộng ra 1.960. Tính lại toàn bộ, thêm bảng cộng dồn theo step. Tổng 8.470 → **9.360** |
| 4 | **Giờ theo phase sai:** header Phase A "~6h" nhưng step cộng ra 8h. Sửa mọi header; tổng 33h → **34,5h** |
| 5 | Checklist "44 FR" → **52 FR** (đếm lại theo nhóm) |
| 6 | Bỏ con số cứng "235 test" của hub — số thật khác; dùng "toàn bộ test suite hiện có" |
| 7 | Thêm A0 verify image mlflow; A1 thêm `deploy/mlflow.Dockerfile`; B4 thêm reconciliation; C2 thêm khóa `revision_no`; D2 lên 7 category — theo SD v1.1 |

---

*Version Governance POC — BD v1.1 | 2026-08-02*
