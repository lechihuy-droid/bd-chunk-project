from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import threading
import time
from pathlib import Path
from typing import Any

import config
from services import replay


try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency not installed
    yaml = None  # type: ignore


SKILL_PROMPT_MAX_CHARS = 12000
_SKILL_TOOL_NAME = "Skill"
_TELEMETRY_WINDOW_DAYS = 30
_TELEMETRY_CACHE_TTL_SECONDS = 30.0
_BOM = "\ufeff"
_FRONTMATTER_RE = re.compile(rf"^{_BOM}?---\s*\n(.*?\n)---\s*\n?", re.DOTALL)

_DEFAULT_SKILL_SOURCES: dict[str, Path] = {
    "hub_builtin": config.HUB_DIR / "skills",
    "claude_user": Path.home() / ".claude" / "skills",
    "claude_project": config.ROOT / ".claude" / "skills",
    "codex_user": Path.home() / ".codex" / "skills",
}

_INDEX_CACHE: dict[str, Any] = {"fingerprint": None, "entries": [], "sources": None}
_SKILL_NAMES_CACHE: dict[str, Any] = {"fingerprint": None, "names": set()}
_LOCK = threading.RLock()
_TELEMETRY_LOCK = threading.RLock()
_TELEMETRY_CACHE: dict[str, Any] = {"expires": 0.0, "fingerprint": None, "events": []}
_SAFE_SKILL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _sources() -> dict[str, Path]:
    sources = getattr(config, "SKILL_SOURCES", None)
    if isinstance(sources, dict) and sources:
        return {str(key): Path(value) for key, value in sources.items()}
    return dict(_DEFAULT_SKILL_SOURCES)


def _deploy_log_path() -> Path:
    path = getattr(config, "SKILL_DEPLOY_LOG", None)
    if isinstance(path, Path):
        return path
    return config.HUB_DIR / ".cache" / "skill_deploy_log.jsonl"


def _clear_cache() -> None:
    _INDEX_CACHE.update({"fingerprint": None, "entries": [], "sources": None})
    _SKILL_NAMES_CACHE.update({"fingerprint": None, "names": set()})


def create_skill(payload: dict[str, Any]) -> dict[str, Any]:
    name, source, content = payload.get("name"), payload.get("source"), payload.get("content")
    if not isinstance(name, str) or not _SAFE_SKILL_NAME.fullmatch(name): raise ValueError("Invalid skill name")
    if not isinstance(source, str) or source not in _sources(): raise ValueError("Unknown skill source")
    if not isinstance(content, str) or not content.strip(): raise ValueError("content is required")
    root = _sources()[source]; path = root / name
    if path.exists(): raise ValueError("Skill already exists")
    path.mkdir(parents=True); (path / "SKILL.md").write_text(content, encoding="utf-8"); _clear_cache()
    return get_skill(f"{source}/{name}")


