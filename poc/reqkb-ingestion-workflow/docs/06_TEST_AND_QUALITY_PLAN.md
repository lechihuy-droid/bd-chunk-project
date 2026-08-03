# Test and quality plan

## Test strategy

Use three layers:

```text
unit tests
→ integration tests
→ golden dataset evaluation
```

No LLM-dependent behavior is considered production-ready without a fixed evaluation set and slot-level metrics.

## Unit tests

### Registry

- deterministic document ID;
- SHA-256 stability;
- UTF-8 and newline normalization;
- changed/unchanged detection;
- duplicate path handling.

### Markdown parser

Fixtures must cover:

- nested headings;
- paragraphs;
- ordered/unordered/nested lists;
- tables;
- blockquotes;
- code fences;
- repeated identical text;
- malformed fences and tables;
- Vietnamese, English and Japanese text.

Assertions:

- exact line ranges;
- exact raw text reconstruction;
- correct heading path;
- deterministic block ordering;
- explicit warnings.

### SourceUnit builder

- stable IDs;
- paragraph units;
- dependent and independent list items;
- table row units with header context;
- no mid-sentence token splitting;
- parent/child lineage after repair.

### Validator

Create one fixture for every rule ID and boundary case.

- PASS for concise independent requirement;
- SPLIT for multiple independent obligations;
- MERGE for incomplete dependent fragment;
- REVIEW for ambiguity/TBD/conflict;
- REJECT for empty or untraceable source.

Test determinism with property-based tests.

### Ontology schema and tagger

- allowed enum values;
- forbidden design classes;
- unknown fallback;
- deterministic modality extraction;
- conflict between rules and model;
- low-confidence review routing;
- invalid JSON/schema retry and failure behavior.

### Persistence

- atomic document replacement;
- unchanged ingestion idempotency;
- retirement of stale units;
- append-only validation history;
- review queue lifecycle.

## Integration scenarios

### Scenario A — initial ingestion

Input: five Markdown RD files.

Expected:

- all documents registered;
- SourceUnits generated and traceable;
- validation and ontology outputs persisted;
- review items created for ambiguous units;
- metrics and run manifest complete.

### Scenario B — single requirement changed

Expected:

- unchanged documents skipped;
- changed document reparsed;
- old affected SourceUnit retired;
- new unit and annotations active;
- unrelated units unchanged.

### Scenario C — file removed

Expected:

- document marked removed;
- units and derived annotations inactive;
- history retained.

### Scenario D — ontology version upgrade

Expected:

- migration decision recorded;
- old annotation retained;
- new annotation version created;
- no silent overwrite.

### Scenario E — LLM unavailable

Expected:

- deterministic pipeline completes;
- unresolved semantic fields route to review;
- evidence ingestion is not lost.

## Golden dataset

Select 100–300 SourceUnits representing:

- simple functional requirements;
- rules and constraints;
- conditions and exceptions;
- definitions;
- NFRs;
- multilingual terminology;
- tables and lists;
- ambiguous and malformed cases;
- explicit design references that must not become design ontology.

Gold labels include:

- expected SourceUnit boundaries;
- validator status and rule hits;
- requirement type;
- modality;
- actors/actions/objects/events;
- conditions/exceptions;
- expected review decision.

Gold labels must be reviewed by at least one requirement-domain reviewer. Record disagreements.

## Metrics

### Parsing and units

```text
source reconstruction accuracy
boundary precision/recall
stable-ID reproducibility
untraceable-unit rate
```

### Validation

```text
status accuracy
false PASS rate
repair success rate
human escalation rate
```

False PASS is the highest-risk validator error.

### Ontology tagging

Report precision, recall and F1 per slot:

```text
requirement_type
modality
actor
action
business_object
event
condition
exception
```

Also report:

- forbidden-design-class rate;
- unsupported-annotation rate;
- exact/alias terminology resolution accuracy;
- review correction rate.

### Incremental ingestion

```text
unchanged skip accuracy
changed-unit detection recall
stale-record leakage rate
idempotency failure rate
```

## Initial quality gates

Suggested POC gates, to be calibrated:

- 100% source reconstruction for accepted units;
- 100% stable IDs on unchanged reruns;
- 0 active annotations without active SourceUnit provenance;
- 0 accepted forbidden design classes;
- ≥95% modality precision;
- ≥90% requirement-type precision;
- unsupported annotation rate <5% on reviewed golden set;
- stale-record leakage = 0 in update tests.

Do not use a single aggregate score to hide weak conditions or exceptions.

## CI checks

Run on each PR:

```text
ruff check
mypy
pytest --cov
schema/config validation
golden deterministic subset
migration smoke test
```

Run LLM evaluation separately or on controlled CI with pinned model configuration. Store evaluation artifacts and do not block ordinary deterministic development when external model service is unavailable.

## Exit criteria

The POC is ready for a pilot only when deterministic ingestion gates pass, ontology slot metrics meet agreed thresholds, all high-risk failures route to review, and incremental tests show no stale active records.