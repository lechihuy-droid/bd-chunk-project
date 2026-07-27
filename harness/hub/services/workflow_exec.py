from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
import json
import re
from typing import Any

from services import governance, runtime_agents, runtime_artifacts, runtime_checkpoint, runtime_children, runtime_events, runtime_interrupts, runtime_state, runtime_validate, workflow
from services.providers import get_provider


_TEMPLATE_REF = re.compile(r"{{(.*?)}}")


def render_template(prompt: str, context: dict[str, str]) -> str:
    """Render validated workflow template references without leaving placeholders behind."""
    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token not in context:
            raise ValueError(f"Unknown workflow template token: {token}")
        return context[token]

    return _TEMPLATE_REF.sub(replace, prompt)


def _metadata(state: dict[str, Any]) -> dict[str, Any]:
    value = state.get("metadata")
    return value if isinstance(value, dict) else {}


def _has_resolved_interrupt(state: dict[str, Any], node_id: str) -> bool:
    return any(
        isinstance(interrupt, dict)
        and interrupt.get("node") == node_id
        and interrupt.get("status") == "resolved"
        for interrupt in state.get("interrupts") or []
    )


def _resolved_interrupt_action(state: dict[str, Any], node_id: str) -> str | None:
    for interrupt in state.get("interrupts") or []:
        if isinstance(interrupt, dict) and interrupt.get("node") == node_id and interrupt.get("status") == "resolved":
            return str(interrupt.get("action") or "resume")
    return None


def _event(run_id: str, event_type: str, **fields: Any) -> dict[str, Any]:
    return runtime_events.append_event(run_id, event_type, **fields)


def _yield_event(run_id: str, event_type: str, **fields: Any) -> Iterator[str]:
    yield runtime_events.to_sse(_event(run_id, event_type, **fields))


def _snapshot(run_id: str) -> Iterator[str]:
    yield from _yield_event(run_id, "state_snapshot", state=runtime_state.read_run(run_id))


def _elapsed_seconds(started_at: str) -> float:
    try:
        parsed = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        return max(0.0, (datetime.fromisoformat(runtime_state.now_iso().replace("Z", "+00:00")) - parsed).total_seconds())
    except (TypeError, ValueError):
        return 0.0


def _fail(run_id: str, message: str) -> Iterator[str]:
    state = runtime_state.update_run_state(
        run_id,
        {"status": "failed", "metadata": {"error": message, "finished_at": runtime_state.now_iso()}},
    )
    runtime_checkpoint.write_checkpoint(run_id, state=state, reason="run-failed")
    yield from _yield_event(run_id, "error", message=message, state=state)


def _context(objective: str, node_outputs: dict[str, Any]) -> dict[str, str]:
    context = {"objective": objective}
    for key, value in node_outputs.items():
        context[str(key)] = str(value)
        context[f"{key}_output"] = str(value)
    return context


