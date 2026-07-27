# SAFEHARNESS Group A - Hub Observability

Group A adds observe-only governance to Harness Hub. It does not call an LLM, does not require an API key, and does not enforce runtime policy.

## A1 Entropy Monitor

- Endpoint: `GET /api/sessions/entropy`
- Config: `ENTROPY_WINDOW = 20`, `ENTROPY_THRESHOLD = 0.3` in `config.py`
- A session is flagged when the max sliding-window violation rate is greater than the threshold.
- A violation is any repeated adjacent tool, `network` or `destructive` tier action, or tool-result error.

## A2 Provenance Tagging

- Session replay rows now include `provenance_role` and `trust`.
- Model rows are tagged `model/trusted`.
- Tool output rows are tagged `tool/untrusted`.
- Replay UI includes an `Untrusted only` filter.

## A3 5-Tier Risk Registry

- Config file: `harness/hub/risk_tiers.json`
- Tiers: `read_only`, `write`, `execute`, `network`, `destructive`; unknown tools or commands return `unknown`.
- `services/risk.py` exposes `classify_tool(name)` and `classify_command(argv_or_string)`.
- `/api/tools` rollups include `tier`, and replay tool calls/results show risk badges.

## A4 Suite Manifest Integrity

- Endpoint: `GET /api/integrity`
- HMAC key source: env `HUB_HMAC_KEY`, otherwise `harness/hub/.hmac_key` is generated locally.
- Signatures are stored in `harness/hub/.cache/suite_sigs.json`.
- First verification signs unsigned suites; later edits produce a mismatch warning in the Suites page.

## A5 Violation Report

- Run summaries/details include `violations`.
- Counts include failed boundary checks, dangerous-command signals, and command evidence at tier `execute` or above.
- Dashboard shows recent violation trend from `/api/runs`.

## codex-wrap B0 governance

- Job records now carry `max_tier`, computed when a Codex worktree job reaches `awaiting-review`.
- `JOB_MAX_RUNS = 3` limits each job to three approvals; `run_count` is incremented on every approve.
- Job briefs are signed with `brief_sig` using the existing HMAC helper, and `/api/jobs/{id}` returns `brief_ok`.
- Rejected and rolled-back jobs best-effort delete only their own `opus-job/<id>` branch after worktree cleanup/reset.
- Job artifacts are labeled with provenance `source = codex-agent` for the Jobs UI.
