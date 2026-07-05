# Harness Learning Path

This folder is the learning and architecture knowledge base for the BD Chunk / Super Agent Harness initiative.

## Goal

Build a framework-independent mental model for designing an enterprise-grade agent harness for Basic Design (BD) work.

The target architecture is not tied to a single framework such as LangGraph, Claude Code, OpenAI Agents SDK, or Microsoft Agent Framework. The goal is to define a canonical architecture first, then map each framework to that architecture.

## Core Learning Outcome

By the end of this 5-day path, you should be able to explain and design the following components clearly:

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

## Folder Structure

```text
harness-learning-path/
├── README.md
├── WEEK01_5_DAY_PLAN.md
├── SA_HANDBOOK.md
└── REFERENCES.md
```

## Main Artifact

The main artifact of this learning path is:

```text
SA_HANDBOOK.md
```

This handbook should become the project knowledge base for agent system architecture decisions.

## How to Use This Path

Each day requires approximately 3–4 hours.

Recommended daily cycle:

```text
1. Learn from selected course/source
2. Extract concept notes
3. Map concept to BD Harness
4. Update SA_HANDBOOK.md
5. Write one architecture decision or diagram
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
- Tools
- Agent Pool
- Human Review
- Traceability
- Evaluation
- Governance
