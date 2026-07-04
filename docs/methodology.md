# Methodology

The BD Harness methodology is process-first, human-gated, and measurement-driven.

## End-to-end flow

```text
Requirement sources
  -> RCD extraction
  -> Traceable chunking
  -> Ontology labeling
  -> RKB review
  -> BD frame mapping
  -> Japanese BD patch
  -> Human review
```

## RCD

RCD means Requirement Control Data in this project. It is the normalized, traceable control layer between raw requirement documents and Basic Design output.

## Operating rules

- Keep every requirement item traceable to its source.
- Separate fact, clarification, addition, pending decision, legacy reference, and technical inference.
- Do not promote pending or conflicting items into approved BD content.
- Prefer deterministic parsing and rule-based mapping before LLM assistance.
- Use LLMs to summarize, classify, and draft only after provenance is locked.

## MVP success definition

A user can provide an Excel QA/RD range and receive a reviewable Japanese BD patch where every generated statement points back to source metadata.
