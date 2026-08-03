# ReqKB persistence and incremental ingestion

## Objective

Persist evidence, validation, terminology and ontology projections with full lineage. Support add, update, remove and reprocess operations without appending stale assertions.

## Recommended POC storage

Use PostgreSQL as the system of record.

```text
documents
source_units
source_unit_lineage
validation_results
term_mentions
ontology_annotations
evidence_validation_results
review_items
ingestion_runs
component_versions
```

Add PostgreSQL full-text indexes for raw source. Add `pgvector` only when semantic retrieval is implemented.

## Core tables

### documents

Key fields:

```text
document_id PK
workspace_id
source_path
file_name
content_hash
document_version
status
parser_name
parser_version
active_from
active_to
ingestion_run_id
```

Unique constraint:

```text
(workspace_id, document_id, content_hash)
```

### source_units

```text
source_unit_id PK
document_id FK
raw_text
content_hash
heading_path JSONB
block_type
line_start
line_end
ordinal
active
schema_version
parser_version
builder_version
ingestion_run_id
created_at
retired_at
```

Indexes:

- `document_id, active`;
- `content_hash`;
- GIN full-text index on `raw_text`;
- optional GIN on `heading_path`.

### source_unit_lineage

```text
parent_source_unit_id
child_source_unit_id
operation  # SPLIT | MERGE | REPROCESS | SUPERSEDE
reason
repair_version
ingestion_run_id
```

### validation_results

Keep append-only results. A view may expose the latest result per SourceUnit.

### ontology_annotations

Store structured JSONB for POC plus indexed top-level fields such as requirement type and modality. Preserve model, prompt, ontology and ruleset versions.

### review_items

Queue state:

```text
OPEN
IN_REVIEW
RESOLVED_ACCEPT
RESOLVED_CORRECT
RESOLVED_REJECT
```

## Transaction boundaries

Process one document in a transaction after parsing and validation complete in memory or staging storage.

Recommended pattern:

1. create ingestion run;
2. parse and validate document;
3. write new document version and units in one transaction;
4. retire stale units from the prior version;
5. write annotations and review items;
6. commit;
7. emit metrics/events after commit.

A failed document must not partially replace its active prior version.

## Incremental decision matrix

### New file

```text
no document record
→ register
→ parse all
→ validate/tag
→ persist active version
```

### Unchanged file

```text
same content hash + same required component versions
→ skip
→ record SKIPPED run result
```

### Changed file

```text
same document business key + different content hash
→ parse new version
→ compare SourceUnit IDs and content fingerprints
→ retain unchanged units where policy allows
→ add new/changed units
→ retire removed units
→ revalidate/re-tag affected units
```

### Removed file

```text
missing from authoritative source inventory
→ mark document removed
→ retire active SourceUnits and derived annotations
→ preserve audit history
```

### Component version change

If parser, builder, validator, ontology or prompt version changes, decide reprocessing scope explicitly.

```text
parser/builder change → reparse affected documents
validator change → revalidate units
ontology schema change → migrate and re-tag
prompt/model change → controlled re-tag benchmark, not automatic production overwrite
terminology change → re-resolve affected aliases
```

## Stale assertion handling

Every derived record references its SourceUnit and source content hash. When a SourceUnit retires:

- its annotations become inactive;
- review items are closed or marked stale;
- indexes exclude inactive records;
- historical records remain queryable for audit.

Never append a new edge or annotation without retiring the one derived from the old source version.

## Idempotency

Use an `ingestion_run_id` and operation keys.

```text
operation_key = workspace_id + document_id + content_hash + pipeline_version
```

Repeated execution of the same operation key must not create duplicate active records.

## Repository interface

```python
class ReqKBRepository(Protocol):
    def get_active_document(self, document_id: str): ...
    def start_run(self, request): ...
    def save_document_version(self, document, units, results): ...
    def retire_units(self, unit_ids, run_id): ...
    def enqueue_reviews(self, items): ...
    def complete_run(self, run_id, metrics): ...
```

Keep SQL details outside pipeline orchestration.

## Retention policy

For the POC:

- never hard-delete source history automatically;
- retain raw source version metadata and retired SourceUnits;
- redact or encrypt sensitive text according to project policy;
- define a later archival policy before production.

## Acceptance criteria

1. Document updates are atomic.
2. Unchanged ingestion is idempotent.
3. Removed SourceUnits do not appear in active retrieval.
4. Historical provenance remains available.
5. Every annotation is invalidated when its source becomes stale.
6. Component version changes have an explicit reprocessing policy.
7. A failed ingestion leaves the last active document version intact.
8. Metrics can identify added, unchanged, changed, removed and failed documents.