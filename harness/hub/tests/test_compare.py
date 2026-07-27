from __future__ import annotations

from pathlib import Path

import pytest

import config
from services import runs


FIXTURE_RUNS_DIR = Path(__file__).resolve().parent / "fixtures" / "compare"


@pytest.fixture(autouse=True)
def fixture_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "RUNS_DIR", FIXTURE_RUNS_DIR)
    runs._RUNS_CACHE.update({"expires": 0.0, "base": None, "items": []})


def test_compare_runs_reports_added_removed_and_status_changed() -> None:
    diff = runs.compare_runs("run-a", "run-b")

    assert diff["a"]["run_id"] == "run-a"
    assert diff["b"]["run_id"] == "run-b"
    assert [item["id"] for item in diff["added"]] == ["check-three"]
    assert [item["id"] for item in diff["removed"]] == ["check-two"]
    assert len(diff["changed"]) == 1
    assert diff["changed"][0]["id"] == "check-one"
    assert diff["changed"][0]["from_status"] == "pass"
    assert diff["changed"][0]["to_status"] == "fail"


def test_compare_runs_rejects_different_suites() -> None:
    with pytest.raises(ValueError):
        runs.compare_runs("run-a", "run-c")
