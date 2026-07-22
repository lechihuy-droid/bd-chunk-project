# Awesome LLM Apps — Cross-Layer Reference Note

## Status

- **Priority:** P1
- **Harness Levels:** Cross-layer — L1 UI, L2 Runtime, L3 Tools / MCP, L5 Skills / Evaluation, L6 AgentOps / Governance
- **Research Type:** Pattern catalog and implementation reference
- **Adoption Status:** Reference only — do not fork as the BD Harness foundation
- **Official Repo:** https://github.com/Shubhamsaboo/awesome-llm-apps
- **Reviewed Snapshot:** `0526b20cbfc48a384b02019d0c816a5ea1738f1e`
- **Overall Fit for BD Harness:** 8.0 / 10 as a pattern source; below 5 / 10 as a production platform foundation

## Decision

Use Awesome LLM Apps as a **pattern mine and POC catalog**.

Do not treat it as a unified framework, runtime, control plane, or production-ready enterprise platform.

The repository is valuable because it contains many self-contained examples across agents, RAG, MCP, agent skills, generative UI, always-on execution, and multi-agent collaboration. Its main limitation is that each example owns its own stack, dependencies, model integration, state handling, and deployment assumptions.

```text
Awesome LLM Apps
    -> discover implementation patterns
    -> extract interfaces and failure modes
    -> rebuild selected patterns behind BD Harness contracts
    -> validate with governance, traceability, evaluation, and human gates
```

## Why this matters for BD Harness

BD Harness needs broad use-case coverage without allowing every use case to define its own runtime architecture.

Awesome LLM Apps can provide concrete examples for:

- agent loops
- skill packaging
- skill evaluation
- multi-agent coordination
- MCP tool routing
- RAG diagnostics
- scheduled and always-on agents
- generative UI
- audit and trust-gate concepts

The correct use is to extract reusable concepts and convert them into controlled Harness contracts.

## Priority Patterns to Study

### P0 — Self-improving skill loop

Reference area:

- `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/`
- `agent_skills/`

Core pattern:

```text
Executor
    -> Evaluator / Analyst
    -> Mutation Proposal
    -> Re-evaluation
    -> Promote only when score improves
```

What BD Harness should extract:

- immutable skill version
- evaluation run
- failure evidence
- mutation proposal
- before / after score comparison
- promotion decision
- rollback reference

BD Harness equivalent:

- generate one BD section
- evaluate traceability, completeness, rule compliance, and review findings
- diagnose the failure
- propose prompt / rule / workflow changes
- rerun on a controlled evaluation set
- promote only after measurable improvement and human approval

Do not copy:

- unconstrained self-modification
- direct promotion without review
- evaluation based only on model judgment

### P0 — Agent skill quality gates

Reference area:

- `.github/workflows/skill-evals.yml`
- `agent_skills/evals/`

Useful checks demonstrated by the repository:

- deterministic evaluations
- strict skill linting
- security and supply-chain scanning
- trigger and routing evaluations

What BD Harness should extract:

```text
Skill Package
    -> Schema Validation
    -> Static Safety Scan
    -> Trigger / Routing Eval
    -> Deterministic Functional Eval
    -> Human Review
    -> Registry Promotion
```

Required BD Harness outputs:

- `SkillManifest`
- `SkillEvalSuite`
- `SkillEvalResult`
- `SecurityFinding`
- `PromotionDecision`

This is one of the strongest patterns in the repository for the planned Skill Registry.

### P0 — Capability-bound MCP routing

Reference area:

- multi-MCP agent routing examples
- MCP-based specialized agents

Useful concept:

Each specialized agent receives only the MCP servers and tools relevant to its domain instead of exposing every tool to one universal agent.

What BD Harness should extract:

- agent-to-capability mapping
- capability-to-tool mapping
- tool allowlist per workflow stage
- explicit tool discovery
- tool invocation audit event
- deny-by-default behavior

BD Harness target:

```text
Agent Role
    -> Required Capability
    -> Policy Decision
    -> Approved Tool Set
    -> Sandboxed Execution
    -> Audited Result
```

