# 05 — KPI, Risk, Issue, and Decision Tracker

## 1. Purpose

This document provides templates for measuring value, managing risk, tracking issues, and recording decisions during the Requirement Phase and MVP Phase.

The goal is to ensure that the program proves business value, not just technical feasibility.

---

## 2. KPI framework

### Productivity KPI

| KPI | Definition | Baseline source | Target | Owner |
|---|---|---|---|---|
| Time to create RCD | Manual effort required to create RCD from input documents | Effort baseline interview / timesheet | 20-30% reduction | PMO / BA Lead |
| Time to create BD draft | Manual effort required to create initial BD artifact | Effort baseline | 20-30% reduction | PMO / Architect |
| Review preparation time | Time required to prepare review package | PMO / reviewer input | 20% reduction | PMO |
| Manual copy/paste reduction | Reduction in manual transfer between docs/templates | Observation / BA estimate | Qualitative + quantified if possible | BA Lead |

### Quality KPI

| KPI | Definition | Target | Owner |
|---|---|---|---|
| Traceability coverage | % of generated items with source reference | 80-90% in MVP | QA Lead |
| Missing source reference count | Number of generated items without evidence | Trending down | QA Lead |
| Inconsistency count | Contradictions across RCD, mapping, BD output | 0 critical | Architect |
| Review comment count | Number of reviewer comments on AI-assisted output | 20% reduction target after pilot | PMO / Reviewer |
| Unsupported claim count | AI statements not grounded in source | 0 critical | QA Lead |

### Governance KPI

| KPI | Definition | Target | Owner |
|---|---|---|---|
| Human gate completion | Required approvals captured before next step | 100% | Product Owner |
| Audit completeness | Workflow run, model/skill use, outputs, approvals logged | 100% MVP run | Platform Lead |
| Policy violation count | Violations of evidence, data, or approval policy | 0 critical | Governance Lead |
| Pending decision count | Number of ambiguous items flagged for human decision | Tracked and reviewed | BA Lead |

### Adoption KPI

| KPI | Definition | Target | Owner |
|---|---|---|---|
| BA acceptance | BA considers RCD output reviewable | Positive qualitative result | BA Lead |
| Architect acceptance | Architect considers BD output reviewable | Positive qualitative result | Architect |
| Skill reuse count | Number of skills reusable after MVP | 5-10 | Skill Engineer |
| Workflow reuse potential | Whether workflow can be reused for next BD project | Yes / No | Product Owner |

---

## 3. KPI tracker template

| Date | Phase | KPI | Baseline | Current | Target | Status | Comment | Owner |
|---|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | Requirement / MVP |  |  |  |  | Green / Amber / Red |  |  |

Status rule:

```text
Green: on track or target met
Amber: risk of missing target
Red: target unlikely or blocked
```

---

## 4. Risk register template

| Risk ID | Risk | Description | Probability | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|
| R-001 | Tool-first trap | Team starts building app before business value is clear | Medium | High | Enforce charter, stage gates, and KPI linkage | Engagement Manager | Open |
| R-002 | Weak adoption | BA/Architect do not trust AI output | Medium | High | Co-design review output, evidence view, human gates | Product Owner | Open |
| R-003 | Hallucination risk | AI creates unsupported design statements | Medium | High | Source refs, validation, unsupported claim log | QA Lead | Open |
| R-004 | Poor data quality | Input docs are incomplete or inconsistent | High | Medium | Data readiness assessment, gap detection | Knowledge Lead | Open |
| R-005 | Scope creep | MVP expands into full platform build | Medium | High | Strict MVP scope and gate discipline | Engagement Manager | Open |
| R-006 | Security blocker | Client data cannot be used as planned | Medium | High | Data boundary review, masking, access control | Security Lead | Open |
| R-007 | KPI not measurable | Baseline missing or weak | Medium | High | Capture baseline in Requirement Phase | PMO | Open |
| R-008 | Human gate unclear | Approval owner or criteria unclear | Medium | Medium | Define RACI and gate policy | Business Owner | Open |

---

## 5. Issue tracker template

| Issue ID | Date | Issue | Impact | Owner | Due date | Status | Resolution |
|---|---|---|---|---|---|---|---|
| I-001 | YYYY-MM-DD |  | High / Medium / Low |  |  | Open / In progress / Closed |  |

Issue severity:

```text
High: blocks stage gate or MVP execution
Medium: affects timeline, quality, or reviewability
Low: manageable within workstream
```

---

## 6. Decision log template

| Decision ID | Date | Decision | Options considered | Rationale | Owner | Impact | Status |
|---|---|---|---|---|---|---|---|
| D-001 | YYYY-MM-DD |  |  |  |  |  | Open / Closed |

Decision examples:

```text
- Approved first pilot use case
- Approved MVP scope
- Approved human gate policy
- Approved source reference standard
- Approved output template
- Approved go / revise / stop gate decision
```

---

## 7. Gate scorecard template

| Gate | Question | Evidence status | KPI status | Risk status | Decision |
|---|---|---|---|---|---|
| R0 | Sponsor aligned? | Complete / Partial / Missing | Green / Amber / Red | Green / Amber / Red | Go / Revise / Stop |
| R1 | Diagnostic complete? |  |  |  |  |
| R2 | Target workflow and MVP scope approved? |  |  |  |  |
| M1 | MVP design approved? |  |  |  |  |
| M2 | MVP build ready for review? |  |  |  |  |
| M3 | MVP output reviewable and traceable? |  |  |  |  |
| M4 | Pilot ready / scale decision? |  |  |  |  |

---

## 8. Weekly status template

```text
Week:
Overall status: Green / Amber / Red

1. Progress this week
- 

2. Key outputs completed
- 

3. KPI movement
- 

4. Risks and issues
- 

5. Decisions needed
- 

6. Next week priorities
- 
```

---

## 9. Management rule

A KPI is valid only if it has:

```text
1. Baseline
2. Target
3. Owner
4. Measurement method
5. Review cadence
6. Decision implication
```

If a KPI does not inform a decision, it should not be used for the steering committee.