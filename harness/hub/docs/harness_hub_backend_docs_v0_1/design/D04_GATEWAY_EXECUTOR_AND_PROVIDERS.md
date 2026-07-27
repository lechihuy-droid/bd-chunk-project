# D04 — Gateway, Executor and Providers

```yaml
document_id: HH-DES-D04
version: 1.1
status: In Review
owner: Execution Platform
depends_on: [D01, D02, D03, D06]
research_sources: [HH-RES-R01, HH-RES-R02, HH-RES-R04, HH-RES-R05, HH-RES-R06, HH-RES-R07]
```

## 1. Boundary

```text
Runtime -> Runtime Gateway -> Router -> Executor Port
                                      -> API Adapter
                                      -> CLI Adapter
```

Gateway validate request/capability/policy, resolve alias và tạo route plan. Runtime sở hữu workflow attempt/retry/state. Executor sở hữu một execution lifecycle. Adapter sở hữu provider protocol.

## 2. ExecutionRequest v1

```json
{
  "schema_version": 1,
  "execution_id": "exec-...",
  "run_id": "run-...",
  "node_id": "draft",
  "attempt_no": 1,
  "correlation_id": "corr-...",
  "idempotency_key": "...",
  "principal": {"kind":"local_user"},
  "agent_snapshot_ref": "sha256:...",
  "input": {"messages_ref":"artifact://..."},
  "requirements": {
    "mode":"chat",
    "streaming":true,
    "tools":[],
    "workspace_write":false
  },
  "route_hint": {"model_class":"smart"},
  "limits": {
    "deadline":"2026-07-27T00:10:00Z",
    "max_output_chars":100000,
    "max_cost":{"amount_minor":500,"currency":"JPY"}
  },
  "security": {
    "data_classification":"internal",
    "secret_refs":[],
    "workspace_ref":null,
    "network_policy":"provider_only"
  }
}
```

Không persist raw secret, host absolute workdir tùy ý hoặc unrestricted environment.

## 3. Capabilities

Adapter manifest:

```json
{
  "adapter_id":"nvidia-api",
  "transport":"http",
  "modes":["chat"],
  "streaming":true,
  "cancel":"best_effort",
  "tools":false,
  "workspace_access":"none",
  "sessions":"stateless",
  "models":["..."],
  "candidate_version":"...",
  "supported":null,
  "evidence":{"kind":"FIXTURE","observed_at":"..."}
}
```

Gateway từ chối trước launch nếu requirement không được capability đáp ứng. `supported=true` chỉ được gán cho exact adapter/provider version đã pass pinned conformance fixture. Living documentation hoặc `--help` chỉ tạo candidate capability, không phải compatibility guarantee.

Manifest phải tách `configured_executable`, `resolved_executable`, `observed_version`, provider/model profile và evidence provenance `DOC | HELP | CODE | LIVE | FIXTURE`.

## 4. Routing precedence và algorithm

Precedence:

1. hard security/data/egress policy;
2. explicit approved route constraint;
3. required capability;
4. model alias/profile snapshot;
5. health/quota/budget;
6. deterministic configured default.

Algorithm:

```text
validate contract
evaluate hard policy (fail closed)
resolve candidate adapters/models
filter capability + classification + availability
rank by explicit config, never model self-reported confidence
produce primary + bounded fallback plan
persist route decision reference
dispatch primary
```

Không có candidate trả `NO_ELIGIBLE_ROUTE`.

## 5. ExecutionEvent và Result

Event types: `started`, `delta`, `reasoning`, `tool_request`, `usage`, `artifact_candidate`, `warning`, `completed`, `failed`, `cancelled`.

Mọi event có `schema_version`, `execution_id`, `sequence`, `occurred_at`, `type`, `payload`. Delta/reasoning có size cap và không được coi là final artifact.

Result:

```json
{
  "schema_version":1,
  "execution_id":"exec-...",
  "status":"succeeded",
  "finish_reason":"stop",
  "output_ref":"artifact-candidate://...",
  "provider":{"adapter_id":"nvidia-api","model":"...","request_id":"..."},
  "usage":{"input_tokens":0,"output_tokens":0,"cost":null},
  "partial":false,
  "contract_validation":{"valid":true,"errors":[]},
  "security_scan":{"status":"passed","findings":[]},
  "capability_receipt_ref":"capability://...",
  "error":null
}
```

## 6. Error taxonomy

`INVALID_REQUEST`, `POLICY_DENIED`, `AUTH_FAILED`, `CAPABILITY_MISMATCH`,  
`MODEL_NOT_FOUND`, `RATE_LIMITED`, `PROVIDER_UNAVAILABLE`, `TRANSPORT_ERROR`,  
`DEADLINE_EXCEEDED`, `CANCELLED`, `OUTPUT_LIMIT`, `MALFORMED_OUTPUT`,  
`PROCESS_EXITED`, `PROCESS_LOST`, `SANDBOX_DENIED`, `INTERNAL`.

