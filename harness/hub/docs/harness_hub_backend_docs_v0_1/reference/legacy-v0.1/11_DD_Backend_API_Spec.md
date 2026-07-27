# Detailed Design — Backend API Specification

> Superseded by `../../design/D05_API_AND_STORAGE_CONTRACTS.md`.

| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-DD-API-001 |
| Version | 0.2 |
| Status | Draft |
| Depends on | Runtime Gateway, Executor Contract, Workflow Runtime, Artifact Store |
| Research source | HH-RES-R01 |
| Last updated | 2026-07-27 |

## 1. Conventions

Target base path: `/api/v1`. Existing unversioned Hub endpoints remain compatibility routes until UI migration.

Headers for state-changing requests:

```text
X-Correlation-Id: <uuid>
Idempotency-Key: <key>
If-Match: <resource-version-or-hash>
X-Hub-Client: harness-hub
```

Authentication/workspace headers are deferred for local single-user mode; schema reserves `principal_ref` and `workspace_ref`.

Error envelope:

```json
{
  "error": {
    "code": "STABLE_CODE",
    "message": "safe message",
    "correlation_id": "uuid",
    "retryable": false,
    "details": {}
  }
}
```

## 2. Gateway execution API

```text
POST /gateway/executions
GET  /gateway/executions/{execution_id}
GET  /gateway/executions/{execution_id}/stream
POST /gateway/executions/{execution_id}/cancel
GET  /gateway/executors
GET  /gateway/models
```

`POST` nhận portable gateway request, trả `202` cùng execution handle. SSE stream dùng normalized ExecutionEvent. Endpoint không nhận raw API key, unrestricted env hoặc arbitrary working directory.

OpenAI-compatible `/v1/chat/completions` MAY là compatibility facade cho chat, nhưng phải chuyển vào cùng Gateway contract và không bypass policy/router.

## 3. Workflows và runs

```text
GET/POST /workflows
GET/PUT  /workflows/{id}
POST     /workflows/validate
POST     /workflows/{id}/runs
GET      /runs/{id}
GET      /runs/{id}/events
POST     /runs/{id}/pause
POST     /runs/{id}/resume
POST     /runs/{id}/cancel
```

Workflow save yêu cầu `If-Match`; stale write trả `409`. Create/resume/cancel idempotent.

## 4. Review và human task

```text
GET  /review-requests
GET  /review-requests/{id}
POST /review-requests/{id}/approve
POST /review-requests/{id}/request-changes
```

Decision body gồm expected version, reason và actor reference. Duplicate decision trả result cũ hoặc conflict, không apply hai lần.

## 5. Artifacts

```text
GET  /artifacts
GET  /artifacts/{id}
GET  /artifacts/{id}/versions
POST /artifacts/{id}/archive
POST /artifacts/{id}/restore
GET  /artifact-versions/{a}/diff/{b}
```

Content response có checksum/media type; immutable version không có update endpoint.

## 6. Streaming

- SSE event ID hỗ trợ resume/replay.
- Event envelope giữ execution/run/node/attempt correlation.
- Client disconnect trigger cancellation chỉ khi endpoint contract quy định.
- Runtime stream và execution stream giữ namespace riêng.

## 7. Status codes

- `200`: query/idempotent replay thành công.
- `201`: resource tạo đồng bộ.
- `202`: execution/run nhận để xử lý.
- `400`: malformed request.
- `401/403`: authentication/policy.
- `404`: resource không tồn tại.
- `409`: stale version/idempotency conflict/invalid transition.
- `422`: schema/contract violation.
- `429`: rate/budget limit.
- `503`: provider/executor unavailable.

## 8. Acceptance

- OpenAPI mô tả đầy đủ request/response/error/status.
- State mutation có idempotency và concurrency token.
- Chat facade không bypass Gateway.
- SSE events validate theo schema.
- Compatibility tests bảo vệ UI hiện tại trong thời gian migration.
