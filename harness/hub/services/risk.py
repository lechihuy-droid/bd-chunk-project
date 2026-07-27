from __future__ import annotations

import re
import shlex
from typing import Any

import config


TIERS = ["read_only", "write", "execute", "network", "destructive"]
TIER_RANK = {tier: index for index, tier in enumerate(TIERS)}
UNKNOWN = "unknown"


def _tier(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in TIER_RANK else UNKNOWN


def _lower_map(values: Any) -> dict[str, str]:
    if not isinstance(values, dict):
        return {}
    return {str(key).lower(): _tier(value) for key, value in values.items()}


def _tokens(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value).lower() for value in values if str(value).strip()]


def _settings() -> dict[str, Any]:
    return config.load_risk_tiers()


def _basename(value: str) -> str:
    stripped = value.strip().strip("\"'")
    return re.split(r"[\\/]", stripped)[-1].lower()


def _split_command(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=False)
    except ValueError:
        return command.split()


def _word_set(parts: list[str]) -> set[str]:
    words: set[str] = set()
    for part in parts:
        lowered = _basename(part)
        words.add(lowered)
        words.update(token.lower() for token in re.findall(r"[A-Za-z0-9_.-]+", part))
    return words


def max_tier(*tiers: str | None) -> str:
    known = [_tier(tier) for tier in tiers if _tier(tier) != UNKNOWN]
    if not known:
        return UNKNOWN
    return max(known, key=lambda item: TIER_RANK[item])


def tier_at_least(tier: str | None, minimum: str) -> bool:
    normalized = _tier(tier)
    floor = _tier(minimum)
    return normalized != UNKNOWN and floor != UNKNOWN and TIER_RANK[normalized] >= TIER_RANK[floor]


def classify_tool(name: str | None) -> str:
    if not isinstance(name, str) or not name.strip():
        return UNKNOWN
    tool = name.strip().lower()
    tool_tiers = _lower_map(_settings().get("tool_tiers"))
    if tool in tool_tiers:
        return tool_tiers[tool]
    short = tool.rsplit(".", 1)[-1]
    if short in tool_tiers:
        return tool_tiers[short]
    return UNKNOWN


def classify_command(command: Any) -> str:
    if isinstance(command, (list, tuple)):
        parts = [str(part) for part in command if str(part).strip()]
        text = " ".join(parts)
    elif isinstance(command, str):
        parts = _split_command(command)
        text = command
    else:
        return UNKNOWN

    if not parts:
        return UNKNOWN

    settings = _settings()
    lowered = text.lower()
    words = _word_set(parts)

    for token in _tokens(settings.get("destructive_tokens")):
        if " " in token:
            if token in lowered:
                return "destructive"
        elif token in words:
            return "destructive"

    for token in _tokens(settings.get("network_tokens")):
        if " " in token:
            if token in lowered:
                return "network"
        elif token in words:
            return "network"

    command_tiers = _lower_map(settings.get("command_tiers"))
    executable = _basename(parts[0])
    if executable in command_tiers:
        return command_tiers[executable]
    return UNKNOWN


def command_from_input(input_data: Any) -> Any:
    if isinstance(input_data, dict):
        for key in ("command", "cmd", "argv"):
            value = input_data.get(key)
            if value:
                return value
    return None


def classify_action(tool: str | None, input_data: Any = None) -> str:
    command = command_from_input(input_data)
    if command is None:
        return classify_tool(tool)
    return max_tier(classify_tool(tool), classify_command(command))
