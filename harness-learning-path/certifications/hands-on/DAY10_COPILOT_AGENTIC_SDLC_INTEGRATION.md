# DAY 10 — HANDS-ON 4: COPILOT + AGENTIC SDLC INTEGRATION

> Integrated track: AI-103 + GH-300  
> Goal: use a coding-agent mental model to implement, test, review, and govern the agent system designed in Days 7–9

---

# 1. Session Outcome

By the end of Day 10, you should be able to explain two layers clearly:

```text
Layer A
Application Agent System
RD Parser / Validator / Builder / Reviewer

Layer B
Coding Agent Workflow
Copilot helps build, test, review, and maintain Layer A
```

The central distinction is:

```text
Agent being built
≠
Agent building it
```

This session closes the AI-103 + GH-300 integrated block and prepares the architecture shift into AB-100.

---

# 2. Start from Engineering Artifacts, Not a Vague Prompt

The coding agent should receive structured engineering context.

Input package:

```text
Architecture
+ Agent specs
+ Tool/MCP contracts
+ Artifact schemas
+ Workflow state
+ Routing rules
+ Guardrails
+ Evaluation criteria
+ Repository conventions
```

Weak instruction:

> Build the RD-to-BD AI system.

Better instruction:

> Implement the supplied workflow and contracts in the existing repository. Keep deterministic routing outside model prompts. Add tests for contract validation, source fidelity, reviewer FAIL→revision, tool timeout, and human-interrupt behavior. Do not introduce new external dependencies without documenting the reason.

---

# 3. Repository Context Engineering

A coding agent performs better when repository context is deliberate.

Useful context:

```text
AGENTS.md / repo instructions
Architecture docs
Relevant source files
Tests
Schemas/contracts
Dependency configuration
CI rules
Security constraints
```

Avoid dumping the entire repository into context without purpose.

## Principle

> Context should be sufficient, relevant, trustworthy, and scoped.

More context is not automatically better context.

---

# 4. Task Decomposition

Do not ask one giant coding task if clean decomposition is available.

Example:

```text
Task 1 — implement contracts
Task 2 — implement tool adapters
Task 3 — implement Parser agent adapter
Task 4 — implement workflow runtime
Task 5 — add tests
Task 6 — security/review pass
```

Each task should have:

- goal;
- allowed scope;
- expected artifact;
- validation criteria;
- stop condition.

---

# 5. When to Use a Subagent

Potential development subagents:

```text
Primary Coding Agent
├── Test Specialist
├── Security Reviewer
└── Documentation Reviewer
```

Use them only when specialization/context separation helps.

Example:

A security-review subagent receives:

- permission model;
- MCP/tool contracts;
- modified code;
- security checklist.

It should not need the full unrelated business context.

---

# 6. Implementation Sequence

Recommended sequence:

```text
Contracts first
      ↓
Deterministic validators
      ↓
Tool adapters
      ↓
Agent adapters
      ↓
Workflow runtime
      ↓
Evaluation hooks
      ↓
Observability
      ↓
Tests
```

Why?

Because contracts and deterministic boundaries create stable interfaces before model behavior is connected.

---

# 7. Test Pyramid for Agentic Software

Do not test only the final LLM output.

## Unit tests

For deterministic code:

- schema validators;
- routing;
- retry logic;
- tool adapters;
- permission checks.

## Contract tests

Verify inputs/outputs between components.

## Agent behavior tests

Use fixed scenarios to check:

- source fidelity;
- tool choice;
- unsupported claims;
- uncertainty handling.

## Workflow tests

Check:

- PASS path;
- FAIL→revision path;
- timeout path;
- partial failure;
- human interrupt/resume.

## Evaluation dataset

Maintain representative examples for regression.

---

# 8. Coding Agent Review Loop

A useful coding-agent loop:

```text
Implement
 ↓
Run Tests
 ↓
Inspect Failure
 ↓
Revise
 ↓
Run Tests
 ↓
Request Review
```

But there must be a stop condition.

Avoid infinite autonomous repair.

Examples:

```text
max iteration count
unresolved security finding
architecture mismatch
ambiguous requirement
human approval required
```

---

# 9. Security Review

Review at least:

```text
Secrets
Permissions
MCP/tool access
Prompt injection boundaries
Untrusted retrieved content
File write scope
Network access
Logging of sensitive data
Dependency changes
```

## Key principle

> A coding agent should receive the minimum permissions required for the development task.

Likewise, the application agent should receive the minimum runtime permissions required for its business role.

These are two separate permission models.

---

# 10. AI-Generated Code Is Not Evidence of Correctness

Do not allow this circular pattern:

```text
Agent writes code
 ↓
Same agent says code looks correct
 ↓
Merge
```

