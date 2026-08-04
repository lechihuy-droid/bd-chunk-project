# SourceUnit Validator and Repair Specification

## 1. Purpose

Validate each `SourceUnitCandidate` produced by the Builder and create an ontology-ready `ValidatedSourceUnit` only when the evidence boundary is acceptable.

The Validator answers one question:

> Is this the smallest source-backed evidence unit that expresses one main proposition, remains interpretable with allowed source context, and is suitable for ontology extraction?

The Validator may understand meaning only to evaluate evidence boundaries, atomicity, completeness, self-containment and ingestion scope. It must not:

- decide whether the business requirement is correct, feasible or desirable;
- add ontology labels or design concepts;
- rewrite, summarize or paraphrase source evidence;
- repair malformed source mappings;
- treat a processing failure as a semantic rejection.

## 2. Normative pipeline and ownership

```text
RegisteredDocumentRevision + ParseResult + BuildResult
  -> CandidateEvidenceResolver
  -> ValidationCandidate / CandidateEvidenceView
  -> Deterministic SourceUnitValidator
  -> ValidationResult

ACCEPT
  -> ValidatedSourceUnit
  -> Ontology Tagger

SPLIT or MERGE
  -> document-level RepairCoordinator
  -> immutable RepairPlan
  -> deterministic RepairExecutor
  -> revised ValidationCandidate
  -> revalidation

REVIEW
  -> optional LLMAdjudicationProposal
  -> deterministic boundary checks
  -> repair and revalidation, or ReviewTask

REJECT
  -> RejectedCandidate

invalid contract, hash, lookup or source mapping
  -> ProcessingError / BLOCKED
```

Public input remains the `SourceUnitCandidate` contract from document 02. The Validator normalizes each Builder candidate into an internal `ValidationCandidate`. Repaired candidates use the same internal contract, which can represent character-level evidence slices without requiring the Parser to create synthetic inline blocks.

| Component | Owns | Does not own |
|---|---|---|
| CandidateEvidenceResolver | Resolve block IDs, exact text slices, context and neighboring candidates | Semantic decisions |
| SourceUnitValidator | Atomicity, completeness, self-containment, context necessity and ontology-ingestion scope | Ontology tags, requirement correctness or source rewriting |
| RepairCoordinator | Resolve document-level split/merge conflicts and produce non-overlapping plans | Invent boundaries or wording |
| RepairExecutor | Apply an approved plan to exact source slices | Choose semantic meaning |
| LLM adjudicator | Propose an operation and exact candidate boundaries for `REVIEW` cases | Mutate candidates, assign canonical IDs or bypass deterministic checks |
| Ontology Tagger | Extract controlled entities, relations and requirement types from accepted units | Change evidence boundaries |
| Evidence Validator | Check whether ontology annotations are supported; return `PASS` or `FAIL` | SourceUnit boundary validation |

## 3. Canonical terminology and decisions

A `SourceUnit` does not exist before Validator acceptance.

```text
SourceUnitCandidate
  -> ValidationCandidate
  -> ValidationResult
  -> ACCEPT
  -> ValidatedSourceUnit
```

Use `ACCEPT`, not `PASS`, for SourceUnit boundary validation. Reserve `PASS` and `FAIL` for the Evidence Validator after ontology tagging.

```python
from enum import StrEnum


class SourceUnitDecision(StrEnum):
    ACCEPT = "accept"
    SPLIT = "split"
    MERGE = "merge"
    REVIEW = "review"
    REJECT = "reject"
```

Decision meanings are normative:

| Decision | Meaning | Required next action |
|---|---|---|
| `ACCEPT` | One main proposition; complete enough with allowed context; in ontology scope | Create `ValidatedSourceUnit` |
| `SPLIT` | Multiple propositions can be partitioned at exact evidence boundaries | Coordinate and execute split, then revalidate children |
| `MERGE` | Candidate needs adjacent primary evidence, not merely structural context | Coordinate and execute merge, then revalidate result |
| `REVIEW` | Meaning, scope or boundary cannot be decided safely, or proposed operations conflict | Optional LLM proposal and/or human review |
| `REJECT` | Evidence is valid and traceable but is deterministically outside ontology-ingestion scope | Preserve as a rejected candidate with reasons |

`REJECT` must never represent empty, corrupt, missing or untraceable input. Those cases are `ProcessingError` records and are operationally `BLOCKED`.

## 4. What an accepted SourceUnit means

An accepted unit must satisfy all of the following:

1. Every primary evidence fragment can be reconstructed exactly from the registered document revision.
2. The evidence expresses one main semantic proposition.
3. Conditions, exceptions and qualifiers remain attached to the proposition they constrain.
4. The proposition is interpretable independently within the context explicitly allowed by policy.
5. The evidence is within the configured Requirement Ontology ingestion scope.

The smallest meaningful unit is not necessarily:

- one Markdown block;
- one sentence;
- one actor/action pair;
- one test case;
- one ontology triple.

For example:

```text
The system shall lock the account after five failed attempts.
```

