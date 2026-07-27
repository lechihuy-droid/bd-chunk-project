from __future__ import annotations

import datetime as dt
import json
import os
from collections.abc import Generator
from copy import deepcopy
from typing import Any

import openai
from openai import OpenAI

import config


NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
AUTH_ERROR_MESSAGE = "NVIDIA_API_KEY not set in environment"
AUTH_INVALID_ERROR_MESSAGE = "NVIDIA_API_KEY not set / invalid"
CHAT_USAGE_FILE = config.HUB_DIR / ".cache" / "chat_usage.jsonl"


class ChatAuthError(RuntimeError):
    """Raised when chat cannot authenticate with NVIDIA."""


class ChatUpstreamError(RuntimeError):
    """Raised when NVIDIA returns a non-auth upstream API status error."""

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


def _detail_text(value: object) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return str(value)


def _body_detail(body: object) -> str:
    if isinstance(body, dict) and "detail" in body:
        return _detail_text(body["detail"])
    return ""


def _api_status_detail(exc: openai.APIStatusError) -> str:
    detail = _body_detail(getattr(exc, "body", None))
    if detail:
        return detail
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            detail = _body_detail(response.json())
        except ValueError:
            detail = ""
        if detail:
            return detail
    return str(exc)


def _api_status_code(exc: openai.APIStatusError) -> int:
    code = getattr(exc, "status_code", None)
    if code is None and getattr(exc, "response", None) is not None:
        code = exc.response.status_code
    return int(code or 0)


def _upstream_error_message(model: str, code: int, detail: str) -> str:
    if code == 410:
        return f"Model '{model}' is unavailable (HTTP 410): {detail}"
    if code == 404:
        return f"Model '{model}' not found (HTTP 404): {detail}"
    if code == 429:
        return f"Rate limited (HTTP 429): {detail}"
    return f"Upstream error (HTTP {code}): {detail}"


def _int_usage(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _usage_event(model: str, usage: dict[str, int]) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "total_tokens": usage["total_tokens"],
    }


def _append_usage_event(usage: dict[str, Any]) -> None:
    try:
        CHAT_USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "ts": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
            "source": "chat",
            "model": usage["model"],
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "cache_read_tokens": usage["cache_read_tokens"],
            "cache_creation_tokens": usage["cache_creation_tokens"],
            "total_tokens": usage["total_tokens"],
            "calls": 1,
        }
        with CHAT_USAGE_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    except OSError:
        pass


def _empty_usage() -> dict[str, int]:
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def _usage_from_openai(value: object) -> dict[str, int]:
    input_tokens = _int_usage(getattr(value, "prompt_tokens", 0))
    output_tokens = _int_usage(getattr(value, "completion_tokens", 0))
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def _reasoning_for_model(model: str) -> dict[str, Any]:
    for entry in config.CHAT_REASONING:
        prefix = entry.get("prefix")
        if isinstance(prefix, str) and model.startswith(prefix):
            return {
                "extra_body": deepcopy(entry.get("extra_body")),
                "params": deepcopy(entry.get("params")),
                "system": entry.get("system"),
            }
    return {"extra_body": None, "params": None, "system": None}


def _messages_with_reasoning_system(
    messages: list[dict[str, str]],
    system_prompt: object,
) -> list[dict[str, str]]:
    outgoing = list(messages)
    if not isinstance(system_prompt, str) or not system_prompt:
        return outgoing
    if outgoing and outgoing[0].get("role") == "system" and outgoing[0].get("content") == system_prompt:
        return outgoing
    return [{"role": "system", "content": system_prompt}, *outgoing]


def _create_completion_with_reasoning_fallback(
    client: OpenAI,
    request: dict[str, Any],
    reasoning_param_keys: set[str],
) -> Any:
    try:
        return client.chat.completions.create(**request)
    except openai.BadRequestError:
        retry_request = dict(request)
        retry_request.pop("extra_body", None)
        for key in reasoning_param_keys:
            retry_request.pop(key, None)
        if retry_request == request:
            raise
        return client.chat.completions.create(**retry_request)


def stream_chat(
    messages: list[dict[str, str]],
    model: str,
    max_tokens: int,
    system_prompt: str | None = None,
) -> Generator[dict[str, Any], None, None]:
    if model not in config.CHAT_MODELS:
        raise ValueError(f"Unsupported chat model: {model}")
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise ChatAuthError(AUTH_ERROR_MESSAGE)

    usage = _empty_usage()
    try:
        client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)
        reasoning_plan = _reasoning_for_model(model)
        reasoning_params = reasoning_plan["params"] if isinstance(reasoning_plan["params"], dict) else {}
        messages_with_reasoning = _messages_with_reasoning_system(messages, reasoning_plan["system"])
        messages_with_reasoning = _messages_with_reasoning_system(messages_with_reasoning, system_prompt)
        request: dict[str, Any] = {
            "model": model,
            "messages": messages_with_reasoning,
            "temperature": 1,
            "top_p": 0.95,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        request.update(reasoning_params)
        extra_body = reasoning_plan["extra_body"]
        if extra_body is not None:
            request["extra_body"] = extra_body

        completion = _create_completion_with_reasoning_fallback(client, request, set(reasoning_params))
        for chunk in completion:
            chunk_usage = getattr(chunk, "usage", None)
            if chunk_usage is not None:
                usage = _usage_from_openai(chunk_usage)

            if not getattr(chunk, "choices", None):
                continue

            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
            content = getattr(delta, "content", None)
            if reasoning:
                yield {"type": "reasoning", "text": reasoning}
            if content:
                yield {"type": "delta", "text": content}
    except openai.AuthenticationError as exc:
        raise ChatAuthError(AUTH_INVALID_ERROR_MESSAGE) from exc
    except openai.APIStatusError as exc:
        code = _api_status_code(exc)
        detail = _api_status_detail(exc)
        raise ChatUpstreamError(_upstream_error_message(model, code, detail), code) from exc

    _append_usage_event(_usage_event(model, usage))
    yield {"type": "done", "usage": usage, "model": model}
