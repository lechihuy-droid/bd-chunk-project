from __future__ import annotations

from pathlib import Path

import pytest

import config
from services import replay


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "replay"


@pytest.fixture(autouse=True)
def fixture_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        config,
        "USAGE_SOURCES",
        {
            "claude": FIXTURES / "claude_projects",
            "codex": [FIXTURES / "codex_sessions"],
            "inspect": FIXTURES / "inspect_logs",
        },
    )


def test_replay_rows_have_provenance_and_trust() -> None:
    session = next(item["session"] for item in replay.list_sessions() if item["source"] == "codex")
    data = replay.session_replay(session)

    assert data["agent"][0]["provenance_role"] == "model"
    assert data["agent"][0]["trust"] == "trusted"
    assert data["monitor"][0]["provenance_role"] == "tool"
    assert data["monitor"][0]["trust"] == "untrusted"


def test_replay_tool_calls_and_results_have_tiers() -> None:
    session = next(item["session"] for item in replay.list_sessions() if item["source"] == "codex")
    data = replay.session_replay(session)

    shell_call = next(call for row in data["agent"] for call in row["tool_calls"] if call["name"] == "functions.shell_command")
    shell_result = next(row for row in data["monitor"] if row["tool"] == "functions.shell_command")

    assert shell_call["tier"] == "execute"
    assert shell_call["command_tier"] == "read_only"
    assert shell_result["tier"] == "execute"
