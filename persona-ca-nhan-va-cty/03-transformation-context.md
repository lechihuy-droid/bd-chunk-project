# 03 — Transformation Context

## 1. Initiative name

Working name:

```text
Super AI Transformation Platform for FPT Japan Department-level Delivery
```

Beachhead solution:

```text
BD Harness / AI-assisted Basic Design Delivery Harness
```

---

## 2. Core problem statement

The department performs software delivery work in a Japan enterprise context where upstream phases such as requirement interpretation, RCD creation, Basic Design drafting, and review preparation consume significant manual effort.

The current process likely depends heavily on:

```text
- Manual reading of RD / QA / meeting notes
- Senior interpretation and review
- Excel-based documentation
- Project-specific knowledge
- Manual traceability management
```

The transformation opportunity is to convert this work into a governed AI-assisted workflow.

---

## 3. Target business capability

```text
Create a department-level AI-assisted delivery capability that can convert project input documents into reviewable, traceable, human-approved delivery artifacts.
```

Capability formula:

```text
AI-assisted Delivery Capability
=
Business Workflow
+ AI Harness Runtime
+ Skill Library
+ Human Gates
+ Validation
+ Traceability
+ KPI Measurement
```

---

## 4. Initial use case

```text
RD / QA / Meeting Notes
  -> Requirement fact extraction
  -> RCD candidate generation
  -> BA approval
  -> BD mapping
  -> BD draft generation
  -> Validation
  -> Architect review
  -> Excel delivery pack
```

The first use case should be bounded to a specific pilot scope, not the full department or all project types.

---

## 5. Why BD Harness is a strong first use case

```text
1. High manual effort
2. High repeatability
3. Structured output
4. Clear review model
5. Strong governance need
6. Strong traceability requirement
7. Direct impact on delivery quality and cycle time
8. Reusable across future projects
```

---

## 6. Target platform architecture direction

The target architecture is a Declarative Super Agent Harness.

```text
Experience Layer
  -> Workflow / Skill / Review UI eventually

Declarative Configuration Layer
  -> workflow.yaml
  -> agent.yaml
  -> SKILL.md
  -> policies
  -> evals

Harness Runtime
  -> Orchestrator
  -> Agent Runner
  -> Skill Loader
  -> Tool Executor
  -> State Manager

Knowledge and Traceability Layer
  -> Source chunks
  -> Requirement facts
  -> RCD
  -> BD mapping
  -> Traceability graph

Governance and Delivery Layer
  -> Human gates
  -> Validation reports
  -> Audit log
  -> Excel export
```

MVP architecture should start file-based before UI-based.

---

## 7. Operating principles

```text
1. Business-first, not technology-first.
2. AI drafts, humans approve.
3. Traceability before automation.
4. File-based MVP before full UI.
5. Reusable skill packages before one-off prompts.
6. KPI baseline before claiming value.
7. Human gate before client-facing output.
8. Start with one department-level use case, then scale.
```

---

## 8. Expected MVP outputs

```text
1. parsed_requirements.json
2. rcd_candidate.json
3. rcd_approved.json
4. bd_mapping.jsonl
5. bd_draft.json or bd_draft.xlsx
6. coverage_report.json
7. consistency_report.json
8. traceability_report.json
9. final_delivery_pack.xlsx
10. pilot_kpi_report.md
```

---

## 9. Success metrics for first pilot

Suggested metrics:

```text
Productivity:
- RCD creation time reduction
- BD draft time reduction
- Review preparation time reduction

Quality:
- Traceability coverage
- Missing source reference count
- Inconsistency count
- Review comment count

Governance:
- Human gate completion
- Unsupported AI claim count
- Audit completeness

Adoption:
- BA acceptance
- Architect acceptance
- Reuse potential
```

---

## 10. Transformation path

```text
Step 1: CEO / sponsor alignment
Step 2: Requirement Phase
Step 3: File-based Harness MVP
Step 4: Real project pilot
Step 5: Department-level adoption
Step 6: Platformization
Step 7: Scale to other delivery workflows
```

---

## 11. What this initiative should avoid

```text
1. Building a generic chatbot.
2. Building UI before proving workflow value.
3. Allowing AI to produce unreviewed client-facing output.
4. Ignoring Excel and source-of-truth constraints.
5. Treating prompts as one-off assets instead of reusable skills.
6. Measuring demo quality instead of business KPI.
7. Expanding scope before one pilot proves value.
```

---

## 12. Recommended internal narrative

```text
We will start with one practical, measurable, department-level AI delivery use case: AI-assisted Basic Design. The goal is not to automate people away, but to reduce manual effort, improve traceability, and make delivery artifacts easier to review. If successful, the same Harness pattern can scale to test design, code review, migration analysis, proposal support, and project QA.
```