# Parser and SourceUnit Builder Specification

## 1. Purpose

Convert a registered Markdown requirement document into deterministic structural blocks, then assemble those blocks into `SourceUnitCandidate` records for validation.

This stage is evidence-first:

- the Parser identifies Markdown structure and exact source locations;
- the SourceUnitBuilder packages structural blocks according to a versioned deterministic profile;
- neither component decides requirement meaning, atomicity, completeness, or ontology labels;
- a final `SourceUnit` exists only after the Validator accepts or repairs a candidate.

## 2. Pipeline and ownership boundary

```text
Registered Markdown
  -> MarkdownParser
  -> ParseResult / ParsedBlock[]
  -> SourceUnitBuilder
  -> BuildResult / SourceUnitCandidate[]
  -> Validator
  -> ValidatedSourceUnit[]
  -> Ontology Tagger
```

| Component | Question answered | Allowed responsibility | Forbidden responsibility |
|---|---|---|---|
| Parser | What structure exists, and where is it in the source? | Parse headings, paragraphs, lists, tables, blockquotes and fences; preserve source spans, hierarchy and raw evidence | Decide whether text is a requirement, atomic, testable or complete |
| SourceUnitBuilder | Which blocks are packaged into each candidate under the configured structural profile? | Select primary blocks, attach structural context, calculate deterministic facts and record skipped blocks | Interpret business meaning; return `ACCEPT`, `SPLIT`, `MERGE`, `REVIEW` or `REJECT` |
| Validator | Is this the smallest meaningful unit that remains interpretable for ontology extraction? | Check atomicity, completeness and self-containment; request split/merge/review/reject | Add ontology tags or rewrite source evidence |
| Ontology Tagger | What business concepts and relationships are expressed? | Extract entities, relations, requirement types and domain concepts | Change provenance or source boundaries |

The decision rule is:

1. If the operation needs only Markdown syntax and source position, it belongs to the Parser.
2. If it packages blocks using a fixed, versioned rule, it belongs to the Builder.
3. If it must understand the meaning of the requirement, it belongs to the Validator or a later semantic component.

The statement `Builder determines whether content is an independently testable assertion` is explicitly invalid. The correct contract is:

> The Builder creates structurally bounded candidates. The Validator determines whether each candidate is atomic, complete, self-contained with its referenced context, and ready for ontology extraction.

## 3. Component separation and deployment

`MarkdownParser` and `SourceUnitBuilder` must be separate classes/modules with separate Pydantic input/output contracts and separate tests. The Builder must never consume native `markdown-it-py` tokens.

For the PoC, both modules may run synchronously in the same process and in one LangGraph node:

```python
def parse_and_build_node(state: WorkflowState) -> dict:
    parsed: ParseResult = parser.parse(state.registered_document)
    built: BuildResult = builder.build(parsed, state.builder_profile)
    return {
        "parse_result": parsed,
        "build_result": built,
    }
```

Create separate LangGraph nodes only when independent cache, retry, observability, profile experimentation or persistence of `ParseResult` provides operational value. Do not split them into separate services for the PoC.

## 4. Normative invariants

The following rules are mandatory:

- `raw_text` is always reconstructed from the registered normalized source by source span; it is never rendered back from parser tokens.
- All internal line coordinates are zero-based and end-exclusive.
- Heading, table-header, list-parent and lead-in context is referenced separately; it is not prepended to primary evidence.
- Parser and Builder outputs contain structural facts only.
- Every contract rejects unknown fields and uses `default_factory` for mutable defaults.
- Parser-library versions, parser profile, diagnostics profile, contract schema and builder profile are persisted.
- IDs are generated from canonical serialization, never from delimiter-concatenated strings.
- Exact revision identity and cross-revision continuity matching are separate concepts.
- A warning is never a substitute for lost evidence. If a required source mapping cannot be produced, the affected candidate is blocked.

## 5. Document registration, normalization and audit hashes

The Parser consumes a `RegisteredDocumentRevision`, not arbitrary bytes. Document registration performs these operations in order:

1. Calculate the SHA-256 `original_bytes_hash` from the unchanged input bytes.
2. Decode UTF-8 strictly. Invalid UTF-8 is a document-level failure.
3. Detect and remove a UTF-8 BOM from the registered text while recording `had_utf8_bom=true`.
4. Normalize CRLF and CR line endings to LF.
5. Preserve all other characters, whitespace and the presence or absence of a final newline. Do not apply Unicode NFC/NFKC normalization to evidence text.
6. Calculate the SHA-256 `normalized_text_hash` from the UTF-8 encoding of the normalized text.

Minimum registration metadata:

```python
from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RegisteredDocumentRevision(ContractModel):
    workspace_id: str
    document_id: str
    document_revision_id: str
    original_bytes_hash: str
    normalized_text_hash: str
    normalized_text: str
    had_utf8_bom: bool
    newline_profile_version: str
```

Both hashes must be persisted. `original_bytes_hash` supports byte-level audit; `normalized_text_hash` proves the exact text against which spans, block hashes and candidate evidence were calculated.

## 6. Canonical source-coordinate convention

Use one coordinate system throughout Parser, Builder, Validator and persistence:

```python
from pydantic import model_validator

class SourceSpan(ContractModel):
    start_line_0: int
    end_line_0_exclusive: int

    @model_validator(mode="after")
    def validate_range(self) -> "SourceSpan":
        if self.start_line_0 < 0:
            raise ValueError("start_line_0 must be >= 0")
        if self.end_line_0_exclusive <= self.start_line_0:
            raise ValueError("source span must contain at least one line")
        return self
```

Raw evidence extraction is therefore:

```python
lines = registered.normalized_text.splitlines(keepends=True)
raw_text = "".join(
    lines[span.start_line_0:span.end_line_0_exclusive]
)
```

For a one-line token map `[0, 1]`, the exact slice is `lines[0:1]`. Never subtract one from `start_line_0`.

Convert coordinates only in the presentation layer:

```text
display_start_line_1 = start_line_0 + 1
display_end_line_1_inclusive = end_line_0_exclusive
```

All spans must satisfy `0 <= start < end <= line_count`. A parser-library token without a line map is not automatically an error: inline and closing tokens may legitimately have no map. `LINE_MAP_UNAVAILABLE` applies only when the adapter requires a block-level evidence span and cannot derive one deterministically.

## 7. Parser implementation

Use `markdown-it-py` behind an internal adapter. Pin the core library and every enabled plugin in the lock file and persist their versions in the parse result.

```python
from markdown_it import MarkdownIt

md = (
    MarkdownIt("commonmark", {"html": False})
    .enable("table")
)
tokens = md.parse(registered.normalized_text)
```

Configuration requirements:

- HTML handling must follow an explicit repository policy. Disabled or unsupported HTML must not disappear silently.
- Table support must be explicitly enabled and covered by golden fixtures.
- Block-level token maps must be converted to canonical `SourceSpan` without changing their zero-based, end-exclusive meaning.
- Parser recovery behavior and project-specific suspicious syntax are recorded through structured diagnostics.
- The adapter must preserve source hierarchy without exposing library token types downstream.

The Parser produces blocks for:

- headings;
- paragraphs;
- list containers and list items;
- tables and table rows;
- blockquotes;
- fenced code blocks;
- horizontal rules.

Inline emphasis, links and code spans may be retained as typed inline metadata, but they do not become independent `ParsedBlock` records unless a later documented use case requires them.

## 8. Parser contracts

The following models define the required shape. Implementations may split them across files, but field meaning and ownership must remain unchanged.

