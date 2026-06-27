# BD Chunk Project

MVP repo for a **Traceable Requirement Knowledge Index** pipeline.

This project is not a generic RAG chatbot. It converts raw requirement sources into a traceable Requirement Knowledge Base, then maps approved requirement items into Basic Design frames.

```text
Raw RD / QA / Legacy files
→ Traceable Source Pool
→ Hybrid Index
→ Ontology Labeling
→ Requirement Knowledge Base
→ BD Mapping
→ BD Patch
```

## Core objective

Build a Python MVP that can:

1. Register raw files and compute file hash.
2. Parse Excel / Markdown / Word-like requirement sources into source units.
3. Preserve deterministic provenance for every chunk.
4. Build traceable chunks.
5. Apply controlled ontology labels.
6. Store normalized items in a Requirement Knowledge Base.
7. Search with metadata + BM25 + semantic-ready index.
8. Map RKB items to BD frames using rules first.
9. Generate Japanese BD patch with source citations.

## Key principle

Raw files must never go directly into the Requirement Knowledge Base.

Every item must pass through:

```text
raw file
→ file registry
→ parser
→ traceable source unit
→ validated chunk
→ ontology labeling
→ RKB item
```

For Excel, every parsed chunk must keep:

```text
workbook_name
workbook_sha256
sheet_name
range_a1
source_granularity = row_range or block_range
```

Source range must come from deterministic parsing, for example `openpyxl`. LLMs must not infer workbook, sheet, range, RKB ID, or BD frame ID.

## Important concepts

| Concept | Meaning | Role |
|---|---|---|
| Indexing | Lookup structure | Find data fast and reliably |
| Vector | Numeric representation of text meaning | Semantic similarity |
| Semantic indexing | Vector-based meaning search | Find related chunks despite wording differences |
| BM25 | Keyword ranking | Find exact field/status/code terms |
| Ontology | Controlled semantic model | Understand chunk type, relation, BD target |
| Hybrid search | Metadata + BM25 + vector | Best retrieval layer for BD mapping |

BM25 retrieves candidate chunks. BM25 must not decide BD mapping by itself. BD mapping should be controlled by ontology rules, validators, and human/LLM fallback only for ambiguous cases.

## Ontology MVP

Source labels:

```text
RD_FACT
QA_CLARIFICATION
QA_ADDITION
PENDING_DECISION
LEGACY_REFERENCE
TECHNICAL_INFERENCE
```

Requirement types:

```text
BUSINESS_RULE
VALIDATION_RULE
SCREEN_BEHAVIOR
API_BEHAVIOR
BATCH_PROCESS
EXCEPTION_RULE
STATE_TRANSITION
DATA_ITEM
AUTHORIZATION_RULE
NON_FUNCTIONAL_REQUIREMENT
INTERFACE_RULE
```

BD frames:

```text
BD-SCREEN-001        画面仕様
BD-API-001           API仕様
BD-RULE-001          業務ルール
BD-VALIDATION-001    入力チェック
BD-EXCEPTION-001     例外処理
BD-STATUS-001        ステータス遷移
BD-BATCH-001         バッチ処理
BD-IF-001            外部IF
BD-DB-001            DB設計
```

Default mapping rules:

```text
BUSINESS_RULE      → BD-RULE-001
VALIDATION_RULE    → BD-VALIDATION-001
EXCEPTION_RULE     → BD-EXCEPTION-001
STATE_TRANSITION   → BD-STATUS-001
SCREEN_BEHAVIOR    → BD-SCREEN-001
API_BEHAVIOR       → BD-API-001
BATCH_PROCESS      → BD-BATCH-001
```

## Proposed repository structure

```text
bd-chunk-project/
  README.md
  pyproject.toml
  .gitignore

  docs/
    methodology.md
    glossary.md
    architecture.md

  ontology/
    source_labels.yaml
    requirement_types.yaml
    ears_types.yaml
    bd_frames.yaml
    mapping_rules.yaml

  data/
    raw/.gitkeep
    outputs/.gitkeep
    index/.gitkeep

  src/bd_chunk/
    __init__.py
    config.py
    ingest/
    chunking/
    ontology/
    index/
    rkb/
    bd/
    cli.py

  tests/
    test_excel_parser.py
    test_traceability_validator.py
    test_ontology_rules.py
    test_bd_mapping.py
```

## Recommended Python stack

```text
Python 3.11+
openpyxl
pydantic
typer
pyyaml
rich
pytest
ruff
mypy
rank-bm25 optional
```

MVP should not require a vector DB. Phase 1 can create a semantic index manifest with `embedding_status = not_generated`.

## CLI target

```text
bdchunk register --path data/raw/qa_keshikomi.xlsx --source-kind QA
bdchunk parse-excel --path data/raw/qa_keshikomi.xlsx --sheet QA票 --range B12:E30 --out data/outputs/source_units.jsonl
bdchunk build-chunks --source-units data/outputs/source_units.jsonl --out data/outputs/traceable_chunks.jsonl
bdchunk validate-chunks --chunks data/outputs/traceable_chunks.jsonl
bdchunk label-ontology --chunks data/outputs/traceable_chunks.jsonl --ontology ontology/ --out data/outputs/rkb_items.jsonl
bdchunk build-bm25 --rkb data/outputs/rkb_items.jsonl --out data/index/keyword_index.jsonl
bdchunk search --query "金額 不一致 手動確認" --rkb data/outputs/rkb_items.jsonl
bdchunk map-bd --rkb data/outputs/rkb_items.jsonl --ontology ontology/ --out data/outputs/bd_mapping.jsonl
bdchunk generate-bd-patch --rkb data/outputs/rkb_items.jsonl --mapping data/outputs/bd_mapping.jsonl --out data/outputs/bd_patch_ja.md
```

## Quality gates

Raw registry gate:

```text
file_id exists
file hash exists
file type detected
source kind assigned
```

Source traceability gate:

```text
Excel unit has workbook / sheet / range
Word or Markdown unit has document / section / paragraph or line reference
raw_text is not empty
```

RKB eligibility gate:

```text
not PENDING_DECISION as fact
not TECHNICAL_INFERENCE as approved
no unresolved conflict_flag
requirement_statement_ja exists
```

BD mapping gate:

```text
target_frame_id exists in bd_frames.yaml
rkb_id exists
source trace exists
status allows generation
mapping_confidence is not low
```

## Acceptance criteria

- Tests pass.
- A sample Excel row can be parsed into `source_units.jsonl`.
- Source units can be converted into `traceable_chunks.jsonl`.
- Traceable chunks can become `rkb_items.jsonl` with ontology labels.
- BM25 search can retrieve relevant RKB items.
- BD mapper maps rule-based labels to BD frames.
- BD patch writer outputs Japanese markdown with source citations.

## What not to build in MVP

```text
full GraphRAG
complex knowledge graph DB
cell-level trace for every field
LLM-only mapping
automatic final BD generation without human gate
vector DB as a hard requirement
```

## Architecture sentence

This project implements a **Provenance-Aware Hierarchical Hybrid Index for Requirements**: raw source files are fingerprinted, parsed into traceable chunks, labeled with controlled ontology, indexed with metadata/BM25/semantic-ready structures, stored in a Requirement Knowledge Base, and mapped into Basic Design frames through rule-based mapping with validator gates.
