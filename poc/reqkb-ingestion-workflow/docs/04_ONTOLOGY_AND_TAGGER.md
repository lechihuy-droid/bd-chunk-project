# Lightweight requirement ontology and tagger

## Objective

Attach a controlled business-level interpretation to validated SourceUnits. The ontology is a schema; the tagger is the engine that fills it. This phase must not infer design artifacts.

## Ontology scope v0.1

### Classes

```text
Requirement
FunctionalRequirement
NonFunctionalRequirement
BusinessRule
Constraint
Assumption
Definition
Actor
BusinessAction
BusinessObject
BusinessEvent
Condition
Exception
Term
```

### Annotation slots

```yaml
requirement_type: functional | business_rule | constraint | non_functional | assumption | definition | unknown
modality: must | must_not | should | may | stated_fact | unknown
actors: []
actions: []
business_objects: []
events: []
conditions: []
exceptions: []
terms: []
```

### Forbidden design concepts

```text
API
Screen
ScreenField
DatabaseTable
DatabaseColumn
Batch
ExternalInterface
TestCase
DesignDecision
```

When source text explicitly mentions an existing API or screen, record it as a raw term/reference, not as a confirmed design ontology instance in this phase.

## Ontology registry

Store ontology in `config/requirement-ontology-light.yaml`.

```yaml
ontology_id: requirement-light
version: 0.1.0
classes:
  FunctionalRequirement:
    parent: Requirement
  BusinessRule:
    parent: Requirement
slots:
  modality:
    values: [must, must_not, should, may, stated_fact, unknown]
constraints:
  - id: ONT-001
    description: design classes are forbidden in ReqKB ingestion
```

Ontology changes require semantic versioning and migration notes.

## Tagging sequence

```text
validated SourceUnit
→ deterministic extraction
→ terminology lookup
→ LLM structured-output completion
→ Pydantic validation
→ ontology constraint validation
→ evidence validation
→ accept or review
```

## Deterministic extraction

Use rules for high-precision signals:

- explicit requirement IDs;
- modality terms such as must/shall/must not;
- configured actors and canonical terms;
- explicit condition markers: if, when, provided that, unless;
- explicit exception markers: except, however, unless;
- NFR keywords only when configured and unambiguous.

Rules may prefill fields. The LLM must not override high-confidence deterministic values without producing a conflict record.

## LLM structured output

Use Pydantic or provider-native JSON Schema.

```python
class OntologyTag(BaseModel):
    requirement_type: RequirementType
    modality: Modality
    actors: list[str]
    actions: list[str]
    business_objects: list[str]
    events: list[str]
    conditions: list[str]
    exceptions: list[str]
    confidence: float
```

Prompt requirements:

1. Include raw SourceUnit and separate heading context.
2. Include allowed values and forbidden concepts.
3. Instruct the model not to rewrite the source.
4. Instruct it to return `unknown` or empty arrays when unsupported.
5. Require conditions and exceptions to remain linked to the relevant action.
6. Require values to be supported by the source text.
7. Include ontology and prompt versions in runtime metadata.

## Terminology canonicalization

Use `config/terminology.yaml`.

```yaml
terms:
  - canonical_id: BO-PURCHASE-REQUEST
    label: PurchaseRequest
    aliases:
      - Purchase Request
      - PR
      - PurchaseApplication
      - 購買申請
```

Resolution order:

```text
exact canonical ID
→ exact alias
→ normalized alias
→ embedding candidate
→ LLM adjudication
→ human review
```

Do not automatically merge terms only because embeddings are similar. Store unresolved aliases explicitly.

## Evidence support policy

Each non-empty field must be supported by:

- an exact source phrase;
- a defensible grammatical interpretation;
- or deterministic heading context allowed by policy.

Examples:

```text
Source: "When an approver submits approval, the system records the decision."
actors: [Approver, System]
actions: [SubmitApproval, RecordDecision]
condition/event: [ApprovalSubmitted]
```

Unsupported example:

```text
API: POST /approve
DatabaseTable: purchase_request
```

These are design inferences and must be rejected.

## Confidence and review policy

Confidence is operational triage, not truth.

Recommended initial policy:

- deterministic-only, no conflicts: auto-accept;
- LLM confidence ≥ 0.90 and evidence validator PASS: auto-accept for POC;
- 0.70–0.90: review sample or queue according to risk;
- < 0.70: human review;
- any forbidden class or unsupported annotation: FAIL;
- deterministic/LLM conflict: REVIEW.

Thresholds must be calibrated on a golden dataset.

## Review corrections

Store:

- original source;
- deterministic annotations;
- model output;
- validator result;
- human correction;
- reviewer and timestamp.

Human corrections may update terminology and future rules, but must never modify the raw evidence record.

## Acceptance criteria

1. All output conforms to the ontology schema.
2. No design classes are produced.
3. Every annotation traces to a SourceUnit.
4. Unsupported fields are rejected or reviewed.
5. Deterministic values are preserved or conflicts are explicit.
6. Ontology, prompt, rules and model versions are recorded.
7. Reprocessing with the same deterministic settings is reproducible; LLM variability is measured.
8. Golden-set precision is reported separately for each slot.