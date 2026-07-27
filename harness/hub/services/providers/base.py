from __future__ import annotations

from typing import Iterator, Protocol, TypedDict


class ProviderStatus(TypedDict):
    id: str
    available: bool
    version: str | None
    detail: str
    capabilities: dict[str, object]


class ChatEvent(TypedDict, total=False):
    type: str  # "reasoning" | "delta" | "done" | "error"
    text: str
    usage: dict[str, object]
    session_id: str | None
    message: str
    code: int | None


class Provider(Protocol):
    """Duck-typed contract each services/providers/<id>.py module implements at module level."""

    def status(self) -> ProviderStatus: ...

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        session_id: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[ChatEvent]: ...
