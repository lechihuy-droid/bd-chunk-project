from __future__ import annotations

import json
from typing import Any

import config
from services import runtime_checkpoint, runtime_events, runtime_state


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _ensure_subset(child: list[str], parent: list[str], label: str) -> None:
    if not parent:
        return
    expanded = sorted(set(child) - set(parent))
    if expanded:
        raise ValueError(f"Child run cannot expand allowed {label}: {', '.join(expanded)}")


def _packet(parent: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    metadata = parent.get("metadata") if isinstance(parent.get("metadata"), dict) else {}
    parent_paths = _as_str_list(metadata.get("allowed_paths"))
    parent_tools = _as_str_list(metadata.get("allowed_tools"))
    child_paths = _as_str_list(raw.get("allowed_paths"))
    child_tools = _as_str_list(raw.get("allowed_tools"))
    _ensure_subset(child_paths, parent_paths, "paths")
    _ensure_subset(child_tools, parent_tools, "tools")

    objective = str(raw.get("objective") or "").strip()
    if not objective:
        raise ValueError("child objective is required")
    return {
        "objective": objective,
        "agent_id": str(raw.get("agent_id") or raw.get("agent") or "researcher"),
        "allowed_paths": child_paths,
        "allowed_tools": child_tools,
        "skills": _as_str_list(raw.get("skills")),
        "budget": raw.get("budget") if isinstance(raw.get("budget"), dict) else {},
        "timeout_seconds": int(raw.get("timeout_seconds") or config.RUNTIME_CHILD_TIMEOUT_SECONDS),
        "use_gitjob": bool(raw.get("use_gitjob")),
    }


def _parent_child_rows(parent_run_id: str) -> list[dict[str, Any]]:
    parent = runtime_state.read_run(parent_run_id)
    return [item for item in parent.get("child_runs", []) if isinstance(item, dict)]


def create_child_run(parent_run_id: str, raw_packet: dict[str, Any]) -> dict[str, Any]:
    parent = runtime_state.read_run(parent_run_id)
    parent_metadata = parent.get("metadata") if isinstance(parent.get("metadata"), dict) else {}
    if parent_metadata.get("agent_id", "lead") != "lead":
        raise ValueError("Only the lead runtime can spawn child runs")
    child_rows = _parent_child_rows(parent_run_id)
    if len(child_rows) >= int(config.RUNTIME_MAX_CHILD_RUNS):
        raise ValueError("child run limit exceeded")

    packet = _packet(parent, raw_packet)
    child = runtime_state.create_run(
        agent_id=packet["agent_id"],
        messages=[{"id": "task", "role": "user", "content": packet["objective"]}],
        metadata={
            "parent_run_id": parent_run_id,
            "child_packet": packet,
            "allowed_paths": packet["allowed_paths"],
            "allowed_tools": packet["allowed_tools"],
            "skills": packet["skills"],
            "timeout_seconds": packet["timeout_seconds"],
        },
    )
    child_run_id = str(child["run_id"])
    artifact_path = runtime_state.runtime_path("run", child_run_id, "artifacts", "task_packet.json")
    artifact_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    job_id = None
    if packet["use_gitjob"]:
        from services import gitjobs

        job = gitjobs.create_job(packet["objective"], agent="codex", allow_override=False)
        job_id = str(job.get("id") or "")

    child = runtime_state.update_run_state(
        child_run_id,
        {
            "artifacts": [
                {
                    "id": "task-packet",
                    "path": "artifacts/task_packet.json",
                    "type": "task_packet",
                    "title": "Child task packet",
                }
            ],
            "metadata": {"job_id": job_id} if job_id else {},
        },
    )
    child_summary = {
        "run_id": child_run_id,
        "status": child["status"],
        "agent_id": packet["agent_id"],
        "objective": packet["objective"],
        "job_id": job_id,
        "created_at": runtime_state.now_iso(),
    }
    parent_state = runtime_state.update_run_state(parent_run_id, {"child_runs": [child_summary]})
    runtime_events.append_event(parent_run_id, "child_run", child_run=child_summary)
    runtime_events.append_event(child_run_id, "debug", message="child run created", parent_run_id=parent_run_id)
    runtime_checkpoint.write_checkpoint(parent_run_id, state=parent_state, reason="child-run-created")
    runtime_checkpoint.write_checkpoint(child_run_id, state=child, reason="child-run-created")
    return {"child_run": child, "parent": parent_state, "task_packet": packet}


def fail_child_run(child_run_id: str, message: str, *, timed_out: bool = False) -> dict[str, Any]:
    child = runtime_state.read_run(child_run_id)
    metadata = child.get("metadata") if isinstance(child.get("metadata"), dict) else {}
    parent_run_id = str(metadata.get("parent_run_id") or "")
    child = runtime_state.update_run_state(
        child_run_id,
        {"status": "failed", "metadata": {"error": message, "timed_out": bool(timed_out)}},
    )
    runtime_events.append_event(child_run_id, "error", message=message, timed_out=bool(timed_out))
    if parent_run_id:
        parent_update = {
            "run_id": child_run_id,
            "status": "failed",
            "error": message,
            "timed_out": bool(timed_out),
            "finished_at": runtime_state.now_iso(),
        }
        parent = runtime_state.update_run_state(parent_run_id, {"child_runs": [parent_update]})
        runtime_events.append_event(parent_run_id, "child_run", child_run=parent_update)
        runtime_checkpoint.write_checkpoint(parent_run_id, state=parent, reason="child-run-failed")
    runtime_checkpoint.write_checkpoint(child_run_id, state=child, reason="child-run-failed")
    return child


def complete_child_run(child_run_id: str, artifacts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    child = runtime_state.read_run(child_run_id)
    metadata = child.get("metadata") if isinstance(child.get("metadata"), dict) else {}
    parent_run_id = str(metadata.get("parent_run_id") or "")
    artifact_rows = [dict(item) for item in (artifacts or []) if isinstance(item, dict)]
    child = runtime_state.update_run_state(child_run_id, {"status": "succeeded", "artifacts": artifact_rows})
    runtime_events.append_event(child_run_id, "done", status="succeeded")
    if parent_run_id:
        parent_artifacts = [
            {**artifact, "source_run_id": child_run_id}
            for artifact in artifact_rows
        ]
        parent_update = {
            "child_runs": [
                {
                    "run_id": child_run_id,
                    "status": "succeeded",
                    "finished_at": runtime_state.now_iso(),
                }
            ],
            "artifacts": parent_artifacts,
        }
        parent = runtime_state.update_run_state(parent_run_id, parent_update)
        runtime_events.append_event(parent_run_id, "child_run", child_run={"run_id": child_run_id, "status": "succeeded"})
        runtime_checkpoint.write_checkpoint(parent_run_id, state=parent, reason="child-run-succeeded")
    runtime_checkpoint.write_checkpoint(child_run_id, state=child, reason="child-run-succeeded")
    return child
