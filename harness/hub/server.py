from __future__ import annotations

import json
import hashlib
import logging
import re
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx


HUB_DIR = Path(__file__).resolve().parent
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

import config
from services import (
    behavior,
    artifact_comments,
    board,
    chat_files,
    chat,
    execution,
    gitjobs,
    governance,
    hooks,
    inspect_evals,
    integrity,
    replay,
    risk,
    runs,
    runtime_agents,
    runtime_artifacts,
    runtime_events,
    runtime_files,
    runtime_interrupts,
    runtime_memory,
    run_inputs,
    runtime_pipeline,
    runtime_policy,
    retention,
    runtime_skills,
    search,
    runtime_state,
    skill_library,
    suites,
    trigger,
    usage,
    workflow,
    workflow_exec,
)
from services.providers import list_providers

# Compatibility for existing in-process callers; API chat execution uses services.execution.
get_provider = execution.get_provider


@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=usage.warm, name="usage-warm", daemon=True).start()
    threading.Thread(target=behavior.warm, name="behavior-warm", daemon=True).start()
    # The first skill-library call parses the telemetry log and walks every skill
    # source, so without this the Skills metric sits in its skeleton for seconds
    # after each restart while the rest of the dashboard has already resolved.
    threading.Thread(target=skill_library.list_skills, name="skills-warm", daemon=True).start()
    threading.Thread(target=list_providers, name="providers-warm", daemon=True).start()
    try:
        gitjobs.reconcile_orphans()
    except Exception:
        pass
    try:
        retention.sweep()
    except Exception:
        pass
    yield
    try:
        from services.providers import procs

        procs.kill_all()
    except Exception:
        pass


app = FastAPI(title="Harness Hub", lifespan=lifespan)
WEB_V3_DIST = HUB_DIR / "web-v3" / "dist"
if WEB_V3_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_V3_DIST / "assets")), name="assets-v3")

_CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_SCHEMA_VERSION = "1"
_IDEMPOTENCY_LOCK = threading.Lock()
_IDEMPOTENCY_RESULTS: dict[tuple[str, str], tuple[int, bytes, str]] = {}
_IDEMPOTENT_COMMANDS = {
    ("POST", "/api/jobs"),
    ("POST", "/api/agent/runs"),
    ("POST", "/api/runs/trigger"),
}
_LOGGER = logging.getLogger(__name__)


def _is_idempotent_command(request: Request) -> bool:
    if (request.method, request.url.path) in _IDEMPOTENT_COMMANDS:
        return True
    return request.method == "POST" and bool(re.fullmatch(
        r"/api/(?:jobs/[^/]+/(?:approve|accept)|memory/candidates/[^/]+/accept|"
        r"(?:agent|workflows)/runs/[^/]+/interrupts/[^/]+/resume|workflows/[^/]+/runs)",
        request.url.path,
    ))


def _error_code(status_code: int) -> str:
    return {
        400: "INVALID_REQUEST", 403: "FORBIDDEN", 404: "NOT_FOUND", 409: "CONFLICT",
        422: "VALIDATION_FAILED", 500: "INTERNAL_ERROR",
    }.get(status_code, "REQUEST_FAILED")


def _safe_error_message(value: object, status_code: int) -> str:
    message = str(value or "Request failed")
    # Exception strings are not a public contract: never echo paths, tracebacks, or likely secrets.
    if "\n" in message or "\r" in message or re.search(r"(?:[A-Za-z]:[\\/]|(?:^|\s)/(?:[^\s]+))", message):
        return {403: "Access denied", 404: "Resource not found"}.get(status_code, "Request failed")
    if re.search(r"(?:token|secret|password|api[_-]?key)\s*[=:]", message, re.I):
        return "Request failed"
    return message[:500]


def _http_error(exc: Exception, status_code: int | None = None) -> HTTPException:
    """Only conversion point from application exceptions to public HTTP errors."""
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        detail = exc.detail
    elif status_code is None and isinstance(exc, PermissionError):
        status_code, detail = 403, exc
    elif status_code is None and isinstance(exc, FileNotFoundError):
        status_code, detail = 404, exc
    else:
        status_code, detail = status_code or 500, exc
    if isinstance(detail, dict):
        code = detail.get("code")
        message = _safe_error_message(detail.get("message"), status_code)
        safe_details = detail.get("details") if isinstance(detail.get("details"), dict) else None
        return HTTPException(status_code=status_code, detail={
            "code": code if isinstance(code, str) and code else _error_code(status_code),
            "message": message, "details": safe_details,
        })
    return HTTPException(status_code=status_code, detail=_safe_error_message(detail, status_code))


def _etag(value: bytes) -> str:
    return f'"{hashlib.sha256(value).hexdigest()}"'


def _check_if_match(request: Request, current: bytes) -> None:
    expected = request.headers.get("If-Match")
    actual = _etag(current)
    # Optional until web-v3 sends preconditions; supplied preconditions are strict.
    if expected is not None and expected != actual:
        raise HTTPException(status_code=409, detail={
            "code": "STALE_DOCUMENT", "message": "Document changed; refresh and retry.",
            "details": {"current_version": actual},
        })


