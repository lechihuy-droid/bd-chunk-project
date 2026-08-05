from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from services import runtime_agents
from services.providers import get_provider
from services.providers.base import ChatEvent, Provider, ToolPolicy
from services import tools


ExecutionEvent = ChatEvent


@dataclass(frozen=True)
class ExecutionRequest:
    correlation_id: str
    provider_id: str
    model: str | None
    messages: list[dict[str, object]]
    session_id: str | None = None
    system_prompt: str | None = None
    tool_policy: ToolPolicy | None = None
    limits: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionError:
    message: str
    code: int | None = None


@dataclass(frozen=True)
class ExecutionRoute:
    provider_id: str
    model: str | None
    provider_class: str | None
    adapter: Provider


@dataclass(frozen=True)
class ExecutionResult:
    route: ExecutionRoute | None = None
    error: ExecutionError | None = None

    @property
    def denied(self) -> bool:
        return self.error is not None


ProviderResolver = Callable[[str], Provider]


def gateway(request: ExecutionRequest, *, resolver: ProviderResolver | None = None) -> ExecutionResult:
    """Resolve one authored provider/model route, or return an explicit denial."""
    # Bound at call time, not as a default argument, so the seam stays injectable.
    resolver = resolver or get_provider
    try:
        routed = runtime_agents.resolve_provider({"provider": request.provider_id, "model": request.model})
        return ExecutionResult(route=ExecutionRoute(
            provider_id=str(routed["provider"]), model=routed["model"], provider_class=routed["class"],
            adapter=resolver(str(routed["provider"])),
        ))
    except ValueError as exc:
        return ExecutionResult(error=ExecutionError(str(exc)))


def execute(
    request: ExecutionRequest, *, resolver: ProviderResolver | None = None, result: ExecutionResult | None = None,
) -> Iterator[ExecutionEvent]:
    """Run exactly the gateway-selected route and preserve adapter event payloads."""
    result = result or gateway(request, resolver=resolver)
    if result.error is not None:
        yield {"type": "error", "message": result.error.message, "code": result.error.code}
        return
    assert result.route is not None
    kwargs: dict[str, object] = {"session_id": request.session_id, "model": result.route.model}
    if request.system_prompt:
        kwargs["system_prompt"] = request.system_prompt
    if request.tool_policy is None or not _supports_tools(result.route.adapter):
        if request.tool_policy is not None:
            kwargs["tool_policy"] = request.tool_policy
        yield from result.route.adapter.stream_chat(request.messages, **kwargs)
        return
    messages = list(request.messages)
    for iteration in range(MAX_TOOL_ITERATIONS):
        events = list(result.route.adapter.stream_chat(messages, **kwargs, tools=tools.schemas()))
        calls = [event for event in events if event.get("type") == "tool_call"]
        for event in events:
            if event.get("type") != "done":
                yield event
        if not calls:
            yield from (event for event in events if event.get("type") == "done")
            return
        results = [tools.dispatch(str(event.get("tool_name", "")), event.get("tool_input"), str(event.get("tool_use_id", "")), request.tool_policy) for event in calls]
        for tool_result in results:
            yield tool_result
        if iteration + 1 == MAX_TOOL_ITERATIONS:
            yield {"type": "error", "message": f"tool loop reached cap ({MAX_TOOL_ITERATIONS})", "code": None}
            return
        messages.append({"role": "assistant", "content": None, "tool_calls": [{"id": event["tool_use_id"], "type": "function", "function": {"name": event["tool_name"], "arguments": json.dumps(event.get("tool_input", {}))}} for event in calls]})
        messages.extend(tools.tool_message(tool_result) for tool_result in results)


MAX_TOOL_ITERATIONS = 8


def _supports_tools(adapter: Provider) -> bool:
    try:
        status = adapter.status()
    except (AttributeError, TypeError):
        return False
    capabilities = status.get("capabilities") if isinstance(status, dict) else None
    return isinstance(capabilities, dict) and capabilities.get("tools") is True


class MockAdapter:
    """In-memory Provider adapter for execution tests; never contacts a provider."""

    def __init__(self, events: list[ChatEvent]) -> None:
        self.events = list(events)
        self.calls: list[dict[str, object]] = []

    def status(self) -> dict[str, object]:
        return {"id": "mock", "available": True, "version": None, "detail": "ok", "capabilities": {"stream": True}}

    def stream_chat(
        self, messages: list[dict[str, object]], session_id: str | None = None, model: str | None = None,
        system_prompt: str | None = None, tool_policy: ToolPolicy | None = None, tools: list[dict[str, object]] | None = None,
    ) -> Iterator[ChatEvent]:
        self.calls.append({
            "messages": messages, "session_id": session_id, "model": model,
            "system_prompt": system_prompt, "tool_policy": tool_policy, "tools": tools,
        })
        yield from self.events
