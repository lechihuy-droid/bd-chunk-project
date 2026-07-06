# codebase-memory-mcp

> ⚠️ Work In Progress
>
> Version: 0.1 Draft
> Status: Research document, not final adoption record
> Last updated: 2026-07-06
> Recommendation: Pilot → likely Adopt for Code Memory layer
> Confidence: Medium-High

## Source Verification

| Source | Status | Notes |
|---|---|---|
| Official repository | Checked | https://github.com/DeusData/codebase-memory-mcp |
| Official README | Checked | README describes architecture, install, features, performance, local security, MCP support. |
| Paper | Checked | https://arxiv.org/abs/2603.27277 |
| Source code | Not fully reviewed | Needs follow-up before final adoption. |
| Independent benchmark | Not checked | Current benchmark numbers are vendor/paper-reported. |

## 1. Executive Summary

`codebase-memory-mcp` is a local MCP server and code intelligence engine that indexes a repository into a persistent code knowledge graph. It is designed to reduce repeated `grep` / file-read exploration by letting an AI coding agent query structural code facts: symbols, calls, dependencies, routes, cross-service links, and change impact.

The official README describes it as a pure C, zero-dependency, single static binary for macOS, Linux, and Windows. It claims support for 158 languages through vendored Tree-sitter grammars, Hybrid LSP semantic type resolution for 10+ major language families, 14 MCP tools, local-only processing, SQLite-backed persistence, and optional 3D graph visualization at `localhost:9749`.

The accompanying arXiv paper reports that Codebase-Memory constructs a persistent Tree-sitter-based knowledge graph via MCP and, across 31 real-world repositories, achieves 83% answer quality versus 92% for file-by-file exploration, while using 10x fewer tokens and 2.1x fewer tool calls.

For the BD / Enterprise Harness project, this is not a replacement for Requirement KB, Obsidian, GraphRAG, or architecture documents. It should be evaluated as a **Code Memory Engine** that sits between source repositories and coding/review agents.

## 2. Problem Statement

AI coding agents often explore codebases by repeatedly calling search tools, opening files, reading large snippets, then searching again. This is expensive in token usage and fragile in large repositories because the agent rebuilds context for every task.

The paper frames this as a structural understanding problem: LLM coding agents consume thousands of tokens per query through repeated file-reading and grep-searching, without retaining a persistent structural model of the repository.

For a Harness, this problem becomes larger because multiple agents may need the same code facts:

- Coding Agent: where should a change be made?
- Review Agent: what is the blast radius?
- Test Agent: what tests should be affected?
- Architecture Agent: which services or packages are connected?

Without Code Memory, every agent repeats discovery work.

## 3. Architecture Overview

The effective architecture can be summarized as:

```text
Source Repository
  -> Language Detection
  -> Tree-sitter Parsing
  -> Semantic Extraction
  -> Knowledge Graph
  -> SQLite-backed Persistence
  -> MCP Tools / CLI
  -> Claude Code / Cursor / Codex / Gemini / Other Agents
```

Official README facts:

- The project uses Tree-sitter AST analysis across 158 languages.
- The binary includes vendored grammars.
- It stores a persistent graph locally, with SQLite-backed storage under the user's cache directory.
- It exposes 14 MCP tools.
- It can be installed into multiple coding agents automatically.
- It has optional graph visualization UI.

Technical interpretation:

This architecture is closer to a local static-analysis backend than to ordinary RAG. It indexes code into entities and relationships first, then exposes graph-aware operations to agents.

Harness interpretation:

This should be treated as a specialized memory subsystem:

```text
Business Memory      Requirement, QA, meeting notes
Architecture Memory  BD docs, API, DB, ADR, diagrams
Code Memory          codebase-memory-mcp
Runtime Memory       CI, logs, test results, metrics
```

## 4. Core Capabilities

### 4.1 Persistent Code Knowledge Graph

Source-backed fact:

The README states that the tool produces a persistent knowledge graph of functions, classes, call chains, HTTP routes, and cross-service links. It also describes SQLite-backed persistence and a team-shared graph artifact `.codebase-memory/graph.db.zst`.

Analysis:

Persistence is the key difference from grep/search. A one-time index becomes reusable memory. Multiple agent sessions can query the same structural representation instead of rediscovering code relationships.

Harness evaluation: High.

This is directly useful once the Harness has real code repositories. It is less useful during the early pure-BD/document-only phase.

### 4.2 Tree-sitter Multi-language Parsing

Source-backed fact:

The README claims 158 vendored Tree-sitter grammars compiled into the binary. The paper also identifies Tree-sitter as the basis for the knowledge graph construction.

Analysis:

Tree-sitter is appropriate for code intelligence because it can parse source code even before it fully compiles, and it supports many languages. For enterprise migration projects, repositories often contain mixed languages and partially broken code during refactoring.

