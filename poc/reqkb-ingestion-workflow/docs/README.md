# ReqKB ingestion implementation documentation

This folder is the implementation specification for the RD Markdown → Requirement Knowledge Base workflow.

## Reading order

1. [`00_IMPLEMENTATION_GUIDE.md`](00_IMPLEMENTATION_GUIDE.md) — architecture boundary, components, package layout and milestones.
2. [`01_DATA_CONTRACTS.md`](01_DATA_CONTRACTS.md) — Pydantic-oriented contracts for documents, SourceUnits, validation, ontology, evidence and review.
3. [`02_PARSER_AND_SOURCE_UNIT_BUILDER.md`](02_PARSER_AND_SOURCE_UNIT_BUILDER.md) — deterministic Markdown parsing, exact source extraction and stable SourceUnit construction.
4. [`03_VALIDATOR_AND_REPAIR.md`](03_VALIDATOR_AND_REPAIR.md) — validation rules, PASS/SPLIT/MERGE/REVIEW/REJECT semantics and repair lineage.
5. [`04_ONTOLOGY_AND_TAGGER.md`](04_ONTOLOGY_AND_TAGGER.md) — lightweight requirement ontology, terminology resolution, LLM structured output and evidence policy.
6. [`05_PERSISTENCE_AND_INCREMENTAL_INGESTION.md`](05_PERSISTENCE_AND_INCREMENTAL_INGESTION.md) — PostgreSQL model, transaction boundaries and add/change/remove processing.
7. [`06_TEST_AND_QUALITY_PLAN.md`](06_TEST_AND_QUALITY_PLAN.md) — unit/integration/golden tests, metrics and quality gates.
8. [`07_OPERATIONS_RUNBOOK.md`](07_OPERATIONS_RUNBOOK.md) — CLI, run state, retries, review operations, monitoring, security and go-live checklist.

## Implementation boundary

Included:

```text
RD source registration
Markdown parsing
SourceUnit construction
metadata
validation and repair
terminology canonicalization
light requirement ontology annotation
evidence validation
ReqKB persistence
incremental ingestion
```

Excluded:

```text
design rules
BD generation
API/Screen/DB inference
design ontology
GraphRAG
impact analysis
```

## Recommended first implementation slice

```text
DocumentRegistry
→ MarkdownParser
→ SourceUnitBuilder
→ SourceUnitValidator
→ JSONL output
```

Complete this deterministic slice and its tests before introducing LLM ontology tagging or database persistence.