def _run_child(
    *, parent_run_id: str, node_id: str, objective: str, agent: dict[str, Any], child_run_id: str
) -> Iterator[str]:
    """Run a child provider synchronously while preserving child failure isolation."""
    agent_id = str(agent["id"])
    try:
        started_at = runtime_state.now_iso()
        runtime_state.update_run_state(child_run_id, {
            "status": "running",
            "metadata": {"run_started_at": started_at, "agent_calls": {}, "agent_elapsed_seconds": {}},
        })
        messages = [
            {"role": "user", "content": f"SYSTEM INSTRUCTIONS:\n{agent['system_prompt']}"},
            {"role": "user", "content": objective},
        ]
        routed = runtime_agents.resolve_provider(agent)
        provider = get_provider(routed["provider"])
        call_started_at = runtime_state.now_iso()
        output: list[str] = []
        for item in provider.stream_chat(messages, session_id=None, model=routed["model"]):
            item_type = item.get("type")
            if item_type == "delta":
                text = str(item.get("text") or "")
                output.append(text)
                yield from _yield_event(parent_run_id, "child_run", child_run_id=child_run_id, parent_run_id=parent_run_id, node=node_id, agent_id=agent_id, text=text)
            elif item_type == "reasoning":
                yield from _yield_event(parent_run_id, "child_run", child_run_id=child_run_id, parent_run_id=parent_run_id, node=node_id, agent_id=agent_id, reasoning=str(item.get("text") or ""))
            elif item_type == "done":
                child_state = runtime_state.read_run(child_run_id)
                child_metadata = _metadata(child_state)
                calls = dict(child_metadata.get("agent_calls") or {})
                elapsed = dict(child_metadata.get("agent_elapsed_seconds") or {})
                calls[agent_id] = int(calls.get(agent_id, 0)) + 1
                elapsed[agent_id] = float(elapsed.get(agent_id, 0.0)) + _elapsed_seconds(call_started_at)
                runtime_state.update_run_state(child_run_id, {"usage": item.get("usage", {}), "metadata": {"agent_calls": calls, "agent_elapsed_seconds": elapsed}})
            elif item_type == "error":
                raise RuntimeError(str(item.get("message") or "Provider error"))

        child_output = "".join(output)
        output_path = runtime_state.runtime_path("run", child_run_id, "artifacts", "output.txt")
        output_path.write_text(child_output, encoding="utf-8")
        runtime_children.complete_child_run(child_run_id, [{"id": "child-output", "path": "artifacts/output.txt", "type": "child_output", "title": "Child output"}])
        claims_path = runtime_state.runtime_path("run", parent_run_id, "artifacts", "claims.jsonl")
        claims_path.parent.mkdir(parents=True, exist_ok=True)
        claim = {"child_run_id": child_run_id, "node_id": node_id, "agent_id": agent_id, "objective": objective, "output": child_output, "ts": runtime_state.now_iso()}
        with claims_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(claim, ensure_ascii=False) + "\n")
        yield from _yield_event(parent_run_id, "child_run", child_run_id=child_run_id, parent_run_id=parent_run_id, node=node_id, agent_id=agent_id, status="succeeded")
        return child_output
    except Exception as exc:
        message = str(exc)
        runtime_children.fail_child_run(child_run_id, message)
        yield from _yield_event(parent_run_id, "error", child_run_id=child_run_id, parent_run_id=parent_run_id, node=node_id, message=message)
        return None


