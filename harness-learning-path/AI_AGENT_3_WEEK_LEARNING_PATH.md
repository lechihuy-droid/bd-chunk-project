# AI Agent Engineering — 3-Week Learning Path

> Scope: Microsoft AI Agent learning track compressed into 21 days, with the BD Chunk / RD→BD Harness as the capstone project.
>
> Baseline date: 2026-08-09. Verify Microsoft exam/course pages again before booking exams because credential requirements can change.

## 1. Goal

Complete a focused 3-week bootcamp that builds the mental model and implementation skills needed to design and build a production-style AI agent harness.

The primary credential checkpoint is **Microsoft AI-103 — Azure AI Apps and Agents Developer Associate**. Advanced content is selectively pulled from **AAAI-1**, **AAAI-2**, and the **AI-500 Multi-Agent AI Solutions Expert** blueprint.

The target is not to cram every Microsoft certification into 21 days. The target is:

```text
AI/LLM fundamentals
        ↓
Tool calling
        ↓
Single Agent
        ↓
RAG / Knowledge
        ↓
MCP
        ↓
Workflow orchestration
        ↓
Multi-Agent
        ↓
Memory / A2A / Contracts
        ↓
Evaluation / Observability
        ↓
Security / HITL / Versioning
        ↓
Runnable BD Chunk Agent Harness PoC
```

## 2. Time Budget

Recommended pace:

- **21 days**
- **~4 hours/day**
- **~84 hours total**

Suggested allocation:

```text
25% Microsoft Learn / official material
20% architecture + mental models
45% coding / capstone
10% exam questions + review
```

Daily learning cycle:

```text
15 min  — previous-day recap
45 min  — concept
30 min  — architecture / diagram
90 min  — coding lab
30 min  — apply to BD Harness
20 min  — exam-style questions
10 min  — checkpoint
```

---

# WEEK 1 — AI-103 Core + Single Agent

## Outcome

Build a single agent that can read RD input, use tools, retrieve knowledge, and produce validated structured output.

```text
RD
 ↓
Parser Agent
 ↓
Tools / MCP
 ↓
RAG
 ↓
Pydantic Contract
 ↓
Parsed RequirementDocument
```

## Day 1 — LLM → Tool → Agent → Workflow

### Learn

- LLM vs Agent
- Tool vs Agent
- Agent vs Workflow Node
- State vs Memory
- Context vs Knowledge
- Framework vs Runtime
- API vs MCP

Canonical mental model:

```text
LLM
 ↓
Tool Calling
 ↓
Agent
 ↓
Workflow
 ↓
Multi-Agent
 ↓
Agent Runtime
```

### Lab

1. Call an LLM from Python.
2. Return structured JSON.
3. Add one Python function as a callable tool.
4. Make the model select and call the tool.

### Gate

Be able to explain why a function with an LLM call is not automatically an agent.

---

## Day 2 — Microsoft Foundry Foundation

### Learn

```text
Microsoft Foundry
├── Project
├── Model
├── Deployment
├── Endpoint
├── SDK
├── Agent Service
└── Agent Framework
```

Critical distinction:

```text
Agent Framework ≠ Agent Service

Framework = build/orchestrate agent logic
Service   = managed runtime/platform for operating agents
```

### Lab

```text
Python
 ↓
Foundry Model
 ↓
Structured Output
```

### Apply to BD Chunk

Create the initial runtime adapter so the harness does not couple domain logic directly to one model SDK.

---

## Day 3 — Agent Anatomy

### Learn

```text
Agent
├── Goal
├── Instructions
├── Model
├── Tools
├── Knowledge
├── State
├── Memory
└── Guardrails
```

### Lab — RD Parser Agent v1

```text
RD Document
    ↓
Parser Agent
    ↓
read_document()
extract_requirement()
    ↓
RequirementDocument
```

### Gate

Explain which parts are deterministic and which parts require model reasoning.

---

## Day 4 — Schema, Pydantic, and Contracts

### Learn

```text
LLM Output
    ↓
Pydantic Contract
    ↓
Structural Validation
    ↓
Domain Validator
    ↓
Accepted Artifact
```

Key rule:

```text
Pydantic = shape / type / contract correctness
Validator = business / semantic correctness
```

### Lab

Define at minimum:

```text
RequirementDocument
RequirementSection
Requirement
SourceReference
ValidationFinding
```

### Apply to BD Chunk

Establish the boundary between Parser output and Validator input.

---

## Day 5 — RAG and Knowledge

### Learn

