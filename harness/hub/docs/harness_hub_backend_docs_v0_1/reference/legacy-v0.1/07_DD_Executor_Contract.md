# Detailed Design — Unified Executor Contract

> Superseded by `../../design/D04_GATEWAY_EXECUTOR_AND_PROVIDERS.md`.

| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-DD-EXEC-001 |
| Document type | Detailed Design |
| Version | 0.2 |
| Status | Draft — merged from research |
| Implementation readiness | Conditional — JSON Schemas and conformance tests required |
| Depends on | Domain Model, Workflow Runtime, Runtime Gateway and Routing |
| Research source | HH-RES-R02 |
| Last updated | 2026-07-27 |

## 1. Mục tiêu

Executor Contract chuẩn hóa một lần thực thi trên API, CLI hoặc backend tương lai để Runtime không phụ thuộc transport/provider. Contract không ép mọi adapter có cùng capability; adapter phải khai báo capability trung thực.

## 2. Domain objects

- `ExecutionRequest`: immutable input cho một attempt.
- `ExecutionHandle`: handle của execution đang chạy.
- `ExecutionEvent`: normalized streaming event.
- `ExecutionResult`: terminal result.
- `ExecutorCapabilities`: capability manifest versioned.
- `ExecutorError`: normalized error.
- `SessionHandle`: optional provider session reference.
- `WorkspaceRef`: reference tới workspace đã được Runtime chuẩn bị.
- `CredentialRef`: reference tới credential; không phải secret value.

Transport, provider protocol, parser và session manager được ghép bằng composition. Không dùng inheritance hierarchy sâu hoặc một “god adapter”.

## 3. ExecutionRequest v1

Required fields:

```yaml
contract_version: "1.0"
execution_id: string
idempotency_key: string
correlation_id: string
trace_id: string?
run_id: string
node_id: string
attempt_no: integer
executor_id: string
provider: string
model: string
agent_version_ref: string
instruction_bundle_ref: string
input_refs: array
output_contract_ref: string?
workspace_ref: string?
credential_refs: array
requirements:
  streaming: boolean
  tools: boolean
  structured_output: boolean
  file_io: boolean
  session_resume: boolean
limits:
  deadline: datetime
  idle_timeout_seconds: integer?
  max_output_tokens: integer?
  resource_limits: object?
security:
  principal_ref: string
  data_classification: string
  filesystem_policy_ref: string?
  network_policy_ref: string?
provider_options: object
```

Rules:

- Request immutable sau submit.
- Không chứa raw secret, raw home path hoặc unrestricted environment.
- `provider_options` phải validate theo adapter config schema.
- Cùng idempotency key + cùng request hash trả cùng handle/result.
- Cùng key + khác hash trả `IDEMPOTENCY_CONFLICT`.

## 4. ExecutorCapabilities

Manifest tối thiểu:

```yaml
executor_id: string
contract_versions: ["1.0"]
adapter_version: string
capabilities:
  streaming: boolean
  tool_calls: boolean
  structured_output: boolean
  file_io: boolean
  shell: boolean
  session: boolean
  resume: boolean
  cancel: boolean
  usage_reporting: boolean
  cost_reporting: boolean
  parallelism: integer
config_schema_ref: string
```

Router phải reject request thiếu capability trước khi submit.

## 5. ExecutionEvent catalogue

Common envelope:

```yaml
schema_version: "1.0"
event_id: string
sequence: integer
occurred_at: datetime
execution_id: string
run_id: string
node_id: string
attempt_no: integer
executor_id: string
provider_session_id: string?
kind: string
data: object
```

Core kinds:

- `execution.accepted`
- `execution.started`
- `message.delta`
- `message.final`
- `reasoning.delta`
- `tool.call.requested`
- `tool.result.received`
- `tool.call.denied`
- `artifact.proposed`
- `usage.updated`
- `execution.warning`
- `execution.completed`
- `execution.failed`
- `execution.cancelled`

Exactly một terminal event được phép. Sequence tăng đơn điệu trong một execution. Provider-specific data chỉ nằm trong validated extension field.

Tool request chỉ là đề xuất; adapter không tự chạy arbitrary tool.

## 6. ExecutionResult