```python
from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field


class BlockKind(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_CONTAINER = "list_container"
    LIST_ITEM = "list_item"
    TABLE = "table"
    TABLE_ROW = "table_row"
    BLOCKQUOTE = "blockquote"
    FENCED_CODE = "fenced_code"
    HORIZONTAL_RULE = "horizontal_rule"


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DiagnosticStage(StrEnum):
    REGISTRATION = "registration"
    PARSER = "parser"
    MARKDOWN_DIAGNOSTICS = "markdown_diagnostics"
    BUILDER = "builder"


class PipelineDiagnostic(ContractModel):
    code: str
    severity: DiagnosticSeverity
    stage: DiagnosticStage
    source_span: SourceSpan | None = None
    detector_version: str
    blocking: bool
    message: str
    related_block_ids: tuple[str, ...] = ()


class ParsedBlockBase(ContractModel):
    block_id: str
    document_revision_id: str
    source_span: SourceSpan
    raw_text: str
    raw_text_hash: str
    ordinal: int
    heading_context_ids: tuple[str, ...] = ()
    parent_block_id: str | None = None
    previous_block_id: str | None = None
    next_block_id: str | None = None
    parser_profile_version: str
    parser_schema_version: str


class HeadingBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.HEADING]
    heading_level: int = Field(ge=1, le=6)
    title_raw: str
    section_number: str | None = None
    parent_heading_id: str | None = None


class ParagraphBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.PARAGRAPH]


class ListContainerBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.LIST_CONTAINER]
    ordered: bool
    start_number: int | None = None
    child_item_ids: tuple[str, ...] = ()


class ListItemBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.LIST_ITEM]
    list_container_id: str
    item_index_0: int
    parent_item_id: str | None = None


class TableBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.TABLE]
    header_row_id: str | None = None
    data_row_ids: tuple[str, ...] = ()


class TableRowBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.TABLE_ROW]
    table_id: str
    row_index_0: int
    is_header: bool
    cell_text: tuple[str, ...] = ()


class BlockquoteBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.BLOCKQUOTE]
    quote_depth: int = Field(ge=1)


class FencedCodeBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.FENCED_CODE]
    fence_marker: str
    info_string: str = ""


class HorizontalRuleBlock(ParsedBlockBase):
    block_kind: Literal[BlockKind.HORIZONTAL_RULE]


ParsedBlock = Annotated[
    HeadingBlock
    | ParagraphBlock
    | ListContainerBlock
    | ListItemBlock
    | TableBlock
    | TableRowBlock
    | BlockquoteBlock
    | FencedCodeBlock
    | HorizontalRuleBlock,
    Field(discriminator="block_kind"),
]
```

`raw_text` is the exact normalized-source slice for `source_span`. Structured fields such as `cell_text` are parser views and must never replace raw evidence.

The document-level result is:

```python
class ParseResult(ContractModel):
    workspace_id: str
    document_id: str
    document_revision_id: str
    original_bytes_hash: str
    normalized_text_hash: str
    parser_name: str
    parser_library_version: str
    parser_plugin_versions: dict[str, str] = Field(default_factory=dict)
    parser_profile_version: str
    parser_schema_version: str
    blocks: tuple[ParsedBlock, ...] = ()
    diagnostics: tuple[PipelineDiagnostic, ...] = ()
```

`block_id` identifies an exact block in one `DocumentRevision`. It must be deterministic for an unchanged registered revision and parser profile. It is not a cross-revision continuity key. Generate it from canonical JSON containing `document_revision_id`, `block_kind`, `source_span`, `raw_text_hash` and `parser_profile_version`.

## 9. Heading and section context

Maintain a heading stack while walking block-level tokens. A heading block is retained as a structural `SectionContext`; it is not a candidate by itself.

`HeadingBlock` is the normative, source-backed representation of section context. Do not persist a second copy with independent fields. A downstream API may expose a derived `SectionContext` view containing `block_id`, `section_number`, `title_raw`, `heading_level`, `parent_heading_id` and `source_span`.

Example:

```markdown
## 3.1 Function Detail

The system validates the user credentials.
```

Parser output, abbreviated:

```yaml
- block_kind: heading
  block_id: heading-031
  heading_level: 2
  section_number: "3.1"
  title_raw: Function Detail
  parent_heading_id: heading-03
  source_span:
    start_line_0: 0
    end_line_0_exclusive: 1

- block_kind: paragraph
  block_id: paragraph-001
  heading_context_ids: [heading-031]
  source_span:
    start_line_0: 2
    end_line_0_exclusive: 3
```

Rules:

- `heading_level` comes from Markdown syntax (`#` through `######`). It must not be inferred from `3.1`.
- `section_number` is optional and is extracted only by a versioned deterministic pattern.
- `title_raw` preserves the heading title without rewriting it.
- Section hierarchy follows Markdown heading levels. A jump in heading level is preserved and may produce a diagnostic; the Parser must not invent missing headings.
- Duplicate heading titles remain distinct blocks with distinct locations.
- Heading text is never prepended to paragraph or table-row evidence.

