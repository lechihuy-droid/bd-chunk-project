from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import config
import server
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


def test_list_sessions_includes_claude_and_codex() -> None:
    sessions = replay.list_sessions()
    sources = {item["source"] for item in sessions}

    assert sources == {"claude", "codex"}
    assert all(item["session"] for item in sessions)


def test_claude_replay_has_tool_args_outline_and_tool_result() -> None:
    session = next(item["session"] for item in replay.list_sessions() if item["source"] == "claude")

    data = replay.session_replay(session)

    assert data["source"] == "claude"
    assert data["agent"][0]["tool_calls"][0]["input"]["command"] == "Get-ChildItem harness"
    assert data["outline"][0]["text"] == "in_progress: Implement replay"
    assert data["monitor"][0]["kind"] == "tool_result"
    assert "summary.json" in data["monitor"][0]["summary"]


def test_codex_replay_has_tool_args_outline_and_tool_result() -> None:
    session = next(item["session"] for item in replay.list_sessions() if item["source"] == "codex")

    data = replay.session_replay(session)

    assert data["source"] == "codex"
    assert any(call["name"] == "functions.shell_command" for item in data["agent"] for call in item["tool_calls"])
    assert data["outline"][0]["text"] == "in_progress: Implement replay"
    assert any(item["kind"] == "tool_result" and "summary.json" in item["summary"] for item in data["monitor"])


def test_replay_rejects_unknown_and_traversal_style_ids() -> None:
    with pytest.raises(FileNotFoundError):
        replay.session_replay("../secret")

    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})
    missing = client.get("/api/sessions/not-a-real-session/replay")
    traversal = client.get("/api/sessions/..%252Fsecret/replay")

    assert missing.status_code == 404
    assert traversal.status_code == 404
