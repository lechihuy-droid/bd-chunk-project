# Basic Design — Orchestrator Agent

> Superseded by `../../design/D02_DOMAIN_AND_WORKFLOW_CONTRACTS.md` and D03.

**Document type:** Basic Design  
**Version:** 0.1

## 1. Mục tiêu

Orchestrator Agent được thiết kế theo từng dòng dự án như RD-to-BD, migration, software delivery hoặc research. Project cụ thể tạo configured instance từ template.

## 2. Trách nhiệm

Orchestrator nhận runtime event, đọc state/policy, chọn action, tạo task instruction, diễn giải reviewer issue và quyết định retry, reroute hoặc hỏi user.

Orchestrator MUST NOT chạy process, sửa database, bỏ qua policy hoặc ghi đè artifact.

## 3. Input

```yaml
runtime_event:
  event_id: string
  run_id: string
  event_type: string
  state_snapshot: object
  available_actions: array
  active_policy: object
  artifact_refs: array
  review_result: object?
```

## 4. Output

```yaml
orchestrator_decision:
  decision_id: string
  action: EXECUTE_NODE | RETRY_NODE | REROUTE_NODE | REQUEST_USER_INPUT | STOP_RUN
  target_node_id: string?
  instruction_patch: string?
  context_refs: array
  rationale_summary: string
  confidence: number
  requires_human_approval: boolean
```

## 5. Template và instance

Template định nghĩa workflow, worker, skill, review, retry, escalation và model policy. Project instance chỉ override workspace, project references, approval chain, budget, data classification và output template.

## 6. Guardrails

- Decision phải validate schema.
- Chỉ action trong allow-list được chấp nhận.
- Confidence thấp phải hỏi user hoặc fallback.
- Chỉ lưu rationale summary, không phụ thuộc chain-of-thought.
