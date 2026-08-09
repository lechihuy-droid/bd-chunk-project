# DAY 6 — GH-300 AGENTIC DEVELOPMENT, DATA, PRIVACY, GOVERNANCE

> Track: GH-300 — GitHub Copilot  
> Position: Day 6 of the 21-day Frontier/Titan certification sprint  
> Role: Final concept day before four integrated AI-103 + GH-300 hands-on sessions  
> Official scope anchor: GH-300 skills measured as of 2026-08-07

---

# 1. Day 6 Goal

Day 6 closes the GH-300 concept rush.

The goal is to connect Copilot features with the broader engineering system:

```text
Developer
   ↓
GitHub Copilot
   ↓
Context + Instructions
   ↓
Agentic Execution
   ↓
Repository / Tools / MCP
   ↓
Tests / Review / Security
   ↓
Governed Software Delivery
```

By the end of the day, you should be able to explain not just how to ask Copilot for code, but how Copilot participates in a controlled software engineering workflow.

---

# 2. Official GH-300 Scope Covered Today

Day 6 emphasizes the remaining exam areas not fully covered in Days 4–5:

- use GitHub Copilot features and capabilities;
- understand GitHub Copilot data and architecture;
- configure privacy, exclusions, and safeguards;
- troubleshoot and apply safeguards;
- improve developer productivity;
- use agentic capabilities appropriately;
- reason about MCP, agent sessions, subagents, review, testing, and security.

The current GH-300 study guide emphasizes productivity, quality, security, responsible AI, prompt engineering, Copilot features, architecture/data, and privacy safeguards.

---

# 3. Module 6.1 — Copilot Chat vs Edit vs Agentic Execution

## Mental Model

```text
Completion
= predicts code locally around the cursor

Chat
= answers/explains/proposes changes

Edit-oriented workflow
= applies targeted changes across selected files

Agentic workflow
= plans, inspects, acts, runs tools/tests, iterates
```

The main difference is degree of autonomy and execution scope.

### Oral Check

Explain why "Copilot generated code" does not automatically mean "Copilot acted as an agent".

Expected idea:

> Agentic behavior requires a goal-directed execution loop with context inspection, tool/action use, evaluation, and iteration—not only text generation.

---

# 4. Module 6.2 — Agent Mode Mental Model

Canonical loop:

```text
Task
 ↓
Interpret Goal
 ↓
Inspect Repository / Context
 ↓
Plan
 ↓
Modify
 ↓
Run Tool / Test
 ↓
Observe Result
 ↓
Revise or Finish
```

This directly maps to the general agent loop learned in AI-103:

```text
Observe → Reason → Act → Observe → Evaluate
```

## Important distinction

```text
GitHub Copilot Agent
= coding/development agent

Application Agent
= agent being built inside your product
```

Example:

```text
Copilot Agent
    ↓ builds
RD Parser Agent
```

Do not confuse the agent that builds software with the software agent being built.

---

# 5. Module 6.3 — Agent Sessions and Long-Running Work

An agent session represents a bounded execution context for a development task.

Think in terms of:

```text
Session
├── Goal
├── Repository context
├── Instructions
├── Changes
├── Tool usage
├── Test results
└── Completion state
```

### Why session boundaries matter

Without a clear session boundary:

- context becomes noisy;
- task scope drifts;
- review becomes harder;
- generated changes become harder to attribute;
- execution may mix unrelated objectives.

### Exam Trap

Do not equate session with long-term memory.

```text
Session
= bounded execution context

Memory
= retained information reused across later tasks/runs
```

---

# 6. Module 6.4 — Subagents

Subagents help divide a broad engineering task into specialized responsibilities.

Example:

```text
Primary Coding Agent
      │
      ├── Test Specialist
      ├── Security Reviewer
      └── Documentation Specialist
```

Use a subagent when specialization or isolated context improves quality.

Do not create subagents for every tiny step.

## Decision Rule

Ask:

```text
Does the subtask need a distinct goal?
Does it need specialized context?
Does it need an independent review/result?
Would separation reduce context noise?
```

If not, keep it within the primary agent/workflow.

---

# 7. Module 6.5 — MCP in GitHub Copilot

MCP provides a standardized way for AI clients/agents to discover and use external tools/resources.

Mental model:

```text
Copilot / Coding Agent
        ↓
     MCP Client
        ↓
     MCP Server
        ↓
External Tools / Data / Services
```

Examples of capabilities exposed through an MCP server might include:

- repository-specific tooling;
- internal documentation search;
- issue/project lookup;
- deployment utilities;
- test systems;
- domain-specific services.

## Security principle

Tool availability must not imply unrestricted permission.

```text
Tool discovery
≠
Authorization
```

The system still requires permission controls and least privilege.

---

# 8. Module 6.6 — Copilot Data and Architecture

You do not need to memorize internal implementation details.

You must understand the architecture-level flow:

```text
Developer Input
     ↓
Context Collection
     ↓
Copilot Service / Model
     ↓
Generated Response / Action
     ↓
Developer / Agent Validation
```

Context can include, depending on feature and configuration:

- current file;
- neighboring code;
- selected text;
- repository context;
- explicit instructions;
- conversation history;
- tool results.