This is one accepted SourceUnit even though the Ontology Tagger may later extract actor, action, object and condition annotations.

## 5. Exact evidence slices

Document 02 defines line coordinates as zero-based and end-exclusive. Those line spans remain the canonical block-level source map. Validator repair additionally needs character-level precision because two propositions may occur in the same paragraph and on the same line.

```python
from pydantic import Field, model_validator


class EvidenceSliceRef(ContractModel):
    block_id: str
    start_char_0: int = Field(ge=0)
    end_char_0_exclusive: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_range(self) -> "EvidenceSliceRef":
        if self.end_char_0_exclusive <= self.start_char_0:
            raise ValueError("evidence slice must be non-empty")
        return self
```

Character offsets use these rules:

- zero-based and end-exclusive;
- relative to `ParsedBlock.raw_text`, never relative to a rendered or normalized paraphrase;
- counted as Unicode code points, matching Python `str` indexing;
- never byte offsets and never UTF-16 code-unit offsets;
- validated cross-record with `end_char_0_exclusive <= len(block.raw_text)`.

The initial adapter converts each Builder primary block into a full-block slice:

```python
EvidenceSliceRef(
    block_id=block.block_id,
    start_char_0=0,
    end_char_0_exclusive=len(block.raw_text),
)
```

A repaired candidate may contain partial-block slices. This is a Validator-domain refinement: the original `ParsedBlock`, `SourceSpan` and `raw_text` remain unchanged.

Canonical evidence is the ordered tuple of exact slices, not a rewritten joined string. Downstream prompt rendering may display the resolved fragments with provenance markers, but those markers are not evidence and are not hashed into the SourceUnit.

## 6. Input and evidence-view contracts

The following types are imported from document 02 and must not be duplicated with different semantics:

```text
ContractModel
RegisteredDocumentRevision
ParseResult
ParsedBlock
BlockKind
SourceSpan
BuildResult
SourceUnitCandidate
ContextRef
ContextRole
```

Validator-owned contracts are:

```python
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field


class CandidateOrigin(StrEnum):
    BUILDER = "builder"
    REPAIR = "repair"


class NeighborRelation(StrEnum):
    PREVIOUS = "previous"
    NEXT = "next"


class EvidenceFragment(ContractModel):
    slice_ref: EvidenceSliceRef
    raw_text: str
    raw_text_hash: str
    block_kind: BlockKind
    block_source_span: SourceSpan


class ResolvedContext(ContractModel):
    context_ref: ContextRef
    raw_text: str
    raw_text_hash: str


class ValidationCandidate(ContractModel):
    validation_candidate_revision_id: str
    document_revision_id: str
    origin: CandidateOrigin
    input_builder_candidate_revision_ids: tuple[str, ...] = Field(min_length=1)
    parent_validation_candidate_revision_ids: tuple[str, ...] = ()
    primary_slices: tuple[EvidenceSliceRef, ...] = Field(min_length=1)
    allowed_context_refs: tuple[ContextRef, ...] = ()
    continuity_fingerprint: str
    repair_cycle_index: int = Field(ge=0, le=2)
    validation_candidate_schema_version: str


class NeighborCandidateRef(ContractModel):
    validation_candidate_revision_id: str
    relation: NeighborRelation
    document_ordinal: int = Field(ge=0)
    primary_slices: tuple[EvidenceSliceRef, ...] = Field(min_length=1)


class CandidateEvidenceView(ContractModel):
    candidate: ValidationCandidate
    normalized_text_hash: str
    primary_fragments: tuple[EvidenceFragment, ...] = Field(min_length=1)
    resolved_contexts: tuple[ResolvedContext, ...] = ()
    neighbor_candidates: tuple[NeighborCandidateRef, ...] = ()
    primary_char_count: int = Field(ge=1)
```

The public batch request provides all authoritative lookups required by validation:

```python
class ValidationBatchRequest(ContractModel):
    ingestion_run_id: str
    registered_document_revision: RegisteredDocumentRevision
    parse_result: ParseResult
    build_result: BuildResult
    validator_profile: "ValidatorProfile"
    validation_request_schema_version: str
```

The request is invalid unless all nested records reference the same `document_revision_id` and compatible schema/profile versions. The Validator must not fetch an unversioned document or infer missing blocks from Markdown parser tokens.

### 6.1 Validation-candidate identity and continuity

`validation_candidate_revision_id` identifies one exact evidence selection in one document revision.

- For an initial candidate, generate it from canonical JSON containing the Builder `candidate_revision_id`, ordered full-block slices, allowed context block IDs and the validation-candidate schema version.
- For repaired output, generate it from canonical JSON containing the document revision ID, ordered primary slices, ordered context block IDs, parent validation-candidate IDs, repair plan ID and the validation-candidate schema version.
- Do not use delimiters, LLM output, mutable ordinals or display line numbers as an identity payload.

