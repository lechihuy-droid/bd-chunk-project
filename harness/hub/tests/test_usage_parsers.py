from __future__ import annotations

from pathlib import Path

import pytest

import config
from parsers import claude_sessions, codex_sessions, inspect_eval
from services import usage


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "usage"


@pytest.fixture(autouse=True)
def fixture_usage_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        config,
        "USAGE_SOURCES",
        {
            "claude": FIXTURES / "claude_projects",
            "codex": [FIXTURES / "codex_sessions", FIXTURES / "codex_archived"],
            "inspect": FIXTURES / "inspect_logs",
        },
    )
    usage._USAGE_CACHE.update({"expires": 0.0, "events": [], "warnings": []})


def test_claude_parser_dedupes_message_id_and_warns_on_bad_line() -> None:
    events, warnings = claude_sessions.collect()

    assert len(events) == 2
    assert any("corrupt.jsonl" in warning for warning in warnings)
    opus = next(event for event in events if event["model"] == "claude-opus-4-8")
    assert opus["input_tokens"] == 10
    assert opus["output_tokens"] == 5
    assert opus["cache_read_tokens"] == 3
    assert opus["cache_creation_tokens"] == 2
    assert opus["total_tokens"] == 20
    assert opus["calls"] == 1


def test_codex_parser_uses_last_cumulative_usage_real_model_and_unknown_only_when_absent() -> None:
    events, warnings = codex_sessions.collect()

    assert len(events) == 2
    assert any("rollout-2026-06-27" in warning for warning in warnings)
    codex = next(event for event in events if event["model"] == "gpt-5-codex")
    assert codex["input_tokens"] == 15
    assert codex["output_tokens"] == 5
    assert codex["cache_read_tokens"] == 3
    assert codex["total_tokens"] == 23
    assert codex["calls"] == 2

    unknown = next(event for event in events if event["model"] == "codex:unknown")
    assert unknown["total_tokens"] == 9
    assert unknown["calls"] == 1


def test_inspect_bad_file_warns_without_crashing() -> None:
    events, warnings = inspect_eval.collect()

    assert events == []
    assert warnings


def test_usage_service_filters_and_rolls_up() -> None:
    events = usage.collect_usage({"source": None, "model": None, "since": None})
    assert [event["ts"] for event in events] == sorted([event["ts"] for event in events], reverse=True)

    filtered = usage.collect_usage({"source": "codex", "model": "gpt-5-codex", "since": "2026-06-27T00:00:00+00:00"})
    assert len(filtered) == 1
    assert filtered[0]["model"] == "gpt-5-codex"

    rolled = usage.rollup(events)
    assert rolled["totals"]["total_tokens"] == sum(event["total_tokens"] for event in events)
    assert rolled["totals"]["cache_tokens"] == sum(
        event["cache_read_tokens"] + event["cache_creation_tokens"] for event in events
    )
    assert rolled["totals"]["non_cache_tokens"] == sum(
        event["input_tokens"] + event["output_tokens"] for event in events
    )
    assert rolled["totals"]["calls"] == sum(event["calls"] for event in events)
    assert any(row["model"] == "claude-opus-4-8" for row in rolled["by_model"])
    assert any(row["source"] == "codex" for row in rolled["by_source"])
