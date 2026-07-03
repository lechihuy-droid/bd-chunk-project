# 03 — WBS for Requirement Phase + MVP Phase

## 1. Purpose

This document provides the Work Breakdown Structure for running the Requirement Phase and File-based Harness MVP Phase.

The WBS is designed for program execution, not only technical delivery. Each work package must create either a consulting deliverable, an approved decision, or a working MVP asset.

---

## 2. Level 1 WBS

```text
1.0 Program Mobilization
2.0 Requirement Phase
3.0 MVP Design
4.0 MVP Build
5.0 MVP Validation
6.0 Gate Review and Pilot Readiness
7.0 Program Management
```

---

## 3. Level 2 WBS

### 1.0 Program Mobilization

```text
1.1 CEO alignment
1.2 Sponsor confirmation
1.3 Stakeholder map
1.4 Project operating rhythm
1.5 Document repository setup
```

Outputs:

```text
CEO Alignment Note
Transformation Charter
Stakeholder Map
Operating Rhythm
```

---

### 2.0 Requirement Phase

```text
2.1 Stakeholder interviews
2.2 Current process mapping
2.3 Artifact inventory
2.4 Pain point heatmap
2.5 Effort baseline
2.6 Review issue taxonomy
2.7 Data readiness assessment
2.8 Use case prioritization
2.9 Target workflow blueprint
2.10 Human gate policy
2.11 Evidence and traceability policy
2.12 MVP scope definition
```

Outputs:

```text
Current Process Map
Pain Point Heatmap
Effort Baseline
Review Issue Taxonomy
Data Readiness Assessment
Use Case Matrix
Target Workflow Blueprint
Human Gate Policy
MVP Scope Definition
```

Critical path:

```text
CEO alignment
  -> Stakeholder interviews
  -> Process map
  -> Effort baseline
  -> Use case selection
  -> Target workflow
  -> MVP scope lock
```

---

### 3.0 MVP Design

```text
3.1 File-based Harness architecture
3.2 Project workspace design
3.3 workflow.yaml schema
3.4 agent.yaml schema
3.5 SKILL.md package standard
3.6 Validation design
3.7 KPI capture design
3.8 MVP backlog creation
```

Outputs:

```text
MVP Architecture
Workspace Structure
Workflow Schema
Agent Schema
Skill Package Standard
Validation Design
KPI Measurement Design
MVP Backlog
```

---

### 4.0 MVP Build

```text
4.1 Runtime skeleton
4.2 Project workspace implementation
4.3 State manager
4.4 Logging
4.5 Input ingestion
4.6 RD Parser Agent
4.7 RCD Builder Agent
4.8 Human Gate 1
4.9 BD Mapping Agent
4.10 BD Draft Agent
4.11 Validation Runner
4.12 Human Gate 2
4.13 Excel Export Agent
4.14 KPI report generation
```

Outputs:

```text
Runnable Workflow Skeleton
parsed_requirements.json
rcd_candidate.json
BA Approval Record
bd_mapping.jsonl
bd_draft output
Validation Reports
Architect Review Record
final_delivery_pack.xlsx
pilot_kpi_report.md
```

Critical path:

```text
Runtime skeleton
  -> Input ingestion
  -> RCD generation
  -> Human Gate 1
  -> BD mapping
  -> BD draft
  -> Validation
  -> Human Gate 2
  -> Excel export
```

---

### 5.0 MVP Validation

```text
5.1 Dry run on sample input
5.2 BA review of RCD output
5.3 Architect review of BD output
5.4 Traceability review
5.5 Unsupported claim review
5.6 KPI capture
5.7 Critical issue remediation
```

Outputs:

```text
Dry Run Log
RCD Review Result
BD Review Result
Traceability Report
Unsupported Claim Log
KPI Report
Remediation Log
```

---

### 6.0 Gate Review and Pilot Readiness

```text
6.1 MVP gate evidence package
6.2 Steering committee review
6.3 Go / Revise / Stop decision
6.4 Pilot execution plan
6.5 Pilot risk review
```

Outputs:

```text
MVP Gate Pack
Gate Decision Record
Pilot Plan
Pilot Risk Register
```

---

### 7.0 Program Management

```text
7.1 Weekly steering summary
7.2 Workstream tracker
7.3 Risk and issue log
7.4 Decision log
7.5 Backlog management
7.6 KPI dashboard update
7.7 Stakeholder communication
```

Outputs:

```text
Weekly Status Report
RAID Log
Decision Log
MVP Backlog
KPI Dashboard
```

---

## 4. Ownership model

```text
Engagement Manager:
CEO alignment, steering, gate reviews, value case, delivery quality.

Business Owner:
Business value, use case selection, adoption, pilot approval.

Product Owner:
MVP backlog, scope control, feature prioritization.

Solution Architect:
Architecture, runtime design, integration guardrails.

BA Lead:
Requirement interpretation, RCD review, human gate 1.

Architect Reviewer:
BD quality, consistency review, human gate 2.

Skill Engineer:
SKILL.md packages, prompt rules, failure mode fixes.

Platform Engineer:
Runtime, tool executor, filesystem, export.

QA / Validation Lead:
Coverage, consistency, traceability checks.

PMO:
Timeline, RAID, KPI baseline, decision log.
```

---

## 5. Gate evidence checklist

### Requirement Gate evidence

```text
- Transformation Charter
- Current Process Map
- Pain Point Heatmap
- Effort Baseline
- Use Case Prioritization Matrix
- Target Workflow Blueprint
- Human Gate Policy
- MVP Scope Definition
```

### MVP Gate evidence

```text
- Demo run log
- Input package
- RCD candidate output
- BA approval record
- BD mapping output
- BD draft output
- Validation report
- Architect review record
- Excel export sample
- KPI capture sheet
```

---

## 6. Completion rule

A work package is complete only if it has:

```text
1. Named owner
2. Concrete output
3. Review owner
4. Exit criteria
5. Link to business KPI, governance requirement, or reusable platform asset
```