def update_skill(skill_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    entry = next((row for row in _scan_all_sources() if row["id"] == skill_id), None)
    if entry is None: raise FileNotFoundError(f"Skill not found: {skill_id}")
    content = payload.get("content")
    if not isinstance(content, str) or not content.strip(): raise ValueError("content is required")
    _skill_md_path(Path(entry["path"])).write_text(content, encoding="utf-8"); _clear_cache()
    return get_skill(skill_id)


def delete_skill(skill_id: str) -> None:
    entry = next((row for row in _scan_all_sources() if row["id"] == skill_id), None)
    if entry is None: raise FileNotFoundError(f"Skill not found: {skill_id}")
    path = Path(entry["path"])
    if path.is_dir(): shutil.rmtree(path)
    else: path.unlink()
    _clear_cache()


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------


def _iter_skill_dirs(root: Path) -> list[tuple[str, Path]]:
    """Return (dirname, skill_path) pairs directly under one source root.

    A skill is either a subdir containing SKILL.md, or a standalone .md file
    (the codex-style single-file skill).
    """
    if not root.exists():
        return []
    items: list[tuple[str, Path]] = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return []
    for entry in entries:
        try:
            if entry.is_dir():
                if (entry / "SKILL.md").is_file():
                    items.append((entry.name, entry))
            elif entry.is_file() and entry.suffix.lower() == ".md":
                items.append((entry.stem, entry))
        except OSError:
            continue
    return items


def _skill_md_path(path: Path) -> Path:
    return path / "SKILL.md" if path.is_dir() else path


def _skill_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return [path]
    try:
        return sorted((p for p in path.rglob("*") if p.is_file()), key=lambda p: p.relative_to(path).as_posix())
    except OSError:
        return []


def _content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in _skill_files(path):
        rel = file_path.relative_to(path).as_posix() if path.is_dir() else file_path.name
        digest.update(rel.encode("utf-8"))
        try:
            digest.update(file_path.read_bytes())
        except OSError:
            continue
    return f"sha256:{digest.hexdigest()}"


def _dir_mtime_ns(path: Path) -> int:
    """Return direct mtime; recursive walks are too costly on hot paths."""
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a SKILL.md document into its frontmatter mapping and its body.

    Returns ({}, text) when the document has no parsable frontmatter block.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    return _parse_block(match.group(1)), text[match.end():]


def _parse_frontmatter(text: str) -> dict[str, str]:
    return split_frontmatter(text)[0]


def _parse_block(block: str) -> dict[str, str]:
    if yaml is not None:
        try:
            data = yaml.safe_load(block)
        except Exception:
            data = None
        if isinstance(data, dict):
            return {str(key): str(value) for key, value in data.items() if value is not None}
    result: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def _read_frontmatter(path: Path) -> dict[str, str]:
    try:
        text = _skill_md_path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    return _parse_frontmatter(text)


def _scan_source(source: str, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dirname, path in _iter_skill_dirs(root):
        meta = _read_frontmatter(path)
        name = meta.get("name") or dirname
        rows.append(
            {
                "id": f"{source}/{dirname}",
                "name": name,
                "description": meta.get("description", ""),
                "source": source,
                "path": str(path),
                "content_hash": _content_hash(path),
            }
        )
    return rows


def _source_roots() -> tuple[tuple[str, str, int], ...]:
    return tuple(sorted((source, str(root), _dir_mtime_ns(root)) for source, root in _sources().items()))


def _snapshot_sources() -> tuple[tuple[str, str, int, tuple[tuple[str, str, int], ...]], ...]:
    """Record source entries after a root change without recursing into skills."""
    rows: list[tuple[str, str, int, tuple[tuple[str, str, int], ...]]] = []
    for source, root in _sources().items():
        skills = tuple(
            (dirname, str(path), _dir_mtime_ns(_skill_md_path(path)))
            for dirname, path in _iter_skill_dirs(root)
        )
        rows.append((source, str(root), _dir_mtime_ns(root), skills))
    return tuple(sorted(rows))


def _fingerprint_sources() -> tuple[tuple[str, str, int, tuple[tuple[str, str, int], ...]], ...]:
    """Detect additions/deletions by source mtime and edits by SKILL.md mtime.

    Warm calls only stat source roots and known SKILL.md files.  This keeps
    runtime deploys visible on the next call without a recursive tree walk.
    """
    roots = _source_roots()
    cached = _INDEX_CACHE.get("sources")
    if not isinstance(cached, tuple) or tuple((source, path, mtime) for source, path, mtime, _ in cached) != roots:
        return _snapshot_sources()
    return tuple(
        (source, root, root_mtime, tuple(
            (dirname, path, _dir_mtime_ns(_skill_md_path(Path(path))))
            for dirname, path, _ in skills
        ))
        for source, root, root_mtime, skills in cached
    )


def _scan_all_sources() -> list[dict[str, Any]]:
    with _LOCK:
        fingerprint = _fingerprint_sources()
        if _INDEX_CACHE["fingerprint"] == fingerprint:
            return list(_INDEX_CACHE["entries"])

        entries: list[dict[str, Any]] = []
        for source, root in _sources().items():
            entries.extend(_scan_source(source, root))

        _INDEX_CACHE.update({"fingerprint": fingerprint, "entries": entries, "sources": fingerprint})
        return list(entries)


def list_skill_names() -> set[str]:
    """Return discovered skill names without collecting session-log telemetry."""
    with _LOCK:
        fingerprint = _fingerprint_sources()
        if _SKILL_NAMES_CACHE["fingerprint"] == fingerprint:
            return set(_SKILL_NAMES_CACHE["names"])

        names: set[str] = set()
        for source, root in _sources().items():
            for dirname, path in _iter_skill_dirs(root):
                names.add(_read_frontmatter(path).get("name") or dirname)

        _SKILL_NAMES_CACHE.update({"fingerprint": fingerprint, "names": names})
        return set(names)


# --------------------------------------------------------------------------
# Telemetry (best-effort, reuses the Claude session-log parser primitives
# already used by services/behavior.py — never modifies that module)
# --------------------------------------------------------------------------


def _parse_ts(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed


def _skill_invocation_matches(invoked: str, name: str) -> bool:
    return invoked == name or invoked.endswith(f":{name}")


def _collect_skill_tool_events() -> list[dict[str, Any]]:
    """Single best-effort pass over Claude session logs for Skill-tool calls."""
    root = config.USAGE_SOURCES.get("claude")
    if not isinstance(root, Path) or not root.exists():
        return []

    events: list[dict[str, Any]] = []
    try:
        paths = list(root.glob("*/*.jsonl"))
    except OSError:
        return []

    for path in paths:
        try:
            for obj in replay._iter_jsonl(path):
                if obj.get("type") != "assistant":
                    continue
                message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
                for block in replay._blocks(message.get("content")):
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    if block.get("name") != _SKILL_TOOL_NAME:
                        continue
                    input_data = block.get("input")
                    invoked = input_data.get("skill") if isinstance(input_data, dict) else None
                    if isinstance(invoked, str) and invoked:
                        events.append(
                            {"skill": invoked, "ts": replay.normalize_ts(obj.get("timestamp"), path)}
                        )
        except OSError:
            continue
    return events


def _telemetry_fingerprint() -> tuple[tuple[str, int, int], ...]:
    root = config.USAGE_SOURCES.get("claude")
    if not isinstance(root, Path) or not root.exists():
        return ()
    try:
        paths = root.glob("*/*.jsonl")
        return tuple(sorted((str(path), _dir_mtime_ns(path), path.stat().st_size) for path in paths))
    except OSError:
        return ()


def _safe_collect_skill_tool_events() -> list[dict[str, Any]]:
    try:
        with _TELEMETRY_LOCK:
            now = time.monotonic()
            if _TELEMETRY_CACHE["expires"] > now:
                return list(_TELEMETRY_CACHE["events"])
            fingerprint = _telemetry_fingerprint()
            if _TELEMETRY_CACHE["fingerprint"] == fingerprint:
                _TELEMETRY_CACHE["expires"] = now + _TELEMETRY_CACHE_TTL_SECONDS
                return list(_TELEMETRY_CACHE["events"])
            events = _collect_skill_tool_events()
            _TELEMETRY_CACHE.update({
                "expires": now + _TELEMETRY_CACHE_TTL_SECONDS,
                "fingerprint": fingerprint,
                "events": events,
            })
            return list(events)
    except Exception:
        return []


def _telemetry(name: str, tool_events: list[dict[str, Any]]) -> tuple[str | None, int | None]:
    matches = [event for event in tool_events if _skill_invocation_matches(event["skill"], name)]
    if not matches:
        return None, None
    timestamps = sorted(event["ts"] for event in matches)
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=_TELEMETRY_WINDOW_DAYS)
    use_count_30d = sum(1 for ts in timestamps if (_parse_ts(ts) or cutoff) >= cutoff)
    return timestamps[-1], use_count_30d


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def list_skills() -> list[dict[str, Any]]:
    raw_entries = _scan_all_sources()

    by_name: dict[str, set[str]] = {}
    for entry in raw_entries:
        by_name.setdefault(entry["name"], set()).add(entry["source"])

    tool_events = _safe_collect_skill_tool_events()

    results: list[dict[str, Any]] = []
    for entry in raw_entries:
        last_used, use_count_30d = _telemetry(entry["name"], tool_events)
        results.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "description": entry["description"],
                "source": entry["source"],
                "path": entry["path"],
                "content_hash": entry["content_hash"],
                "coverage": sorted(by_name[entry["name"]]),
                "last_used": last_used,
                "use_count_30d": use_count_30d,
            }
        )

    results.sort(key=lambda item: (str(item["name"]), str(item["source"])))
    return results


