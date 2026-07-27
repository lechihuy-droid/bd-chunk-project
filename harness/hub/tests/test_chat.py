from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

import config
import server
from services import chat as chat_service


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setattr(chat_service, "CHAT_USAGE_FILE", tmp_path / "chat_usage.jsonl")
    return TestClient(server.app, headers={"x-hub-client": "harness-hub"})


def _messages() -> list[dict[str, str]]:
    return [{"role": "user", "content": "hello"}]


def _sse_events(text: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in text.replace("\r\n", "\n").strip().split("\n\n"):
        if not block.strip():
            continue
        event_name = "message"
        data_lines: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        events.append((event_name, json.loads("\n".join(data_lines))))
    return events


def _chunk(*, reasoning: str | None = None, content: str | None = None, usage: object | None = None) -> object:
    if usage is not None:
        return SimpleNamespace(choices=[], usage=usage)
    delta = SimpleNamespace(reasoning=reasoning, content=content)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)], usage=None)


def _bad_request_error() -> openai.BadRequestError:
    request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
    response = httpx.Response(400, request=request)
    return openai.BadRequestError("bad request", response=response, body=None)


def _api_status_error(status_code: int, body: object) -> openai.APIStatusError:
    request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
    response = httpx.Response(status_code, request=request, json=body)
    return openai.APIStatusError(f"upstream {status_code}", response=response, body=body)


def _install_fake_openai(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[dict[str, object]],
    chunks: list[object] | None = None,
    create: Callable[[dict[str, object]], object] | None = None,
) -> list[dict[str, object]]:
    client_calls: list[dict[str, object]] = []

    class FakeCompletions:
        def create(self, **kwargs: object) -> object:
            calls.append(kwargs)
            if create is not None:
                return create(kwargs)
            return iter(chunks if chunks is not None else [_chunk(content="ok")])

    class FakeChat:
        def __init__(self) -> None:
            self.completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs: object) -> None:
            client_calls.append(kwargs)
            self.chat = FakeChat()

    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setattr(chat_service, "OpenAI", FakeOpenAI)
    return client_calls


def test_chat_models_returns_catalog(client: TestClient) -> None:
    response = client.get("/api/chat/models")

    assert response.status_code == 200
    data = response.json()
    assert data["models"] == config.CHAT_MODELS
    assert data["default"] == "nvidia/nemotron-3-super-120b-a12b"
    assert data["catalog"] == config.CHAT_MODEL_CATALOG
    assert len(data["catalog"]) == 21


def test_chat_models_are_derived_from_catalog() -> None:
    assert config.CHAT_MODELS == [row["id"] for row in config.CHAT_MODEL_CATALOG]
    assert len(config.CHAT_MODELS) == 21


def test_chat_rejects_unknown_model(client: TestClient) -> None:
    response = client.post("/api/chat", json={"messages": _messages(), "model": "not-a-model"})
    events = _sse_events(response.text)

    assert response.status_code == 200
    assert [event for event, _payload in events] == ["error"]
    assert "not-a-model" in str(events[0][1]["message"])


def test_chat_rejects_unknown_agent(client: TestClient) -> None:
    response = client.post("/api/chat", json={"agent_id": "missing", "messages": _messages()})

    assert response.status_code == 400
    assert "missing" in response.json()["detail"]


def test_chat_rejects_unknown_skill(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server.skill_library, "list_skill_names", lambda: {"known-skill"})

    response = client.post("/api/chat", json={"skills": ["missing-skill"], "messages": _messages()})

    assert response.status_code == 400
    assert "missing-skill" in response.json()["detail"]