Do not copy:

- keyword-only agent routing
- launching arbitrary MCP packages with `npx -y` during runtime
- direct filesystem access without workspace boundaries
- tool access without approval, quota, or policy evaluation

### P0 — RAG failure diagnostics taxonomy

Reference area:

- `rag_tutorials/rag_failure_diagnostics_clinic/`

Useful failure classes include:

- retrieval hallucination
- chunk boundary failure
- stale index
- router misalignment
- memory leakage
- evaluation blind spot
- multi-agent interference

What BD Harness should extract:

- standard failure taxonomy
- incident evidence format
- root-cause classification
- recommended remediation
- regression-test linkage

BD Harness equivalent failure classes should cover:

- source unit not retrieved
- wrong requirement chunk selected
- provenance lost
- ontology label mismatch
- BD mapping rule mismatch
- generated section unsupported by source
- reviewer correction not incorporated
- stale source version

This pattern should feed the BD Harness error database and evaluation dataset.

### P1 — Generative UI and artifact workspace

Reference area:

- `generative_ui_agents/`
- generative UI starter projects
- dashboard and canvas agents

What BD Harness should study:

- agent output rendered as interactive components rather than plain chat
- persistent workspace separate from conversation history
- editable generated artifacts
- UI events sent back to the agent runtime
- component-level loading, error, and approval states

BD Harness equivalent:

- requirement evidence panel
- source chunk viewer
- generated BD section canvas
- validation findings panel
- human approval controls
- revision comparison

Adoption rule:

Use the UI interaction patterns, but keep BD Harness state and governance in the backend runtime. The frontend must not become the source of truth.

### P1 — Always-on and scheduled agents

Reference area:

- `always_on_agents/`

What BD Harness should study:

- scheduled execution
- repeated polling
- change detection
- notification only when a meaningful condition is met
- persistent run state

Potential BD Harness use cases:

- detect newly uploaded RD or QA files
- detect changed source versions
- rerun impacted traceability checks
- detect overdue review gates
- generate daily project health summaries

Required controls:

- idempotency key
- schedule profile
- last successful checkpoint
- change fingerprint
- retry policy
- notification policy
- run budget

### P1 — Trust gate and tamper-evident audit concepts

Reference area:

- `advanced_ai_agents/multi_agent_apps/trust_gated_agent_team/`

Useful concepts:

- agent identity
- minimum trust threshold
- explicit execution gate
- hash-linked audit entries
- verification of audit-chain integrity

What BD Harness should extract:

- execution identity
- policy verdict
- input / output digest
- previous-event linkage
- immutable audit event schema

Do not copy as a security design:

- static trust scores declared in source code
- local in-memory identity registry
- in-memory audit storage
- hash chaining without external signing or immutable persistence

For BD Harness, trust must come from policy, identity, permissions, validation history, and approval state rather than an arbitrary numeric score.

### P2 — Framework crash courses and application examples

Reference areas include examples for OpenAI Agents SDK, Google ADK, CrewAI, LangGraph, and other frameworks.

Use these examples for:

- adapter research
- conformance testing
- framework comparison
- onboarding exercises
- provider migration experiments

Do not let framework-specific examples define the core architecture.

BD Harness must remain framework-independent at the contract level.

## Mapping to BD Harness Layers

| Awesome LLM Apps pattern | BD Harness layer | Extraction target |
|---|---|---|
| Generative UI | L1 Experience | Artifact canvas, evidence panel, approval UI |
| Agent loops | L2 Runtime | Planner / executor / evaluator run contract |
| Always-on agents | L2 Runtime | Schedule profile, checkpoint, idempotency |
| Multi-MCP routing | L3 Tools / Integration | Capability registry and policy-bound tool access |
| RAG diagnostics | L4 Context / Knowledge | Failure taxonomy and retrieval evidence |
| Agent skills | L5 Skills | Skill manifest, versioning, registry lifecycle |
| Skill eval workflow | L5 Evaluation | Deterministic tests, routing eval, promotion gate |
| Trust-gated team | L6 Governance | Identity, policy verdict, audit event |
| Hash-linked audit log | L6 AgentOps | Tamper-evident event linkage concept |

