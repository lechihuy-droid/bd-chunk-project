# DAY 9 — HANDS-ON 3: WORKFLOW + MULTI-AGENT ORCHESTRATION

> Integrated track: AI-103 + GH-300  
> Goal: move from one agent to a controlled workflow with explicit boundaries

---

# 1. Session Outcome

By the end of Day 9, you should be able to design a workflow where each step is classified deliberately as:

```text
Agent
Tool
Deterministic Node
Validator
Human Review
```

The target architecture is not "make everything an agent".

It is:

```text
Use deterministic execution where possible
+
Use model reasoning where necessary
```

---

# 2. Starting Pipeline

Use this capstone:

```text
RD
 ↓
Parser
 ↓
Validator
 ↓
Ontology Tagger
 ↓
Builder
 ↓
Reviewer
 ↓
GO / NO-GO
```

For each component, ask:

```text
Does it need reasoning?
Does it need autonomy?
Does it use tools?
Does it iterate?
Does it require memory?
Does it pursue a goal?
Can deterministic code solve it reliably?
```

---

# 3. Component Classification

## Parser

Often needs semantic interpretation.

Likely:

> Agent or model-powered node.

## Validator

Split into two layers.

```text
Structural Validator
→ deterministic

Semantic Validator
→ may need model reasoning
```

## Ontology Tagger

Could be:

- deterministic lookup when ontology mapping is exact;
- model-powered classification when language is ambiguous.

Do not decide by component name—decide by behavior.

## Builder

Usually requires reasoning and synthesis.

Likely:

> Agent.

## Reviewer

If evaluation requires semantic judgment, it can be a reviewing agent.

If the gate is an exact threshold/rule, the gate itself should remain deterministic.

---

# 4. Workflow Runtime vs Orchestrator Agent

Critical architecture distinction:

```text
Workflow Runtime
├── node execution
├── state transitions
├── retries
├── timeout
├── persistence
├── interrupts
└── deterministic routing

Orchestrator Agent
└── reasoning-based decisions when needed
```

## Rule

> Runtime owns execution semantics. The LLM should not own control logic that can be represented deterministically.

Bad pattern:

```text
LLM decides every next step
LLM decides retry
LLM decides timeout
LLM decides whether state is valid
```

Better pattern:

```text
Runtime handles mechanics
Agent handles ambiguity/reasoning
```

---

# 5. Sequential Pattern

```text
Parser → Validator → Builder
```

Use when:

- output B depends on A;
- ordering matters;
- the next step cannot start safely before previous output is accepted.

Risk:

- latency compounds;
- early errors propagate.

Mitigation:

- validate contracts between stages.

---

# 6. Parallel Pattern

Example:

```text
             ┌→ API Analysis
Parsed RD ───┼→ Data Analysis
             └→ UI Analysis
                  ↓
                Merge
```

Use when subtasks are independent.

Requirements:

- shared input contract;
- isolated execution;
- merge strategy;
- partial failure policy.

Do not parallelize tasks that have hidden dependencies.

---

# 7. Handoff Pattern

```text
Agent A
  ↓ artifact/contract
Agent B
```

Handoff should pass defined artifacts, not arbitrary conversation history.

Preferred:

```yaml
HandoffArtifact:
  task_id:
  source_refs:
  findings:
  unresolved_items:
  status:
```

Avoid:

> "Here is my full chat; figure it out."

---

# 8. Reviewer Pattern

```text
Builder
   ↓
Reviewer
 ├── PASS → next
 └── FAIL → revision
```

Separate:

```text
Reviewer reasoning
= identifies semantic findings

Gate logic
= determines route based on accepted result/threshold
```

Example:

```text
Reviewer outputs:
severity=high
status=fail
```

Then deterministic workflow decides:

```text
if status == fail:
    route_to_revision
```

---

# 9. Supervisor Pattern

```text
        Supervisor
       /    |     \
      A     B      C
```

Use when one reasoning component genuinely needs to decompose/delegate tasks dynamically.

Do not use a supervisor simply because the diagram looks "multi-agent".

Costs:

- more model calls;
- more context coordination;
- harder debugging;
- harder evaluation;
- greater latency/cost.

---

