# Implementation Detail — Declarative Super Agent Harness

## 1. Purpose

This document summarizes the implementation approach for a Declarative Super Agent Harness focused on BD delivery.

Target workflow:

```text
RD / QA / Meeting Notes
  -> RCD
  -> BD Mapping
  -> BD Draft
  -> Validation
  -> Human Review
  -> Excel Export
```

The implementation should treat AI work as a controlled artifact pipeline, not as a simple chatbot interaction.

---

## 2. MVP scope

Start with a file-based Harness before building the full visual platform.

MVP modules:

```text
1. Project workspace
2. Workflow definition
3. Skill package loader
4. Agent runner
5. Shared filesystem
6. Blackboard state
7. Human gate mechanism
8. Validation engine
9. Excel export
```

MVP flow:

```text
Input Manager
  -> RD Parser Agent
  -> RCD Builder Agent
  -> Human Gate 1
  -> BD Mapping Agent
  -> BD Draft Agent
  -> Validation Agent
  -> Human Gate 2
  -> Excel Export Agent
```

---

## 3. Recommended repository structure

```text
bd-ai-harness/
  projects/
    project_alpha/
      inputs/
      intermediate/
      artifacts/
      reviews/
      logs/
      state/

  workflows/
    bd_generation/
      workflow.md
      workflow.yaml

  agents/
    lead_bd_agent/agent.yaml
    rd_parser_agent/agent.yaml
    rcd_builder_agent/agent.yaml
    bd_mapping_agent/agent.yaml
    screen_bd_agent/agent.yaml
    api_bd_agent/agent.yaml
    db_bd_agent/agent.yaml
    batch_if_bd_agent/agent.yaml
    consistency_review_agent/agent.yaml
    excel_export_agent/agent.yaml

  skills/
    rd_parse/SKILL.md
    rcd_extract/SKILL.md
    gap_detection/SKILL.md
    bd_mapping/SKILL.md
    screen_bd/SKILL.md
    api_bd/SKILL.md
    db_bd/SKILL.md
    batch_if_bd/SKILL.md
    consistency_check/SKILL.md
    traceability_check/SKILL.md
    excel_export/SKILL.md

  policies/
    human_gate_policy.md
    evidence_policy.md
    access_policy.md

  evals/
    coverage_check.yaml
    consistency_check.yaml
    traceability_check.yaml
    format_check.yaml

  runtime/
    orchestrator.py
    graph_builder.py
    agent_runner.py
    skill_loader.py
    tool_executor.py
    state_manager.py
    validation_runner.py
    artifact_exporter.py
```

---

## 4. Runtime components

### 4.1 Workflow Orchestrator

Responsibilities:

- Load `workflow.yaml`.
- Validate workflow schema.
- Build execution graph.
- Resolve dependencies.
- Execute steps sequentially or in parallel.
- Stop at human gates.
- Trigger retry or recovery logic.
- Persist execution state.

Suggested engine: LangGraph StateGraph.

### 4.2 Agent Runner

Responsibilities:

- Load `agent.yaml`.
- Build agent instruction from role, goal, and policies.
- Attach scoped context.
- Attach permitted tools.
- Load relevant skill metadata.
- Execute model call.
- Write structured output.
- Check termination rule.

### 4.3 Skill Loader

Use progressive disclosure:

```text
Stage 1: Load skill metadata only.
Stage 2: Load full SKILL.md when selected.
Stage 3: Load schema files when output validation is needed.
Stage 4: Load examples or scripts only when required.
```

### 4.4 Tool Executor

Possible tools:

- Read and write files.
- Read and write Excel.
- Parse PDF, Word, and Markdown.
- Search project knowledge base.
- Search Git repository.
- Query DB schema.
- Generate Mermaid or review reports.
- Export final artifact package.

Tool execution must be controlled by agent permissions.

### 4.5 State Manager

Maintains blackboard state such as:

- Project ID.
- Current phase.
- Approved RCD path.
- Open issues.
- Validation results.
- Human gate status.
- Artifact locations.

---

## 5. Workflow configuration model

The workflow should define:

- Workflow ID and version.
- Input project directory.
- Nodes.
- Dependencies.
- Agent assignment.
- Input and output paths.
- Human gates.
- Parallel execution groups.
- Validation phase.
- Export phase.

Example node types:

```text
agent
human_gate
parallel
condition
retry
export
```

Recommended BD workflow nodes:

```text
ingest
build_rcd
human_gate_1
bd_mapping
bd_fanout
screen_bd
api_bd
db_bd
batch_if_bd
validation
human_gate_2
export
```

---

## 6. Agent configuration model

Each agent should define:

- Agent ID.
- Name.
- Role.
- Goal.
- Context scope.
- Assigned skills.
- Applied policies.
- Allowed tools.
- Model policy.
- Output contract.
- Termination rule.

