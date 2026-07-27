from __future__ import annotations

import os
from typing import Iterator

import config
from services import chat
from services.providers.base import ChatEvent, ProviderStatus

PROVIDER_ID = "nvidia"


def status() -> ProviderStatus:
    available = bool(os.environ.get("NVIDIA_API_KEY"))
    return {
        "id": PROVIDER_ID,
        "available": available,
        "version": None,
        "detail": "ok" if available else chat.AUTH_ERROR_MESSAGE,
        "capabilities": {"stream": True, "resume": False, "models": list(config.CHAT_MODELS)},
    }


def stream_chat(
    messages: list[dict[str, str]],
    session_id: str | None = None,
    model: str | None = None,
    system_prompt: str | None = None,
) -> Iterator[ChatEvent]:
    """Thin adapter over the existing services/chat.py NVIDIA client — does not modify it."""
    chat_model = model or config.CHAT_DEFAULT_MODEL
    try:
        if system_prompt:
            stream = chat.stream_chat(messages, chat_model, config.CHAT_MAX_TOKENS, system_prompt=system_prompt)
        else:
            stream = chat.stream_chat(messages, chat_model, config.CHAT_MAX_TOKENS)
        for item in stream:
            item_type = item.get("type")
            if item_type == "reasoning":
                yield {"type": "reasoning", "text": item.get("text", "")}
            elif item_type == "delta":
                yield {"type": "delta", "text": item.get("text", "")}
            elif item_type == "done":
                yield {"type": "done", "usage": item.get("usage", {}), "session_id": None}
    except chat.ChatUpstreamError as exc:
        yield {"type": "error", "message": str(exc), "code": exc.code or None}
    except chat.ChatAuthError as exc:
        yield {"type": "error", "message": str(exc) or chat.AUTH_ERROR_MESSAGE, "code": None}
    except ValueError as exc:
        yield {"type": "error", "message": str(exc), "code": None}