def run_workflow(ir: list[dict[str, Any]], *, stop: dict[str, Any], objective: str, run_id: str) -> Iterator[str]:
    """Execute a resolved linear workflow against an existing runtime run."""
    run_id = runtime_state.validate_id("run", run_id)
    state = runtime_state.read_run(run_id)
    metadata = _metadata(state)
    initial = {
        "node_index": int(metadata.get("node_index") or 0),
        "completed_nodes": list(metadata.get("completed_nodes") or []),
        "node_outputs": dict(metadata.get("node_outputs") or {}),
        "run_started_at": str(metadata.get("run_started_at") or runtime_state.now_iso()),
        "agent_calls": dict(metadata.get("agent_calls") or {}),
        "agent_elapsed_seconds": dict(metadata.get("agent_elapsed_seconds") or {}),
    }
    state = runtime_state.update_run_state(run_id, {"status": "running", "metadata": initial})
    runtime_checkpoint.write_checkpoint(run_id, state=state, reason="run-started")

    try:
        while True:
            metadata = _metadata(runtime_state.read_run(run_id))
            node_index = int(metadata.get("node_index") or 0)
            completed_nodes = list(metadata.get("completed_nodes") or [])
            node_outputs = dict(metadata.get("node_outputs") or {})
            agent_calls = dict(metadata.get("agent_calls") or {})
            agent_elapsed = dict(metadata.get("agent_elapsed_seconds") or {})
            started_at = str(metadata.get("run_started_at") or runtime_state.now_iso())

            if node_index >= len(ir):
                state = runtime_state.update_run_state(
                    run_id, {"status": "succeeded", "metadata": {"finished_at": runtime_state.now_iso()}}
                )
                runtime_checkpoint.write_checkpoint(run_id, state=state, reason="run-finished")
                yield from _yield_event(run_id, "done", status="succeeded", state=state)
                return

            node = ir[node_index]
            if node.get("type") == "validate":
                node_id = str(node["id"])
                target = str(node["target"])
                try:
                    text = runtime_artifacts.read_artifact(run_id, f"{target}.md")
                except FileNotFoundError:
                    text = str(node_outputs.get(target, ""))
                state = runtime_state.update_run_state(
                    run_id, {"metadata": {"current_node": node_id, "node_index": node_index}}
                )
                if _has_resolved_interrupt(state, node_id):
                    if _resolved_interrupt_action(state, node_id) == "reject":
                        yield from _fail(run_id, f"rejected at validate:{node_id}")
                        return
                    violations: list[dict[str, Any]] = []
                else:
                    violations = runtime_validate.run_checks(text, node["checks"])
                    if violations:
                        _event(run_id, "validation_fail", node=node_id, target=target, violations=violations)
                        if node["on_fail"] == "fail":
                            yield from _fail(run_id, f"validation failed at {node_id}")
                            return
                        runtime_interrupts.create_interrupt(
                            run_id,
                            reason="validation_failed",
                            payload={"node": node_id, "target": target, "violations": violations},
                            node=node_id,
                        )
                        yield runtime_events.to_sse(runtime_events.read_events(run_id)[-1])
                        yield from _snapshot(run_id)
                        return
                    _event(run_id, "validation_pass", node=node_id, target=target)
                completed_nodes.append(node_id)
                next_index = node_index + 1
                next_node = ir[next_index]["id"] if next_index < len(ir) else None
                state = runtime_state.update_run_state(
                    run_id,
                    {"metadata": {
                        "node_index": next_index,
                        "completed_nodes": completed_nodes,
                        "node_outputs": node_outputs,
                        "agent_calls": agent_calls,
                        "agent_elapsed_seconds": agent_elapsed,
                        "current_node": node_id,
                    }},
                )
                runtime_checkpoint.write_checkpoint(run_id, state=state, reason=f"node:{node_id}")
                yield from _yield_event(run_id, "node_update", node=node_id, goto=next_node)
                yield from _snapshot(run_id)
                continue
            agent = node["agent"]
            agent_id = str(agent["id"])
            agent_budget = agent["budget"]
            if len(completed_nodes) >= stop["max_nodes"]:
                yield from _fail(run_id, "budget_exceeded: max_nodes")
                return
            if _elapsed_seconds(started_at) >= stop["max_seconds"]:
                yield from _fail(run_id, "budget_exceeded: max_seconds")
                return
            if int(agent_calls.get(agent_id, 0)) >= agent_budget["max_calls"]:
                yield from _fail(run_id, f"budget_exceeded: agent max_calls ({agent_id})")
                return
            if float(agent_elapsed.get(agent_id, 0.0)) >= agent_budget["seconds"]:
                yield from _fail(run_id, f"budget_exceeded: agent seconds ({agent_id})")
                return

            context = _context(objective, node_outputs)
            rendered_prompt = render_template(str(node["prompt"]), context)
            state = runtime_state.update_run_state(
                run_id, {"metadata": {"current_node": node["id"], "node_index": node_index}}
            )
            if _resolved_interrupt_action(state, str(node["id"])) == "reject":
                yield from _fail(run_id, f"rejected at gate:{node['id']}")
                return
            if node.get("gate") == "approval" and not _has_resolved_interrupt(state, str(node["id"])):
                runtime_interrupts.create_interrupt(
                    run_id,
                    reason="approval_required",
                    payload={"node": node["id"], "prompt": rendered_prompt, "objective": objective},
                    node=str(node["id"]),
                )
                yield runtime_events.to_sse(runtime_events.read_events(run_id)[-1])
                yield from _snapshot(run_id)
                return

            messages = [
                {"role": "user", "content": f"SYSTEM INSTRUCTIONS:\n{agent['system_prompt']}"},
                {"role": "user", "content": rendered_prompt},
            ]
            routed = runtime_agents.resolve_provider(agent)
            provider = get_provider(routed["provider"])
            call_started_at = runtime_state.now_iso()
            output: list[str] = []
            for item in provider.stream_chat(messages, session_id=None, model=routed["model"]):
                item_type = item.get("type")
                if item_type == "delta":
                    text = str(item.get("text") or "")
                    output.append(text)
                    yield from _yield_event(run_id, "assistant_delta", node=node["id"], text=text)
                elif item_type == "reasoning":
                    yield from _yield_event(run_id, "reasoning", node=node["id"], text=str(item.get("text") or ""))
                elif item_type == "done":
                    runtime_state.update_run_state(run_id, {"usage": item.get("usage", {})})
                    agent_calls[agent_id] = int(agent_calls.get(agent_id, 0)) + 1
                    agent_elapsed[agent_id] = float(agent_elapsed.get(agent_id, 0.0)) + _elapsed_seconds(call_started_at)
                elif item_type == "error":
                    yield from _fail(run_id, str(item.get("message") or "Provider error"))
                    return

            node_id = str(node["id"])
            node_outputs[node_id] = "".join(output)
            full = node_outputs[node_id]
            rel = runtime_artifacts.write_node_artifact(run_id, node_id, full)
            _event(run_id, "artifact_written", node=node_id, path=rel, chars=len(full))
            for spawn in node.get("spawn", []):
                spawn_agent = spawn["agent"]
                spawn_agent_id = str(spawn_agent["id"])
                tier = str(spawn_agent["risk_tier"])
                if tier in governance.effective_blocked_tiers():
                    governance.record_denial(run_id, [f"risk_tier '{tier}' blocked for agent '{spawn_agent_id}'"])
                    yield from _yield_event(run_id, "error", node=node_id, agent_id=spawn_agent_id, message=f"spawn denied for agent '{spawn_agent_id}' at node '{node_id}': risk_tier '{tier}' blocked")
                    continue
                rendered_objective = render_template(str(spawn["objective"]), _context(objective, node_outputs))
                child = runtime_children.create_child_run(run_id, {
                    "objective": rendered_objective,
                    "agent_id": spawn_agent_id,
                    "budget": spawn_agent["budget"],
                    "skills": spawn_agent.get("skills", []),
                })
                child_run_id = str(child["child_run"]["run_id"])
                child_output = yield from _run_child(
                    parent_run_id=run_id,
                    node_id=node_id,
                    objective=rendered_objective,
                    agent=spawn_agent,
                    child_run_id=child_run_id,
                )
                if child_output is not None:
                    node_outputs[f"{node_id}_claims"] = child_output
            completed_nodes.append(str(node["id"]))
            next_index = node_index + 1
            next_node = ir[next_index]["id"] if next_index < len(ir) else None
            state = runtime_state.update_run_state(
                run_id,
                {"metadata": {
                    "node_index": next_index,
                    "completed_nodes": completed_nodes,
                    "node_outputs": node_outputs,
                    "agent_calls": agent_calls,
                    "agent_elapsed_seconds": agent_elapsed,
                    "current_node": node["id"],
                }},
            )
            runtime_checkpoint.write_checkpoint(run_id, state=state, reason=f"node:{node['id']}")
            yield from _yield_event(run_id, "node_update", node=node["id"], goto=next_node)
            yield from _snapshot(run_id)
    except Exception as exc:
        yield from _fail(run_id, str(exc))