Example for RCD Builder Agent:

```text
agent_id: rcd_builder_agent
role: Requirement Structuring Agent
goal: Convert parsed RD input into structured RCD candidate items.
context_scope: parsed requirements and source references
skills: rcd_extract, gap_detection
allowed_tools: read_file, write_json, search_kb
output: rcd_candidate.json
termination: every item has source reference; unclear items are marked PENDING_DECISION
```

---

## 7. Skill package model

Each skill should be a reusable package, not only a prompt.

Recommended skill structure:

```text
skills/rcd_extract/
  SKILL.md
  schema.input.json
  schema.output.json
  examples/
  tests/
```

`SKILL.md` should contain:

- Purpose.
- Input.
- Output.
- Rules.
- Failure modes.
- Recovery approach.
- Examples.
- Test cases.

For BD project, initial skills should include:

- RD parse.
- RCD extract.
- Gap detection.
- BD mapping.
- Screen BD generation.
- API BD generation.
- DB BD generation.
- Batch/IF BD generation.
- Consistency check.
- Traceability check.
- Excel export.

---

## 8. Human gate model

Human gate should be treated as a first-class workflow node.

Recommended gate states:

```text
pending
approved
rejected
needs_revision
escalated
```

Runtime behavior:

```text
approved -> continue workflow
rejected -> stop workflow
needs_revision -> return to previous agent with reviewer comments
escalated -> notify owner or architect
```

BD gates:

```text
Gate 1: BA approves RCD before BD generation.
Gate 2: Architect reviews BD consistency and design direction.
Gate 3: Client reviewer approves final delivery pack if required.
```

---

## 9. Validation model

Validation should run before final export and after major artifact generation.

Key checks:

| Check | Objective |
|---|---|
| Coverage check | Every approved RCD item is addressed in BD artifacts. |
| Consistency check | Screen, API, DB, Batch, and IF designs do not contradict each other. |
| Traceability check | Every generated BD item has a source reference. |
| Conflict detection | Unresolved decisions, duplicate rules, and incompatible assumptions are flagged. |
| Format check | Output conforms to Excel or template requirements. |

---

## 10. Traceability data model

Traceability should be stored as structured records linking source input to final artifact.

Recommended fields:

```text
trace_id
source_file
source_sheet
source_cell_range
source_text
rcd_id
bd_target_type
bd_target_id
artifact_file
artifact_sheet
artifact_cell_range
coverage_status
review_status
```

Traceability principle:

```text
Every generated BD item must link back to a requirement, QA item, meeting note, approved decision, or source cell.
```

---

## 11. Implementation roadmap

### Phase 1 — File-based Harness MVP

Deliver:

- `workflow.yaml` runner.
- `agent.yaml` loader.
- `SKILL.md` loader.
- Shared project directory.
- Basic blackboard state.
- Basic human gate.
- Basic validation reports.

### Phase 2 — BD workflow MVP

Deliver:

- RD parser skill.
- RCD extract skill.
- Gap detection skill.
- BD mapping skill.
- Basic BD draft skill.
- Excel export skill.
- Traceability output.

### Phase 3 — Visual Workflow Builder

Deliver:

- Canvas UI.
- Agent node.
- Skill node.
- Human gate node.
- Edge and condition node.
- Save as `workflow.yaml`.
- Load `workflow.yaml` into UI.

### Phase 4 — Sub-agent Runtime

Deliver:

- Lead agent.
- Child task packet.
- Scoped context.
- Parallel execution.
- Shared blackboard coordination.
- Sub-agent output merge.

### Phase 5 — Evaluation and Learning Loop

Deliver:

- Coverage score.
- Consistency score.
- Traceability score.
- Skill failure tracking.
- Skill versioning.
- Prompt and version audit.

---

## 12. Success metrics

Productivity metrics:

- Time to create RCD.
- Time to create BD draft.
- Time to prepare review package.
- Manual copy/paste reduction.

Quality metrics:

- Traceability coverage rate.
- Number of missing source references.
- Number of contradictions detected.
- Number of review comments.
- Rework cycle count.

Governance metrics:

- Human gate approval rate.
- Number of policy violations.
- Number of unsupported AI claims.
- Audit completeness rate.

Reuse metrics:

- Skill reuse count.
- Workflow reuse count.
- Prompt and version stability.
- Reduction of repeated failure modes.

---

## 13. Implementation principle

Bad pattern:

```text
User asks -> Agent answers -> User manually copies output
```

Good pattern:

```text
Input artifact -> Controlled workflow -> Agent/skill execution -> Validation -> Human gate -> Versioned output artifact
```

The final goal is to make AI-generated delivery work:

```text
repeatable,
traceable,
reviewable,
measurable,
and reusable.
```
