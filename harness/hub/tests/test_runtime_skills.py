from __future__ import annotations

from pathlib import Path

import pytest

import config
from services import runtime_skills


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def skill_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Path]:
    sources = {"claude_user": tmp_path / "claude", "codex_user": tmp_path / "codex"}
    for root in sources.values():
        root.mkdir(parents=True)
    monkeypatch.setattr(config, "SKILL_SOURCES", sources, raising=False)
    return sources


def test_real_frontmatter_yields_name_title_and_description(skill_roots: dict[str, Path]) -> None:
    _write(
        skill_roots["codex_user"] / "caveman-commit" / "SKILL.md",
        "---\nname: caveman-commit\ndescription: >\n  Ultra-compressed commit message generator.\n---\n\n# Heading\n",
    )

    entries = runtime_skills.list_skills()

    assert len(entries) == 1
    assert entries[0]["id"] == "caveman-commit"
    assert entries[0]["title"] == "caveman-commit"
    assert entries[0]["description"] == "Ultra-compressed commit message generator."
    assert runtime_skills.get_skill("caveman-commit")["body"].startswith("---")


def test_frontmatter_survives_bom_and_crlf(skill_roots: dict[str, Path]) -> None:
    _write(
        skill_roots["claude_user"] / "skillspector" / "SKILL.md",
        "﻿---\r\nname: skillspector\r\ndescription: Scan a skill.\r\n---\r\nbody\r\n",
    )

    entry = runtime_skills.list_skills()[0]

    assert entry["id"] == "skillspector"
    assert entry["title"] == "skillspector"
    assert entry["description"] == "Scan a skill."


@pytest.mark.parametrize(
    "text",
    [
        "---\nname: never-closed\ndescription: dangling\nbody without a closing delimiter\n",
        "---\nname: [unbalanced\n\tdescription: \"mixed indent\n---\nbody\n",
        "not frontmatter at all\n",
        "",
    ],
)
def test_malformed_frontmatter_degrades_without_crashing(skill_roots: dict[str, Path], text: str) -> None:
    _write(skill_roots["codex_user"] / "broken-skill" / "SKILL.md", text)

    entries = runtime_skills.list_skills()

    assert len(entries) == 1
    # Falls back to the directory name instead of a synthetic hash id.
    assert entries[0]["id"] == "broken-skill"
    assert entries[0]["title"] != "Untitled skill"
    assert entries[0]["description"] != "---"
    assert runtime_skills.get_skill("broken-skill")["path"].endswith("SKILL.md")


def test_body_heading_titles_a_skill_without_frontmatter(skill_roots: dict[str, Path]) -> None:
    _write(skill_roots["codex_user"] / "demo" / "SKILL.md", "# Demo Skill\n\nUse for runtime tests.\n")

    entry = runtime_skills.list_skills()[0]

    assert entry["id"] == "demo"
    assert entry["title"] == "Demo Skill"
    assert entry["description"] == "Use for runtime tests."


def test_duplicate_version_directories_collapse_to_one_entry(skill_roots: dict[str, Path]) -> None:
    frontmatter = "---\nname: control-chrome\ndescription: Drive Chrome.\n---\n"
    _write(skill_roots["codex_user"] / "control-chrome" / "SKILL.md", frontmatter)

    entries = runtime_skills.list_skills()

    assert [entry["id"] for entry in entries] == ["control-chrome"]


def test_same_skill_in_two_sources_collapses_to_one_entry(skill_roots: dict[str, Path]) -> None:
    _write(skill_roots["claude_user"] / "skillspector" / "SKILL.md", "---\nname: skillspector\n---\n")
    _write(skill_roots["codex_user"] / "skillspector" / "SKILL.md", "---\nname: skillspector\n---\n")

    entries = runtime_skills.list_skills()

    assert [entry["id"] for entry in entries] == ["skillspector"]


def test_scan_is_scoped_to_configured_skill_sources(skill_roots: dict[str, Path], tmp_path: Path) -> None:
    _write(skill_roots["codex_user"] / "mine" / "SKILL.md", "---\nname: mine\n---\n")
    # Vendored plugin cache lives outside the configured sources -> not listed.
    _write(tmp_path / "plugins" / "cache" / "bundled" / "SKILL.md", "---\nname: bundled\n---\n")
    # Nested packages are not a second discovery surface; skill_library owns direct source entries.
    _write(skill_roots["codex_user"] / ".system" / "skill-installer" / "SKILL.md", "---\nname: skill-installer\n---\n")

    ids = {entry["id"] for entry in runtime_skills.list_skills()}

    assert ids == {"mine"}


def test_get_skill_rejects_unknown_id(skill_roots: dict[str, Path]) -> None:
    with pytest.raises(FileNotFoundError):
        runtime_skills.get_skill("does-not-exist")
