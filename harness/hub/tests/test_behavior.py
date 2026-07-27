from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

import config
from services import behavior, replay


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "behavior"


@pytest.fixture(autouse=True)
def fixture_behavior_sources(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        config,
        "USAGE_SOURCES",
        {
            "claude": FIXTURES / "claude_projects",
            "codex": [FIXTURES / "codex_sessions"],
            "inspect": FIXTURES / "inspect_logs",
        },
    )
    monkeypatch.setattr(behavior, "_DISK_CACHE", tmp_path / "behavior.json")
    behavior._BEHAVIOR_CACHE.update(
        {"expires": 0.0, "events": [], "warnings": [], "sessions": [], "fingerprint": None}
    )


def test_collect_tool_events_counts_claude_and_codex_tools() -> None:
    events, warnings = behavior.collect_tool_events()

    counts = Counter(event["tool"] for event in events)
    assert warnings == []
    assert len(events) == 17
    assert counts["Bash"] == 1
    assert counts["Read"] == 1
    assert counts["functions.shell_command"] == 12
    assert {event["source"] for event in events} == {"claude", "codex"}
    assert next(event for event in events if event["tool"] == "Bash")["model"] == "claude-opus-4-8"
    assert next(event for event in events if event["tool"] == "functions.shell_command")["model"] == "gpt-5-codex"


def test_tool_rollup_summarizes_tools_days_sessions_and_models() -> None:
    events, _warnings = behavior.collect_tool_events()
    rolled = behavior.tool_rollup(events)

    assert rolled["totals"] == {"tool_calls": 17, "distinct_tools": 6}
    assert rolled["by_day"] == [{"day": "2026-06-27", "count": 17}]
    shell = next(row for row in rolled["by_tool"] if row["tool"] == "functions.shell_command")
    assert shell["count"] == 12
    assert shell["sessions"] == 1
    assert shell["models"] == ["gpt-5-codex"]


def test_session_loops_flags_repeated_tool_fixture() -> None:
    loops = behavior.session_loops()
    codex = next(item for item in loops if item["source"] == "codex")
    claude = next(item for item in loops if item["source"] == "claude")

    assert codex["max_consecutive"] == 12
    assert codex["max_consecutive_same_tool"] == 12
    assert codex["top_tool"] == "functions.shell_command"
    assert codex["total_tool_calls"] == 12
    assert codex["repeat_ratio"] == pytest.approx(1 - (1 / 12))
    assert codex["loop_risk"] is True
    assert claude["loop_risk"] is False


def test_replay_latency_is_computed_and_clamped() -> None:
    session = next(item["session"] for item in replay.list_sessions() if item["source"] == "claude")

    data = replay.session_replay(session)

    assert [row["latency_s"] for row in data["agent"]] == [None, 5.0, 5.0, None, None]
    stats = next(item for item in behavior.session_loops() if item["source"] == "claude")
    assert stats["avg_latency_s"] == 5.0
    assert stats["max_latency_s"] == 5.0
