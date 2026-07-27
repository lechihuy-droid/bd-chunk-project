from __future__ import annotations

from pathlib import Path

import pytest

import config
from services import integrity


def test_integrity_detects_tampered_suite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    suites_dir = tmp_path / "suites"
    suites_dir.mkdir()
    suite = suites_dir / "sample.json"
    suite.write_text('{"id":"sample","checks":[]}\n', encoding="utf-8")

    monkeypatch.setattr(config, "SUITES_DIR", suites_dir)
    monkeypatch.setattr(config, "HMAC_KEY_FILE", tmp_path / ".hmac_key")
    monkeypatch.setattr(config, "INTEGRITY_SIGS_FILE", tmp_path / ".cache" / "suite_sigs.json")

    signed = integrity.resign_suites()
    assert signed == [{"suite": "sample.json", "ok": True, "expected": signed[0]["actual"], "actual": signed[0]["actual"]}]

    suite.write_text('{"id":"sample","checks":[{"id":"changed"}]}\n', encoding="utf-8")
    verified = integrity.verify_suites()

    assert verified[0]["suite"] == "sample.json"
    assert verified[0]["ok"] is False
    assert verified[0]["expected"] != verified[0]["actual"]