The initial `continuity_fingerprint` comes from the Builder candidate. Split and merge outputs recalculate it from ordered exact fragment hashes, block kinds and stable structural-context signatures. It excludes `document_revision_id`, absolute line numbers, character offsets and repair-cycle index. Like the Builder fingerprint, it is a cross-revision matching aid and is not guaranteed to be unique.

## 7. Context policy: ACCEPT with context versus MERGE

Context and primary evidence are different evidence roles.

- Heading, table header, list parent, lead-in and caption references remain context.
- Context is never prepended to primary evidence.
- A context reference may be allowed but unnecessary for a specific candidate.
- Validator output records which allowed references are required for interpretation.
- A missing adjacent proposition is primary evidence and requires `MERGE`; it must not be disguised as context.

```python
class ContextAssessment(ContractModel):
    allowed_context_block_ids: tuple[str, ...] = ()
    required_context_block_ids: tuple[str, ...] = ()
    unused_context_block_ids: tuple[str, ...] = ()
    missing_context_roles: tuple[ContextRole, ...] = ()
```

Cross-record invariants:

- required and unused IDs are disjoint subsets of allowed IDs;
- their union equals all allowed IDs after evaluation;
- every ID resolves to the same document revision;
- `missing_context_roles` cannot be repaired by inventing text.

Examples:

| Case | Result |
|---|---|
| Table data row needs its existing header | `ACCEPT` with `TABLE_HEADER` required context |
| Requirement is under heading `3.1 Login Function` | `ACCEPT` with ancestor section context when needed |
| Fragment `After five failed attempts.` needs the preceding action | `MERGE` with adjacent primary candidate |
| Candidate only lacks a heading label | Use existing heading context; never merge heading text into primary evidence |
| Table-row candidate has no header reference although Builder row mode requires one | `ProcessingError` for upstream contract violation |

A heading such as `3.1 Function Detail` never reaches the Validator as a standalone candidate. It remains a `HeadingBlock`/section context before and after validation.

## 8. Validator profile and rule configuration

Rules live in `config/validator-rules.yaml`, use stable IDs and versions, and are loaded into a typed profile.

```python
class RuleCategory(StrEnum):
    TRACEABILITY = "traceability"
    CONTEXT = "context"
    ATOMICITY = "atomicity"
    SIZE = "size"
    SCOPE = "scope"
    QUALITY_SIGNAL = "quality_signal"


class RuleSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class RuleAction(StrEnum):
    PROCESSING_ERROR = "processing_error"
    OBSERVE = "observe"
    SPLIT_OR_REVIEW = "split_or_review"
    MERGE_OR_REVIEW = "merge_or_review"
    REVIEW = "review"
    REJECT = "reject"


class ValidatorRuleConfig(ContractModel):
    rule_id: str
    rule_version: str
    order: int = Field(ge=0)
    category: RuleCategory
    severity: RuleSeverity
    action_on_hit: RuleAction
    detector_version: str
    enabled: bool = True


class ValidatorProfile(ContractModel):
    profile_name: str
    profile_version: str
    validator_schema_version: str
    ruleset_version: str
    decision_reducer_version: str
    sentence_segmenter_version: str
    scope_policy_version: str
    soft_max_chars: int = Field(gt=0)
    hard_max_chars: int = Field(gt=0)
    neighbor_window_size: int = Field(default=1, ge=1, le=2)
    max_automated_repair_cycles: int = Field(default=2, ge=0, le=2)
    llm_adjudication_enabled: bool = False
    llm_adjudication_policy_version: str | None = None
    rules: tuple[ValidatorRuleConfig, ...] = Field(min_length=1)
```

Profile validation must require `hard_max_chars > soft_max_chars`. Enabling LLM adjudication requires a policy version. Rule IDs and `order` values must be unique within one profile.

Illustrative YAML:

```yaml
profile_name: reqkb-source-unit-validator
profile_version: 0.2.0
validator_schema_version: 0.2.0
ruleset_version: validator-rules@0.2.0
decision_reducer_version: decision-reducer@0.2.0
sentence_segmenter_version: req-sentence-segmenter@0.1.0
scope_policy_version: req-ontology-scope@0.1.0
soft_max_chars: 4000
hard_max_chars: 12000
neighbor_window_size: 1
max_automated_repair_cycles: 2
llm_adjudication_enabled: false
rules:
  - rule_id: TRACE-001
    rule_version: "1"
    order: 10
    category: traceability
    severity: error
    action_on_hit: processing_error
    detector_version: traceability-detector@0.2.0
  - rule_id: ATOMIC-003
    rule_version: "2"
    order: 200
    category: atomicity
    severity: warning
    action_on_hit: split_or_review
    detector_version: atomicity-detector@0.2.0
  - rule_id: SCOPE-001
    rule_version: "1"
    order: 300
    category: scope
    severity: warning
    action_on_hit: reject
    detector_version: scope-detector@0.1.0
```

Rule order is explicit and stable. Configuration validation must reject duplicate `(rule_id, rule_version)` pairs, duplicate order values, unsupported actions and missing detector versions. Severity communicates importance; it is not a decision.

## 9. Rule hits and deterministic results

