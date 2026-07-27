from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any

from services import (
    runtime_checkpoint,
    runtime_children,
    runtime_events,
    runtime_interrupts,
    runtime_state,
)


NodeResult = dict[str, Any]
NodeFn = Callable[[dict[str, Any]], NodeResult]
NODE_ORDER = ["prepare_context", "plan", "act", "review", "finalize"]


def _node_result(
    *,
    update: dict[str, Any] | None = None,
    goto: str | None = None,
    interrupts: list[dict[str, Any]] | None = None,
    spawn: list[dict[str, Any]] | None = None,
) -> NodeResult:
    return {
        "update": dict(update or {}),
        "goto": goto,
        "interrupts": list(interrupts or []),
        "spawn": list(spawn or []),
    }


def _metadata(state: dict[str, Any]) -> dict[str, Any]:
    value = state.get("metadata")
    return value if isinstance(value, dict) else {}


def _objective(state: dict[str, Any]) -> str:
    metadata = _metadata(state)
    objective = str(metadata.get("objective") or "").strip()
    if objective:
        return objective
    for message in reversed(state.get("messages") or []):
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content") if message.get("content") is not None else message.get("text")
            if str(content or "").strip():
                return str(content).strip()
    return "Run deterministic lead pipeline"


def _has_resolved_interrupt(state: dict[str, Any], node: str) -> bool:
    for interrupt in state.get("interrupts") or []:
        if (
            isinstance(interrupt, dict)
            and interrupt.get("node") == node
            and interrupt.get("status") == "resolved"
        ):
            return True
    return False


def _needs_interrupt(state: dict[str, Any], node: str) -> bool:
    metadata = _metadata(state)
    interrupt_at = metadata.get("interrupt_at")
    approval_required = bool(metadata.get("require_approval")) and node == "act"
    requested = interrupt_at == node or approval_required
    return requested and not _has_resolved_interrupt(state, node)


def prepare_context(state: dict[str, Any]) -> NodeResult:
    return _node_result(
        update={
            "metadata": {
                "context_prepared": True,
                "context_summary": f"{len(state.get('messages') or [])} message(s) available",
            },
            "usage": {"internal_steps": 1},
        },
        goto="plan",
    )


def plan(state: dict[str, Any]) -> NodeResult:
    run_id = str(state.get("run_id") or "")
    objective = _objective(state)
    return _node_result(
        update={
            "messages": [
                {
                    "id": f"{run_id}-plan",
                    "role": "assistant",
                    "node": "plan",
                    "content": f"Plan prepared for: {objective}",
                }
            ],
            "metadata": {"plan_ready": True},
            "usage": {"internal_steps": 1},
        },
        goto="act",
    )


def act(state: dict[str, Any]) -> NodeResult:
    if _needs_interrupt(state, "act"):
        return _node_result(
            goto="act",
            interrupts=[
                {
                    "reason": "approval_required",
                    "payload": {
                        "node": "act",
                        "objective": _objective(state),
                        "choices": ["approve", "reject", "edit"],
                    },
                }
            ],
        )

    metadata = _metadata(state)
    spawn = metadata.get("spawn")
    spawn_rows = [item for item in spawn if isinstance(item, dict)] if isinstance(spawn, list) else []
    run_id = str(state.get("run_id") or "")
    objective = _objective(state)
    artifact_content = {
        "run_id": run_id,
        "objective": objective,
        "mode": "deterministic",
        "spawn_requested": len(spawn_rows),
    }
    return _node_result(
        update={
            "messages": [
                {
                    "id": f"{run_id}-act",
                    "role": "assistant",
                    "node": "act",
                    "content": "Action phase completed with deterministic runtime execution.",
                }
            ],
            "artifacts": [
                {
                    "id": f"{run_id}-runtime-output",
                    "path": "artifacts/runtime_output.json",
                    "type": "runtime_output",
                    "title": "Runtime output",
                    "content": artifact_content,
                }
            ],
            "metadata": {"action_complete": True},
            "usage": {"internal_steps": 1},
        },
        goto="review",
        spawn=spawn_rows,
    )