If the heading is `3.1 Login Function Detail`, `Login` may later provide evidence for a business function. The Ontology Tagger may use the referenced heading, but the Parser and Builder must not create `Function = Login` or `Function = Function Detail`.

## 10. SourceUnitBuilder input and output contracts

The Builder accepts only `ParseResult` plus a versioned `BuilderProfile`.

```python
class ListBuildMode(StrEnum):
    ITEM = "item"
    GROUP = "group"


class TableBuildMode(StrEnum):
    WHOLE_TABLE = "whole_table"
    ROW = "row"


class SectionBuildRule(ContractModel):
    rule_id: str
    heading_path_regex: str
    list_mode: ListBuildMode
    table_mode: TableBuildMode


class BuilderProfile(ContractModel):
    profile_name: str
    profile_version: str
    list_mode: ListBuildMode = ListBuildMode.ITEM
    table_mode: TableBuildMode = TableBuildMode.WHOLE_TABLE
    section_rules: tuple[SectionBuildRule, ...] = ()
    include_blockquotes: bool = True
    include_fenced_code: bool = False
    hard_candidate_char_limit: int | None = Field(default=None, gt=0)
    sentence_segmenter_version: str | None = None


class ContextRole(StrEnum):
    ANCESTOR_SECTION = "ancestor_section"
    TABLE_HEADER = "table_header"
    LIST_PARENT = "list_parent"
    LIST_LEAD_IN = "list_lead_in"
    CAPTION = "caption"


class ContextRef(ContractModel):
    block_id: str
    role: ContextRole
    source_span: SourceSpan


class StructuralFacts(ContractModel):
    block_count: int = Field(ge=1)
    line_count: int = Field(ge=1)
    char_count: int = Field(ge=0)
    sentence_count: int | None = None
    sentence_segmenter_version: str | None = None
    hard_limit_exceeded: bool = False


class SourceUnitCandidate(ContractModel):
    candidate_revision_id: str
    continuity_fingerprint: str
    document_revision_id: str
    primary_block_ids: tuple[str, ...] = Field(min_length=1)
    primary_spans: tuple[SourceSpan, ...] = Field(min_length=1)
    context_refs: tuple[ContextRef, ...] = ()
    structural_facts: StructuralFacts
    builder_profile_version: str
    builder_schema_version: str


class SkippedBlockReason(StrEnum):
    STRUCTURAL_CONTEXT_ONLY = "structural_context_only"
    EXCLUDED_BY_PROFILE = "excluded_by_profile"
    REPRESENTED_BY_PARENT_CANDIDATE = "represented_by_parent_candidate"


class SkippedBlock(ContractModel):
    block_id: str
    reason: SkippedBlockReason


class BuildResult(ContractModel):
    document_revision_id: str
    parse_result_hash: str
    builder_profile_version: str
    builder_schema_version: str
    candidates: tuple[SourceUnitCandidate, ...] = ()
    skipped_blocks: tuple[SkippedBlock, ...] = ()
    diagnostics: tuple[PipelineDiagnostic, ...] = ()
```

`primary_spans` may contain multiple ordered, non-overlapping spans when a structural profile intentionally packages several blocks. They identify primary evidence only. `context_refs` remain separate and are never concatenated into `raw_text`.

Section rules are evaluated in declared tuple order; the first match wins. The BuildResult must record the matched `rule_id` in candidate diagnostics or trace metadata. Profile validation must reject duplicate rule IDs and invalid regular expressions.

The Builder may calculate deterministic facts such as character count, line count and, when a segmenter is pinned, sentence count. `hard_limit_exceeded=true` is a fact for the Validator; it is not a `SPLIT_REQUIRED` decision.

## 11. SourceUnitBuilder rules

### 11.1 Headings and structural-only blocks

- A heading is recorded as context and skipped with `STRUCTURAL_CONTEXT_ONLY`; it never becomes a candidate by itself.
- A horizontal rule is structural-only unless a versioned project profile explicitly defines another deterministic treatment.
- Empty structural containers do not become candidates.

### 11.2 Paragraphs