```python
class ObservedFact(ContractModel):
    name: str
    value: str


class RuleHit(ContractModel):
    rule_id: str
    rule_version: str
    category: RuleCategory
    severity: RuleSeverity
    suggested_decision: SourceUnitDecision | None = None
    message: str
    evidence_slices: tuple[EvidenceSliceRef, ...] = ()
    context_block_ids: tuple[str, ...] = ()
    observed_facts: tuple[ObservedFact, ...] = ()


class SplitChildSuggestion(ContractModel):
    child_index_0: int = Field(ge=0)
    primary_slices: tuple[EvidenceSliceRef, ...] = Field(min_length=1)


class SplitSuggestion(ContractModel):
    operation: Literal["split"] = "split"
    children: tuple[SplitChildSuggestion, ...] = Field(min_length=2)


class MergeSuggestion(ContractModel):
    operation: Literal["merge"] = "merge"
    input_validation_candidate_revision_ids: tuple[str, ...] = Field(min_length=2)


RepairSuggestion = Annotated[
    SplitSuggestion | MergeSuggestion,
    Field(discriminator="operation"),
]


class ValidationResult(ContractModel):
    validation_result_id: str
    validation_candidate_revision_id: str
    decision: SourceUnitDecision
    rule_hits: tuple[RuleHit, ...] = ()
    context_assessment: ContextAssessment
    repair_suggestion: RepairSuggestion | None = None
    validator_profile_version: str
    ruleset_version: str
    decision_reducer_version: str
    validation_result_schema_version: str
    repair_cycle_index: int = Field(ge=0, le=2)
    deterministic: Literal[True] = True
```

Required model and service-level invariants:

- every processed candidate receives exactly one `ValidationResult`;
- every non-`ACCEPT` result has at least one reason-bearing `RuleHit`;
- `SPLIT` has exactly one valid `SplitSuggestion`;
- `MERGE` has exactly one valid `MergeSuggestion`;
- `ACCEPT` and `REJECT` have no repair suggestion;
- `REVIEW` may carry diagnostic boundary hints, but not an executable plan in `repair_suggestion`;
- rule-hit evidence is a subset of the candidate or its allowed context;
- no result embeds modified source text.

`validation_result_id` is deterministic over the validation candidate ID, ruleset version, reducer version, canonical rule hits, context assessment and decision. Operational timestamps belong to a separate run/audit envelope.

## 10. Rule groups and ownership boundaries

### 10.1 Traceability and contract integrity

The resolver verifies before semantic rules run:

- registered document, `ParseResult` and `BuildResult` refer to one document revision;
- `0 <= start_line_0 < end_line_0_exclusive <= line_count` for every block span;
- each Builder primary/context block exists;
- Builder `primary_block_ids` and `primary_spans` have matching cardinality, order and source locations;
- each slice is in bounds and reconstructs the expected block substring;
- block hashes and recalculated evidence-fragment hashes match their exact text;
- recalculated structural counts agree with authoritative Builder facts where the profile declares them exact;
- parser, Builder, schema and profile versions are present and compatible;
- candidate primary slices are ordered and non-overlapping.

Failure creates `ProcessingError/BLOCKED`, not `REJECT`. Line zero is valid.

### 10.2 Atomicity

Atomicity rules look for more than one independently evaluable proposition, including:

- multiple complete modality clauses;
- numbered independent obligations;
- unrelated actor/action pairs;
- independent positive and negative requirements;
- sentences with separate test outcomes;
- conjunctions joining complete requirement clauses.

Heuristics must use pinned detector and sentence-segmenter versions. A heuristic may return `REVIEW` when it cannot supply exact safe boundaries. It must not assume that every conjunction or sentence boundary is a split point.

Do not split:

- a condition from the action it qualifies;
- an exception from the rule it limits;
- a pronoun-bearing sentence from its required antecedent;
- a data row from required header context;
- a coordinated phrase that represents one test outcome.

### 10.3 Completeness and self-containment

The Validator checks whether primary evidence plus allowed context contains enough information to interpret the proposition. Signals such as an unresolved pronoun, continuation marker, terminal colon or dependent clause may trigger `MERGE` only when an exact adjacent primary candidate is identified. Otherwise they trigger `REVIEW`.

Structural context is assessed through `ContextAssessment`; it is not merged into raw evidence.

### 10.4 Size

Size protects downstream systems but is not the primary segmentation strategy.

- below a configured advisory size: never merge based on size alone;
- above soft maximum: record a fact and evaluate structure;
- above hard maximum: `SPLIT` only when an exact evidence partition exists;
- an indivisible table or a candidate without safe split points becomes `REVIEW`.

Estimated token count may be recorded for operations, but it does not define evidence identity.

### 10.5 Ingestion scope

`REJECT` requires valid evidence and a deterministic, versioned scope rule. Examples include a project-configured section explicitly excluded from Requirement Ontology ingestion or source explicitly marked as non-normative sample content by supported syntax.

