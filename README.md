# BD Harness Project

This repository is the working skeleton for a **BD-focused Super Agent Harness**.

The first production use case is not a generic chatbot. It is a governed pipeline that converts Japanese requirement sources into traceable requirement chunks, maps approved requirement items to Basic Design frames, and generates reviewable Japanese BD patches with citations.

```text
Raw RD / QA / Meeting Notes / Legacy References
  -> File Registry
  -> Deterministic Parsing
  -> Traceable Source Units
  -> Traceable Chunks
  -> Ontology Labeling
  -> Requirement Knowledge Base
  -> BD Mapping
  -> BD Patch
  -> Human Review
  -> Excel / Client Delivery Pack
```

## Harness positioning

The Harness separates orchestration, agent roles, skills, tools, ontology, data, and BD output generation.

```text
harness/
  registry/       agent, skill, and tool profile definitions
  workflows/      executable workflow specifications
  policies/       governance and guardrail policies

ontology/         controlled labels, requirement types, BD frames, mapping rules
src/bd_chunk/     deterministic Python pipeline implementation
data/             raw input, normalized output, and indexes
docs/             methodology, architecture, glossary
tests/            validation tests and quality gates
```

## Core design principles

1. **No raw file goes directly into the RKB.** Every raw input must pass through registry, parser, traceability validation, chunking, ontology labeling, and eligibility gates.
2. **LLMs must not invent provenance.** Workbook, sheet, cell range, document section, RKB ID, and BD frame ID are deterministic system outputs, not model guesses.
3. **Rules first, model second.** Mapping starts from controlled ontology rules. LLM fallback is allowed only for ambiguous cases and must be human-reviewed.
4. **Human gate before BD output.** Pending decisions, conflicts, and low-confidence mappings must be blocked before BD patch generation.
5. **File-based MVP first.** The MVP should run with JSONL/YAML/Markdown files before adding cloud DB, vector DB, or complex GraphRAG.

## MVP modules

| Layer | Responsibility | Main artifacts |
|---|---|---|
| File registry | Hash raw files and assign source kind | `file_registry.jsonl` |
| Parser | Parse Excel / Markdown / Word-like sources | `source_units.jsonl` |
| Chunking | Normalize source units into traceable chunks | `traceable_chunks.jsonl` |
| Ontology | Apply controlled source and requirement labels | `rkb_candidates.jsonl` |
| Review gate | Promote only approved candidates | `rkb_items.jsonl` |
| Index | Build metadata + BM25 + semantic-ready index | `data/index/*` |
| BD mapping | Map RKB items to BD frames | `bd_mapping.jsonl` |
| BD generation | Generate Japanese BD patch with citations | `bd_patch_ja.md` |

## Planned CLI

```bash
bdchunk register --path data/raw/qa_keshikomi.xlsx --source-kind QA
bdchunk parse-excel --path data/raw/qa_keshikomi.xlsx --sheet QA票 --range B12:E30 --out data/outputs/source_units.jsonl
bdchunk build-chunks --source-units data/outputs/source_units.jsonl --out data/outputs/traceable_chunks.jsonl
bdchunk validate-chunks --chunks data/outputs/traceable_chunks.jsonl
bdchunk label-ontology --chunks data/outputs/traceable_chunks.jsonl --ontology ontology/ --out data/outputs/rkb_candidates.jsonl
bdchunk promote-rkb --candidates data/outputs/rkb_candidates.jsonl --out data/outputs/rkb_items.jsonl
bdchunk build-bm25 --rkb data/outputs/rkb_items.jsonl --out data/index/keyword_index.jsonl
bdchunk map-bd --rkb data/outputs/rkb_items.jsonl --ontology ontology/ --out data/outputs/bd_mapping.jsonl
bdchunk generate-bd-patch --rkb data/outputs/rkb_items.jsonl --mapping data/outputs/bd_mapping.jsonl --out data/outputs/bd_patch_ja.md
```

## Acceptance criteria

- A sample Excel range can be parsed into deterministic `source_units.jsonl`.
- Every chunk keeps source trace: workbook/document, hash, sheet/section, range/paragraph, and source granularity.
- Ambiguous terms such as `別途確認`, `未定`, `必要に応じて`, `適切に`, and `原則として` are marked for review.
- Pending, conflict, or low-confidence items are blocked from BD patch generation.
- BD mapping uses controlled `ontology/mapping_rules.yaml` before any model fallback.
- Generated Japanese BD patches include citations back to source units.

## What this MVP intentionally excludes

```text
- Full GraphRAG
- Complex graph database
- LLM-only mapping
- Automatic final BD generation without human review
- Vector DB as a hard requirement
- Direct production database access from sandbox runtime
```
