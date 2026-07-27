# Detailed Design — Runtime Gateway and Routing

> Superseded by `../../design/D04_GATEWAY_EXECUTOR_AND_PROVIDERS.md`.

| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-DD-GATEWAY-001 |
| Document type | Detailed Design |
| Version | 0.1 |
| Status | Draft — merged from research |
| Implementation readiness | Conditional |
| Depends on | HH-ARCH-001, Architecture Principles, Backend Module Map, Executor Contract |
| Research sources | HH-RES-R01, HH-RES-R02 |
| Last updated | 2026-07-27 |

## 1. Mục tiêu và phạm vi

Runtime Gateway là boundary giữa Application/Workflow Runtime và các executor backend. Gateway:

- nhận yêu cầu thực thi độc lập vendor;
- áp dụng policy và resolve logical model/model class;
- chọn một execution route có khả năng đáp ứng;
- chuẩn hóa streaming và lỗi từ executor;
- ghi routing evidence, usage và telemetry.

Gateway không sở hữu workflow state, không chạy agent logic, không thực thi tool và không quản lý nội dung hội thoại dài hạn.

MVP là module trong FastAPI modular monolith. Không tạo gateway service, queue, Redis hoặc cluster riêng.

## 2. Ranh giới trách nhiệm

```text
Application / Workflow Runtime
    → Runtime Gateway
        → Policy evaluation
        → Model & Executor Registry
        → Execution Router
        → Executor Contract
            → API Adapter | CLI Adapter
```

| Thành phần | Sở hữu |
|---|---|
| Runtime | run/node/attempt state, workflow retry, pause/resume/cancel |
| Gateway | policy evaluation, route selection, fallback plan, normalized execution stream |
| Router | deterministic candidate filtering/ranking |
| Executor | một lần thực thi trên backend đã chọn |
| Adapter | transport, provider protocol, parser, provider-local transient retry |
| Registry | model alias, provider, capability, health metadata |

Forbidden dependencies:

- UI/API không gọi provider trực tiếp.
- Gateway không cập nhật run/node state.
- Adapter không chọn workflow node hoặc tự thực thi arbitrary tool.
- Executor không tự đổi provider ngoài route đã được Runtime chấp nhận.

## 3. Gateway request

Gateway nhận `GatewayExecutionRequest`:

```yaml
contract_version: "1.0"
request_id: string
correlation_id: string
idempotency_key: string
run_id: string
node_id: string
attempt_no: integer
model_selector:
  alias: string?
  provider: string?
  model: string?
requirements:
  streaming: boolean
  tools: boolean
  structured_output: boolean
  file_io: boolean
  session_resume: boolean
limits:
  deadline: datetime
  max_output_tokens: integer?
  budget:
    amount_minor: integer?
    currency: string?
security:
  principal_ref: string
  data_classification: PUBLIC | INTERNAL | CONFIDENTIAL | RESTRICTED
  policy_version: string
execution_payload_ref: string
metadata: object
```

Secret value, raw environment variable và arbitrary working directory không được phép xuất hiện trong Gateway request. Chỉ dùng reference đã được Policy Engine chấp nhận.

## 4. Routing precedence

Router áp dụng theo thứ tự:

1. Hard platform/workspace security policy.
2. Data classification và provider residency/allow-list.
3. Capability requirements.
4. Explicit provider/model của user hoặc agent, nếu được policy cho phép.
5. Workflow/model-class default.
6. Provider availability và compatibility.
7. Cost/latency preference.
8. Stable deterministic tie-breaker.

Lower-level preference không được nới lỏng hard policy. Conflict hoặc thiếu capability phải fail closed.

## 5. Routing algorithm

```text
load registry snapshot
→ expand alias/model class thành candidates
→ remove policy-denied candidates
→ remove capability-incompatible candidates
→ remove unavailable/incompatible candidates
→ rank candidates deterministically
→ produce primary route + bounded fallback routes
→ persist RoutingDecision evidence
```

`RoutingDecision` gồm:

```yaml
decision_id: string
request_id: string
registry_version: string
policy_version: string
selected:
  executor_id: string
  provider: string
  model: string
fallbacks: array
rejected_candidates:
  - candidate: string
    reason_code: string
rationale_codes: array
created_at: datetime
```

