from __future__ import annotations

import json
from pathlib import Path

import pytest

import config
from services import behavior


def _reset_behavior(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(behavior, "_DISK_CACHE", tmp_path / "entropy-cache.json")
    behavior._BEHAVIOR_CACHE.update(
        {"expires": 0.0, "events": [], "warnings": [], "sessions": [], "entropy": [], "fingerprint": None}
    )


def test_entropy_flags_repeated_tool_and_error_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    codex_dir = tmp_path / "codex" / "2026" / "06" / "27"
    codex_dir.mkdir(parents=True)
    path = codex_dir / "rollout-2026-06-27T12-00-00-entropy.jsonl"
    rows = [
        {"timestamp": "2026-06-27T12:00:00Z", "type": "session_meta", "payload": {"model": "gpt-5-codex"}},
    ]
    for index in range(8):
        rows.append(
            {
                "timestamp": f"2026-06-27T12:00:{index + 1:02d}Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": f"call-{index}",
                    "name": "functions.shell_command",
                    "arguments": {"command": "Get-ChildItem harness"},
                },
            }
        )
    rows.append(
        {
            "timestamp": "2026-06-27T12:00:10Z",
            "type": "response_item",
            "payload": {"type": "function_call_output", "call_id": "call-7", "output": "Exit code: 1\nboom"},
        }
    )
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    monkeypatch.setattr(config, "USAGE_SOURCES", {"claude": tmp_path / "missing", "codex": [tmp_path / "codex"]})
    _reset_behavior(tmp_path, monkeypatch)

    entropy = behavior.session_entropy()

    assert len(entropy) == 1
    assert entropy[0]["flagged"] is True
    assert entropy[0]["actions"] == 9
    assert entropy[0]["max_violation_rate"] > config.ENTROPY_THRESHOLD
    assert entropy[0]["top_reason"] == "repeat_tool"
