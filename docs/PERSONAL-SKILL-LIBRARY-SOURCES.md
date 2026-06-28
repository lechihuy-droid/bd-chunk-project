# Personal Skill Library — Source Strategy

**Date:** 2026-06-29  
**Status:** Draft / Planning  
**Scope:** Source strategy, taxonomy, adoption rules, and target structure for the Opus Animus personal skill library.

---

## 1. Purpose

This document defines how Opus Animus should build a personal skill library.

The skill library should not be a random prompt collection. It should become a curated standard library for repeatable personal, research, execution, and BD workflows.

Core idea:

```text
Official skills and SDK patterns
→ community workflow patterns
→ Opus-specific skill templates
→ reusable personal operating workflows
```

The goal is not to copy any single ecosystem directly. The goal is to extract durable patterns and normalize them into an Opus-native format that can be used by Claude, ChatGPT, Codex, Gemini, or future agent runtimes.

---

## 2. Source Priority

| Priority | Source | What to Learn |
|---|---|---|
| P0 | Claude official skills / Claude Code | Skill structure, slash commands, workflow conventions, coding-agent ergonomics |
| P0 | OpenAI Agents SDK / Codex patterns | Tool calling, handoff, guardrails, structured outputs, agent workflow boundaries |
| P0 | GStack | Role orchestration, review gates, software-factory workflow, browser/QA harness patterns |
| P1 | GitHub Copilot | Workspace context, code review style, developer workflow integration |
| P1 | Cursor | Rules, context loading, workspace-level prompting |
| P1 | Gemini CLI | CLI agent workflow, command design, cross-model comparison |
| P1 | ECC and agent-engineering repos | Agent engineering patterns, drop-in commands, review/checking conventions |
| P2 | Community skill repos | Idea mining only; adopt after verification and normalization |

Rule:

```text
Official-first for primitives.
Community-first for workflow inspiration.
Opus-first for final structure.
```

---

## 3. Four-Layer Skill Taxonomy

### 3.1 Core Skills

Core skills are stable, general-purpose operations used across many workflows.

Examples:

```text
research
plan
review
debug
refactor
summarize
document
test
```

These should be learned primarily from official Claude/OpenAI/Codex patterns.

Expected role:

```text
General building blocks used by all subsystems.
```

---

### 3.2 Workflow Skills

Workflow skills orchestrate multiple core skills into a repeatable process.

Examples inspired by GStack:

```text
office-hours
strategy-review
engineering-review
qa-review
ship
release
browser-test
```

These should not be copied directly from GStack. Extract the pattern, then adapt to Opus.

Expected role:

```text
Turn one-shot prompting into multi-step operating flows with review gates.
```

---

### 3.3 Personal Skills

Personal skills encode Huy-specific workflows.

Examples:

```text
repo-review
paper-review
decision-review
weekly-review
finance-ingest
health-review
house-plan
trip-plan
pmp-review
jlpt-content
```

Expected role:

```text
Convert repeated personal workflows into durable commands and templates.
```

This is the most valuable layer because it cannot be copied from public repos.

---

### 3.4 BD / Work Skills

BD skills support AI-assisted Basic Design and enterprise workflow transformation.

Examples:

```text
rd-analysis
ontology-build
chunk-index
traceability-review
bd-review
mapping-review
rcd-review
```

Expected role:

```text
Bridge Personal OS harness learning with enterprise BD Stack design.
```

---

## 4. Target Folder Structure

Proposed structure:

```text
opus-animus/
  skills/
    official/
      claude/
      openai/
      gemini/
    adopted/
      gstack/
      ecc/
      cursor/
    personal/
      finance/
      knowledge/
      learning/
      decision/
      travel/
    bd/
      ontology/
      mapping/
      review/
    templates/
      skill-template.md
      workflow-template.md
      command-template.md
    patterns/
      prompt-patterns.md
      workflow-patterns.md
      review-patterns.md
```

Important:

```text
Do not create the full folder structure until the source-of-truth map is updated.
```

The operating model already states that no agent should create a new source of truth without registering it. This skill library should therefore be registered as either:

```text
opus-animus/skills/ = executable/reusable workflow library
```

or, if it remains research-only at first:

```text
opus-animus/04_harness/skills/ = harness practice artifacts
```

---

## 5. Skill Format

Do not store skills as unstructured prompts.

Use a normalized schema:

```yaml
name: repo-review
version: 0.1
status: draft
owner_subsystem: Consilium

intent:
  Evaluate a repository and decide whether it should be adopted, studied, ignored, or archived.

inputs:
  - github_url
  - evaluation_context
  - target_use_case

steps:
  - identify repository purpose
  - inspect README and architecture docs
  - inspect commits and maturity signals
  - extract reusable patterns
  - compare against current Opus roadmap
  - write recommendation
  - update reading list or decision log if approved

outputs:
  - repo-review.md
  - extracted-patterns.md
  - adoption-decision.md

quality_gate:
  - source was checked directly
  - architecture was reviewed
  - risks were identified
  - adoption decision is explicit
  - next action is clear

approval_required:
  - before writing to source-of-truth files
```

This format keeps the skill portable across Claude, ChatGPT, Codex, Gemini, and future runtimes.

---

## 6. Adoption Rules

### Rule 1 — Source before adoption

Every imported or inspired skill must record its source.

```text
source_name
source_url
license_if_known
pattern_extracted
what_was_not_adopted
```

### Rule 2 — Pattern, not copy

Prefer extracting patterns over copying full prompts or implementation.

```text
Copying creates dependency.
Pattern extraction creates capability.
```

### Rule 3 — Official primitives, personal workflows

Use official Claude/OpenAI/Codex patterns for primitives such as tool use, structured outputs, handoff, and guardrails.

Use Opus-specific design for workflows such as finance, decision, learning, PMP, JLPT, BD review, and repo research.

### Rule 4 — Every skill needs a quality gate

A skill without a quality gate is only a prompt.

Minimum quality gate:

```text
input clarity
source checked
output schema followed
risks considered
next action defined
```

### Rule 5 — Every workflow skill should produce durable artifacts

For example:

```text
/repo-review
→ repo-review.md
→ extracted-patterns.md
→ decision-log entry
→ reading-list update
```

If a workflow produces only a chat answer, it is not yet an Opus skill.

---

## 7. Initial Skill Backlog

### P0 Skills

```text
repo-review
research-pack
decision-review
weekly-review
harness-experiment
```

### P1 Skills

```text
finance-ingest
paper-review
bd-review
traceability-review
jlpt-content
```

### P2 Skills

```text
travel-plan
health-review
house-plan
personal-retrospective
```

---

## 8. GStack Adoption Target

GStack should be treated as a workflow-harness reference, not as a direct dependency.

Extract these patterns:

```text
skill library organization
slash command naming
role-based review
multi-step planning
human review gate
browser/QA harness
release/documentation workflow
```

Map to Opus:

| GStack Pattern | Opus Adaptation |
|---|---|
| Office hours | Nexus intake / intent packet |
| CEO review | Logos strategy review |
| Engineering review | Rector execution review |
| QA/browser | Nexus dashboard QA / workflow verification |
| Release | handoff + status update + decision log |
| Skills | Opus skill library |
| Slash commands | Opus command layer |

---

## 9. Relationship to Harness Roadmap

Skill library is the user-facing API of the Personal OS.

```text
Harness Engineering
  ├── Official Skills and SDK Patterns
  ├── Community Workflow Patterns
  ├── Opus Skill Library
  ├── Review Gates
  ├── Context Loading Policy
  └── Durable Artifacts
```

Frameworks such as LangGraph, MCP, or OpenAI Agents SDK define execution and tool layers.

The skill library defines how the user actually operates the system.

---

## 10. Recommended Next Actions

1. Add GStack to `opus-consilium/personal-wiki/Research/consilium-reading-list.md` as a P0 queued item.
2. Create `opus-animus/04_harness/repos/gstack/repo-review.md` after source-of-truth registration.
3. Create `skill-template.md`, `workflow-template.md`, and `command-template.md`.
4. Implement the first P0 skill: `repo-review`.
5. Update `opus-animus/ai/status.md` so the current objective reflects harness practice, not the older LLM migration task.

---

## 11. Final Principle

```text
A prompt answers once.
A skill compounds.
A skill library becomes an operating system.
```