def review(state: dict[str, Any]) -> NodeResult:
    run_id = str(state.get("run_id") or "")
    return _node_result(
        update={
            "messages": [
                {
                    "id": f"{run_id}-review",
                    "role": "assistant",
                    "node": "review",
                    "content": "Review complete. No external model or tool call was required.",
                }
            ],
            "metadata": {"review_complete": True},
            "usage": {"internal_steps": 1},
        },
        goto="finalize",
    )


def finalize(state: dict[str, Any]) -> NodeResult:
    run_id = str(state.get("run_id") or "")
    return _node_result(
        update={
            "messages": [
                {
                    "id": f"{run_id}-final",
                    "role": "assistant",
                    "node": "finalize",
                    "content": "Run finalized.",
                }
            ],
            "metadata": {"finalized": True, "next_node": None},
            "usage": {"internal_steps": 1},
        },
        goto=None,
    )


NODES: dict[str, NodeFn] = {
    "prepare_context": prepare_context,
    "plan": plan,
    "act": act,
    "review": review,
    "finalize": finalize,
}


def _default_next(node: str) -> str | None:
    try:
        index = NODE_ORDER.index(node)
    except ValueError:
        return None
    next_index = index + 1
    return NODE_ORDER[next_index] if next_index < len(NODE_ORDER) else None


def _event(run_id: str, event_type: str, **fields: Any) -> dict[str, Any]:
    return runtime_events.append_event(run_id, event_type, **fields)


def _yield_event(run_id: str, event_type: str, **fields: Any) -> Iterator[str]:
    yield runtime_events.to_sse(_event(run_id, event_type, **fields))


def _materialize_artifacts(run_id: str, update: dict[str, Any]) -> dict[str, Any]:
    artifacts = update.get("artifacts")
    if not isinstance(artifacts, list):
        return update
    cleaned: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        item = dict(artifact)
        content = item.pop("content", None)
        path = item.get("path")
        if content is not None and isinstance(path, str) and path:
            artifact_path = runtime_state.runtime_path("run", run_id, path)
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        cleaned.append(item)
    patched = dict(update)
    patched["artifacts"] = cleaned
    return patched


def _assistant_events(run_id: str, update: dict[str, Any]) -> Iterator[str]:
    messages = update.get("messages")
    if not isinstance(messages, list):
        return
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        text = str(message.get("content") or message.get("text") or "")
        if text:
            yield from _yield_event(run_id, "assistant_delta", message_id=message.get("id"), node=message.get("node"), text=text)


def _artifact_events(run_id: str, update: dict[str, Any]) -> Iterator[str]:
    artifacts = update.get("artifacts")
    if not isinstance(artifacts, list):
        return
    for artifact in artifacts:
        if isinstance(artifact, dict):
            yield from _yield_event(run_id, "artifact", artifact=artifact)


def _snapshot(run_id: str) -> Iterator[str]:
    state = runtime_state.read_run(run_id)
    yield from _yield_event(run_id, "state_snapshot", state=state)


