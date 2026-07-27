from __future__ import annotations

from typing import Any

from services import runtime_checkpoint, runtime_events, runtime_state


def create_interrupt(
    run_id: str,
    *,
    reason: str,
    payload: dict[str, Any] | None = None,
    node: str | None = None,
) -> dict[str, Any]:
    runtime_state.validate_id("run", run_id)
    interrupt = {
        "interrupt_id": runtime_state.new_id("interrupt"),
        "run_id": run_id,
        "node": node,
        "status": "pending",
        "reason": str(reason),
        "payload": dict(payload or {}),
        "created_at": runtime_state.now_iso(),
        "resolved_at": None,
        "resume_payload": None,
    }
    state = runtime_state.update_run_state(
        run_id,
        {
            "status": "interrupted",
            "interrupts": [interrupt],
            "metadata": {"interrupted_at": interrupt["created_at"], "next_node": node},
        },
    )
    runtime_events.append_event(
        run_id,
        "interrupt",
        interrupt_id=interrupt["interrupt_id"],
        reason=interrupt["reason"],
        node=node,
        payload=interrupt["payload"],
    )
    runtime_checkpoint.write_checkpoint(run_id, state=state, reason="interrupt")
    return interrupt


def list_interrupts(run_id: str, status: str | None = None) -> list[dict[str, Any]]:
    state = runtime_state.read_run(run_id)
    rows = [item for item in state.get("interrupts", []) if isinstance(item, dict)]
    if status is not None:
        rows = [item for item in rows if item.get("status") == status]
    return rows


def get_interrupt(run_id: str, interrupt_id: str) -> dict[str, Any]:
    runtime_state.validate_id("interrupt", interrupt_id)
    for item in list_interrupts(run_id):
        if item.get("interrupt_id") == interrupt_id:
            return item
    raise FileNotFoundError(f"Interrupt not found: {interrupt_id}")


def resolve_interrupt(
    run_id: str,
    interrupt_id: str,
    *,
    resume_payload: dict[str, Any] | None = None,
    action: str = "resume",
) -> dict[str, Any]:
    interrupt = get_interrupt(run_id, interrupt_id)
    if interrupt.get("status") != "pending":
        raise ValueError(f"Interrupt is not pending: {interrupt_id}")
    resolved = dict(interrupt)
    resolved["status"] = "resolved"
    resolved["action"] = str(action or "resume")
    resolved["resolved_at"] = runtime_state.now_iso()
    resolved["resume_payload"] = dict(resume_payload or {})

    state = runtime_state.update_run_state(
        run_id,
        {
            "status": "running",
            "interrupts": [resolved],
            "metadata": {
                "last_resume_payload": resolved["resume_payload"],
                "resumed_interrupt_id": interrupt_id,
                "resumed_at": resolved["resolved_at"],
            },
        },
    )
    runtime_events.append_event(
        run_id,
        "debug",
        message="interrupt resolved",
        interrupt_id=interrupt_id,
        action=resolved["action"],
    )
    runtime_checkpoint.write_checkpoint(run_id, state=state, reason="interrupt-resolved")
    return {"interrupt": resolved, "state": state}