@app.middleware("http")
async def _csrf_guard(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or f"corr-{uuid.uuid4().hex}"
    request.state.correlation_id = correlation_id
    if request.method not in _CSRF_SAFE_METHODS:
        origin = request.headers.get("origin") or request.headers.get("referer")
        if origin and not any(origin.startswith(allowed) for allowed in config.ALLOWED_ORIGINS):
            return await _http_exception(request, _http_error(HTTPException(status_code=403, detail="cross-origin blocked")))
        if request.headers.get(config.HUB_CLIENT_HEADER) != config.HUB_CLIENT_VALUE:
            return await _http_exception(request, _http_error(HTTPException(status_code=403, detail="missing hub client header")))
    key = request.headers.get("Idempotency-Key")
    cache_key = (request.url.path, key) if key and _is_idempotent_command(request) else None
    if cache_key:
        with _IDEMPOTENCY_LOCK:
            cached = _IDEMPOTENCY_RESULTS.get(cache_key)
        if cached:
            status_code, body, content_type = cached
            response = Response(content=body, status_code=status_code, media_type=content_type)
            response.headers["Idempotency-Replayed"] = "true"
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Schema-Version"] = _SCHEMA_VERSION
            return response
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Schema-Version"] = _SCHEMA_VERSION
    if response.media_type == "text/event-stream":
        response.body_iterator = _correlated_sse(response.body_iterator, correlation_id)
    if cache_key and response.status_code < 500:
        response.body_iterator = _cache_response(response.body_iterator, cache_key, response.status_code, response.media_type or "application/json")
    # SPA assets change on every deploy; force revalidation so the browser
    # never runs stale app.js/workspace.js against a newer backend.
    if request.url.path == "/" or request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache"
    _LOGGER.info("api_request correlation_id=%s method=%s path=%s status=%s", correlation_id, request.method, request.url.path, response.status_code)
    return response


async def _cache_response(iterator, cache_key: tuple[str, str], status_code: int, content_type: str):
    body: list[bytes] = []
    async for chunk in iterator:
        value = chunk.encode("utf-8") if isinstance(chunk, str) else chunk
        body.append(value)
        yield value
    with _IDEMPOTENCY_LOCK:
        _IDEMPOTENCY_RESULTS.setdefault(cache_key, (status_code, b"".join(body), content_type))


async def _correlated_sse(iterator, correlation_id: str):
    async for chunk in iterator:
        text = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
        def decorate(match):
            try:
                data = json.loads(match.group(1))
            except (TypeError, ValueError):
                return match.group(0)
            if not isinstance(data, dict):
                return match.group(0)
            data.setdefault("schema_version", 1)
            data.setdefault("correlation_id", correlation_id)
            return f"data: {json.dumps(data, ensure_ascii=False)}"
        yield re.sub(r"data: (\{[^\n]*\})", decorate, text)


@app.exception_handler(HTTPException)
async def _http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    normalized = _http_error(exc)
    correlation_id = getattr(request.state, "correlation_id", f"corr-{uuid.uuid4().hex}")
    structured = normalized.detail if isinstance(normalized.detail, dict) else None
    detail = str(structured["message"] if structured else normalized.detail)
    error: dict[str, object] = {
        "code": structured["code"] if structured else _error_code(normalized.status_code),
        "message": detail, "correlation_id": correlation_id,
    }
    if structured and structured.get("details") is not None:
        error["details"] = structured["details"]
    return JSONResponse(
        status_code=normalized.status_code,
        content={"detail": detail, "schema_version": 1, "error": error},
        headers={"X-Correlation-ID": correlation_id, "X-Schema-Version": _SCHEMA_VERSION},
    )


@app.exception_handler(Exception)
async def _unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    return await _http_exception(request, _http_error(exc))


@app.exception_handler(RequestValidationError)
async def _validation_exception(request: Request, _exc: RequestValidationError) -> JSONResponse:
    return await _http_exception(request, _http_error(HTTPException(status_code=422, detail="Invalid request")))


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _chat_messages(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise HTTPException(status_code=400, detail="messages must be a list")
    messages: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail="messages must contain objects")
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"}:
            raise HTTPException(status_code=400, detail="message role must be user or assistant")
        if not isinstance(content, str):
            raise HTTPException(status_code=400, detail="message content must be a string")
        messages.append({"role": role, "content": content})
    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")
    return messages


CHAT_SKILL_MAX_CHARS = skill_library.SKILL_PROMPT_MAX_CHARS


def _chat_skills(value: object) -> tuple[list[str], bool]:
    if value is None:
        return [], False
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise HTTPException(status_code=400, detail="skills must be a list of skill names")

    requested = [item for item in value if item]
    known = skill_library.list_skill_names()
    unknown = next((name for name in requested if name not in known), None)
    if unknown is not None:
        raise HTTPException(status_code=400, detail=f"Unknown skill: {unknown}")

    contents, truncated, _missing = skill_library.load_skill_prompt_contents(requested)
    return contents, truncated


def _system_prompt_with_skills(system_prompt: str | None, contents: list[str]) -> str | None:
    return skill_library.system_prompt_with_skills(system_prompt, contents)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_V3_DIST / "index.html")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "root": str(config.ROOT),
        "runs_dir": str(config.RUNS_DIR),
        "port": config.PORT,
    }


@app.get("/api/chat/models")
def api_chat_models() -> dict[str, object]:
    return {
        "models": config.CHAT_MODELS,
        "default": config.CHAT_DEFAULT_MODEL,
        "catalog": config.CHAT_MODEL_CATALOG,
    }


@app.get("/api/providers")
def api_providers() -> list[dict[str, object]]:
    return list_providers()


