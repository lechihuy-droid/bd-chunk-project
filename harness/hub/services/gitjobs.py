from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

import config
from services import governance, inform, integrity, risk, verify
from services.boundary import resolve_in_root


JOB_ID_RE = re.compile(r"^j-[0-9a-z-]+$")
JOB_ARTIFACT_SOURCE = "codex-agent"


@dataclass
class JobStream:
    job_id: str
    process: subprocess.Popen[str]
    log_path: Path
    started_monotonic: float
    events: "queue.Queue[dict[str, Any]]" = field(default_factory=queue.Queue)
    exit_code: int | None = None
    timed_out: bool = False
    log_lock: threading.Lock = field(default_factory=threading.Lock)


_STREAMS: dict[str, JobStream] = {}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _run_git(cwd: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        check=False,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result


def _git_output(cwd: Path, args: list[str]) -> str:
    return _run_git(cwd, args).stdout.strip()


def _validate_agent(agent: str) -> None:
    if agent not in config.JOB_ALLOW_AGENTS:
        raise ValueError(f"Unsupported agent: {agent}")


def _validate_job_id(job_id: str) -> None:
    if not JOB_ID_RE.fullmatch(job_id or ""):
        raise FileNotFoundError(f"Job not found: {job_id}")


def _job_dir(job_id: str, must_exist: bool = True) -> Path:
    _validate_job_id(job_id)
    path = resolve_in_root(job_id, config.JOBS_DIR)
    if must_exist and not (path / "job.json").is_file():
        raise FileNotFoundError(f"Job not found: {job_id}")
    return path


def _job_path(job_id: str) -> Path:
    return _job_dir(job_id) / "job.json"


def _read_job(job_id: str) -> dict[str, Any]:
    with _job_path(job_id).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid job record: {job_id}")
    return data


def _write_job(job: dict[str, Any]) -> None:
    job_id = str(job.get("id") or "")
    path = _job_dir(job_id, must_exist=False) / "job.json"
    path.write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _new_job_id() -> str:
    return f"j-{datetime.now(UTC):%Y%m%d}-{uuid.uuid4().hex[:10]}"


def _per_job_branch(job_id: str) -> str:
    _validate_job_id(job_id)
    return f"opus-job/{job_id}"


def _worktree_path(job: dict[str, Any]) -> Path:
    worktree = job.get("worktree")
    if not isinstance(worktree, str) or not worktree:
        raise ValueError("Job worktree is missing")
    path = Path(worktree).resolve()
    expected = (_job_dir(str(job["id"])) / "wt").resolve()
    if path != expected:
        raise PermissionError(f"Unexpected job worktree path: {path}")
    return path


def _job_log_path(job_id: str) -> Path:
    return resolve_in_root("stdout.log", _job_dir(job_id))


def _job_diff_path(job_id: str) -> Path:
    return resolve_in_root("diff.patch", _job_dir(job_id))


def _spawn_agent(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        shell=False,
        env=env,
    )


def _agent_command(job: dict[str, Any]) -> list[str]:
    agent = job.get("agent")
    if agent != "codex":
        raise ValueError(f"Unsupported agent: {agent}")
    return [
        config.JOB_AGENT_CMD,
        "exec",
        "--cd",
        str(_worktree_path(job)),
        "-s",
        "workspace-write",
        str(job.get("brief") or ""),
    ]


def verify_brief(job: dict[str, Any]) -> bool:
    return integrity.verify_text(str(job.get("brief") or ""), job.get("brief_sig"))


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    data = dict(job)
    data.setdefault("max_tier", "read_only")
    data.setdefault("run_count", 0)
    data.setdefault("allow_override", False)
    data.setdefault("inform_findings", [])
    data.setdefault("l2_decision", None)
    data.setdefault("l2_reasons", [])
    data.setdefault("l2_warnings", [])
    data.setdefault("approval_block_reasons", [])
    data.setdefault("flagged", False)
    data.setdefault("flag_reasons", [])
    data["run_cap"] = int(config.JOB_MAX_RUNS)
    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    provenance.setdefault("source", JOB_ARTIFACT_SOURCE)
    data["provenance"] = provenance
    data["brief_ok"] = verify_brief(data)
    return data


def _budget_payload(stream: JobStream) -> dict[str, Any]:
    elapsed = max(0, int(time.monotonic() - stream.started_monotonic))
    cap = int(config.JOB_TIME_CAP_SECONDS)
    return {
        "stream_id": stream.job_id,
        "job_id": stream.job_id,
        "kind": "time",
        "steps_done": min(elapsed, cap),
        "steps_total": cap,
        "step_cap": cap,
        "warn": elapsed > int(cap * 0.8),
        "tokens_used": None,
        "token_cap": None,
        "elapsed_seconds": elapsed,
        "time_cap_seconds": cap,
    }


def _append_log(stream: JobStream, text: str) -> None:
    with stream.log_lock:
        with stream.log_path.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(text + "\n")


def _emit_line(stream: JobStream, line: str) -> None:
    text = line.rstrip("\r\n")
    _append_log(stream, text)
    stream.events.put({"type": "line", "data": text})


def _read_pipe(stream: JobStream, pipe: Any) -> None:
    if pipe is None:
        return
    try:
        for line in pipe:
            _emit_line(stream, str(line))
    finally:
        close = getattr(pipe, "close", None)
        if callable(close):
            close()


def _stage_intent_to_add(worktree: Path) -> None:
    _run_git(worktree, ["add", "-N", "--", "."], check=False)


def _compute_diffstat(worktree: Path, base_sha: str) -> dict[str, int]:
    _stage_intent_to_add(worktree)
    result = _run_git(worktree, ["diff", "--numstat", base_sha], check=False)
    files = 0
    insertions = 0
    deletions = 0
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        files += 1
        if parts[0].isdigit():
            insertions += int(parts[0])
        if parts[1].isdigit():
            deletions += int(parts[1])
    return {"files": files, "insertions": insertions, "deletions": deletions}


def _classify_diff_files(worktree: Path, base_sha: str) -> list[str]:
    result = _run_git(worktree, ["diff", "--name-status", base_sha], check=False)
    tiers: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0].upper()
        if status.startswith("D"):
            tiers.append("destructive")
        else:
            tiers.append("write")
    return tiers


