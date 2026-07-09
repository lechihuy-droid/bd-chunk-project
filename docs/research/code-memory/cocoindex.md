# CocoIndex

> ⚠️ Work In Progress
>
> Version: 0.1 Draft
> Status: Research document, not final adoption record
> Last updated: 2026-07-09
> Recommendation: Pilot for Context Indexing / Freshness layer
> Confidence: Medium-High

## Source Verification

| Source | Status | Notes |
|---|---|---|
| Official repository | Checked | https://github.com/cocoindex-io/cocoindex |
| Official website | Checked | https://cocoindex.io/ |
| Source code | Not fully reviewed | Needs follow-up before final adoption. |
| Independent benchmark | Not checked | Current claims are official-project claims. |

## 1. Executive Summary

CocoIndex is an incremental data framework for AI agents and LLM applications. It is designed to turn codebases, meeting notes, inboxes, Slack, PDFs, videos, and other source data into continuously fresh context with minimal delta-only reprocessing.

For the BD / Enterprise Harness project, CocoIndex should not be treated as a replacement for Codebase-Memory MCP, CodeGraph, RKB, Graph DB, Vector DB, or Obsidian. It should be evaluated as a **Context Indexing and Freshness Engine** that keeps derived context stores synchronized when raw sources or transformation code change.

Recommended positioning:

```text
Raw Sources
  -> File Registry
  -> Deterministic Parsing / Source Units
  -> Traceable Chunks
  -> CocoIndex Incremental Engine
      -> BM25 Index
      -> Vector Index
      -> Graph Index
      -> Code Memory Index
  -> Context Selector
  -> Agent / BD Workflow
```

## 2. Problem Statement

A Harness becomes unreliable when its context is stale. Requirement documents change, QA files are updated, source code moves, API definitions are modified, and meeting notes add new decisions. If the system only runs batch indexing, agents may reason over old context.

The current BD Harness design already prioritizes deterministic source units, traceable chunks, RKB promotion, and controlled mapping. The missing part is an incremental engine that can answer:

- Which source changed?
- Which chunks are affected?
- Which embeddings or graph edges need recomputation?
- Which target stores are stale?
- Which agent memories should be refreshed?

CocoIndex is relevant because it targets exactly this freshness and delta-processing problem.

## 3. Architecture Overview

Effective architecture:

```text
Sources
  -> Python-native transformation flow
  -> Incremental engine
  -> Lineage / cache / version tracking
  -> Target stores
      -> Relational DB
      -> Vector DB
      -> Graph DB
      -> Message Queue
      -> Feature Store
  -> Agents / LLM apps
```

Harness interpretation:

```text
Business Memory      Requirement, QA, meeting notes
Architecture Memory  BD docs, API, DB, ADR, diagrams
Code Memory          codebase-memory-mcp / CodeGraph
Freshness Engine     CocoIndex
Runtime Memory       CI, logs, test results, metrics
```

CocoIndex is not the memory itself. It is the mechanism that keeps memory and indexes fresh.

## 4. Core Capabilities

### 4.1 Incremental Processing

Source-backed fact:

The official README positions CocoIndex around fresh context and delta-only incremental processing. It says CocoIndex turns codebases, meeting notes, inboxes, Slack, PDFs, and videos into live context for AI agents, and that re-runs only reprocess changed files or affected outputs.

Analysis:

This is the key distinction from simple RAG or manual batch indexing. A changed source should not force full re-indexing of all project data.

Harness evaluation: Very high.

BD projects are document-heavy and change-heavy. Incremental recomputation protects the harness from stale context without making every update expensive.

### 4.2 Declarative Python Dataflow

Source-backed fact:

The README presents Python-native transformation flows, where the developer declares what target state should contain and CocoIndex keeps it synchronized.

Analysis:

This fits the BD Harness because the current design already uses deterministic pipelines: file registry, source units, traceable chunks, ontology labeling, RKB, and BD mapping.

Harness evaluation: High.

CocoIndex can become the control plane for derived indexes, while deterministic parsers and ontology rules remain project-owned.

### 4.3 Lineage and Explainability

Source-backed fact:

The official README emphasizes lineage from source bytes to target rows/vectors/graph nodes.

Analysis:

This aligns strongly with the BD Harness rule that every generated statement must trace back to source metadata.

Harness evaluation: Very high.

