# Phase 3 Plan — File-based Harness MVP After Diagnostic

## 1. Purpose

This document defines the MVP phase after the business diagnostic and target operating model design are completed.

The goal is not to build a full AI application. The goal is to build the smallest governed AI artifact pipeline that can prove business value on the first BD use case.

MVP positioning:

```text
Business diagnostic defines what matters.
MVP proves that the new AI-assisted operating model can run on real project artifacts.
```

The MVP should validate four hypotheses:

```text
1. AI can reduce manual effort in RD -> RCD -> BD preparation.
2. AI output can be made reviewable by BA and Architect.
3. AI-generated artifacts can preserve source traceability.
4. Human gates and validation can control risk sufficiently for enterprise delivery.
```

---

## 2. Required inputs from diagnostic phase

The MVP must not start until the following diagnostic outputs are available.

```text
1. Current Process Map
2. Pain Point Heatmap
3. Effort Baseline
4. Review Issue Taxonomy
5. Data Readiness Assessment
6. Pilot Scope Recommendation
7. Target Workflow Blueprint
8. Human Gate Policy
9. Evidence and Traceability Policy
10. MVP Scope Definition
```

If these are missing, the team is at risk of building a generic AI demo instead of a transformation MVP.

---

## 3. MVP design principles

### 3.1 Business-first

Every MVP component must map to a business pain or KPI.

```text
Business pain -> MVP capability -> Technical component -> KPI
```

Example:

```text
BA spends too much time structuring requirements
  -> RCD generation capability
  -> RCD Builder Agent + RCD Extract Skill
  -> RCD creation time reduction
```

### 3.2 File-based before UI-based

Do not build the Visual Workflow Builder first.

Start with:

```text
workflow.yaml
agent.yaml
SKILL.md
shared project folder
validation reports
human approval status file
```

This proves the operating model before investing in UI.

### 3.3 Human-gated by design

The MVP should not automate decisions that require BA, Architect, or client approval.

AI drafts. Humans approve.

### 3.4 Traceability-first

Every generated RCD or BD item must have a source reference or be flagged as pending decision.

### 3.5 Reusable asset mindset

Every workflow, skill, prompt, validation rule, and policy should be designed as a reusable asset.

---

## 4. MVP scope

### In scope

```text
1. Project workspace structure
2. Document ingestion from selected pilot files
3. RD parsing into structured facts
4. RCD candidate generation
5. Human Gate 1: BA approval
6. BD mapping generation
7. Basic BD draft generation
8. Validation report generation
9. Human Gate 2: Architect review
10. Excel export prototype
11. KPI capture for effort and quality
```

### Out of scope

```text
1. Full Visual Workflow Builder
2. Full enterprise access control
3. Full multi-tenant architecture
4. Full production UI
5. Full autonomous sub-agent execution
6. Client-facing output without human review
7. Large-scale model routing optimization
8. Enterprise skill marketplace
```

---

## 5. Target MVP workflow

```text
Pilot Input Package
  -> Ingestion Step
  -> RD Parser Agent
  -> RCD Builder Agent
  -> Human Gate 1: BA Approval
  -> BD Mapping Agent
  -> BD Draft Agent
  -> Validation Agent
  -> Human Gate 2: Architect Review
  -> Excel Export Agent
  -> KPI Report
```

Detailed workflow:

```text
1. Collect input files into project workspace.
2. Parse RD, QA sheet, and meeting notes.
3. Generate structured requirement facts with source references.
4. Generate RCD candidate items.
5. BA reviews and approves/rejects RCD items.
6. Generate BD mapping from approved RCD.
7. Generate draft BD artifact sections.
8. Validate coverage, consistency, and traceability.
9. Architect reviews validation and BD draft.
10. Export Excel delivery pack prototype.
11. Measure effort reduction and quality indicators.
```

---

## 6. MVP architecture

```text
Project Workspace
  -> workflow.yaml
  -> Orchestrator
  -> Agent Runner
  -> Skill Loader
  -> Tool Executor
  -> Shared Filesystem
  -> Blackboard State
  -> Validation Runner
  -> Human Gate Status
  -> Artifact Exporter
```

### 6.1 Project workspace

Recommended structure:

```text
projects/pilot_bd_001/
  inputs/
  intermediate/
  artifacts/
  reviews/
  logs/
  state/
  metrics/
```

### 6.2 Workflow configuration

The MVP workflow should be defined in a declarative file:

```text
workflows/bd_mvp/workflow.yaml
```

It should contain:

```text
- node id
- node type
- assigned agent
- input path
- output path
- dependency
- human gate rule
- validation rule
```

### 6.3 Agent configuration

Each agent should have a simple `agent.yaml`.

Required fields:

```text
- agent_id
- role
- goal
- context_scope
- allowed_tools
- assigned_skills
- output_contract
- termination_rule
```

### 6.4 Skill package

Each skill should be stored as a package:

```text
skills/<skill_name>/SKILL.md
```

Required sections:

```text
- Purpose
- Input
- Output
- Rules
- Failure modes
- Recovery behavior
- Examples
- Tests
```

### 6.5 Blackboard state

The MVP should maintain a simple state file:

```text
projects/pilot_bd_001/state/blackboard.json
```

It should track:

```text
- current_phase
- input_files
- generated_artifacts
- approved_rcd_path
- open_issues
- validation_results
- human_gate_status
- metric_status
```

---

## 7. MVP components and ownership

| Component | Purpose | Owner |
|---|---|---|
| Project workspace | Store inputs, outputs, logs, state, metrics | Platform Engineer |
| Workflow runner | Execute workflow from config | Platform Engineer |
| Agent runner | Run agent instructions and model calls | AI Workflow Engineer |
| Skill loader | Load SKILL.md and related schemas | Skill Engineer |
| Document parser | Convert input docs to structured facts | Knowledge Engineer |
| RCD Builder | Generate RCD candidates | Skill Engineer + BA Lead |
| BD Mapping | Map RCD to BD sections | Skill Engineer + Architect |
| Validation runner | Check coverage, consistency, traceability | QA / Validation Lead |
| Human gate | Capture approval and review comments | BA Lead / Architect |
| Excel exporter | Produce delivery pack prototype | Platform Engineer |
| KPI capture | Track effort and quality metrics | Engagement Manager / PMO |

---

## 8. MVP sprint plan

### Sprint 0 — MVP setup

Duration: 3-5 days

Objectives:

```text
- Lock MVP scope.
- Confirm pilot input package.
- Confirm output template.
- Confirm metric baseline.
- Set up repository structure.
```

Deliverables:

```text
- MVP backlog
- Pilot input package
- Output template list
- Repository structure
- Baseline KPI sheet
```

Exit criteria:

```text
- Business owner approves MVP scope.
- BA/Architect approve target artifacts.
- Engineering team can access sample inputs.
```

---

### Sprint 1 — Runtime skeleton and workspace

Duration: 1 week

Objectives:

```text
- Build file-based workflow runner.
- Set up project workspace.
- Implement blackboard state.
- Implement basic logging.
```

Build items:

```text
- workflow.yaml schema
- orchestrator skeleton
- state manager
- folder conventions
- execution log format
```

Deliverables:

```text
- Runnable empty workflow
- Project workspace template
- blackboard.json
- run log
```

Exit criteria:

```text
- Workflow runner can execute mock nodes in sequence.
- State is persisted after each node.
```

---

### Sprint 2 — Ingestion, RD parsing, and RCD generation

Duration: 1-2 weeks

Objectives:

```text
- Parse pilot input documents.
- Generate structured requirement facts.
- Generate RCD candidate items.
- Preserve source references.
```

Build items:

```text
- RD Parser Agent
- RD Parse Skill
- RCD Builder Agent
- RCD Extract Skill
- Gap Detection Skill
- source reference model
```

Deliverables:

```text
- parsed_requirements.json
- rcd_candidate.json
- open_issues.json
- source_reference_report.json
```

Exit criteria:

```text
- RCD candidates are reviewable by BA.
- Each RCD item has source reference or PENDING_DECISION flag.
```

---

### Sprint 3 — Human Gate 1 and BD mapping

Duration: 1 week

Objectives:

```text
- Add BA approval mechanism.
- Generate BD mapping only from approved RCD.
- Create mapping between RCD and BD target sections.
```

Build items:

```text
- human_gate_1 status file
- review comment format
- BD Mapping Agent
- BD Mapping Skill
- bd_mapping.jsonl
```

Deliverables:

```text
- rcd_approved.json
- review_comments_gate_1.json
- bd_mapping.jsonl
```

Exit criteria:

```text
- Workflow stops until BA approval exists.
- BD mapping uses only approved RCD items.
```

---

### Sprint 4 — BD draft and validation

Duration: 1-2 weeks

Objectives:

```text
- Generate basic BD draft sections.
- Validate coverage, consistency, and traceability.
- Prepare review package for Architect.
```

Build items:

```text
- BD Draft Agent
- BD Draft Skill
- Validation Agent
- Coverage Check Skill
- Consistency Check Skill
- Traceability Check Skill
```

Deliverables:

```text
- bd_draft.json or bd_draft.xlsx
- coverage_report.json
- consistency_report.json
- traceability_report.json
- validation_summary.md
```

Exit criteria:

```text
- Architect can review BD draft and validation summary.
- Missing coverage and unsupported claims are flagged.
```

---

### Sprint 5 — Human Gate 2, Excel export, and KPI report

Duration: 1 week

Objectives:

```text
- Add Architect review gate.
- Export final MVP delivery pack.
- Capture KPI for pilot comparison.
```

Build items:

```text
- human_gate_2 status file
- Excel Export Agent
- Excel Export Skill
- KPI capture template
- pilot result summary template
```

Deliverables:

```text
- final_delivery_pack.xlsx
- validation_summary.md
- pilot_kpi_report.md
- mvp_demo_script.md
```

Exit criteria:

```text
- Final output can be reviewed as a realistic BD delivery package.
- KPI report can compare MVP output to manual baseline.
```

---

## 9. MVP success criteria

The MVP is successful if it meets these conditions:

```text
1. It can process real or realistic BD input.
2. It produces RCD candidates with source references.
3. It stops at BA approval before BD mapping.
4. It generates BD mapping from approved RCD.
5. It generates a reviewable BD draft.
6. It validates coverage, consistency, and traceability.
7. It stops at Architect approval before export.
8. It exports a realistic Excel delivery pack prototype.
9. It captures KPI for effort and quality comparison.
10. BA and Architect can understand and review the output.
```

Suggested target metrics:

```text
- 20-30% reduction in RCD / BD draft effort.
- 80-90% traceability coverage.
- 0 critical unsupported claims in final reviewed output.
- 5-10 reusable skills created.
- 1 reusable workflow template created.
- 1 validated pilot package generated.
```

---

## 10. MVP stage gate

At the end of the MVP phase, run Gate 3 review.

Gate question:

```text
Can the Harness process project input and produce reviewable, traceable, human-gated BD output?
```

Decision options:

```text
Go to pilot:
MVP is stable enough for real project pilot.

Revise MVP:
MVP works but key quality, traceability, or usability gaps remain.

Stop / re-scope:
MVP cannot prove value or the use case is not feasible with current data/process.
```

Required evidence for Gate 3:

```text
1. Demo run log
2. Input package
3. RCD candidate output
4. BA approval record
5. BD mapping output
6. BD draft output
7. Validation report
8. Architect review record
9. Excel export sample
10. KPI capture sheet
```

---

## 11. Management checklist for Engagement Manager

During the MVP phase, the engagement manager should check weekly:

```text
1. Is the team still solving the agreed business pain?
2. Are MVP components tied to target KPI?
3. Are BA and Architect involved in review?
4. Are source references preserved?
5. Are unsupported AI claims being flagged?
6. Is the team avoiding full UI overbuild?
7. Are skills being written as reusable assets?
8. Is the pilot baseline ready?
9. Are stage gate artifacts being collected?
10. Is the sponsor still aligned on success criteria?
```

---

## 12. Final recommendation

The MVP after diagnostic should be deliberately narrow.

Do not attempt to build the full transformation platform immediately.

Build this first:

```text
A file-based, human-gated, traceability-first BD Harness that can convert pilot input into reviewable RCD, BD mapping, validation report, and Excel output.
```

Only after this MVP proves value should the program move to:

```text
Visual Workflow Builder
Skill Library UI
Multi-agent runtime
Governance dashboard
Enterprise scale platform
```
