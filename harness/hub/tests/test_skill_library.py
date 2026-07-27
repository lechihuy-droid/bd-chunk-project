from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import config
import server
from services import skill_library as sl


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "skills"


@pytest.fixture(autouse=True)
def fixture_sources(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Path]:
    root = tmp_path / "skills"
    shutil.copytree(FIXTURES, root)
    sources = {
        "claude_user": root / "claude_user",
        "claude_project": root / "claude_project",
        "codex_user": root / "codex_user",
    }
    monkeypatch.setattr(config, "SKILL_SOURCES", sources, raising=False)
    monkeypatch.setattr(config, "SKILL_DEPLOY_LOG", tmp_path / "skill_deploy_log.jsonl", raising=False)
    # Point the Claude session-log source at an empty dir so telemetry is a
    # graceful best-effort null instead of scanning the real machine's history.
    monkeypatch.setitem(config.USAGE_SOURCES, "claude", tmp_path / "empty_claude_projects")
    sl._INDEX_CACHE.update({"expires": 0.0, "fingerprint": None, "entries": []})
    return sources


def test_list_skills_covers_all_sources_and_computes_coverage(fixture_sources: dict[str, Path]) -> None:
    entries = sl.list_skills()
    ids = {entry["id"] for entry in entries}
    assert ids == {"claude_user/skillspector", "claude_project/skillspector", "codex_user/lonewolf"}

    claude_user_entry = next(entry for entry in entries if entry["id"] == "claude_user/skillspector")
    assert claude_user_entry["name"] == "skillspector"
    assert set(claude_user_entry["coverage"]) == {"claude_user", "claude_project"}
    # No telemetry present in the fixture source -> best-effort null, not a crash.
    assert claude_user_entry["last_used"] is None
    assert claude_user_entry["use_count_30d"] is None

    lonewolf_entry = next(entry for entry in entries if entry["id"] == "codex_user/lonewolf")
    assert lonewolf_entry["coverage"] == ["codex_user"]


def test_drift_detects_content_mismatch_and_flags_unique_skill_in_sync(fixture_sources: dict[str, Path]) -> None:
    entries = sl.drift()
    by_name = {entry["name"]: entry for entry in entries}

    skillspector = by_name["skillspector"]
    assert len(skillspector["variants"]) == 2
    assert skillspector["in_sync"] is False
    hashes = {variant["content_hash"] for variant in skillspector["variants"]}
    assert len(hashes) == 2

    lonewolf = by_name["lonewolf"]
    assert len(lonewolf["variants"]) == 1
    assert lonewolf["in_sync"] is True


def test_get_skill_returns_content_and_files(fixture_sources: dict[str, Path]) -> None:
    detail = sl.get_skill("claude_user/skillspector")
    assert detail["name"] == "skillspector"
    assert "variant A" in detail["content"]
    assert detail["files"] == ["SKILL.md"]


def test_get_skill_rejects_traversal_ids(fixture_sources: dict[str, Path]) -> None:
    with pytest.raises(FileNotFoundError):
        sl.get_skill("claude_user/../../../../etc/passwd")
    with pytest.raises(FileNotFoundError):
        sl.get_skill("unknown_source/unknown_skill")


def test_deploy_creates_backup_of_existing_target_and_appends_log(fixture_sources: dict[str, Path]) -> None:
    codex_root = fixture_sources["codex_user"]
    existing = codex_root / "skillspector"
    existing.mkdir()
    (existing / "SKILL.md").write_text("---\nname: skillspector\n---\nold content", encoding="utf-8")

    result = sl.deploy("claude_user/skillspector", "codex_user")

    assert result["ok"] is True
    assert result["target"] == "codex_user"
    dest = Path(result["path"])
    assert dest == codex_root / "skillspector"
    assert "variant A" in (dest / "SKILL.md").read_text(encoding="utf-8")

    backups = list(codex_root.glob("skillspector.bak-*"))
    assert len(backups) == 1
    assert (backups[0] / "SKILL.md").read_text(encoding="utf-8") == "---\nname: skillspector\n---\nold content"

    log_path = config.SKILL_DEPLOY_LOG
    lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["skill_id"] == "claude_user/skillspector"
    assert record["target"] == "codex_user"
    assert record["path"] == str(dest)


def test_deploy_rejects_target_outside_skill_sources(fixture_sources: dict[str, Path]) -> None:
    with pytest.raises(ValueError):
        sl.deploy("claude_user/skillspector", "not_a_real_target")


def test_deploy_rejects_unknown_skill_id(fixture_sources: dict[str, Path]) -> None:
    with pytest.raises(FileNotFoundError):
        sl.deploy("claude_user/does_not_exist", "codex_user")


def test_deploy_log_endpoint_returns_newest_rows_first() -> None:
    records = [
        {"ts": "2026-01-01T00:00:00+00:00", "skill_id": "claude_user/old", "target": "codex_user", "path": "old"},
        {"ts": "2026-01-02T00:00:00+00:00", "skill_id": "codex_user/new", "target": "claude_user", "path": "new"},
    ]
    config.SKILL_DEPLOY_LOG.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )

    response = TestClient(server.app).get("/api/skill-library/deploy-log")

    assert response.status_code == 200
    assert response.json() == list(reversed(records))


def test_deploy_log_endpoint_returns_empty_list_when_file_missing() -> None:
    response = TestClient(server.app).get("/api/skill-library/deploy-log")

    assert response.status_code == 200
    assert response.json() == []
