# Parser and SourceUnit builder specification

## Objective

Convert Markdown RD files into deterministic structural blocks and then into stable, meaningful `SourceUnit` records. This stage preserves evidence; it does not interpret requirement semantics.

## Parser implementation

Use `markdown-it-py` with an explicitly configured Markdown profile. Pin the parser and plugin versions.

```python
from markdown_it import MarkdownIt

md = (
    MarkdownIt("commonmark", {"html": False})
    .enable("table")
)
tokens = md.parse(text)
```

Configuration requirements:

- HTML must be disabled or sanitized according to repository policy.
- Table support must be explicitly enabled and tested.
- Source line maps from tokens must be retained.
- The parser must not silently recover malformed structures without recording a warning.
- Input encoding is UTF-8; invalid encoding is a document-level failure.

## ParsedBlock contract

The parser adapter converts library tokens into a stable internal model so later stages are not coupled to `markdown-it-py` internals.

```python
class ParsedBlock(BaseModel):
    block_id: str
    block_type: str
    raw_text: str
    line_start: int
    line_end: int
    heading_path: list[str]
    ordinal: int
    attributes: dict = {}
```

The adapter must produce blocks for:

- heading;
- paragraph;
- list item and list group;
- table with header and rows;
- blockquote;
- fenced code block;
- horizontal rule where it has section significance.

## Raw text extraction

Use line ranges against the original input text rather than reconstructing Markdown from parsed tokens. This prevents formatting loss.

```python
lines = original_text.splitlines(keepends=True)
raw_text = "".join(lines[line_start - 1:line_end])
```

Define and document newline normalization. Recommended policy:

- normalize CRLF and CR to LF at document registration;
- calculate line ranges and hashes after normalization;
- retain the original file hash separately if byte-level audit is needed.

## Heading context

Maintain a heading stack while walking blocks.

```text
# Campaign Management
## Lead Scoring
### Click Events
```

Produces:

```json
["Campaign Management", "Lead Scoring", "Click Events"]
```

Heading text is metadata. It is not prepended to `raw_text`, but may be supplied as separate context to validation or ontology tagging.

## SourceUnitBuilder rules

### Paragraphs

- A normal paragraph becomes one candidate SourceUnit.
- Do not split only because it exceeds a preferred embedding size.
- If above hard limits, emit candidate status `SPLIT_REQUIRED` for validator/repair handling.

### Lists

- Preserve the list container and ordering metadata.
- An item becomes a separate unit when it expresses an independently testable assertion.
- A lead-in sentence plus dependent list items may be grouped as one unit when each item is grammatically incomplete without the lead-in.
- Nested list items retain parent item IDs.

### Tables

- Never emit isolated cells without their header context.
- For row-oriented requirement tables, create one SourceUnit per logical row with table title and column headers as metadata/context.
- For matrix tables, preserve the whole table unless a deterministic table profile is configured.
- Store `table_id`, row index and column names in attributes.

### Blockquotes and notes

- Preserve as separate units when they contain requirement-relevant content.
- Mark note/warning style when syntax makes it deterministic.

### Code and examples

- Keep code fences separate from requirement prose.
- Mark as `code_block` or `example` only when deterministically identifiable.
- Do not ontology-tag code blocks by default.

### Cross-references

Extract explicit references such as `REQ-123`, section anchors and document links as deterministic metadata only. Resolution happens in canonicalization.

## Stable ID generation

```python
import uuid

NAMESPACE = uuid.UUID("...")
name = "|".join([
    workspace_id,
    document_id,
    "/".join(heading_path),
    str(line_start),
    str(line_end),
    raw_text_hash,
])
source_unit_id = f"SU-{uuid.uuid5(NAMESPACE, name)}"
```

Requirements:

- IDs are stable for unchanged source.
- IDs change when source content or source boundary changes.
- Parent/child lineage links old and repaired units.
- Do not derive IDs from ordinal alone.

## Parser warnings

Emit structured warnings:

```text
UNSUPPORTED_HTML
UNCLOSED_FENCE
MALFORMED_TABLE
BROKEN_LIST_NESTING
EMPTY_SECTION
DUPLICATE_HEADING_ANCHOR
LINE_MAP_UNAVAILABLE
```

A warning may allow processing to continue, but it must be persisted and considered by validation.

## Acceptance tests

1. Heading paths are correct for nested sections.
2. Raw text matches normalized source lines exactly.
3. Repeated identical paragraphs receive different IDs when locations differ.
4. Tables retain header context.
5. List items preserve ordering and nesting.
6. Unchanged reruns produce identical blocks and SourceUnit IDs.
7. Malformed Markdown generates explicit warnings rather than silent data loss.
8. No semantic or design annotation appears in parser output.