## Patterns to Reject or Replace

The following patterns are acceptable in demos but should not enter BD Harness architecture unchanged:

- Streamlit session state as runtime state
- API keys entered directly into application sidebars
- direct provider SDK calls from every application
- hard-coded model identifiers
- keyword-only routing
- unrestricted MCP server spawning
- runtime installation through `npx -y`
- broad filesystem access
- static agent trust scores
- in-memory audit logs
- duplicated dependency management per use case
- missing centralized policy enforcement
- missing cost, token, and tool-call budgets
- missing durable checkpoints and replay support
- model-only evaluation without deterministic evidence

## BD Harness Extraction Backlog

### REF-01 — Skill evaluation contract

Create a framework-independent schema for:

- skill metadata
- test case
- expected behavior
- actual result
- deterministic score
- model-judge score when needed
- security findings
- promotion decision

Success condition:

A skill cannot enter the approved registry without passing schema, safety, routing, functional, and human-review gates.

### REF-02 — Capability-bound tool router

Create a policy-controlled mapping:

```text
Workflow Stage + Agent Role + Project Policy
    -> Approved Capabilities
    -> Approved Tools
    -> Execution Constraints
```

Success condition:

An agent can discover and invoke only tools explicitly authorized for the current stage and project.

### REF-03 — BD failure taxonomy

Adapt the RAG diagnostics approach into a BD-specific failure catalog.

Initial classes:

- parsing failure
- source-unit failure
- retrieval failure
- provenance failure
- ontology failure
- mapping failure
- generation failure
- evaluation failure
- review-state failure
- stale-version failure

Success condition:

Every failed evaluation or human rejection can be assigned a stable failure code and linked to evidence and regression tests.

### REF-04 — Generative artifact UI contract

Define backend-owned artifact state for:

- source evidence
- generated BD section
- validation finding
- proposed revision
- reviewer decision

Success condition:

The same artifact state can be rendered in chat, canvas, or document UI without changing workflow semantics.

### REF-05 — Scheduled agent run profile

Define:

- trigger type
- schedule
- project scope
- checkpoint
- change fingerprint
- retry policy
- notification rule
- cost ceiling

Success condition:

Repeated runs are idempotent and notify users only when a relevant state change occurs.

### REF-06 — Audit event schema

Define an immutable event containing:

- run ID
- actor / agent identity
- policy verdict
- workflow stage
- action
- tool
- input digest
- output digest
- source references
- previous-event reference
- timestamp
- review state

Success condition:

A BD artifact can be traced from source ingestion through generation, evaluation, revision, and human approval.

## Adoption Rules

1. Do not fork Awesome LLM Apps as the BD Harness base repository.
2. Do not add it as a runtime dependency.
3. Extract one pattern at a time behind a BD Harness interface.
4. Reimplement patterns with centralized policy, tracing, evaluation, and configuration.
5. Require a POC and architecture review before adopting a pattern.
6. Keep model and framework integrations behind adapters.
7. Preserve Apache 2.0 attribution when code is copied or materially adapted.
8. Promote only patterns that improve traceability, controllability, or delivery quality.

## Recommended Study Order

1. Agent skill evaluation workflow
2. Self-improving skill loop
3. Multi-MCP capability routing
4. RAG failure diagnostics
5. Generative artifact UI
6. Always-on execution
7. Trust and audit concepts
8. Framework adapter examples

## Initial Recommendation

Study selectively and convert the strongest examples into BD Harness contracts and POCs.

The highest-value references are:

- skill quality gates
- controlled self-improvement
- capability-bound MCP routing
- RAG failure taxonomy
- generative artifact UI
- scheduled execution profiles
- auditable agent actions

The repository should remain an external reference catalog. BD Harness should own the runtime, policy model, schemas, evaluation system, traceability model, and human approval flow.