def get_skill(skill_id: str) -> dict[str, Any]:
    entry = next((row for row in _scan_all_sources() if row["id"] == skill_id), None)
    if entry is None:
        raise FileNotFoundError(f"Skill not found: {skill_id}")

    path = Path(entry["path"])
    try:
        content = _skill_md_path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        content = ""

    files = sorted(
        file_path.relative_to(path).as_posix() if path.is_dir() else file_path.name
        for file_path in _skill_files(path)
    )

    return {
        "id": entry["id"],
        "name": entry["name"],
        "description": entry["description"],
        "source": entry["source"],
        "path": entry["path"],
        "content_hash": entry["content_hash"],
        "content": content,
        "files": files,
    }


def read_skill_content(skill_name: str) -> str:
    """Read SKILL.md for a validated skill name without accepting a raw path."""
    for source, root in _sources().items():
        for dirname, path in _iter_skill_dirs(root):
            name = _read_frontmatter(path).get("name") or dirname
            if name != skill_name:
                continue
            try:
                return _skill_md_path(path).read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                raise FileNotFoundError(f"Skill not readable: {skill_name}") from exc
    raise FileNotFoundError(f"Skill not found: {skill_name}")


def pin_skill_prompt_contents(skill_names: list[str]) -> list[dict[str, str]]:
    """Resolve skills once, retaining their identity and exact prompt text for a run."""
    pins: list[dict[str, str]] = []
    for name in skill_names:
        entry = next((row for row in _scan_all_sources() if row["name"] == name), None)
        if entry is None:
            raise FileNotFoundError(f"Skill not found: {name}")
        try:
            content = _skill_md_path(Path(entry["path"])).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise FileNotFoundError(f"Skill not readable: {name}") from exc
        pins.append({"source": str(entry["source"]), "name": name, "content_hash": str(entry["content_hash"]), "content": content})
    return pins


