# Week 01 — 5-Day Harness Learning Plan

## Objective

Build a practical, framework-independent understanding of agent system architecture for the BD Chunk / Super Agent Harness project.

Total study time: **15–20 hours**  
Daily time: **3–4 hours/day**

## Final Outputs of the Week

By the end of Day 5, create or update:

1. `SA_HANDBOOK.md` — central architecture KB.
2. A canonical diagram of the target harness.
3. A concept mapping table across LangGraph, Claude Code, OpenAI Agents SDK, and Microsoft Agent Framework.
4. A first version of the BD Harness runtime flow.

---

# Day 1 — Agent Architecture Foundation

## Theme

Workflow vs Agent vs Planner vs Orchestrator.

## Main Source

Anthropic Academy / Anthropic Learn

- https://www.anthropic.com/learn
- Focus: AI Fluency, Claude foundation, agent workflow concepts.

## Time Plan — 3.5 hours

| Time | Activity |
|---:|---|
| 0:00–0:30 | Read Anthropic Learn overview and identify relevant courses. |
| 0:30–1:30 | Study AI Fluency / foundation material. |
| 1:30–2:15 | Read or review Anthropic's agent design ideas: workflow, agent, tool use, context. |
| 2:15–3:00 | Write concept notes: Workflow, Agent, Tool, Context, Planning. |
| 3:00–3:30 | Update `SA_HANDBOOK.md` sections: `Workflow vs Agent`, `Canonical Architecture`. |

## Deliverable

Create a 1-page concept map:

```text
Workflow
Agent
Planner
Orchestrator
Router
Scheduler
Tool
Context
```

## Key Question

When should we use a deterministic workflow, and when should we allow agent autonomy?

---

# Day 2 — Claude Code / Artifact-Centric Architecture

## Theme

Workspace, artifact store, Git, file-based state, coding agent runtime.

## Main Source

Claude Code in Action

- https://anthropic.skilljar.com/claude-code-in-action

## Why This Matters

Claude Code is a strong example of an artifact-centric agent system. It treats the repo, files, Git diff, tests, and terminal output as the operational workspace.

## Time Plan — 4 hours

| Time | Activity |
|---:|---|
| 0:00–0:30 | Skim course overview and curriculum. |
| 0:30–1:30 | Study coding assistant architecture and project setup. |
| 1:30–2:15 | Study context control and project resources. |
| 2:15–3:00 | Study GitHub integration / MCP / hooks conceptually. |
| 3:00–4:00 | Map Claude Code concepts to BD Harness architecture. |

## Deliverable

Add to `SA_HANDBOOK.md`:

```text
Artifact-Centric Architecture
Workspace as State
Git as Checkpoint Layer
Spec → Code → Test artifact chain
```

## BD Harness Mapping

```text
/specs/screen/login.md
/specs/api/login_api.md
/specs/db/user_table.md
/deliverables/basic_design.xlsx
/reviews/traceability_report.md
```

## Key Question

Which information should be stored in runtime state, and which should become a file artifact?

---

# Day 3 — Skills, MCP, and Tool Layer

## Theme

Skill library, reusable workflows, tool registry, external system integration.

## Main Sources

Anthropic Academy

- https://www.anthropic.com/learn
- Focus: Agent Skills, MCP, Claude Code extensibility.

Optional Reference:

- Claude Code in Action: MCP servers, custom commands, hooks.

## Time Plan — 3.5 hours

| Time | Activity |
|---:|---|
| 0:00–0:45 | Study Agent Skills concept. |
| 0:45–1:30 | Study MCP concept and tool discovery. |
| 1:30–2:15 | Define Skill Library for BD Harness. |
| 2:15–3:00 | Define Tool Registry for BD Harness. |
| 3:00–3:30 | Update `SA_HANDBOOK.md` with Skill and Tool architecture. |

## Deliverable

Draft the first BD Harness Skill Library:

```text
Requirement Chunking Skill
RD Fact Extraction Skill
QA Classification Skill
Screen Design Skill
API Design Skill
DB Design Skill
Traceability Review Skill
Excel Export Skill
```

## Key Question

What is the boundary between a skill, an agent, and a tool?

---

# Day 4 — Microsoft Enterprise Agent Architecture

## Theme

Enterprise-grade agent systems: multi-agent, governance, responsible AI, deployment, orchestration.

## Main Sources

Microsoft AI Agents for Beginners

- https://github.com/microsoft/ai-agents-for-beginners

Microsoft AI Agents Professional Certificate on Coursera

- https://www.coursera.org/professional-certificates/microsoft-ai-agents

## Time Plan — 4 hours

| Time | Activity |
|---:|---|
| 0:00–0:45 | Skim Microsoft AI Agents for Beginners structure. |
| 0:45–1:30 | Study agent design and multi-agent concepts. |
| 1:30–2:15 | Review Coursera certificate outcomes and enterprise skills. |
| 2:15–3:00 | Extract enterprise requirements: security, responsible AI, deployment, testing. |
| 3:00–4:00 | Map these concerns to BD Harness governance. |

## Deliverable

Add to `SA_HANDBOOK.md`:

```text
Enterprise Governance
Human Review
Approval Gates
Traceability
Audit Log
Evaluation
Security Boundary
```

## Key Question

What must be human-gated in a BD document generation workflow?

---

# Day 5 — LangGraph / State-Centric Orchestration + Canonical Architecture

## Theme

StateGraph, nodes, routing, checkpointing, human-in-the-loop, canonical framework mapping.

## Main Sources

DeepLearning.AI — AI Agents in LangGraph

- https://www.deeplearning.ai/courses/ai-agents-in-langgraph

LangChain Academy — Foundation: Introduction to LangGraph

- https://academy.langchain.com/courses/intro-to-langgraph

## Time Plan — 4 hours

| Time | Activity |
|---:|---|
| 0:00–1:00 | Study LangGraph components: state, node, edge, router. |
| 1:00–1:45 | Study persistence/checkpoint and human-in-the-loop concepts. |
| 1:45–2:30 | Compare LangGraph state-centric model vs Claude Code artifact-centric model. |
| 2:30–3:30 | Build canonical mapping table across frameworks. |
| 3:30–4:00 | Finalize `SA_HANDBOOK.md` v0.1. |

## Deliverable

Create the first canonical architecture map:

```text
Canonical Agent Architecture
├── Goal
├── Input Intake
├── Planner
├── Orchestrator
├── Scheduler
├── Runtime State
├── Artifact Store
├── Knowledge Base
├── Skill Library
├── Tool Registry
├── Agent Pool
├── Review / Validation
└── Deliverables
```

## Key Question

If we switch from LangGraph to OpenAI Agents SDK, which parts of the architecture should remain unchanged?

---

# End-of-Week Review

## Required Final Checklist

- [ ] Can explain Planner vs Orchestrator.
- [ ] Can explain State vs Artifact vs Memory.
- [ ] Can explain why Claude Code is artifact-centric.
- [ ] Can explain why LangGraph is state-centric.
- [ ] Can define a Skill Library for BD Harness.
- [ ] Can define human review gates for BD outputs.
- [ ] Can map the same architecture to LangGraph, Claude Code, OpenAI Agents SDK, and Microsoft Agent Framework.
- [ ] Can draw the first version of the BD Harness architecture without looking at external references.

## Final Artifact

Update `SA_HANDBOOK.md` and treat it as the project KB for future harness design decisions.
