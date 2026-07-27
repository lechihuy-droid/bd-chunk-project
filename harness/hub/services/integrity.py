from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any

import config


def _suite_files() -> list[Path]:
    if not config.SUITES_DIR.exists():
        return []
    return sorted(path for path in config.SUITES_DIR.rglob("*.json") if path.is_file())


def _suite_rel(path: Path) -> str:
    return path.resolve().relative_to(config.SUITES_DIR.resolve()).as_posix()


def _key() -> bytes:
    env_value = os.environ.get("HUB_HMAC_KEY")
    if env_value:
        return env_value.encode("utf-8")
    try:
        value = config.HMAC_KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        value = ""
    if not value:
        value = secrets.token_hex(32)
        config.HMAC_KEY_FILE.write_text(value, encoding="utf-8")
    return value.encode("utf-8")


def _digest(path: Path) -> str:
    return hmac.new(_key(), path.read_bytes(), hashlib.sha256).hexdigest()


def sign_text(value: str) -> str:
    return hmac.new(_key(), str(value).encode("utf-8"), hashlib.sha256).hexdigest()


def verify_text(value: str, signature: str | None) -> bool:
    if not isinstance(signature, str) or not signature:
        return False
    return hmac.compare_digest(signature, sign_text(value))


def _load_sigs() -> dict[str, str]:
    try:
        data = json.loads(config.INTEGRITY_SIGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    suites = data.get("suites", data)
    if not isinstance(suites, dict):
        return {}
    return {str(key): str(value) for key, value in suites.items()}


def _save_sigs(sigs: dict[str, str]) -> None:
    config.INTEGRITY_SIGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.INTEGRITY_SIGS_FILE.write_text(
        json.dumps({"suites": dict(sorted(sigs.items()))}, indent=2),
        encoding="utf-8",
    )


def resign_suites() -> list[dict[str, Any]]:
    sigs = {_suite_rel(path): _digest(path) for path in _suite_files()}
    _save_sigs(sigs)
    return [{"suite": suite, "ok": True, "expected": sig, "actual": sig} for suite, sig in sorted(sigs.items())]


def verify_suites() -> list[dict[str, Any]]:
    sigs = _load_sigs()
    results: list[dict[str, Any]] = []
    changed = False
    seen: set[str] = set()

    for path in _suite_files():
        rel = _suite_rel(path)
        actual = _digest(path)
        expected = sigs.get(rel)
        if expected is None:
            expected = actual
            sigs[rel] = actual
            changed = True
        seen.add(rel)
        results.append(
            {
                "suite": rel,
                "ok": hmac.compare_digest(expected, actual),
                "expected": expected,
                "actual": actual,
            }
        )

    for rel, expected in sorted(sigs.items()):
        if rel not in seen:
            results.append({"suite": rel, "ok": False, "expected": expected, "actual": None})

    if changed:
        _save_sigs(sigs)
    return sorted(results, key=lambda item: str(item.get("suite") or ""))
