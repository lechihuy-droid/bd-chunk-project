---
name: testing-strategy
description: Design testing strategies using the testing pyramid and component-specific coverage for APIs, data pipelines, frontends, and infrastructure.
---

# Testing Strategy

Use this skill to plan evidence-producing tests for a change, system, or
component without confusing coverage volume with confidence.

1. Define the behaviours, risks, and failure modes that need evidence.
2. Identify the component type: business logic, API, data flow, interface, or
   infrastructure.
3. Start with fast, focused tests for deterministic rules and edge cases.
4. Add integration tests where boundaries, contracts, or persistence can fail.
5. Reserve end-to-end coverage for critical user journeys and costly regressions.
6. Keep the test mix aligned with the testing pyramid and maintenance cost.
7. Specify normal, boundary, invalid, and recovery scenarios.
8. Include authorization, concurrency, time, and partial-failure cases when
   they affect correctness.
9. Define representative inputs, fixtures, and expected observable outcomes.
10. Identify contracts between components and the evidence needed to protect them.
11. Separate stable product assertions from brittle implementation details.
12. Include regression coverage for known defects and high-risk changes.
13. State non-functional checks for performance, resilience, or accessibility
   when the requirements call for them.
14. Prioritize the smallest set of tests that meaningfully reduces risk.
15. Mark gaps, assumptions, and untestable claims for follow-up.

Do not claim a test strategy proves behaviour that has not been evidenced.
