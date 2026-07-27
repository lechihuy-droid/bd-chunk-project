from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

import config
from parsers import claude_sessions, codex_sessions, inspect_eval
from services import usage


_NOW = dt.datetime.now(dt.UTC).date()
TODAY = _NOW.isoformat()
YESTERDAY = (_NOW - dt.timedelta(days=1)).isoformat()
EIGHT_DAYS_AGO = (_NOW - dt.timedelta(days=8)).isoformat()  # outside the 7-day window (today - 6 days)


def _line(
    *,
    ts: str,
    model: str,
    input_tokens: int = 10,
    output_tokens: int = 5,
    calls: int = 1,
) -> str:
    total = input_tokens + output_tokens
    return json.dumps(
        {
            "ts": ts,
            "source": "chat",
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": 0,
            "cache_creation_tokens": 0,
            "total_tokens": total,
            "calls": calls,
        }
    )


@pytest.fixture()
def chat_usage_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    chat_file = tmp_path / "chat_usage.jsonl"
    lines = [
        # today, claude CLI provider, 2 calls
        _line(ts=f"{TODAY}T09:00:00Z", model="cli:claude", input_tokens=100, output_tokens=50, calls=1),
        _line(ts=f"{TODAY}T10:00:00Z", model="cli:claude", input_tokens=20, output_tokens=10, calls=1),
        # today, codex CLI provider
        _line(ts=f"{TODAY}T11:00:00Z", model="cli:codex", input_tokens=40, output_tokens=20, calls=1),
        # today, nvidia via catalog id (not "nvidia/" prefixed)
        _line(
            ts=f"{TODAY}T12:00:00Z",
            model="deepseek-ai/deepseek-v4-flash",
            input_tokens=30,
            output_tokens=15,
            calls=1,
        ),
        # today, nvidia via "nvidia/" prefix
        _line(
            ts=f"{TODAY}T13:00:00Z",
            model="nvidia/nemotron-3-super-120b-a12b",
            input_tokens=5,
            output_tokens=5,
            calls=1,
        ),
        # yesterday, within the 7-day window, claude
        _line(ts=f"{YESTERDAY}T08:00:00Z", model="cli:claude", input_tokens=1, output_tokens=1, calls=1),
        # 8 days ago -- outside the 7-day window
        _line(ts=f"{EIGHT_DAYS_AGO}T08:00:00Z", model="cli:claude", input_tokens=999, output_tokens=999, calls=1),
        # unmapped model -- should be ignored by cockpit_stats but still counted by collect_usage/rollup
        _line(ts=f"{TODAY}T14:00:00Z", model="some-unmapped-model", input_tokens=7, output_tokens=7, calls=1),
    ]
    chat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    monkeypatch.setattr(config, "CHAT_USAGE_FILE", chat_file)
    monkeypatch.setattr(config, "QUOTA_WARN_PER_DAY", 3)
    monkeypatch.setattr(
        config,
        "USAGE_SOURCES",
        {
            "claude": tmp_path / "no_such_claude_dir",
            "codex": [tmp_path / "no_such_codex_dir"],
            "inspect": tmp_path / "no_such_inspect_dir",
        },
    )
    monkeypatch.setattr(claude_sessions, "paths", lambda: [])
    monkeypatch.setattr(codex_sessions, "paths", lambda: [])
    monkeypatch.setattr(inspect_eval, "paths", lambda: [])

    usage._USAGE_CACHE.update({"expires": 0.0, "events": [], "warnings": [], "fingerprint": None})
    monkeypatch.setattr(usage, "_DISK_CACHE", tmp_path / "usage_files_cache.json")

    return chat_file


def _by_provider(stats: dict, provider: str) -> dict | None:
    return next((row for row in stats["by_provider"] if row["provider"] == provider), None)


def test_collect_usage_includes_chat_events(chat_usage_env: Path) -> None:
    events = usage.collect_usage()

    assert len(events) == 8
    assert all(event["source"] == "chat" for event in events)
    claude_today = next(e for e in events if e["model"] == "cli:claude" and e["ts"].startswith(f"{TODAY}T09"))
    assert claude_today["input_tokens"] == 100
    assert claude_today["total_tokens"] == 150


