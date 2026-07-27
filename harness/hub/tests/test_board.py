from __future__ import annotations

from pathlib import Path

import pytest

import config
from services import board
from services import runs


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_task_board_parses_status_without_codex_handoff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPUS_AI_DIR", FIXTURES / "board")
    monkeypatch.setattr(config, "RUNS_DIR", FIXTURES / "runs")
    runs._RUNS_CACHE.update({"expires": 0.0, "base": None, "items": []})

    data = board.task_board()

    assert data["objective"] == "Ship Harness Hub Phase 3."
    assert data["owner"] == "codex"
    assert data["updated"] == "2026-06-27"
    assert data["sub_systems"][0] == {"name": "Harness Hub", "status": "Active", "note": "Phase 3"}
    assert "Run pytest." in data["next_step"]
    assert data["source_files"] == ["harness/hub/tests/fixtures/board/status.md"]
    assert data["progress"]["latest_run"]["run_id"] == "20260627-234104-workspace-smoke"
    assert data["progress"]["pass_count"] == 1
    assert data["progress"]["fail_count"] == 0


def test_task_board_missing_fields_return_nulls_without_crashing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPUS_AI_DIR", FIXTURES / "board_missing")

    data = board.task_board()

    assert data["objective"] is None
    assert data["owner"] is None
    assert data["updated"] is None
    assert data["sub_systems"] == []
    assert data["next_step"] is None
