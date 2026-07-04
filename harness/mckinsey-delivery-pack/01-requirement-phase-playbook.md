# 01 — Requirement Phase Playbook

## 1. Objective

The Requirement Phase defines the business problem, target capability, governance model, requirement baseline, MVP scope, and success metrics before any meaningful platform build begins.

The goal is to avoid a technology-first build and create a **build-ready transformation requirement pack** for the File-based Harness MVP.

This phase must answer:

```text
1. What business pain are we solving?
2. Which process will AI transform?
3. Which outputs must be generated?
4. Which decisions remain human-approved?
5. Which data and artifacts are available?
6. Which KPI will prove value?
7. What exactly should the MVP build?
```

---

## 2. Phase duration and cadence

Recommended duration:

```text
2-4 weeks
```

Recommended structure:

```text
Week 1: CEO alignment and current-state diagnostic
Week 2: Stakeholder interviews, artifact review, pain point and KPI baseline
Week 3: Target workflow, governance, requirement taxonomy, MVP scope
Week 4: Requirement gate review and MVP handoff, if needed
```

Recommended cadence:

```text
Weekly sponsor check-in
2-3 working sessions with BA / Architect / PMO
Weekly requirement synthesis review
Final Requirement Gate review before MVP build
```

---

## 3. Requirement phase output model

The phase must produce three packs.

### 3.1 Business Requirement Pack

Purpose: prove that the initiative is business-led.

Required outputs:

```text
- CEO Alignment Note
- Transformation Charter
- Business problem statement
- Value tree
- Use case prioritization matrix
- KPI baseline and measurement plan
```

### 3.2 Operating Model Pack

Purpose: define how the AI-assisted process should work.

Required outputs:

```text
- Current process map
- Target workflow blueprint
- Role and RACI model
- Human gate policy
- Review model
- Exception and escalation rules
```

### 3.3 MVP Requirement Pack

Purpose: hand off clear requirements to the MVP build team.

Required outputs:

```text
- Requirement taxonomy
- Functional requirements
- Non-functional requirements
- Data requirements
- Artifact/output requirements
- Governance requirements
- Validation requirements
- MVP acceptance criteria
- Build handoff checklist
- Requirement traceability matrix
```

---

## 4. Key questions

### 4.1 CEO / Sponsor questions

```text
1. Which business metric should AI improve after 12 months?
2. Is the primary value productivity, quality, speed, risk reduction, growth, or differentiation?
3. Which business process is painful enough to justify the platform?
4. Which AI outputs must be human-approved?
5. What evidence is required after 90 days to justify scale?
6. Who is accountable for business value?
```

### 4.2 Business / Delivery questions

```text
1. Where is manual effort concentrated?
2. Which tasks are repetitive but still require senior review?
3. Which review comments repeat across projects?
4. Which outputs require traceability?
5. Which source documents are reliable enough for pilot use?
6. Which output templates are mandatory for client delivery?
```

### 4.3 Governance questions

```text
1. Can client documents be used in AI workflow?
2. Which data must be masked or restricted?
3. What audit trail is required?
4. Who approves requirement interpretation?
5. Who approves final BD output?
6. What is not allowed for AI to decide?
```

### 4.4 Technical handoff questions

```text
1. Which input files will be used in the MVP?
2. Which output artifacts must be produced?
3. Which workflow steps must be implemented?
4. Which human gates are mandatory?
5. Which validation checks are mandatory?
6. Which fields must appear in each output artifact?
```

---

## 5. Core activities

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
- Business owner nomination
```

---

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
- Manual effort by step
- Waiting time
- Review loops
- Pain points
- Rework causes
- Existing tools and templates
```

---

### Activity 3 — Artifact and data readiness review

Collect and review:

```text
- RD documents
- QA sheets
- Meeting notes
- Existing RCD files
- Existing BD templates
- Review comments
- Delivery checklists
- Excel templates
```

Assess:

```text
- Document structure
- Completeness
- Ambiguity
- Source traceability
- Reuse potential
- Data sensitivity
- Excel sheet structure
- Merged cells / unstable formatting
- Japanese terminology consistency
- Ability to trace to file / sheet / row / cell
```

Required data readiness output:

```text
Data Readiness Assessment
  -> usable as-is
  -> usable with cleanup
  -> usable only for limited scope
  -> not usable for MVP
```

---

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

Each pain point must connect to:

```text
- affected role
- current effort or issue
- expected improvement
- KPI
- possible MVP capability
```

---

### Activity 5 — Baseline measurement

The requirement phase must establish a practical baseline before MVP starts.

Baseline does not need to be perfect, but it must be good enough for before/after comparison.

| Baseline | Measurement method | Owner | Required before MVP |
|---|---|---|---|
| RCD creation effort | Interview + sample task timing | BA Lead / PMO | Yes |
| BD draft effort | Historical estimate + reviewer input | Architect / PMO | Yes |
| Review preparation time | Reviewer estimate + sample observation | PMO | Preferred |
| Review comment count | Past review log or sample review | QA Lead | Preferred |
| Traceability coverage | Sample artifact audit | QA Lead | Yes |
| Rework cycle count | PMO/project history | PMO | Preferred |

Minimum baseline required for MVP:

```text
1. RCD creation effort baseline
2. BD draft effort baseline
3. Traceability coverage baseline
4. Review process baseline
```

---

### Activity 6 — Use case prioritization

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

Use case selection rule:

```text
Select the use case that is valuable, measurable, bounded, and governable.
Do not select a use case only because it is easy to demo.
```

---

### Activity 7 — Target workflow design

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

For each workflow step define:

```text
- input artifact
- output artifact
- owner
- AI role
- human role
- validation rule
- exception path
- completion criteria
```

---

### Activity 8 — Governance and human gate design

Define human gates:

```text
Gate 1: BA approves RCD before BD mapping.
Gate 2: Architect approves BD draft and validation before export.
Gate 3: Client reviewer approval if output becomes client-facing.
```

For each human gate define:

```text
- Gate ID
- Reviewer role
- Input artifact
- Review criteria
- Decision options
- SLA
- Output artifact
- Escalation rule
```

Decision options:

```text
approved
rejected
needs_revision
escalated
```

Required policies:

```text
- Evidence policy
- Source reference policy
- Unsupported claim policy
- Human approval policy
- Data boundary policy
- Audit policy
```

---

### Activity 9 — Requirement taxonomy

Use the following taxonomy to structure MVP requirements.

```text
BR — Business Requirement
PR — Process Requirement
FR — Functional Requirement
NFR — Non-functional Requirement
DR — Data Requirement
GR — Governance Requirement
VR — Validation Requirement
AR — Artifact Requirement
MR — Measurement Requirement
```

Examples:

```text
BR-001: Reduce manual effort in RCD creation.
PR-001: Workflow must stop after RCD candidate generation for BA approval.
FR-001: System must generate rcd_candidate.json from parsed requirement facts.
NFR-001: MVP must persist intermediate outputs and run logs.
DR-001: Every extracted item must preserve source file, sheet, and cell range where available.
GR-001: AI-generated BD output must not be exported before Architect approval.
VR-001: Validation must check whether every approved RCD item is mapped to at least one BD section.
AR-001: Final output must be exportable to Excel delivery template.
MR-001: MVP must capture effort and quality metrics for pilot comparison.
```

---

### Activity 10 — Artifact and output requirement definition

Define output structure before MVP build.

#### RCD Candidate

Required fields:

```text
rcd_id
requirement_text
category
source_ref
confidence
status
open_issue_ref
```

#### BD Mapping

Required fields:

```text
mapping_id
rcd_id
bd_target_type
bd_target_id
rationale
source_ref
status
```

#### BD Draft

Required fields:

```text
bd_item_id
bd_section
design_content
related_rcd_id
source_ref
assumption
open_issue_ref
review_status
```

#### Validation Report

Required fields:

```text
check_id
check_type
target_artifact
result
severity
finding
recommended_action
```

#### KPI Report

Required fields:

```text
metric_id
metric_name
baseline
current_result
target
status
measurement_method
owner
```

---

### Activity 11 — MVP scope lock

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

MVP must not include:

```text
- Full visual workflow builder
- Full enterprise UI
- Full multi-tenant platform
- Unreviewed client-facing output
- Large-scale multi-agent marketplace
```

---

## 6. MVP acceptance criteria