@app.get("/api/model-classes")
def api_model_classes() -> dict[str, dict[str, object]]:
    return config.MODEL_CLASS_ROUTING


@app.post("/api/chat")
def api_chat(payload: dict[str, object]) -> StreamingResponse:
    agent_id = payload.get("agent_id")
    if agent_id is not None and not isinstance(agent_id, str):
        raise HTTPException(status_code=400, detail="agent_id must be a string")
    agent: dict[str, object] | None = None
    if agent_id:
        try:
            agent = runtime_agents.get_agent(agent_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_id}") from exc

    provider_id = (agent["provider"] if agent else payload.get("provider")) or "nvidia"
    if not isinstance(provider_id, str):
        raise HTTPException(status_code=400, detail="provider must be a string")
    messages = _chat_messages(payload.get("messages"))
    chat_id = payload.get("chat_id")
    if chat_id is not None and not isinstance(chat_id, str):
        raise HTTPException(status_code=400, detail="chat_id must be a string")
    if chat_id:
        try:
            file_context = chat_files.context(chat_id)
        except (FileNotFoundError, PermissionError) as exc:
            raise _http_error(exc) from exc
        if file_context:
            messages = [{"role": "system", "content": f"[Tệp đính kèm của chat]\n{file_context}"}, *messages]
    model = runtime_agents.resolve_provider(agent)["model"] if agent else payload.get("model")
    if agent and model is None:
        model = payload.get("model")
    if model is not None and not isinstance(model, str):
        raise HTTPException(status_code=400, detail="model must be a string")
    session_id = payload.get("session_id")
    if session_id is not None and not isinstance(session_id, str):
        raise HTTPException(status_code=400, detail="session_id must be a string")
    system_prompt = agent.get("system_prompt") if agent else None
    if system_prompt is not None and not isinstance(system_prompt, str):
        raise HTTPException(status_code=400, detail="agent system_prompt must be a string")
    skill_contents, skills_truncated = _chat_skills(payload.get("skills"))
    system_prompt = _system_prompt_with_skills(system_prompt, skill_contents)
    skill_notice = "Một phần nội dung skill đã bị cắt do giới hạn prompt." if skills_truncated else None

    tool_policy = (
        {
            "permission": agent["permission"],
            "allowed_tools": list(agent.get("allowed_tools") or []),
            "allowed_paths": list(agent.get("allowed_paths") or []),
        }
        if agent
        else None
    )
    request = execution.ExecutionRequest(
        correlation_id=session_id or "chat", provider_id=provider_id, model=model, messages=messages,
        session_id=session_id, system_prompt=system_prompt, tool_policy=tool_policy,
    )
    route = execution.gateway(request)
    if route.error is not None:
        raise HTTPException(status_code=400, detail=route.error.message)

    def events():
        try:
            for item in execution.execute(request, result=route):
                item_type = item.get("type")
                if item_type == "reasoning":
                    yield _sse("reasoning", {"text": item.get("text", "")})
                elif item_type == "delta":
                    yield _sse("delta", {"text": item.get("text", "")})
                elif item_type in {"tool_call", "tool_result"}:
                    yield _sse(item_type, {key: value for key, value in item.items() if key != "type"})
                elif item_type == "done":
                    done_payload: dict[str, object] = {
                        "usage": item.get("usage", {}),
                        "model": item.get("model") or model or provider_id,
                        "session_id": item.get("session_id"),
                    }
                    if skill_notice:
                        done_payload["skill_notice"] = skill_notice
                    yield _sse("done", done_payload)
                elif item_type == "error":
                    yield _sse("error", {"message": item.get("message", ""), "code": item.get("code")})
        except Exception:
            yield _sse("error", {"message": "Chat stream error", "code": None})

    return StreamingResponse(events(), media_type="text/event-stream")


# --- C1 agent profile routes ---
@app.get("/api/agents")
def api_agents() -> list[dict[str, object]]:
    return runtime_agents.list_agents()


@app.get("/api/risk-tiers")
def api_risk_tiers() -> list[str]:
    return list(risk.TIERS)


@app.post("/api/agents")
def api_agents_create_or_update(payload: dict[str, object], request: Request, response: Response) -> dict[str, object]:
    try:
        agent_id = payload.get("id")
        if isinstance(agent_id, str):
            try:
                current = runtime_agents.get_agent(agent_id)
                current_path = runtime_agents.AGENTS_DIR / f"{current['id']}.agent.yaml"
                _check_if_match(request, current_path.read_bytes())
            except FileNotFoundError:
                pass
        result = runtime_agents.create_or_update_agent(payload)
        response.headers["ETag"] = _etag((runtime_agents.AGENTS_DIR / f"{result['id']}.agent.yaml").read_bytes())
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/agents/{agent_id}")
def api_agents_delete(agent_id: str) -> dict[str, bool]:
    try:
        runtime_agents.delete_agent(agent_id)
    except FileNotFoundError as exc:
        raise _http_error(exc) from exc
    return {"ok": True}
# --- end C1 agent profile routes ---


@app.get("/api/agent/runs")
def api_agent_runs(agent_id: str | None = None) -> list[dict[str, object]]:
    rows = runtime_state.list_runs()
    if agent_id is not None:
        rows = [row for row in rows if (row.get("metadata") or {}).get("agent_id") == agent_id]
    return rows


