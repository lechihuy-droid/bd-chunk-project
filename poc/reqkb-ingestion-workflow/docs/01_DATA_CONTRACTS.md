# ReqKB data contracts — implementation methodology

## 1. Purpose

Data contracts define how information moves through the RD → ReqKB workflow without losing source traceability, introducing design assumptions or mixing responsibilities between pipeline stages.

The contract is not intended to prescribe database columns or implementation classes in detail. Its purpose is to establish stable boundaries that every implementation must respect.

The workflow is built around one principle:

> Source evidence, processing results and semantic interpretation are different concerns and must remain distinguishable.

## 2. Contract layers

Use four logical contract layers.

```text
Document identity and revision
        ↓
SourceUnit evidence
        ↓
Processing results
        ↓
Semantic annotations and review
```

Each layer answers a different question:

| Layer | Question answered |
|---|---|
| Document | Which logical RD document and which revision is being processed? |
| SourceUnit | What exact source fragment is the evidence unit? |
| Processing | Is the unit structurally valid and how was it produced? |
| Semantic | What business meaning was interpreted from the unit, and how reliable is that interpretation? |

Do not merge these layers into one opaque record even when a POC serializes them together for convenience.

## 3. Document identity and revision

### Methodology

Separate the identity of a logical document from a specific content revision.

```text
Document
└── DocumentRevision
    └── SourceUnit
```

The logical document remains stable across updates. A revision represents a concrete content state at a point in time.

### Required concepts

A document contract must provide:

- workspace or project scope;
- deterministic document identity;
- business key or logical name;
- revision identity;
- source location;
- exact content hash;
- version label when available;
- lifecycle status;
- ingestion run reference.

### Implementation requirements

1. IDs must not be generated from LLM output.
2. The exact source bytes must have an audit hash.
3. A changed revision must not overwrite the historical revision record.
4. Removed or superseded revisions must remain traceable.
5. Every SourceUnit must reference the exact revision from which it was produced.

### Why this matters

Without revision separation, the system cannot reliably answer:

- whether two units came from the same document version;
- which annotations became stale after an update;
- what source was used for a prior result;
- whether a deleted requirement is still active.

## 4. SourceUnit as the canonical evidence unit

### Methodology

A `SourceUnit` is the smallest useful fragment of source text accepted by the ingestion workflow.

It is not a rewritten claim and not an LLM summary.

```text
SourceUnit = immutable raw evidence + deterministic source location
```

### Required concepts

A SourceUnit contract must include:

- deterministic `source_unit_id`;
- exact raw text;
- document revision reference;
- structural path such as heading hierarchy;
- source boundaries such as line range;
- block type;
- local ordering and structural relationships;
- content fingerprint;
- parser and builder versions;
- lifecycle state.

### Identity methodology

Identity should be deterministic from stable source properties:

```text
workspace
+ document revision
+ structural path
+ source boundary
+ content fingerprint
```

Do not derive identity from extracted actor, action, ontology label or model-generated text.

### Invariants

1. Raw source text is never silently rewritten.
2. Every SourceUnit resolves to an exact source location.
3. The same source and ruleset produce the same identity.
4. A SourceUnit belongs to exactly one document revision.
5. Split and merge operations preserve lineage to original units.

## 5. Deterministic metadata

### Methodology

Parser metadata records facts that can be reproduced without semantic interpretation.

Typical metadata includes:

- document and revision reference;
- source path;
- heading path;
- block type;
- line boundaries;
- previous, next and parent structural links;
- parser, builder and ingestion versions;
- hashes and run identifiers.

### Boundary rule

Parser metadata must answer:

```text
Where did this unit come from?
How was it structurally produced?
```

It must not answer:

```text
What does this requirement mean?
```

Actor, action, condition, requirement type and modality belong to semantic annotation, not parser metadata.

## 6. Validation contract

### Methodology

Validation determines whether a SourceUnit is suitable for semantic processing. It does not decide whether the business meaning is correct.

