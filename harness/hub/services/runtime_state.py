from __future__ import annotations

import json
import re
import hashlib
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import config
from services import runtime_reducers


ID_PATTERNS = {
    "thread": re.compile(r"^thread-[0-9a-z-]+$"),
    "run": re.compile(r"^run-[0-9a-z-]+$"),
    "checkpoint": re.compile(r"^checkpoint-[0-9a-z-]+$"),
    "interrupt": re.compile(r"^interrupt-[0-9a-z-]+$"),
}


class StaleRunVersionError(ValueError):
    pass


class IdempotencyConflictError(ValueError):
    pass


class RuntimeJournalCorruptionError(ValueError):
    pass


_RUN_LOCKS: dict[str, threading.RLock] = {}
_RUN_LOCKS_GUARD = threading.Lock()


def _run_lock(run_id: str) -> threading.RLock:
    with _RUN_LOCKS_GUARD:
        return _RUN_LOCKS.setdefault(run_id, threading.RLock())


def _canonical_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_id(kind: str) -> str:
    if kind not in ID_PATTERNS:
        raise ValueError(f"Unknown runtime id kind: {kind}")
    return f"{kind}-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid.uuid4().hex[:8]}"


def validate_id(kind: str, value: str) -> str:
    pattern = ID_PATTERNS.get(kind)
    if pattern is None or not pattern.fullmatch(value or ""):
        label = kind.capitalize()
        raise FileNotFoundError(f"{label} not found: {value}")
    return value


def _resolve_under(base: Path, p: str | Path = ".") -> Path:
    base_path = Path(base).resolve()
    candidate = Path(p)
    if not candidate.is_absolute():
        candidate = base_path / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(base_path)
    except ValueError as exc:
        raise PermissionError(f"Path is outside runtime root: {resolved}") from exc
    return resolved


def runtime_dir() -> Path:
    return Path(config.RUNTIME_DIR)


def threads_dir() -> Path:
    return Path(config.RUNTIME_THREADS_DIR)


def runs_dir() -> Path:
    return Path(config.RUNTIME_RUNS_DIR)


def store_dir() -> Path:
    return Path(config.RUNTIME_STORE_DIR)


def ensure_runtime_dirs() -> None:
    threads_dir().mkdir(parents=True, exist_ok=True)
    runs_dir().mkdir(parents=True, exist_ok=True)
    store_dir().mkdir(parents=True, exist_ok=True)


def thread_dir(thread_id: str, must_exist: bool = True) -> Path:
    validate_id("thread", thread_id)
    path = _resolve_under(threads_dir(), thread_id)
    if must_exist and not (path / "state.json").is_file():
        raise FileNotFoundError(f"Thread not found: {thread_id}")
    return path


def run_dir(run_id: str, must_exist: bool = True) -> Path:
    validate_id("run", run_id)
    path = _resolve_under(runs_dir(), run_id)
    if must_exist and not (path / "run.json").is_file():
        raise FileNotFoundError(f"Run not found: {run_id}")
    return path


def run_state_path(run_id: str) -> Path:
    return run_dir(run_id) / "run.json"


def run_journal_path(run_id: str) -> Path:
    return run_dir(run_id) / "transactions.jsonl"


def thread_state_path(thread_id: str) -> Path:
    return thread_dir(thread_id) / "state.json"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _append_journal(run_id: str, record: dict[str, Any]) -> dict[str, Any]:
    stored = dict(record)
    stored["checksum"] = _canonical_hash(stored)
    with run_journal_path(run_id).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(stored, ensure_ascii=False, sort_keys=True) + "\n")
    return stored


def _quarantine_journal_tail(run_id: str, tail: bytes) -> Path:
    quarantine = run_dir(run_id) / "quarantine"
    quarantine.mkdir(parents=True, exist_ok=True)
    path = quarantine / f"transactions.tail-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid.uuid4().hex[:8]}.jsonl"
    path.write_bytes(tail)
    return path


def _read_journal(run_id: str, repair_tail: bool = True) -> list[dict[str, Any]]:
    path = run_journal_path(run_id)
    if not path.is_file():
        return []
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    records: list[dict[str, Any]] = []
    offset = 0
    previous_hash = ""
    for line in lines:
        line_end = offset + len(line)
        try:
            item = json.loads(line.decode("utf-8"))
            if not isinstance(item, dict):
                raise ValueError("journal record is not an object")
            checksum = item.pop("checksum", None)
            if not isinstance(checksum, str) or checksum != _canonical_hash(item):
                raise ValueError("journal checksum mismatch")
            if str(item.get("prior_transaction_hash") or "") != previous_hash:
                raise ValueError("journal chain mismatch")
            item["checksum"] = checksum
            records.append(item)
            previous_hash = checksum
            offset = line_end
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            tail = raw[offset:]
            if not repair_tail:
                raise RuntimeJournalCorruptionError(f"Corrupt transaction journal for {run_id}")
            _quarantine_journal_tail(run_id, tail)
            path.write_bytes(raw[:offset])
            break
    return records