```text
Document
 ↓
Chunk
 ↓
Embedding / Index
 ↓
Retrieve
 ↓
Context
 ↓
Agent
```

Decision question:

> When is retrieval necessary, and when should the agent simply read the source file directly?

### Lab

```text
RD Corpus
   ↓
Retrieve relevant section
   ↓
Parser Agent
```

### Apply to BD Chunk

Compare direct-file access vs retrieval for function-level BD generation.

---

## Day 6 — Tool Architecture + MCP

### Learn

- MCP client/server
- Tool discovery
- Tool schema
- Permission boundary
- Timeout
- Error handling
- Tool result validation

Evolution:

```text
Agent
├── read_file()
├── search()
└── get_schema()
```

into:

```text
Agent
 ↓
MCP / Tool Gateway
 ├── read_document
 ├── search_document
 └── get_schema
```

### Lab

Create a minimal MCP-backed document tool interface.

---

## Day 7 — Week 1 Checkpoint / AI-103 Review

Review:

- Model
- Agent
- Tools
- Foundry
- State
- Memory
- RAG
- MCP
- Pydantic
- Validator

Do 30–50 AI-103-style questions and explain every incorrect answer.

### Week 1 Exit Criteria

- Single RD Parser Agent runs end-to-end.
- Output is schema validated.
- At least one tool is called through a defined interface.
- Knowledge/retrieval decision is documented.
- Agent vs tool vs validator boundaries are explicit.

---

# WEEK 2 — Multi-Agent Engineering

## Outcome

Turn the single-agent pipeline into an orchestrated system with explicit workflow control, contracts, review loops, and agent boundaries.

```text
              Workflow Runtime
                     │
               Orchestrator
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
       Parser                Retriever
          │
          ↓
      Validator
          │
          ↓
      Ontology
          │
          ↓
       Builder
          │
          ↓
       Reviewer
          │
       GO / NO-GO
```

## Day 8 — Agentic Loops

### Learn

```text
Observe
 ↓
Reason
 ↓
Act
 ↓
Observe
 ↓
Evaluate
 ↓
Continue / Stop
```

### Lab

```text
Parser
 ↓
Self Review
 ↓
Problem?
 ├── No  → Done
 └── Yes → Revise → Self Review
```

### Gate

Explain the difference between:

- an agent reasoning loop;
- a workflow retry loop;
- a human rejection/revision loop.

---

## Day 9 — Workflow Orchestration

### Learn

Sequential:

```text
A → B → C
```

Parallel:

```text
   ┌→ B ─┐
A ─┤     ├→ D
   └→ C ─┘
```

Conditional:

```text
Reviewer
 ├── GO    → Builder / Next Stage
 └── NO-GO → Revision Path
```

Map to LangGraph concepts:

- State
- Node
- Edge
- Conditional Edge
- Checkpoint
- Interrupt

### Lab

Implement Parser → Validator → Builder with one conditional edge.

---

## Day 10 — Agent vs Tool vs Workflow Node

Evaluate each component using:

```text
Need reasoning?
Need autonomy?
Need tools?
Need iterative decisions?
Need memory?
Need goal-directed behavior?
```

Apply explicitly to:

- Parser
- Validator
- Ontology Tagger
- Builder
- Reviewer

Rule:

> Do not turn every processing step into an agent. Prefer deterministic code/tool/node when autonomous reasoning is unnecessary.

### Output

Create an ADR documenting the classification of each BD Chunk component.

---

## Day 11 — Multi-Agent Patterns

### Learn

1. Sequential
2. Concurrent
3. Handoff
4. Reviewer
5. Hub-and-spoke
6. Supervisor / hierarchical

Examples:

```text
        Supervisor
       /    |     \
      A     B      C
```

```text
       ┌→ API Agent
Plan ──┼→ DB Agent
       └→ UI Agent
```

### Lab

Run at least two independent specialist operations in parallel and merge their outputs deterministically.

---

## Day 12 — Orchestrator Agent vs Workflow Runtime

Core architecture rule:

```text
Workflow Runtime
      │
      ├── deterministic execution control
      │
      └── Orchestrator Agent
              ↓
        reasoning only when needed
```

> Runtime owns execution semantics. The LLM-based orchestrator should only own decisions that genuinely require reasoning.

### Apply to BD Chunk

Define which routing decisions remain graph/config driven and which may be delegated to an orchestration agent.

---

## Day 13 — Memory and Context Engineering

### Learn

