---
name: hub-diff-review
description: Review a focused code diff for correctness, regressions, and missing tests.
---

# Focused diff review

Use this when asked to review a change. Inspect the diff and enough surrounding
code to understand each changed behavior; do not review unrelated code.

1. State the intended behavior in one sentence before judging it.
2. Check every changed branch, input, and error path against that behavior.
3. Look for regressions at boundaries: caller/callee contracts, persisted data,
   permissions, paths, and configuration defaults.
4. Verify tests cover the new behavior and its most likely failure case. If a
   test cannot run, say what was not verified.
5. Report only actionable findings, ordered by severity. Each finding needs a
   file and line (when available), the concrete failure mode, and a proposed fix.

If no issue is found, say that explicitly and name the checks performed. Do not
claim the change is safe when the diff or required context is unavailable.