def _regenerate_derived_events(run_id: str, records: list[dict[str, Any]]) -> None:
    """Restore missing transaction timeline entries; no provider or executor is invoked."""
    path = runtime_path("run", run_id, "events.jsonl")
    existing: list[dict[str, Any]] = []
    valid: list[bytes] = []
    if path.is_file():
        raw = path.read_bytes()
        offset = 0
        for line in raw.splitlines(keepends=True):
            try:
                item = json.loads(line.decode("utf-8"))
                if not isinstance(item, dict):
                    raise ValueError("event is not an object")
                existing.append(item)
                valid.append(line)
                offset += len(line)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                _quarantine_journal_tail(run_id, raw[offset:])
                path.write_bytes(b"".join(valid))
                break
    known = {str(item.get("event_id") or "") for item in existing}
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            if record.get("phase") != "committed":
                continue
            event_id = f"event-{record['transaction_id']}"
            if event_id in known:
                continue
            event = {
                "event_id": event_id,
                "type": "run.command_committed",
                "run_id": run_id,
                "sequence": record["target_state_version"],
                "ts": record["occurred_at"],
                "causation_id": record["command_id"],
                "command_type": record["command_type"],
            }
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def recover_run(run_id: str) -> dict[str, Any]:
    """Repairs a corrupt transaction-journal tail; it never replays external work."""
    run_id = validate_id("run", run_id)
    with _run_lock(run_id):
        state = runtime_reducers.normalize_state(_read_json(run_state_path(run_id)))
        if "state_version" not in state:
            state["runtime_compatibility"] = "legacy_unjournaled"
            return state
        _regenerate_derived_events(run_id, _read_journal(run_id, repair_tail=True))
        return state


def create_thread(metadata: dict[str, Any] | None = None, thread_id: str | None = None) -> dict[str, Any]:
    ensure_runtime_dirs()
    value = thread_id or new_id("thread")
    validate_id("thread", value)
    path = thread_dir(value, must_exist=False)
    if (path / "state.json").exists():
        raise FileExistsError(f"Thread already exists: {value}")
    ts = now_iso()
    state = {
        "thread_id": value,
        "created_at": ts,
        "updated_at": ts,
        "latest_run_id": None,
        "runs": [],
        "metadata": dict(metadata or {}),
    }
    _write_json(path / "state.json", state)
    (path / "checkpoints").mkdir(parents=True, exist_ok=True)
    (path / "uploads").mkdir(parents=True, exist_ok=True)
    (path / "workspace").mkdir(parents=True, exist_ok=True)
    (path / "outputs").mkdir(parents=True, exist_ok=True)
    return state


def read_thread(thread_id: str) -> dict[str, Any]:
    return _read_json(thread_state_path(thread_id))


def list_threads() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not threads_dir().exists():
        return items
    for path in threads_dir().glob("thread-*/state.json"):
        try:
            item = _read_json(_resolve_under(threads_dir(), path))
            if ID_PATTERNS["thread"].fullmatch(str(item.get("thread_id") or "")):
                items.append(item)
        except (OSError, ValueError, PermissionError, json.JSONDecodeError):
            continue
    items.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    return items


def _write_thread_state(state: dict[str, Any]) -> None:
    thread_id = str(state.get("thread_id") or "")
    validate_id("thread", thread_id)
    state["updated_at"] = now_iso()
    _write_json(thread_dir(thread_id, must_exist=False) / "state.json", state)


