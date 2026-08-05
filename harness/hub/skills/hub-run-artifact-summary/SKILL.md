---
name: hub-run-artifact-summary
description: Turn a hub run's artifacts and events into a concise evidence-based handoff.
---

# Run artifact handoff

Use this when a hub run has produced artifacts, events, or validation output.
Read the available run record and artifact contents before summarising; treat
missing records as unknown, not as success.

Structure the handoff as:

1. **Outcome** — completed, blocked, failed, or awaiting approval.
2. **Delivered** — artifact titles or concrete outputs, each with one-line purpose.
3. **Evidence** — validations, tests, or event results actually present in the run.
4. **Open items** — failures, pending approvals, assumptions, and unverified claims.
5. **Next action** — one specific action, only when the run is not complete.

Keep it factual. Link or name artifacts when identifiers are available. Never
describe generated prose as a verified result unless a recorded check supports it.