## Critical idea

The quality and sensitivity of supplied context directly affect both output quality and privacy risk.

---

# 9. Module 6.7 — Privacy, Content Exclusions, and Safeguards

Enterprise Copilot usage requires more than prompt quality.

Think in layers:

```text
Identity
 ↓
Organization Policy
 ↓
Repository Access
 ↓
Content Exclusion / Context Rules
 ↓
Copilot Feature
 ↓
Human Review
```

Topics to recognize:

- organization-level policy;
- user access;
- repository permissions;
- content exclusions;
- data/privacy considerations;
- safeguards;
- auditing/review expectations.

## Exam Scenario

A repository contains sensitive generated files that should not become Copilot context.

Best mental response:

> Control context exposure through repository/policy/content-exclusion mechanisms rather than relying on developers to remember a prompt instruction such as "do not read this folder".

---

# 10. Module 6.8 — Responsible Use in Engineering

Responsible AI in coding means the developer remains accountable for the delivered code.

Copilot output can contain:

- functional bugs;
- insecure patterns;
- incorrect APIs;
- hidden assumptions;
- outdated patterns;
- inadequate tests.

Therefore:

```text
Generate
 ↓
Inspect
 ↓
Test
 ↓
Security Review
 ↓
Human Decision
```

## Key Rule

> AI-generated code is a proposal until validated.

---

# 11. Module 6.9 — Developer Productivity

Productivity is not "more generated lines of code".

Useful productivity outcomes include:

- faster code understanding;
- lower time-to-first-draft;
- faster test generation;
- faster refactoring;
- faster debugging;
- reduced repetitive work;
- more consistent documentation;
- shorter review cycles.

A bad use of Copilot can increase rework even if initial code generation is fast.

### Better metric

```text
Engineering throughput
= useful validated change / total effort
```

not merely:

```text
lines generated / minute
```

---

# 12. Module 6.10 — Testing and Review with Copilot

Copilot can assist with:

- generating test cases;
- identifying edge cases;
- explaining failed tests;
- reviewing changes;
- suggesting refactoring;
- documenting behavior.

But validation boundaries remain explicit.

```text
Copilot Suggestion
     ↓
Automated Test
     ↓
Static / Security Check
     ↓
Human Review
     ↓
Merge
```

Do not use the same generated answer as both implementation and unquestioned proof of correctness.

---

# 13. AI-103 ↔ GH-300 Integration Map

At this point you should connect the two certificates:

```text
AI-103
Build AI application / agent

GH-300
Use AI agent capabilities to build software
```

Common concepts:

| General concept | AI-103 | GH-300 |
|---|---|---|
| Agent | application agent | coding agent |
| Tool | business/system action | repo/dev tool |
| Context | app/agent task context | code/repo context |
| MCP | agent tool integration | coding-agent tool integration |
| Human review | approval / safeguard | code review / validation |
| Evaluation | agent quality | code/test/security quality |
| Runtime | app/agent runtime | coding-agent execution environment |

---

# 14. Exam Traps

1. **Copilot is not a substitute for testing.**
2. **Agent Mode is not the same as chat.**
3. **MCP does not automatically grant authorization.**
4. **Repository context is not automatically safe context.**
5. **Subagents should represent meaningful specialized work, not every tiny action.**
6. **Content exclusion/policy controls are stronger than prompt-only warnings.**
7. **Productivity means validated engineering outcome, not generated code volume.**
8. **The developer remains responsible for correctness and security.**

---

# 15. Voice Scenario Drill

Answer verbally.

### Scenario 1
A developer asks Copilot Chat to explain a function. Is this agentic execution?

### Scenario 2
Copilot independently inspects multiple files, edits code, runs tests, sees a failure, and fixes the implementation. What changed architecturally compared with plain chat?

### Scenario 3
An MCP server exposes an internal deployment tool. Does tool discovery mean the coding agent should automatically have production deployment rights?

### Scenario 4
A sensitive folder must never be supplied to Copilot. Would you solve this primarily with a prompt or with policy/context controls?

### Scenario 5
Why can a specialist security subagent be useful?

### Scenario 6
Why is "generated 1,000 lines" a weak productivity metric?

---

# 16. Day 6 Oral Checkpoint

Without notes, explain:

1. Chat vs Agent Mode.
2. Agent session vs memory.
3. Primary agent vs subagent.
4. MCP's role in Copilot.
5. Tool discovery vs authorization.
6. Repository context vs safe context.
7. Content exclusion vs prompt instruction.
8. Why human validation remains required.
9. How Copilot improves productivity beyond code completion.
10. Difference between a coding agent and an application agent.

## PASS CONDITION

Pass if at least **8/10** answers are clear and scenario-based.

---

# 17. Transition to Hands-On

Day 6 closes the concept rush.

Next four sessions intentionally combine AI-103 and GH-300:

```text
DAY 7
Design one application agent

DAY 8
Tool + RAG + MCP integration

DAY 9
Workflow + Multi-Agent orchestration

DAY 10
Use an AI coding workflow to build/review the agent system
```

The goal is to stop learning certificates as isolated vocabularies and turn them into one engineering model.