Ambiguous relevance is `REVIEW`, not `REJECT`. The Validator does not reject a requirement because it appears incorrect, incomplete as a business specification, inconsistent with another requirement or difficult to implement.

### 10.6 Quality signals owned elsewhere

The Validator consumes upstream diagnostics but does not duplicate their detectors:

| Signal | Detector owner | Validator behavior |
|---|---|---|
| Unclosed/broken Markdown fence | `MarkdownDiagnostics` | Block if diagnostic is blocking; otherwise include a rule hit and review as configured |
| Table row missing required header reference | Builder contract validation | `ProcessingError`, not MERGE |
| Heading-only candidate | Builder contract validation | `ProcessingError`; Builder must never emit it |
| Undefined abbreviation | `TerminologyCanonicalizer` | Defer; do not rediscover in Validator |
| Malformed/unresolved reference | `ReferenceExtractor/Resolver` | Consume status when available; do not own resolution |
| Copied boilerplate across the corpus | Corpus quality analyzer | Consume a quality signal; ambiguous cases go to review |
| Placeholder such as TBD/TBC/XXX | Versioned quality rule | Usually `REVIEW`; never silently discard |
| Unsupported ontology annotation | Evidence Validator after tagging | `FAIL` there, not a SourceUnit decision here |

## 11. Deterministic decision reducer

Rule evaluation and decision reduction are separate, versioned operations.

For each candidate:

1. Run contract and evidence reconstruction checks. On failure, emit `ProcessingError`; do not emit a semantic decision.
2. Evaluate enabled rules in stable configured order and collect `RuleHit` records.
3. Collect distinct non-`ACCEPT` suggested decisions.
4. Reduce them with the following exact policy:
   - no non-`ACCEPT` suggestion -> `ACCEPT` if all acceptance invariants hold; an uncovered failed invariant is `ProcessingError(code="RULE_COVERAGE_GAP")`;
   - only `SPLIT` -> `SPLIT` when a complete exact partition exists, otherwise `REVIEW`;
   - only `MERGE` -> `MERGE` when one compatible adjacent target set exists, otherwise `REVIEW`;
   - only `REJECT` -> `REJECT` when the scope rule is deterministic and versioned;
   - any set containing `REVIEW`, or two or more different decisions -> `REVIEW`.
5. Validate the result contract and generate its deterministic ID.

This policy prevents rule ordering from silently choosing between `SPLIT` and `MERGE`. The contributing hits remain visible in a `REVIEW` result.

## 12. Validated SourceUnit contract

Only `ACCEPT` creates a canonical SourceUnit:

```python
class ValidatedSourceUnit(ContractModel):
    source_unit_revision_id: str
    document_revision_id: str
    origin_validation_candidate_revision_id: str
    input_builder_candidate_revision_ids: tuple[str, ...] = Field(min_length=1)
    primary_fragments: tuple[EvidenceFragment, ...] = Field(min_length=1)
    required_context_refs: tuple[ContextRef, ...] = ()
    primary_evidence_hash: str
    continuity_fingerprint: str
    accepted_by_validation_result_id: str
    source_unit_schema_version: str
```

Invariants:

- the referenced validation result exists and has decision `ACCEPT`;
- fragments exactly match the accepted candidate slices and remain in document order;
- required context is exactly the required subset from `ContextAssessment`;
- context is not copied into `primary_fragments`;
- `primary_evidence_hash` is calculated from canonical JSON containing ordered slice references and exact fragment hashes;
- no validation history, ontology annotation or mutable review state is embedded in this immutable evidence record.

`source_unit_revision_id` is generated from canonical JSON containing `document_revision_id`, ordered primary slice references, ordered fragment hashes, required context block IDs and `source_unit_schema_version`. Validator profile and ruleset versions belong to the linked result, not to evidence identity. If a new ruleset accepts the same exact boundary and required context, the SourceUnit revision identity remains stable while a new validation result is appended.

## 13. Repair plan contracts

Repairs alter evidence selection and grouping only. They never alter `ParsedBlock.raw_text`.

```python
class RepairOperation(StrEnum):
    SPLIT = "split"
    MERGE = "merge"


class SplitChildPlan(ContractModel):
    child_index_0: int = Field(ge=0)
    primary_slices: tuple[EvidenceSliceRef, ...] = Field(min_length=1)
    inherited_context_refs: tuple[ContextRef, ...] = ()


class SplitRepairPlan(ContractModel):
    operation: Literal["split"] = "split"
    repair_plan_id: str
    parent_validation_candidate_revision_id: str
    children: tuple[SplitChildPlan, ...] = Field(min_length=2)
    reason_rule_ids: tuple[str, ...] = Field(min_length=1)
    repair_profile_version: str
    repair_cycle_index: int = Field(ge=1, le=2)


class MergeRepairPlan(ContractModel):
    operation: Literal["merge"] = "merge"
    repair_plan_id: str
    input_validation_candidate_revision_ids: tuple[str, ...] = Field(min_length=2)
    merged_primary_slices: tuple[EvidenceSliceRef, ...] = Field(min_length=1)
    inherited_context_refs: tuple[ContextRef, ...] = ()
    reason_rule_ids: tuple[str, ...] = Field(min_length=1)
    repair_profile_version: str
    repair_cycle_index: int = Field(ge=1, le=2)


RepairPlan = Annotated[
    SplitRepairPlan | MergeRepairPlan,
    Field(discriminator="operation"),
]


class RepairExecutionResult(ContractModel):
    repair_plan_id: str
    output_validation_candidates: tuple[ValidationCandidate, ...] = Field(min_length=1)
    retired_validation_candidate_revision_ids: tuple[str, ...] = Field(min_length=1)
    repair_executor_version: str
    repair_execution_result_schema_version: str
```

