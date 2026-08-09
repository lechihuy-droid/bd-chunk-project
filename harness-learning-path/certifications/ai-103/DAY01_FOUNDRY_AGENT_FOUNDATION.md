# AI-103 DAY 1 — FOUNDRY + MODEL + AGENT FOUNDATION

> Track: Microsoft AI-103 — Azure AI Apps and Agents Developer Associate  
> Mode: Voice-first / concept-first  
> Purpose: Build the platform and agent mental model before RAG, tools, and multi-agent on Day 2.

---

# 1. Day 1 Outcome

By the end of Day 1, explain this architecture without looking at notes:

```text
Business / Application Need
        ↓
Microsoft Foundry Project
        ↓
Model Selection + Deployment
        ↓
Agent
        ├── Instructions
        ├── Tools
        ├── Knowledge
        ├── State / Context / Memory
        └── Guardrails
        ↓
Workflow / Runtime
        ↓
Evaluation + Monitoring + Security
```

Day 1 is not about memorizing every Azure product name. It is about recognizing the role of each layer in an AI solution.

---

# 2. Session Structure

Recommended voice-first sequence:

```text
Module 1 — Model Selection
Module 2 — Microsoft Foundry Landscape
Module 3 — Agent Anatomy
Module 4 — Context / State / Memory / Knowledge
Module 5 — Framework / Service / Harness / Runtime
Module 6 — Deployment + Operations Basics
Final Checkpoint
```

Suggested time:

| Section | Time |
|---|---:|
| Model selection | 25 min |
| Foundry landscape | 35 min |
| Agent anatomy | 45 min |
| State/context/memory/knowledge | 30 min |
| Framework/service/harness/runtime | 30 min |
| Deployment/operations | 30 min |
| Exam-style checkpoint | 25 min |
| **Total** | **~3h 40m** |

---

# MODULE 1 — MODEL SELECTION

## 1.1 Mental Model

A model is a reasoning/generation engine selected for a workload.

```text
Task Requirement
      ↓
Input / Output Modality
      ↓
Reasoning Complexity
      ↓
Latency Requirement
      ↓
Cost Constraint
      ↓
Model Selection
```

Do not select a model only because it is the largest or newest.

## 1.2 Model categories to recognize

- Large Language Model (LLM)
- Small Language Model (SLM)
- Code-oriented model
- Multimodal model

The exam may present a scenario and ask for the most appropriate model characteristics rather than asking for a definition.

## 1.3 Oral questions

Answer without notes:

1. Why is a larger model not automatically the best model?
2. When would a small model be preferable?
3. When does a workload require a multimodal model?
4. Which factors affect model choice besides quality?

## 1.4 Exam trap

### Wrong mental model

> Best quality = always choose the biggest model.

### Better mental model

Choose according to:

```text
Capability
+ Latency
+ Cost
+ Modality
+ Operational Constraint
```

## PASS

Explain model selection as a trade-off, not as a ranking of models.

---

# MODULE 2 — MICROSOFT FOUNDRY LANDSCAPE

## 2.1 Core Mental Model

Microsoft Foundry is the Microsoft platform layer used to build and operate AI applications and agents.

```text
Microsoft Foundry
├── Project
├── Models
├── Deployments
├── Endpoints / SDK access
├── Tools / Connections
├── Knowledge / Search integration
├── Agent Service
├── Evaluation
└── Monitoring
```

Do not memorize this only as a list. Understand the dependency:

```text
Project
  ↓
Model / Service Configuration
  ↓
Deployment
  ↓
Application / Agent
  ↓
Evaluation / Monitoring
```

## 2.2 Project

Think of a project as an organizational boundary for an AI solution.

It groups the resources/configuration needed by the solution rather than being the model itself.

### Oral question

> Is a Foundry Project the same thing as an Agent?

Expected answer: No. A project is the solution/workspace boundary. An agent is a runnable goal-directed component inside the solution.

---

## 2.3 Model vs Deployment vs Endpoint

Mental distinction:

```text
Model
= capability / model family

Deployment
= configured runnable instance/access configuration of that model

Endpoint / SDK access
= interface used by the application to consume the deployed capability
```