MVP acceptance criteria must be approved during the requirement phase.

The MVP is accepted only if:

```text
1. It processes selected pilot inputs.
2. It generates RCD candidates with source references.
3. It stops at BA approval before BD mapping.
4. It generates BD mapping from approved RCD only.
5. It generates reviewable BD draft.
6. It produces validation report.
7. It stops at Architect approval before export.
8. It exports Excel prototype.
9. It captures KPI for comparison.
10. BA and Architect can review and understand outputs.
```

Minimum target metrics:

```text
- RCD / BD draft effort reduction can be measured.
- Traceability coverage can be measured.
- Unsupported AI claims are flagged.
- Human approval records are captured.
- Reusable skills and workflow assets are created.
```

---

## 7. Requirement traceability matrix

Create a requirement traceability matrix before MVP build.

Required mapping:

```text
Business Pain
  -> Requirement ID
  -> MVP Capability
  -> Workflow Step
  -> Agent / Skill
  -> KPI
  -> Acceptance Criteria
```

Example:

| Business pain | Requirement | MVP capability | KPI | Acceptance criteria |
|---|---|---|---|---|
| BA spends effort creating RCD | BR-001 / FR-001 | RCD Builder Agent | RCD effort reduction | RCD candidate generated with source refs |
| Review lacks evidence | GR-001 / DR-001 | Traceability Check | Traceability coverage | Every item has source_ref or pending flag |
| Architect spends time checking consistency | VR-001 | Validation Agent | Review comment reduction | Validation report identifies gaps |

---

## 8. Requirement phase deliverables

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
13. Requirement Taxonomy
14. Artifact Requirement Definition
15. MVP Acceptance Criteria
16. Requirement Traceability Matrix
17. MVP Scope Definition
18. KPI Baseline and Measurement Plan
19. Build Handoff Checklist
```

---

## 9. Requirement gate checklist

Move to MVP only if all conditions are true:

```text
1. Sponsor confirms business objective.
2. Business owner is assigned.
3. First use case is selected.
4. Pilot scope is bounded.
5. Input documents are available.
6. Output templates are available.
7. Current process baseline is captured.
8. KPI baseline exists.
9. Target workflow is approved.
10. Human gates are approved and owners assigned.
11. Traceability requirement is defined.
12. Data boundary is approved.
13. Requirement taxonomy is complete.
14. MVP acceptance criteria are approved.
15. MVP scope is approved by business and technical leads.
```

Hard fail conditions:

```text
- No business owner
- No usable input artifact
- No output template
- No effort baseline
- No human gate owner
- No traceability rule
- No MVP acceptance criteria
```

---

## 10. Build handoff checklist

MVP team can start only when:

```text
1. Input package is available.
2. Output template is available.
3. Target workflow blueprint is approved.
4. Human gates are assigned.
5. Requirement taxonomy is complete.
6. Artifact requirements are defined.
7. Acceptance criteria are approved.
8. KPI baseline exists.
9. Data boundary is approved.
10. MVP backlog is ready.
```

Handoff package:

```text
- Requirement Pack
- Target Workflow Blueprint
- MVP Scope Definition
- Artifact Requirement Definition
- Human Gate Policy
- Evidence and Traceability Policy
- KPI Measurement Plan
- Requirement Traceability Matrix
```

---

## 11. Exit criteria

The phase is complete when the team can answer:

```text
- What business pain are we solving?
- Which KPI will improve?
- Which workflow will AI assist?
- Which decisions remain human-approved?
- Which source artifacts will be used?
- What outputs must be generated?
- What fields must those outputs contain?
- What exactly will the MVP build?
- What criteria determine MVP success?
```

---

## 12. Engagement manager notes

During this phase, the Engagement Manager should prevent these failure modes:

```text
1. The team starts discussing models/frameworks too early.
2. The sponsor expects full automation without governance.
3. MVP scope expands beyond what is needed to prove the first use case.
4. KPI baseline is skipped.
5. Output templates are not locked.
6. Human gate ownership remains ambiguous.
7. Requirement artifacts are too vague for build handoff.
```

Management rule:

```text
Requirement Phase is not complete when discovery is complete.
Requirement Phase is complete only when the MVP team has a build-ready requirement pack.
```