Repair plan IDs and output candidate IDs are generated from canonical plan contents, not from LLM-assigned identifiers.

## 14. Split invariants

A split is executable only if all children form an exact partition of parent primary evidence:

- every child slice is within a parent slice;
- children are ordered and non-overlapping;
- the ordered union of all child slices equals the parent slices exactly;
- no character, punctuation mark or whitespace is lost or duplicated;
- every child is non-empty;
- no context block is converted into primary evidence;
- no generated paraphrase or separator becomes evidence.

Example for two requirements on one line:

```text
The system locks the account. The system sends an email.
```

The split plan contains two exact character ranges within the same paragraph block. `boundary_line_or_char` is forbidden because it does not define a coordinate system.

If a safe exact partition cannot be produced, the decision is `REVIEW`, not an approximate split.

## 15. Merge invariants

MERGE is a document-level operation. The coordinator may merge candidates only when:

- all inputs belong to the same document revision;
- candidates are adjacent in Builder/repair document order;
- their primary evidence does not overlap;
- no unrelated primary candidate lies between them;
- the merge does not cross a section boundary unless a versioned policy explicitly permits it;
- context remains context and is deduplicated by block ID and role;
- merged slices remain ordered and exact.

Non-contiguous merges require human review and are not automated in the PoC.

Directional local outputs such as `MERGE_WITH_PREVIOUS` are suggestions, not plans. The coordinator must resolve them into one symmetric plan containing every input candidate ID.

## 16. Document-level RepairCoordinator

Do not execute `SPLIT` or `MERGE` independently while iterating through candidates. First validate the whole active candidate set for the document, then coordinate operations:

```text
validate all active candidates
  -> collect deterministic repair suggestions
  -> build operation graph
  -> find overlapping/conflicting components
  -> route conflicts to REVIEW
  -> emit non-overlapping RepairPlans
  -> sort plans by first source position
  -> execute left-to-right
  -> revalidate affected outputs and impacted neighbors
```

Coordinator rules:

- one active candidate may participate in at most one plan per cycle;
- identical compatible merge suggestions collapse into one plan;
- `SPLIT` and `MERGE` involving the same candidate conflict and become `REVIEW`;
- overlapping merge groups that are not identical become `REVIEW`;
- a plan cannot consume an already retired candidate;
- unaffected candidates retain their exact identities;
- repair lineage is append-only and queryable.

This prevents duplicate evidence, lost evidence and order-dependent merge behavior.

## 17. LLM-assisted adjudication

LLM assistance is optional and allowed only after the deterministic result is `REVIEW`. The LLM produces a proposal, never a validation result or repair mutation.

```python
class LLMProposalOperation(StrEnum):
    KEEP = "keep"
    SPLIT = "split"
    MERGE = "merge"
    HUMAN_REVIEW = "human_review"


class LLMAdjudicationProposal(ContractModel):
    proposal_id: str
    validation_result_id: str
    validation_candidate_revision_id: str
    input_hash: str
    operation: LLMProposalOperation
    proposed_split_children: tuple[SplitChildSuggestion, ...] = ()
    proposed_merge_candidate_revision_ids: tuple[str, ...] = ()
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    model_provider: str
    model_name: str
    model_version: str
    prompt_version: str
    adjudication_policy_version: str
    raw_response_ref: str
    proposal_schema_version: str
```

Requirements:

- `input_hash` covers exact candidate fragments, allowed context, deterministic rule hits and prompt inputs;
- the model must return exact `EvidenceSliceRef` boundaries for a split;
- merge targets must be candidate IDs from the supplied neighbor window;
- the proposal cannot contain replacement source text;
- `KEEP` cannot automatically turn `REVIEW` into `ACCEPT`; it becomes reviewer evidence;
- an exact SPLIT/MERGE proposal may be converted into a deterministic `RepairPlan` only after all boundary and conflict checks pass;
- repaired output is always revalidated by the deterministic Validator;
- model timeout, malformed output or low confidence routes to `ReviewTask` and cannot block deterministic processing of other candidates.

Do not claim LLM output is deterministic. Persist model, prompt, policy, input hash, proposal and raw-response reference separately from deterministic validation.

## 18. Loop control and lineage

Default and maximum automated repair cycles for the PoC are two.

Each cycle records:

- input candidate IDs;
- validation result IDs;
- repair plan IDs;
- output candidate IDs;
- repair executor version;
- ruleset and reducer versions.