def load_pinned_skill_prompt_contents(skill_pins: list[dict[str, Any]]) -> tuple[list[str], bool]:
    """Validate pinned identity against the live resolver, then return pinned text.

    A changed hash or a higher-priority same-name source is an execution error:
    using either live variant would make a run unreproducible.
    """
    entries = _scan_all_sources()
    contents: list[str] = []
    used = 0
    truncated = False
    for pin in skill_pins:
        name = str(pin.get("name") or "")
        resolved = next((row for row in entries if row["name"] == name), None)
        if resolved is None:
            raise ValueError(f"Pinned skill missing: {name}")
        if resolved["source"] != pin.get("source"):
            raise ValueError(f"Pinned skill source drift: {name}")
        if resolved["content_hash"] != pin.get("content_hash"):
            raise ValueError(f"Pinned skill content drift: {name}")
        content = pin.get("content")
        if not isinstance(content, str):
            raise ValueError(f"Pinned skill content missing: {name}")
        remaining = SKILL_PROMPT_MAX_CHARS - used
        if remaining <= 0:
            truncated = True
            break
        if len(content) > remaining:
            contents.append(content[:remaining])
            truncated = True
            break
        contents.append(content)
        used += len(content)
    return contents, truncated


def load_skill_prompt_contents(
    skill_names: list[str], *, skip_missing: bool = False
) -> tuple[list[str], bool, list[str]]:
    """Load skill instructions within the shared prompt budget.

    Missing skills are returned for callers that can safely continue with a
    stale profile reference. Interactive chat keeps its existing strict
    validation before calling this helper.
    """
    contents: list[str] = []
    missing: list[str] = []
    used = 0
    truncated = False
    for name in skill_names:
        try:
            content = read_skill_content(name)
        except FileNotFoundError:
            if not skip_missing:
                raise
            missing.append(name)
            continue
        remaining = SKILL_PROMPT_MAX_CHARS - used
        if remaining <= 0:
            truncated = True
            break
        if len(content) > remaining:
            contents.append(content[:remaining])
            truncated = True
            break
        contents.append(content)
        used += len(content)
    return contents, truncated, missing