@app.post("/api/agents/{agent_id}/test")
def api_agent_test(agent_id: str) -> dict[str, object]:
    try:
        agent = runtime_agents.get_agent(agent_id)
        started = time.monotonic(); output: list[str] = []; usage: dict[str, object] = {}
        request = execution.ExecutionRequest(
            correlation_id=f"agent-test-{agent_id}", provider_id=str(agent["provider"]), model=agent.get("model"),
            messages=[{"role": "user", "content": "Trả lời ngắn: kết nối agent hoạt động."}],
            tool_policy={"permission": agent["permission"], "allowed_tools": agent.get("allowed_tools", []), "allowed_paths": agent.get("allowed_paths", [])},
        )
        for item in execution.execute(request):
            if item.get("type") == "delta": output.append(str(item.get("text") or ""))
            elif item.get("type") == "done": usage = dict(item.get("usage") or {})
            elif item.get("type") == "error": raise RuntimeError(str(item.get("message") or "Provider error"))
        elapsed = time.monotonic() - started
        if elapsed > agent["budget"]["seconds"]: raise RuntimeError("budget_exceeded: agent seconds")
        return {"output": "".join(output), "elapsed_seconds": elapsed, "usage": usage}
    except FileNotFoundError as exc:
        raise _http_error(exc) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/agent/runs")
def api_create_agent_run(payload: dict[str, object]) -> StreamingResponse:
    try:
        references, inputs = run_inputs.resolve_inputs(payload.get("inputs"))
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    forwarded = dict(payload)
    if references:
        metadata = dict(forwarded.get("metadata") or {}) if isinstance(forwarded.get("metadata"), dict) else {}
        metadata.update({"inputs": inputs, "input_references": references})
        forwarded["metadata"] = metadata
    return StreamingResponse(runtime_pipeline.create_run_stream(forwarded), media_type="text/event-stream")


