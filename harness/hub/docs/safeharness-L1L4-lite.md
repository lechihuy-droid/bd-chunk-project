# SAFEHARNESS L1-L4 Lite

This is the rule-based lite version of the Harness Hub runtime defense stack. It does not call an LLM, does not require an API key, and does not add packages. The LLM Judge and Causal Diagnostics tiers are intentionally deferred.

## L1 INFORM

- File: `services/inform.py`
- Entry point: `sanitize_text(s) -> (clean, findings)`
- Behavior:
  - NFKC normalizes input text.
  - Removes zero-width controls: U+200B..U+200D, U+FEFF, U+2060.
  - Removes bidi controls: U+202A..U+202E, U+2066..U+2069.
  - Detects prompt-injection indicators with case-insensitive regex rules, including previous-instruction overrides, system prompt references, BCC, exfiltration, secret reveal requests, and long base64-like blobs.
- Job integration:
  - `create_job` sanitizes the brief before storing it.
  - `inform_findings` is stored on the job record and surfaced in the UI.
  - L1 never blocks job creation.

## L2 VERIFY

- File: `services/verify.py`
- Entry point: `rule_check(job)`
- Decisions:
  - `deny` when L1 has an injection-pattern finding.
  - `deny` when the job command, diff, or recorded tier has destructive content and `allow_override` is not set.
  - `warn` for `execute` or `network` tier.
  - `allow` otherwise.
- Job integration:
  - `approve` records `l2_decision`, `l2_reasons`, and `l2_warnings`.
  - L2 deny returns HTTP 400 and raises governance degradation.

## L3 CONSTRAIN

- Files: `config.py`, `services/gitjobs.py`, `services/governance.py`
- Config:
  - `JOB_BLOCKED_TIERS = ["destructive"]`
  - `JOB_TTL_SECONDS = 3600`
- Enforcement:
  - `approve` blocks expired jobs.
  - `approve` blocks jobs whose `max_tier` is in the effective blocked tier set unless `allow_override` is true.
  - Existing run cap and brief HMAC stay in place.
  - Work remains scoped to each job worktree and branch.

## L4 CORRECT

- File: `services/governance.py`
- State file: `harness/hub/.cache/governance.json`
- Config:
  - `GOV_RECOVERY_STEPS = 5`
- Degradation:
  - Level 0: `JOB_BLOCKED_TIERS`
  - Level 1: same as level 0
  - Level 2: add `network`
  - Level 3: add `execute`
  - Level 4: block every tier except `read_only`
- Recovery:
  - L2 deny raises degradation by one level, capped at 4.
  - A job that finishes flagged raises degradation by one level, capped at 4.
  - Each clean finished job increments the clean streak.
  - After `GOV_RECOVERY_STEPS` consecutive clean jobs, degradation lowers by one level.

## API and UI

- Endpoint: `GET /api/governance`
- Response fields:
  - `degradation`
  - `blocked_tiers`
  - `recent_denials`
  - `recent_findings`
- UI:
  - Dashboard includes a Governance card.
  - Job detail shows L1 findings, L2 decision and reasons, approval block reasons, and flagged finish reasons.
  - `#/governance` lists recent denials and recent L1 findings.
