from __future__ import annotations

from pathlib import Path

import pytest

import config
from services import runs


FIXTURE_RUNS_DIR = Path(__file__).resolve().parent / "fixtures" / "runs"
FIXTURE_RUN_ID = "20260627-234104-workspace-smoke"


@pytest.fixture(autouse=True)
def fixture_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "RUNS_DIR", FIXTURE_RUNS_DIR)
    runs._RUNS_CACHE.update({"expires": 0.0, "base": None, "items": []})


def test_list_runs_returns_summary_contract() -> None:
    items = runs.list_runs()
    assert len(items) == 1
    assert items[0]["run_id"] == FIXTURE_RUN_ID
    assert items[0]["suite"] == "workspace-smoke"
    assert items[0]["status"] == "pass"
    assert items[0]["passed"] == 11
    assert items[0]["failed"] == 0
    assert items[0]["total"] == 11
    assert items[0]["duration_seconds"] > 0
    assert "results" not in items[0]


def test_get_run_returns_detail_with_report_artifacts_and_logs() -> None:
    detail = runs.get_run(FIXTURE_RUN_ID)
    assert detail["summary"]["run_id"] == FIXTURE_RUN_ID
    assert len(detail["checks"]) == 11
    assert detail["report_md"].startswith("# Harness Report")
    assert "summary.json" in detail["artifacts"]
    assert "report.md" in detail["artifacts"]
    assert "logs/recall-tests.stdout.txt" in detail["artifacts"]
    recall = next(check for check in detail["checks"] if check["id"] == "recall-tests")
    assert "logs/recall-tests.stdout.txt" in recall["logs"]


def test_read_artifact_rejects_missing_or_outside_run() -> None:
    assert "Harness Report" in runs.read_artifact(FIXTURE_RUN_ID, "report.md")
    with pytest.raises(FileNotFoundError):
        runs.get_run("missing")
    with pytest.raises(PermissionError):
        runs.read_artifact(FIXTURE_RUN_ID, "../outside.txt")