- Default profile: one paragraph block becomes one candidate.
- Do not split a paragraph because of embedding preferences.
- Record size facts and hard-limit diagnostics. The Validator decides whether semantic split or review is required.
- Do not decide whether the paragraph is a requirement or an independently testable assertion.

### 11.3 Lists

List behavior must be selected explicitly in `BuilderProfile`:

- `ITEM`: create one candidate per configured leaf/item block; parent item, list container and immediate lead-in may be attached as context.
- `GROUP`: create one candidate for the list container and mark child items as represented by that parent candidate.
- a matching `SectionBuildRule` may override the profile default using a deterministic heading-path pattern, never an LLM judgment.

The Builder must preserve list ordering, container ID, parent item ID and nesting depth. It must not ask whether an item is independently testable or semantically complete. If an item such as `After five failed attempts` depends on a lead-in, the Builder records the structural relationship; the Validator decides `ACCEPT` with context or `MERGE`.

A block cannot be primary evidence in both a list-group candidate and a list-item candidate in the same profile execution.

### 11.4 Tables

Table behavior must also be profile-driven:

- `WHOLE_TABLE`: preserve the full table as one candidate. This is the safe default for unknown or matrix-shaped tables.
- `ROW`: create one candidate per data row; the header row, table caption and ancestor headings are context references.
- a matching `SectionBuildRule` may override the default for known document/section structure.

Never emit isolated cells. In row mode, the primary evidence is the exact data-row span; column headers remain separate context. Escaped pipes, alignment rows and multiline constructs must be handled by parser fixtures rather than by reconstructing Markdown from cells.

### 11.5 Blockquotes, notes, code and examples

- Blockquotes are included or excluded by profile; the Builder does not judge whether they contain requirement-relevant content.
- Note/warning style may be recorded only when deterministically encoded by supported syntax or a configured marker.
- Fenced code remains separate from prose. The profile may exclude it from ontology candidates by default and record the skip reason.
- `example` may be assigned only from deterministic syntax or configured labels. Do not infer example status from meaning.

### 11.6 Primary evidence versus structural context

Use the following rule:

- `primary_block_ids` and `primary_spans` are the evidence being evaluated as the candidate.
- `context_refs` identify source-backed context needed or potentially useful for interpretation.
- Context blocks remain independently retrievable with their own spans and hashes.
- The Builder never creates a rewritten sentence that combines primary evidence and context.

Example table candidate:

```yaml
candidate_revision_id: candidate-001
primary_block_ids: [table-row-002]
primary_spans:
  - start_line_0: 12
    end_line_0_exclusive: 13
context_refs:
  - block_id: table-row-001
    role: table_header
    source_span:
      start_line_0: 10
      end_line_0_exclusive: 11
  - block_id: heading-031
    role: ancestor_section
    source_span:
      start_line_0: 7
      end_line_0_exclusive: 8
```

## 12. Handoff to Validator and Ontology Tagger

The Builder does not create an ontology-ready `SourceUnit`. It creates a candidate that the Validator evaluates.

Validator decisions are:

- `ACCEPT`: candidate is atomic and sufficiently self-contained, including allowed source context;
- `SPLIT`: candidate contains multiple semantic assertions;
- `MERGE`: candidate is too small or depends on adjacent primary evidence;
- `REVIEW`: meaning or boundary is ambiguous;
- `REJECT`: content is outside the ontology ingestion scope.

Example:

```text
The system locks the account and sends an email to the user.
```

The Parser returns one paragraph block. The default Builder returns one candidate. Only the Validator may decide that it contains two independently testable behaviors and return `SPLIT`.

`3.1 Function Detail` remains a heading/section context before and after validation. It is not accepted or rejected as a SourceUnit because the Builder never submits it as a candidate.

The validated SourceUnit is the smallest source-backed evidence unit that can be interpreted independently within its referenced context and is suitable for ontology extraction. It is not required to map to only one ontology triple.

## 13. Cross-reference ownership

Cross-reference work is separated from terminology canonicalization:

1. The Parser preserves explicit link, anchor and identifier syntax with source spans.
2. A deterministic `ReferenceExtractor` emits references such as `REQ-123`, section anchors and document links.
3. A `ReferenceResolver` resolves those references against the document/unit registry after relevant targets exist.
4. `TerminologyCanonicalizer` canonicalizes domain terms only; it does not own document-link resolution.