The loop signature is the canonical hash of the active ordered evidence boundaries plus the proposed operation graph. Stop and create `ReviewTask` when:

- the same loop signature repeats;
- the next repair exceeds cycle two;
- a coordinator conflict exists;
- a proposed plan fails executor invariants;
- repaired candidates remain ambiguous under the deterministic rules.

Repeating only the same decision name is not a sufficient loop detector; boundary changes must be part of the signature.

Parent candidates become inactive after successful repair but remain auditable. No repaired candidate is accepted without a new `ValidationResult`.

## 19. Rejection, review and processing-error contracts

```python
class RejectedCandidate(ContractModel):
    validation_candidate_revision_id: str
    rejected_by_validation_result_id: str
    reason_rule_ids: tuple[str, ...] = Field(min_length=1)
    rejected_candidate_schema_version: str


class ReviewTask(ContractModel):
    review_task_id: str
    document_revision_id: str
    validation_candidate_revision_ids: tuple[str, ...] = Field(min_length=1)
    validation_result_ids: tuple[str, ...] = Field(min_length=1)
    reason_rule_ids: tuple[str, ...] = Field(min_length=1)
    llm_proposal_id: str | None = None
    review_task_schema_version: str


class ProcessingStage(StrEnum):
    EVIDENCE_RESOLUTION = "evidence_resolution"
    VALIDATOR = "validator"
    REPAIR_COORDINATOR = "repair_coordinator"
    REPAIR_EXECUTOR = "repair_executor"


class ProcessingError(ContractModel):
    processing_error_id: str
    ingestion_run_id: str
    document_revision_id: str
    affected_validation_candidate_revision_ids: tuple[str, ...] = ()
    stage: ProcessingStage
    code: str
    message: str
    retryable: bool
    component_version: str
    processing_error_schema_version: str
```

Examples:

| Condition | Record |
|---|---|
| Missing document revision | `ProcessingError(code="DOCUMENT_REVISION_NOT_FOUND")` |
| Hash mismatch | `ProcessingError(code="EVIDENCE_HASH_MISMATCH")` |
| Slice outside block | `ProcessingError(code="EVIDENCE_SLICE_OUT_OF_BOUNDS")` |
| Valid candidate in excluded non-normative section | `RejectedCandidate` |
| Unclear proposition boundary | `ReviewTask` |

## 20. Batch result contract

```python
class ValidationBatchResult(ContractModel):
    ingestion_run_id: str
    document_revision_id: str
    validation_results: tuple[ValidationResult, ...] = ()
    accepted_source_units: tuple[ValidatedSourceUnit, ...] = ()
    repair_plans: tuple[RepairPlan, ...] = ()
    repair_execution_results: tuple[RepairExecutionResult, ...] = ()
    rejected_candidates: tuple[RejectedCandidate, ...] = ()
    review_tasks: tuple[ReviewTask, ...] = ()
    processing_errors: tuple[ProcessingError, ...] = ()
    validator_profile_version: str
    validation_batch_result_schema_version: str
```

Batch-level invariants:

- each active processable candidate has one result in each cycle in which it participates;
- blocked candidates appear only in `processing_errors` for that failed cycle;
- every accepted unit references one `ACCEPT` result;
- every rejected candidate references one `REJECT` result;
- every plan has at least one initiating `SPLIT` or `MERGE` result; an adjacent `ACCEPT` candidate may be consumed by a compatible merge before its SourceUnit is materialized;
- every unresolved `REVIEW` result produces one review task;
- no active accepted SourceUnits have overlapping primary evidence unless a documented table/list profile explicitly represents a parent aggregate instead of children, never both.

## 21. Deterministic execution algorithm

Reference sequence:

```python
def validate_document(request: ValidationBatchRequest) -> ValidationBatchResult:
    resolved = evidence_resolver.resolve(request)
    pending = resolved.validation_candidates
    accumulator = batch_result_factory.start(request)

    for cycle_index in range(request.validator_profile.max_automated_repair_cycles + 1):
        views = evidence_resolver.build_views(pending, cycle_index)
        results, errors = validator.validate_all(views, request.validator_profile)
        accumulator.add_results(results, errors)

        if not pending:
            break

        if cycle_index == request.validator_profile.max_automated_repair_cycles:
            accumulator.add_reviews(review_factory.from_unresolved(results))
            break

        plans, conflicts = repair_coordinator.coordinate(pending, results)
        consumed_ids = repair_coordinator.consumed_candidate_ids(plans)
        accumulator.add_reviews(review_factory.from_conflicts(conflicts))

        terminal_views = views.excluding(consumed_ids).excluding_conflicts(conflicts)
        accumulator.add_source_units(
            source_unit_factory.from_accept_results(terminal_views, results)
        )
        accumulator.add_rejections(
            rejection_factory.from_reject_results(terminal_views, results)
        )
        accumulator.add_reviews(
            review_factory.from_review_results(terminal_views, results)
        )

        if not plans:
            break

        execution_results = repair_executor.execute(plans, pending)
        accumulator.add_repairs(plans, execution_results)
        pending = candidate_set.repaired_outputs(execution_results)
        loop_guard.assert_new_signature(pending, plans)

    return accumulator.finish()
```

