# Personal Skill Library — Source Strategy

**Date:** 2026-06-29  
**Status:** Draft / Planning  
**Scope:** Source strategy, vendor-neutral architecture, taxonomy, adoption rules, and target structure for the BD / Opus skill library.

---

## 1. Purpose

This document defines how to build a personal and BD-oriented skill library.

The skill library should not be a random prompt collection. It should become a curated standard library for repeatable personal, research, execution, and BD workflows.

Core idea:

```text
Official skills and SDK patterns
→ community workflow patterns
→ vendor-neutral pattern library
→ runtime-specific adapters
→ reusable personal / BD operating workflows
```

The goal is not to copy any single ecosystem directly. The goal is to extract durable patterns and normalize them into a tool-agnostic format that can be used by Claude, Codex, ChatGPT, OpenAI Agents SDK, Gemini, Cursor, or future agent runtimes.

---

## 2. Vendor-Neutral Architecture

Do not make Claude, Codex, OpenAI, Gemini, or GStack the source of truth.

Use this architecture:

```text
Knowledge / Research Source
        ↓
Pattern Layer
        ↓
Workflow Layer
        ↓
Playbook Layer
        ↓
Skill Layer
        ↓
Runtime Adapter Layer
        ├── Claude Code
        ├── Codex
        ├── OpenAI Agents SDK
        ├── Gemini CLI
        ├── Cursor
        └── Future runtimes
```

Meaning:

| Layer | Role | Example |
|---|---|---|
| Knowledge | Raw source or reference | Claude docs, OpenAI docs, GStack repo |
| Pattern | Reusable concept | Review gate, context loading, handoff |
| Workflow | Repeatable process | Repo review, research pack, BD review |
| Playbook | Operational best practice | How to evaluate a repo for adoption |
| Skill | Executable unit | `repo-review`, `bd-review`, `decision-review` |
| Adapter | Runtime-specific implementation | `claude.md`, `codex.md`, `openai.md` |

Rule:

```text
Pattern is the source of truth.
Runtime adapter is replaceable.
```

---

## 3. Source Priority

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
Vendor-neutral for source of truth.
Runtime-specific only at adapter layer.
```

---

## 4. Four-Layer Skill Taxonomy

### 4.1 Core Skills

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

These should be learned primarily from official Claude/OpenAI/Codex patterns, then normalized into a vendor-neutral schema.

Expected role:

```text
General building blocks used by all subsystems.
```

---

### 4.2 Workflow Skills

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

These should not be copied directly from GStack. Extract the pattern, then adapt to BD / Opus.

Expected role:

```text
Turn one-shot prompting into multi-step operating flows with review gates.
```

---

### 4.3 Personal Skills

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

### 4.4 BD / Work Skills

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
Bridge harness learning with enterprise BD Stack design.
```

---

## 5. Target Folder Structure

Recommended structure for `bd-chunk-project`:

```text
bd-chunk-project/
  docs/
    PERSONAL-SKILL-LIBRARY-SOURCES.md
  harness/
    knowledge-sources/
      claude/
      openai/
      gstack/
      ecc/
      cursor/
      gemini/
    patterns/
      review-gate.md
      context-loading.md
      handoff.md
      tool-calling.md
      workflow-orchestration.md
    workflows/
      repo-review.md
      research-pack.md
      bd-review.md
      decision-review.md
    playbooks/
      repo-evaluation-playbook.md
      harness-learning-playbook.md
      bd-workflow-playbook.md
    skills/
      repo-review/
        skill.yaml
        claude.md
        codex.md
        openai.md
        gemini.md
      bd-review/
        skill.yaml
        claude.md
        codex.md
        openai.md
      templates/
        skill-template.yaml
        workflow-template.md
        command-template.md
```

Important:

```text
Do not treat runtime-specific files as source of truth.
skill.yaml is the canonical definition.
claude.md / codex.md / openai.md are adapters.
```

---

## 6. Skill Format

Do not store skills as unstructured prompts.

Use a normalized schema:

