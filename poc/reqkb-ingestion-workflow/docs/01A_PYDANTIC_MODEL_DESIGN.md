# Pydantic model design for ReqKB ingestion

## 1. Purpose

This document translates the data-contract methodology in [`01_DATA_CONTRACTS.md`](01_DATA_CONTRACTS.md) into a Pydantic-oriented model design.

The goal is not to prescribe every field or produce final source code. The goal is to define how the implementation team should use Pydantic to enforce the architectural boundaries of the RD → ReqKB ingestion workflow.

Pydantic is used here as a contract-enforcement layer between pipeline stages:

```text
external input
→ structural parsing
→ SourceUnit construction
→ validation
→ terminology and ontology annotation
→ persistence
```

Each stage must receive and return explicit models. Free-form dictionaries should be limited to diagnostic payloads and external compatibility boundaries.

## 2. Methodology

### 2.1 Begin with lifecycle and ownership, not with Python classes

Before creating a model, answer:

1. What real-world object does this record represent?
2. Which stage creates it?
3. Which stage may update it?
4. Is it evidence, interpretation, process state or review state?
5. What is its stable identity?
6. How is it versioned or invalidated?
7. What other record must exist before this one is valid?

Pydantic models should reflect these answers. They should not be designed merely around convenient JSON shapes.

### 2.2 Model the pipeline boundaries explicitly

The minimum conceptual boundaries are:

```text
Document
→ DocumentRevision
→ SourceUnit
→ ValidationResult
→ TerminologyAnnotation
→ RequirementOntologyAnnotation
→ EvidenceValidationResult
→ ReviewDecision
```

Supporting process records include:

```text
IngestionRun
ProcessingError
SourceUnitLineage
```

Each boundary should have its own model because each has a different owner, lifecycle and trust level.

### 2.3 Keep evidence separate from interpretation

The implementation must distinguish:

- immutable source evidence;
- deterministic parser metadata;
- validator findings;
- semantic annotations;
- human corrections;
- execution metadata.

A SourceUnit model must not be expanded into a universal object that is repeatedly mutated by every stage. Instead, later stages create separate result records linked by stable IDs.

### 2.4 Prefer append-and-supersede over in-place mutation

For auditable records, a new parser, validator, ontology or prompt version should create a new result version rather than silently replacing the old result.

This is particularly important for:

- ontology annotations;
- validation results;
- human corrections;
- reprocessed document revisions;
- repaired SourceUnits.

## 3. Model families

Organize Pydantic models by responsibility rather than placing every model in one module.

Recommended families:

```text
identity.py
  WorkspaceId
  DocumentId
  DocumentRevisionId
  SourceUnitId
  RunId

source.py
  Document
  DocumentRevision
  SourceLocation
  SourceUnit
  SourceUnitLineage

validation.py
  ValidationResult
  RuleHit
  EvidenceValidationResult

terminology.py
  TermMention
  CanonicalTermReference
  TerminologyAnnotation

ontology.py
  EvidenceSpan
  SemanticValue
  RequirementOntologyAnnotation

review.py
  ReviewTask
  ReviewDecision

runtime.py
  IngestionRun
  ProcessingError
```

The exact filenames may change, but the responsibility boundaries should remain.

## 4. Base model strategy

### 4.1 Define a small project base model

Use a shared base model to standardize behavior such as:

- rejecting unknown fields at trusted internal boundaries;
- serializing enums consistently;
- validating assignment only where mutation is intentionally allowed;
- generating JSON Schema for documentation and API contracts;
- using timezone-aware datetimes.

Conceptually:

```python
class ReqKBModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=False,
        validate_default=True,
    )
```

The final configuration should be tested against persistence and API needs. Do not enable settings globally without understanding their impact.

### 4.2 Separate immutable and mutable bases

Evidence records should be immutable after creation. Runtime and review queue records may have controlled state changes.

Recommended distinction:

```text
FrozenReqKBModel
- source evidence
- document revision identity
- SourceUnit
- completed annotation result

MutableReqKBModel
- ingestion run status
- review assignment
- retry state
```

Immutability is a design safeguard, not merely a coding preference.

### 4.3 Avoid generic catch-all models

Do not use models such as:

```text
GenericRecord
GenericAnnotation
GenericEntity
```

unless they represent a real stable abstraction. Generic models usually hide lifecycle differences and weaken validation.

## 5. Identity design

### 5.1 Use explicit identifier types

IDs should not be anonymous strings throughout the codebase. Define constrained aliases or lightweight value objects for major identifiers.

Examples:

```text
WorkspaceId
DocumentId
DocumentRevisionId
SourceUnitId
AnnotationId
ValidationId
ReviewId
IngestionRunId
```

The purpose is to prevent accidental substitution of one ID type for another and to document model relationships.

### 5.2 IDs must be independent from LLM output

Stable identities are generated from deterministic source and business keys. LLM-produced labels, summaries, actors or actions must never participate in canonical identity generation.

### 5.3 Distinguish logical and physical identity

The model design must preserve:

```text
Document
= logical identity across versions

DocumentRevision
= exact ingested version/content

SourceUnit
= exact evidence unit within one revision
```

This distinction is required for incremental ingestion and stale-result invalidation.

## 6. Source and evidence models

### 6.1 Document

The Document model represents the stable logical document, for example one MRD maintained across multiple versions.

It should contain only stable identity and ownership information.

### 6.2 DocumentRevision

The DocumentRevision model represents one concrete ingested version of a Document.

It owns:

- exact source hash;
- source URI/path;
- version label when provided;
- ingestion status;
- discovered timestamp;
- content media type.

Parser version does not define document identity; it belongs to processing lineage.

### 6.3 SourceLocation

Source location should be a dedicated model rather than scattered fields.

For Markdown v0.1 it may contain:

- line start and end;
- heading path;
- block type;
- ordinal;
- optional character offsets.

This abstraction permits later support for PDF pages, Excel cells or Word paragraphs without redesigning every higher-level model.

### 6.4 SourceUnit

SourceUnit is the canonical evidence object.

Its design principles are:

1. raw text is verbatim;
2. source revision is explicit;
3. source location is reproducible;
4. identity is deterministic;
5. source evidence is not overwritten by annotations;
6. lifecycle state is explicit;
7. repair lineage is external or strongly typed.

The SourceUnit model should remain small. It should not embed all validation, ontology and review history.

## 7. Validation model design

### 7.1 Validation is a separate result

A ValidationResult records a validator's judgment about a SourceUnit at a particular time and ruleset version.

It should identify:

- input SourceUnit;
- validator component version;
- ruleset version;
- status;
- rule hits;
- execution/run identity;
- completion time.

### 7.2 Use controlled enums

Use enums for stable workflow values such as:

```text
PASS
SPLIT
MERGE
REVIEW
REJECT
```

The enum is part of the contract. Adding a new status is a schema change and must be reviewed.

### 7.3 RuleHit is evidence, not free-form logging

A RuleHit should provide enough information to support deterministic repair or review:

- rule identifier;
- severity;
- affected source location or span;
- reason;
- recommended action;
- blocking/non-blocking classification.

Technical stack traces belong in ProcessingError, not in RuleHit.

## 8. Terminology and ontology annotation models

### 8.1 Annotation results are versioned projections

Terminology and ontology annotations are interpretations of a SourceUnit. They must record:

- SourceUnit ID;
- annotation ID/version;
- ontology or dictionary version;
- extraction method;
- model and prompt version when applicable;
- review status;
- evidence spans.

### 8.2 Use field-level semantic values

Do not represent ontology output only as lists of strings.

Each semantic value should conceptually contain:

```text
canonical ID when resolved
human-readable label
surface form from source
one or more evidence spans
extraction method
epistemic status
confidence
```

This allows the system to validate and review individual actors, actions, objects, conditions and exceptions.