@app.get("/api/agent/runs/{run_id}")
def api_agent_run(run_id: str) -> dict[str, object]:
    try:
        return runtime_state.read_run(run_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/agent/runs/{run_id}/events")
def api_agent_run_events(run_id: str) -> list[dict[str, object]]:
    try:
        return runtime_events.read_events(run_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/agent/runs/{run_id}/interrupts/{interrupt_id}/resume")
def api_agent_run_interrupt_resume(run_id: str, interrupt_id: str, payload: dict[str, object]) -> StreamingResponse:
    try:
        runtime_state.read_run(run_id)
        runtime_interrupts.get_interrupt(run_id, interrupt_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return StreamingResponse(
        runtime_pipeline.resume_run_stream(run_id, interrupt_id, payload),
        media_type="text/event-stream",
    )


@app.get("/api/skills")
def api_skills() -> list[dict[str, object]]:
    return runtime_skills.list_skills()


@app.get("/api/search")
def api_search(q: str = "") -> list[dict[str, str]]:
    return search.search(q)


@app.get("/api/skills/names")
def api_skill_names() -> list[str]:
    return sorted(skill_library.list_skill_names())


@app.get("/api/skills/{skill_id}/usage")
def api_skill_usage(skill_id: str) -> dict[str, object]:
    try:
        return runtime_skills.skill_usage(skill_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/skills/{skill_id}")
def api_skill(skill_id: str) -> dict[str, object]:
    try:
        return runtime_skills.get_skill(skill_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/memory")
def api_memory() -> list[dict[str, object]]:
    return runtime_memory.list_memory()


@app.get("/api/settings/retention")
def api_retention_settings() -> dict[str, int]:
    return retention.settings()


@app.put("/api/settings/retention")
def api_retention_update(payload: dict[str, object]) -> dict[str, int]:
    try:
        result = retention.update(payload.get("days"))
        retention.sweep()
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/memory/candidates")
def api_memory_candidates() -> list[dict[str, object]]:
    return runtime_memory.list_candidates()


@app.post("/api/memory/candidates/{candidate_id}/accept")
def api_memory_candidate_accept(candidate_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    try:
        return runtime_memory.accept_candidate(candidate_id, payload if isinstance(payload, dict) else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/memory/candidates/{candidate_id}/reject")
def api_memory_candidate_reject(candidate_id: str) -> dict[str, object]:
    try:
        return runtime_memory.reject_candidate(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/memory/{memory_id}/revoke")
def api_memory_revoke(memory_id: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        return runtime_memory.revoke_memory(memory_id, str(payload.get("revoked_by") or ""), str(payload.get("reason") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/guardrails/decisions")
def api_guardrail_decisions() -> list[dict[str, object]]:
    return runtime_policy.list_decisions()


@app.post("/api/guardrails/decisions/command")
def api_guardrail_command_decision(payload: dict[str, object]) -> dict[str, object]:
    subject_id = str(payload.get("subject_id") or "manual")
    command = payload.get("command")
    return runtime_policy.decide_command(subject_id, command)


@app.get("/api/runs")
def api_runs() -> list[dict[str, object]]:
    return runs.list_runs()


@app.get("/api/jobs")
def api_jobs() -> list[dict[str, object]]:
    return gitjobs.list_jobs()


@app.post("/api/jobs")
def api_create_job(payload: dict[str, object]) -> dict[str, object]:
    brief = payload.get("brief")
    agent = payload.get("agent") or "codex"
    allow_override = bool(payload.get("allow_override"))
    if not isinstance(brief, str) or not brief.strip():
        raise HTTPException(status_code=400, detail="brief is required")
    if not isinstance(agent, str):
        raise HTTPException(status_code=400, detail="agent must be a string")
    if agent not in config.JOB_ALLOW_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported agent: {agent}")
    try:
        return gitjobs.create_job(brief, agent, allow_override=allow_override)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (OSError, PermissionError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str) -> dict[str, object]:
    try:
        job = dict(gitjobs.get_job(job_id))
        patch = gitjobs.diff(job_id)
        if patch:
            job["diff"] = patch
        return job
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/jobs/{job_id}/approve")
def api_job_approve(job_id: str) -> dict[str, object]:
    try:
        return gitjobs.approve(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except (OSError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/jobs/{job_id}/stream")
def api_job_stream(job_id: str) -> StreamingResponse:
    try:
        gitjobs.get_job(job_id)
        return StreamingResponse(gitjobs.stream_events(job_id), media_type="text/event-stream")
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/jobs/{job_id}/accept")
def api_job_accept(job_id: str) -> dict[str, object]:
    try:
        return gitjobs.accept(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/jobs/{job_id}/rollback")
def api_job_rollback(job_id: str) -> dict[str, object]:
    try:
        return gitjobs.rollback(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/jobs/{job_id}/reject")
def api_job_reject(job_id: str) -> dict[str, object]:
    try:
        return gitjobs.reject(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError, RuntimeError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/jobs/{job_id}/diff")
def api_job_diff(job_id: str) -> PlainTextResponse:
    try:
        return PlainTextResponse(gitjobs.diff(job_id), media_type="text/plain; charset=utf-8")
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/runs/trigger")
def api_trigger(payload: dict[str, object]) -> dict[str, str]:
    suite = payload.get("suite")
    check = payload.get("check")
    if not isinstance(suite, str) or not suite:
        raise HTTPException(status_code=400, detail="suite is required")
    if check is not None and not isinstance(check, str):
        raise HTTPException(status_code=400, detail="check must be a string")
    try:
        stream_id = trigger.start_run(suite, check)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise _http_error(exc) from exc
    return {"stream_id": stream_id}


@app.get("/api/runs/stream/{stream_id}")
def api_run_stream(stream_id: str) -> StreamingResponse:
    try:
        return StreamingResponse(trigger.stream_events(stream_id), media_type="text/event-stream")
    except FileNotFoundError as exc:
        raise _http_error(exc) from exc


@app.get("/api/runs/budget/{stream_id}")
def api_run_budget(stream_id: str) -> dict[str, object]:
    try:
        return trigger.budget_status(stream_id)
    except FileNotFoundError as exc:
        raise _http_error(exc) from exc


@app.get("/api/runs/compare")
def api_run_compare(a: str = Query(..., min_length=1), b: str = Query(..., min_length=1)) -> dict[str, object]:
    try:
        return runs.compare_runs(a, b)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/runs/{run_id}")
def api_run(run_id: str) -> dict[str, object]:
    try:
        return runs.get_run(run_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/runs/{run_id}/artifact")
def api_run_artifact(run_id: str, rel: str = Query(..., min_length=1)) -> PlainTextResponse:
    try:
        return PlainTextResponse(runs.read_artifact(run_id, rel), media_type="text/plain; charset=utf-8")
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/suites")
def api_suites() -> list[dict[str, object]]:
    return suites.list_suites()


@app.get("/api/suites/{suite_id}")
def api_suite(suite_id: str) -> dict[str, object]:
    try:
        return suites.get_suite(suite_id)
    except FileNotFoundError as exc:
        raise _http_error(exc) from exc


@app.get("/api/integrity")
def api_integrity() -> dict[str, object]:
    results = integrity.verify_suites()
    return {
        "ok": all(bool(item.get("ok")) for item in results),
        "suites": results,
        "count": len(results),
    }


@app.get("/api/governance")
def api_governance() -> dict[str, object]:
    return governance.status()


@app.get("/api/usage")
def api_usage(
    source: str | None = None,
    model: str | None = None,
    since: str | None = None,
) -> list[dict[str, object]]:
    try:
        return usage.collect_usage({"source": source, "model": model, "since": since})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/usage/rollup")
def api_usage_rollup(
    source: str | None = None,
    model: str | None = None,
    since: str | None = None,
) -> dict[str, object]:
    try:
        events = usage.collect_usage({"source": source, "model": model, "since": since})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return usage.rollup(events)


@app.get("/api/tools")
@app.get("/api/tools/usage")
def api_tools(
    source: str | None = None,
    model: str | None = None,
    since: str | None = None,
) -> dict[str, object]:
    try:
        events, _warnings = behavior.collect_tool_events()
        filtered = behavior.filter_tool_events(events, {"source": source, "model": model, "since": since})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return behavior.tool_rollup(filtered)


@app.get("/api/inspect/logs")
def api_inspect_logs() -> list[dict[str, object]]:
    return inspect_evals.list_logs()


@app.get("/api/inspect/mep")
def api_inspect_mep() -> dict[str, object]:
    try:
        return inspect_evals.latest_mep()
    except FileNotFoundError as exc:
        raise _http_error(exc) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/usage/cockpit")
def api_usage_cockpit() -> dict[str, object]:
    stats = usage.cockpit_stats()
    stats["providers_online"] = [
        {"id": provider["id"], "available": provider["available"]}
        for provider in list_providers()
    ]
    return stats


@app.get("/api/skill-library")
def api_skill_library() -> list[dict[str, object]]:
    return skill_library.list_skills()


@app.post("/api/skill-library")
def api_skill_library_create(payload: dict[str, object]) -> dict[str, object]:
    try: return skill_library.create_skill(payload)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/skill-library/{skill_id:path}")
def api_skill_library_update(skill_id: str, payload: dict[str, object]) -> dict[str, object]:
    try: return skill_library.update_skill(skill_id, payload)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc


@app.delete("/api/skill-library/{skill_id:path}")
def api_skill_library_delete(skill_id: str) -> dict[str, bool]:
    try: skill_library.delete_skill(skill_id)
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc
    return {"ok": True}


@app.get("/api/skill-library/drift")
def api_skill_library_drift() -> list[dict[str, object]]:
    return skill_library.drift()


@app.get("/api/skill-library/deploy-log")
def api_skill_library_deploy_log() -> list[dict[str, object]]:
    return skill_library.deploy_log()


@app.get("/api/skill-library/{skill_id:path}")
def api_skill_library_detail(skill_id: str) -> dict[str, object]:
    try:
        return skill_library.get_skill(skill_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/skill-library/{skill_id:path}/deploy")
def api_skill_library_deploy(skill_id: str, payload: dict[str, object]) -> dict[str, object]:
    target = payload.get("target")
    if not isinstance(target, str) or not target:
        raise HTTPException(status_code=400, detail="target is required")
    try:
        return skill_library.deploy(skill_id, target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/hooks")
def api_hooks() -> list[dict[str, object]]: return hooks.list_hooks()


@app.get("/api/hooks/events")
def api_hook_events() -> list[str]: return hooks.events()


@app.post("/api/hooks")
def api_hooks_create(payload: dict[str, object]) -> dict[str, object]:
    try: return hooks.create(payload)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/hooks/{hook_id}")
def api_hooks_update(hook_id: str, payload: dict[str, object]) -> dict[str, object]:
    try: return hooks.update(hook_id, payload)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc: raise _http_error(exc) from exc


@app.delete("/api/hooks/{hook_id}")
def api_hooks_delete(hook_id: str) -> dict[str, bool]:
    try: hooks.delete(hook_id)
    except FileNotFoundError as exc: raise _http_error(exc) from exc
    return {"ok": True}


@app.get("/api/hooks/{hook_id}/log")
def api_hook_log(hook_id: str) -> list[dict[str, object]]: return hooks.log(hook_id)


@app.get("/api/runs/{run_id}/files")
def api_run_files(run_id: str) -> list[dict[str, object]]:
    try: return runtime_files.list_files(run_id)
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc


@app.post("/api/runs/{run_id}/files")
async def api_run_files_upload(run_id: str, file: UploadFile = File(...)) -> dict[str, object]:
    try: return runtime_files.upload(run_id, file.filename or "", await file.read())
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc


@app.get("/api/runs/{run_id}/files/{name:path}")
def api_run_file_download(run_id: str, name: str) -> FileResponse:
    try: return FileResponse(runtime_files.download(run_id, name), filename=Path(name).name)
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc


@app.delete("/api/runs/{run_id}/files/{name:path}")
def api_run_file_delete(run_id: str, name: str) -> dict[str, bool]:
    try: runtime_files.delete(run_id, name)
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc
    return {"ok": True}


@app.get("/api/chats/{chat_id}/files")
def api_chat_files(chat_id: str) -> list[dict[str, object]]:
    try: return chat_files.list_files(chat_id)
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc


@app.get("/api/chat-files")
def api_all_chat_files() -> list[dict[str, object]]:
    try: return chat_files.list_all_files()
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc


@app.post("/api/chats/{chat_id}/files")
async def api_chat_files_upload(chat_id: str, file: UploadFile = File(...)) -> dict[str, object]:
    try: return chat_files.upload(chat_id, file.filename or "", await file.read())
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc


@app.get("/api/chats/{chat_id}/files/{name:path}")
def api_chat_file_download(chat_id: str, name: str) -> FileResponse:
    try: return FileResponse(chat_files.download(chat_id, name), filename=Path(name).name)
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc


@app.delete("/api/chats/{chat_id}/files/{name:path}")
def api_chat_file_delete(chat_id: str, name: str) -> dict[str, bool]:
    try: chat_files.delete(chat_id, name)
    except (FileNotFoundError, PermissionError) as exc: raise _http_error(exc) from exc
    return {"ok": True}


# --- C2a workflow routes ---
@app.get("/api/workflows")
def api_workflows() -> list[dict[str, object]]:
    return workflow.list_workflows()


@app.post("/api/workflows", status_code=201)
def api_workflow_create(payload: dict[str, object], response: Response) -> dict[str, object]:
    workflow_id = payload.get("id")
    yaml_text = payload.get("yaml_text")
    agent = payload.get("agent")
    if not isinstance(workflow_id, str):
        raise HTTPException(status_code=400, detail="id must be a string")
    if yaml_text is not None and not isinstance(yaml_text, str):
        raise HTTPException(status_code=400, detail="yaml_text must be a string")
    if agent is not None and not isinstance(agent, str):
        raise HTTPException(status_code=400, detail="agent must be a string")
    try:
        result = workflow.create_workflow(workflow_id, yaml_text, agent=agent)
        response.headers["ETag"] = _etag(workflow.workflow_path(workflow_id).read_bytes())
        return result
    except workflow.WorkflowConflictError as exc:
        raise _http_error(exc, 409) from exc
    except (PermissionError, ValueError) as exc:
        raise _http_error(exc, 400) from exc


@app.get("/api/workflows/{workflow_id}/layout")
def api_workflow_layout(workflow_id: str, response: Response) -> dict[str, object]:
    try:
        response.headers["ETag"] = _etag(workflow.workflow_layout_path(workflow_id).read_bytes()) if workflow.workflow_layout_path(workflow_id).exists() else '"empty"'
        return {"nodes": workflow.read_layout(workflow_id)}
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/workflows/{workflow_id}/layout")
def api_workflow_layout_save(workflow_id: str, payload: dict[str, object], request: Request, response: Response) -> dict[str, object]:
    try:
        path = workflow.workflow_layout_path(workflow_id)
        _check_if_match(request, path.read_bytes() if path.exists() else b"")
        result = {"nodes": workflow.save_layout(workflow_id, payload)}
        response.headers["ETag"] = _etag(path.read_bytes())
        return result
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/workflows/{workflow_id}/model")
def api_workflow_model_save(workflow_id: str, payload: dict[str, object], request: Request, response: Response) -> dict[str, object]:
    model = payload.get("model")
    if not isinstance(model, dict):
        raise HTTPException(status_code=400, detail="model must be a mapping")
    try:
        _check_if_match(request, workflow.workflow_path(workflow_id).read_bytes())
        yaml_text = workflow.model_yaml_text(workflow_id, model)
        result = workflow.save_workflow(workflow_id, yaml_text)
        response.headers["ETag"] = _etag(workflow.workflow_path(workflow_id).read_bytes())
        return result
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/workflows/{workflow_id}/source")
def api_workflow_source(workflow_id: str, response: Response) -> dict[str, str]:
    try:
        path = workflow.workflow_path(workflow_id)
        response.headers["ETag"] = _etag(path.read_bytes())
        return {"id": workflow_id, "yaml_text": path.read_text(encoding="utf-8")}
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc


@app.post("/api/workflows/validate")
def api_workflow_validate(payload: dict[str, object]) -> dict[str, object]:
    yaml_text = payload.get("yaml_text")
    workflow_id = payload.get("id")
    if isinstance(yaml_text, str):
        source = yaml_text
    elif isinstance(workflow_id, str):
        try:
            source = workflow.workflow_path(workflow_id).read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError) as exc:
            raise _http_error(exc) from exc
    else:
        raise HTTPException(status_code=400, detail="yaml_text or id is required")

    try:
        data = workflow.parse_workflow(source)
    except ValueError as exc:
        return {"ok": False, "errors": [str(exc)], "ir": None}
    errors = workflow.validate_workflow(data)
    return {"ok": not errors, "errors": errors, "ir": workflow.build_ir(data) if not errors else None}


@app.put("/api/workflows/{workflow_id}")
def api_workflow_save(workflow_id: str, payload: dict[str, object], request: Request, response: Response) -> dict[str, object]:
    yaml_text = payload.get("yaml_text")
    if not isinstance(yaml_text, str):
        raise HTTPException(status_code=400, detail="yaml_text must be a string")
    try:
        _check_if_match(request, workflow.workflow_path(workflow_id).read_bytes())
        result = workflow.save_workflow(workflow_id, yaml_text)
        response.headers["ETag"] = _etag(workflow.workflow_path(workflow_id).read_bytes())
        return result
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/workflows/{workflow_id}")
def api_workflow_delete(workflow_id: str) -> dict[str, bool]:
    try:
        workflow.delete_workflow(workflow_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return {"ok": True}


# --- end C2a workflow routes ---


# --- C2b workflow run routes ---
@app.post("/api/workflows/{workflow_id}/runs", response_model=None)
def api_workflow_run(workflow_id: str, payload: dict[str, object]):
    objective = payload.get("objective")
    if not isinstance(objective, str):
        raise HTTPException(status_code=400, detail="objective must be a string")
    try:
        references, inputs = run_inputs.resolve_inputs(payload.get("inputs"))
        source = workflow.workflow_path(workflow_id).read_text(encoding="utf-8")
        errors = workflow.validate_workflow(workflow.parse_workflow(source))
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise _http_error(exc, 400) from exc
    if errors:
        raise _http_error(ValueError("Workflow validation failed"), 422)
    return StreamingResponse(workflow_exec.create_workflow_run_stream(workflow_id, objective, inputs, references), media_type="text/event-stream")


@app.get("/api/workflows/runs/{run_id}/artifacts")
def api_workflow_run_artifacts(run_id: str) -> dict[str, object]:
    try:
        return {"artifacts": runtime_artifacts.list_artifacts(run_id)}
    except (FileNotFoundError, PermissionError) as exc:
        raise HTTPException(status_code=404) from exc


@app.get("/api/workflows/runs/{run_id}/artifacts/{name}")
def api_workflow_run_artifact(run_id: str, name: str) -> dict[str, str]:
    try:
        return {"name": name, "text": runtime_artifacts.read_artifact(run_id, name)}
    except (FileNotFoundError, PermissionError) as exc:
        raise HTTPException(status_code=404) from exc


@app.post("/api/workflows/runs/{run_id}/interrupts/{interrupt_id}/resume")
def api_workflow_run_interrupt_resume(run_id: str, interrupt_id: str, payload: dict[str, object]) -> StreamingResponse:
    try:
        runtime_state.read_run(run_id)
        runtime_interrupts.get_interrupt(run_id, interrupt_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return StreamingResponse(
        workflow_exec.resume_workflow_run_stream(run_id, interrupt_id, payload),
        media_type="text/event-stream",
    )
# --- end C2b workflow run routes ---


@app.get("/api/artifacts")
def api_artifacts() -> dict[str, object]:
    try:
        return {"artifacts": runtime_artifacts.list_library_artifacts()}
    except (PermissionError, ValueError) as exc:
        raise _http_error(exc) from exc


@app.get("/api/artifacts/{artifact_id}")
def api_artifact(artifact_id: str) -> dict[str, object]:
    try:
        return runtime_artifacts.read_library_artifact(artifact_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise HTTPException(status_code=404) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/artifacts")
def api_artifact_save(payload: dict[str, object]) -> dict[str, object]:
    artifact_id = payload.get("id")
    title = payload.get("title")
    content = payload.get("content")
    source = payload.get("source")
    if artifact_id is not None and not isinstance(artifact_id, str):
        raise HTTPException(status_code=400, detail="id must be a string")
    if title is not None and not isinstance(title, str):
        raise HTTPException(status_code=400, detail="title must be a string")
    if not isinstance(content, str):
        raise HTTPException(status_code=400, detail="content must be a string")
    if not isinstance(source, str):
        raise HTTPException(status_code=400, detail="source must be a string")
    try:
        return runtime_artifacts.save_library_artifact(artifact_id, title, content, source)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except (PermissionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _require_artifact(artifact_id: str) -> None:
    runtime_artifacts.read_library_artifact(artifact_id)


@app.get("/api/artifacts/{artifact_id}/comments")
def api_artifact_comments(artifact_id: str) -> dict[str, object]:
    try:
        _require_artifact(artifact_id)
        return {"comments": artifact_comments.list_comments(artifact_id)}
    except FileNotFoundError as exc: raise HTTPException(status_code=404) from exc
    except (PermissionError, ValueError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/artifacts/{artifact_id}/comments")
def api_artifact_comment_create(artifact_id: str, payload: dict[str, object]) -> dict[str, object]:
    quoted_text, author, body = payload.get("quoted_text"), payload.get("author"), payload.get("body")
    if not all(isinstance(value, str) for value in (quoted_text, author, body)):
        raise HTTPException(status_code=400, detail="quoted_text, author and body must be strings")
    try:
        _require_artifact(artifact_id)
        return artifact_comments.create(artifact_id, quoted_text, author, body)
    except FileNotFoundError as exc: raise HTTPException(status_code=404) from exc
    except (PermissionError, ValueError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/artifacts/{artifact_id}/comments/{comment_id}")
def api_artifact_comment_resolve(artifact_id: str, comment_id: str, payload: dict[str, object]) -> dict[str, object]:
    resolved = payload.get("resolved")
    if not isinstance(resolved, bool): raise HTTPException(status_code=400, detail="resolved must be a boolean")
    try:
        _require_artifact(artifact_id)
        return artifact_comments.resolve(artifact_id, comment_id, resolved)
    except FileNotFoundError as exc: raise HTTPException(status_code=404) from exc
    except (PermissionError, ValueError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/artifacts/{artifact_id}/comments/{comment_id}")
def api_artifact_comment_delete(artifact_id: str, comment_id: str) -> dict[str, bool]:
    try:
        _require_artifact(artifact_id)
        artifact_comments.delete(artifact_id, comment_id)
    except FileNotFoundError as exc: raise HTTPException(status_code=404) from exc
    except (PermissionError, ValueError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.api_route("/api/vgov/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def api_vgov_proxy(path: str, request: Request) -> Response:
    """Keep Version Governance behind the Hub control-plane boundary.

    vgov-api mounts every functional router under /api/vgov, so the prefix must be preserved.
    Forwarding to /{path} only ever resolved /health and 404'd everything else.
    """
    target = f"{config.VGOV_BASE_URL.rstrip('/')}/api/vgov/{path}"
    headers = {name: value for name, value in request.headers.items()
               if name.lower() in {"x-actor", "content-type"}}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            upstream = await client.request(
                request.method, target, params=request.query_params,
                content=await request.body(), headers=headers,
            )
    except (httpx.ConnectError, httpx.TimeoutException):
        return JSONResponse(
            status_code=502,
            content={"error": {"code": "RUNTIME_UNAVAILABLE", "message": "Version Governance API is unavailable"}},
        )
    content_type = upstream.headers.get("content-type")
    return Response(content=upstream.content, status_code=upstream.status_code, media_type=content_type)


@app.get("/api/board")
def api_board() -> dict[str, object]:
    return board.task_board()


@app.get("/api/sessions")
def api_sessions() -> list[dict[str, object]]:
    return replay.list_sessions()


@app.get("/api/sessions/loops")
def api_session_loops() -> list[dict[str, object]]:
    return behavior.session_loops()


@app.get("/api/sessions/entropy")
def api_session_entropy() -> list[dict[str, object]]:
    return behavior.session_entropy()


@app.get("/api/sessions/{session}/replay")
def api_session_replay(session: str) -> dict[str, object]:
    try:
        return replay.session_replay(session)
    except FileNotFoundError as exc:
        raise _http_error(exc) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=config.PORT)
