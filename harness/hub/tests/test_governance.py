from __future__ import annotations

from pathlib import Path

import pytest

import config
from services import governance


@pytest.fixture()
def governance_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    path = tmp_path / "governance.json"
    monkeypatch.setattr(config, "GOVERNANCE_STATE_FILE", path)
    monkeypatch.setattr(config, "JOB_BLOCKED_TIERS", ["destructive"])
    monkeypatch.setattr(config, "GOV_RECOVERY_STEPS", 5)
    return path


def test_effective_blocked_tiers_grow_with_degradation(governance_state: Path) -> None:
    assert governance.effective_blocked_tiers(0) == ["destructive"]
    assert governance.effective_blocked_tiers(2) == ["network", "destructive"]
    assert governance.effective_blocked_tiers(3) == ["execute", "network", "destructive"]
    assert governance.effective_blocked_tiers(4) == ["write", "execute", "network", "destructive"]


def test_degradation_raises_on_denial(governance_state: Path) -> None:
    governance.record_denial("j-1", ["L2 deny"], escalate=True)

    status = governance.status()

    assert status["degradation"] == 1
    assert status["recent_denials"][0]["job_id"] == "j-1"
    assert status["recent_denials"][0]["reasons"] == ["L2 deny"]


def test_degradation_recovers_after_clean_jobs(governance_state: Path) -> None:
    governance.raise_degradation("j-1", ["L2 deny"])
    assert governance.status()["degradation"] == 1

    for _index in range(config.GOV_RECOVERY_STEPS):
        governance.record_clean_job()

    assert governance.status()["degradation"] == 0
