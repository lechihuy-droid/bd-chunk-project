# Harness Learning Path

This folder is the learning and architecture knowledge base for the BD Chunk / Super Agent Harness initiative.

## Goal

Build a framework-independent mental model for designing enterprise-grade AI agent systems while following the Microsoft Frontier / Titan certification path.

The architecture is not tied to a single framework such as LangGraph, Claude Code, OpenAI Agents SDK, or Microsoft Agent Framework. Canonical concepts come first; product/framework mappings come after.

## Primary Learning Track

### Frontier / Titan — 21-Day Certification Sprint

```text
AI-103 — 3-day concept rush
        ↓
GH-300 — 3-day concept rush
        ↓
4 integrated hands-on sessions
        ↓
AB-100 — 11-day intensive
        ↓
Titan / Project Ready / Frontier
```

Main roadmap:

- [`AI_AGENT_3_WEEK_LEARNING_PATH.md`](./AI_AGENT_3_WEEK_LEARNING_PATH.md)

Detailed certification units:

- [`certifications/AI-103_3_DAY_RUSH.md`](./certifications/AI-103_3_DAY_RUSH.md) — Certificate #1

Voice-learning record:

- [`VOICE_LEARNING_PROGRESS.md`](./VOICE_LEARNING_PROGRESS.md)

## Certificate #1 — AI-103

**Microsoft Certified: Azure AI Apps and Agents Developer Associate**

Current strategy:

```text
Day 1 — Foundry + Model + Agent + Platform
Day 2 — Generative AI + RAG + Tools + Agents
Day 3 — Vision + Text + Extraction + Security + Operations + Exam Review
```

Implementation is intentionally deferred into the four integrated hands-on sessions after the GH-300 concept rush.

## Harness Architecture Track

Separate focused architecture material:

- [`WEEK01_5_DAY_PLAN.md`](./WEEK01_5_DAY_PLAN.md)
- [`DAY02_ARTIFACT_CENTRIC_ARCHITECTURE.md`](./DAY02_ARTIFACT_CENTRIC_ARCHITECTURE.md)
- [`DAY03_HOOK_TRIGGER_INTEGRATION_RUNTIME_OBSERVABILITY.md`](./DAY03_HOOK_TRIGGER_INTEGRATION_RUNTIME_OBSERVABILITY.md)
- [`SA_HANDBOOK.md`](./SA_HANDBOOK.md)
- [`REFERENCES.md`](./REFERENCES.md)

## Canonical Architecture

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
Agent Pool + Tools / MCP
  ↓
Review / Validation / Human Gate
  ↓
Evaluation / Observability / Governance
  ↓
Deliverables
```

## Learning Mode

The current learning mode can be voice-first.

```text
Official objective
      ↓
Mental model
      ↓
Explain verbally
      ↓
Challenge scenario
      ↓
Exam-style checkpoint
      ↓
Hands-on validation later
```

API access is not required for the early concept-rush days. Python/SDK knowledge is still required at code-reading level for AI-103 and will be exercised during hands-on sessions.

## Priority

Do not learn more frameworks first. Focus on:

- Model vs Agent
- Agent vs Tool
- Workflow Runtime
- State / Context / Memory / Knowledge
- Agent Contracts
- RAG / Search
- Tools / MCP
- Multi-Agent Orchestration
- Human Review
- Security
- Evaluation
- Observability
- Governance

Frameworks are implementation mappings after the canonical architecture is understood.
