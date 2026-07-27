# Opus Agent Harness

Local harness for workspace health, agent-task evaluation, and trace-grounded repair.

This is intentionally lightweight:

- no background service
- no API key required
- no dependency required for the bootstrap suite
- all run evidence is written under `harness/runs/`

The design borrows the useful parts from the local agent-harness paper pack:

- executable checks, not vibes
- trace files for every run
- repair hints attached to failing checks
- suite manifests that can grow from smoke checks to agent rubrics
- optional adapter path for Inspect AI when model/agent evals need a full framework

## Quick Start

From `C:\Users\HUY\workspace\ai-project-opus`:

```powershell
C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe harness\run_harness.py --suite workspace-smoke
```

List available suites:

```powershell
C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe harness\run_harness.py --list
```

Run one check:

```powershell
C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe harness\run_harness.py --suite workspace-smoke --check recall-tests
```

Run boundary compliance probes:

```powershell
C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe harness\run_harness.py --suite boundary-compliance
```

Run the local CI loop:

```powershell
.\harness\ci-harness.ps1
```

Artifacts are written to:

```text
harness/runs/YYYYMMDD-HHMMSS-<suite>/
  summary.json
  trace.jsonl
  report.md
  logs/
```

## Suite Shape

Suites live in `harness/suites/*.json`.

Supported check types:

- `path_exists`: verify a file or directory exists.
- `json_load`: verify a JSON file parses.
- `file_contains`: verify required text appears in a file.
- `glob_count`: verify a glob has a count within bounds.
- `python_compile`: compile Python files without importing them.
- `command`: run an executable command with timeout and output assertions.

Boundary policy is enabled by default:

- file, JSON, glob, and compile checks must stay inside `{root}`
- command `cwd` must stay inside `{root}`
- path-like command arguments must stay inside `{root}`
- raw shell launchers such as `powershell.exe`, `cmd.exe`, `bash`, and `wsl`
  require explicit `allow_shell`
- dangerous command tokens require explicit `allow_dangerous_commands`

Use per-check allowlists only when the exception is intentional:

```json
{
  "allowed_outside_paths": ["C:/approved/tool.exe"],
  "allowed_executables": ["git"],
  "allow_system_executable": true
}
```

Command fields use tokens:

- `{root}`: project root
- `{harness}`: harness directory
- `{python}`: runner Python
- `{py311}`: preferred Python 3.11 path, falling back to `{python}`

## When To Use Inspect AI

Use this local harness for workspace/pipeline health and deterministic checks.

Add Inspect AI when the task becomes true model/agent evaluation:

- compare multiple model/provider behaviors
- run long-horizon agent tasks with tools
- use sandboxed untrusted model code
- inspect rich eval logs in a UI

Installed Inspect stack:

```text
.ih/
  inspect-ai  0.3.241
  inspect-swe 0.2.63
  inspect-viz 0.4.0
```

Use the wrapper so Inspect runtime files stay under the workspace where possible:

```powershell
.\harness\run-inspect.ps1 list tasks .\harness\inspect\tasks
.\harness\run-inspect.ps1 eval .\harness\inspect\tasks\workspace_smoke.py --log-dir .\harness\inspect\logs --display plain
.\harness\run-inspect.ps1 eval .\harness\inspect\tasks\boundary_compliance.py --log-dir .\harness\inspect\logs --display plain
.\harness\run-inspect.ps1 log list --log-dir .\harness\inspect\logs
```

Export a minimal explanation packet from the newest Inspect log:

```powershell
.\.ih\Scripts\python.exe harness\inspect\export_mep.py
```

Docker sandbox files are available under `harness/sandbox/`. Docker CLI was not
installed when this harness was configured, so install Docker Desktop before
running:

```powershell
.\harness\run-docker-harness.ps1 workspace-smoke
.\harness\run-docker-harness.ps1 boundary-compliance
```

Primary references:

- Inspect AI: https://inspect.aisi.org.uk/
- OpenAI Evals: https://github.com/openai/evals
- promptfoo: https://www.promptfoo.dev/docs/intro/
- LangSmith observability: https://docs.langchain.com/langsmith/observability
