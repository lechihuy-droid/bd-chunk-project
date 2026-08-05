from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import re
import threading
import time
from typing import Any

import config
from services import boundary, execution, governance, runtime_agents, runtime_artifacts, runtime_checkpoint, runtime_children, runtime_events, runtime_interrupts, runtime_state, runtime_validate, skill_library, workflow
from services.providers import procs


_TEMPLATE_REF = re.compile(r"{{(.*?)}}")
_RENDER_LINE_LIMIT = 1000
_RENDER_TOTAL_LINES = 200


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


def _context(objective: str, node_outputs: dict[str, Any], inputs: str = "") -> dict[str, str]:
    context = {"objective": objective, "inputs": inputs}
    for key, value in node_outputs.items():
        context[str(key)] = str(value)
        context[f"{key}_output"] = str(value)
    return context


def _resolve_in_runtime_root(path: Path, base: Path) -> Path:
    """Use the project boundary guard, preserving isolated test runtime roots."""
    try:
        return boundary.resolve_in_root(path, base)
    except PermissionError:
        resolved = path.resolve()
        try:
            resolved.relative_to(base.resolve())
        except ValueError as exc:
            raise PermissionError(f"Path is outside allowed root: {resolved}") from exc
        return resolved


def _render_argv(target: dict[str, Any], props_path: Path) -> list[str]:
    command = target.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(value, str) for value in command):
        raise ValueError("Render target command must be a non-empty argv list")
    argv: list[str] = []
    for value in command:
        if "{" in value or "}" in value:
            if value != "{props}":
                raise ValueError("Render target command may only contain the {props} placeholder")
            argv.append(str(props_path))
        else:
            argv.append(value)
    return argv


def _render_env(target: dict[str, Any]) -> dict[str, str]:
    additions = target.get("env")
    if not isinstance(additions, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in additions.items()):
        raise ValueError("Render target env must be a string mapping")
    return {"PATH": os.environ.get("PATH", ""), **additions}


def _reported_output(report: Path, output_root: Path) -> Path | None:
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    values: list[str] = []
    stack: list[Any] = [data]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
        elif isinstance(value, str) and value.lower().endswith((".mp4", ".mov", ".webm")):
            values.append(value)
    for value in values:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = report.parent / candidate
        try:
            candidate = boundary.resolve_in_root(candidate, output_root)
        except PermissionError:
            continue
        if candidate.is_file():
            return candidate
    return None


