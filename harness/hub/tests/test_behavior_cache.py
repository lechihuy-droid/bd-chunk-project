from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

import config
from services import behavior, replay


def _write_session(path: Path, ts: str, marker: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ts + marker, encoding="utf-8")


@pytest.fixture()
def fake_behavior_sources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Callable[[str, str, str], Path], list[Path]]:
    claude_root = tmp_path / "claude_projects"
    codex_root = tmp_path / "codex_sessions"
    sources: dict[Path, str] = {}
    analyze_calls: list[Path] = []

    def add_session(source: str, name: str, ts: str) -> Path:
        if source == "claude":
            path = claude_root / "Project" / f"{name}.jsonl"
        else:
            path = codex_root / "2026" / "06" / "27" / f"{name}.jsonl"
        _write_session(path, ts)
        sources[path] = source
        return path

    def records() -> dict[str, replay.SessionRecord]:
        rows: dict[str, replay.SessionRecord] = {}
        for path, source in sorted(sources.items(), key=lambda item: str(item[0])):
            if not path.exists():
                continue
            rows[path.stem] = replay.SessionRecord(
                session=path.stem,
                source=source,
                path=path,
                ts=path.read_text(encoding="utf-8").splitlines()[0],
                project=None,
            )
        return rows

    def analyze_record(record: replay.SessionRecord) -> dict[str, Any]:
        analyze_calls.append(record.path)
        ts = record.path.read_text(encoding="utf-8").splitlines()[0]
        tool = f"tool-{record.session}"
        return {
            "events": [
                {
                    "tool": tool,
                    "tier": "read",
                    "source": record.source,
                    "model": f"{record.source}-model",
                    "session": record.session,
                    "ts": ts,
                }
            ],
            "session_stat": {
                "session": record.session,
                "source": record.source,
                "max_consecutive": 1,
                "max_consecutive_same_tool": 1,
                "top_tool": tool,
                "total_tool_calls": 1,
                "repeat_ratio": 0.0,
                "loop_risk": False,
                "avg_latency_s": None,
                "max_latency_s": None,
            },
            "entropy": {
                "session": record.session,
                "source": record.source,
                "actions": 1,
                "max_violation_rate": 0.0,
                "flagged": False,
                "top_reason": None,
            },
            "warning": None,
        }

    monkeypatch.setattr(
        config,
        "USAGE_SOURCES",
        {"claude": claude_root, "codex": [codex_root], "inspect": tmp_path / "inspect_logs"},
    )
    monkeypatch.setattr(replay, "_records", records)
    monkeypatch.setattr(behavior, "_analyze_record", analyze_record)
    monkeypatch.setattr(behavior, "_DISK_CACHE", tmp_path / "behavior_files.json")
    behavior._BEHAVIOR_CACHE.update(
        {"expires": 0.0, "events": [], "warnings": [], "sessions": [], "entropy": [], "fingerprint": None}
    )
    return add_session, analyze_calls


def test_collect_all_reuses_per_file_cache_without_reanalysis(
    fake_behavior_sources: tuple[Callable[[str, str, str], Path], list[Path]],
) -> None:
    add_session, analyze_calls = fake_behavior_sources
    first = add_session("claude", "first", "2026-06-27T10:00:00+00:00")
    second = add_session("codex", "second", "2026-06-27T11:00:00+00:00")

    events, warnings, sessions, entropy = behavior._collect_all()
    assert warnings == []
    assert [path.name for path in analyze_calls] == [first.name, second.name]

    analyze_calls.clear()
    behavior._BEHAVIOR_CACHE.update({"expires": 0.0})
    cached_events, cached_warnings, cached_sessions, cached_entropy = behavior._collect_all()

    assert analyze_calls == []
    assert cached_events == events
    assert cached_warnings == warnings
    assert cached_sessions == sessions
    assert cached_entropy == entropy


def test_collect_all_reanalyzes_only_added_or_changed_session(
    fake_behavior_sources: tuple[Callable[[str, str, str], Path], list[Path]],
) -> None:
    add_session, analyze_calls = fake_behavior_sources
    first = add_session("claude", "first", "2026-06-27T10:00:00+00:00")
    second = add_session("codex", "second", "2026-06-27T11:00:00+00:00")
    behavior._collect_all()

    analyze_calls.clear()
    third = add_session("claude", "third", "2026-06-27T12:00:00+00:00")
    added_events, _warnings, added_sessions, added_entropy = behavior._collect_all()

    assert [path.name for path in analyze_calls] == [third.name]
    assert {event["session"] for event in added_events} == {"first", "second", "third"}
    assert {session["session"] for session in added_sessions} == {"first", "second", "third"}
    assert {item["session"] for item in added_entropy} == {"first", "second", "third"}

    analyze_calls.clear()
    _write_session(first, "2026-06-27T13:00:00+00:00", marker="\nchanged-size")
    changed_events, _warnings, _changed_sessions, _changed_entropy = behavior._collect_all()

    assert [path.name for path in analyze_calls] == [first.name]
    assert next(event for event in changed_events if event["session"] == "first")["ts"] == "2026-06-27T13:00:00+00:00"
    assert second.exists()


def test_collect_all_drops_removed_session_from_results_and_cache(
    fake_behavior_sources: tuple[Callable[[str, str, str], Path], list[Path]],
) -> None:
    add_session, analyze_calls = fake_behavior_sources
    kept = add_session("claude", "kept", "2026-06-27T10:00:00+00:00")
    removed = add_session("codex", "removed", "2026-06-27T11:00:00+00:00")
    removed_key = str(removed.resolve())
    behavior._collect_all()

    analyze_calls.clear()
    removed.unlink()
    events, warnings, sessions, entropy = behavior._collect_all()
    disk_cache = json.loads(behavior._DISK_CACHE.read_text(encoding="utf-8"))

    assert analyze_calls == []
    assert warnings == []
    assert {event["session"] for event in events} == {"kept"}
    assert {session["session"] for session in sessions} == {"kept"}
    assert {item["session"] for item in entropy} == {"kept"}
    assert removed_key not in disk_cache["files"]
    assert str(kept.resolve()) in disk_cache["files"]