Không dùng LLM confidence làm routing hoặc security decision.

## 6. Retry và fallback ownership

- Adapter MAY retry lỗi transport tạm thời trên cùng provider trong bounded policy.
- Executor MUST báo mọi attempt transport và kết quả cuối.
- Runtime sở hữu node attempt và workflow retry.
- Gateway tạo fallback plan; Runtime quyết định mở attempt mới trên fallback route.
- Security, authentication, validation, capability và contract error không fallback.
- Sau khi partial output đã được công bố, không silent fallback. Runtime phải đánh dấu partial/incomplete và yêu cầu explicit retry hoặc policy riêng.
- Cùng idempotency key không được tạo execution thứ hai.

## 7. Streaming

Gateway dùng internal async iterator và expose SSE cho client.

Execution events dùng namespace `execution.*`, `message.*`, `usage.*`, `tool.*`; runtime events dùng namespace `run.*`, `node.*`, `review.*`. Hai catalogue không được trộn.

Gateway:

- giữ `event_id`, sequence, execution/run/node/attempt IDs;
- chuyển execution event sang SSE mà không mất correlation;
- áp dụng output-size limit và redaction;
- propagate client disconnect thành cancellation request;
- không coi mất UI stream là mất runtime state.

WebSocket không thuộc MVP.

## 8. State và session

Gateway stateless đối với nội dung hội thoại. `session_id` chỉ là correlation/provider-session reference.

- Runtime giữ message/context cần cho replay.
- Adapter MAY hỗ trợ provider session/resume nếu capability khai báo.
- Sticky CLI session không phải source of truth.
- Mất session phải có thể retry bằng persisted context hoặc trả capability error rõ ràng.

## 9. Error model

Gateway trả normalized error từ Executor Contract và bổ sung routing errors:

- `ROUTE_NOT_FOUND`
- `POLICY_DENIED`
- `CAPABILITY_UNAVAILABLE`
- `PROVIDER_UNAVAILABLE`
- `BUDGET_EXCEEDED`
- `FALLBACK_EXHAUSTED`
- `STALE_REGISTRY_VERSION`

Error gồm `code`, `category`, `retryable`, `user_visible`, `correlation_id`, `details_ref`; không chứa secret hoặc raw provider payload nhạy cảm.

## 10. Observability

Mỗi request ghi:

- request/run/node/attempt/execution/correlation IDs;
- selected route và rejection reason codes;
- provider/model/executor;
- time-to-first-event và total duration;
- input/output tokens và estimated cost;
- retry/fallback/cancel counts;
- terminal status và normalized error code.

Prompt/output không log mặc định. Operational log, runtime event và audit event là ba luồng riêng.

## 11. MVP và non-goals

MVP:

- registry bằng config hiện hữu;
- model class/alias → provider/model;
- capability validation;
- primary route và bounded fallback plan;
- API và local CLI adapters qua Executor Contract;
- SSE, timeout, cancellation và normalized telemetry.

Ngoài MVP:

- multi-tenant RBAC;
- circuit breaker phân tán;
- semantic cache;
- dynamic A/B/canary routing;
- queue/remote workers;
- LiteLLM/Kong/Portkey dependency;
- model-based dynamic routing.

## 12. Acceptance criteria

- Cùng registry/policy/request luôn tạo cùng RoutingDecision.
- Hard policy override explicit model choice.
- Missing capability fail trước execution.
- Adapter transport retry không tạo workflow attempt mới.
- Fallback chỉ chạy bằng attempt mới do Runtime tạo.
- Partial stream không silent fallback.
- Client disconnect propagate cancel.
- Routing evidence và usage truy vết được nhưng không lộ secret/prompt.

## 13. Traceability

Nguồn nghiên cứu:

- HH-RES-R01: gateway boundary, routing, streaming, reliability, observability.
- HH-RES-R02: capability model, executor/adapter boundary, cancellation.

Điểm đã hiệu chỉnh:

- policy precedence đặt hard security lên trên user choice;
- retry ownership tách adapter, Gateway và Runtime;
- bỏ raw API key/env/workdir khỏi request;
- giữ Gateway trong modular monolith thay vì tạo service mới.
