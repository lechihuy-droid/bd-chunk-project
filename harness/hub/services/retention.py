from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import config
from services import audit


_FILE = "retention.json"


def _path() -> Path:
    return config.RUNTIME_STORE_DIR / _FILE


def settings() -> dict[str, int]:
    try:
        value = json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        value = {}
    days = value.get("days") if isinstance(value, dict) else None
    return {"days": days if isinstance(days, int) and config.RETENTION_DAYS_MIN <= days <= config.RETENTION_DAYS_MAX else config.RETENTION_DAYS_DEFAULT}


def update(days: int) -> dict[str, int]:
    if not isinstance(days, int) or isinstance(days, bool) or not config.RETENTION_DAYS_MIN <= days <= config.RETENTION_DAYS_MAX:
        raise ValueError(f"Retention days must be {config.RETENTION_DAYS_MIN}-{config.RETENTION_DAYS_MAX}")
    path = _path(); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"days": days}) + "\n", encoding="utf-8")
    audit.append("retention.settings_changed", context={"days": days})
    return {"days": days}


def _active(run_dir: Path) -> bool:
    try:
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(state, dict) and str(state.get("status") or "") in {"running", "active"}


def _old(path: Path, cutoff: datetime) -> bool:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, UTC) < cutoff
    except OSError:
        return False


def sweep(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=settings()["days"])
    removed: list[str] = []
    for run_dir in config.RUNTIME_RUNS_DIR.iterdir() if config.RUNTIME_RUNS_DIR.is_dir() else ():
        if not run_dir.is_dir() or _active(run_dir):
            continue
        event_log = run_dir / "events.jsonl"
        if event_log.is_file() and _old(event_log, cutoff):
            event_log.unlink(); removed.append(str(event_log))
    for log in config.JOBS_DIR.glob("*/stdout.log") if config.JOBS_DIR.is_dir() else ():
        try:
            job = json.loads((log.parent / "job.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            job = {}
        if str(job.get("status") or "") not in {"running", "active"} and _old(log, cutoff):
            log.unlink(); removed.append(str(log))
    caches = (config.CHAT_USAGE_FILE, config.HUB_DIR / ".cache" / "usage_files.json", config.HUB_DIR / ".cache" / "behavior_files.json")
    for cache in caches:
        if cache.is_file() and _old(cache, cutoff):
            cache.unlink(); removed.append(str(cache))
    result = {"days": settings()["days"], "removed": removed, "removed_count": len(removed)}
    audit.append("retention.swept", context={"days": result["days"], "removed_count": result["removed_count"], "removed": removed})
    return result