Reference metadata never replaces primary evidence and unresolved references must remain auditable.

## 14. Identity and incremental ingestion

Do not use one ID for both exact evidence identity and cross-revision continuity.

### 14.1 Exact candidate revision identity

`candidate_revision_id` identifies the exact Builder output in one `DocumentRevision`. Generate it from canonical JSON:

```python
import hashlib
import json
import uuid

payload = {
    "document_revision_id": document_revision_id,
    "primary_spans": [span.model_dump(mode="json") for span in primary_spans],
    "primary_raw_text_hashes": primary_raw_text_hashes,
    "builder_profile_version": builder_profile_version,
}
canonical_name = json.dumps(
    payload,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
)
candidate_revision_id = f"SUC-{uuid.uuid5(NAMESPACE, canonical_name)}"
```

Requirements:

- unchanged registered revision plus unchanged profiles produces identical IDs;
- changing primary content, boundary, document revision or Builder profile changes the exact revision ID;
- ordered spans and hashes prevent ordinal-only identity;
- canonical JSON prevents ambiguity when headings or text contain characters such as `|` or `/`.

The final `source_unit_revision_id` is owned by the Validator/persistence contract because split and merge may change boundaries. It must retain lineage to the input candidate revision IDs.

### 14.2 Cross-revision continuity

Calculate a separate `continuity_fingerprint` from stable evidence features such as ordered primary raw-text hashes, block kinds and exact structural-context signatures. Do not include absolute line numbers or `document_revision_id`.

The fingerprint is a matching aid, not a unique key. Repeated paragraphs can have identical fingerprints. Cross-revision matching must combine it with sequence alignment, neighboring anchors, section context and explicit lineage.

When a line is inserted near the beginning of a file:

- affected block and candidate revision IDs may change because the document revision and coordinates changed;
- unchanged content can still be matched through continuity evidence;
- persistence may reuse validated/ontology outputs only after matching policy and profile compatibility checks pass.

## 15. Parser diagnostics and Markdown linting

CommonMark parsing and project diagnostics are separate concerns:

- `MarkdownParser` performs structural parsing and adapter invariant checks.
- `MarkdownDiagnostics` performs project-specific suspicious-syntax checks before and/or after parsing.

For example, an unclosed fenced code block may be accepted by CommonMark through the end of the document. Therefore `UNCLOSED_FENCE` requires a dedicated diagnostic rule; it cannot be assumed to come from the parser.

All stages use the shared `PipelineDiagnostic` contract defined with the Parser contracts. `stage` identifies the owner; `detector_version` makes each rule reproducible.

Required codes and expected owner:

| Code | Owner | Notes |
|---|---|---|
| `INVALID_UTF8` | Registration | Blocking document failure |
| `UNSUPPORTED_HTML` | MarkdownDiagnostics/Parser policy | Must prove no source silently disappeared |
| `UNCLOSED_FENCE` | MarkdownDiagnostics | Dedicated fence-balance policy |
| `MALFORMED_TABLE` | MarkdownDiagnostics | Project-specific suspicious table syntax |
| `BROKEN_LIST_NESTING` | MarkdownDiagnostics | Do not silently repair source hierarchy |
| `EMPTY_SECTION` | Post-parse diagnostics | Heading has no eligible content before the next peer section |
| `DUPLICATE_HEADING_ANCHOR` | Post-parse diagnostics | Duplicate titles are still preserved as distinct blocks |
| `HEADING_LEVEL_JUMP` | Post-parse diagnostics | Preserve the jump; do not invent nodes |
| `LINE_MAP_UNAVAILABLE` | Parser adapter | Blocking only for evidence-bearing block mappings |
| `CANDIDATE_HARD_LIMIT_EXCEEDED` | Builder | Structural fact; Validator owns the response |

Warnings that permit processing must be persisted and passed to validation. Blocking diagnostics stop only the affected document or candidate at the narrowest safe scope.

## 16. Error handling and observability

Persist or emit metrics for:

- parser and plugin versions;
- parser, diagnostics and Builder profile versions;
- document, block, candidate and diagnostic counts;
- count of blocks skipped by reason;
- count of candidates by structural profile;
- blocking and non-blocking diagnostics by code;
- parse/build duration;
- exact rerun ID stability;
- cross-revision continuity match rate and ambiguous-match rate.

