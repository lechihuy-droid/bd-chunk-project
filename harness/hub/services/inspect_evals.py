from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any

import config
from parsers.common import file_ts, normalize_ts


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _paths() -> list[Path]:
    root = config.USAGE_SOURCES.get("inspect")
    if not isinstance(root, Path) or not root.exists():
        return []
    return sorted(root.glob("*.eval"), key=lambda path: path.stat().st_mtime, reverse=True)


def _plain(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        try:
            return _plain(dump())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return {
            key: _plain(item)
            for key, item in vars(value).items()
            if not key.startswith("_") and isinstance(key, str)
        }
    return str(value)


def _read_eval(path: Path) -> dict[str, Any]:
    from inspect_ai.log import read_eval_log

    log = read_eval_log(str(path))
    stats = _get(log, "stats")
    eval_info = _get(log, "eval")
    task = _get(eval_info, "task") or _get(eval_info, "task_id") or _get(eval_info, "name")
    ts = _get(eval_info, "created") or _get(eval_info, "started_at") or _get(stats, "started_at")
    model_usage = _get(stats, "model_usage")
    return {
        "name": path.name,
        "task": task,
        "model_usage": _plain(model_usage),
        "ts": normalize_ts(ts, path),
    }


def list_logs() -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for path in _paths():
        try:
            logs.append(_read_eval(path))
        except Exception as exc:
            warnings.warn(f"Skipping unreadable Inspect eval {path}: {exc}", RuntimeWarning, stacklevel=2)
            continue
    return logs


def _latest_eval() -> Path:
    paths = _paths()
    if not paths:
        root = config.USAGE_SOURCES.get("inspect")
        raise FileNotFoundError(f"No Inspect .eval logs found in {root}")
    return paths[0]


def _mep_json_path(eval_path: Path) -> Path:
    return config.INSPECT_MEP_DIR / eval_path.stem / "mep.json"


def _python_exe() -> str:
    bundled = config.ROOT / ".ih" / "Scripts" / "python.exe"
    if bundled.exists():
        return str(bundled)
    return sys.executable


def _export_mep(eval_path: Path, mep_path: Path) -> None:
    completed = subprocess.run(
        [
            _python_exe(),
            str(config.INSPECT_EXPORT_MEP),
            "--log",
            str(eval_path),
            "--out-dir",
            str(config.INSPECT_MEP_DIR),
        ],
        cwd=config.ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        timeout=120,
    )
    if mep_path.is_file():
        return
    message = completed.stderr.strip() or completed.stdout.strip() or f"export_mep exited {completed.returncode}"
    raise RuntimeError(message)


def latest_mep() -> dict[str, Any]:
    eval_path = _latest_eval()
    mep_path = _mep_json_path(eval_path)
    if not mep_path.is_file() or mep_path.stat().st_mtime < eval_path.stat().st_mtime:
        _export_mep(eval_path, mep_path)
    try:
        data = json.loads(mep_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read MEP packet {mep_path}: {exc}") from exc
    if isinstance(data, dict):
        data.setdefault("source_log", str(eval_path))
        data.setdefault("generated_at", file_ts(mep_path))
        return data
    raise RuntimeError(f"MEP packet must be a JSON object: {mep_path}")