```text
Working Context
      ↓
Session State
      ↓
Semantic Memory
      ↓
Persistent Knowledge
```

Distinguish:

```text
Context ≠ State ≠ Memory ≠ Database ≠ Knowledge Base
```

### Lab

Persist useful information from run 1 and retrieve only relevant memory in run 2.

---

## Day 14 — Agent Manifest + A2A Contracts

Define a framework-independent manifest:

```yaml
AgentManifest:
  id:
  role:
  goal:
  input_contract:
  output_contract:
  tools:
  knowledge:
  memory:
  permissions:
  retry_policy:
  timeout:
  evaluation:
```

### Learn

- capability discovery
- agent-to-agent contract
- context handoff
- identity
- state isolation
- conflict resolution

### Rule

> Agents should exchange defined artifacts/contracts, not arbitrary prompt text.

### Week 2 Exit Criteria

- Workflow runtime exists separately from agent reasoning.
- Parser/Validator/Ontology/Builder/Reviewer roles are classified.
- Conditional GO/NO-GO path works.
- AgentManifest schema exists.
- State/context/memory boundaries are documented.

---

# WEEK 3 — Production Agent Harness

## Outcome

Add the minimum production engineering layer around the multi-agent system.

```text
┌────────────────────────────┐
│         USER / UI          │
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│      WORKFLOW RUNTIME      │
│ LangGraph / Agent Framework│
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│        AGENT LAYER         │
│ Parser / Builder / Reviewer│
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│        TOOL / MCP          │
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│ KNOWLEDGE / MEMORY / STATE │
└────────────┬───────────────┘
             ↓
┌────────────────────────────┐
│ EVAL / TRACE / SECURITY    │
└────────────────────────────┘
```

## Day 15 — Evaluation

### Metrics

Single-agent/system quality:

- Task completion
- Accuracy
- Groundedness
- Tool correctness
- Contract compliance
- Hallucination rate
- Latency
- Cost

Multi-agent quality:

- Handoff success
- Coordination success
- Workflow completion
- Retry rate
- Human intervention rate

### Lab

Create a small golden dataset and an automated evaluation run.

---

## Day 16 — Observability

Trace hierarchy:

```text
Workflow Trace
      ↓
Agent Trace
      ↓
LLM Call
      ↓
Tool Call
      ↓
Artifact
```

The system must support diagnosis of:

> Was the bad result caused by prompt, model, agent logic, tool, retrieval, contract, or source data?

### Lab

Add trace IDs across one complete RD→parsed artifact workflow.

---

## Day 17 — Security and Permissions

### Learn

- identity
- RBAC
- secrets
- managed identity
- sandbox
- allowlists
- least privilege

Target permission model:

```text
Parser   → read source documents
Builder  → read + write generated artifacts
Reviewer → read artifacts / findings only
```

### Rule

> Never give every agent every tool with full permission.

---

## Day 18 — Human-in-the-Loop + Guardrails

Design HITL as a workflow primitive:

```text
Agent
 ↓
Risk / Quality Gate
 ├── Low Risk  → Continue
 └── High Risk → Human Review
                   ├── Approve
                   ├── Reject
                   └── Edit / Revise
```

Rule:

> Human approval is runtime state + workflow control, not a prompt such as “please ask the user”.

---

## Day 19 — Versioning and Reproducibility

Version independently:

```text
Workflow vN
├── Agent vN
├── Prompt vN
├── Tool vN
├── Schema vN
├── Model Config vN
└── Eval Dataset vN
```

Every execution should persist a `RunManifest` sufficient to reconstruct the run configuration.

### Lab

Create a minimal RunManifest and compare two runs with different prompt/model configurations.

---

## Day 20 — Harness Architecture Integration

Integrate:

```text
Agent Registry
Workflow Runtime
Tool / MCP Layer
Knowledge Layer
State Store
Memory
Evaluation
Observability
Human Gate
Security
Versioning
```

### Architecture Review Questions

1. What is deterministic?
2. What requires model reasoning?
3. Who owns state transitions?
4. Where are contracts enforced?
5. What can retry safely?
6. Where does human approval interrupt execution?
7. How is every artifact traced back to source + run configuration?

---

## Day 21 — Final Capstone Review

Explain the complete system without referring to framework-specific terminology first:

```text
Business Requirement
        ↓
Workflow
        ↓
Agent / Tool Selection
        ↓
Contracts
        ↓
State
        ↓
Knowledge / Memory
        ↓
Execution
        ↓
Review / Human Gate
        ↓
Artifact
        ↓
Evaluation / Trace
```