def _classify_diff_commands(diff_text: str) -> list[str]:
    tiers: list[str] = []
    for line in diff_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        tier = risk.classify_command(line[1:].strip())
        if tier != risk.UNKNOWN:
            tiers.append(tier)
    return tiers


def _compute_max_tier(worktree: Path, base_sha: str, diff_text: str) -> str:
    tiers = ["read_only", *_classify_diff_files(worktree, base_sha), *_classify_diff_commands(diff_text)]
    computed = risk.max_tier(*tiers)
    return computed if computed in risk.TIER_RANK else "read_only"


def _write_diff_patch(job: dict[str, Any]) -> str:
    job_id = str(job["id"])
    worktree = _worktree_path(job)
    base_sha = str(job["base_sha"])
    _stage_intent_to_add(worktree)
    result = _run_git(worktree, ["diff", base_sha], check=False)
    _job_diff_path(job_id).write_text(result.stdout, encoding="utf-8", errors="replace")
    return result.stdout


def _delete_job_branch(job_id: str) -> None:
    _run_git(config.ROOT, ["branch", "-D", _per_job_branch(job_id)], check=False)


def _finalize_job(job_id: str, exit_code: int) -> dict[str, Any]:
    job = _read_job(job_id)
    job["exit_code"] = exit_code
    job["finished_at"] = _now()
    job["diffstat"] = _compute_diffstat(_worktree_path(job), str(job["base_sha"]))
    diff_text = _write_diff_patch(job)
    job["max_tier"] = _compute_max_tier(_worktree_path(job), str(job["base_sha"]), diff_text)
    blocked = governance.effective_blocked_tiers()
    flag_reasons: list[str] = []
    if not bool(job.get("allow_override")) and str(job.get("max_tier") or "") in blocked:
        flag_reasons.append(f"job finished with blocked tier: {job['max_tier']}")
    job["flagged"] = bool(flag_reasons)
    job["flag_reasons"] = flag_reasons
    if flag_reasons:
        governance.raise_degradation(job_id, flag_reasons)
    else:
        governance.record_clean_job()
    job["status"] = "awaiting-review"
    _write_job(job)
    return job


def _fail_job(job_id: str, message: str, exit_code: int | None = None) -> dict[str, Any]:
    job = _read_job(job_id)
    job["status"] = "failed"
    job["exit_code"] = exit_code
    job["finished_at"] = _now()
    job["error"] = message
    _write_job(job)
    return job


