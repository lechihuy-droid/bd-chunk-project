# <Technology Name>

> ⚠️ Work In Progress / Research Template
>
> Use this template for technical research documents that support Enterprise Harness architecture decisions.

## Document Control

| Field | Value |
|---|---|
| Status | Research / PoC / Adopted / Deprecated |
| Priority | High / Medium / Low |
| Category | Code Memory / Agent Framework / Workflow / Knowledge / UIUX |
| Last Reviewed | YYYY-MM-DD |
| Confidence | Low / Medium / High |
| Decision | Adopt / Pilot / Watch / Reject |
| Owner | TBD |

## Source Verification

| Source Type | Status | Notes |
|---|---|---|
| Official README | Not checked / Checked |
| Official documentation | Not checked / Checked |
| Paper / benchmark | Not available / Checked |
| Source code | Not checked / Checked |
| Independent validation | Not checked / Checked |

## 1. Executive Summary

Summarize the technology in 5-10 lines. The reader should be able to understand whether this tool is relevant to the Harness without reading the full document.

## 2. Problem Statement

Explain the pain point this technology is trying to solve.

## 3. Architecture Overview

Describe the high-level architecture.

```text
Input
  -> Processing Layer
  -> Storage / Memory Layer
  -> API / MCP / UI Layer
  -> Agent / User
```

## 4. Core Capabilities

| Capability | Source-backed fact | Harness relevance | Evaluation |
|---|---|---|---|
| Capability name | What the official source claims | Why it matters | High / Medium / Low |

## 5. Performance and Benchmarks

Record only source-backed numbers. Clearly distinguish vendor benchmarks from independent benchmarks.

## 6. Enterprise Evaluation

| Criterion | Rating | Reason |
|---|---:|---|
| Scalability | TBD | |
| Maintainability | TBD | |
| Security / local processing | TBD | |
| Integration cost | TBD | |
| Learning cost | TBD | |
| Harness fit | TBD | |

## 7. Harness Integration

Explain where this tool sits in the target Harness architecture.

```text
Business Memory
  -> Architecture Memory
  -> Code Memory
  -> Runtime Memory
  -> Agent Workflow
```

## 8. Comparison

Compare against alternatives in the same category.

## 9. Risks and Limitations

List what the tool does not solve.

## 10. Decision Record

### Current Decision

Pilot / Adopt / Watch / Reject

### Why

Explain the decision.

### Blocking Issues

- TBD

### Revisit After

- TBD

## 11. References

Use original sources first. Add retrieval date when useful.

- Official repo/docs:
- Paper:
- Benchmarks:
- Community / secondary sources:

## 12. Self Review

| Criterion | Score | Notes |
|---|---:|---|
| Technical accuracy | /30 | |
| Completeness | /20 | |
| Harness relevance | /20 | |
| Decision support | /15 | |
| Reference quality | /10 | |
| Readability | /5 | |
| Total | /100 | |
