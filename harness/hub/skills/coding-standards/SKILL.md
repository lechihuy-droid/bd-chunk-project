---
name: coding-standards
description: Apply cross-project coding standards for naming, immutability, error handling, and avoidance of common code smells.
---

# Coding Standards

Use this skill to assess or improve code clarity, correctness, and long-term
maintainability without imposing a framework-specific style.

1. Name values, functions, and types for their domain role and observable intent.
2. Keep each unit focused on one coherent responsibility.
3. Make data flow and mutation explicit; prefer immutable transformations where
   they improve reasoning.
4. Keep interfaces small and expose only what callers need.
5. Validate inputs at boundaries and preserve useful error context.
6. Handle expected failure paths deliberately instead of swallowing errors.
7. Use types, assertions, and invariants to express important constraints.
8. Avoid hidden state, surprising side effects, and implicit coupling.
9. Replace duplicated logic when it represents one shared rule, not merely a
   similar shape.
10. Avoid premature abstraction, deeply nested control flow, and cleverness
    that obscures intent.
11. Keep comments for rationale, constraints, and non-obvious decisions.
12. Keep formatting and conventions consistent with surrounding code.
13. Treat security-sensitive values and authorization decisions as explicit
    concerns.
14. Prefer small, reviewable changes with clear behavioural intent.
15. Call out incompatible conventions or missing context instead of guessing.

Do not describe code as clean, correct, or secure when the available evidence is incomplete.
