from __future__ import annotations

from pathlib import Path

from services import execution, tools


def test_mock_adapter_conforms_to_execution_port() -> None:
    adapter = execution.MockAdapter([
        {"type": "reasoning", "text": "think"}, {"type": "delta", "text": "answer"},
        {"type": "tool_call", "tool_name": "Read"}, {"type": "tool_result", "tool_output": "ok"},
        {"type": "done", "usage": {"total_tokens": 2}},
    ])
    request = execution.ExecutionRequest(
        correlation_id="test-1", provider_id="nvidia", model="model", messages=[{"role": "user", "content": "hi"}],
        system_prompt="system", tool_policy={"permission": "read_only"}, limits={"seconds": 1},
    )

    assert list(execution.execute(request, resolver=lambda _provider_id: adapter)) == adapter.events
    assert adapter.calls == [{
        "messages": [{"role": "user", "content": "hi"}], "session_id": None, "model": "model",
        "system_prompt": "system", "tool_policy": {"permission": "read_only"}, "tools": None,
    }]


def test_gateway_returns_normalized_denial() -> None:
    result = execution.gateway(execution.ExecutionRequest(
        correlation_id="test-2", provider_id="missing", model=None, messages=[],
    ))

    assert result.denied
    assert result.route is None
    assert result.error is not None
    assert result.error.message.startswith("Unknown provider: missing; valid providers or model classes:")


def test_runtime_callers_do_not_import_or_call_provider_directly() -> None:
    hub = Path(__file__).resolve().parents[1]
    workflow_source = (hub / "services" / "workflow_exec.py").read_text(encoding="utf-8")
    transport_source = (hub / "services" / "chat.py").read_text(encoding="utf-8")
    route_source = (hub / "server.py").read_text(encoding="utf-8")

    assert "from services.providers import get_provider" not in workflow_source
    assert ".stream_chat(" not in workflow_source
    assert "from services.providers import get_provider" not in transport_source
    assert ".stream_chat(" not in route_source


def test_tool_registry_has_only_read_only_schema_tools() -> None:
    assert set(tools.REGISTRY) == {"read_file", "grep", "list_dir"}
    assert all(schema["type"] == "function" and "parameters" in schema["function"] for schema in tools.schemas())


def test_dispatch_allows_permitted_file_read() -> None:
    result = tools.dispatch("read_file", {"path": "harness/hub/tests/conftest.py"}, "call-1", {"allowed_tools": ["read_file"], "allowed_paths": ["harness/hub/tests"]})
    assert result["type"] == "tool_result"
    assert "from __future__" in result["tool_output"]


def test_dispatch_refuses_unallowed_tool_and_path_traversal() -> None:
    denied_tool = tools.dispatch("read_file", {"path": "x"}, "call-1", {"allowed_tools": [], "allowed_paths": ["."]})
    denied_path = tools.dispatch("read_file", {"path": "harness/hub/tests/conftest.py"}, "call-2", {"allowed_tools": ["read_file"], "allowed_paths": ["harness/hub/services"]})
    traversal = tools.dispatch("read_file", {"path": "../outside.txt"}, "call-3", {"allowed_tools": ["read_file"], "allowed_paths": ["."]})
    assert denied_tool["tool_output"] == {"refused": "tool not allowed: read_file"}
    assert "refused" in denied_path["tool_output"]
    assert "refused" in traversal["tool_output"]


def test_nvidia_tool_loop_stops_at_cap_and_cli_path_is_unchanged() -> None:
    class ToolAdapter(execution.MockAdapter):
        def status(self):
            return {"id": "mock", "available": True, "version": None, "detail": "ok", "capabilities": {"stream": True, "tools": True}}

        def stream_chat(self, *args, **kwargs):
            self.calls.append(kwargs)
            yield {"type": "tool_call", "tool_name": "list_dir", "tool_input": {"path": "."}, "tool_use_id": "call"}
            yield {"type": "done", "usage": {}}

    adapter = ToolAdapter([])
    request = execution.ExecutionRequest("cap", "nvidia", "model", [{"role": "user", "content": "hi"}], tool_policy={"allowed_tools": ["list_dir"], "allowed_paths": ["."]})
    events = list(execution.execute(request, resolver=lambda _provider_id: adapter))
    assert len(adapter.calls) == execution.MAX_TOOL_ITERATIONS
    assert events[-1] == {"type": "error", "message": "tool loop reached cap (8)", "code": None}

    cli = execution.MockAdapter([{"type": "done", "usage": {}}])
    cli.status = lambda: {"id": "mock", "available": True, "version": None, "detail": "ok", "capabilities": {"stream": True}}  # type: ignore[method-assign]
    assert list(execution.execute(request, resolver=lambda _provider_id: cli)) == cli.events
    assert cli.calls[0]["tool_policy"] == request.tool_policy
