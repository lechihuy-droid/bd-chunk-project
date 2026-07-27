from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "harness"
INSPECT_DIR = HARNESS_DIR / "inspect"
DEFAULT_LOG_DIR = INSPECT_DIR / "logs"
DEFAULT_OUT_DIR = INSPECT_DIR / "mep"
DEFAULT_INSPECT_EXE = ROOT / ".ih" / "Scripts" / "inspect.exe"


def _latest_eval(log_dir: Path) -> Path:
    logs = sorted(log_dir.glob("*.eval"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not logs:
        raise FileNotFoundError(f"No Inspect .eval logs found in {log_dir}")
    return logs[0]


def _inspect_env() -> dict[str, str]:
    env = os.environ.copy()
    local_data = INSPECT_DIR / ".localappdata"
    roaming_data = INSPECT_DIR / ".appdata"
    cache_data = INSPECT_DIR / ".cache"
    trace_data = INSPECT_DIR / "traces"
    for path in (local_data, roaming_data, cache_data, trace_data):
        path.mkdir(parents=True, exist_ok=True)
    env["LOCALAPPDATA"] = str(local_data)
    env["APPDATA"] = str(roaming_data)
    env["XDG_DATA_HOME"] = str(local_data)
    env["XDG_CACHE_HOME"] = str(cache_data)
    env["INSPECT_TRACE_FILE"] = str(trace_data / f"trace-export-mep-{os.getpid()}.log")
    env["OPUS_INSPECT_DATA_DIR"] = str(local_data)
    env["OPUS_INSPECT_CACHE_DIR"] = str(cache_data)
    sitecustomize = INSPECT_DIR / "sitecustomize"
    env["PYTHONPATH"] = (
        str(sitecustomize)
        if not env.get("PYTHONPATH")
        else str(sitecustomize) + os.pathsep + env["PYTHONPATH"]
    )
    return env


def _dump_log(inspect_exe: Path, log_path: Path) -> dict[str, Any]:
    if not inspect_exe.exists():
        raise FileNotFoundError(f"Inspect CLI not found: {inspect_exe}")
    completed = subprocess.run(
        [str(inspect_exe), "log", "dump", str(log_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_inspect_env(),
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def _score_is_failure(sample: dict[str, Any]) -> bool:
    value = sample.get("value")
    answer = str(sample.get("answer", "")).lower()
    if value in (True, 1, 1.0, "1", "1.0"):
        return False
    if answer in {"pass", "passed", "correct"} and value not in (False, 0, 0.0, "0", "0.0"):
        return False
    return True


def _local_failures(sample: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = sample.get("metadata")
    if not isinstance(metadata, dict):
        return []
    summary = metadata.get("summary")
    if not isinstance(summary, dict):
        return []
    results = summary.get("results")
    if not isinstance(results, list):
        return []
    failures = []
    for result in results:
        if isinstance(result, dict) and result.get("status") != "pass":
            failures.append(
                {
                    "id": result.get("id"),
                    "type": result.get("type"),
                    "message": result.get("message"),
                    "hint": result.get("hint"),
                    "evidence": result.get("evidence"),
                }
            )
    return failures


def _collect_samples(log: dict[str, Any]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for reduction in log.get("reductions", []) or []:
        if not isinstance(reduction, dict):
            continue
        scorer = reduction.get("scorer")
        for sample in reduction.get("samples", []) or []:
            if not isinstance(sample, dict):
                continue
            item = dict(sample)
            item["scorer"] = scorer
            samples.append(item)
    return samples


def _build_mep(log_path: Path, log: dict[str, Any]) -> dict[str, Any]:
    eval_info = log.get("eval", {}) if isinstance(log.get("eval"), dict) else {}
    results = log.get("results", {}) if isinstance(log.get("results"), dict) else {}
    stats = log.get("stats", {}) if isinstance(log.get("stats"), dict) else {}
    samples = _collect_samples(log)
    failed_samples = [sample for sample in samples if _score_is_failure(sample)]

    packets = []
    for sample in failed_samples:
        metadata = sample.get("metadata") if isinstance(sample.get("metadata"), dict) else {}
        packets.append(
            {
                "sample_id": sample.get("sample_id"),
                "scorer": sample.get("scorer"),
                "value": sample.get("value"),
                "answer": sample.get("answer"),
                "explanation": sample.get("explanation"),
                "command": metadata.get("command") if isinstance(metadata, dict) else None,
                "cwd": metadata.get("cwd") if isinstance(metadata, dict) else None,
                "returncode": metadata.get("returncode") if isinstance(metadata, dict) else None,
                "report": metadata.get("report") if isinstance(metadata, dict) else None,
                "stdout_tail": metadata.get("stdout_tail") if isinstance(metadata, dict) else None,
                "stderr_tail": metadata.get("stderr_tail") if isinstance(metadata, dict) else None,
                "local_failures": _local_failures(sample),
            }
        )

    return {
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "source_log": str(log_path),
        "status": log.get("status"),
        "task": eval_info.get("task"),
        "task_file": eval_info.get("task_file"),
        "model": eval_info.get("model"),
        "created": eval_info.get("created"),
        "completed_at": stats.get("completed_at"),
        "scores": results.get("scores"),
        "failed_sample_count": len(packets),
        "failed_samples": packets,
    }


def _write_markdown(path: Path, mep: dict[str, Any]) -> None:
    lines = [
        f"# Minimal Explanation Packet - {mep.get('task') or 'inspect-eval'}",
        "",
        f"- Source log: `{mep['source_log']}`",
        f"- Status: `{mep.get('status')}`",
        f"- Model: `{mep.get('model')}`",
        f"- Failed samples: {mep.get('failed_sample_count')}",
        "",
    ]
    scores = mep.get("scores") or []
    if scores:
        lines.append("## Scores")
        for score in scores:
            metrics = score.get("metrics", {}) if isinstance(score, dict) else {}
            metric_text = ", ".join(
                f"{name}={metric.get('value')}" for name, metric in metrics.items() if isinstance(metric, dict)
            )
            lines.append(f"- `{score.get('name')}`: {metric_text}")
        lines.append("")

    failures = mep.get("failed_samples") or []
    if not failures:
        lines.append("No failed samples.")
    for failure in failures:
        lines.extend(
            [
                f"## Sample `{failure.get('sample_id')}`",
                "",
                f"- Scorer: `{failure.get('scorer')}`",
                f"- Value: `{failure.get('value')}`",
                f"- Answer: `{failure.get('answer')}`",
                f"- Report: `{failure.get('report')}`",
                "",
            ]
        )
        explanation = failure.get("explanation")
        if explanation:
            lines.extend(["### Explanation", "", "```text", str(explanation), "```", ""])
        local_failures = failure.get("local_failures") or []
        if local_failures:
            lines.append("### Local Harness Failures")
            for item in local_failures:
                lines.append(f"- `{item.get('id')}`: {item.get('message')}")
                if item.get("hint"):
                    lines.append(f"  Hint: {item.get('hint')}")
            lines.append("")
        stderr_tail = failure.get("stderr_tail") or []
        if stderr_tail:
            lines.extend(["### Stderr Tail", "", "```text", *[str(line) for line in stderr_tail[-20:]], "```", ""])
        stdout_tail = failure.get("stdout_tail") or []
        if stdout_tail:
            lines.extend(["### Stdout Tail", "", "```text", *[str(line) for line in stdout_tail[-20:]], "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a minimal explanation packet from an Inspect eval log.")
    parser.add_argument("--log", type=Path, help="Inspect .eval log. Defaults to newest log in --log-dir.")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--inspect-exe", type=Path, default=DEFAULT_INSPECT_EXE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    log_path = (args.log or _latest_eval(args.log_dir)).resolve()
    log = _dump_log(args.inspect_exe.resolve(), log_path)
    mep = _build_mep(log_path, log)

    out_dir = args.out_dir / log_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "mep.json"
    md_path = out_dir / "mep.md"
    json_path.write_text(json.dumps(mep, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(md_path, mep)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0 if mep["failed_sample_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
