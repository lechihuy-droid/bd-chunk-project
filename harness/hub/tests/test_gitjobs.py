from __future__ import annotations

import io
import subprocess
from pathlib import Path

import pytest

import config
from services import boundary, gitjobs


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        check=True,
    )


def branch_exists(cwd: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(cwd), "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    return result.returncode == 0


@pytest.fixture()
def temp_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    run_git(repo, "config", "user.email", "hub-tests@example.test")
    run_git(repo, "config", "user.name", "Hub Tests")

    (repo / "README.md").write_text("# tmp\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "initial")
    (repo / "second.txt").write_text("second\n", encoding="utf-8")
    run_git(repo, "add", "second.txt")
    run_git(repo, "commit", "-m", "second")

    jobs_dir = repo / "harness" / "hub" / "jobs"
    monkeypatch.setattr(config, "ROOT", repo)
    monkeypatch.setattr(config, "JOBS_DIR", jobs_dir)
    monkeypatch.setattr(config, "JOB_ALLOW_AGENTS", {"codex"})
    monkeypatch.setattr(config, "JOB_AGENT_CMD", "codex")
    monkeypatch.setattr(config, "JOB_TIME_CAP_SECONDS", 10)
    monkeypatch.setattr(config, "JOB_MAX_RUNS", 3)
    monkeypatch.setattr(config, "JOB_BLOCKED_TIERS", ["destructive"])
    monkeypatch.setattr(config, "JOB_TTL_SECONDS", 3600)
    monkeypatch.setattr(config, "GOV_RECOVERY_STEPS", 5)
    monkeypatch.setattr(config, "HMAC_KEY_FILE", tmp_path / ".hmac_key")
    monkeypatch.setattr(config, "INTEGRITY_SIGS_FILE", tmp_path / ".cache" / "suite_sigs.json")
    monkeypatch.setattr(config, "GOVERNANCE_STATE_FILE", tmp_path / ".cache" / "governance.json")
    monkeypatch.setattr(config, "RUNTIME_DIR", tmp_path / "runtime")
    monkeypatch.setattr(config, "RUNTIME_STORE_DIR", tmp_path / "runtime" / "store")
    monkeypatch.setattr(boundary, "ROOT_RESOLVED", repo.resolve())
    gitjobs._STREAMS.clear()
    return repo


def force_awaiting_approval(job_id: str) -> None:
    job = gitjobs._read_job(job_id)
    job["status"] = "awaiting-approval"
    gitjobs._write_job(job)


def test_job_lifecycle_uses_temp_repo_and_worktree_only(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spawned: list[tuple[list[str], Path]] = []
    run_git(temp_repo, "branch", "other-branch")

    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = io.StringIO("agent wrote file\n")
            self.stderr = io.StringIO("")

        def wait(self, timeout: int | None = None) -> int:
            return 0

        def kill(self) -> None:
            return None

    def fake_spawn(command: list[str], cwd: Path, env: dict[str, str]) -> FakeProcess:
        spawned.append((command, Path(cwd)))
        (Path(cwd) / "agent-output.txt").write_text("curl https://example.com\n", encoding="utf-8")
        return FakeProcess()

    monkeypatch.setattr(gitjobs, "_spawn_agent", fake_spawn)

    job = gitjobs.create_job("write a file", "codex")
    worktree = Path(job["worktree"])

    assert job["status"] == "awaiting-approval"
    assert job["run_count"] == 0
    assert job["max_tier"] == "read_only"
    assert job["provenance"]["source"] == "codex-agent"
    assert gitjobs.get_job(job["id"])["brief_ok"] is True
    assert worktree.is_dir()
    assert job["base_sha"] == run_git(temp_repo, "rev-parse", "HEAD").stdout.strip()
    assert branch_exists(temp_repo, job["branch"])

    running = gitjobs.approve(job["id"])
    assert running["status"] == "running"
    assert running["run_count"] == 1
    assert spawned
    assert spawned[0][0][0] == "codex"
    assert spawned[0][1] == worktree

    streamed = "".join(gitjobs.stream_events(job["id"]))
    assert "agent wrote file" in streamed
    assert "event: exit" in streamed

    reviewed = gitjobs.get_job(job["id"])
    assert reviewed["status"] == "awaiting-review"
    assert reviewed["diffstat"]["files"] == 1
    assert reviewed["diffstat"]["insertions"] == 1
    assert reviewed["max_tier"] == "network"
    assert "agent-output.txt" in gitjobs.diff(job["id"])

    rolled_back = gitjobs.rollback(job["id"])
    assert rolled_back["status"] == "rolledback"
    assert run_git(worktree, "status", "--porcelain").stdout.strip() == ""
    assert not (worktree / "agent-output.txt").exists()
    assert not branch_exists(temp_repo, job["branch"])
    assert branch_exists(temp_repo, "other-branch")

    rejected = gitjobs.create_job("reject before run", "codex")
    rejected_wt = Path(rejected["worktree"])
    assert rejected_wt.is_dir()
    assert branch_exists(temp_repo, rejected["branch"])

    rejected = gitjobs.reject(rejected["id"])
    assert rejected["status"] == "rejected"
    assert not rejected_wt.exists()
    assert not branch_exists(temp_repo, rejected["branch"])
    assert branch_exists(temp_repo, "other-branch")


def test_approval_is_one_time_even_if_job_status_is_tampered(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = io.StringIO("ok\n")
            self.stderr = io.StringIO("")

        def wait(self, timeout: int | None = None) -> int:
            return 0

        def kill(self) -> None:
            return None

    def fake_spawn(command: list[str], cwd: Path, env: dict[str, str]) -> FakeProcess:
        (Path(cwd) / "run-count.txt").write_text("ran\n", encoding="utf-8")
        return FakeProcess()

    monkeypatch.setattr(gitjobs, "_spawn_agent", fake_spawn)

    job = gitjobs.create_job("run repeatedly", "codex")
    running = gitjobs.approve(job["id"])
    assert running["run_count"] == 1
    assert "event: exit" in "".join(gitjobs.stream_events(job["id"]))
    force_awaiting_approval(job["id"])
    with pytest.raises(ValueError, match="already used"):
        gitjobs.approve(job["id"])


def test_brief_signature_detects_tampering(temp_repo: Path) -> None:
    job = gitjobs.create_job("keep this brief intact", "codex")

    created = gitjobs.get_job(job["id"])
    assert created["brief_sig"]
    assert created["brief_ok"] is True
    assert gitjobs.verify_brief(created) is True

    tampered = gitjobs._read_job(job["id"])
    tampered["brief"] = "changed after signing"
    gitjobs._write_job(tampered)

    checked = gitjobs.get_job(job["id"])
    assert checked["brief_ok"] is False
    assert gitjobs.verify_brief(checked) is False


def test_approval_binding_rejects_mutated_brief(temp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitjobs, "_spawn_agent", lambda *_args, **_kwargs: pytest.fail("agent should not launch"))
    job = gitjobs.create_job("keep action exact", "codex")
    record = gitjobs._read_job(job["id"])
    record["brief"] = "different action"
    gitjobs._write_job(record)
    with pytest.raises(ValueError, match="approval binding changed"):
        gitjobs.approve(job["id"])


def test_approve_blocks_destructive_tier_without_override(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_spawn(command: list[str], cwd: Path, env: dict[str, str]) -> object:
        raise AssertionError("agent should not launch")

    monkeypatch.setattr(gitjobs, "_spawn_agent", fail_spawn)
    job = gitjobs.create_job("review destructive diff", "codex")
    record = gitjobs._read_job(job["id"])
    record["max_tier"] = "destructive"
    gitjobs._write_job(record)

    with pytest.raises(ValueError, match="destructive"):
        gitjobs.approve(job["id"])

    checked = gitjobs.get_job(job["id"])
    assert checked["status"] == "awaiting-approval"
    assert checked["l2_decision"] == "deny"


def test_approve_blocks_expired_job_token(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_spawn(command: list[str], cwd: Path, env: dict[str, str]) -> object:
        raise AssertionError("agent should not launch")

    monkeypatch.setattr(gitjobs, "_spawn_agent", fail_spawn)
    job = gitjobs.create_job("expired job", "codex")
    record = gitjobs._read_job(job["id"])
    record["approval_receipt"]["expires_at"] = "2000-01-01T00:00:00Z"
    gitjobs._write_job(record)

    with pytest.raises(ValueError, match="expired"):
        gitjobs.approve(job["id"])

    checked = gitjobs.get_job(job["id"])
    assert checked["approval_block_reasons"]


def test_allow_override_lets_blocked_tier_approve(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = io.StringIO("override ok\n")
            self.stderr = io.StringIO("")

        def wait(self, timeout: int | None = None) -> int:
            return 0

        def kill(self) -> None:
            return None

    spawned: list[Path] = []

    def fake_spawn(command: list[str], cwd: Path, env: dict[str, str]) -> FakeProcess:
        spawned.append(Path(cwd))
        (Path(cwd) / "override.txt").write_text("ok\n", encoding="utf-8")
        return FakeProcess()

    monkeypatch.setattr(gitjobs, "_spawn_agent", fake_spawn)
    job = gitjobs.create_job("override destructive tier", "codex", allow_override=True)
    record = gitjobs._read_job(job["id"])
    record["max_tier"] = "destructive"
    gitjobs._write_job(record)

    running = gitjobs.approve(job["id"])

    assert running["status"] == "running"
    assert spawned == [Path(job["worktree"])]
    streamed = "".join(gitjobs.stream_events(job["id"]))
    assert "override ok" in streamed
    checked = gitjobs.get_job(job["id"])
    assert checked["status"] == "awaiting-review"
    assert checked["allow_override"] is True