def system_prompt_with_skills(system_prompt: str | None, contents: list[str]) -> str | None:
    """Append activated skill instructions in the common chat/workflow format."""
    if not contents:
        return system_prompt
    skills_prompt = "\n\n[Activated skills]\n" + "\n\n---\n\n".join(contents)
    return f"{system_prompt}{skills_prompt}" if system_prompt else skills_prompt.removeprefix("\n\n")


def drift() -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for entry in _scan_all_sources():
        by_name.setdefault(entry["name"], []).append(entry)

    results: list[dict[str, Any]] = []
    for name, group in by_name.items():
        variants: list[dict[str, Any]] = []
        for entry in sorted(group, key=lambda row: row["source"]):
            mtime_ns = _dir_mtime_ns(Path(entry["path"]))
            mtime = dt.datetime.fromtimestamp(mtime_ns / 1e9, tz=dt.UTC).isoformat() if mtime_ns else None
            variants.append(
                {
                    "id": entry["id"],
                    "source": entry["source"],
                    "path": entry["path"],
                    "content_hash": entry["content_hash"],
                    "mtime": mtime,
                }
            )
        hashes = {variant["content_hash"] for variant in variants}
        results.append({"name": name, "variants": variants, "in_sync": len(hashes) <= 1})

    results.sort(key=lambda item: (item["in_sync"], str(item["name"])))
    return results


def deploy_log(limit: int = 50) -> list[dict[str, Any]]:
    if limit <= 0:
        return []

    try:
        lines = _deploy_log_path().read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    except OSError:
        return []

    rows: list[dict[str, Any]] = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(row, dict):
            rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def deploy(skill_id: str, target: str) -> dict[str, Any]:
    sources = _sources()
    if target not in sources:
        raise ValueError(f"Unknown deploy target: {target}")

    entry = next((row for row in _scan_all_sources() if row["id"] == skill_id), None)
    if entry is None:
        raise FileNotFoundError(f"Skill not found: {skill_id}")

    source_path = Path(entry["path"])
    target_root = sources[target]
    target_root.mkdir(parents=True, exist_ok=True)
    dest_path = target_root / source_path.name

    if dest_path.exists():
        timestamp = time.strftime("%Y%m%dT%H%M%S")
        backup_path = dest_path.parent / f"{dest_path.name}.bak-{timestamp}"
        suffix = 1
        while backup_path.exists():
            backup_path = dest_path.parent / f"{dest_path.name}.bak-{timestamp}-{suffix}"
            suffix += 1
        shutil.move(str(dest_path), str(backup_path))

    if source_path.is_dir():
        shutil.copytree(source_path, dest_path)
    else:
        shutil.copy2(source_path, dest_path)

    _clear_cache()
    _append_deploy_log(skill_id, target, str(dest_path))
    return {"ok": True, "target": target, "path": str(dest_path)}


def _append_deploy_log(skill_id: str, target: str, dest_path: str) -> None:
    log_path = _deploy_log_path()
    record = {
        "ts": dt.datetime.now(dt.UTC).isoformat(),
        "skill_id": skill_id,
        "target": target,
        "path": dest_path,
    }
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass
