# Opus Agent Harness

Local harness for workspace health, agent-task evaluation, and trace-grounded repair.
## Cài đặt và chạy

Yêu cầu: **Python 3.11+**. Dashboard Hub cần thêm **Node.js 20+** và `pnpm` (qua Corepack). Docker và Inspect AI là tùy chọn.

```powershell
git clone https://github.com/lechihuy-droid/bd-chunk-project.git
cd bd-chunk-project
py -3.11 -m venv .ih
.\.ih\Scripts\python.exe -m pip install --upgrade pip
.\.ih\Scripts\python.exe -m pip install -r .\harness\hub\requirements-hub.txt
```

Nếu không có `py -3.11`, thay bằng đường dẫn tới Python 3.11+ trên máy. Core harness không cần API key.

Chạy kiểm tra cơ bản từ thư mục gốc repository:

```powershell
.\.ih\Scripts\python.exe .\harness\run_harness.py --suite workspace-smoke
.\.ih\Scripts\python.exe .\harness\run_harness.py --suite boundary-compliance
.\harness\ci-harness.ps1 -SkipInspect
```

### Harness Hub

Chạy backend trong một cửa sổ PowerShell:

```powershell
.\.ih\Scripts\python.exe .\harness\hub\server.py
```

Chạy UI development trong cửa sổ khác:

```powershell
cd .\harness\hub\web-v3
corepack enable
pnpm install --frozen-lockfile
pnpm dev
```

Mở `http://127.0.0.1:5173`; Vite sẽ proxy API đến backend ở `http://127.0.0.1:8799`.

Để chạy kiểu production cục bộ, dùng `pnpm build` trong `harness\hub\web-v3`, rồi khởi động backend và mở `http://127.0.0.1:8799`. Backend sẽ phục vụ thư mục `dist` khi build tồn tại.

### Tùy chọn

- Claude, Codex, Gemini: cài và đăng nhập CLI tương ứng trên máy.
- NVIDIA API: đặt `NVIDIA_API_KEY` trong biến môi trường hoặc file `.env` ở gốc repo (không commit file này).
- Inspect AI: chạy `.\harness\install-inspect.ps1` trước khi dùng `.\harness\run-inspect.ps1`.
- Docker: cài Docker Desktop trước khi chạy `run-docker-harness.ps1`.

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

From the repository root:

```powershell
.\.ih\Scripts\python.exe .\harness\run_harness.py --suite workspace-smoke
```

List available suites:

```powershell
.\.ih\Scripts\python.exe .\harness\run_harness.py --list
```

Run one check:

```powershell
.\.ih\Scripts\python.exe .\harness\run_harness.py --suite workspace-smoke --check recall-tests
```

Run boundary compliance probes:

```powershell
.\.ih\Scripts\python.exe .\harness\run_harness.py --suite boundary-compliance
```

Run the local CI loop:

```powershell
.\harness\ci-harness.ps1 -SkipInspect
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
