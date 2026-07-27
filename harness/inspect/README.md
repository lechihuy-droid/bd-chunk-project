# Inspect Harness Tasks

Inspect tasks for the Opus workspace.

Run from `C:\Users\HUY\workspace\ai-project-opus`:

```powershell
.\harness\run-inspect.ps1 list tasks .\harness\inspect\tasks
.\harness\run-inspect.ps1 eval .\harness\inspect\tasks\workspace_smoke.py --log-dir .\harness\inspect\logs --display plain
.\harness\run-inspect.ps1 eval .\harness\inspect\tasks\boundary_compliance.py --log-dir .\harness\inspect\logs --display plain
.\harness\run-inspect.ps1 view --log-dir .\harness\inspect\logs
```

Current tasks:

- `workspace_smoke`: wraps the local deterministic workspace smoke harness.
- `boundary_compliance`: runs negative probes that should be blocked by the
  harness boundary policy.

Run the local harness directly:

```powershell
C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe harness\run_harness.py --suite workspace-smoke
C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe harness\run_harness.py --suite boundary-compliance
```

Export a minimal explanation packet from the newest Inspect log:

```powershell
.\.ih\Scripts\python.exe harness\inspect\export_mep.py
```

Use these as the baseline before adding model-backed or Codex/Claude-backed tasks.
