from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Iterator

import config
from services.providers import procs
from services.providers.base import ChatEvent, ProviderStatus

PROVIDER_ID = "codex"
_STATUS_TTL = 60.0
_status_cache: dict[str, Any] = {"ts": 0.0, "value": None}


def _base_cmd() -> list[str]:
    providers_cfg = getattr(config, "PROVIDERS", {})
    entry = providers_cfg.get("codex", {}) if isinstance(providers_cfg, dict) else {}
    cmd = entry.get("cmd") if isinstance(entry, dict) else None
    if isinstance(cmd, list) and cmd:
        return list(cmd)
    return ["codex"]


def _build_cmd(prompt: str, session_id: str | None, model: str | None = None, system_prompt: str | None = None) -> list[str]:
    if system_prompt and not session_id:
        prompt = f"[Agent system prompt]\n{system_prompt}\n\n[User request]\n{prompt}"
    full_prompt = f"FRESH START\n\n{prompt}"
    base = _base_cmd()
    options = ["-s", "read-only", "--skip-git-repo-check", "--json"]
    if model:
        options += ["-m", model]
    if session_id:
        # Resume path — verified against real Codex CLI 0.144.3 (B3 gate):
        # exec options must precede the `resume` subcommand per clap grammar
        # `codex exec [OPTIONS] resume [SESSION_ID] [PROMPT]`.
        return base + ["exec", *options, "resume", session_id, full_prompt]
    return base + ["exec", *options, full_prompt]


def status() -> ProviderStatus:
    now = time.monotonic()
    cached = _status_cache.get("value")
    if cached is not None and now - float(_status_cache.get("ts") or 0.0) < _STATUS_TTL:
        return cached  # type: ignore[return-value]

    available = False
    version: str | None = None
    detail = "not_installed"
    try:
        result = subprocess.run(
            procs.resolve_cmd([*_base_cmd(), "--version"]),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=10,
        )
        if result.returncode == 0:
            available = True
            version = (result.stdout or result.stderr or "").strip() or None
            detail = "ok"
        else:
            detail = ((result.stderr or "").strip() or (result.stdout or "").strip() or f"exit code {result.returncode}")[:200]
    except FileNotFoundError:
        detail = "not_installed"
    except (OSError, subprocess.TimeoutExpired) as exc:
        detail = str(exc).strip()[:200]

    value: ProviderStatus = {
        "id": PROVIDER_ID,
        "available": available,
        "version": version,
        "detail": detail,
        "capabilities": {"stream": True, "resume": True, "models": None},
    }
    _status_cache["ts"] = now
    _status_cache["value"] = value
    return value


def _latest_user_prompt(messages: list[dict[str, str]]) -> str:
    for item in reversed(messages):
        if item.get("role") == "user":
            return item.get("content", "")
    return messages[-1].get("content", "") if messages else ""


def _text_from_line(data: dict[str, Any]) -> str | None:
    # codex exec --json JSONL: item.completed events carry the agent message text.
    item = data.get("item")
    if isinstance(item, dict) and item.get("type") in {"agent_message", "reasoning"}:
        text = item.get("text")
        if isinstance(text, str) and text:
            return text
    delta = data.get("delta")
    if isinstance(delta, str) and delta and data.get("type") in {"agent_message_delta", "item.delta"}:
        return delta
    return None


def _usage_from_line(data: dict[str, Any]) -> dict[str, int] | None:
    if data.get("type") != "token_count":
        return None
    info = data.get("usage")
    if not isinstance(info, dict):
        info = data.get("info") if isinstance(data.get("info"), dict) else None
    if not isinstance(info, dict):
        return None
    nested = info.get("total_token_usage")
    if isinstance(nested, dict):
        info = nested
    input_tokens = info.get("input_tokens")
    output_tokens = info.get("output_tokens")
    if input_tokens is None and output_tokens is None:
        return None
    try:
        input_tokens = int(input_tokens or 0)
    except (TypeError, ValueError):
        input_tokens = 0
    try:
        output_tokens = int(output_tokens or 0)
    except (TypeError, ValueError):
        output_tokens = 0
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": input_tokens + output_tokens}


def _is_end_event(data: dict[str, Any]) -> bool:
    return data.get("type") in {"turn.completed", "task_complete", "session.completed"}


def _usage_file() -> Path:
    default = config.HUB_DIR / ".cache" / "chat_usage.jsonl"
    value = getattr(config, "CHAT_USAGE_FILE", default)
    return value if isinstance(value, Path) else default


def _append_usage_event(usage: dict[str, int]) -> None:
    try:
        usage_file = _usage_file()
        usage_file.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "ts": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
            "source": "chat",
            "model": "cli:codex",
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "cache_read_tokens": 0,
            "cache_creation_tokens": 0,
            "total_tokens": usage["total_tokens"],
            "calls": 1,
        }
        with usage_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    except OSError:
        pass


def stream_chat(
    messages: list[dict[str, str]],
    session_id: str | None = None,
    model: str | None = None,
    system_prompt: str | None = None,
) -> Iterator[ChatEvent]:
    prompt = _latest_user_prompt(messages)
    cmd = _build_cmd(prompt, session_id, model=model, system_prompt=system_prompt)
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    timeout = float(getattr(config, "CHAT_CLI_TIMEOUT", 300))

    try:
        proc_id = procs.registry.spawn(
            cmd,
            cwd=getattr(config, "ROOT", None),
            env=env,
            timeout=timeout,
            provider=PROVIDER_ID,
            stdin=subprocess.DEVNULL,
        )
    except procs.BusyError as exc:
        yield {"type": "error", "message": str(exc), "code": 429}
        return

    process = procs.registry.get(proc_id)
    if process is None or process.stdout is None:
        procs.registry.unregister(proc_id)
        yield {"type": "error", "message": "codex process failed to start", "code": None}
        return

    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    result_session_id: str | None = session_id
    timed_out = False
    saw_success_event = False
    stream_error: str | None = None
    stderr = ""
    returncode: int | None = None
    try:
        for raw_line in process.stdout:
            line = raw_line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict):
                continue

            data_type = str(data.get("type") or "")
            if data_type in {"error", "turn.failed", "task.failed", "session.failed"} or isinstance(data.get("error"), (str, dict)):
                error = data.get("error")
                if isinstance(error, dict):
                    error = error.get("message") or error.get("detail") or error.get("error")
                stream_error = str(error or data.get("message") or "codex reported an error")
                continue

            text = _text_from_line(data)
            if text:
                saw_success_event = True
                yield {"type": "delta", "text": text}

            line_usage = _usage_from_line(data)
            if line_usage is not None:
                usage = line_usage

            sid = data.get("session_id") or data.get("conversation_id")
            if isinstance(sid, str) and sid:
                result_session_id = sid

            if _is_end_event(data):
                saw_success_event = True
    finally:
        timed_out = procs.registry.is_timed_out(proc_id)
        returncode = process.returncode
        if process.stderr is not None:
            stderr = process.stderr.read().strip()
        procs.registry.unregister(proc_id)

    if timed_out:
        yield {"type": "error", "message": f"codex timed out after {int(timeout)}s", "code": None}
        return
    if stream_error is not None:
        yield {"type": "error", "message": stream_error, "code": None}
        return
    if returncode not in (None, 0):
        yield {"type": "error", "message": stderr or f"codex exited with code {returncode}", "code": None}
        return
    if stderr and not saw_success_event:
        yield {"type": "error", "message": stderr, "code": None}
        return

    _append_usage_event(usage)
    yield {"type": "done", "usage": usage, "session_id": result_session_id}
