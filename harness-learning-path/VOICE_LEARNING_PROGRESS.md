# AI Agent Voice Learning Progress

> Learning mode: voice-first / conversational. No API access is required for the early conceptual track. Coding and SDK labs can be added later without changing the architecture mental model.
>
> Started: 2026-08-09
> Current status: **Day 1–Day 4 completed conceptually**

## Progress

| Day | Topic | Status |
|---|---|---|
| Day 1 | Model, Agent, Tool, Workflow Node, State vs Memory | ✅ Completed |
| Day 2 | Foundry vs Harness + Agent Anatomy | ✅ Completed |
| Day 3 | RD Parser Agent + Output Contract | ✅ Completed |
| Day 4 | Contract, Pydantic, Domain Validator | ✅ Completed |
| Day 5 | RAG and Knowledge | ⏭ Next |

---

# Day 1 — Model → Tool → Agent → Workflow

## Mental models locked in

### Model

A model is the reasoning/generation engine. By itself it does not own an application goal, workflow, tools, permissions, or execution lifecycle.

### Agent

An LLM agent is a goal-directed system built around a model and additional runtime/application capabilities.

Canonical anatomy preview:

```text
Agent
├── Role
├── Goal
├── Model
├── Instructions
├── Input Contract
├── Output Contract
├── Tools
├── Knowledge
├── State / Memory
├── Guardrails
└── Evaluation
```

In the LLM-agent context used in this learning path, the model is a core component of the agent. A deterministic component without an LLM may still be a workflow worker/tool/service, but it should not automatically be classified as an LLM agent.

### Tool

A tool performs a bounded capability.

```text
Tool
= specific operation
= no independent business goal
= no autonomous execution loop
= invoked by an agent or workflow runtime
```

Examples:

```text
read_document()
search_document()
validate_schema()
write_artifact()
```

### Workflow Node

A workflow node does **not** have to be an agent.

A node can be:

```text
Agent
Tool / Function
Deterministic Validator
Router
Human Review Step
External Service
```

Core rule:

> Do not make every workflow node an agent.

### State vs Memory

```text
State
= current execution/workflow data
= what is happening in this run

Memory
= information intentionally retained for reuse
= may survive across steps, sessions, or runs
```

The practical distinction is lifecycle and reuse, not merely “short-term vs long-term”.

## Day 1 checkpoint

Can explain verbally:

- Model vs Agent
- Tool vs Agent
- Workflow Node vs Agent
- State vs Memory

Status: **Passed**

---

# Day 2 — Microsoft Foundry vs Harness + Agent Anatomy

## Foundry vs Harness

Important correction/clarification:

```text
Harness ≠ Microsoft Foundry
```

### Harness

Harness is the general architectural/application layer that surrounds models and agents so they can execute reliably inside a system.

Typical harness responsibilities:

```text
Workflow / orchestration
Agent contracts
Tool interfaces / tool calling
State
Memory
Knowledge access
Guardrails
Evaluation
Observability
Human review
Execution policies
```

Harness is **vendor-independent**.

If Microsoft Foundry is replaced by another provider, the canonical harness concepts should remain mostly stable.

### Microsoft Foundry

Microsoft Foundry is a concrete Microsoft platform/product ecosystem for building and operating AI applications and agents.

It can provide managed capabilities used by a harness, but it is not identical to the abstract harness concept.

Canonical relationship:

```text
Application / Agent Harness
        ↓ uses
Microsoft Foundry services
        ↓
Models / managed agent capabilities / evaluation / operations
```

## What remains if Foundry changes?

The learner identified correctly:

- workflow design
- agent design
- tool-calling design

Extend this to include:

- contracts
- evaluation criteria
- guardrail policy
- state transitions
- domain architecture

These should be designed independently of a specific provider when possible.

---

## Agent Anatomy

The working anatomy for this course is:

```text
Agent
├── 1. Role
├── 2. Goal
├── 3. Model
├── 4. Instructions
├── 5. Input Contract
├── 6. Output Contract
├── 7. Tools
├── 8. Knowledge
├── 9. State / Memory
├── 10. Guardrails
└── 11. Evaluation
```

### 1. Role

Who/what the agent is responsible for.

Example:

```text
RD Parser Agent
```

### 2. Goal

The outcome the agent must achieve.

### 3. Model

The reasoning/generation engine used by the agent.

### 4. Instructions

Operational rules describing how the agent should perform its role.

### 5. Input Contract

What the agent is allowed/expected to receive.

### 6. Output Contract

What downstream components can depend on receiving.

### 7. Tools

Actions/capabilities the agent can invoke.

### 8. Knowledge

