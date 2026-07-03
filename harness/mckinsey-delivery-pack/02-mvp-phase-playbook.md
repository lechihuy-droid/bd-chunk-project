# 02 — MVP Phase Playbook

## 1. Objective

The MVP Phase builds the smallest governed AI artifact pipeline that can prove value on the first BD use case.

The MVP must not be treated as a full product build. It is a controlled business proof point.

MVP objective:

```text
Prove that a file-based, human-gated, traceability-first Harness can convert pilot BD inputs into reviewable RCD, BD mapping, validation report, and Excel output.
```

## 2. Entry criteria

Do not start MVP unless the Requirement Phase has produced:

```text
1. Approved pilot use case
2. Bounded pilot scope
3. Available input artifacts
4. Target workflow blueprint
5. Human gate policy
6. Evidence and traceability policy
7. MVP scope definition
8. KPI baseline
```

## 3. MVP scope

### In scope

```text
- Project workspace
- File-based workflow runner
- Agent config loader
- Skill package loader
- RD parsing
- RCD candidate generation
- Human Gate 1: BA approval
- BD mapping generation
- BD draft generation
- Validation report
- Human Gate 2: Architect review
- Excel export prototype
- KPI capture
```

### Out of scope

```text
- Full visual workflow builder
- Full production UI
- Enterprise multi-tenant setup
- Autonomous client-facing output
- Complete multi-agent marketplace
- Advanced model routing optimization
```

## 4. MVP architecture

```text
Pilot Input Package
  -> Project Workspace
  -> workflow.yaml
  -> Orchestrator
  -> Agent Runner
  -> Skill Loader
  -> Tool Executor
  -> Shared Filesystem
  -> Blackboard State
  -> Validation Runner
  -> Human Gate Status
  -> Excel Exporter
  -> KPI Report
```

## 5. Target workflow

```text
1. Input collection
2. Document ingestion
3. RD parsing
4. Requirement fact extraction
5. RCD candidate generation
6. BA approval gate
7. BD mapping
8. BD draft generation
9. Validation
10. Architect approval gate
11. Excel export
12. KPI report
```

## 6. Sprint plan

### Sprint 0 — MVP setup

Duration: 3-5 days

Objectives:

```text
- Confirm MVP scope
- Confirm pilot inputs
- Confirm output templates
- Confirm baseline KPI
- Set repository/workspace structure
```

Deliverables:

```text
- MVP backlog
- Input package list
- Output template list
- Baseline KPI sheet
- Workspace structure
```

Exit criteria:

```text
Business owner, BA, Architect, and platform lead approve MVP scope.
```

### Sprint 1 — Runtime skeleton

Duration: 1 week

Build items:

```text
- workflow.yaml schema
- orchestrator skeleton
- agent runner skeleton
- state manager
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
Workflow runner can execute mock nodes and persist state.
```

### Sprint 2 — Ingestion and RCD generation

Duration: 1-2 weeks

Build items:

```text
- RD Parser Agent
- RD Parse Skill
- RCD Builder Agent
- RCD Extract Skill
- Gap Detection Skill
- Source reference model
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
Each RCD item has source reference or PENDING_DECISION flag.
```

### Sprint 3 — Human Gate 1 and BD mapping

Duration: 1 week

Build items:

```text
- BA approval status file
- Review comment structure
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
Workflow stops until BA approval exists.
BD mapping uses only approved RCD items.
```

### Sprint 4 — BD draft and validation

Duration: 1-2 weeks

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
Architect can review BD draft and validation summary.
Missing coverage and unsupported claims are flagged.
```

### Sprint 5 — Human Gate 2, export, KPI report

Duration: 1 week

Build items:

```text
- Architect approval status file
- Excel Export Agent
- Excel Export Skill
- KPI capture template
- Pilot result summary template
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
Final output can be reviewed as realistic BD delivery package.
KPI report can compare MVP output to manual baseline.
```

## 7. MVP success criteria

The MVP is successful if:

```text
1. It processes real or realistic BD input.
2. It produces RCD candidates with source references.
3. It stops at BA approval before BD mapping.
4. It generates BD mapping from approved RCD.
5. It generates reviewable BD draft.
6. It validates coverage, consistency, and traceability.
7. It stops at Architect approval before export.
8. It exports realistic Excel delivery pack prototype.
9. It captures KPI for effort and quality comparison.
10. BA and Architect can understand and review output.
```

## 8. Target metrics

```text
- 20-30% reduction in RCD / BD draft effort
- 80-90% traceability coverage
- 0 critical unsupported claims in reviewed output
- 5-10 reusable skills created
- 1 reusable workflow template created
- 1 validated pilot package generated
```

## 9. MVP gate review

Gate question:

```text
Can the Harness process project input and produce reviewable, traceable, human-gated BD output?
```

Required evidence:

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

Decision options:

```text
Go to pilot
Revise MVP
Stop / re-scope
```

## 10. Engagement manager weekly checklist

```text
1. Is the team solving the agreed business pain?
2. Are MVP components tied to KPI?
3. Are BA and Architect involved in review?
4. Are source references preserved?
5. Are unsupported AI claims flagged?
6. Is the team avoiding UI overbuild?
7. Are skills reusable?
8. Is pilot baseline ready?
9. Are stage-gate artifacts collected?
10. Is sponsor still aligned?
```