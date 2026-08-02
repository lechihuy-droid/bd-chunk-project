# ReqKB data contracts

## Principles

- `SourceUnit` is the canonical evidence unit.
- Raw source text is immutable.
- Parser metadata contains only deterministic facts.
- Validation and ontology are separate projections attached to a SourceUnit.
- All records carry schema and component versions.

## DocumentRecord

```python
from datetime import datetime
from pydantic import BaseModel, Field

class DocumentRecord(BaseModel):
    document_id: str
    workspace_id: str
    source_path: str
    file_name: str
    media_type: str = "text/markdown"
    content_hash: str
    document_version: str | None = None
    status: str = "active"
    parser_name: str
    parser_version: str
    ingestion_run_id: str
    discovered_at: datetime
```

Requirements:

- `document_id` must be deterministic from workspace and configured business key, not from LLM output.
- `content_hash` uses SHA-256 over normalized bytes.
- `status` supports `active`, `superseded`, `removed`, `invalid`.
- changing only parser version may trigger controlled reprocessing even when content is unchanged.

## SourceUnitMetadata

```python
class SourceUnitMetadata(BaseModel):
    document_id: str
    source_path: str
    heading_path: list[str] = []
    block_type: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    ordinal: int = Field(ge=0)
    previous_source_unit_id: str | None = None
    next_source_unit_id: str | None = None
    content_hash: str
    parser_name: str
    parser_version: str
    builder_version: str
    ingestion_run_id: str
```

Allowed `block_type` values for v0.1:

```text
paragraph
list_item
list_group
table
blockquote
code_block
heading_context
```

## SourceUnit

```python
class SourceUnit(BaseModel):
    schema_version: str = "source-unit@0.1.0"
    source_unit_id: str
    raw_text: str
    metadata: SourceUnitMetadata
    parent_source_unit_ids: list[str] = []
    active: bool = True
```

Stable identity formula:

```text
UUIDv5(
  namespace = workspace_id,
  name = document_id
       + canonical_heading_path
       + line_start
       + line_end
       + SHA256(raw_text)
)
```

The line range is included to distinguish repeated identical text. A content-only fingerprint may also be stored for duplicate detection.

## ValidationRecord

```python
from enum import StrEnum

class ValidationStatus(StrEnum):
    PASS = "PASS"
    SPLIT = "SPLIT"
    MERGE = "MERGE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"

class RuleHit(BaseModel):
    rule_id: str
    severity: str
    message: str
    evidence: dict = {}

class ValidationRecord(BaseModel):
    source_unit_id: str
    status: ValidationStatus
    rule_hits: list[RuleHit] = []
    notes: list[str] = []
    validator_version: str
    validated_at: datetime
```

Rules:

- `PASS` means structurally suitable, not semantically correct.
- `SPLIT` and `MERGE` require a repair action before ontology tagging.
- `REVIEW` may proceed only after configured human or adjudication policy.
- `REJECT` is for empty, corrupt or untraceable input.

## TerminologyAnnotation

```python
class TermMention(BaseModel):
    surface_form: str
    canonical_term_id: str | None = None
    canonical_label: str | None = None
    start_char: int | None = None
    end_char: int | None = None
    resolution_method: str
    confidence: float = Field(ge=0, le=1)
    review_status: str
```

Raw text is never replaced by canonical labels. Canonicalization creates an annotation.

## RequirementOntologyAnnotation

```python
class RequirementOntologyAnnotation(BaseModel):
    ontology_version: str
    requirement_type: str
    modality: str
    actors: list[str] = []
    actions: list[str] = []
    business_objects: list[str] = []
    events: list[str] = []
    conditions: list[str] = []
    exceptions: list[str] = []
    terms: list[TermMention] = []
    tagging_method: str
    model_name: str | None = None
    prompt_version: str | None = None
    confidence: float = Field(ge=0, le=1)
    review_status: str
```

Allowed requirement types:

```text
functional
business_rule
constraint
non_functional
assumption
definition
unknown
```

Allowed modalities:

```text
must
must_not
should
may
stated_fact
unknown
```

Forbidden classes in this phase:

```text
API
Screen
ScreenField
DatabaseTable
DatabaseColumn
Batch
TestCase
DesignDecision
```

## EvidenceValidationRecord

```python
class EvidenceValidationRecord(BaseModel):
    source_unit_id: str
    annotation_version: str
    status: str  # PASS | REVIEW | FAIL
    unsupported_fields: list[str] = []
    contradictory_fields: list[str] = []
    validator_version: str
    validated_at: datetime
```

A field is unsupported when its value cannot be tied to an exact phrase or defensible interpretation in the SourceUnit and configured heading context.

## ReviewRecord

```python
class ReviewRecord(BaseModel):
    review_id: str
    source_unit_id: str
    queue_type: str
    reason_codes: list[str]
    proposed_value: dict | None = None
    reviewer_decision: str | None = None
    corrected_value: dict | None = None
    reviewer: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None
```

Never overwrite model output with human correction. Preserve both for audit and evaluation.

## JSONL interchange

For filesystem POC output, emit separate files:

```text
output/documents.jsonl
output/source-units.jsonl
output/validation.jsonl
output/terminology.jsonl
output/ontology-annotations.jsonl
output/evidence-validation.jsonl
output/review-queue.jsonl
```

Do not use a single denormalized JSONL as the long-term system of record; it is acceptable only as a portable POC interchange format.