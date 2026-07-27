from __future__ import annotations

import json
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path


HUB_DIR = Path(__file__).resolve().parent
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import config
from services import (
    behavior,
    board,
    chat,
    gitjobs,
    governance,
    inspect_evals,
    integrity,
    replay,
    risk,
    runs,
    runtime_agents,
    runtime_artifacts,
    runtime_events,
    runtime_interrupts,
    runtime_memory,
    runtime_pipeline,
    runtime_policy,
    runtime_skills,
    runtime_state,
    skill_library,
    suites,
    trigger,
    usage,
    workflow,
    workflow_exec,
)
from services.providers import get_provider, list_providers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=usage.warm, name="usage-warm", daemon=True).start()
    threading.Thread(target=behavior.warm, name="behavior-warm", daemon=True).start()
    try:
        gitjobs.reconcile_orphans()
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


@app.middleware("http")
async def _csrf_guard(request: Request, call_next):
    if request.method not in _CSRF_SAFE_METHODS:
        origin = request.headers.get("origin") or request.headers.get("referer")
        if origin and not any(origin.startswith(allowed) for allowed in config.ALLOWED_ORIGINS):
            return JSONResponse(status_code=403, content={"detail": "cross-origin blocked"})
        if request.headers.get(config.HUB_CLIENT_HEADER) != config.HUB_CLIENT_VALUE:
            return JSONResponse(status_code=403, content={"detail": "missing hub client header"})
    response = await call_next(request)
    # SPA assets change on every deploy; force revalidation so the browser
    # never runs stale app.js/workspace.js against a newer backend.
    if request.url.path == "/" or request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache"
    return response


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


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


CHAT_SKILL_MAX_CHARS = 12000


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

    contents: list[str] = []
    used = 0
    truncated = False
    for name in requested:
        content = skill_library.read_skill_content(name)
        remaining = CHAT_SKILL_MAX_CHARS - used
        if remaining <= 0:
            truncated = True
            break
        if len(content) > remaining:
            contents.append(content[:remaining])
            truncated = True
            break
        contents.append(content)
        used += len(content)
    return contents, truncated


def _system_prompt_with_skills(system_prompt: str | None, contents: list[str]) -> str | None:
    if not contents:
        return system_prompt
    skills_prompt = "\n\n[Activated skills]\n" + "\n\n---\n\n".join(contents)
    return f"{system_prompt}{skills_prompt}" if system_prompt else skills_prompt.removeprefix("\n\n")


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

    provider_id = (runtime_agents.resolve_provider(agent)["provider"] if agent else payload.get("provider")) or "nvidia"
    if not isinstance(provider_id, str):
        raise HTTPException(status_code=400, detail="provider must be a string")
    try:
        provider = get_provider(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    messages = _chat_messages(payload.get("messages"))
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

    def events():
        try:
            stream_kwargs: dict[str, object] = {"session_id": session_id, "model": model}
            if system_prompt:
                stream_kwargs["system_prompt"] = system_prompt
            for item in provider.stream_chat(messages, **stream_kwargs):
                item_type = item.get("type")
                if item_type == "reasoning":
                    yield _sse("reasoning", {"text": item.get("text", "")})
                elif item_type == "delta":
                    yield _sse("delta", {"text": item.get("text", "")})
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
def api_agents_create_or_update(payload: dict[str, object]) -> dict[str, object]:
    try:
        return runtime_agents.create_or_update_agent(payload)
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
def api_agent_runs() -> list[dict[str, object]]:
    return runtime_state.list_runs()


@app.post("/api/agent/runs")
def api_create_agent_run(payload: dict[str, object]) -> StreamingResponse:
    return StreamingResponse(runtime_pipeline.create_run_stream(payload), media_type="text/event-stream")


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


@app.get("/api/memory/candidates")
def api_memory_candidates() -> list[dict[str, object]]:
    return runtime_memory.list_candidates()


@app.post("/api/memory/candidates/{candidate_id}/accept")
def api_memory_candidate_accept(candidate_id: str) -> dict[str, object]:
    try:
        return runtime_memory.accept_candidate(candidate_id)
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


# --- C2a workflow routes ---
@app.get("/api/workflows")
def api_workflows() -> list[dict[str, object]]:
    return workflow.list_workflows()


@app.get("/api/workflows/{workflow_id}/layout")
def api_workflow_layout(workflow_id: str) -> dict[str, object]:
    try:
        return {"nodes": workflow.read_layout(workflow_id)}
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/workflows/{workflow_id}/layout")
def api_workflow_layout_save(workflow_id: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        return {"nodes": workflow.save_layout(workflow_id, payload)}
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/workflows/{workflow_id}/model")
def api_workflow_model_save(workflow_id: str, payload: dict[str, object]) -> dict[str, object]:
    model = payload.get("model")
    if not isinstance(model, dict):
        raise HTTPException(status_code=400, detail="model must be a mapping")
    try:
        yaml_text = workflow.model_yaml_text(workflow_id, model)
        return workflow.save_workflow(workflow_id, yaml_text)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/workflows/{workflow_id}/source")
def api_workflow_source(workflow_id: str) -> dict[str, str]:
    try:
        path = workflow.workflow_path(workflow_id)
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
def api_workflow_save(workflow_id: str, payload: dict[str, object]) -> dict[str, object]:
    yaml_text = payload.get("yaml_text")
    if not isinstance(yaml_text, str):
        raise HTTPException(status_code=400, detail="yaml_text must be a string")
    try:
        return workflow.save_workflow(workflow_id, yaml_text)
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- end C2a workflow routes ---


# --- C2b workflow run routes ---
@app.post("/api/workflows/{workflow_id}/runs", response_model=None)
def api_workflow_run(workflow_id: str, payload: dict[str, object]):
    objective = payload.get("objective")
    if not isinstance(objective, str):
        raise HTTPException(status_code=400, detail="objective must be a string")
    try:
        source = workflow.workflow_path(workflow_id).read_text(encoding="utf-8")
        errors = workflow.validate_workflow(workflow.parse_workflow(source))
    except (FileNotFoundError, PermissionError) as exc:
        raise _http_error(exc) from exc
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"errors": [str(exc)]})
    if errors:
        return JSONResponse(status_code=400, content={"errors": errors})
    return StreamingResponse(workflow_exec.create_workflow_run_stream(workflow_id, objective), media_type="text/event-stream")


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