def _find_render_output(target: dict[str, Any], started: float) -> Path:
    cwd = Path(target["cwd"])
    output_root = boundary.resolve_in_root(cwd / str(target["output_hint"]), cwd)
    if not output_root.is_dir():
        raise FileNotFoundError(f"Render output directory not found: {output_root}")
    reports = sorted(output_root.rglob("render-report.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for report in reports:
        if report.stat().st_mtime + 1 < started:
            continue
        output = _reported_output(report, output_root)
        if output is not None:
            return output
    videos = sorted(
        (path for path in output_root.rglob("*") if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".webm"} and path.stat().st_mtime + 1 >= started),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if videos:
        return boundary.resolve_in_root(videos[0], output_root)
    raise FileNotFoundError("Renderer completed but produced no video artifact")


def _run_render_node(run_id: str, node: dict[str, Any], node_outputs: dict[str, Any]) -> Iterator[str]:
    target = dict(node["render_target"])
    props_from = str(node["props_from"])
    artifacts_dir = runtime_state.runtime_path("run", run_id, "artifacts")
    props_path = _resolve_in_runtime_root(artifacts_dir / f"{node['id']}-props.json", artifacts_dir)
    props_path.write_text(str(node_outputs.get(props_from, "")), encoding="utf-8")
    argv = _render_argv(target, props_path)
    cwd = boundary.resolve_in_root(Path(target["cwd"]))
    timeout = target.get("timeout_seconds")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise ValueError("Render target timeout_seconds must be positive")
    yield from _yield_event(run_id, "node_update", node=node["id"], status="running")
    started = time.time()
    proc_id = procs.registry.spawn(argv, cwd=cwd, env=_render_env(target), timeout=float(timeout), provider="render")
    process = procs.registry.get(proc_id)
    if process is None:
        raise RuntimeError("Render process was not registered")
    lines: queue.Queue[tuple[str, str | None]] = queue.Queue()

    def drain(stream: Any, label: str) -> None:
        for line in iter(stream.readline, ""):
            lines.put((label, line.rstrip()))
        lines.put((label, None))

    readers = [threading.Thread(target=drain, args=(process.stdout, "stdout"), daemon=True), threading.Thread(target=drain, args=(process.stderr, "stderr"), daemon=True)]
    for reader in readers:
        reader.start()
    stderr: list[str] = []
    emitted = 0
    try:
        while process.poll() is None or any(reader.is_alive() for reader in readers):
            try:
                label, line = lines.get(timeout=0.2)
            except queue.Empty:
                continue
            if line is None:
                continue
            if label == "stderr":
                stderr.append(line)
                stderr[:] = stderr[-30:]
            if emitted < _RENDER_TOTAL_LINES:
                yield from _yield_event(run_id, "node_update", node=node["id"], status="running", stream=label, message=line[:_RENDER_LINE_LIMIT])
                emitted += 1
        while not lines.empty():
            label, line = lines.get_nowait()
            if line is not None and label == "stderr":
                stderr.append(line)
                stderr[:] = stderr[-30:]
        if procs.registry.is_timed_out(proc_id):
            raise RuntimeError(f"render timed out after {timeout} seconds: {' '.join(stderr[-10:])}")
        if process.returncode != 0:
            raise RuntimeError(f"render exited with code {process.returncode}: {' '.join(stderr[-10:])}")
        output = _find_render_output(target, started)
        artifact = runtime_artifacts.register_file_artifact(run_id, str(node["id"]), output)
        yield from _yield_event(run_id, "artifact_written", node=node["id"], path=artifact["path"], size=artifact["size"])
    finally:
        procs.registry.unregister(proc_id)


def _agent_system_prompt(agent: dict[str, Any]) -> tuple[str, list[str]]:
    pins = agent.get("skill_pins")
    if isinstance(pins, list):
        contents, truncated = skill_library.load_pinned_skill_prompt_contents(pins)
        warnings = []
    else:
        contents, truncated, missing = skill_library.load_skill_prompt_contents(
            list(agent.get("skills") or []), skip_missing=True
        )
        warnings = [f"Skill unavailable and skipped: {name}" for name in missing]
    if truncated:
        warnings.append("Skill instructions truncated at shared prompt limit")
    return str(skill_library.system_prompt_with_skills(agent["system_prompt"], contents) or ""), warnings


def _snapshot_agent(agent: dict[str, Any]) -> dict[str, Any]:
    frozen = dict(agent)
    frozen["resolved_route"] = runtime_agents.resolve_provider(frozen)
    frozen["skill_pins"] = skill_library.pin_skill_prompt_contents(list(frozen.get("skills") or []))
    return frozen


def _snapshot_ir(ir: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frozen: list[dict[str, Any]] = []
    for node in ir:
        copy = dict(node)
        if isinstance(copy.get("agent"), dict):
            copy["agent"] = _snapshot_agent(copy["agent"])
        copy["spawn"] = [
            {**dict(spawn), "agent": _snapshot_agent(dict(spawn["agent"]))}
            for spawn in copy.get("spawn", [])
        ]
        frozen.append(copy)
    return frozen


def _workflow_snapshot(data: dict[str, Any], ir: list[dict[str, Any]]) -> dict[str, Any]:
    frozen_ir = _snapshot_ir(ir)
    profiles: dict[str, dict[str, Any]] = {}
    for node in frozen_ir:
        for agent in [node.get("agent"), *(spawn.get("agent") for spawn in node.get("spawn", []))]:
            if isinstance(agent, dict):
                profiles[str(agent["id"])] = dict(agent)
    return {"definition": deepcopy(data), "ir": frozen_ir, "stop": deepcopy(data["stop"]), "agent_profiles": profiles}


def _snapshot_inputs(state: dict[str, Any], ir: list[dict[str, Any]], stop: dict[str, Any], objective: str) -> tuple[list[dict[str, Any]], dict[str, Any], str, str]:
    snapshot = _metadata(state).get("workflow_snapshot")
    if not isinstance(snapshot, dict):
        runtime_state.update_run_state(str(state["run_id"]), {"metadata": {"snapshot_status": "legacy_live_read"}})
        return ir, stop, objective, str(_metadata(state).get("inputs") or "")
    frozen_ir = snapshot.get("ir")
    frozen_stop = snapshot.get("stop")
    if not isinstance(frozen_ir, list) or not isinstance(frozen_stop, dict):
        raise ValueError("Invalid workflow snapshot")
    metadata = _metadata(state)
    return frozen_ir, frozen_stop, str(metadata.get("objective") or objective), str(metadata.get("inputs") or "")


def _provider_route(agent: dict[str, Any]) -> dict[str, Any]:
    route = agent.get("resolved_route")
    return dict(route) if isinstance(route, dict) else runtime_agents.resolve_provider(agent)


def _tool_policy(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "permission": agent["permission"],
        "allowed_tools": list(agent.get("allowed_tools") or []),
        "allowed_paths": list(agent.get("allowed_paths") or []),
    }


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
        system_prompt, warnings = _agent_system_prompt(agent)
        for message in warnings:
            yield from _yield_event(parent_run_id, "warning", child_run_id=child_run_id, node=node_id, agent_id=agent_id, message=message)
        messages = [
            {"role": "user", "content": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"},
            {"role": "user", "content": objective},
        ]
        call_started_at = runtime_state.now_iso()
        output: list[str] = []
        route = _provider_route(agent)
        request = execution.ExecutionRequest(
            correlation_id=child_run_id, provider_id=str(route["provider"]), model=route.get("model"),
            messages=messages, tool_policy=_tool_policy(agent), limits=dict(agent.get("budget") or {}),
        )
        for item in execution.execute(request):
            item_type = item.get("type")
            if item_type == "delta":
                text = str(item.get("text") or "")
                output.append(text)
                yield from _yield_event(parent_run_id, "child_run", child_run_id=child_run_id, parent_run_id=parent_run_id, node=node_id, agent_id=agent_id, text=text)
            elif item_type == "reasoning":
                yield from _yield_event(parent_run_id, "child_run", child_run_id=child_run_id, parent_run_id=parent_run_id, node=node_id, agent_id=agent_id, reasoning=str(item.get("text") or ""))
            elif item_type in {"tool_call", "tool_result"}:
                yield from _yield_event(parent_run_id, "child_run", child_run_id=child_run_id, parent_run_id=parent_run_id, node=node_id, agent_id=agent_id, tool_event=dict(item))
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
    ir, stop, objective, inputs = _snapshot_inputs(state, ir, stop, objective)
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
            if node.get("type") == "render":
                node_id = str(node["id"])
                tier = str(node["risk_tier"])
                state = runtime_state.update_run_state(
                    run_id, {"metadata": {"current_node": node_id, "node_index": node_index}}
                )
                if tier in governance.effective_blocked_tiers():
                    governance.record_denial(run_id, [f"risk_tier '{tier}' blocked for render '{node_id}'"])
                    yield from _fail(run_id, f"render denied at {node_id}: risk_tier '{tier}' blocked")
                    return
                if _resolved_interrupt_action(state, node_id) == "reject":
                    yield from _fail(run_id, f"rejected at gate:{node_id}")
                    return
                if node.get("gate") == "approval" and not _has_resolved_interrupt(state, node_id):
                    runtime_interrupts.create_interrupt(
                        run_id,
                        reason="approval_required",
                        payload={"node": node_id, "target": node["target"], "props_from": node["props_from"]},
                        node=node_id,
                    )
                    yield runtime_events.to_sse(runtime_events.read_events(run_id)[-1])
                    yield from _snapshot(run_id)
                    return
                yield from _run_render_node(run_id, node, node_outputs)
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

            context = _context(objective, node_outputs, inputs)
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

            system_prompt, warnings = _agent_system_prompt(agent)
            for message in warnings:
                yield from _yield_event(run_id, "warning", node=node["id"], agent_id=agent_id, message=message)
            messages = [
                {"role": "user", "content": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"},
                {"role": "user", "content": rendered_prompt},
            ]
            call_started_at = runtime_state.now_iso()
            output: list[str] = []
            route = _provider_route(agent)
            request = execution.ExecutionRequest(
                correlation_id=run_id, provider_id=str(route["provider"]), model=route.get("model"),
                messages=messages, tool_policy=_tool_policy(agent), limits=dict(agent.get("budget") or {}),
            )
            for item in execution.execute(request):
                item_type = item.get("type")
                if item_type == "delta":
                    text = str(item.get("text") or "")
                    output.append(text)
                    yield from _yield_event(run_id, "assistant_delta", node=node["id"], text=text)
                elif item_type == "reasoning":
                    yield from _yield_event(run_id, "reasoning", node=node["id"], text=str(item.get("text") or ""))
                elif item_type in {"tool_call", "tool_result"}:
                    yield from _yield_event(run_id, item_type, node=node["id"], **{key: value for key, value in item.items() if key != "type"})
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
                rendered_objective = render_template(str(spawn["objective"]), _context(objective, node_outputs, inputs))
                child = runtime_children.create_child_run(run_id, {
                    "objective": rendered_objective,
                    "agent_id": spawn_agent_id,
                    "risk_tier": tier,
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


def create_workflow_run_stream(workflow_id: str, objective: str, inputs: str = "", input_references: list[dict[str, str]] | None = None) -> Iterator[str]:
    data, ir = _load_workflow(workflow_id)
    snapshot = _workflow_snapshot(data, ir)
    run_started_at = runtime_state.now_iso()
    metadata = {
        "objective": objective,
        "workflow_id": workflow_id,
        "node_index": 0,
        "completed_nodes": [],
        "node_outputs": {},
        "run_started_at": run_started_at,
        "agent_calls": {},
        "agent_elapsed_seconds": {},
        "workflow_snapshot": snapshot,
        "snapshot_status": "pinned",
    }
    if input_references:
        metadata.update({"inputs": inputs, "input_references": input_references})
    run = runtime_state.create_run(
        agent_id="lead",
        messages=[{"id": "user-objective", "role": "user", "content": objective}],
        metadata=metadata,
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
    snapshot = metadata.get("workflow_snapshot")
    if isinstance(snapshot, dict):
        yield from run_workflow([], stop={}, objective=str(metadata.get("objective") or ""), run_id=run_id)
        return
    workflow_id = str(metadata.get("workflow_id") or "")
    data, ir = _load_workflow(workflow_id)
    yield from run_workflow(ir, stop=data["stop"], objective=str(metadata.get("objective") or ""), run_id=run_id)