The exact implementation can vary, but these conceptual roles should remain separate.

### Oral scenario

> Your organization selected a suitable model but the application still cannot call it. Which missing concept should you think about next?

Expected reasoning: deployment/access configuration and the interface/endpoint used by the application.

---

# MODULE 3 — AGENT ANATOMY

## 3.1 Canonical Agent

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
├── Context / State
├── Memory
├── Guardrails
└── Evaluation
```

For exam recognition, the essential idea is:

> An agent is not just an LLM call. It is a goal-directed system around a model with instructions, context, capabilities, and execution behavior.

---

## 3.2 Model vs Agent

```text
Model
= generates / reasons from supplied input

Agent
= uses a model plus instructions, tools, context,
  state, and control behavior to pursue a goal
```

### Oral checkpoint

Give a two-sentence explanation of Model vs Agent.

### Exam trap

If a scenario only calls a model once to summarize a paragraph, that does not automatically make it an agent.

---

## 3.3 Tool vs Agent

```text
Tool
= bounded capability

Agent
= decides how/when to use capabilities toward a goal
```

Examples of tools:

- read a document;
- query a search index;
- call an API;
- retrieve customer data;
- create a ticket.

### Oral question

> Does a tool need its own goal and reasoning loop?

Expected answer: No. A tool performs a bounded operation when invoked.

---

## 3.4 Workflow Node vs Agent

```text
Workflow Node
= one execution step
```

A node may be:

- deterministic function;
- validator;
- tool invocation;
- agent;
- human approval step.

### Architecture rule

> Do not make every node an agent.

Use model reasoning only where reasoning is required.

### Oral scenario

A JSON schema validator receives output and returns PASS/FAIL. Should it be an LLM agent?

Expected answer: Normally no. This is deterministic validation.

---

# MODULE 4 — CONTEXT, STATE, MEMORY, KNOWLEDGE

This distinction is essential for both AI-103 and later AB-100 architecture.

## 4.1 Context

```text
Context
= information available to the model for the current reasoning step
```

Examples:

- system instructions;
- retrieved passages;
- recent conversation turns;
- current task data.

---

## 4.2 State

```text
State
= current execution condition/data of the workflow or run
```

Example:

```text
run_id
current_step
parsed_requirements
validation_status
```

State exists to allow the runtime to know where execution is and what has happened.

---

## 4.3 Memory

```text
Memory
= information intentionally retained for later reuse
```

Memory can persist beyond one reasoning step or one run, depending on design.

Example:

- user preference;
- prior decision;
- recurring project convention.

Important:

> Memory is not automatically every previous message.

---

## 4.4 Knowledge

```text
Knowledge
= external source of truth used by the solution
```

Examples:

- enterprise documents;
- requirement repository;
- policies;
- product documentation;
- search index.

---

## 4.5 Four-way example

```text
RD repository
→ Knowledge

The section retrieved for the current call
→ Context

Current parser step + already-produced blocks
→ State

A reusable project naming convention retained across runs
→ Memory
```

## Oral checkpoint

Explain all four concepts using one project example.

## Exam trap

Do not use “memory” as a generic word for all persisted information.

---

# MODULE 5 — FRAMEWORK, SERVICE, HARNESS, RUNTIME

## 5.1 Agent Framework

```text
Agent Framework
= developer framework/SDK for defining agent logic and orchestration
```

It is about building behavior.

---

## 5.2 Agent Service

```text
Agent Service
= managed platform/service capability used to host/manage/operate agents
```

It is about managed operation.

---

## 5.3 Harness

```text
Harness
= architectural/runtime pattern surrounding models/agents
```

A harness may contain:

- workflow control;
- tool integration;
- state;
- memory;
- evaluation;
- observability;
- guardrails;
- human approval;
- artifact handling.

Harness is vendor-independent as a concept.

---

## 5.4 Foundry vs Harness

```text
Foundry
= Microsoft platform/product ecosystem

