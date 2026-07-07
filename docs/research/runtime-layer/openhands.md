# OpenHands Implementation Research Note

## Status

- **Priority:** P1+
- **Harness Level:** L2 — Agent Runtime / Orchestration
- **Research Type:** Runtime architecture study
- **Adoption Status:** Research → Architecture extraction candidate
- **Official Repo:** https://github.com/All-Hands-AI/OpenHands
- **Docs:** https://docs.all-hands.dev/
- **Overall Score:** 8.8 / 10

## Why this matters for BD Harness

OpenHands should be studied as a reference implementation for a full coding-agent runtime.

The goal is not to adopt OpenHands directly. The goal is to extract runtime design patterns that can inform BD Harness architecture:

- agent loop
- planner / executor separation
- event system
- sandbox and workspace management
- tool routing
- multi-step task execution
- human-in-the-loop interaction
- runtime state management

## Fit to Harness Architecture

OpenHands belongs to L2 Runtime / Orchestration.

BD Harness needs a smaller and more controlled runtime, but OpenHands is useful as a concrete architecture reference for how a production coding agent is organized.

```text
OpenHands Reference Runtime
    ↓ extract patterns
BD Harness Runtime
    ↓
Planner / Executor / Tool Router / Sandbox / Workspace / Review Gate
```

## Capabilities to study

### 1. Agent loop

Study how OpenHands structures repeated reasoning / action / observation cycles.

Key question:

- Which parts are reusable for BD workflows where the agent generates design documents rather than code?

### 2. Planner / executor separation

Study how task planning is separated from action execution.

BD Harness equivalent:

- Planner: decompose RD / QA into BD work packages.
- Executor: generate, validate, and revise each BD section.
- Reviewer: compare output against requirement chunks and design rules.

### 3. Workspace management

Study how the runtime handles files and repository workspace access.

BD Harness equivalent:

- project workspace
- input documents
- extracted chunks
- generated artifacts
- review records
- Git-tracked design outputs

### 4. Sandbox and tool execution

Study how sandbox boundaries are modeled.

BD Harness equivalent:

- no direct production DB access
- controlled file reads/writes
- controlled Git operations
- controlled cloud/document connectors
- reproducible execution environment

### 5. Event system and runtime state

Study how runtime events are emitted and consumed.

BD Harness equivalent:

- run started
- document parsed
- retrieval completed
- design generated
- evaluation failed
- human review requested
- artifact committed

These events should later connect to Langfuse or another AgentOps backend.

### 6. Human-in-the-loop

Study how user intervention, approval, or correction is represented.

BD Harness equivalent:

- BA review gate
- PM approval gate
- architect review gate
- client feedback incorporation

## BD Harness POC Plan

### POC-1: Runtime pattern extraction

Goal: read OpenHands architecture and map its components to BD Harness.

Output:

- runtime component map
- reusable patterns
- patterns to reject
- simplified BD Harness runtime diagram

### POC-2: Minimal planner / executor skeleton

Goal: build a small BD Harness skeleton inspired by OpenHands patterns.

Scope:

1. Planner receives one RD feature.
2. Planner creates BD work items.
3. Executor generates one BD section.
4. Evaluator validates against source chunks.
5. Human gate records accept/reject.

Success criteria:

- Runtime state is explicit.
- Steps are observable.
- Tool access is controlled.
- Output is traceable to source chunks.

### POC-3: Runtime event schema

Goal: design event schema compatible with Langfuse / OpenTelemetry.

Success criteria:

- Every planner/executor/tool/review event has a stable schema.
- Events can be converted into observability traces.
- Events can be replayed or audited.

## Open Questions

- Which OpenHands runtime components are too heavy for BD Harness?
- Can the planner/executor pattern be simplified for document-generation workflows?
- How should BD Harness represent workspace state?
- Should tool execution be synchronous, queued, or event-driven?
- What is the minimum runtime state needed for traceability and replay?

## Initial Recommendation

Study deeply, but do not adopt directly.

OpenHands is a strong L2 runtime reference. Its main value is architectural: it can teach how a real agent runtime organizes planning, execution, tools, workspace, sandbox, and human interaction. BD Harness should extract the patterns and build a smaller, domain-specific runtime.
