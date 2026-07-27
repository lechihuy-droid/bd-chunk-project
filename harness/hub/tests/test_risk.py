from __future__ import annotations

from services import risk


def test_tool_tier_defaults() -> None:
    assert risk.classify_tool("Read") == "read_only"
    assert risk.classify_tool("Edit") == "write"
    assert risk.classify_tool("functions.shell_command") == "execute"
    assert risk.classify_tool("web_search") == "network"
    assert risk.classify_tool("not-a-real-tool") == "unknown"


def test_command_tier_defaults() -> None:
    assert risk.classify_command("Get-ChildItem harness") == "read_only"
    assert risk.classify_command(["curl", "https://example.com"]) == "network"
    assert risk.classify_command("git reset --hard HEAD") == "destructive"
    assert risk.classify_command(["C:/Python/python.exe", "script.py"]) == "execute"
    assert risk.classify_command("custom-tool --flag") == "unknown"


def test_action_tier_uses_tool_and_command() -> None:
    assert risk.classify_action("functions.shell_command", {"command": "Get-ChildItem harness"}) == "execute"
    assert risk.classify_action("Bash", {"command": "curl https://example.com"}) == "network"
    assert risk.classify_action("Bash", {"command": "rm -rf tmp"}) == "destructive"