### 8.3 EvidenceSpan must have a single offset convention

The implementation must choose and document one convention. Recommended:

```text
zero-based Unicode code-point offsets
start inclusive
end exclusive
relative to SourceUnit.raw_text
```

The invariant is:

```python
raw_text[start:end] == quoted_text
```

### 8.4 Confidence is not a validity decision

Confidence is diagnostic metadata. It must not replace:

- schema validation;
- evidence support;
- ontology constraints;
- review policy.

A high-confidence unsupported annotation remains invalid.

## 9. Review and correction models

### 9.1 Preserve proposal and decision separately

The model must preserve:

```text
machine proposal
human decision
corrected value
reason
reviewer identity
timestamps
```

Human correction must not overwrite the original annotation record.

### 9.2 Model review as a state machine

Review tasks should use controlled states such as:

```text
OPEN
ASSIGNED
RESOLVED
DISMISSED
CANCELLED
```

Transitions should be enforced in service logic and tested. Pydantic validates record shape, while workflow code validates allowed state transitions.

## 10. Runtime and error models

### 10.1 IngestionRun is the root of processing lineage

Every parser, builder, validator and tagger result should resolve to an IngestionRun.

The run model records:

- pipeline version;
- component versions;
- configuration/ruleset versions;
- start/end status;
- input/output counts;
- error counts.

### 10.2 ProcessingError is an operational contract

Processing errors require a structured model containing:

- pipeline stage;
- affected document revision or SourceUnit;
- error code;
- retryability;
- safe message;
- technical details;
- run identity.

Errors should not be stored as arbitrary notes on domain records.

## 11. Validation layers

Pydantic validation should be designed in layers.

### Layer 1 — shape and primitive constraints

Examples:

- required fields;
- enum membership;
- non-empty strings;
- confidence between zero and one;
- timezone-aware datetime;
- start offset before end offset.

### Layer 2 — record invariants

Examples:

- SourceLocation end is not before start;
- EvidenceSpan matches quoted source text;
- resolved canonical term has a canonical ID;
- completed review has resolver and resolution timestamp.

Use field/model validators for invariants contained within one record.

### Layer 3 — cross-record constraints

Examples:

- SourceUnit references an existing DocumentRevision;
- ontology annotation references a PASS-approved SourceUnit;
- one current active result exists per selected component/ruleset version;
- superseded records point to a valid replacement.

These do not belong entirely inside Pydantic models. Enforce them in application services and persistence transactions.

### Layer 4 — business and workflow policy

Examples:

- low-confidence annotations require human review;
- unsupported fields block automatic acceptance;
- removed document revisions invalidate active projections.

Policy belongs in workflow services/configuration, not hidden inside model validators.

## 12. Serialization and interchange

### 12.1 Use one canonical JSON representation

Define one canonical serialization policy for:

- enum representation;
- datetime format;
- null handling;
- field aliases;
- schema version placement.

Use `model_dump(mode="json")` or equivalent through a shared serialization utility rather than ad hoc serialization across components.

### 12.2 JSONL is an interchange format

For the POC, Pydantic models may serialize into separate JSONL files. JSONL must not dictate the internal domain model.

When PostgreSQL is added, the same model contracts should continue to define service boundaries even if persistence tables are normalized differently.

### 12.3 Generate JSON Schema

Generate and version JSON Schema from public/interchange Pydantic models. Use it for:

- structured LLM output;
- test fixtures;
- API/event contracts;
- documentation;
- compatibility checks.

Do not expose every internal runtime model as a public schema automatically.

## 13. Schema versioning and compatibility

### 13.1 Version contracts explicitly

Each externally stored or exchanged record family should include a schema version.

Examples:

```text
document-revision@0.1.0
source-unit@0.1.0
requirement-annotation@0.1.0
```

### 13.2 Classify model changes

- **Patch:** clarification or non-breaking validation correction.
- **Minor:** backward-compatible optional field or enum extension where consumers tolerate it.
- **Major:** renamed/removed field, changed semantics, identity change or incompatible enum change.