The contract must support these outcomes:

- `PASS` — suitable for ontology tagging;
- `SPLIT` — likely contains several independent assertions;
- `MERGE` — lacks enough local context;
- `REVIEW` — boundary or structure remains ambiguous;
- `REJECT` — empty, corrupt, unsupported or untraceable input.

### Required validation information

A validation result should record:

- SourceUnit reference;
- final status;
- triggered rule identifiers;
- severity and blocking nature;
- rule or ruleset version;
- validator component version;
- validation run reference;
- evidence location within the SourceUnit;
- proposed next action where relevant.

### Invariants

1. Every SourceUnit has one current validation outcome.
2. Only eligible outcomes continue automatically to ontology tagging.
3. Validation remains reproducible for a fixed source and ruleset.
4. Repairs do not overwrite the original SourceUnit.
5. Human adjudication is auditable.

## 7. Repair and lineage

### Methodology

Split, merge and replacement are explicit lineage operations, not silent text edits.

Use typed lineage relations such as:

```text
SPLIT_FROM
MERGED_FROM
REPLACES
STRUCTURAL_PARENT
PREVIOUS
NEXT
```

### Requirements

- A split result references its source unit.
- A merge result references every contributing unit.
- The resulting text remains reconstructable from original source ranges.
- Old units receive a lifecycle state rather than being deleted without trace.
- Reprocessing must preserve the history of how the current unit was obtained.

## 8. Terminology annotation

### Methodology

Canonicalization adds controlled terminology without changing raw source text.

Each terminology annotation should distinguish:

- surface form found in the source;
- canonical term or entity identifier;
- canonical label;
- source character span;
- resolution method;
- confidence;
- review state;
- terminology dictionary version.

### Offset convention

The implementation must define one offset convention and use it everywhere. A recommended convention is:

```text
zero-based Unicode character indexes
start is inclusive
end is exclusive
indexes refer to SourceUnit.raw_text
```

The system must be able to verify that the recorded span reproduces the source phrase.

### Invariants

1. Canonical labels never replace source wording.
2. Ambiguous aliases are not silently merged.
3. Resolution method and dictionary version are recorded.
4. Every accepted mapping is traceable to a source span.

## 9. Requirement ontology annotation

### Methodology

Ontology annotation is a controlled interpretation attached to a SourceUnit.

The ontology schema defines allowed semantic slots. The tagger fills those slots using deterministic rules, LLM structured output or human review.

The lightweight ontology is limited to requirement and business semantics, such as:

- requirement type;
- modality;
- actors;
- actions;
- business objects;
- events;
- conditions;
- exceptions;
- terminology references.

Design concepts such as API, Screen, DatabaseTable, Batch, TestCase and DesignDecision remain outside this contract.

### Field-level evidence

Do not rely only on one confidence score for the entire annotation.

Each semantic value should carry:

- canonical value or identifier;
- human-readable label;
- exact supporting source span;
- extraction method;
- epistemic status such as explicit or inferred;
- confidence;
- review state.

This enables the system to distinguish:

```text
The source explicitly says this
```

from:

```text
The model inferred this from context
```

### Invariants

1. Every accepted semantic value has evidence.
2. Unsupported values are rejected or routed to review.
3. Ontology version and tagger version are recorded.
4. Model and prompt versions are recorded when an LLM is used.
5. Design artifacts are not introduced at this stage.

## 10. Evidence validation

### Methodology

Evidence validation checks whether semantic annotations are supported by the SourceUnit and allowed context.

It must operate at field level, not only at whole-record level.

A result should identify:

- supported fields;
- unsupported fields;
- contradictory fields;
- missing evidence spans;
- invalid ontology values;
- review requirements;
- validator and ruleset versions.

### Acceptance rule

An annotation is eligible for automatic acceptance only when:

- its schema is valid;
- all required semantic values are supported;
- no blocking contradiction is found;
- confidence and policy thresholds are satisfied.

## 11. Review contract

### Methodology

