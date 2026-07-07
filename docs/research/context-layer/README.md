# Context Layer Research

## Purpose

This folder stores implementation-oriented research for the BD Harness Context Layer.

The goal is to separate general reading material from project-specific technical evaluation, benchmarks, architecture decisions, and adoption notes.

## Decision

Use two repositories for two different types of knowledge:

1. **AI Project Opus**
   - Stores the general AI / Harness reading list.
   - Intended for long-term learning material, papers, frameworks, architecture patterns, and broad technology references.
   - File example: `docs/ai-harness-reading-list.md`.

2. **BD Chunk Project**
   - Stores implementation-oriented research for the BD Harness.
   - Intended for benchmark notes, adoption decisions, architecture notes, ADRs, integration plans, and proof-of-concept findings.
   - Folder example: `docs/research/context-layer/`.

## Classification Rules

| Material Type | Destination |
|---|---|
| General reading / survey / paper | AI Project Opus reading list |
| Framework worth studying broadly | AI Project Opus reading list |
| Tool evaluation for BD Harness | BD Chunk Project research folder |
| Benchmark / POC result | BD Chunk Project research folder |
| Architecture decision | BD Chunk Project research folder |
| Final implementation design | BD Chunk Project research folder |
| Material that is both general and implementable | Short entry in Opus + detailed research note in BD Chunk |

## Current Research Scope

The initial scope of this folder is the Harness Context Layer:

- codebase-memory-mcp
- Microsoft GraphRAG
- Neo4j and alternatives
- Kuzu
- TypeDB
- Memgraph
- ArangoDB
- OpenWiki
- CodeGraph
- Context Orchestrator design

## Planned Files

- `codebase-memory-mcp.md`
- `graphrag.md`
- `neo4j-vs-alternatives.md`
- `openwiki.md`
- `codegraph.md`
- `context-harness-architecture.md`
- `adr-context-layer-classification.md`

## Related Harness Implementation Layers

Adjacent implementation notes are stored outside this folder:

- L2 Runtime / Orchestration: `docs/research/runtime-layer/`
- L6 AgentOps / Observability: `docs/research/agentops-layer/`

## Operating Rule

When a new repo, article, or framework is reviewed:

- If it is mainly learning material, add it to the Opus reading list.
- If it affects BD Harness implementation, add a research note in the correct Harness layer folder.
- If it is both, create both records: a short reading-list entry in Opus and a detailed implementation note in BD Chunk.