Enum extensions are not automatically backward compatible; consumer behavior must be checked.

### 13.3 Keep migration outside model constructors

Do not hide significant data migration inside Pydantic validators. Use explicit migration functions:

```text
v0.1 record
→ migrate_0_1_to_0_2
→ validate as v0.2 model
```

This keeps migration auditable and testable.

## 14. Design rules for Pydantic usage

1. Use Pydantic for contracts, not for persistence orchestration.
2. Keep evidence models immutable.
3. Separate source, interpretation, review and runtime records.
4. Use enums for controlled vocabularies.
5. Use `default_factory` for mutable collections.
6. Reject unexpected fields at trusted internal boundaries.
7. Do not put network, database or LLM calls in validators.
8. Keep validators deterministic and side-effect free.
9. Do not use one global confidence value as proof of correctness.
10. Preserve model/prompt/ruleset versions on generated results.
11. Use explicit migrations for schema changes.
12. Generate JSON Schema only for intended public/interchange models.
13. Avoid untyped `dict` fields except for bounded diagnostics or extension points.
14. Never let LLM output construct canonical source identities.

## 15. Implementation sequence

### Phase 1 — foundational source contracts

Implement and test:

```text
identifier types
Document
DocumentRevision
SourceLocation
SourceUnit
IngestionRun
```

### Phase 2 — deterministic validation contracts

Implement:

```text
ValidationStatus
RuleHit
ValidationResult
SourceUnitLineage
ProcessingError
```

### Phase 3 — semantic annotation contracts

Implement:

```text
EvidenceSpan
SemanticValue
TermMention
TerminologyAnnotation
RequirementOntologyAnnotation
EvidenceValidationResult
```

### Phase 4 — review contracts

Implement:

```text
ReviewTask
ReviewDecision
review state-transition tests
```

### Phase 5 — compatibility and schema publication

Add:

```text
JSON Schema generation
schema snapshots
migration functions
compatibility tests
```

Do not implement all models before the deterministic parser slice is working. Add model families when their owning pipeline stage becomes executable.

## 16. Testing principles

Every model family should have:

- valid construction tests;
- invalid boundary tests;
- serialization round-trip tests;
- schema snapshot tests for public contracts;
- deterministic identity tests;
- invariant tests;
- migration tests when versions change.

For evidence spans and SourceUnits, include multilingual fixtures to ensure offset and Unicode behavior is correct.

## 17. Definition of done

The Pydantic design is ready for implementation when:

1. each model has one clear owner and lifecycle;
2. Document, DocumentRevision and SourceUnit identities are distinct;
3. evidence and interpretation are represented separately;
4. all controlled statuses and methods use reviewed enums;
5. SourceUnit and evidence models preserve immutable provenance;
6. annotation values support field-level evidence;
7. validation boundaries are divided into record, cross-record and policy layers;
8. schema versions and migration responsibilities are explicit;
9. public JSON Schemas can be generated reproducibly;
10. model validators contain no side effects or external calls.

## 18. Relationship to other documents

- [`01_DATA_CONTRACTS.md`](01_DATA_CONTRACTS.md) defines the methodology and conceptual contracts.
- This document defines how those contracts should be represented and governed using Pydantic.
- [`02_PARSER_AND_SOURCE_UNIT_BUILDER.md`](02_PARSER_AND_SOURCE_UNIT_BUILDER.md) owns SourceUnit production logic.
- [`03_VALIDATOR_AND_REPAIR.md`](03_VALIDATOR_AND_REPAIR.md) owns validation and repair policy.
- [`04_ONTOLOGY_AND_TAGGER.md`](04_ONTOLOGY_AND_TAGGER.md) owns ontology extraction behavior.
- [`05_PERSISTENCE_AND_INCREMENTAL_INGESTION.md`](05_PERSISTENCE_AND_INCREMENTAL_INGESTION.md) owns cross-record persistence constraints and lifecycle transactions.