def execute_run(run_id: str, *, start_node: str | None = None) -> Iterator[str]:
    run_id = runtime_state.validate_id("run", run_id)
    state = runtime_state.update_run_state(run_id, {"status": "running"})
    runtime_checkpoint.write_checkpoint(run_id, state=state, reason="run-started")
    node = start_node or str(_metadata(state).get("next_node") or "prepare_context")

    try:
        while node:
            if node not in NODES:
                raise ValueError(f"Unknown runtime node: {node}")
            state = runtime_state.update_run_state(run_id, {"metadata": {"current_node": node, "next_node": node}})
            result = NODES[node](state)
            interrupts = [item for item in result.get("interrupts", []) if isinstance(item, dict)]
            if interrupts:
                for interrupt in interrupts:
                    created = runtime_interrupts.create_interrupt(
                        run_id,
                        reason=str(interrupt.get("reason") or "approval_required"),
                        payload=interrupt.get("payload") if isinstance(interrupt.get("payload"), dict) else {},
                        node=node,
                    )
                    yield runtime_events.to_sse(runtime_events.read_events(run_id)[-1])
                    yield from _snapshot(run_id)
                    if created:
                        return

            spawn_rows = [item for item in result.get("spawn", []) if isinstance(item, dict)]
            for spawn in spawn_rows:
                created = runtime_children.create_child_run(run_id, spawn)
                child_run = {
                    "run_id": created["child_run"]["run_id"],
                    "status": created["child_run"]["status"],
                    "agent_id": created["task_packet"]["agent_id"],
                    "objective": created["task_packet"]["objective"],
                }
                yield from _yield_event(run_id, "child_run", child_run=child_run)

            update = _materialize_artifacts(run_id, result.get("update") if isinstance(result.get("update"), dict) else {})
            completed = list(_metadata(runtime_state.read_run(run_id)).get("completed_nodes") or [])
            if node not in completed:
                completed.append(node)
            next_node = result.get("goto")
            if next_node is None:
                next_node = _default_next(node)
            update = {
                **update,
                "metadata": {
                    **(update.get("metadata") if isinstance(update.get("metadata"), dict) else {}),
                    "completed_nodes": completed,
                    "current_node": node,
                    "next_node": next_node,
                },
            }
            state = runtime_state.update_run_state(run_id, update)
            yield from _assistant_events(run_id, update)
            yield from _artifact_events(run_id, update)
            yield from _yield_event(run_id, "node_update", node=node, goto=next_node, update_keys=sorted(update.keys()))
            runtime_checkpoint.write_checkpoint(run_id, state=state, reason=f"node:{node}")
            yield from _snapshot(run_id)
            node = next_node

        state = runtime_state.update_run_state(run_id, {"status": "succeeded", "metadata": {"finished_at": runtime_state.now_iso()}})
        runtime_checkpoint.write_checkpoint(run_id, state=state, reason="run-finished")
        yield from _yield_event(run_id, "done", status="succeeded", state=state)
    except Exception as exc:
        state = runtime_state.update_run_state(
            run_id,
            {"status": "failed", "metadata": {"error": str(exc), "finished_at": runtime_state.now_iso()}},
        )
        runtime_checkpoint.write_checkpoint(run_id, state=state, reason="run-failed")
        yield from _yield_event(run_id, "error", message=str(exc), state=state)


def create_run_stream(payload: dict[str, Any]) -> Iterator[str]:
    objective = str(payload.get("objective") or payload.get("prompt") or "").strip()
    messages = payload.get("messages")
    rows = [item for item in messages if isinstance(item, dict)] if isinstance(messages, list) else []
    if objective and not rows:
        rows = [{"id": "user-objective", "role": "user", "content": objective}]
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    for key in ("interrupt_at", "require_approval", "spawn", "allowed_paths", "allowed_tools"):
        if key in payload:
            metadata[key] = payload[key]
    if objective:
        metadata["objective"] = objective

    run = runtime_state.create_run(
        thread_id=payload.get("thread_id") if isinstance(payload.get("thread_id"), str) else None,
        agent_id=str(payload.get("agent_id") or payload.get("agent") or "lead"),
        messages=rows,
        metadata=metadata,
    )
    run_id = str(run["run_id"])
    _event(run_id, "debug", message="run created", thread_id=run["thread_id"])
    runtime_checkpoint.write_checkpoint(run_id, state=run, reason="run-created")
    yield runtime_events.to_sse(runtime_events.read_events(run_id)[-1])
    yield from execute_run(run_id)


def resume_run_stream(run_id: str, interrupt_id: str, payload: dict[str, Any]) -> Iterator[str]:
    resume_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
    action = str(payload.get("action") or "resume")
    result = runtime_interrupts.resolve_interrupt(
        run_id,
        interrupt_id,
        resume_payload=resume_payload if isinstance(resume_payload, dict) else {},
        action=action,
    )
    yield runtime_events.to_sse(runtime_events.read_events(run_id)[-1])
    state = result["state"]
    start_node = str(_metadata(state).get("next_node") or "act")
    yield from execute_run(run_id, start_node=start_node)
