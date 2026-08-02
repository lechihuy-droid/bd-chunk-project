# SourceUnit validator and repair specification

## Objective

Determine whether a candidate SourceUnit is structurally suitable for ontology tagging and ReqKB persistence. Validation is rule-based by default. It does not judge whether the business requirement is correct.

## Status model

```text
PASS    structurally suitable
SPLIT   contains multiple independent units or exceeds safe structural limits
MERGE   incomplete fragment requiring adjacent context
REVIEW  cannot be decided safely by deterministic rules
REJECT  empty, corrupt, untraceable or unsupported input
```

Only `PASS` units enter ontology tagging automatically.

## Rule configuration

Rules live in `config/validator-rules.yaml` and have stable IDs.

```yaml
rules:
  - id: TRACE-001
    enabled: true
    severity: error
    description: source unit must have a valid document and line range
  - id: SIZE-002
    enabled: true
    severity: warning
    soft_max_chars: 4000
    hard_max_chars: 12000
  - id: ATOMIC-003
    enabled: true
    severity: review
    modality_terms: [must, shall, should, may, phải, cần, được phép]
```

Record the exact ruleset version on every validation result.

## Required rule groups

### Traceability rules

- document exists in registry;
- line range is positive and ordered;
- source slice can reproduce `raw_text`;
- content hash matches;
- parser and builder versions are present.

Failure is `REJECT` when evidence cannot be reconstructed.

### Boundary rules

Detect:

- broken Markdown fence;
- table row without header context;
- list item missing required lead-in context;
- fragment beginning with unresolved pronouns or continuation markers;
- fragment ending with a colon or conjunction that clearly introduces following content;
- heading-only records when headings are not configured as indexable units.

Boundary issues normally produce `MERGE` or `REVIEW`.

### Size rules

Size limits protect downstream systems but are not the primary segmentation strategy.

- below minimum: consider `MERGE`, except explicit IDs, definitions or concise obligations;
- above soft maximum: `REVIEW` or `SPLIT`;
- above hard maximum: `SPLIT` unless the unit is an indivisible table requiring special handling.

Measure characters and estimated tokens, but keep decisions based on structure.

### Atomicity heuristics

Flag when a unit contains likely independent obligations:

- multiple distinct modality clauses;
- numbered independent requirements;
- unrelated actor/action pairs;
- independent positive and negative requirements;
- several sentences with separate test outcomes;
- conjunctions joining complete requirement clauses.

Do not split:

- a condition from the action it qualifies;
- an exception from the rule it limits;
- a table row from its header;
- a pronoun-bearing sentence from the antecedent required to understand it.

### Content quality rules

Flag:

- placeholder text such as TBD/TBC/XXX;
- contradictory modality in the same unit;
- undefined abbreviation according to configured terminology policy;
- copied boilerplate with no requirement content;
- malformed references.

These usually produce `REVIEW`, not rejection.

## Repair model

Repairs alter grouping, not wording.

```text
candidate units
→ validator decision
→ repair plan
→ rebuilt SourceUnits
→ revalidation
```

### Split repair

A split repair records:

```json
{
  "operation": "SPLIT",
  "parent_source_unit_id": "SU-parent",
  "child_source_unit_ids": ["SU-a", "SU-b"],
  "boundary_line_or_char": 120,
  "reason_rule_ids": ["ATOMIC-003"],
  "repair_version": "repair@0.1.0"
}
```

Children use exact contiguous source spans. No generated paraphrase is allowed.

### Merge repair

A merge repair records all parents and creates a new SourceUnit from contiguous source blocks. Non-contiguous merges require human approval.

### LLM-assisted adjudication

LLM assistance is allowed only for `REVIEW` units and returns a proposal:

```text
KEEP
SPLIT_AT_SENTENCE_BOUNDARIES
MERGE_WITH_PREVIOUS
MERGE_WITH_NEXT
HUMAN_REVIEW
```

The LLM must not rewrite content. A deterministic repair executor applies only valid source boundaries.

## Loop control

- maximum two automated repair cycles;
- repeated identical decision ends in human review;
- every repair creates lineage;
- no repaired unit is accepted without revalidation;
- parent units become inactive but remain auditable.

## Metrics

Track:

- PASS rate;
- SPLIT/MERGE/REVIEW/REJECT rates;
- rule-hit distribution;
- automated repair success rate;
- human correction rate;
- unit-size distribution before and after repair;
- source reconstruction failures.

## Acceptance criteria

1. Every candidate receives exactly one status.
2. Every non-PASS status includes at least one reason code.
3. Repairs preserve exact source text and provenance.
4. Parent/child lineage is queryable.
5. Repaired units are revalidated.
6. Validator output is deterministic for identical input and ruleset.
7. LLM failure cannot block deterministic processing; it routes to review.
8. No validator or repair component adds ontology or design meaning.