Then map the canonical architecture to Microsoft Agent Framework and/or LangGraph.

## Final Deliverables

The 3-week capstone should produce:

1. Architecture document
2. Workflow graph
3. `AgentManifest`
4. Pydantic contracts
5. MCP/tool interfaces
6. Single-agent implementation
7. Multi-agent/workflow implementation
8. Human review gate
9. Evaluation suite
10. Trace/observability model
11. Versioning + `RunManifest`
12. Runnable PoC

---

# 3. Microsoft Credential Mapping

## Primary Target — AI-103

**Microsoft Certified: Azure AI Apps and Agents Developer Associate**

Use AI-103 as the first formal credential checkpoint after or near the end of this 3-week bootcamp.

Official references:

- Certification: https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-apps-and-agents-developer-associate/
- Course: https://learn.microsoft.com/en-us/training/courses/ai-103t00

## Advanced Technical Content — AAAI-1 + AAAI-2

Selectively use these modules during Week 2:

- AAAI-1 — Architect production-grade multi-agent AI solutions
  - https://learn.microsoft.com/en-us/training/paths/aaai-1-architect-production-grade-multi-agent-ai-solutions/
- AAAI-2 — Build production-grade multi-agent capabilities with Microsoft Foundry
  - https://learn.microsoft.com/en-us/training/paths/aaai-2-build-production-grade-multi-agent-capabilities-microsoft-foundry/

## Next Technical Certification — AI-500

After AI-103, continue toward:

**Microsoft Certified: Multi-Agent AI Solutions Expert**

- Certification: https://learn.microsoft.com/en-us/credentials/certifications/multi-agent-ai-solutions-expert/
- Exam/study guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-500

AI-500 is not the 21-day exam target. Its architecture, orchestration, evaluation, security, and production concepts are used as the Week 2–3 technical north star.

---

# 4. Frontier / Titan Follow-On

After the bootcamp and AI-103, the broader Microsoft Frontier direction can be pursued separately.

Recommended sequence:

```text
3-Week Agent Bootcamp
        ↓
AI-103
        ↓
AI-500
        ↓
AB-100
        ↓
GH-300
        ↓
Titan / Frontier project-readiness path
        ↓
Frontier Transformation Engineer direction
```

AI-300 / GenAIOps can be inserted when deeper production CI/CD, lifecycle, and operational engineering become necessary.

The Frontier/Titan path is broader than agent coding: it expands into business architecture, GitHub Copilot engineering, governance, delivery readiness, and Microsoft partner transformation capability.

---

# 5. BD Chunk Capstone Mapping

The same project is evolved across all 3 weeks.

## Version 1 — Single Agent

```text
RD
 ↓
Parser Agent
 ↓
Structured RequirementDocument
```

## Version 2 — Contract-Driven Pipeline

```text
RD
 ↓
Parser
 ↓
Pydantic Contract
 ↓
Validator
 ↓
Parsed + Validated Document
```

## Version 3 — Multi-Step Workflow

```text
Parser
 ↓
Validator
 ↓
Ontology Tagger
 ↓
Builder
 ↓
Reviewer
```

## Version 4 — Agent Harness

```text
                    Workflow Runtime
                           │
                   Orchestration Logic
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
      Specialist       Deterministic      Reviewer /
       Agents              Tools          Human Gate
          │                │                │
          └────────────────┼────────────────┘
                           ↓
             State / Artifact / Knowledge
                           ↓
               Eval / Trace / Versioning
```

The capstone is successful only if the architecture remains understandable independently of Microsoft Agent Framework, LangGraph, Claude Code, or OpenAI Agents SDK.

---

# 6. Completion Definition

The 3-week learning path is complete when the learner can answer, design, and demonstrate all of the following:

- Why a component should be an agent vs tool vs workflow node.
- How state differs from memory and knowledge.
- How an agent invokes tools safely.
- When RAG is useful vs direct document access.
- How MCP fits into the tool ecosystem.
- How deterministic workflow control and LLM orchestration coexist.
- How multi-agent handoffs use explicit contracts.
- How human review is represented in runtime state.
- How an output can be traced back to source, prompt, model, tool, schema, and run version.
- How to evaluate the system beyond “the output looks good”.
- How to map the canonical architecture to both Microsoft Agent Framework and LangGraph.

The desired end-state is not “knows Microsoft Agent terminology”. It is:

> **Can architect and build a framework-independent production-style AI agent harness, then map it onto Microsoft and open agent frameworks.**