def test_rollup_gathers_chat_by_model_and_by_source(chat_usage_env: Path) -> None:
    events = usage.collect_usage()
    rolled = usage.rollup(events)

    assert any(row["source"] == "chat" for row in rolled["by_source"])
    assert any(row["model"] == "cli:claude" for row in rolled["by_model"])
    assert rolled["totals"]["calls"] == 8


def test_cockpit_stats_today_groups_by_provider(chat_usage_env: Path) -> None:
    stats = usage.cockpit_stats()

    today = stats["today"]
    # 2 claude calls + 1 codex + 2 nvidia (catalog id + nvidia/ prefix) = 5 calls
    # (the unmapped model is excluded from provider grouping)
    assert today["calls"] == 5
    assert today["total_tokens"] == (150 + 30 + 60 + 45 + 10)

    claude_row = _by_provider(today, "claude")
    assert claude_row is not None
    assert claude_row["calls"] == 2
    assert claude_row["total_tokens"] == 150 + 30

    codex_row = _by_provider(today, "codex")
    assert codex_row is not None
    assert codex_row["calls"] == 1
    assert codex_row["total_tokens"] == 60

    nvidia_row = _by_provider(today, "nvidia")
    assert nvidia_row is not None
    assert nvidia_row["calls"] == 2
    assert nvidia_row["total_tokens"] == 45 + 10

    assert _by_provider(today, None) is None  # sanity: no stray provider rows
    provider_names = {row["provider"] for row in today["by_provider"]}
    assert provider_names == {"claude", "codex", "nvidia"}


def test_cockpit_stats_week7d_includes_yesterday_excludes_eight_days_ago(chat_usage_env: Path) -> None:
    stats = usage.cockpit_stats()
    week = stats["week7d"]

    claude_row = _by_provider(week, "claude")
    assert claude_row is not None
    # today's 2 claude calls (150+30 tokens) + yesterday's 1 call (2 tokens); the
    # event from 8 days ago (999+999 tokens) must be excluded from the window.
    assert claude_row["calls"] == 3
    assert claude_row["total_tokens"] == 150 + 30 + 2
    assert week["calls"] == 6  # 5 today (mapped) + 1 yesterday (claude)


def test_cockpit_stats_warn_flag_and_quota(chat_usage_env: Path) -> None:
    stats = usage.cockpit_stats()

    assert stats["quota_warn_per_day"] == 3
    assert stats["today"]["calls"] == 5
    assert stats["warn"] is True
    assert stats["providers_online"] == []


def test_cockpit_stats_no_warn_when_under_quota(chat_usage_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "QUOTA_WARN_PER_DAY", 999)
    usage._USAGE_CACHE.update({"expires": 0.0, "events": [], "warnings": [], "fingerprint": None})

    stats = usage.cockpit_stats()

    assert stats["warn"] is False


def test_cockpit_stats_missing_chat_file_is_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(config, "CHAT_USAGE_FILE", tmp_path / "does_not_exist.jsonl")
    monkeypatch.setattr(
        config,
        "USAGE_SOURCES",
        {
            "claude": tmp_path / "no_such_claude_dir",
            "codex": [tmp_path / "no_such_codex_dir"],
            "inspect": tmp_path / "no_such_inspect_dir",
        },
    )
    monkeypatch.setattr(claude_sessions, "paths", lambda: [])
    monkeypatch.setattr(codex_sessions, "paths", lambda: [])
    monkeypatch.setattr(inspect_eval, "paths", lambda: [])
    monkeypatch.setattr(usage, "_DISK_CACHE", tmp_path / "usage_files_cache2.json")
    usage._USAGE_CACHE.update({"expires": 0.0, "events": [], "warnings": [], "fingerprint": None})

    stats = usage.cockpit_stats()

    assert stats["today"] == {"by_provider": [], "calls": 0, "total_tokens": 0}
    assert stats["week7d"] == {"by_provider": [], "calls": 0, "total_tokens": 0}
    assert stats["providers_online"] == []
