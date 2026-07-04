# 04 — CEO / Sponsor Interview Assumptions

## 1. Purpose

This document defines the assumptions to use when simulating or preparing CEO / sponsor interviews for the Super AI Transformation Platform initiative.

The user is not the CEO. The user is a middle manager in FPT Japan who wants to build a department-level AI-assisted delivery solution for a unit of approximately 80-100 people.

Therefore, the interview should be adapted from a CEO-only conversation to a **sponsor / department leadership alignment** conversation.

---

## 2. Confirmed context for interview simulation

```text
Company: FPT Japan / FPT Software Japan context
User role: Middle manager
Department scope: 80-100 people
Initiative: Build AI-assisted delivery solution for the department
First focus: RD -> RCD -> Basic Design transformation
```

---

## 3. Primary interview audience

The likely stakeholders are:

```text
1. Department Head / Business Sponsor
2. Delivery Manager
3. PMO Lead
4. Solution Architect
5. BA Lead
6. QA / Review Lead
7. Security or Compliance representative
8. Platform / Engineering Lead
```

If CEO-level framing is used, it should be adapted as:

```text
CEO-level question:
Which business metric should AI improve for the company?

Department-level version:
Which delivery metric should this AI solution improve for our 80-100 person department?
```

---

## 4. Interview framing

Open the conversation with:

```text
This is not a generic AI tool proposal. This is a department-level delivery transformation initiative. The goal is to use AI to reduce manual effort, improve traceability, and make Basic Design work more reviewable while keeping human approval in the process.
```

---

## 5. First interview sequence

### Question 1 — Department ambition

```text
If this AI-assisted delivery solution succeeds after 6-12 months, what should change for the department?
```

Potential answer categories:

```text
- Less manual effort
- Faster BD delivery
- Better quality and fewer review comments
- Less dependency on senior people
- Better traceability
- Better client-facing delivery confidence
- More reusable delivery assets
```

### Question 2 — Business pain

```text
Where does the department currently spend the most effort in upstream delivery?
```

Probe:

```text
- RD reading
- QA clarification
- RCD creation
- BD mapping
- Screen/API/DB design drafting
- Review preparation
- Excel formatting
```

### Question 3 — First use case

```text
Which bounded use case should we choose first so that we can prove value within 90 days?
```

Recommended first use case:

```text
RD / QA / Meeting Notes -> RCD -> BD Mapping -> BD Draft -> Validation
```

### Question 4 — Governance

```text
Which outputs can AI draft, and which outputs must remain human-approved?
```

Expected governance stance:

```text
AI can draft and validate.
BA approves RCD.
Architect approves BD output.
Client-facing output requires human review.
```

### Question 5 — Success metrics

```text
What evidence would make leadership believe this should scale beyond one pilot?
```

Suggested metrics:

```text
- 20-30% RCD / BD draft effort reduction
- 80-90% traceability coverage
- Reduction in review preparation time
- Reviewer acceptance
- Reusable workflow and skill assets
```

---

## 6. Reframed CEO interview model for middle-manager-led initiative

Because the user is a middle manager, the interview should focus on internal sponsorship and departmental adoption.

```text
CEO-style question:
What company metric should change?

Department-level question:
What delivery metric should change for our unit?
```

```text
CEO-style question:
What strategic ambition should AI serve?

Department-level question:
What practical delivery pain should AI solve first?
```

```text
CEO-style question:
What investment decision is needed?

Department-level question:
What pilot scope and leadership support do we need to prove value?
```

---

## 7. Working assumption for future plans

Use the following assumption unless updated:

```text
The initiative is led by a middle manager in FPT Japan for an 80-100 person department. The goal is to prove a department-level AI-assisted delivery capability, starting with Basic Design transformation, and then use pilot evidence to win leadership support for broader platformization.
```

---

## 8. Recommended sponsor ask

The user should ask leadership for:

```text
1. Permission to run a bounded pilot.
2. Access to sample RD / QA / BD artifacts.
3. BA and Architect review time.
4. Agreement on success metrics.
5. Approval to create reusable workflow / skill assets.
6. Clear rule on data usage and human review.
```

---

## 9. Recommended first sponsor pitch

```text
I would like to run a bounded AI-assisted Basic Design pilot for our department. The goal is not to replace BA or Architect work, but to reduce manual effort in RD/RCD/BD preparation, improve traceability, and create a reusable delivery workflow. We will keep human approval gates, measure effort reduction and output quality, and decide after the pilot whether this should scale.
```