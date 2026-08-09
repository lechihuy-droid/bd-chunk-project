# Harness Learning Path

This folder is the learning and architecture knowledge base for the BD Chunk / Super Agent Harness initiative.

## Goal

Build a framework-independent mental model for designing an enterprise-grade agent harness for Basic Design (BD) work.

The target architecture is not tied to a single framework such as LangGraph, Claude Code, OpenAI Agents SDK, or Microsoft Agent Framework. The goal is to define a canonical architecture first, then map each framework to that architecture.

## Learning Tracks

### 1. AI Agent Engineering — 3-Week Bootcamp

Main track for learning to build AI agents and a production-style multi-agent harness while mapping the work to Microsoft AI-103, AAAI-1/2, AI-500, and the later Frontier/Titan direction.

- [`AI_AGENT_3_WEEK_LEARNING_PATH.md`](./AI_AGENT_3_WEEK_LEARNING_PATH.md)
- [`VOICE_LEARNING_PROGRESS.md`](./VOICE_LEARNING_PROGRESS.md) — live voice-first learning notes and checkpoints

Current voice-learning progress: **Day 1–Day 4 completed conceptually; Day 5 is next.**

### 2. Harness Architecture — 5-Day Path

Focused architecture track for the canonical Super Agent Harness model.

- [`WEEK01_5_DAY_PLAN.md`](./WEEK01_5_DAY_PLAN.md)
- [`SA_HANDBOOK.md`](./SA_HANDBOOK.md)

## Core Learning Outcome

By the end of the architecture path, you should be able to explain and design the following components clearly:

```text
Goal
  ↓
Input Intake
  ↓
Planner
  ↓
Execution Plan
  ↓
Orchestrator / Runtime
  ↓
State + Artifact Store + Knowledge Base
  ↓
Agent Pool
  ↓
Review / Validation
  ↓
Deliverables
```

The 3-week AI Agent track extends this into:

```text
LLM / Model
  ↓
Tools + MCP
  ↓
Single Agent
  ↓
Workflow Runtime
  ↓
Multi-Agent Orchestration
  ↓
State / Memory / Knowledge
  ↓
Human Gate
  ↓
Evaluation / Observability / Security
  ↓
Runnable BD Chunk Agent Harness PoC
```

## Folder Structure

```text
harness-learning-path/
├── README.md
├── AI_AGENT_3_WEEK_LEARNING_PATH.md
├── VOICE_LEARNING_PROGRESS.md
├── WEEK01_5_DAY_PLAN.md
├── DAY02_ARTIFACT_CENTRIC_ARCHITECTURE.md
├── DAY03_HOOK_TRIGGER_INTEGRATION_RUNTIME_OBSERVABILITY.md
├── SA_HANDBOOK.md
└── REFERENCES.md
```

## Main Artifacts

For agent engineering:

```text
AI_AGENT_3_WEEK_LEARNING_PATH.md
VOICE_LEARNING_PROGRESS.md
```

For canonical harness architecture:

```text
SA_HANDBOOK.md
```

The handbook should become the project knowledge base for agent system architecture decisions.

## How to Use These Paths

For the 3-week AI Agent bootcamp, use approximately 4 hours/day and evolve the same BD Chunk / RD→BD capstone every day.

The current learning mode can be voice-first: explain concepts verbally, answer checkpoints verbally, correct the mental model, then map it to implementation later. API access is not required for the early conceptual days.

For the architecture path, each day requires approximately 3–4 hours.

Recommended daily cycle:

```text
1. Learn from selected course/source
2. Extract concept notes
3. Map concept to BD Harness
4. Build or update one artifact/lab
5. Update SA_HANDBOOK.md when an architecture decision stabilizes
6. Write one architecture decision or diagram
```

## Priority

Do not learn more frameworks first. Focus on the canonical concepts:

- Planner
- Orchestrator
- Scheduler
- State
- Artifact Store
- Workspace
- Memory
- Knowledge Base
- Skills
- Tools / MCP
- Agent Pool
- Human Review
- Traceability
- Evaluation
- Governance

Frameworks are implementation mappings after the canonical architecture is understood.