def test_skill_names_endpoint_matches_chat_validator(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    names = {"caveman", "skillspector"}
    monkeypatch.setattr(server.skill_library, "list_skill_names", lambda: names)
    monkeypatch.setattr(server.skill_library, "read_skill_content", lambda name: f"content for {name}")

    response = client.get("/api/skills/names")

    assert response.status_code == 200
    assert response.json() == sorted(names)
    for name in response.json():
        assert server._chat_skills([name])[0] == [f"content for {name}"]


def test_chat_loads_skill_after_agent_prompt(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)
    monkeypatch.setattr(server.skill_library, "list_skill_names", lambda: {"known-skill"})
    monkeypatch.setattr(server.skill_library, "read_skill_content", lambda _name: "Follow skill rules.")
    monkeypatch.setattr(server.runtime_agents, "get_agent", lambda _agent_id: {
        "id": "reviewer", "provider": "nvidia", "model": config.CHAT_DEFAULT_MODEL,
        "system_prompt": "Agent role.", "skills": [], "permission": "read_only",
        "budget": {"seconds": 60, "max_calls": 1}, "risk_tier": "read_only",
    })

    response = client.post("/api/chat", json={
        "agent_id": "reviewer", "skills": ["known-skill"], "messages": _messages(),
    })

    assert response.status_code == 200
    sent_messages = calls[0]["messages"]
    assert isinstance(sent_messages, list)
    agent_skill_index = next(index for index, message in enumerate(sent_messages) if message["content"] == "Agent role.\n\n[Activated skills]\nFollow skill rules.")
    user_index = next(index for index, message in enumerate(sent_messages) if message["role"] == "user")
    assert agent_skill_index < user_index


def test_chat_without_skills_never_collects_telemetry(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)
    monkeypatch.setattr(server.skill_library, "list_skills", lambda: (_ for _ in ()).throw(AssertionError("telemetry")))

    response = client.post("/api/chat", json={"messages": _messages(), "model": config.CHAT_DEFAULT_MODEL})

    assert response.status_code == 200
    assert calls


def test_chat_reports_skill_prompt_truncation(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_openai(monkeypatch, [])
    monkeypatch.setattr(server.skill_library, "list_skill_names", lambda: {"large-skill"})
    monkeypatch.setattr(server.skill_library, "read_skill_content", lambda _name: "x" * (server.CHAT_SKILL_MAX_CHARS + 1))

    response = client.post("/api/chat", json={"skills": ["large-skill"], "messages": _messages()})
    events = _sse_events(response.text)

    assert response.status_code == 200
    assert "cắt" in str(events[-1][1]["skill_notice"])


def test_chat_agent_overrides_provider_model_and_delivers_system_prompt(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)
    monkeypatch.setattr(server.runtime_agents, "get_agent", lambda _agent_id: {
        "id": "reviewer", "provider": "nvidia", "model": "deepseek-ai/deepseek-v4-flash",
        "system_prompt": "Review strictly.", "skills": [], "permission": "read_only",
        "budget": {"seconds": 60, "max_calls": 1}, "risk_tier": "read_only",
    })

    response = client.post("/api/chat", json={
        "agent_id": "reviewer", "provider": "claude", "model": config.CHAT_DEFAULT_MODEL,
        "messages": _messages(),
    })

    assert response.status_code == 200
    assert calls[0]["model"] == "deepseek-ai/deepseek-v4-flash"
    assert calls[0]["messages"] == [{"role": "system", "content": "Review strictly."}, *_messages()]


def test_chat_agent_with_null_model_uses_client_model(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)
    monkeypatch.setattr(server.runtime_agents, "get_agent", lambda _agent_id: {
        "id": "reviewer", "provider": "nvidia", "model": None, "system_prompt": "Review.",
        "skills": [], "permission": "read_only", "budget": {"seconds": 60, "max_calls": 1},
        "risk_tier": "read_only",
    })

    response = client.post("/api/chat", json={
        "agent_id": "reviewer", "provider": "nvidia", "model": config.CHAT_DEFAULT_MODEL,
        "messages": _messages(),
    })

    assert response.status_code == 200
    assert calls[0]["model"] == config.CHAT_DEFAULT_MODEL
    assert calls[0]["messages"][0] == {"role": "system", "content": "Review."}


def test_chat_rejects_client_system_message(client: TestClient) -> None:
    response = client.post("/api/chat", json={"messages": [{"role": "system", "content": "spoof"}]})

    assert response.status_code == 400


def test_chat_streams_delta_done_and_records_usage(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []
    client_calls = _install_fake_openai(
        monkeypatch,
        calls,
        chunks=[
            _chunk(reasoning="think"),
            _chunk(content="Hel"),
            _chunk(content="lo"),
            _chunk(usage=SimpleNamespace(prompt_tokens=12, completion_tokens=5, total_tokens=17)),
        ],
    )

    response = client.post("/api/chat", json={"messages": _messages(), "model": config.CHAT_DEFAULT_MODEL})
    events = _sse_events(response.text)

    assert response.status_code == 200
    assert [event for event, _payload in events] == ["reasoning", "delta", "delta", "done"]
    assert events[0][1] == {"text": "think"}
    assert events[1][1] == {"text": "Hel"}
    assert events[2][1] == {"text": "lo"}
    assert events[3][1] == {
        "usage": {"input_tokens": 12, "output_tokens": 5, "total_tokens": 17},
        "model": config.CHAT_DEFAULT_MODEL,
        "session_id": None,
    }
    assert client_calls == [{"base_url": chat_service.NVIDIA_BASE_URL, "api_key": "test-key"}]
    assert calls == [
        {
            "model": config.CHAT_DEFAULT_MODEL,
            "messages": [{"role": "system", "content": "detailed thinking on"}, *_messages()],
            "temperature": 1,
            "top_p": 0.95,
            "max_tokens": config.CHAT_MAX_TOKENS,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
    ]

    usage_lines = (tmp_path / "chat_usage.jsonl").read_text(encoding="utf-8").splitlines()
    event = json.loads(usage_lines[0])
    assert event["source"] == "chat"
    assert event["model"] == config.CHAT_DEFAULT_MODEL
    assert event["input_tokens"] == 12
    assert event["output_tokens"] == 5
    assert event["cache_read_tokens"] == 0
    assert event["cache_creation_tokens"] == 0
    assert event["total_tokens"] == 17
    assert event["calls"] == 1


@pytest.mark.parametrize(
    "model",
    [
        config.CHAT_DEFAULT_MODEL,
        "deepseek-ai/deepseek-v4-flash",
        "openai/gpt-oss-120b",
    ],
)
def test_chat_always_sends_configured_max_tokens_across_model_branches(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    model: str,
) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)

    response = client.post("/api/chat", json={"messages": _messages(), "model": model})

    assert response.status_code == 200
    assert calls
    assert all(call["max_tokens"] == config.CHAT_MAX_TOKENS for call in calls)


def test_chat_deepseek_uses_thinking_extra_body(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)

    response = client.post("/api/chat", json={"messages": _messages(), "model": "deepseek-ai/deepseek-v4-flash"})

    assert response.status_code == 200
    assert calls[0]["extra_body"] == {"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}}


def test_chat_qwen_uses_thinking_extra_body(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)

    response = client.post("/api/chat", json={"messages": _messages(), "model": "qwen/qwen3.5-122b-a10b"})

    assert response.status_code == 200
    assert calls[0]["extra_body"] == {"chat_template_kwargs": {"thinking": True}}
    assert "reasoning_effort" not in calls[0]


def test_chat_gpt_oss_uses_top_level_reasoning_effort(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)

    response = client.post("/api/chat", json={"messages": _messages(), "model": "openai/gpt-oss-120b"})

    assert response.status_code == 200
    assert calls[0]["reasoning_effort"] == "high"
    assert "extra_body" not in calls[0]


def test_chat_nemotron_uses_system_reasoning_prompt(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)

    response = client.post(
        "/api/chat",
        json={"messages": _messages(), "model": "nvidia/nemotron-3-ultra-550b-a55b"},
    )

    assert response.status_code == 200
    assert calls[0]["messages"] == [{"role": "system", "content": "detailed thinking on"}, *_messages()]
    assert "extra_body" not in calls[0]
    assert "reasoning_effort" not in calls[0]


def test_chat_plain_model_sends_no_reasoning_flags(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    _install_fake_openai(monkeypatch, calls)

    response = client.post(
        "/api/chat",
        json={"messages": _messages(), "model": "mistralai/mistral-small-4-119b-2603"},
    )

    assert response.status_code == 200
    assert calls[0]["messages"] == _messages()
    assert "extra_body" not in calls[0]
    assert "reasoning_effort" not in calls[0]


def test_chat_retries_bad_request_without_reasoning_extras(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def create(_kwargs: dict[str, object]) -> object:
        if len(calls) == 1:
            raise _bad_request_error()
        return iter([_chunk(content="ok")])

    _install_fake_openai(monkeypatch, calls, create=create)

    response = client.post("/api/chat", json={"messages": _messages(), "model": "openai/gpt-oss-120b"})
    events = _sse_events(response.text)

    assert response.status_code == 200
    assert [event for event, _payload in events] == ["delta", "done"]
    assert events[0][1] == {"text": "ok"}
    assert len(calls) == 2
    assert calls[0]["reasoning_effort"] == "high"
    assert "extra_body" not in calls[0]
    assert "reasoning_effort" not in calls[1]
    assert "extra_body" not in calls[1]


def test_chat_missing_key_streams_error_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_openai(**_kwargs: object) -> object:
        raise AssertionError("OpenAI client should not be constructed without a key")

    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr(chat_service, "OpenAI", fail_openai)

    response = client.post("/api/chat", json={"messages": _messages(), "model": config.CHAT_DEFAULT_MODEL})
    events = _sse_events(response.text)

    assert response.status_code == 200
    assert events == [("error", {"message": chat_service.AUTH_ERROR_MESSAGE, "code": None})]


@pytest.mark.parametrize(
    ("status_code", "detail", "expected_message"),
    [
        (
            410,
            "The model has reached its end of life and is no longer available.",
            f"Model '{config.CHAT_DEFAULT_MODEL}' is unavailable (HTTP 410)",
        ),
        (
            404,
            "The requested model was not found.",
            f"Model '{config.CHAT_DEFAULT_MODEL}' not found (HTTP 404)",
        ),
        (
            429,
            "Too many requests.",
            "Rate limited (HTTP 429)",
        ),
    ],
)
def test_chat_upstream_status_error_streams_error_code_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    detail: str,
    expected_message: str,
) -> None:
    calls: list[dict[str, object]] = []

    def create(_kwargs: dict[str, object]) -> object:
        raise _api_status_error(status_code, {"detail": detail})

    _install_fake_openai(monkeypatch, calls, create=create)

    response = client.post("/api/chat", json={"messages": _messages(), "model": config.CHAT_DEFAULT_MODEL})
    events = _sse_events(response.text)

    assert response.status_code == 200
    assert len(calls) == 1
    assert [event for event, _payload in events] == ["error"]
    assert events[0][1]["code"] == status_code
    assert expected_message in str(events[0][1]["message"])
    assert detail in str(events[0][1]["message"])