# 10. State Design

Workflow state should be explicit.

Example:

```yaml
WorkflowState:
  run_id:
  source_document:
  parsed_requirements:
  validation_findings:
  ontology_tags:
  design_artifacts:
  review_findings:
  status:
  retry_count:
  human_decision:
```

State is not the same as message history.

The workflow must be able to answer:

> What has happened, what artifacts exist, and what step is next?

---

# 11. Contract Boundaries

Every major transition should have an artifact contract.

```text
Parser
 ↓ RequirementDocument contract
Validator
 ↓ ValidatedRequirementDocument contract
Builder
 ↓ DesignArtifact contract
Reviewer
 ↓ ReviewResult contract
Runtime
```

Benefits:

- easier testing;
- easier versioning;
- framework independence;
- less prompt coupling;
- better traceability.

---

# 12. Failure and Retry Design

Classify errors.

## Technical/transient

Examples:

- timeout;
- temporary service error;
- rate limit.

Potential retry.

## Deterministic invalid output

Example:

- schema invalid.

May retry with correction policy or fail controlled.

## Semantic failure

Example:

- source fidelity violation.

Requires revision/reasoning/review, not blind identical retry.

## Human/policy rejection

Requires explicit state transition.

---

# 13. Human-in-the-Loop

Human review is a workflow primitive.

```text
Agent Result
 ↓
Risk / Quality Gate
 ├── low risk → continue
 └── high risk → interrupt
                   ↓
                 Human
              approve/reject/edit
                   ↓
             resume workflow
```

Human review is not just:

> "Agent, please ask the user."

The runtime must persist the waiting state.

---

# 14. Multi-Agent Evaluation

Do not evaluate only each agent separately.

System metrics:

```text
Workflow completion
Handoff success
Coordination failure
Retry rate
Latency
Cost
Human intervention rate
Artifact consistency
End-to-end correctness
```

A workflow can fail even if each individual agent looks good in isolation.

---

# 15. Observability

Trace hierarchy:

```text
Workflow Run
├── Parser span
│   ├── model call
│   └── tool call
├── Validator span
├── Builder span
└── Reviewer span
```

You need to diagnose:

> Which component caused the bad final artifact?

This is why explicit state, contracts, and traces matter.

---

# 16. GH-300 Coding-Agent Perspective

Now ask a coding agent to implement the workflow.

Good context:

```text
Workflow diagram
Node classifications
Artifact schemas
Routing rules
Retry rules
Human gate behavior
Testing strategy
Repository conventions
```

Good instruction:

> Implement the workflow from the supplied spec. Keep deterministic routing outside LLM prompts. Persist typed workflow state. Add tests for PASS, FAIL→revision, timeout, and human-interrupt paths. Do not convert validators into agents unless the spec says reasoning is required.

This demonstrates context engineering, not just prompt cleverness.

---

# 17. Voice Exercise

Classify each one:

### A
Check JSON schema.

> Deterministic validator.

### B
Interpret whether two requirements conflict semantically.

> Model/agent reasoning candidate.

### C
Choose the next node based on `review.status`.

> Deterministic workflow routing.

### D
Decide which specialist should investigate a novel unstructured issue.

> Potential orchestrator/supervisor reasoning.

### E
Wait for manager approval before production action.

> Human interrupt/workflow primitive.

---

# 18. Day 9 PASS Gate

Explain without notes:

1. Agent vs deterministic node.
2. Workflow Runtime vs Orchestrator Agent.
3. Sequential vs parallel.
4. What makes a safe handoff.
5. Reviewer reasoning vs gate logic.
6. When a supervisor is justified.
7. State vs message history.
8. Why contracts exist between nodes.
9. Technical retry vs semantic revision.
10. Why HITL must be represented in workflow state.

## PASS

Pass at **8/10** plus a complete workflow diagram with component classifications.

---

# 19. Deliverable

```text
RD_TO_BD_WORKFLOW_SPEC
├── nodes
├── node classifications
├── artifact contracts
├── state schema
├── routing
├── retry policy
├── human gate
├── evaluation
└── observability
```

Next: Day 10 uses GH-300 concepts to define how an AI coding workflow should implement and validate this whole system.
