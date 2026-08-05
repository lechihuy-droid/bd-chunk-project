import asyncio

import httpx
import pytest

from adapters.langgraph_runtime import LangGraphRuntimeAdapter
from adapters.mlflow_prompt import MlflowPromptAdapter
from ports.prompt_registry import PromptResolutionError
from ports.runtime import CancelRunRequest, ResumeRunRequest, RuntimeCapabilityNotSupported


class _Prompt:
    def __init__(self, version: int) -> None:
        self.name = "api-bd-generator"
        self.version = version
        self.template = "template"


class _ClientStub:
    """Đóng vai MlflowClient: alias luôn đọc lại giá trị hiện tại, không cache."""

    def __init__(self, alias_version: int) -> None:
        self.alias_version = alias_version

    def get_prompt_version_by_alias(self, name: str, alias: str) -> _Prompt:
        return _Prompt(self.alias_version)

    def get_prompt_version(self, name: str, version: str) -> _Prompt:
        return _Prompt(int(version))


def test_mlflow_prompt_adapter_resolves_integer_version() -> None:
    resolved = MlflowPromptAdapter(_ClientStub(2)).resolve("api-bd-generator", alias="production")
    assert resolved.version == 2
    assert isinstance(resolved.version, int)
    assert resolved.uri == "prompts:/api-bd-generator/2"


def test_mlflow_prompt_adapter_sees_alias_moves() -> None:
    """Adapter không được cache alias — alias là mutable pointer, phải đọc lại mỗi lần."""
    client = _ClientStub(1)
    adapter = MlflowPromptAdapter(client)
    assert adapter.resolve("api-bd-generator", alias="production").version == 1
    client.alias_version = 2
    assert adapter.resolve("api-bd-generator", alias="production").version == 2


def test_mlflow_prompt_adapter_rejects_ambiguous_arguments() -> None:
    adapter = MlflowPromptAdapter(_ClientStub(1))
    with pytest.raises(PromptResolutionError):
        adapter.resolve("api-bd-generator")
    with pytest.raises(PromptResolutionError):
        adapter.resolve("api-bd-generator", alias="production", version=1)


def test_mlflow_prompt_adapter_wraps_mlflow_exception() -> None:
    from mlflow.exceptions import MlflowException

    class Failing:
        def get_prompt_version_by_alias(self, name: str, alias: str):
            raise MlflowException("missing prompt")

    with pytest.raises(PromptResolutionError):
        MlflowPromptAdapter(Failing()).resolve("api-bd-generator", alias="production")


def test_langgraph_adapter_capabilities_and_status_mapping() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"canonical": "error", "provider_status": "error"})

    adapter = LangGraphRuntimeAdapter("http://runtime", httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    status = asyncio.run(adapter.get_status("run-1"))
    assert status.canonical == "FAILED"
    with pytest.raises(RuntimeCapabilityNotSupported):
        asyncio.run(adapter.resume(ResumeRunRequest("c", "r", {})))
    with pytest.raises(RuntimeCapabilityNotSupported):
        asyncio.run(adapter.cancel(CancelRunRequest("c", "r")))


def test_langgraph_adapter_marks_unknown_status_failed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"canonical": "mystery", "provider_status": "mystery"})

    adapter = LangGraphRuntimeAdapter("http://runtime", httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    status = asyncio.run(adapter.get_status("run-1"))
    assert status.canonical == "FAILED"
    assert status.detail == "RUNTIME_STATUS_UNKNOWN"