Harness evaluation: High.

A BD-to-code Harness should not assume a single language. Multi-language parsing is required if the target includes legacy WinForms, web frontend, backend services, scripts, IaC, and database-related code.

### 4.3 Hybrid LSP Semantic Type Resolution

Source-backed fact:

The README claims Hybrid LSP semantic type resolution for Python, TypeScript / JavaScript / JSX / TSX, PHP, C#, Go, C, C++, Java, Kotlin, and Rust. It describes this as a lightweight C implementation of language type-resolution algorithms structurally inspired by major language servers such as tsserver, pyright, gopls, Roslyn, Eclipse JDT, and rust-analyzer.

Analysis:

Tree-sitter alone provides syntax. Semantic type resolution tries to answer harder questions: which implementation is actually called, what type a symbol has, how generic substitution or JSX dispatch resolves, and how cross-file calls connect.

Harness evaluation: Very high.

If reliable, this is crucial for impact analysis and review automation. However, this part should be validated against source code and real repositories before final adoption.

### 4.4 Graph and Architecture Tools

Source-backed fact:

The README lists `get_architecture`, `manage_adr`, Louvain community detection, `detect_changes`, call graph, dead code detection, and Cypher-like queries. It says `get_architecture` returns languages, packages, entry points, routes, hotspots, boundaries, layers, and clusters.

Analysis:

These features move the tool beyond symbol lookup. They suggest a codebase-level architecture summarization capability. `manage_adr` is especially relevant because it stores architectural decisions across sessions.

Harness evaluation: High.

This can support Architecture Review Agent and Change Impact Agent. But architecture output from code should be treated as derived evidence, not as the source of business truth.

### 4.5 Search Capabilities

Source-backed fact:

The README lists semantic search, BM25 full-text search via SQLite FTS5, structural search through `search_graph`, and graph-augmented grep through `search_code`.

Analysis:

The tool combines several retrieval modes:

- exact/code text search
- full-text search
- structural graph search
- semantic search

This hybrid retrieval model is stronger than using only vector search or only grep.

Harness evaluation: High.

A Harness orchestrator could route questions by type:

- Business meaning → Requirement KB / RAG
- Symbol/call/dependency → Code Memory
- Mixed design-code traceability → future cross-layer graph

### 4.6 Cross-service and Cross-repo Intelligence

Source-backed fact:

The README lists HTTP route ↔ call-site matching, gRPC, GraphQL, tRPC service detection, channel detection for Socket.IO/EventEmitter/pub-sub patterns, `CROSS_*` edges across multiple repos, and cross-repo architecture summaries.

Analysis:

This is one of the most important enterprise features. Many production systems are not one repository or one process. They are microservices connected by REST, GraphQL, events, and messaging.

Harness evaluation: Very high.

For enterprise modernization, cross-repo and cross-service analysis is more valuable than single-file assistance. This should be tested with a realistic multi-repo sample before adoption.

### 4.7 Team-shared Graph Artifact

Source-backed fact:

The README describes `.codebase-memory/graph.db.zst` as a zstd-compressed SQLite graph snapshot. It claims typical 8-13:1 compression and says teammates can skip a full reindex by importing the artifact.

Analysis:

This makes Code Memory portable across a team. It also introduces governance questions: whether to commit graph artifacts, how to handle merge conflicts, and whether the graph contains sensitive derived information.

Harness evaluation: Medium-High.

Useful for team productivity, but needs security and repository policy review.

## 5. Performance and Benchmarks

Official README claims:

| Operation | Claimed result |
|---|---:|
| Linux kernel full index | 3 minutes for 28M LOC / 75K files |
| Linux kernel graph size | 4.81M nodes / 7.72M edges |
| Django full index | about 6 seconds |
| Cypher query | under 1 ms |
| Trace call path depth 5 | under 10 ms |
| Dead code detection | about 150 ms |
| Structural query token reduction | about 3,400 tokens vs about 412,000 tokens for file-by-file grep exploration |

Paper claims:

| Metric | Claimed result |
|---|---:|
| Evaluation set | 31 real-world repositories |
| Answer quality | 83% |
| File-by-file baseline answer quality | 92% |
| Token reduction | 10x fewer tokens |
| Tool call reduction | 2.1x fewer tool calls |
| Graph-native query performance | matches/exceeds explorer on 19 of 31 languages |

Interpretation:

The benchmark suggests a trade-off: slightly lower general answer quality than file-by-file exploration, but substantially lower token usage and tool-call count. For enterprise Harness workflows, this trade-off may be acceptable if the Harness can fall back to direct file reading when graph results are insufficient.

Decision impact:

Pilot should measure:

- accuracy of caller/callee results
- freshness after file edits
- usefulness of impact analysis
- token reduction on actual enterprise repositories
- failure modes when code is generated or partially broken

