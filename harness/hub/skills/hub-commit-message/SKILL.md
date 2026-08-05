---
name: hub-commit-message
description: Write a concise, truthful conventional commit message from a completed change.
---

# Commit message

Use the completed diff and verification results as the source of truth. Do not
invent scope, impact, or test results.

1. Identify the user-visible or maintenance outcome, not the implementation detail.
2. Choose the narrowest conventional type: `feat`, `fix`, `test`, `docs`,
   `refactor`, `chore`, or `build`.
3. Write an imperative subject under 72 characters: `type: outcome`.
4. Add a body only when the why, risk, or compatibility implication is not clear
   from the subject. Wrap it as short plain paragraphs.
5. If verification was not run, do not imply it passed; mention that separately
   from the commit message when asked for a handoff.

Return one proposed message unless alternatives are explicitly requested.
