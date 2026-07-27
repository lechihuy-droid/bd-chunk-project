from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import py_compile
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent
SUITES_DIR = HARNESS_DIR / "suites"
RUNS_DIR = HARNESS_DIR / "runs"
DEFAULT_PY311 = Path(r"C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe")
ROOT_RESOLVED = ROOT.resolve()

SHELL_LAUNCHERS = {
    "bash",
    "bash.exe",
    "cmd",
    "cmd.exe",
    "powershell",
    "powershell.exe",
    "pwsh",
    "pwsh.exe",
    "sh",
    "sh.exe",
    "wsl",
    "wsl.exe",
}
DANGEROUS_EXECUTABLES = SHELL_LAUNCHERS | {
    "diskpart",
    "diskpart.exe",
    "format",
    "format.com",
    "shutdown",
    "shutdown.exe",
    "taskkill",
    "taskkill.exe",
}
DANGEROUS_COMMAND_TOKENS = {
    "bcdedit",
    "cipher",
    "del",
    "diskpart",
    "erase",
    "format",
    "iex",
    "invoke-expression",
    "invoke-restmethod",
    "invoke-webrequest",
    "irm",
    "iwr",
    "mkfs",
    "rd",
    "reg",
    "remove-item",
    "rm",
    "rmdir",
    "set-executionpolicy",
    "shutdown",
    "stop-process",
    "sudo",
    "taskkill",
}
PATHLIKE_SUFFIXES = {
    ".cmd",
    ".json",
    ".jsonl",
    ".md",
    ".ps1",
    ".py",
    ".sql",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


class BoundaryPolicyError(ValueError):
    """Raised when a suite attempts work outside the harness boundary."""


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "check"


def _preferred_python() -> Path:
    env_python = os.environ.get("OPUS_HARNESS_PYTHON")
    if env_python:
        path = Path(env_python)
        if path.exists():
            return path
    if DEFAULT_PY311.exists():
        return DEFAULT_PY311
    return Path(sys.executable)


def _context(args: argparse.Namespace, run_dir: Path | None = None) -> dict[str, str]:
    py311 = _preferred_python()
    return {
        "root": str(ROOT),
        "harness": str(HARNESS_DIR),
        "runs": str(RUNS_DIR),
        "run_dir": str(run_dir or RUNS_DIR),
        "python": str(Path(sys.executable)),
        "py311": str(py311),
    }


def _expand(value: Any, ctx: dict[str, str]) -> Any:
    if isinstance(value, str):
        out = value
        for key, replacement in ctx.items():
            out = out.replace("{" + key + "}", replacement)
        return out
    if isinstance(value, list):
        return [_expand(item, ctx) for item in value]
    if isinstance(value, dict):
        return {key: _expand(item, ctx) for key, item in value.items()}
    return value


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _suite_path(name: str) -> Path:
    candidate = Path(name)
    if candidate.exists():
        return candidate.resolve()
    if not name.endswith(".json"):
        name = f"{name}.json"
    return SUITES_DIR / name


def _load_suite(name: str) -> tuple[Path, dict[str, Any]]:
    path = _suite_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Suite not found: {path}")
    suite = _read_json(path)
    if not isinstance(suite, dict):
        raise ValueError(f"Suite must be a JSON object: {path}")
    checks = suite.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError(f"Suite has no checks: {path}")
    return path, suite


def _list_suites() -> int:
    print("Available suites:")
    for path in sorted(SUITES_DIR.glob("*.json")):
        try:
            suite = _read_json(path)
            title = suite.get("name", path.stem)
            description = suite.get("description", "")
        except Exception as exc:  # pragma: no cover - diagnostic path
            title = path.stem
            description = f"INVALID: {exc}"
        print(f"- {path.stem}: {title}")
        if description:
            print(f"  {description}")
    return 0


def _make_run_dir(suite_id: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"{stamp}-{_safe_name(suite_id)}"
    (run_dir / "logs").mkdir(parents=True, exist_ok=False)
    return run_dir


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _norm_path(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _inside_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT_RESOLVED)
    except ValueError:
        return False
    return True


def _allowed_outside_paths(check: dict[str, Any], ctx: dict[str, str]) -> list[Path]:
    paths: list[Path] = []
    for value in _as_list(check.get("allowed_outside_paths")):
        paths.append(Path(_expand(value, ctx)).resolve())
    return paths


def _path_matches_allowed(path: Path, allowed: list[Path]) -> bool:
    resolved = path.resolve()
    for base in allowed:
        try:
            resolved.relative_to(base)
        except ValueError:
            if _norm_path(resolved) == _norm_path(base):
                return True
            continue
        return True
    return False


def _enforce_inside_root(path: Path, ctx: dict[str, str], check: dict[str, Any], field: str) -> None:
    if check.get("allow_outside_root"):
        return
    allowed = _allowed_outside_paths(check, ctx)
    if _inside_root(path) or _path_matches_allowed(path, allowed):
        return
    raise BoundaryPolicyError(f"{field} outside project root: {path.resolve()}")


def _glob_base(pattern: str) -> Path:
    prefix = re.split(r"[*?\[]", pattern, maxsplit=1)[0]
    if not prefix:
        return ROOT
    path = Path(prefix)
    if not path.is_absolute():
        path = ROOT / path
    if prefix.endswith(("/", "\\")):
        return path
    if path.exists() and path.is_dir():
        return path
    return path.parent


def _token_matches_dangerous(token: str) -> str | None:
    lowered = token.lower()
    for dangerous in DANGEROUS_COMMAND_TOKENS:
        pattern = rf"(?<![a-z0-9_-]){re.escape(dangerous)}(?![a-z0-9_-])"
        if re.search(pattern, lowered):
            return dangerous
    return None


def _looks_like_path_argument(value: str) -> bool:
    if not value or value.startswith("-"):
        return False
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return True
    if value.startswith(("./", ".\\", "../", "..\\")):
        return True
    if "/" in value or "\\" in value:
        return True
    return Path(value).suffix.lower() in PATHLIKE_SUFFIXES


def _enforce_command_boundary(command: Any, cwd: Path, ctx: dict[str, str], check: dict[str, Any]) -> None:
    if not isinstance(command, list) or not command:
        raise BoundaryPolicyError("command must be a non-empty argv list")

    _enforce_inside_root(cwd, ctx, check, "command cwd")

    executable = str(command[0])
    executable_name = Path(executable).name.lower() or executable.lower()
    if executable_name in SHELL_LAUNCHERS and not check.get("allow_shell"):
        raise BoundaryPolicyError(f"shell launcher requires explicit allow_shell: {executable}")
    if executable_name in DANGEROUS_EXECUTABLES and not check.get("allow_dangerous_commands"):
        raise BoundaryPolicyError(f"dangerous executable requires explicit allowlist: {executable}")

    allowed_names = {str(item).lower() for item in _as_list(check.get("allowed_executables"))}
    allowed_names.update({"py", "py.exe", "python", "python.exe"})
    safe_external_paths = {
        _norm_path(Path(ctx["python"])),
        _norm_path(Path(ctx["py311"])),
        _norm_path(Path(sys.executable)),
    }

    if Path(executable).is_absolute() or "/" in executable or "\\" in executable:
        executable_path = Path(executable)
        if not executable_path.is_absolute():
            executable_path = cwd / executable_path
        allowed_external = _norm_path(executable_path) in safe_external_paths
        allowed_external = allowed_external or _path_matches_allowed(executable_path, _allowed_outside_paths(check, ctx))
        if not (_inside_root(executable_path) or allowed_external):
            raise BoundaryPolicyError(f"executable outside project root is not allowlisted: {executable_path.resolve()}")
    elif executable_name not in allowed_names and not check.get("allow_system_executable"):
        raise BoundaryPolicyError(f"system executable is not allowlisted: {executable}")

    if not check.get("allow_dangerous_commands"):
        for token in command:
            dangerous = _token_matches_dangerous(str(token))
            if dangerous:
                raise BoundaryPolicyError(f"dangerous command token requires explicit allowlist: {dangerous}")

    for value in command[1:]:
        argument = str(value)
        if not _looks_like_path_argument(argument):
            continue
        argument_path = Path(argument)
        if not argument_path.is_absolute():
            argument_path = cwd / argument_path
        _enforce_inside_root(argument_path, ctx, check, "command argument")


def _write_log(run_dir: Path, check_id: str, name: str, text: str) -> str | None:
    if not text:
        return None
    path = run_dir / "logs" / f"{_safe_name(check_id)}.{name}.txt"
    path.write_text(text, encoding="utf-8")
    return _relative(path)


def _base_result(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": check["id"],
        "type": check["type"],
        "severity": check.get("severity", "normal"),
        "status": "fail",
        "message": "",
        "hint": check.get("hint", ""),
        "started_at": _now_utc(),
        "duration_seconds": 0.0,
        "evidence": {},
    }


def _finish(result: dict[str, Any], start: float, status: str, message: str) -> dict[str, Any]:
    result["status"] = status
    result["message"] = message
    result["finished_at"] = _now_utc()
    result["duration_seconds"] = round(time.perf_counter() - start, 3)
    return result


def _check_path_exists(check: dict[str, Any], ctx: dict[str, str], run_dir: Path) -> dict[str, Any]:
    start = time.perf_counter()
    result = _base_result(check)
    path = Path(_expand(check["path"], ctx))
    _enforce_inside_root(path, ctx, check, "path")
    kind = check.get("kind")
    exists = path.exists()
    ok = exists
    if kind == "file":
        ok = path.is_file()
    elif kind == "dir":
        ok = path.is_dir()
    result["evidence"] = {"path": _relative(path), "kind": kind or "any", "exists": exists}
    if ok:
        return _finish(result, start, "pass", f"Found {kind or 'path'}: {_relative(path)}")
    return _finish(result, start, "fail", f"Missing {kind or 'path'}: {_relative(path)}")


def _check_json_load(check: dict[str, Any], ctx: dict[str, str], run_dir: Path) -> dict[str, Any]:
    start = time.perf_counter()
    result = _base_result(check)
    path = Path(_expand(check["path"], ctx))
    _enforce_inside_root(path, ctx, check, "path")
    result["evidence"] = {"path": _relative(path)}
    try:
        data = _read_json(path)
    except Exception as exc:
        return _finish(result, start, "fail", f"JSON parse failed: {exc}")
    if isinstance(data, dict):
        detail = f"JSON object with {len(data)} keys"
    elif isinstance(data, list):
        detail = f"JSON list with {len(data)} items"
    else:
        detail = f"JSON {type(data).__name__}"
    result["evidence"]["detail"] = detail
    return _finish(result, start, "pass", detail)


def _check_file_contains(check: dict[str, Any], ctx: dict[str, str], run_dir: Path) -> dict[str, Any]:
    start = time.perf_counter()
    result = _base_result(check)
    path = Path(_expand(check["path"], ctx))
    _enforce_inside_root(path, ctx, check, "path")
    result["evidence"] = {"path": _relative(path)}
    try:
        text = path.read_text(encoding=check.get("encoding", "utf-8"))
    except Exception as exc:
        return _finish(result, start, "fail", f"Cannot read file: {exc}")
    missing = [needle for needle in check.get("contains", []) if needle not in text]
    result["evidence"]["missing"] = missing
    if missing:
        return _finish(result, start, "fail", f"Missing required text: {missing}")
    return _finish(result, start, "pass", "All required text found")


def _check_glob_count(check: dict[str, Any], ctx: dict[str, str], run_dir: Path) -> dict[str, Any]:
    start = time.perf_counter()
    result = _base_result(check)
    pattern = _expand(check["pattern"], ctx)
    _enforce_inside_root(_glob_base(pattern), ctx, check, "glob base")
    matches = [Path(item) for item in glob.glob(pattern, recursive=True)]
    min_count = check.get("min")
    max_count = check.get("max")
    count = len(matches)
    result["evidence"] = {
        "pattern": pattern,
        "count": count,
        "matches": [_relative(path) for path in matches[:25]],
    }
    if min_count is not None and count < int(min_count):
        return _finish(result, start, "fail", f"Expected at least {min_count}, found {count}")
    if max_count is not None and count > int(max_count):
        return _finish(result, start, "fail", f"Expected at most {max_count}, found {count}")
    return _finish(result, start, "pass", f"Found {count} matches")


def _check_python_compile(check: dict[str, Any], ctx: dict[str, str], run_dir: Path) -> dict[str, Any]:
    start = time.perf_counter()
    result = _base_result(check)
    patterns = check.get("files", [])
    files: list[Path] = []
    for pattern in patterns:
        expanded = _expand(pattern, ctx)
        matches = [Path(item) for item in glob.glob(expanded, recursive=True)]
        files.extend(matches if matches else [Path(expanded)])
    errors: list[str] = []
    for path in files:
        _enforce_inside_root(path, ctx, check, "python file")
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append(f"{_relative(path)}: {exc}")
    result["evidence"] = {
        "files": [_relative(path) for path in files],
        "errors": errors,
    }
    if errors:
        return _finish(result, start, "fail", f"{len(errors)} compile errors")
    return _finish(result, start, "pass", f"Compiled {len(files)} files")


def _assert_output(check: dict[str, Any], stdout: str, stderr: str) -> list[str]:
    failures: list[str] = []
    output = stdout + stderr
    for needle in check.get("stdout_contains", []):
        if needle not in stdout:
            failures.append(f"stdout missing {needle!r}")
    for needle in check.get("stderr_contains", []):
        if needle not in stderr:
            failures.append(f"stderr missing {needle!r}")
    for needle in check.get("output_contains", []):
        if needle not in output:
            failures.append(f"output missing {needle!r}")
    for needle in check.get("output_not_contains", []):
        if needle in output:
            failures.append(f"output unexpectedly contains {needle!r}")
    if check.get("stdout_json"):
        try:
            json.loads(stdout)
        except Exception as exc:
            failures.append(f"stdout is not valid JSON: {exc}")
    return failures


def _check_command(check: dict[str, Any], ctx: dict[str, str], run_dir: Path) -> dict[str, Any]:
    start = time.perf_counter()
    result = _base_result(check)
    command = _expand(check["command"], ctx)
    cwd = Path(_expand(check.get("cwd", "{root}"), ctx))
    _enforce_command_boundary(command, cwd, ctx, check)
    timeout = int(check.get("timeout_seconds", 60))
    env = os.environ.copy()
    env.update({key: str(_expand(value, ctx)) for key, value in check.get("env", {}).items()})
    result["evidence"] = {
        "command": command,
        "cwd": _relative(cwd),
        "timeout_seconds": timeout,
    }
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        result["evidence"]["stdout_log"] = _write_log(run_dir, check["id"], "stdout", exc.stdout or "")
        result["evidence"]["stderr_log"] = _write_log(run_dir, check["id"], "stderr", exc.stderr or "")
        return _finish(result, start, "fail", f"Timed out after {timeout}s")
    except Exception as exc:
        return _finish(result, start, "fail", f"Command failed to start: {exc}")

    stdout_log = _write_log(run_dir, check["id"], "stdout", completed.stdout)
    stderr_log = _write_log(run_dir, check["id"], "stderr", completed.stderr)
    result["evidence"].update(
        {
            "returncode": completed.returncode,
            "stdout_log": stdout_log,
            "stderr_log": stderr_log,
        }
    )
    expected = int(check.get("expected_exit", 0))
    failures = []
    if completed.returncode != expected:
        failures.append(f"exit {completed.returncode}, expected {expected}")
    failures.extend(_assert_output(check, completed.stdout, completed.stderr))
    if failures:
        return _finish(result, start, "fail", "; ".join(failures))
    return _finish(result, start, "pass", f"Command exited {completed.returncode}")


CHECKS = {
    "path_exists": _check_path_exists,
    "json_load": _check_json_load,
    "file_contains": _check_file_contains,
    "glob_count": _check_glob_count,
    "python_compile": _check_python_compile,
    "command": _check_command,
}


def _run_suite(args: argparse.Namespace) -> int:
    suite_path, suite = _load_suite(args.suite)
    suite_id = suite.get("id", suite_path.stem)
    checks = suite["checks"]
    suite_policy = suite.get("policy", {})
    if not isinstance(suite_policy, dict):
        suite_policy = {}
    if args.check:
        checks = [check for check in checks if check.get("id") == args.check]
        if not checks:
            raise ValueError(f"Check not found in suite {suite_id}: {args.check}")
    run_dir = _make_run_dir(suite_id)
    ctx = _context(args, run_dir)
    trace_path = run_dir / "trace.jsonl"
    results: list[dict[str, Any]] = []

    print(f"Suite: {suite.get('name', suite_id)}")
    print(f"Run:   {_relative(run_dir)}")
    print("")

    with trace_path.open("w", encoding="utf-8") as trace:
        for raw_check in checks:
            merged_check = dict(suite_policy)
            merged_check.update(raw_check)
            check = _expand(merged_check, ctx)
            check_id = check.get("id")
            check_type = check.get("type")
            if not check_id or check_type not in CHECKS:
                raise ValueError(f"Invalid check in {suite_path}: {check}")
            if args.dry_run:
                print(f"DRY {check_id} ({check_type})")
                continue
            check_start = time.perf_counter()
            try:
                result = CHECKS[check_type](check, ctx, run_dir)
            except BoundaryPolicyError as exc:
                result = _base_result(check)
                result["evidence"] = {
                    "policy": "workspace-boundary",
                    "root": str(ROOT_RESOLVED),
                }
                result = _finish(result, check_start, "fail", f"Boundary policy violation: {exc}")
            result["suite"] = suite_id
            results.append(result)
            trace.write(json.dumps(result, ensure_ascii=False) + "\n")
            trace.flush()
            mark = "PASS" if result["status"] == "pass" else "FAIL"
            print(f"{mark} {check_id}: {result['message']}")
            if result["status"] != "pass" and result.get("hint"):
                print(f"     hint: {result['hint']}")
            if args.fail_fast and result["status"] != "pass":
                break

    if args.dry_run:
        return 0

    passed = sum(1 for result in results if result["status"] == "pass")
    failed = sum(1 for result in results if result["status"] != "pass")
    summary = {
        "run_id": run_dir.name,
        "suite": suite_id,
        "suite_name": suite.get("name", suite_id),
        "suite_path": _relative(suite_path),
        "started_at": results[0]["started_at"] if results else _now_utc(),
        "finished_at": _now_utc(),
        "status": "pass" if failed == 0 else "fail",
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "results": results,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(run_dir, summary)

    print("")
    print(f"Result: {summary['status'].upper()} ({passed} passed, {failed} failed)")
    print(f"Report: {_relative(run_dir / 'report.md')}")
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    return 0 if failed == 0 else 1


def _write_report(run_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"# Harness Report - {summary['suite_name']}",
        "",
        f"- Run: `{summary['run_id']}`",
        f"- Status: `{summary['status']}`",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Trace: `trace.jsonl`",
        "",
        "| Check | Status | Duration | Message | Evidence |",
        "|---|---:|---:|---|---|",
    ]
    for result in summary["results"]:
        evidence = result.get("evidence", {})
        logs = [value for key, value in evidence.items() if key.endswith("_log") and value]
        evidence_text = "<br>".join(f"`{log}`" for log in logs) if logs else ""
        message = str(result["message"]).replace("|", "\\|")
        lines.append(
            f"| `{result['id']}` | `{result['status']}` | "
            f"{result['duration_seconds']}s | {message} | {evidence_text} |"
        )
        if result["status"] != "pass" and result.get("hint"):
            hint = str(result["hint"]).replace("|", "\\|")
            lines.append(f"| `{result['id']}` hint |  |  | {hint} | |")
    lines.append("")
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Opus workspace harness suites.")
    parser.add_argument("--suite", default="workspace-smoke", help="suite id or path")
    parser.add_argument("--check", help="run a single check id")
    parser.add_argument("--list", action="store_true", help="list available suites")
    parser.add_argument("--fail-fast", action="store_true", help="stop after first failing check")
    parser.add_argument("--dry-run", action="store_true", help="print checks without running")
    parser.add_argument("--json", action="store_true", help="also print summary JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = _parser()
    args = parser.parse_args(argv)
    if args.list:
        return _list_suites()
    return _run_suite(args)


if __name__ == "__main__":
    raise SystemExit(main())