## 6. Security and Operation

Source-backed fact:

The README states that processing happens locally and code never leaves the machine. It also says every release binary is signed, checksummed, and scanned by 70+ antivirus engines. The README badges include MIT license, CI, SLSA 3, VirusTotal, and OpenSSF Scorecard.

Analysis:

Local-only processing is a major advantage for enterprise projects where source code cannot be sent to third-party systems. However, because the tool reads source code and writes agent configuration files, installation should still be controlled.

Harness evaluation: High.

For enterprise adoption, install should be managed through internal tooling rather than arbitrary developer curl scripts.

## 7. Harness Integration

Recommended position:

```text
Harness Orchestrator
  -> Requirement Memory MCP / RAG
  -> Architecture Memory / ADR
  -> Codebase-Memory MCP
  -> Git / CI / Test tools
  -> Coding Agent / Review Agent / Test Agent
```

Best-fit Harness workflows:

1. **Code onboarding**
   - get architecture overview
   - identify entry points
   - locate major packages and routes

2. **Change impact analysis**
   - detect changed symbols
   - trace callers/callees
   - classify risk

3. **Architecture validation**
   - compare expected BD architecture with actual code dependencies
   - detect boundary violations

4. **Review support**
   - find blast radius from git diff
   - recommend test scope

Not a good fit for:

- extracting business requirements from Excel
- reading Japanese meeting notes
- generating BD documents
- replacing ontology/mapping rules
- replacing source-of-truth architecture documents

## 8. Comparison: codebase-memory-mcp vs CodeGraph

| Dimension | codebase-memory-mcp | CodeGraph |
|---|---|---|
| Positioning | Code intelligence engine for AI agents | Semantic code intelligence for agents |
| Language support claim | 158 Tree-sitter grammars | 20+ languages |
| Distribution | Pure C static binary | Bundled CLI / npm package |
| Persistence | SQLite-backed local graph, team-shared artifact | Local `.codegraph/` project graph |
| Cross-repo | Explicit `CROSS_*` edges and cross-repo summaries | Stronger emphasis on local project workflow in README |
| Architecture features | `get_architecture`, ADR, community detection, diff impact | surgical context, impact analysis, framework routes, auto-sync |
| Best Harness role | Enterprise Code Memory candidate | Lightweight developer-side Code Memory / navigation candidate |

## 9. Risks and Limitations

- Vendor/paper benchmark claims should be validated on our own repositories.
- Graph correctness depends on parser and semantic resolution quality.
- Hybrid LSP behavior should be tested per language.
- Cross-service inference can produce false positives if route/call matching is heuristic.
- Committing graph artifacts may create security and repository hygiene questions.
- This tool does not understand business requirements unless connected to another layer.

## 10. Decision Record

### Current Decision

Pilot.

### Why

The tool directly targets a missing Harness layer: reusable code semantics for AI agents. Its official README and paper both align with the target direction: local code graph, MCP access, impact analysis, cross-service links, cross-repo intelligence, and token reduction.

### Adoption Conditions

Adopt only after a pilot confirms:

- graph quality is reliable enough for caller/callee and impact analysis
- indexing and auto-sync work on realistic repositories
- security model is acceptable
- graph artifacts do not create compliance issues
- agent workflows actually reduce tool calls without losing important context

### Recommended Pilot

Use a 2-repo sample:

- one backend service
- one frontend or API client

Tasks:

1. Index both repositories.
2. Ask architecture overview questions.
3. Run impact analysis from a simulated git diff.
4. Compare against manual grep/read workflow.
5. Record token/tool-call savings and answer accuracy.

## 11. References

Official:

- DeusData/codebase-memory-mcp repository: https://github.com/DeusData/codebase-memory-mcp
- README sections reviewed: overview, features, indexing pipeline, performance, team-shared graph artifact, installation, local processing.

Paper:

- Martin Vogel, Falk Meyer-Eschenbach, Severin Kohler, Elias Grünewald, Felix Balzer. `Codebase-Memory: Tree-Sitter-Based Knowledge Graphs for LLM Code Exploration via MCP`. arXiv:2603.27277. https://arxiv.org/abs/2603.27277

## 12. Self Review

| Criterion | Score | Notes |
|---|---:|---|
| Technical accuracy | 26/30 | Based on official README and paper, but source code not fully reviewed. |
| Completeness | 17/20 | Good WIP coverage; needs exact MCP tool list and source-code validation. |
| Harness relevance | 20/20 | Strongly tied to Code Memory layer. |
| Decision support | 14/15 | Clear Pilot decision and conditions. |
| Reference quality | 8/10 | Official README and paper used; no independent benchmark yet. |
| Readability | 5/5 | Structured for architect decision-making. |
| Total | 90/100 | Usable WIP, not final validated record. |
