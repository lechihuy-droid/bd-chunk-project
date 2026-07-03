# 01 — Requirement Phase Playbook

## 1. Objective

The Requirement Phase defines the business problem, target capability, governance model, MVP scope, and success metrics before any meaningful platform build begins.

The goal is to avoid a technology-first build and ensure that the MVP is anchored in business value.

## 2. Phase duration

Recommended duration:

```text
2-4 weeks
```

Recommended structure:

```text
Week 1: CEO alignment and current-state diagnostic
Week 2: Stakeholder interviews, artifact review, pain point and KPI baseline
Week 3: Target workflow, governance, MVP scope, requirement pack
Week 4: Requirement gate review and MVP handoff, if needed
```

## 3. Key questions

### CEO / Sponsor questions

```text
1. Which business metric should AI improve after 12 months?
2. Is the primary value productivity, quality, speed, risk reduction, or growth?
3. Which business process is painful enough to justify the platform?
4. Which AI outputs must be human-approved?
5. What evidence is required after 90 days to justify scale?
```

### Business / Delivery questions

```text
1. Where is manual effort concentrated?
2. Which tasks are repetitive but still require senior review?
3. Which review comments repeat across projects?
4. Which outputs require traceability?
5. Which source documents are reliable enough for pilot use?
```

### Governance questions

```text
1. Can client documents be used in AI workflow?
2. Which data must be masked or restricted?
3. What audit trail is required?
4. Who approves requirement interpretation?
5. Who approves final BD output?
```

## 4. Core activities

### Activity 1 — CEO alignment

Purpose:

```text
Confirm that this is a business transformation program, not an AI app experiment.
```

Outputs:

```text
- CEO Alignment Note
- Transformation Charter v0.1
- Strategic value hypothesis
```

### Activity 2 — Current process diagnostic

Map current process:

```text
RD / QA / Meeting Notes
  -> Requirement clarification
  -> RCD creation
  -> BD mapping
  -> BD draft
  -> Review
  -> Excel delivery
```

Capture:

```text
- Process steps
- Owners
- Inputs and outputs
- Effort by step
- Waiting time
- Review loops
- Pain points
```

### Activity 3 — Artifact review

Collect and review:

```text
- RD documents
- QA sheets
- Meeting notes
- Existing RCD files
- Existing BD templates
- Review comments
- Delivery checklists
```

Assess:

```text
- Structure
- Completeness
- Ambiguity
- Source traceability
- Reuse potential
- Data sensitivity
```

### Activity 4 — Pain point and value tree

Build a value tree connecting pain to measurable business value.

```text
Super AI Transformation Platform
  -> Productivity value
  -> Quality value
  -> Speed value
  -> Governance value
  -> Reuse / scale value
```

### Activity 5 — Use case prioritization

Score candidate use cases by:

```text
1. Business value
2. Effort reduction potential
3. Repeatability
4. Output structure clarity
5. Data readiness
6. Risk controllability
7. Measurability
8. Executive visibility
9. Reuse potential
```

Recommended first use case:

```text
RD / QA / Meeting Notes -> RCD -> BD Mapping -> BD Draft -> Validation
```

### Activity 6 — Target workflow design

Define target AI-assisted workflow:

```text
Input Collection
  -> RD Parsing
  -> Requirement Structuring
  -> RCD Candidate Generation
  -> Human Gate 1: BA Approval
  -> BD Mapping
  -> BD Draft Generation
  -> Validation
  -> Human Gate 2: Architect Review
  -> Excel Export
  -> KPI Measurement
```

### Activity 7 — Governance and human gate design

Define human gates:

```text
Gate 1: BA approves RCD before BD mapping.
Gate 2: Architect approves BD draft and validation before export.
Gate 3: Client reviewer approval if output becomes client-facing.
```

Define policies:

```text
- Evidence policy
- Source reference policy
- Unsupported claim policy
- Human approval policy
- Data boundary policy
```

### Activity 8 — MVP scope lock

Lock MVP scope using the rule:

```text
Only build components required to prove the first business use case.
```

MVP should include:

```text
- File-based workflow runner
- Project workspace
- Agent config
- Skill packages
- Human gate status
- Validation report
- Excel export prototype
- KPI capture
```

## 5. Requirement phase deliverables

```text
1. CEO Alignment Note
2. Transformation Charter
3. Stakeholder Map
4. Current Process Map
5. Pain Point Heatmap
6. Effort Baseline
7. Review Issue Taxonomy
8. Data Readiness Assessment
9. Use Case Prioritization Matrix
10. Target Workflow Blueprint
11. Human Gate Policy
12. Evidence and Traceability Policy
13. MVP Scope Definition
14. KPI Baseline and Measurement Plan
```

## 6. Requirement gate checklist

Move to MVP only if all conditions are true:

```text
1. Sponsor confirms business objective.
2. Business owner is assigned.
3. First use case is selected.
4. Pilot scope is bounded.
5. Input documents are available.
6. Current process baseline is captured.
7. Target workflow is approved.
8. Human gates are approved.
9. Traceability requirement is defined.
10. MVP scope is approved by business and technical leads.
```

## 7. Exit criteria

The phase is complete when the team can answer:

```text
- What business pain are we solving?
- Which KPI will improve?
- Which workflow will AI assist?
- Which decisions remain human-approved?
- Which source artifacts will be used?
- What exactly will the MVP build?
```

## 8. Engagement manager notes

During this phase, the Engagement Manager should prevent three failure modes:

```text
1. The team starts discussing models/frameworks too early.
2. The sponsor expects full automation without governance.
3. MVP scope expands beyond what is needed to prove the first use case.
```