Fail fast when:

- input cannot be decoded as UTF-8;
- normalized text hash does not match the registered revision;
- a required block span is invalid or cannot reproduce `raw_text`;
- a block reference, primary span or context reference points outside the same document revision;
- contract validation fails.

Do not continue with fabricated spans, reconstructed evidence or silently dropped blocks.

## 17. Acceptance tests

### 17.1 Golden fixtures

1. A one-line paragraph with a parser token map `[0, 1]` extracts exactly `lines[0:1]`.
2. LF, CRLF and CR inputs normalize deterministically; files with and without a final newline preserve that distinction in normalized evidence.
3. UTF-8 BOM, Vietnamese and Japanese text preserve exact characters and produce both required hashes.
4. Nested headings produce correct parent IDs and heading-context paths.
5. `3.1 Function Detail` separates section number, raw title and Markdown heading level without becoming a candidate.
6. Repeated and duplicate headings remain distinct; heading-level jumps generate diagnostics without invented headings.
7. Nested ordered/unordered lists retain container, item, parent and ordering metadata.
8. List `ITEM` and `GROUP` profiles never create overlapping primary evidence or duplicate candidates.
9. Lead-in paragraphs and dependent list items are linked structurally; no semantic completeness decision appears in Builder output.
10. Tables with escaped pipes, alignment rows and repeated header text preserve exact row evidence and header context.
11. Row-mode tables never emit isolated cells; whole-table mode produces one non-overlapping candidate.
12. An unclosed fence is structurally parsed according to CommonMark behavior and independently flagged by `MarkdownDiagnostics`.
13. Inline and closing tokens without maps do not cause false `LINE_MAP_UNAVAILABLE`; an unmappable evidence-bearing block does.
14. Every candidate can reconstruct all primary evidence exactly from ordered `primary_spans`.
15. Context retrieval reproduces heading/table/list context without modifying primary evidence.
16. Unchanged reruns produce identical blocks, diagnostics, candidates and exact revision IDs.
17. Inserting a line before unchanged content creates a new document revision while continuity matching can identify the unchanged evidence.
18. Repeated identical paragraphs receive distinct exact revision identities where boundaries differ; continuity fingerprints are never assumed unique.
19. Changing `BuilderProfile` changes affected candidate revision IDs and invalidates incompatible cached results.
20. Parser output contains no requirement type, ontology tag, atomicity, testability or validation decision.
21. Builder output contains no `ACCEPT`, `SPLIT`, `MERGE`, `REVIEW`, `REJECT` or rewritten requirement text.
22. Malformed Markdown produces explicit diagnostics and never silent evidence loss.

### 17.2 Property-based invariants

For generated documents and supported Markdown structures, verify:

- every block span is in bounds and non-empty;
- `block.raw_text` equals the normalized-source slice for `block.source_span`;
- `raw_text_hash` equals the hash of that exact slice;
- every primary/context block ID exists in the same `ParseResult`;
- primary spans are ordered and non-overlapping;
- no primary block is represented by more than one candidate in one profile execution;
- every non-primary block is either referenced as context or recorded in `skipped_blocks` when the profile requires accounting;
- canonical serialization produces stable IDs independent of dictionary insertion order;
- validation rejects unexpected fields and mutable shared defaults cannot occur.

## 18. Definition of done

This specification is coding-ready when:

- the contracts above exist as executable Pydantic models;
- Parser and Builder implementations depend only on their declared contracts;
- golden fixtures and property-based invariants pass;
- source-coordinate, normalization and hashing policies are used consistently by persistence;
- diagnostics demonstrate that malformed syntax never causes silent evidence loss;
- exact revision identity and continuity matching are implemented as separate mechanisms;
- the Validator can consume `BuildResult` through the declared `ParsedBlock`/context lookup contract without accessing `markdown-it-py` tokens or guessing candidate structure.

Implementation references:

- `markdown-it-py` usage and token maps: <https://markdown-it-py.readthedocs.io/en/latest/using.html>
- CommonMark specification: <https://spec.commonmark.org/current/>