Human review is a first-class workflow object, not a free-text note.

A review record should identify:

- reviewed SourceUnit or annotation;
- queue type and reason codes;
- priority;
- current state;
- proposed value;
- original machine output;
- human correction or decision;
- assignment and reviewer identity;
- timestamps and resolution reason.

Recommended lifecycle:

```text
OPEN → ASSIGNED → RESOLVED
                 ↘ DISMISSED
                 ↘ CANCELLED
```

### Invariants

1. Human corrections do not overwrite machine output.
2. Original and corrected values remain available for audit and evaluation.
3. Review state changes are traceable.
4. Resolved reviews feed quality measurement and future rule improvement.

## 12. Ingestion run contract

### Methodology

Every pipeline execution must be represented as an ingestion run.

The run record should capture:

- workspace;
- pipeline version;
- component versions;
- ontology and ruleset versions;
- model and prompt versions when applicable;
- start and completion times;
- run status;
- input and output counts;
- warning and error counts;
- parent or retry run where relevant.

### Why this matters

Without a run contract, component IDs and version fields cannot be resolved into an auditable processing history.

## 13. Processing error contract

### Methodology

Errors should be structured workflow records rather than appended notes.

An error record should identify:

- ingestion run;
- processing stage;
- document revision or SourceUnit;
- stable error code;
- human-readable message;
- retryability;
- technical details;
- occurrence time;
- resolution status.

This allows the pipeline to continue processing other documents while preserving a controlled recovery path.

## 14. Lifecycle and incremental update

### Methodology

Use explicit lifecycle states rather than a single `active` boolean.

Typical states include:

```text
ACTIVE
SUPERSEDED
REMOVED
INVALIDATED
```

When a document revision changes:

1. register the new revision;
2. parse and build new SourceUnits;
3. compare old and new units;
4. preserve unchanged identities where possible;
5. invalidate or supersede removed units;
6. invalidate dependent validation and ontology results;
7. reprocess only affected units;
8. retain historical lineage.

Do not append new records while leaving stale semantic annotations active.

## 15. Contract versioning

### Methodology

Every contract family must be versioned independently:

- document contract;
- SourceUnit contract;
- validation contract;
- terminology contract;
- ontology annotation contract;
- review contract;
- ingestion run contract.

### Compatibility policy

- Additive optional fields may remain backward compatible.
- Renamed fields, changed semantics or enum changes require a new contract version.
- Consumers must reject unsupported major versions.
- Migration or reprocessing strategy must be documented before contract changes are adopted.

## 16. Minimal contract set for implementation

The initial implementation should support these logical records:

```text
Document
DocumentRevision
IngestionRun
SourceUnit
SourceUnitLineage
ValidationResult
TerminologyAnnotation
RequirementOntologyAnnotation
EvidenceSpan
EvidenceValidationResult
ReviewRecord
ProcessingError
```

A POC may serialize some records together, but the logical boundaries must remain explicit.

## 17. Implementation sequence

Recommended order:

```text
1. Document and revision identity
2. SourceUnit and deterministic provenance
3. Validation result and repair lineage
4. Ingestion run and processing error
5. Terminology annotation
6. Lightweight ontology annotation with field-level evidence
7. Evidence validation
8. Review workflow
9. Lifecycle and incremental update
10. Contract versioning and migration policy
```

Do not begin with database optimization or graph schema. First ensure that the evidence, identity, lineage and semantic boundaries are stable.

## 18. Definition of done

The data-contract design is ready for implementation when:

1. every SourceUnit resolves to one exact document revision;
2. raw evidence is immutable and reproducible;
3. deterministic metadata is separated from semantic interpretation;
4. validation, repair and review have explicit lifecycle states;
5. every semantic value can point to supporting evidence;
6. all processing results record component and schema versions;
7. incremental updates can invalidate stale results without deleting history;
8. tenant/workspace boundaries are explicit;
9. unsupported contract versions fail safely;
10. no design artifact is inferred or stored by this workflow.