Domain information, documents, policies, schemas, or retrieval sources available to the agent.

### 9. State / Memory

Execution state and intentionally retained information.

### 10. Guardrails

Boundaries around allowed behavior, data access, output, risk, and escalation.

### 11. Evaluation

Criteria used to determine whether the agent performed correctly.

## Learner conclusion

For the RD Parser Agent, **Output Contract** was selected as the most important design boundary because downstream workflow nodes need a predictable artifact to consume and evaluate.

That conclusion is retained as a core design principle:

> Define the output artifact before optimizing the prompt.

Status: **Passed**

---

# Day 3 — Design the RD Parser Agent from the Output Backward

## Core lesson

Do not begin agent design with the prompt.

Begin with:

```text
Expected Artifact
      ↓
Output Contract
      ↓
Validation Criteria
      ↓
Agent Responsibility
      ↓
Tools / Knowledge
      ↓
Instructions / Prompt
```

## RD Parser Agent — current conceptual contract

### Responsibility

Read a requirement document and decompose it into the smallest meaningful requirement blocks needed by the downstream BD workflow.

### Output concept

Learner-defined version:

> Output của RD Parser Agent là các block nhỏ nhất có nghĩa của tài liệu requirement, trong đó có metadata để đảm bảo traceability về nguồn.

Canonicalized version:

```text
RD Parser Output
= smallest meaningful requirement blocks
+ original/source context
+ source metadata / traceability
+ review flags when uncertain
```

### Example fields

```text
RequirementBlock
├── id
├── original_text
├── normalized_requirement
├── source_document
├── source_section
├── source_location
├── metadata
└── needs_review
```

## Traceability principle

Every derived requirement should retain enough source metadata to trace it back to the RD source.

```text
Generated Requirement
        ↓ trace
Source Section
        ↓ trace
Original RD
```

This is essential for validation, review, auditability, and later BD generation.

## Microsoft implementation note

When mapped to Microsoft technologies, the implementation can use Microsoft Foundry/model services. The architectural contract remains vendor-independent so the model/provider can be replaced later.

Status: **Passed conceptually**

---

# Day 4 — Contract, Pydantic, and Domain Validation

## Core pipeline

```text
Agent Output
    ↓
Contract Enforcement
    ↓
Structural / Machine-checkable Validation
    ↓
Domain / Semantic Validation
    ↓
Accepted Artifact or Finding
```

## Important refinement

Earlier shorthand was:

```text
Contract = shape
Validator = meaning
```

That is useful for beginners but too narrow for architecture work.

The more precise model is:

### Contract

A contract defines what another component is allowed to rely on.

It may include:

```text
Structural obligations
+ simple invariants
+ semantic/business obligations
```

Example:

```text
RequirementBlock must contain source_section.
source_section must refer to the source requirement from which the block was derived.
```

The first obligation is primarily structural; the second is semantic.

### Pydantic / Schema validation

Pydantic is an implementation mechanism for enforcing machine-checkable parts of the contract, such as:

```text
required fields
field types
enum values
formats
ranges
simple cross-field invariants
```

### Domain Validator

A domain validator checks correctness that requires business/domain/source understanding.

Examples:

```text
Does source_section actually exist in the RD?
Does original_text match the source?
Was an important requirement meaning lost?
Does the normalized requirement preserve the original obligation?
Is the requirement mapped to the correct domain/ontology?
```

## Voice checkpoint

Scenario:

> Parser returns all required fields, but `original_text` does not match the RD source.

Answer:

```text
Domain / semantic validation failure
```

Correct.

## Day 4 mental model

Use this version going forward:

```text
Contract
= what downstream may rely on

Schema / Pydantic
= machine-checkable contract enforcement

Domain Validator
= semantic / source / business correctness
```

Status: **Passed**

---

# Next — Day 5

## Topic

**RAG and Knowledge**

Questions to answer:

1. What is the difference between context, knowledge, state, and memory?
2. When should an agent read the source document directly?
3. When is RAG actually required?
4. What does retrieval add that a large context window does not?
5. In the RD→BD pipeline, which knowledge should be retrieved and which should remain deterministic/reference data?

Target mental model:

```text
Source Documents
      ↓
Direct Read OR Retrieval
      ↓
Working Context
      ↓
Agent Reasoning
      ↓
Contracted Artifact
```

---

# Voice Learning Rule

For the current learning mode:

```text
Explain verbally
    ↓
Learner answers verbally
    ↓
Challenge / correction
    ↓
Canonical mental model
    ↓
Apply to RD→BD Harness
```

Coding is optional during the conceptual phase. When API/SDK access becomes available, the same mental models will be mapped to implementation labs rather than relearned from scratch.