Error gồm category, retryable, safe message, `retry_after`, provider error reference đã redact.

## 7. Retry/fallback ownership

- Adapter: bounded retry cùng provider cho connection reset, 429/`Retry-After`, 502/503/504.
- Gateway: tạo fallback plan trước launch; không tự đổi route sau partial output.
- Runtime: tạo workflow attempt mới và quyết định fallback/retry.
- Auth, policy, validation, capability, contract: không retry/fallback.
- Deadline tổng không kéo dài bởi adapter retry.

## 8. API adapter

Pipeline: normalize request → resolve secret ref → capability check → HTTP stream → normalize event/error → usage/result.

Controls:

- per-provider timeout/rate limit;
- circuit state chỉ ảnh hưởng candidate eligibility;
- token/cost accounting không được chặn result nếu telemetry phụ lỗi;
- tool call chỉ tạo typed `tool_request`; adapter không tự chạy tool;
- prompt/output không log mặc định.

## 9. CLI adapter

Composition: command builder, workspace resolver, process supervisor, parser, artifact collector.

Lifecycle:

```text
resolve canonical workspace
apply policy + allowlists
build argv without shell interpolation
spawn process with minimal env
stream bounded stdout/stderr
cancel/timeout -> terminate then kill tree
collect declared outputs/diff
scan + normalize result
cleanup execution temp
```

CLI MUST:

- allowlist executable, arguments, env names và workspace roots;
- dùng argument array, không shell string;
- cap time/output; hard CPU/process limits chỉ khi process supervisor chứng minh được enforcement;
- file count/write bytes watcher chỉ là soft detection; hard quota cần quota storage boundary/separate identity/broker;
- không claim network deny nếu chưa có admin pre-provisioned WFP policy, authenticated privileged broker hoặc isolated worker;
- không mount secret store;
- reject symlink/junction/reparse-point escape trong supported workspace profile;
- pin/record CLI version;
- coi interactive prompt ngoài protocol là failure.

Same-user CLI chỉ là low-assurance application profile, không phải filesystem/secret/network containment. Job Object chỉ chứa associated descendants; brokered WMI/COM/service/task-scheduler escape phải bị loại bằng restricted identity/rights và adversarial tests.

Controlled Windows executor là milestone Gate D riêng, gồm native Job Object supervisor, dedicated/restricted identity, disposable workspace ACL/reparse controls, minimal environment, enforceable quota storage và pre-provisioned/brokered egress. Nếu thiếu, CLI workspace-write vẫn NO-GO và restricted data bị deny.

Accepted launch chain là pinned native executable, hoặc pinned native runtime + immutable/hash-pinned script/dependency root. `.cmd`/`.bat` mediation với untrusted arguments không thuộc controlled profile.

## 10. Typed tool và child capability

Model/provider chỉ được **propose** action:

```json
{
  "tool_request_id":"tool-...",
  "tool_id":"builtin.read",
  "schema_hash":"sha256:...",
  "canonical_args":{},
  "target_refs":[],
  "requested_data_class":"internal",
  "requested_egress":[],
  "causation_id":"exec-..."
}
```

Deterministic Policy Enforcement Point trả `PolicyDecision`; execution chỉ xảy ra khi có capability receipt bind exact action, args, targets, policy/schema/skill hashes, secret/egress scopes và expiry. Missing/empty capability = none. Wildcard là representation riêng và cần hard-policy approval.

Child capability là intersection của parent receipt, agent profile, workflow policy và platform hard policy. Provider-internal tool/plugin/MCP opaque phải bị disable hoặc route bị từ chối.

## 11. Session

Default stateless. Provider session ID chỉ là hint/reference; mất session không làm mất source of truth. Sticky CLI session và shared mutable memory ngoài v1.

## 12. Conformance suite

Mọi adapter phải pass:

- capability mismatch trước launch;
- ordered event sequence;
- normal completion và malformed output;
- timeout/cancel;
- redaction;
- output/usage mapping;
- transient retry bounds;
- partial stream no silent fallback;
- duplicate execution idempotency behavior;
- provider-specific error mapping.
- configured/resolved executable và exact version truth;
- typed tool proposal không tự execute;
- empty child capability không mở rộng quyền;
- capability/approval invalidated khi action, policy, schema hoặc content hash đổi;
- Windows Job/process/workspace/egress claims chỉ pass theo exact controlled profile.

Ít nhất mock adapter + một API adapter phải pass trước migration Runtime.
