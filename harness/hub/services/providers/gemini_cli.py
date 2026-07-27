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

PROVIDER_ID = "gemini"
_STATUS_TTL = 60.0
_status_cache: dict[str, Any] = {"ts": 0.0, "value": None}


def _base_cmd() -> list[str]:
    providers_cfg = getattr(config, "PROVIDERS", {})
    entry = providers_cfg.get(PROVIDER_ID, {}) if isinstance(providers_cfg, dict) else {}
    cmd = entry.get("cmd") if isinstance(entry, dict) else None
    return list(cmd) if isinstance(cmd, list) and cmd else ["gemini"]


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
            procs.resolve_cmd([*_base_cmd(), "--version"]), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
            errors="replace", shell=False, timeout=10,
        )
        if result.returncode == 0:
            available = True
            version = (result.stdout or result.stderr or "").strip() or None
            detail = "ok"
        else:
            detail = (result.stderr or result.stdout or f"exit code {result.returncode}").strip()[:200]
    except FileNotFoundError:
        detail = "not_installed"
    except (OSError, subprocess.TimeoutExpired) as exc:
        detail = str(exc).strip()[:200]

    value: ProviderStatus = {
        "id": PROVIDER_ID, "available": available, "version": version, "detail": detail,
        "capabilities": {"stream": True, "resume": False, "models": None},
    }
    _status_cache["ts"] = now
    _status_cache["value"] = value
    return value


def _transcript(messages: list[dict[str, str]]) -> str:
    text = "\n".join(
        f"{item.get('role', 'user').capitalize()}: {item.get('content', '')}"
        for item in messages if item.get("content")
    )
    return text[-4000:]


def _build_cmd(messages: list[dict[str, str]], system_prompt: str | None = None) -> list[str]:
    transcript = _transcript(messages)
    if system_prompt:
        transcript = f"[Agent system prompt]\n{system_prompt}\n\n[User request]\n{transcript}"
    return [*_base_cmd(), "-p", transcript]


def _usage_file() -> Path:
    default = config.HUB_DIR / ".cache" / "chat_usage.jsonl"
    value = getattr(config, "CHAT_USAGE_FILE", default)
    return value if isinstance(value, Path) else default


def _append_usage_event(usage: dict[str, int]) -> None:
    try:
        usage_file = _usage_file()
        usage_file.parent.mkdir(parents=True, exist_ok=True)
        event = {"ts": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"), "source": "chat", "model": "cli:gemini", "input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"], "cache_read_tokens": 0, "cache_creation_tokens": 0, "total_tokens": usage["total_tokens"], "calls": 1}
        with usage_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    except OSError:
        pass


def stream_chat(messages: list[dict[str, str]], session_id: str | None = None, model: str | None = None, system_prompt: str | None = None) -> Iterator[ChatEvent]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    timeout = float(getattr(config, "CHAT_CLI_TIMEOUT", 300))
    try:
        proc_id = procs.registry.spawn(_build_cmd(messages, system_prompt=system_prompt), cwd=getattr(config, "ROOT", None), env=env, timeout=timeout, provider=PROVIDER_ID, stdin=subprocess.DEVNULL)
    except procs.BusyError as exc:
        yield {"type": "error", "message": str(exc), "code": 429}
        return

    process = procs.registry.get(proc_id)
    if process is None or process.stdout is None:
        procs.registry.unregister(proc_id)
        yield {"type": "error", "message": "gemini process failed to start", "code": None}
        return

    timed_out = False
    stdout_lines: list[str] = []
    stderr = ""
    returncode: int | None = None
    try:
        for raw_line in process.stdout:
            text = raw_line.strip()
            if text:
                stdout_lines.append(text)
                yield {"type": "delta", "text": text}
    finally:
        timed_out = procs.registry.is_timed_out(proc_id)
        returncode = process.returncode
        if process.stderr is not None:
            stderr = process.stderr.read().strip()
        procs.registry.unregister(proc_id)
    if timed_out:
        yield {"type": "error", "message": f"gemini timed out after {int(timeout)}s", "code": None}
        return
    if returncode not in (None, 0):
        yield {"type": "error", "message": stderr or f"gemini exited with code {returncode}", "code": None}
        return
    if stderr and not stdout_lines:
        yield {"type": "error", "message": stderr, "code": None}
        return

    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    _append_usage_event(usage)
    yield {"type": "done", "usage": usage, "session_id": None}
