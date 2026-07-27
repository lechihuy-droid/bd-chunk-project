# D02 — Domain and Workflow Contracts

```yaml
document_id: HH-DES-D02
version: 1.0
status: In Review
owner: Runtime
depends_on: [D01]
```

## 1. Ubiquitous language

| Term | Định nghĩa |
|---|---|
| Workflow Definition | YAML topology có version, chưa chạy |
| Workflow Run | Một execution của definition snapshot |
| Thread | Nhóm runs và shared persisted context |
| Node Definition | Cấu hình node `agent` hoặc `validate` |
| Node Attempt | Một lần thực thi node; retry tạo attempt mới |
| Agent Profile | Cấu hình provider/model/prompt/skills/budget |
| Runtime | State machine và scheduler của workflow |
| Gateway | Boundary chuẩn hóa route/execution |
| Executor | Thực thi một request qua adapter |
| Interrupt | Human task tạm dừng run |
| Runtime Event | Timeline operational có thể replay |
| Audit Record | Evidence security/governance append-only |
| Artifact | Logical output |
| Artifact Version | Immutable content + manifest của output |
| Workspace | Allowed filesystem root cho task |

## 2. Aggregate và ownership

```text
WorkflowDefinition -> WorkflowVersion -> NodeDefinition + Edge
Thread -> WorkflowRun -> NodeAttempt + Interrupt
WorkflowRun -> Artifact -> ArtifactVersion
AgentProfile -> immutable snapshot in WorkflowRun
```

- `WorkflowRun` là consistency boundary cho state transition.
- `Thread` chỉ index runs/context; không quyết định run status.
- `ArtifactVersion` immutable; `current_version` là projection.
- Executor session là technical resource, không phải source of truth.

Mọi entity có string ID theo allowlisted pattern, `created_at` UTC ISO-8601 và `schema_version`. Persisted mutable aggregate có integer `version`, tăng đúng một lần trên mỗi successful command.

## 3. Workflow v1 canonical shape

```yaml
schema_version: 1
id: research-draft-review
title: Research draft review
nodes:
  - id: draft
    type: agent
    agent: drafter
    prompt: "Draft: {{objective}}"
    gate: none
  - id: validate
    type: validate
    target: draft
    checks:
      - kind: min_length
        value: 500
    on_fail: interrupt
edges:
  - [draft, validate]
stop:
  max_nodes: 10
  max_seconds: 900
```

Required top-level: `schema_version`, `id`, `nodes`, `edges`, `stop`. Unknown top-level fields MAY be preserved for forward compatibility but MUST NOT affect execution unless schema declares chúng.

## 4. Node contracts

### Agent node

Required: `id`, `type=agent`, `agent`, `prompt`, `gate`.  
Optional: `spawn`, `output`, `timeout_seconds`.

- `gate`: `none | approval`.
- Template variables v1: `objective` và output của node trước được Runtime cung cấp theo explicit binding; unresolved variable là validation error.
- `spawn` chỉ reference agent profile tồn tại và chịu child-run policy.

### Validate node

Required: `id`, `type=validate`, `target`, `checks`, `on_fail`.

Check v1:

- `min_length {value:int}`;
- `must_include {values:[string]}`;
- `must_not_include {values:[string]}`;
- `json_parseable`.

`on_fail`: `interrupt | fail`. Validate node deterministic, không gọi model.

## 5. Graph invariants

- Node ID unique và non-empty.
- Edge gồm đúng `[source, target]`, cả hai phải tồn tại.
- Một start, một end; in/out degree tối đa 1.
- Không cycle, disconnected node hoặc self-edge.
- Thứ tự IR phải cover mọi node đúng một lần.
- `stop.max_nodes` positive integer và không nhỏ hơn số node.
- `stop.max_seconds` positive number.
- Branch, conditional edge, join và dynamic node là invalid trong schema v1.

## 6. Agent profile snapshot

Run snapshot tối thiểu:

```json
{
  "schema_version": 1,
  "agent_id": "reviewer",
  "profile_hash": "sha256:...",
  "provider_ref": "smart",
  "resolved_provider": "nvidia",
  "resolved_model": "model-id",
  "system_prompt_ref": "sha256:...",
  "skills": [],
  "budget": {"max_calls": 5, "max_seconds": 600}
}
```

Alias phải resolve trước execution và được snapshot. Thay đổi profile sau khi run tạo không ảnh hưởng run đó.

## 7. Domain invariants

- Definition/version đã dùng trong run không mutate.
- Terminal run không quay về running.
- Một node chỉ thành succeeded khi artifact/result contract hợp lệ.
- Retry không ghi đè attempt evidence.
- Pending interrupt chặn launch node tương ứng.
- Resolve interrupt chỉ một lần; duplicate cùng idempotency key trả kết quả cũ.
- Child run không được có quyền rộng hơn parent.
- Workspace file không tự động là Artifact; chỉ output được manifest hóa mới là ArtifactVersion.

## 8. Compatibility

- Validator MUST reject `schema_version` không hỗ trợ.
- Minor additive field được ignore/preserve nếu không ảnh hưởng semantics.
- Rename/remove/change semantics cần version mới và migration tool/fixture.
- Layout nằm trong `<workflow>.layout.json`, không ảnh hưởng workflow hash hoặc runtime semantics.

## 9. Validation errors

Mỗi error có:

```json
{"code":"WORKFLOW_INVALID_EDGE","path":"edges[1]","message":"target not found","details":{}}
```

Không chỉ trả message tổng. API trả toàn bộ lỗi deterministic trong một lần validate.

## 10. Acceptance

- JSON Schema và Python validator cho cùng kết quả trên fixture valid/invalid.
- Template workflow hiện có validate ở schema v1.
- Branch/cycle/unknown agent/unresolved template bị reject.
- Snapshot hash ổn định và replay không phụ thuộc profile hiện tại.

