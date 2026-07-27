# Harness Sandbox

This directory makes the Opus Agent Harness Docker-ready for coding-agent and
SWE-style evals.

Current machine status: Docker CLI was not found when this was configured.
Install Docker Desktop to activate this runner.

Run from the project root:

```powershell
.\harness\run-docker-harness.ps1 workspace-smoke
.\harness\run-docker-harness.ps1 boundary-compliance
```

The runner uses:

- read-only bind mount of the project at `/src`
- copy-on-run working tree under `/work/repo`
- no network
- read-only container root filesystem
- writable tmpfs for `/tmp` and `/work`
- CPU, memory, and pid limits
- non-root user `harness`

For `inspect-swe` coding-agent evals, use this runner or an equivalent Docker,
E2B, or WebAssembly sandbox profile before allowing agents to execute real CLI
commands.
