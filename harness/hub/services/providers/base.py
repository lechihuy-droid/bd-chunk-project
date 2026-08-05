from __future__ import annotations

from typing import Iterator, Protocol, TypedDict


class ProviderStatus(TypedDict):
    id: str
    available: bool
    version: str | None
    detail: str
    capabilities: dict[str, object]


class ChatEvent(TypedDict, total=False):
    type: str  # "reasoning" | "delta" | "tool_call" | "tool_result" | "done" | "error"
    text: str
    usage: dict[str, object]
    session_id: str | None
    message: str
    code: int | None
    tool_name: str
    tool_input: object
    tool_use_id: str
    tool_output: object


class ToolPolicy(TypedDict, total=False):
    permission: str
    allowed_tools: list[str]
    allowed_paths: list[str]


class Provider(Protocol):
    """Duck-typed contract each services/providers/<id>.py module implements at module level."""

    def status(self) -> ProviderStatus: ...

    def stream_chat(
        self,
        messages: list[dict[str, object]],
        session_id: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        tool_policy: ToolPolicy | None = None,
        tools: list[dict[str, object]] | None = None,
    ) -> Iterator[ChatEvent]: ...


def turn_context(messages: list[dict[str, str]]) -> str:
    """Join system-role messages carried by a single turn.

    CLI providers are driven by one prompt string, so they read only the latest
    user message. Per-turn context the hub injects as system messages — chat
    file attachments, for example — is otherwise dropped for them. Unlike an
    agent's static system prompt this can change between turns, so it must be
    replayed even when resuming a session.
    """
    return "\n\n".join(
        content for item in messages
        if item.get("role") == "system" and (content := (item.get("content") or "").strip())
    )


def latest_user_prompt(messages: list[dict[str, str]]) -> str:
    """The prompt text a single-prompt CLI provider actually sends."""
    for item in reversed(messages):
        if item.get("role") == "user":
            return item.get("content", "")
    return messages[-1].get("content", "") if messages else ""


def turn_prompt(messages: list[dict[str, str]]) -> str:
    """Assemble one CLI prompt: this turn's system context plus the user text."""
    prompt = latest_user_prompt(messages)
    turn = turn_context(messages)
    return f"{turn}\n\n[User request]\n{prompt}" if turn else prompt