def _load_workflow(workflow_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = workflow.workflow_path(workflow_id)
    source = path.read_text(encoding="utf-8")
    data = workflow.parse_workflow(source)
    errors = workflow.validate_workflow(data)
    if errors:
        raise ValueError(errors)
    return data, workflow.build_ir(data)


def create_workflow_run_stream(workflow_id: str, objective: str) -> Iterator[str]:
    data, ir = _load_workflow(workflow_id)
    run_started_at = runtime_state.now_iso()
    run = runtime_state.create_run(
        agent_id="lead",
        messages=[{"id": "user-objective", "role": "user", "content": objective}],
        metadata={
            "objective": objective,
            "workflow_id": workflow_id,
            "node_index": 0,
            "completed_nodes": [],
            "node_outputs": {},
            "run_started_at": run_started_at,
            "agent_calls": {},
            "agent_elapsed_seconds": {},
        },
    )
    run_id = str(run["run_id"])
    yield from _yield_event(run_id, "debug", message="workflow run created", thread_id=run["thread_id"])
    yield from run_workflow(ir, stop=data["stop"], objective=objective, run_id=run_id)


def resume_workflow_run_stream(run_id: str, interrupt_id: str, payload: dict[str, Any]) -> Iterator[str]:
    resume_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
    result = runtime_interrupts.resolve_interrupt(run_id, interrupt_id, resume_payload=resume_payload, action=str(payload.get("action") or "resume"))
    yield runtime_events.to_sse(runtime_events.read_events(run_id)[-1])
    state = result["state"]
    metadata = _metadata(state)
    workflow_id = str(metadata.get("workflow_id") or "")
    data, ir = _load_workflow(workflow_id)
    yield from run_workflow(ir, stop=data["stop"], objective=str(metadata.get("objective") or ""), run_id=run_id)
