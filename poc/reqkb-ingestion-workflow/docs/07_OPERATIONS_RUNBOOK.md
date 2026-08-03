# Operations runbook

## CLI contract

Recommended commands:

```bash
reqkb ingest ./input --workspace WS-001
reqkb validate --run INGEST-...
reqkb review export --queue ontology-low-confidence
reqkb review import corrections.jsonl
reqkb reprocess --document RD-001 --from-stage ontology
reqkb status --run INGEST-...
reqkb metrics --run INGEST-...
```

Each command must return a non-zero exit code for operational failure and emit a machine-readable run summary.

## Ingestion run states

```text
CREATED
DISCOVERING
PARSING
VALIDATING
TAGGING
PERSISTING
COMPLETED
COMPLETED_WITH_REVIEW
FAILED
CANCELLED
```

A run may complete with review items. Review items are not pipeline crashes.

## Run manifest

```json
{
  "run_id": "INGEST-20260802-001",
  "workspace_id": "WS-001",
  "pipeline_version": "reqkb-ingestion@0.1.0",
  "input_root": "./input",
  "started_at": "...",
  "completed_at": "...",
  "component_versions": {
    "parser": "markdown-it-py@...",
    "builder": "source-unit-builder@0.1.0",
    "validator": "source-unit-validator@0.1.0",
    "ontology": "requirement-light@0.1.0",
    "prompt": "ontology-tagger@0.1.0"
  },
  "documents": {
    "added": 4,
    "changed": 1,
    "unchanged": 20,
    "removed": 0,
    "failed": 0
  },
  "source_units": {
    "pass": 180,
    "split": 3,
    "merge": 2,
    "review": 8,
    "reject": 1
  }
}
```

## Logging

Use structured JSON logs with:

```text
timestamp
level
run_id
workspace_id
document_id
source_unit_id
stage
component_version
event_code
message
exception_type
```

Never log secrets or unrestricted sensitive document text. Log SourceUnit IDs and short approved excerpts only when needed.

## Error handling

### Document-level errors

Examples:

- unreadable file;
- invalid UTF-8;
- malformed Markdown causing unrecoverable parse failure;
- duplicate document business key.

Action:

- mark document failed;
- continue other documents;
- leave previous active version intact;
- create review/incident record.

### Unit-level errors

Examples:

- validation ambiguity;
- ontology schema failure;
- unsupported annotation;
- terminology resolution conflict.

Action:

- route unit to review;
- continue the document where safe;
- do not activate failed annotation.

### Infrastructure errors

Examples:

- database unavailable;
- transaction failure;
- model endpoint unavailable.

Action:

- retry only idempotent operations with bounded exponential backoff;
- do not retry validation/schema errors;
- abort persistence transaction safely;
- preserve staging artifacts for diagnosis.

## Retry policy

Suggested defaults:

```text
filesystem transient read: 2 retries
database transient error: 3 retries
LLM timeout/rate limit: 3 retries
invalid structured output: 1 corrective retry
schema/evidence failure: no automatic retry
```

Every retry records attempt number and reason.

## Review queue operations

Queues:

```text
source-boundary-review
terminology-ambiguity
ontology-low-confidence
ontology-conflict
unsupported-annotation
parser-warning-review
```

Review UI or export must show:

- raw SourceUnit;
- heading path and source location;
- parser/validator rule hits;
- deterministic annotations;
- model proposal;
- evidence validation result;
- neighboring units when needed.

Reviewer actions:

```text
accept
correct
split
merge
reject
mark-not-requirement
add-alias-proposal
```

## Reprocessing

Support stage-selective reprocessing:

```text
registry
parse
build
validate
canonicalize
ontology
evidence_validate
persist_projection
```

Do not reparse source when only ontology prompt changes unless required. Do not overwrite prior outputs; create a new version and retire the old projection after acceptance.

## Backup and recovery

For POC:

- daily PostgreSQL backup;
- retain input file snapshots or immutable source references;
- retain run manifests and review exports;
- test restore before pilot acceptance.

Recovery objective: reconstruct active ReqKB from source files plus versioned configs and human review decisions.

## Monitoring

Track:

- run success/failure;
- document throughput and latency;
- parser warning rate;
- validation status distribution;
- LLM call count, latency and failure;
- review queue size and age;
- stale active record count;
- idempotency conflicts;
- source reconstruction failures.

Alert on:

- any source reconstruction failure;
- stale-record leakage;
- sudden forbidden design annotation increase;
- repeated database transaction failure;
- review queue age above agreed threshold.

## Security

- enforce workspace isolation in queries and storage keys;
- use least-privilege database and model credentials;
- do not send restricted documents to external LLMs without approval;
- support local/private model configuration when required;
- record model provider and data-handling mode in run metadata;
- encrypt data in transit and at rest according to project policy.

## Go-live checklist

1. Golden-set quality gates pass.
2. Incremental add/change/remove tests pass.
3. Backup and restore tested.
4. Review ownership and SLA assigned.
5. Ontology and terminology owners assigned.
6. Model data-handling approval complete.
7. Logs and metrics visible.
8. Rollback to previous active document version tested.
9. No design artifact inference exists in the ReqKB ingestion path.
10. Runbook owner accepts operational handover.