Coordination occurs before materializing `ACCEPT` units because a neighboring accepted candidate may be a required input to a compatible merge. Candidates consumed by a plan are not materialized or rejected in that cycle. The implementation may optimize unchanged candidates, but optimization must not change observable results or skip impacted-neighbor checks after merge/split operations.

## 22. Metrics and observability

Track at minimum:

- first-pass `ACCEPT` rate;
- `ACCEPT` rate after automated repair;
- `SPLIT`, `MERGE`, `REVIEW` and `REJECT` rates by cycle;
- `ProcessingError/BLOCKED` rate separately from semantic decisions;
- rule-hit distribution by rule/version;
- decision-conflict rate;
- split/merge plan count and executor failure rate;
- automated repair success rate;
- human correction and rejection rates;
- primary evidence size before and after repair;
- exact reconstruction failure count;
- duplicate/overlap invariant failure count;
- LLM proposal, valid-boundary, applied-plan and human-override rates;
- deterministic rerun stability;
- validation, coordination, repair and review latency.

Do not combine first-pass acceptance with acceptance after repair. Do not include blocked candidates in the `REJECT` denominator.

## 23. Acceptance tests

### 23.1 Golden scenarios

1. Candidate beginning at `start_line_0=0` passes traceability checks.
2. Two independent requirements on one line split through exact character offsets.
3. Condition and qualified action remain one unit.
4. Exception remains attached to the rule it limits.
5. Heading `3.1 Function Detail` remains context and never becomes a SourceUnit.
6. Table row is `ACCEPT` with existing header context recorded as required.
7. Fragment requiring adjacent primary evidence returns `MERGE` with exact candidate IDs.
8. Missing table header required by Builder profile creates `ProcessingError`, not `MERGE` or `REJECT`.
9. Corrupt span or hash creates `ProcessingError`, not `REJECT`.
10. Valid evidence in an explicitly excluded section returns `REJECT`.
11. Ambiguous ontology relevance returns `REVIEW`, not `REJECT`.
12. SPLIT children partition parent evidence exactly, including punctuation and whitespace.
13. Conflicting or overlapping MERGE proposals route every involved candidate to `REVIEW`.
14. A candidate proposed for both SPLIT and MERGE routes to `REVIEW`.
15. Repair cycle creates no duplicate, overlap or lost evidence.
16. LLM proposal cannot change `ParsedBlock.raw_text`, candidate IDs or SourceUnit IDs directly.
17. LLM `KEEP` proposal does not bypass deterministic `REVIEW`.
18. Failed LLM output does not block deterministic results for other candidates.
19. Same source, profile and ruleset produce identical deterministic results and IDs.
20. Metrics distinguish first-pass `ACCEPT` from post-repair `ACCEPT`.
21. Repeating identical operation graph and boundaries creates one review task and stops the loop.
22. Automated repair never exceeds two cycles.
23. Vietnamese, Japanese, emoji and combining-character fixtures use the documented code-point offset convention.
24. Required and unused context form a disjoint partition of allowed context.
25. Accepted SourceUnit creation fails when its linked result is not `ACCEPT`.

### 23.2 Property-based invariants

For generated candidate sets and valid source documents, verify:

- evidence resolution returns only exact substrings of referenced blocks;
- every slice is non-empty and in bounds;
- canonical hashes and IDs are independent of dictionary insertion order;
- initial ValidationCandidates contain full-block slices matching Builder primary blocks;
- split output is an exact partition of parent slices;
- merge output is the exact ordered union of input slices;
- context never becomes primary evidence through repair;
- no candidate participates in more than one repair plan per cycle;
- applying a valid plan then replaying it is idempotent or rejected as already applied;
- active accepted units do not overlap or duplicate evidence;
- processing failures cannot be serialized as `REJECT` decisions;
- result reduction is independent of rule evaluation iteration order after canonical sorting;
- unexpected fields are rejected and mutable shared defaults cannot occur.

## 24. Definition of done

This specification is coding-ready when:

- all contracts above exist as executable Pydantic v2 models with `extra="forbid"`;
- the Builder-to-Validator adapter consumes only contracts from document 02, never native parser tokens;
- character-level repair offsets follow one tested Unicode convention;
- the deterministic rule engine and decision reducer are separately versioned and tested;
- `ProcessingError`, `REJECT` and `REVIEW` cannot be confused by schema or reducer logic;
- the document-level coordinator produces only non-overlapping repair plans;
- every repair preserves exact evidence and lineage and is revalidated;
- LLM proposals remain separate, auditable records and cannot mutate evidence directly;
- golden tests and property-based invariants pass;
- first-pass and post-repair quality metrics are emitted separately;
- Ontology Tagger input is only `ValidatedSourceUnit` created from an `ACCEPT` result.
