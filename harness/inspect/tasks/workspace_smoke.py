from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import Score, Target, accuracy, scorer
from inspect_ai.solver import Generate, TaskState, solver


ROOT = Path(__file__).resolve().parents[3]
LOCAL_HARNESS = ROOT / "harness" / "run_harness.py"


def _parse_summary(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "status" in data and "results" in data:
            return data
    return None


@solver
def local_workspace_smoke() -> Any:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        command = [
            sys.executable,
            str(LOCAL_HARNESS),
            "--suite",
            "workspace-smoke",
            "--json",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        summary = _parse_summary(completed.stdout)
        payload: dict[str, Any] = {
            "command": command,
            "cwd": str(ROOT),
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout.splitlines()[-20:],
            "stderr_tail": completed.stderr.splitlines()[-20:],
            "summary": summary,
        }
        if summary:
            payload["status"] = summary.get("status")
            payload["passed"] = summary.get("passed")
            payload["failed"] = summary.get("failed")
            payload["report"] = str(ROOT / "harness" / "runs" / summary["run_id"] / "report.md")
        else:
            payload["status"] = "fail"
            payload["error"] = "Could not parse local harness summary JSON from stdout."

        state.metadata["local_harness"] = payload
        state.output = ModelOutput(
            model="local/workspace-smoke",
            completion=json.dumps(payload, ensure_ascii=False, indent=2),
        )
        state.completed = True
        return state

    return solve


@scorer(metrics=[accuracy()])
def local_harness_passed() -> Any:
    async def score(state: TaskState, target: Target) -> Score:
        payload = state.metadata.get("local_harness", {})
        summary = payload.get("summary") if isinstance(payload, dict) else None
        passed = (
            isinstance(payload, dict)
            and payload.get("returncode") == 0
            and isinstance(summary, dict)
            and summary.get("status") == "pass"
            and summary.get("failed") == 0
        )
        explanation = "Local harness passed."
        if not passed:
            explanation = json.dumps(payload, ensure_ascii=False, indent=2)
        return Score(
            value=passed,
            answer=str(payload.get("status", "unknown")) if isinstance(payload, dict) else "unknown",
            explanation=explanation,
            metadata=payload if isinstance(payload, dict) else {},
        )

    return score


@task
def workspace_smoke() -> Task:
    return Task(
        dataset=[
            Sample(
                id="workspace-smoke",
                input="Run the Opus local workspace smoke harness and score pass/fail.",
                target="pass",
            )
        ],
        solver=local_workspace_smoke(),
        scorer=local_harness_passed(),
        model="mockllm/model",
        name="workspace_smoke",
        version=1,
        metadata={
            "harness": "local+inspect",
            "local_suite": "workspace-smoke",
            "requires_model_api": False,
        },
    )
