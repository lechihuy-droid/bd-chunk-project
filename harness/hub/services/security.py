from __future__ import annotations

import os
import re
from typing import Any


_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password|authorization)\s*[:=]\s*(?:bearer\s+)?['\"]?[^\s,'\"]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
)
_SAFE_ENV = frozenset({"APPDATA", "COMSPEC", "LOCALAPPDATA", "PATH", "PATHEXT", "PYTHONIOENCODING", "SYSTEMROOT", "TEMP", "TMP", "USERPROFILE"})


def redact_text(value: Any) -> str:
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {str(key): redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value


def subprocess_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key.upper() in _SAFE_ENV}
    env["PYTHONIOENCODING"] = "utf-8"
    for key, value in (extra or {}).items():
        if key.upper() in _SAFE_ENV:
            env[key] = value
    return env