Stronger validation:

```text
Generated Change
 ↓
Automated Tests
 ↓
Static/Security Checks
 ↓
Independent Review
 ↓
Human Decision
```

The reviewer can use AI assistance, but the evidence should include executable checks and explicit criteria.

---

# 11. Change Scope Control

Coding agents can over-modify repositories.

Protect scope with:

- explicit allowed files/directories;
- public-interface constraints;
- dependency-change restrictions;
- architectural rules;
- small commits/tasks;
- reviewable diffs.

Example instruction:

> Modify only `src/agents/parser`, `src/contracts`, and related tests. Do not change deployment configuration or package versions.

---

# 12. Traceability from Requirement to Code

For the capstone, maintain:

```text
Requirement / Learning Objective
        ↓
Architecture Decision
        ↓
Agent / Workflow Spec
        ↓
Implementation Change
        ↓
Test
        ↓
Review Result
```

This mirrors the traceability principle inside the RD Parser itself.

The system should not lose provenance merely because AI generated the implementation.

---

# 13. Versioning

Version separately where useful:

```text
Workflow version
Agent spec version
Prompt/instruction version
Tool contract version
Schema version
Model config version
Evaluation dataset version
```

A code commit alone may not capture every runtime behavior change.

This becomes important later in AB-100 governance and ALM.

---

# 14. Pull Request Mental Model

The coding agent's work should become a reviewable change, not an invisible workspace mutation.

PR should communicate:

```text
Why
What changed
Architecture impact
Tests
Security impact
Known limitations
Evaluation evidence
```

This creates the bridge from AI-assisted coding to governed engineering.

---

# 15. Example End-to-End Development Flow

```text
1. Read architecture/spec
2. Inspect repository instructions
3. Plan scoped implementation
4. Implement contracts
5. Add deterministic validation
6. Add tool/MCP adapters
7. Add agent integration
8. Add workflow routing
9. Run tests
10. Fix bounded failures
11. Run security/review pass
12. Produce reviewable diff/PR
13. Human approval
```

This is the practical synthesis of GH-300 around an AI-103-style agent application.

---

# 16. Voice Simulation

No Copilot license/API is required to learn the architecture.

Run this as a conversation.

## Round A — Architect

You provide:

- one agent spec;
- one workflow diagram;
- one tool contract.

## Round B — Coding Agent

State the implementation plan.

## Round C — Reviewer

Challenge:

- scope creep;
- missing tests;
- insecure tool permission;
- unclear failure handling.

## Round D — Correction

Revise the engineering plan.

The goal is to practice **context-driven development**, not syntax generation.

---

# 17. Scenario Drill

### Scenario 1
Coding agent modifies 25 unrelated files while implementing one parser contract.

Problem:

> Scope control failure.

### Scenario 2
All tests pass, but no test checks source fidelity.

Problem:

> Test coverage does not represent agent-quality requirements.

### Scenario 3
Application agent has read-only document access, but coding agent has production-deployment credentials.

Question:

> Are these permissions equivalent?

No. Development and runtime identities are different trust boundaries.

### Scenario 4
A reviewer agent says "looks good" but no automated tests ran.

Problem:

> Weak evidence.

### Scenario 5
Prompt changed but code did not.

Question:

> Can behavior still change?

Yes. Prompt/instruction/model configuration are behavior-bearing artifacts and should be versioned/evaluated.

---

# 18. Day 10 PASS Gate

Explain without notes:

1. Application agent vs coding agent.
2. Why context engineering matters for implementation.
3. What should be in the coding agent's context package.
4. Why tasks should be scoped/decomposed.
5. When a subagent helps.
6. What should be deterministic unit-tested.
7. What needs agent/workflow evaluation.
8. Why AI self-review is insufficient by itself.
9. Why development permissions differ from runtime permissions.
10. Why prompts/model config require versioning alongside code.

## PASS

Pass at **8/10** plus an end-to-end engineering plan for implementing the Day 9 workflow.

---

# 19. Deliverable

```text
AGENTIC_SDLC_PLAN
├── context package
├── task decomposition
├── coding-agent instructions
├── subagent decisions
├── implementation sequence
├── test strategy
├── security review
├── change scope
├── versioning
└── PR/review checklist
```

---

# 20. Transition to AB-100

After Day 10, the mental model changes level.

So far:

```text
AI-103
How do I build and operate an AI application/agent?

GH-300
How do I use AI capabilities to engineer software effectively?
```

Next:

```text
AB-100
What agentic business solution should an enterprise choose,
how should it be architected, integrated, governed, deployed,
and measured for business value?
```

Day 11 begins the Solution Architect phase.