```yaml
name: repo-review
version: 0.1
status: draft
canonical_layer: skill
owner_domain: harness
runtime_neutral: true

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
  - compare against current roadmap
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

adapters:
  claude: claude.md
  codex: codex.md
  openai: openai.md
  gemini: gemini.md

approval_required:
  - before writing to source-of-truth files
```

This format keeps the skill portable across Claude, Codex, OpenAI Agents SDK, Gemini, and future runtimes.

---

## 7. Runtime Adapter Rule

Each runtime adapter translates the canonical skill into the runtime's conventions.

Example:

```text
skills/repo-review/
  skill.yaml    # canonical source of truth
  claude.md     # Claude Code command / skill style
  codex.md      # Codex CLI / AGENTS.md compatible style
  openai.md     # OpenAI Agents SDK / tool-calling style
  gemini.md     # Gemini CLI compatible style
```

Adapter responsibilities:

| Adapter | Responsibility |
|---|---|
| `claude.md` | Slash command wording, Claude Code context instructions, subagent hints |
| `codex.md` | Terminal/Codex workflow, repo file handling, verification steps |
| `openai.md` | Agent instructions, tool contract, structured output schema |
| `gemini.md` | Gemini CLI prompt/command variant |

Adapter rule:

```text
If adapter conflicts with skill.yaml, skill.yaml wins.
```

---

## 8. Pattern / Workflow / Playbook / Skill Split

Do not mix these layers.

| Type | Meaning | Example |
|---|---|---|
| Pattern | Reusable concept | Review Gate |
| Workflow | Ordered process | Repo Review Workflow |
| Playbook | Human-facing best practice | How to evaluate a repo |
| Skill | Executable package | `/repo-review` |
| Adapter | Runtime implementation | Claude/Codex/OpenAI/Gemini variant |

Recommended flow:

```text
Pattern
  ↓
Workflow
  ↓
Playbook
  ↓
Skill
  ↓
Runtime Adapter
```

This prevents vendor lock-in and keeps the knowledge reusable.

---

## 9. Adoption Rules

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

Use BD / Opus-specific design for workflows such as decision, learning, PMP, JLPT, BD review, traceability, and repo research.

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

If a workflow produces only a chat answer, it is not yet a skill.

### Rule 6 — Adapter can change, canonical skill should not

A runtime-specific adapter may be rewritten when Claude/Codex/OpenAI/Gemini changes.

The canonical skill should remain stable unless the workflow itself changes.

---

## 10. Initial Skill Backlog

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

## 11. GStack Adoption Target

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

Map to vendor-neutral patterns first:

| GStack Pattern | Neutral Pattern | BD / Opus Use |
|---|---|---|
| Office hours | Intake workflow | Nexus / BD intake packet |
| CEO review | Strategy review gate | Logos / presales value review |
| Engineering review | Technical review gate | Rector / BD feasibility review |
| QA/browser | Verification harness | Screen/API/dashboard QA |
| Release | Handoff + decision log | Delivery / documentation update |
| Skills | Skill package | `skill.yaml` + adapters |
| Slash commands | Runtime command adapter | Claude/Codex command variants |

---

## 12. Relationship to Harness Roadmap

Skill library is the user-facing API of the harness.

```text
Harness Engineering
  ├── Official Skills and SDK Patterns
  ├── Community Workflow Patterns
  ├── Pattern Library
  ├── Workflow Library
  ├── Playbook Library
  ├── Skill Library
  ├── Runtime Adapters
  ├── Review Gates
  ├── Context Loading Policy
  └── Durable Artifacts
```

Frameworks such as LangGraph, MCP, or OpenAI Agents SDK define execution and tool layers.

The skill library defines how the user actually operates the system.

---

## 13. Recommended Next Actions

1. Add GStack as a P0 harness learning target.
2. Create `harness/patterns/`, `harness/workflows/`, `harness/playbooks/`, and `harness/skills/` after confirming this structure.
3. Create `skill-template.yaml`, `workflow-template.md`, and `command-template.md`.
4. Implement the first P0 skill: `repo-review`.
5. Add Claude and Codex adapters for `repo-review` first; OpenAI/Gemini can follow later.

---

## 14. Final Principle

```text
A prompt answers once.
A skill compounds.
A runtime adapter executes.
A vendor-neutral skill library becomes an operating system.
```