```yaml
contract_version: "1.0"
execution_id: string
status: COMPLETED | FAILED | CANCELLED | TIMED_OUT
finish_reason: string
output_refs: array
partial_output_ref: string?
artifact_refs: array
usage:
  input_tokens: integer?
  output_tokens: integer?
  duration_ms: integer
  estimated_cost:
    amount_minor: integer?
    currency: string?
provider_request_id: string?
provider_session_id: string?
security_scan_ref: string?
output_validation_ref: string?
error: ExecutorError?
```

Raw response, stdout/stderr hoặc file diff được lưu bằng reference, không nhúng không giới hạn vào result.

## 7. Error taxonomy

| Code/category | Retry mặc định | Ý nghĩa |
|---|---:|---|
| `CONFIGURATION` | No | executor/model/options không hợp lệ |
| `AUTHENTICATION` | No | credential thiếu/hết hạn |
| `CAPABILITY` | No | adapter không đáp ứng requirement |
| `POLICY` / `SECURITY` | No | permission hoặc boundary bị từ chối |
| `TRANSPORT` | Yes, bounded | reset, 502/503/504, transient network |
| `RATE_LIMIT` | Yes, respect retry-after | provider 429 |
| `PROVIDER` | Depends | provider error đã normalize |
| `PROCESS` | Depends | CLI non-zero/crash |
| `PARSE` / `CONTRACT` | No | output không đúng protocol/schema |
| `TIMEOUT` | No at adapter boundary | deadline/idle timeout |
| `RESOURCE` | No | CPU/RAM/process/output cap |
| `CANCELLED` | No | explicit cancellation |
| `CLEANUP` | No; warning/audit | cleanup không hoàn chỉnh |
| `INTERNAL` | No | unexpected adapter bug |

Mỗi error có `code`, `category`, `message`, `retryable`, `user_visible`, `details_ref`, `retry_after_ms`.

## 8. Interface

```python
class Executor:
    def capabilities(self) -> ExecutorCapabilities: ...
    async def submit(self, request: ExecutionRequest) -> ExecutionHandle: ...
    async def stream(self, handle: ExecutionHandle): ...
    async def get_result(self, handle: ExecutionHandle) -> ExecutionResult: ...
    async def cancel(self, handle: ExecutionHandle, reason: str) -> None: ...
```

Adapter factory resolve `executor_id`; adapter không tự route model khác.

## 9. Lifecycle

```text
ACCEPTED → PREPARING → STARTING → RUNNING
RUNNING → COMPLETING → COMPLETED
RUNNING/PREPARING/STARTING → CANCELLING → CANCELLED
non-terminal → FAILED | TIMED_OUT
terminal → CLEANING_UP → CLOSED
```

Cleanup luôn chạy. `CLOSED` là lifecycle nội bộ; terminal business status không bị thay đổi bởi cleanup warning.

## 10. Cancellation và timeout

- Explicit cancel có ưu tiên hơn timeout.
- API adapter abort request/stream.
- CLI adapter terminate process tree: graceful terminate → grace period → force kill.
- Cancel phải idempotent.
- Cancellation không xóa event, partial output hoặc attempt evidence.
- Adapter phát terminal `execution.cancelled`; Runtime quyết định trạng thái node/run.

## 11. Session

Stateless là mặc định. Session/resume chỉ dùng khi manifest khai báo.

- Session ID là opaque provider reference.
- Runtime giữ context cần để replay.
- Session có expiry và không chia sẻ giữa workspace.
- Session loss không làm mất run state.

## 12. Conformance requirements

Mọi adapter phải pass chung:

- request/schema validation;
- capability claims;
- event envelope, ordering và exactly-one-terminal-event;
- idempotent submit/cancel;
- timeout/cancel cleanup;
- normalized errors;
- secret redaction;
- partial output behavior;
- usage semantics;
- version compatibility.

## 13. Acceptance criteria

- API và CLI adapter dùng cùng contract mà Runtime không branch theo provider.
- Capability mismatch fail trước launch.
- Same idempotency key không chạy hai lần.
- Cancel/timeout không để orphan process/request.
- Không có secret trong request evidence, events, logs hoặc result.
- Adapter-specific behavior chỉ nằm trong manifest/config extension.

## 14. Traceability

Merged từ HH-RES-R02: domain model, capability manifest, event model, lifecycle, error taxonomy, cancellation, testing. Đã sửa:

- thêm node/attempt/idempotency/version/provenance fields;
- thay raw API key/env bằng references;
- tách Runtime event khỏi Execution event;
- không bắt buộc dynamic plugin loader trong MVP.