def _pump(stream: JobStream) -> None:
    stream.events.put({"type": "budget", "data": _budget_payload(stream)})
    readers = [
        threading.Thread(target=_read_pipe, args=(stream, stream.process.stdout), daemon=True),
        threading.Thread(target=_read_pipe, args=(stream, stream.process.stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()

    try:
        code = stream.process.wait(timeout=int(config.JOB_TIME_CAP_SECONDS))
    except subprocess.TimeoutExpired:
        stream.timed_out = True
        _emit_line(stream, f"TIME CAP EXCEEDED {config.JOB_TIME_CAP_SECONDS}s; killing job")
        stream.process.kill()
        code = stream.process.wait()

    for reader in readers:
        reader.join(timeout=1.0)

    stream.exit_code = int(code)
    try:
        job = _finalize_job(stream.job_id, stream.exit_code)
        status = job.get("status")
    except Exception as exc:  # pragma: no cover - defensive path for background thread
        _emit_line(stream, f"JOB FINALIZE FAILED: {exc}")
        _fail_job(stream.job_id, str(exc), stream.exit_code)
        status = "failed"

    stream.events.put({"type": "budget", "data": _budget_payload(stream)})
    stream.events.put(
        {
            "type": "exit",
            "data": {
                "code": stream.exit_code,
                "job_id": stream.job_id,
                "status": status,
                "timed_out": stream.timed_out,
            },
        }
    )


def create_job(brief: str, agent: str = "codex", allow_override: bool = False) -> dict[str, Any]:
    brief, inform_findings = inform.sanitize_text(brief)
    brief = brief.strip()
    if not brief:
        raise ValueError("brief is required")
    _validate_agent(agent)

    config.JOBS_DIR.mkdir(parents=True, exist_ok=True)
    base_sha = _git_output(config.ROOT, ["rev-parse", "HEAD"])
    job_id = _new_job_id()
    job_dir = _job_dir(job_id, must_exist=False)
    while job_dir.exists():
        job_id = _new_job_id()
        job_dir = _job_dir(job_id, must_exist=False)

    branch = _per_job_branch(job_id)
    worktree = job_dir / "wt"
    job_dir.mkdir(parents=True, exist_ok=False)
    try:
        _run_git(config.ROOT, ["worktree", "add", "-b", branch, str(worktree), base_sha])
        job = {
            "id": job_id,
            "brief": brief,
            "agent": agent,
            "status": "awaiting-approval",
            "worktree": str(worktree.resolve()),
            "branch": branch,
            "base_sha": base_sha,
            "created_at": _now(),
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "diffstat": {"files": 0, "insertions": 0, "deletions": 0},
            "log": f"jobs/{job_id}/stdout.log",
            "max_tier": "read_only",
            "run_count": 0,
            "allow_override": bool(allow_override),
            "inform_findings": inform_findings,
            "l2_decision": None,
            "l2_reasons": [],
            "l2_warnings": [],
            "approval_block_reasons": [],
            "flagged": False,
            "flag_reasons": [],
            "brief_sig": integrity.sign_text(brief),
            "provenance": {"source": JOB_ARTIFACT_SOURCE},
        }
        _write_job(job)
        try:
            governance.record_findings(job_id, inform_findings)
        except OSError:
            pass
        _job_log_path(job_id).write_text("", encoding="utf-8")
        return job
    except Exception:
        if worktree.exists():
            _run_git(config.ROOT, ["worktree", "remove", "--force", str(worktree)], check=False)
        _delete_job_branch(job_id)
        try:
            job_dir.rmdir()
        except OSError:
            pass
        raise


def reconcile_orphans() -> list[str]:
    """Mark jobs stuck in 'running' with no live stream as failed (restart recovery)."""
    orphaned: list[str] = []
    if not config.JOBS_DIR.exists():
        return orphaned
    for path in config.JOBS_DIR.glob("*/job.json"):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        job_id = str(data.get("id") or "")
        if not JOB_ID_RE.fullmatch(job_id):
            continue
        if data.get("status") == "running" and job_id not in _STREAMS:
            data["status"] = "failed"
            data["error"] = "orphaned by restart"
            data["finished_at"] = _now()
            try:
                _write_job(data)
                orphaned.append(job_id)
            except OSError:
                continue
    return orphaned


def list_jobs() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    if not config.JOBS_DIR.exists():
        return jobs
    for path in config.JOBS_DIR.glob("*/job.json"):
        try:
            job_dir = resolve_in_root(path.parent, config.JOBS_DIR)
            with (job_dir / "job.json").open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict) and JOB_ID_RE.fullmatch(str(data.get("id") or "")):
                jobs.append(_public_job(data))
        except (OSError, PermissionError, ValueError, json.JSONDecodeError):
            continue
    jobs.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return jobs


def get_job(job_id: str) -> dict[str, Any]:
    return _public_job(_read_job(job_id))


def approve(job_id: str) -> dict[str, Any]:
    job = _read_job(job_id)
    if job.get("status") != "awaiting-approval":
        raise ValueError(f"Job is not awaiting approval: {job_id}")
    _validate_agent(str(job.get("agent") or ""))
    run_count = int(job.get("run_count") or 0)
    if run_count >= int(config.JOB_MAX_RUNS):
        raise ValueError("run cap exceeded")
    if not verify_brief(job):
        job["approval_block_reasons"] = ["brief signature mismatch"]
        _write_job(job)
        governance.record_denial(job_id, job["approval_block_reasons"])
        raise ValueError("brief signature mismatch")

    created_at = _parse_time(job.get("created_at"))
    ttl_seconds = int(config.JOB_TTL_SECONDS)
    if created_at is None or (datetime.now(UTC) - created_at).total_seconds() > ttl_seconds:
        reasons = [f"job token expired after {ttl_seconds}s"]
        job["approval_block_reasons"] = reasons
        _write_job(job)
        governance.record_denial(job_id, reasons)
        raise ValueError("; ".join(reasons))

    worktree = _worktree_path(job)
    log_path = _job_log_path(job_id)
    log_path.write_text("", encoding="utf-8")
    command = _agent_command(job)
    check_job = dict(job)
    check_job["command"] = command
    check_job["diff"] = diff(job_id)
    l2 = verify.rule_check(check_job)
    job["l2_decision"] = l2["decision"]
    job["l2_reasons"] = list(l2.get("reasons") or [])
    job["l2_warnings"] = list(l2.get("reasons") or []) if l2["decision"] == "warn" else []
    job["approval_block_reasons"] = []
    if l2["decision"] == "deny":
        _write_job(job)
        governance.record_denial(job_id, job["l2_reasons"], escalate=True)
        raise ValueError("; ".join(job["l2_reasons"]))

    blocked = governance.effective_blocked_tiers()
    max_tier = str(job.get("max_tier") or "read_only")
    if not bool(job.get("allow_override")) and max_tier in blocked:
        reasons = [f"tier blocked at degradation {governance.status()['degradation']}: {max_tier}"]
        job["approval_block_reasons"] = reasons
        _write_job(job)
        governance.record_denial(job_id, reasons)
        raise ValueError("; ".join(reasons))

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    job["status"] = "running"
    job["started_at"] = _now()
    job["finished_at"] = None
    job["exit_code"] = None
    job["run_count"] = run_count + 1
    _write_job(job)

    try:
        process = _spawn_agent(command, cwd=worktree, env=env)
    except OSError as exc:
        _fail_job(job_id, str(exc))
        raise

    stream = JobStream(job_id=job_id, process=process, log_path=log_path, started_monotonic=time.monotonic())
    _STREAMS[job_id] = stream
    threading.Thread(target=_pump, args=(stream,), daemon=True).start()
    result = dict(job)
    result["stream_id"] = job_id
    return result


def accept(job_id: str) -> dict[str, Any]:
    job = _read_job(job_id)
    if job.get("status") != "awaiting-review":
        raise ValueError(f"Job is not awaiting review: {job_id}")
    worktree = _worktree_path(job)
    _run_git(worktree, ["add", "-A"])
    commit = _run_git(worktree, ["commit", "-m", f"opus-job {job_id}"], check=False)
    if commit.returncode != 0:
        status = _run_git(worktree, ["status", "--porcelain"], check=False).stdout.strip()
        if status:
            detail = (commit.stderr or commit.stdout or "").strip()
            raise RuntimeError(f"git commit failed: {detail}")
    job["status"] = "accepted"
    job["finished_at"] = _now()
    _write_job(job)
    return job


def rollback(job_id: str) -> dict[str, Any]:
    job = _read_job(job_id)
    if job.get("status") != "awaiting-review":
        raise ValueError(f"Job is not awaiting review: {job_id}")
    worktree = _worktree_path(job)
    _run_git(worktree, ["reset", "--hard", str(job["base_sha"])])
    _run_git(worktree, ["clean", "-fd"])
    _run_git(worktree, ["checkout", "--detach", str(job["base_sha"])], check=False)
    _delete_job_branch(job_id)
    job["status"] = "rolledback"
    job["finished_at"] = _now()
    job["diffstat"] = _compute_diffstat(worktree, str(job["base_sha"]))
    _write_diff_patch(job)
    _write_job(job)
    return job


def reject(job_id: str) -> dict[str, Any]:
    job = _read_job(job_id)
    if job.get("status") != "awaiting-approval":
        raise ValueError(f"Job has already started: {job_id}")
    worktree = _worktree_path(job)
    _run_git(config.ROOT, ["worktree", "remove", "--force", str(worktree)])
    _delete_job_branch(job_id)
    job["status"] = "rejected"
    job["finished_at"] = _now()
    _write_job(job)
    return job


def diff(job_id: str) -> str:
    path = _job_diff_path(job_id)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def stream_events(job_id: str) -> Iterator[str]:
    _read_job(job_id)
    stream = _STREAMS.get(job_id)
    if stream is None:
        raise FileNotFoundError(f"Job stream not found: {job_id}")

    def _iter() -> Iterator[str]:
        while True:
            event = stream.events.get()
            payload = json.dumps(event, ensure_ascii=False)
            yield f"event: {event['type']}\ndata: {payload}\n\n"
            if event.get("type") == "exit":
                break

    return _iter()
