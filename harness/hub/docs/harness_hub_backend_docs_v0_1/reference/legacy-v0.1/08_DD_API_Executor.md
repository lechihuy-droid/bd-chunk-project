# Detailed Design — API Executor

> Superseded by `../../design/D04_GATEWAY_EXECUTOR_AND_PROVIDERS.md`.

| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-DD-APIEXEC-001 |
| Version | 0.2 |
| Status | Draft — merged from research |
| Depends on | Unified Executor Contract v0.2, Runtime Gateway and Routing |
| Research sources | HH-RES-R01, HH-RES-R02 |
| Last updated | 2026-07-27 |

## 1. Mục tiêu

API Executor thực thi `ExecutionRequest` qua HTTP model/provider API và trả normalized `ExecutionEvent`/`ExecutionResult`. Adapter không sở hữu routing, workflow retry hoặc tool execution.

## 2. Composition

```text
ApiExecutor
  ├─ HttpTransport
  ├─ ProviderProtocol
  ├─ StreamParser
  ├─ UsageNormalizer
  ├─ ErrorMapper
  └─ CredentialInjector
```

Provider protocol chuyển portable request sang provider payload; transport chỉ quản lý HTTP lifecycle.

## 3. Pipeline

```text
validate contract/capability
→ resolve credential references
→ build provider request
→ apply deadline and transport retry policy
→ send/stream HTTP
→ normalize deltas, usage and tool-call requests
→ validate final output
→ produce terminal event/result
→ dispose credentials and connection
```

## 4. Provider capability manifest

Mỗi API adapter khai báo:

- model IDs và contract versions;
- streaming/tool/structured-output/vision support;
- max context/output;
- cancellation semantics;
- usage/cost reporting;
- residency/endpoint classification;
- provider-specific config schema.

Gateway phải validate capability trước submit.

## 5. Streaming

- Provider SSE/chunk được parse thành `message.delta`, `reasoning.delta`, `usage.updated`.
- Chỉ một terminal event: completed, failed, cancelled hoặc timed out.
- Malformed frame tạo `PARSE`/`CONTRACT` error; không đưa raw frame nhạy cảm ra UI.
- Client disconnect được Gateway chuyển thành cancel; adapter abort HTTP request.
- Partial output được lưu bằng reference và đánh dấu incomplete; không silent fallback.

## 6. Retry

Adapter chỉ retry bounded transport errors trên cùng provider:

- retry: connection reset, 429 theo `Retry-After`, 502, 503, 504;
- không retry: 400/404/410/422, authentication, capability, policy, contract;
- deadline tổng không được gia hạn bởi retry;
- mỗi transport attempt phải ghi telemetry;
- hết retry trả normalized error; Runtime/Gateway quyết định workflow retry/fallback.

## 7. Tool calls

Adapter phát `tool.call.requested`. Policy/Tool Executor quyết định. Adapter không tự chạy arbitrary tool hoặc gửi tool result giả. Tool call ID phải được giữ xuyên suốt request/result.

## 8. Security

- Request chỉ chứa credential reference.
- Credential resolve ngay trước call và không ghi log.
- Authorization header, provider payload và prompt được redact theo policy.
- Endpoint phải nằm trong provider registry/allow-list.
- Restricted data bị chặn nếu provider/residency không phù hợp.
- Provider output là untrusted và phải qua output contract/security scan trước publish.

## 9. Error mapping

Mọi provider adapter map về Executor Error Taxonomy. Result giữ `provider_request_id`, status và safe details reference; không expose stack trace hoặc raw credential-bearing response.

## 10. Observability

Ghi provider/model, request/execution IDs, time-to-first-event, duration, status, token/cost, retry count, cancel, normalized error. Không log prompt/output mặc định.

## 11. Conformance tests

- fake HTTP success, stream và non-stream;
- malformed SSE/JSON;
- retry/backoff và `Retry-After`;
- timeout/deadline;
- cancellation/client disconnect;
- usage normalization;
- tool-call normalization;
- credential/log redaction;
- capability mismatch;
- exactly-one-terminal-event.

## 12. Acceptance

- Ít nhất hai API/provider adapters hoặc một adapter + conformance fake pass cùng contract.
- Runtime không import provider-specific protocol.
- Streaming/cancel/timeout/usage hoạt động theo contract.
- Không có secret trong event, log hoặc result.