Harness
= architecture/runtime concept
```

A harness can use Foundry.

Foundry can provide managed capabilities that implement parts of a harness.

But they are not synonyms.

---

## 5.5 Runtime

```text
Runtime
= component/environment that actually executes the workflow/agent behavior
```

Architecture principle:

> Runtime owns execution semantics. Model reasoning should be used only where needed.

### Oral checkpoint

Explain:

1. Agent Framework vs Agent Service.
2. Harness vs Foundry.
3. Agent vs Runtime.

---

# MODULE 6 — DEPLOYMENT + OPERATIONS BASICS

Day 1 does not require implementation, but AI-103 expects operational awareness.

## 6.1 Lifecycle

```text
Code / Configuration
       ↓
Build / CI
       ↓
Deploy Model / Agent
       ↓
Application Uses It
       ↓
Evaluate
       ↓
Monitor
       ↓
Improve / Redeploy
```

---

## 6.2 Quotas and Rate Limits

Know why these matter:

```text
Traffic
 ↓
Quota / Rate Limit
 ↓
Capacity behavior
```

A production solution must plan for expected usage and service limits.

---

## 6.3 Cost

Cost can be influenced by:

- model choice;
- token volume;
- number of calls;
- retrieval/tool calls;
- concurrency;
- unnecessary context.

Do not think of cost only as “price per request.”

---

## 6.4 Monitoring Dimensions

```text
Production AI
├── Availability
├── Latency
├── Error Rate
├── Cost
├── Quality
├── Safety
├── Grounding
└── Retrieval / Search Health
```

AI monitoring differs from ordinary API monitoring because quality and safety are also first-class concerns.

---

# 3. DAY 1 EXAM-STYLE SCENARIOS

## Scenario 1

A team wants to summarize short internal text with low latency and low cost. The task has limited reasoning complexity.

Question: Should they automatically use the largest available model?

Expected reasoning: No. Consider a smaller suitable model if it meets capability requirements.

---

## Scenario 2

A solution uses an LLM to decide whether to call `search_policy` or `create_ticket` and then continues based on the tool result.

Question: Is this closer to a plain model call or an agent pattern?

Expected reasoning: Agent pattern, because the model participates in goal-directed tool selection and iterative execution.

---

## Scenario 3

A node only checks whether required JSON fields exist.

Question: Should this normally be implemented as an autonomous agent?

Expected reasoning: No. Prefer deterministic validation.

---

## Scenario 4

A user preference must be reused across future sessions.

Question: Is that primarily context, state, memory, or knowledge?

Expected answer: Memory.

---

## Scenario 5

A policy repository is indexed and retrieved from when needed.

Question: Is the repository itself context, state, memory, or knowledge?

Expected answer: Knowledge. Retrieved passages may become context for a model call.

---

# 4. DAY 1 FINAL ORAL CHECKPOINT

Answer without notes:

1. What is the difference between Model and Agent?
2. What is the difference between Tool and Agent?
3. Why is a workflow node not automatically an agent?
4. Define Context, State, Memory, and Knowledge.
5. What is Microsoft Foundry?
6. Foundry vs Harness?
7. Agent Framework vs Agent Service?
8. What does a runtime own?
9. Why do quota and rate limits matter?
10. Why does AI monitoring include more than latency and errors?

## PASS CONDITION

Pass Day 1 when:

- at least 8/10 answers are conceptually correct;
- Model/Agent/Tool/Node distinctions are stable;
- Context/State/Memory/Knowledge distinctions are stable;
- Foundry/Harness/Framework/Service distinctions are stable.

If not, review only the failed modules instead of repeating the whole day.

---

# 5. Mapping to the 4 Later Hands-on Sessions

No API key is required today.

Day 1 concepts are applied later:

```text
Day 1 Concept
      ↓
Hands-on Session 1
Design One Agent
```

Specifically:

- Agent Anatomy → AgentManifest/design spec
- Tool vs Agent → component classification
- State/Memory/Knowledge → runtime/data architecture
- Foundry vs Harness → platform abstraction
- Framework vs Service → implementation/deployment mapping

---

# 6. Voice Study Script

Use this file interactively with ChatGPT.

Recommended flow:

```text
Ask: Teach Module 1 only.
↓
Explain it back in your own words.
↓
Ask for one scenario question.
↓
Get correction.
↓
Move to Module 2.
```

Do not read the whole document passively.

The goal is active recall and architecture recognition.
