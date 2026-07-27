from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import config
from services import suites


@dataclass
class RunStream:
    stream_id: str
    suite: str
    check: str | None
    process: subprocess.Popen[str]
    events: "queue.Queue[dict[str, Any]]" = field(default_factory=queue.Queue)
    run_id: str | None = None
    exit_code: int | None = None
    steps_done: int = 0
    steps_total: int = 0


_STREAMS: dict[str, RunStream] = {}


def _python_exe() -> str:
    bundled = config.ROOT / ".ih" / "Scripts" / "python.exe"
    if bundled.exists():
        return str(bundled)
    return sys.executable


def _suite_by_id(suite_id: str) -> dict[str, Any]:
    for suite in suites.list_suites():
        if suite.get("id") == suite_id:
            return suite
    raise ValueError(f"Unknown suite: {suite_id}")


def _validate_check(suite: dict[str, Any], check_id: str | None) -> None:
    if not check_id:
        return
    check_ids = {item.get("id") for item in suite.get("checks", []) if isinstance(item, dict)}
    if check_id not in check_ids:
        raise ValueError(f"Unknown check for suite {suite.get('id')}: {check_id}")


def _extract_run_id(line: str) -> str | None:
    text = line.strip()
    if not text.startswith("{"):
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    run_id = data.get("run_id") if isinstance(data, dict) else None
    return run_id if isinstance(run_id, str) and run_id else None


def _budget_payload(stream: RunStream) -> dict[str, Any]:
    return {
        "stream_id": stream.stream_id,
        "suite": stream.suite,
        "steps_done": stream.steps_done,
        "steps_total": stream.steps_total,
        "step_cap": config.STEP_CAP,
        "warn": stream.steps_done > int(config.STEP_CAP * 0.8),
        "tokens_used": None,
        "token_cap": None,
    }


def _update_budget_from_line(stream: RunStream, line: str) -> bool:
    text = line.strip()
    before = stream.steps_done
    if text.startswith("PASS ") or text.startswith("FAIL "):
        stream.steps_done = min(stream.steps_total or stream.steps_done + 1, stream.steps_done + 1)
    elif text.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            results = data.get("results")
            if isinstance(results, list):
                stream.steps_total = len(results)
                stream.steps_done = len(results)
    return stream.steps_done != before


def _emit_line(stream: RunStream, line: str) -> None:
    text = line.rstrip("\r\n")
    run_id = _extract_run_id(text)
    if run_id:
        stream.run_id = run_id
    stream.events.put({"type": "line", "data": text})
    if _update_budget_from_line(stream, text):
        stream.events.put({"type": "budget", "data": _budget_payload(stream)})


def _read_pipe(stream: RunStream, pipe: Any) -> None:
    if pipe is None:
        return
    try:
        for line in pipe:
            _emit_line(stream, str(line))
    finally:
        close = getattr(pipe, "close", None)
        if callable(close):
            close()


def _pump(stream: RunStream) -> None:
    readers = [
        threading.Thread(target=_read_pipe, args=(stream, stream.process.stdout), daemon=True),
        threading.Thread(target=_read_pipe, args=(stream, stream.process.stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()
    code = stream.process.wait()
    for reader in readers:
        reader.join(timeout=1.0)
    stream.exit_code = int(code)
    stream.events.put({"type": "budget", "data": _budget_payload(stream)})
    stream.events.put({"type": "exit", "data": {"code": stream.exit_code, "run_id": stream.run_id}})


def start_run(suite: str, check: str | None = None) -> str:
    suite_data = _suite_by_id(suite)
    _validate_check(suite_data, check)

    command = [
        _python_exe(),
        str(config.HARNESS_DIR / "run_harness.py"),
        "--suite",
        suite,
        "--json",
    ]
    if check:
        command.extend(["--check", check])

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    process = subprocess.Popen(
        command,
        cwd=config.ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        shell=False,
        env=env,
    )

    stream_id = uuid.uuid4().hex
    stream = RunStream(
        stream_id=stream_id,
        suite=suite,
        check=check,
        process=process,
        steps_total=1 if check else int(suite_data.get("check_count") or 0),
    )
    _STREAMS[stream_id] = stream
    threading.Thread(target=_pump, args=(stream,), daemon=True).start()
    return stream_id


def budget_status(stream_id: str) -> dict[str, Any]:
    stream = _STREAMS.get(stream_id)
    if stream is None:
        raise FileNotFoundError(f"Stream not found: {stream_id}")
    return _budget_payload(stream)


def stream_events(stream_id: str) -> Iterator[str]:
    stream = _STREAMS.get(stream_id)
    if stream is None:
        raise FileNotFoundError(f"Stream not found: {stream_id}")

    while True:
        event = stream.events.get()
        payload = json.dumps(event, ensure_ascii=False)
        yield f"event: {event['type']}\ndata: {payload}\n\n"
        if event.get("type") == "exit":
            break