For client-facing Japanese BD output, provenance is more important than retrieval convenience. CocoIndex should only be adopted if lineage can be connected to workbook/sheet/row-cell and chunk IDs.

### 4.4 Multi-target Indexing

Source-backed fact:

The official materials show targets such as relational DB, vector DB, graph DB, message queue, and feature store.

Analysis:

This is useful because the Harness should not rely on one retrieval backend. Requirement lookup, semantic search, traceability graph, and code memory all need different stores.

Harness evaluation: High.

CocoIndex should feed target indexes, not replace them.

## 5. Comparison: CocoIndex vs codebase-memory-mcp

| Dimension | CocoIndex | codebase-memory-mcp |
|---|---|---|
| Primary role | Context indexing / freshness engine | Code memory / structural code graph engine |
| Main problem | Keep derived context stores fresh as sources change | Avoid repeated grep/file-read exploration by querying code facts |
| Source scope | Codebases, docs, Slack, PDFs, meeting notes, inboxes, videos | Source code repositories |
| Output | Updated target stores: relational, vector, graph, etc. | Persistent code knowledge graph exposed through MCP |
| Retrieval style | Depends on configured target stores | MCP tools for code symbols, calls, routes, architecture, impact |
| Memory type | Memory maintenance layer | Memory query layer |
| BD Harness fit | Freshness and lineage across all context | Code understanding for coding/review agents |
| Replace each other? | No | No |

Recommended combined model:

```text
CocoIndex
  keeps indexes fresh

codebase-memory-mcp / CodeGraph
  provide code-specific memory and query tools

Graph DB / Vector DB / BM25
  store searchable context

Context Selector
  chooses what the agent receives
```

## 6. View from Harness Memory Layer

The Harness memory layer should not be a single database. It should be a controlled stack:

```text
Memory Layer
  ├── Business Memory
  │   └── RKB, QA, RD, meeting notes
  ├── Architecture Memory
  │   └── BD docs, API specs, DB specs, ADRs
  ├── Code Memory
  │   └── codebase-memory-mcp, CodeGraph, repo-level dependency graph
  ├── Runtime Memory
  │   └── CI, logs, test results, metrics
  └── Freshness / Indexing Control
      └── CocoIndex
```

In this model:

- Codebase-Memory MCP is a code memory provider.
- CodeGraph is a code structure provider.
- CocoIndex is the freshness/indexing control plane.
- Vector DB is a semantic retrieval backend.
- Graph DB is the traceability backend.
- RKB remains the source of truth for BD requirement interpretation.

## 7. Adoption Recommendation

Current decision: Pilot.

Adopt CocoIndex only if a pilot confirms:

- source-to-chunk lineage can preserve BD source metadata
- incremental updates correctly refresh affected chunks and indexes
- vector and graph targets can be updated without losing traceability
- local or enterprise deployment is acceptable
- it integrates cleanly with future Code Memory tools such as codebase-memory-mcp or CodeGraph

## 8. Recommended Pilot

Use a small BD sample:

1. RD Excel file
2. QA Excel file
3. Meeting note markdown file
4. Small API/code repository

Pipeline:

```text
Source files
  -> deterministic parser
  -> traceable_chunks.jsonl
  -> CocoIndex incremental flow
  -> BM25 / vector / graph targets
  -> Context Selector
```

Test cases:

1. Modify one QA row and verify only affected chunks and indexes refresh.
2. Modify parser code and verify affected outputs recompute.
3. Update one API file and verify Code Memory remains aligned with context indexes.
4. Generate a Japanese BD patch and confirm every statement retains source citation.

## 9. Decision Record

CocoIndex should be added to the same research group as Codebase-Memory MCP and CodeGraph because all three support the Harness context / memory layer.

However, its role is different:

```text
CocoIndex = freshness and incremental indexing
Codebase-Memory MCP = persistent code memory via MCP
CodeGraph = code structure and dependency intelligence
```

Recommended folder: `docs/research/code-memory/`

Recommended future category rename:

```text
code-memory/ -> context-memory/
```

or split later:

```text
context-layer/
  ├── indexing/
  ├── code-memory/
  └── retrieval/
```

## 10. References

Official:

- CocoIndex repository: https://github.com/cocoindex-io/cocoindex
- CocoIndex website: https://cocoindex.io/
