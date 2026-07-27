# Harness Hub Super Agent Runtime

Harness Hub owns the runtime schema and persistence. LangGraph concepts are used as architecture references, but the first implementation is file-backed and does not depend on `langgraph`.

## File Layout

Runtime data lives under `harness/hub/runtime/`:

```text
runtime/
  threads/<thread_id>/
    state.json
    latest.json
    checkpoints/<checkpoint_id>.json
    uploads/
    workspace/
    outputs/
  runs/<run_id>/
    run.json
    events.jsonl
    artifacts/
  store/
    memory.jsonl
    memory_candidates.jsonl
    skill_usage.jsonl
    guardrail_decisions.jsonl
```

Run state uses the Hub-native shape:

```json
{
  "run_id": "run-...",
  "thread_id": "thread-...",
  "status": "queued|running|interrupted|succeeded|failed|cancelled",
  "messages": [],
  "artifacts": [],
  "tool_calls": [],
  "child_runs": [],
  "interrupts": [],
  "usage": {},
  "metadata": {}
}
```

## Execution

The lead pipeline is deterministic and test-safe:

1. `prepare_context`
2. `plan`
3. `act`
4. `review`
5. `finalize`

Nodes return `{ "update": {}, "goto": "...", "interrupts": [], "spawn": [] }`. Updates are merged through runtime reducers, then the runtime appends events and writes checkpoints.

## Events

Runtime event logs are append-only JSONL. The SSE stream uses these event types:

- `node_update`
- `state_snapshot`
- `assistant_delta`
- `tool_result`
- `artifact`
- `child_run`
- `interrupt`
- `debug`
- `done`
- `error`

## APIs

- `GET /api/agents`
- `GET /api/agent/runs`
- `POST /api/agent/runs`
- `GET /api/agent/runs/{run_id}`
- `GET /api/agent/runs/{run_id}/events`
- `POST /api/agent/runs/{run_id}/interrupts/{interrupt_id}/resume`
- `GET /api/skills`
- `GET /api/skills/{id}`
- `GET /api/skills/{id}/usage`
- `GET /api/memory`
- `GET /api/memory/candidates`
- `POST /api/memory/candidates/{id}/accept`
- `POST /api/memory/candidates/{id}/reject`
- `GET /api/guardrails/decisions`
- `POST /api/guardrails/decisions/command`

## Current Boundaries

- No real LLM calls are made by the runtime pipeline.
- Child runs are scoped runtime records with task packets. They can optionally create a `gitjobs` job only when the spawn packet explicitly requests it.
- Child runs cannot expand parent `allowed_paths` or `allowed_tools` when the parent defines those scopes.
- `langgraph` remains optional future adapter work; Hub files and events stay the source of truth.
