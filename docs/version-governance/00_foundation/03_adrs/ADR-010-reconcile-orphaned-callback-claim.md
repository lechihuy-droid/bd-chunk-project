# ADR-010 — Reconcile Must Close Runs Behind an Orphaned Callback Claim

**Status:** Accepted
**Scope:** Version Governance — Run Reconciliation
**Decision date:** 2026-08-03

## Context

`[SD §4.1]` introduced reconciliation so `GET /runs/{id}` can close a run stuck in `RUNNING` when the
runtime backend reports a terminal status but no callback ever arrived. The original condition was:

```text
nếu st.canonical thuộc {SUCCEEDED, FAILED, CANCELLED} và chưa có callback:
    → đánh dấu run theo st, error_code = CALLBACK_LOST
```

`[SD §4.2]` implements callback idempotency with a claim-then-update pattern: the callback handler
first `INSERT`s a `runtime_callback` row (`response_body IS NULL`), does the work (write blob, insert
`artifact_revision`), and only then `UPDATE`s `response_body` at the end of the same handler
invocation. If the process handling that callback dies between the INSERT and the final UPDATE —
container killed, unhandled exception, lost DB connection — the row survives forever with
`response_body IS NULL`.

The existing reconcile condition treats "a `runtime_callback` row exists" as proof the callback is
being handled and defers to it unconditionally. It cannot distinguish a claim that is genuinely being
processed right now from a claim whose owning process is gone. The run is then stuck `RUNNING`
permanently — the exact failure mode `[SD §4.1]` was written to prevent, just triggered from an
orphaned claim instead of a missing row. This violates DoD #12 (the POC demo must be repeatable): a
run that gets unlucky with a crash mid-callback can never be retried.

A test capturing the desired behavior already existed as `xfail`:
`harness/version-governance/app/tests/test_reconcile_orphaned_claim.py`.

## Decision

`reconcile()` closes a `RUNNING` run when the runtime reports a terminal status **and** the callback
has not genuinely completed, where "not genuinely completed" now covers two cases:

1. No `runtime_callback` row exists at all (unchanged from `[SD §4.1]`).
2. A `runtime_callback` row exists, `response_body IS NULL`, **and** `received_at` is older than a
   configurable grace period (default **120 seconds**, env `VGOV_CALLBACK_GRACE_SECONDS`).

```text
nếu st.canonical thuộc {SUCCEEDED, FAILED, CANCELLED}:
    callback = lookup runtime_callback theo correlation_id
    mồ_côi = callback là None
              hoặc (callback.response_body IS NULL
                    và now() - callback.received_at > VGOV_CALLBACK_GRACE_SECONDS)
    nếu mồ_côi:
        → đánh dấu run theo st, error_code = CALLBACK_LOST
        → KHÔNG tự tạo artifact_revision (không đổi so với [SD §4.1])
```

The grace period exists because a claim with `response_body IS NULL` is also the **normal** in-flight
state of a callback that is legitimately still running: it is between the INSERT claim and the final
UPDATE while it writes the output blob to MinIO and inserts the `artifact_revision`. Closing the run
the instant a claim is observed would race a healthy callback and yank the run out from under it —
the callback's later `UPDATE runtime_callback SET response_body = ...` would then be updating a row
whose run has already been marked `CALLBACK_LOST` and possibly retried.

This ADR does **not** introduce a background sweep. Reconciliation, orphaned-claim or not, still only
runs synchronously inside `GET /runs/{id}` — a periodic job that scans for stale claims proactively is
out of scope for the POC.

## Consequences

### Positive

- A crash mid-callback-processing no longer strands a run in `RUNNING` forever; polling
  `GET /runs/{id}` eventually closes it as `CALLBACK_LOST`, matching the existing recovery path
  (manifest is preserved, run must be retried).
- The fix is a pure extension of the existing reconcile predicate — no new tables, no new
  side-channel state, no change to the 13-step freeze-then-execute order or to callback idempotency
  in `[SD §4.2]`.
- `artifact_revision` creation stays exclusively inside the callback handler; reconcile never creates
  one, in either orphan case — consistent with `[SD §4.1]`.

### Trade-offs

- A truly orphaned claim is not detected instantly — it waits out the full grace period before the
  next `GET /runs/{id}` call can close it. For the POC this is acceptable: no SLA on recovery latency
  exists yet, and the alternative (no grace period) risks closing a healthy in-flight callback instead.
- A fixed grace period cannot truly distinguish "callback is just slow" from "callback's process is
  dead" — it is a heuristic. A callback that legitimately takes longer than the grace period (e.g. a
  very large blob upload) would be marked `CALLBACK_LOST` even though it is still working, and its
  eventual `UPDATE` would land on a run that has already moved on. Picking 120 seconds is a judgment
  call, not a measured bound; it may need tuning once real payload sizes are observed.
- Because there is still no background sweep, a genuinely orphaned run stays `RUNNING` until someone
  calls `GET /runs/{id}` on it — the POC continues to rely on user-driven polling to trigger recovery.

## References

- `harness/version-governance/50_sdd/02_system_design.md` §4.1, §4.2
- `harness/version-governance/app/services/run_service.py`
- `harness/version-governance/app/tests/test_reconcile_orphaned_claim.py`
