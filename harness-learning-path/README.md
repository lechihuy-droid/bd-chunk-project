# Harness Learning Path

This folder is the learning and architecture knowledge base for the BD Chunk / Super Agent Harness initiative.

## Latest / Canonical Learning Path

> **LATEST as of 2026-08-09:** the canonical learning path is the complete **Day 1–21 certification sprint + Titan / Frontier continuation**.
>
> Start here: [`LATEST.md`](./LATEST.md)

Canonical sequence:

```text
Day 1–3   — AI-103 concept rush
        ↓
Day 4–6   — GH-300 concept rush
        ↓
Day 7–10  — 4 integrated AI-103 + GH-300 hands-on sessions
        ↓
Day 11–21 — AB-100 intensive
        ↓
Titan / Project Ready
        ↓
Center of Excellence + Hypervelocity Engineering + delivery patterns
        ↓
Frontier Transformation Engineer
```

The files and indexes under `certifications/` are the authoritative day-by-day material for this path.

Older learning plans in this folder are retained as **reference / historical material** and must not override the canonical sequence above unless a later version explicitly replaces `LATEST.md`.

## Goal

Build a framework-independent mental model for designing enterprise-grade AI agent systems while following the Microsoft Frontier / Titan certification path.

The architecture is not tied to a single framework such as LangGraph, Claude Code, OpenAI Agents SDK, or Microsoft Agent Framework. Canonical concepts come first; product/framework mappings come after.

## Primary Learning Track

### Frontier / Titan — 21-Day Certification Sprint

Main high-level roadmap:

- [`AI_AGENT_3_WEEK_LEARNING_PATH.md`](./AI_AGENT_3_WEEK_LEARNING_PATH.md)

Detailed sprint indexes:

- [`certifications/DAY01_DAY05_CERT_SPRINT_INDEX.md`](./certifications/DAY01_DAY05_CERT_SPRINT_INDEX.md)
- [`certifications/DAY06_DAY10_CERT_AND_HANDSON_INDEX.md`](./certifications/DAY06_DAY10_CERT_AND_HANDSON_INDEX.md)
- [`certifications/DAY11_DAY15_AB100_INDEX.md`](./certifications/DAY11_DAY15_AB100_INDEX.md)
- [`certifications/DAY16_DAY20_AB100_INDEX.md`](./certifications/DAY16_DAY20_AB100_INDEX.md)
- [`certifications/DAY21_TO_TITAN_FRONTIER_INDEX.md`](./certifications/DAY21_TO_TITAN_FRONTIER_INDEX.md)

Certificate-level material:

- [`certifications/AI-103_3_DAY_RUSH.md`](./certifications/AI-103_3_DAY_RUSH.md)
- [`certifications/ai-103/`](./certifications/ai-103/)
- [`certifications/gh-300/`](./certifications/gh-300/)
- [`certifications/hands-on/`](./certifications/hands-on/)
- [`certifications/ab-100/`](./certifications/ab-100/)
- [`certifications/titan/FRONTIER_TRANSFORMATION_ENGINEER_PATH.md`](./certifications/titan/FRONTIER_TRANSFORMATION_ENGINEER_PATH.md)

Voice-learning record:

- [`VOICE_LEARNING_PROGRESS.md`](./VOICE_LEARNING_PROGRESS.md)

## Harness Architecture Track

Separate focused architecture material:

- [`WEEK01_5_DAY_PLAN.md`](./WEEK01_5_DAY_PLAN.md)
- [`DAY02_ARTIFACT_CENTRIC_ARCHITECTURE.md`](./DAY02_ARTIFACT_CENTRIC_ARCHITECTURE.md)
- [`DAY03_HOOK_TRIGGER_INTEGRATION_RUNTIME_OBSERVABILITY.md`](./DAY03_HOOK_TRIGGER_INTEGRATION_RUNTIME_OBSERVABILITY.md)
- [`SA_HANDBOOK.md`](./SA_HANDBOOK.md)
- [`REFERENCES.md`](./REFERENCES.md)

These files are supporting architecture references, not a replacement for the current certification sprint.

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

## Versioning Rule

Use these rules when the learning path evolves:

1. `LATEST.md` always points to the current canonical path.
2. `README.md` must identify the same path as latest.
3. Previous learning plans remain available as reference unless they are factually unsafe or explicitly removed.
4. A new version becomes canonical only when both `LATEST.md` and this README are updated.
5. Official Microsoft credential requirements should be re-verified before exam booking or Titan / Frontier completion.