def _ensure_thread(thread_id: str | None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if thread_id:
        return read_thread(thread_id)
    return create_thread(metadata=metadata)


def create_run(
    *,
    thread_id: str | None = None,
    run_id: str | None = None,
    agent_id: str = "lead",
    messages: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_runtime_dirs()
    thread = _ensure_thread(thread_id, metadata={"created_by": "runtime"})
    actual_thread_id = str(thread["thread_id"])
    actual_run_id = run_id or new_id("run")
    validate_id("run", actual_run_id)
    path = run_dir(actual_run_id, must_exist=False)
    if (path / "run.json").exists():
        raise FileExistsError(f"Run already exists: {actual_run_id}")

    ts = now_iso()
    state = runtime_reducers.default_state(actual_run_id, actual_thread_id, "queued")
    state["messages"] = list(messages or [])
    state["metadata"] = {
        **dict(metadata or {}),
        "agent_id": agent_id,
        "created_at": ts,
        "updated_at": ts,
    }
    state["state_version"] = 0
    path.mkdir(parents=True, exist_ok=False)
    (path / "artifacts").mkdir(parents=True, exist_ok=True)
    _write_json(path / "run.json", state)

    runs = list(thread.get("runs") or [])
    if actual_run_id not in runs:
        runs.append(actual_run_id)
    thread["runs"] = runs
    thread["latest_run_id"] = actual_run_id
    _write_thread_state(thread)
    return state


def read_run(run_id: str) -> dict[str, Any]:
    return recover_run(run_id)


def write_run_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized = runtime_reducers.normalize_state(state)
    run_id = validate_id("run", str(normalized.get("run_id") or ""))
    thread_id = validate_id("thread", str(normalized.get("thread_id") or ""))
    metadata = dict(normalized.get("metadata") or {})
    metadata["updated_at"] = now_iso()
    normalized["metadata"] = metadata
    _write_json(run_dir(run_id, must_exist=False) / "run.json", normalized)

    try:
        thread = read_thread(thread_id)
    except FileNotFoundError:
        thread = create_thread(thread_id=thread_id, metadata={"created_by": "runtime"})
    thread["latest_run_id"] = run_id
    runs = list(thread.get("runs") or [])
    if run_id not in runs:
        runs.append(run_id)
    thread["runs"] = runs
    _write_thread_state(thread)
    return normalized


def update_run_state(
    run_id: str,
    update: dict[str, Any],
    *,
    expected_version: int | None = None,
    command_id: str | None = None,
    idempotency_key: str | None = None,
    command_type: str = "run.update",
) -> dict[str, Any]:
    """Atomically apply one local state command; legacy runs remain read-only compatible."""
    run_id = validate_id("run", run_id)
    request = {"type": command_type, "update": update, "expected_version": expected_version}
    request_hash = _canonical_hash(request)
    command_id = command_id or f"cmd-{uuid.uuid4().hex}"
    key = idempotency_key or command_id
    with _run_lock(run_id):
        state = runtime_reducers.normalize_state(_read_json(run_state_path(run_id)))
        if "state_version" not in state:
            if expected_version is not None or idempotency_key is not None:
                raise RuntimeJournalCorruptionError(f"Run {run_id} is legacy and has no command journal")
            merged = runtime_reducers.merge_state(state, update)
            return write_run_state(merged)
        version = state["state_version"]
        if not isinstance(version, int):
            raise RuntimeJournalCorruptionError(f"Run {run_id} has invalid state version")
        journal = _read_journal(run_id, repair_tail=True)
        committed = [item for item in journal if item.get("phase") == "committed"]
        for item in committed:
            if item.get("command_type") == command_type and item.get("idempotency_key") == key:
                if item.get("request_hash") != request_hash:
                    raise IdempotencyConflictError(f"Idempotency key conflicts for {run_id}")
                return runtime_reducers.normalize_state(_read_json(run_state_path(run_id)))
        if expected_version is not None and expected_version != version:
            raise StaleRunVersionError(f"Expected version {expected_version}, current version {version}")
        prior_hash = str(journal[-1].get("checksum") if journal else "")
        transaction_id = f"tx-{uuid.uuid4().hex}"
        base = {
            "schema_version": 1,
            "transaction_id": transaction_id,
            "command_id": command_id,
            "command_type": command_type,
            "idempotency_key": key,
            "request_hash": request_hash,
            "prior_state_version": version,
            "target_state_version": version + 1,
            "prior_transaction_hash": prior_hash,
            "occurred_at": now_iso(),
        }
        prepared = _append_journal(run_id, {**base, "phase": "prepared"})
        merged = runtime_reducers.merge_state(state, update)
        merged["state_version"] = version + 1
        persisted = write_run_state(merged)
        _append_journal(
            run_id,
            {
                **base,
                "phase": "committed",
                "prior_transaction_hash": prepared["checksum"],
                "projection_hash": _canonical_hash(persisted),
                "response_hash": _canonical_hash({"state_version": persisted["state_version"]}),
            },
        )
        _regenerate_derived_events(run_id, _read_journal(run_id, repair_tail=False))
        return persisted


def set_run_status(run_id: str, status: str, error: str | None = None) -> dict[str, Any]:
    update: dict[str, Any] = {"status": status}
    if error:
        update["metadata"] = {"error": error}
    return update_run_state(run_id, update)


def list_runs() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not runs_dir().exists():
        return items
    for path in runs_dir().glob("run-*/run.json"):
        try:
            item = runtime_reducers.normalize_state(_read_json(_resolve_under(runs_dir(), path)))
            if ID_PATTERNS["run"].fullmatch(str(item.get("run_id") or "")):
                items.append(item)
        except (OSError, ValueError, PermissionError, json.JSONDecodeError):
            continue
    items.sort(
        key=lambda item: str((item.get("metadata") or {}).get("updated_at") or (item.get("metadata") or {}).get("created_at") or ""),
        reverse=True,
    )
    return items


def runtime_path(kind: str, owner_id: str, *parts: str) -> Path:
    if kind == "run":
        base = run_dir(owner_id)
    elif kind == "thread":
        base = thread_dir(owner_id)
    elif kind == "store":
        base = store_dir()
        base.mkdir(parents=True, exist_ok=True)
    else:
        raise ValueError(f"Unknown runtime path kind: {kind}")
    return _resolve_under(base, Path(*parts) if parts else ".")
