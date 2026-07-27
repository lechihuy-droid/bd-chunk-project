# D05 — API and Storage Contracts

```yaml
document_id: HH-DES-D05
version: 1.1
status: In Review
owner: Backend
depends_on: [D02, D03, D04, D06]
research_sources: [HH-RES-R03, HH-RES-R07]
```

## 1. API conventions

As-is routes dùng `/api`. Target v1 giữ path để không phá UI; payload mới có `schema_version: 1`. Việc chuyển `/api/v1` là OD-01.

- JSON UTF-8; timestamps UTC ISO-8601.
- Request correlation: `X-Correlation-ID`, server tạo nếu thiếu.
- State command: `Idempotency-Key` và `If-Match: "<version>"`.
- Collection response: `{items, next_cursor, total?}`; cursor opaque.
- Error response:

```json
{
  "error": {
    "code":"STALE_RUN_VERSION",
    "message":"Run changed; refresh and retry.",
    "correlation_id":"corr-...",
    "details":{"current_version":8}
  }
}
```

Không trả stack trace, secret, provider raw body hoặc host path.

## 2. Authorization baseline

Target local v1 có principal `local_user`, nhưng CSRF/origin và path boundary vẫn bắt buộc. API bind loopback mặc định. Endpoint execution/state change không được expose public network nếu chưa có authentication ADR.

## 3. Workflow API

| Method/path | Contract | Success | Errors |
|---|---|---|---|
| `GET /api/workflows` | list metadata | 200 | 500 |
| `GET /api/workflows/{id}/source` | YAML + version/hash | 200 | 404 |
| `POST /api/workflows/validate` | `{yaml_text}` | 200 `{valid,errors,normalized?}` | 400 malformed request |
| `PUT /api/workflows/{id}` | YAML/model + expected hash | 200 saved definition | 400/404/409/422 |
| `GET/PUT /api/workflows/{id}/layout` | visual coordinates only | 200 | 400/404 |
| `POST /api/workflows/{id}/runs` | objective/thread/idempotency | 202 SSE hoặc run reference | 404/409/422 |

Save workflow ghi backup hoặc atomic replace; workflow validation phải hoàn tất trước write. Layout không thay đổi semantic version/hash.

## 4. Run/interrupt API

| Method/path | Ý nghĩa |
|---|---|
| `GET /api/agent/runs` | list runtime runs |
| `POST /api/agent/runs` | create managed agent run |
| `GET /api/agent/runs/{id}` | run projection + version |
| `GET /api/agent/runs/{id}/events` | paged events hoặc SSE-compatible list |
| `POST /api/agent/runs/{id}/interrupts/{iid}/resume` | idempotent resolve |
| `POST /api/workflows/runs/{id}/interrupts/{iid}/resume` | workflow alias; cùng command service |
| `GET /api/workflows/runs/{id}/artifacts` | manifests |

Hai resume endpoint MUST đi chung một application command; không duplicate business logic.

State command:

- `202` khi accepted nhưng chưa terminal.
- `200` khi synchronous command hoàn tất hoặc replay idempotent response.
- `409` stale version/idempotency conflict/invalid state.
- `422` payload hợp lệ JSON nhưng contract sai.

## 5. SSE contract

Headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, disable proxy buffering.

```text
id: 12
event: attempt.progress
data: {"schema_version":1,"event_id":"evt-...","run_id":"run-...","sequence":12,"payload":{}}

```

- Client reconnect gửi `Last-Event-ID`.
- Server replay derived event timeline sau cursor rồi tiếp tục live stream. Nếu timeline thiếu nhưng transaction đã commit, event được regenerate trước khi stream.
- Heartbeat comment tối đa mỗi 15 giây idle.
- Terminal stream luôn có `run.succeeded|failed|cancelled`.
- Lỗi sau khi headers gửi phải là event `error`, không giả HTTP 500.
- Slow client có bounded buffer; overflow disconnect với resumable cursor.

## 6. Existing non-runtime APIs

Chat, jobs, suites, usage, sessions, skills, memory, guardrails và inspect giữ API hiện tại. Khi sửa, chúng tuân conventions chung nhưng không bị ép vào WorkflowRun aggregate. `gitjobs` không được tái sử dụng như Executor nếu chưa qua D04/D06 contract.

## 7. Runtime storage layout

```text
runtime/
  threads/thread-<id>/
    state.json
    checkpoints/
    uploads/
    workspace/
    outputs/
  runs/run-<id>/
    run.json
    transactions/<state-version>-<transaction-id>/<phase>.json
    definition.snapshot.yaml
    agents.snapshot.json
    events.jsonl
    checkpoints/
    attempts/<node-id>/<attempt-no>.json
    artifacts/
      manifest.json
      <artifact-id>/<version>/content
  store/
    idempotency/
    quarantine/
```

Caller không điều khiển absolute path. Mọi ID/path qua canonical resolver và symlink boundary check.

## 8. Atomicity và locking

- Mutable JSON: write sibling temp, flush, replace.
- Mutable runtime command dùng immutable checksummed transaction phase records + committed projection; replace một file không được coi là transaction.
- JSONL event là derived timeline; append dưới per-run lock, phát hiện torn tail và có journaled quarantine/repair.
- Command sequence trong một run dưới keyed lock.
- Artifact content ghi temp, hash/scan, rename immutable, rồi update manifest.
- Crash giữa content và manifest: orphan scanner quarantine; không expose artifact chưa manifest.

Target v1 chỉ support một server process. `--workers > 1` là unsupported cho runtime mutation đến khi có cross-process lock/storage ADR.

Recovery không chọn transaction theo timestamp/creation order. Record phải chứa prior/target state version và previous hash; fork/gap/corrupt chain fail closed.

`flush`/`fsync`/replace chỉ được claim theo durability envelope đã kiểm chứng bằng R03 probes trên supported Windows/Python/NTFS profile. Manifest có content bị mất/hash mismatch sau recovery là corruption và bị quarantine.

## 9. Artifact manifest

```json
{
  "schema_version":1,
  "artifact_id":"art-...",
  "version":1,
  "run_id":"run-...",
  "node_id":"draft",
  "attempt_no":1,
  "media_type":"text/markdown",
  "size_bytes":1234,
  "sha256":"...",
  "created_at":"...",
  "lineage":{"inputs":[],"execution_id":"exec-..."},
  "content_path":"artifacts/art-.../1/content",
  "scan_status":"passed"
}
```

Version không overwrite. Archive là projection flag; purge là explicit governed operation. Download kiểm tra manifest, boundary, hash và authorization.

## 10. Retention/backup baseline

Cho đến OD-05:

- không auto-delete active runtime data;
- cache có thể rebuild và không backup;
- workflow/agent definitions, run state/events/checkpoints/artifact manifests/content là backup set;
- secret env và `.env` không nằm trong artifact backup.

## 11. Acceptance

- API contract tests cho status/error/idempotency/stale write.
- SSE reconnect không mất/duplicate state effect.
- Multi-worker mutation bị guard hoặc documented startup failure.
- Path traversal/symlink bị reject.
- Artifact hash/version không đổi sau tạo.
- Crash injection quanh atomic write phục hồi được hoặc quarantine rõ.
- Transaction journal fork/gap/torn-tail tests pass.
- RPO statement không mạnh hơn power-loss experiments đã owner duyệt.
