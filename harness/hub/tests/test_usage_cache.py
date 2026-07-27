from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import config
from parsers import claude_sessions, codex_sessions, inspect_eval
from services import usage


def _write_event(
    path: Path,
    *,
    ts: str,
    model: str = "test-model",
    source: str = "claude",
    input_tokens: int = 1,
    output_tokens: int = 2,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
    calls: int = 1,
) -> None:
    data = {
        "ts": ts,
        "model": model,
        "source": source,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": cache_creation_tokens,
        "total_tokens": input_tokens + output_tokens + cache_read_tokens + cache_creation_tokens,
        "calls": calls,
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def _event_from_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "ts": data["ts"],
        "source": data["source"],
        "model": data["model"],
        "session": path.stem,
        "command": None,
        "input_tokens": data["input_tokens"],
        "output_tokens": data["output_tokens"],
        "cache_read_tokens": data["cache_read_tokens"],
        "cache_creation_tokens": data["cache_creation_tokens"],
        "total_tokens": data["total_tokens"],
        "calls": data["calls"],
    }


@pytest.fixture()
def fake_usage_sources(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, list[Path]]:
    root = tmp_path / "sessions"
    root.mkdir()
    parse_calls: list[Path] = []

    def parse_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
        parse_calls.append(path)
        return [_event_from_file(path)], []

    monkeypatch.setattr(usage, "_DISK_CACHE", tmp_path / "usage_files.json")
    usage._USAGE_CACHE.update({"expires": 0.0, "events": [], "warnings": [], "fingerprint": None})
    monkeypatch.setattr(config, "CHAT_USAGE_FILE", tmp_path / "chat_usage_absent.jsonl")
    monkeypatch.setattr(claude_sessions, "paths", lambda: sorted(root.glob("*.jsonl")))
    monkeypatch.setattr(claude_sessions, "parse_file", parse_file)
    monkeypatch.setattr(codex_sessions, "paths", lambda: [])
    monkeypatch.setattr(inspect_eval, "paths", lambda: [])
    return root, parse_calls


def test_collect_all_reuses_per_file_cache_without_reparse(
    fake_usage_sources: tuple[Path, list[Path]],
) -> None:
    root, parse_calls = fake_usage_sources
    first = root / "first.jsonl"
    second = root / "second.jsonl"
    _write_event(first, ts="2026-06-27T10:00:00+00:00")
    _write_event(second, ts="2026-06-27T11:00:00+00:00")

    events, warnings = usage._collect_all()
    assert warnings == []
    assert [path.name for path in parse_calls] == ["first.jsonl", "second.jsonl"]

    parse_calls.clear()
    usage._USAGE_CACHE.update({"expires": 0.0})
    cached_events, cached_warnings = usage._collect_all()

    assert parse_calls == []
    assert cached_events == events
    assert cached_warnings == warnings


def test_collect_all_reparses_only_added_or_changed_file(
    fake_usage_sources: tuple[Path, list[Path]],
) -> None:
    root, parse_calls = fake_usage_sources
    first = root / "first.jsonl"
    second = root / "second.jsonl"
    _write_event(first, ts="2026-06-27T10:00:00+00:00")
    _write_event(second, ts="2026-06-27T11:00:00+00:00")
    usage._collect_all()

    parse_calls.clear()
    third = root / "third.jsonl"
    _write_event(third, ts="2026-06-27T12:00:00+00:00")
    added_events, _warnings = usage._collect_all()

    assert [path.name for path in parse_calls] == ["third.jsonl"]
    assert {event["session"] for event in added_events} == {"first", "second", "third"}

    parse_calls.clear()
    _write_event(first, ts="2026-06-27T13:00:00+00:00", input_tokens=10)
    changed_events, _warnings = usage._collect_all()

    assert [path.name for path in parse_calls] == ["first.jsonl"]
    assert next(event for event in changed_events if event["session"] == "first")["input_tokens"] == 10


def test_collect_all_drops_removed_file_from_results_and_cache(
    fake_usage_sources: tuple[Path, list[Path]],
) -> None:
    root, parse_calls = fake_usage_sources
    kept = root / "kept.jsonl"
    removed = root / "removed.jsonl"
    removed_key = str(removed.resolve())
    _write_event(kept, ts="2026-06-27T10:00:00+00:00")
    _write_event(removed, ts="2026-06-27T11:00:00+00:00")
    usage._collect_all()

    parse_calls.clear()
    removed.unlink()
    events, warnings = usage._collect_all()
    disk_cache = json.loads(usage._DISK_CACHE.read_text(encoding="utf-8"))

    assert parse_calls == []
    assert warnings == []
    assert {event["session"] for event in events} == {"kept"}
    assert removed_key not in disk_cache["files"]


def test_collect_usage_since_filtering_and_rollup_are_unchanged(
    fake_usage_sources: tuple[Path, list[Path]],
) -> None:
    root, _parse_calls = fake_usage_sources
    _write_event(
        root / "older.jsonl",
        ts="2026-06-26T10:00:00+00:00",
        model="model-a",
        input_tokens=3,
        output_tokens=4,
        cache_read_tokens=1,
    )
    _write_event(
        root / "newer.jsonl",
        ts="2026-06-27T10:00:00+00:00",
        model="model-b",
        input_tokens=5,
        output_tokens=6,
        cache_creation_tokens=2,
    )

    events = usage.collect_usage({"source": None, "model": None, "since": None})
    filtered = usage.collect_usage({"source": None, "model": None, "since": "2026-06-27T00:00:00+00:00"})
    rolled = usage.rollup(events)

    assert [event["session"] for event in filtered] == ["newer"]
    assert [(row["model"], row["calls"], row["input_tokens"], row["output_tokens"], row["total_tokens"])
            for row in rolled["by_model"]] == [("model-b", 1, 5, 6, 13), ("model-a", 1, 3, 4, 8)]
    assert [(row["day"], row["calls"], row["input_tokens"], row["output_tokens"], row["total_tokens"])
            for row in rolled["by_day"]] == [("2026-06-26", 1, 3, 4, 8), ("2026-06-27", 1, 5, 6, 13)]
    assert [(row["source"], row["calls"], row["total_tokens"])
            for row in rolled["by_source"]] == [("claude", 2, 21)]
    assert {key: rolled["totals"][key] for key in (
        "calls", "input_tokens", "output_tokens", "total_tokens", "cache_tokens", "non_cache_tokens"
    )} == {
        "calls": 2,
        "input_tokens": 8,
        "output_tokens": 10,
        "total_tokens": 21,
        "cache_tokens": 3,
        "non_cache_tokens": 18,
    }
