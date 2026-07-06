# CodeGraph

> ⚠️ Work In Progress
>
> Version: 0.1 Draft
> Status: Research document, not final adoption record
> Last updated: 2026-07-06
> Recommendation: Pilot / Watch
> Confidence: Medium-High

## Source Verification

| Source | Status | Notes |
|---|---|---|
| Official repository | Checked | https://github.com/colbymchenry/codegraph |
| Official README | Checked | README describes installation, supported agents, local graph, benchmark, auto-sync, routes, framework support. |
| Official docs | Identified | https://colbymchenry.github.io/codegraph/ |
| Source code | Not fully reviewed | Needs follow-up before final adoption. |
| Independent benchmark | Not checked | Current benchmark numbers are README-reported. |

## 1. Executive Summary

CodeGraph is a local semantic code intelligence tool for AI coding agents. It builds a project-level graph and exposes it through an MCP server / CLI so agents can retrieve relevant code context, call paths, dependencies, and blast radius without crawling files manually.

The official README positions CodeGraph as a way to supercharge Claude Code, Cursor, Codex, OpenCode, Hermes Agent, Gemini, Antigravity, and Kiro with local semantic code intelligence. It emphasizes surgical context, fewer tool calls, faster answers, 100% local processing, and auto-sync.

For the BD / Enterprise Harness project, CodeGraph is best understood as a **lightweight developer-side Code Memory / navigation layer**. It may be easier to adopt early than a heavier enterprise graph engine, but it should not be treated as the final cross-repository architecture memory without further validation.

## 2. Problem Statement

The README describes the same core problem as other code graph tools: an AI agent discovers structure through grep, glob, and file reads, rebuilding call paths and dependencies manually. This creates unnecessary tool calls and slows down the actual coding/reasoning work.

CodeGraph's answer is to pre-build a knowledge graph of symbols, call edges, and dependencies so the agent can request targeted context in one or a few calls.

For Harness work, this matters because coding agents will eventually need to answer questions like:

- Where is this API implemented?
- What calls this method?
- What flow is affected by this change?
- Which files should be reviewed or tested?

## 3. Architecture Overview

The practical architecture is:

```text
Source Repository
  -> codegraph init
  -> Local .codegraph/ project index
  -> Auto-sync watcher
  -> MCP server / CLI
  -> Claude Code / Cursor / Codex / Gemini / Other Agents
```

Official README facts:

- Installation can be done via shell/PowerShell installer or npm package.
- `codegraph install` wires CodeGraph to supported agents.
- `codegraph init` creates a local `.codegraph/` directory and builds the project graph.
- Auto-sync is enabled by default and watches file changes.
- `codegraph uninstall` removes MCP server configuration and leaves project indexes untouched.

Technical interpretation:

This is developer-workstation oriented. The workflow is simple: install CLI, connect agents, initialize each project, then let the graph auto-sync.

Harness interpretation:

CodeGraph is a strong candidate for individual developer productivity and early Harness prototyping. It may be used before building or adopting a centralized Code Memory layer.

## 4. Core Capabilities

### 4.1 Surgical Context

Source-backed fact:

The README says CodeGraph gives agents exact code context in one call, including related symbols, relevant source, call paths, and blast radius. It contrasts this with file-by-file search.

Analysis:

This is the primary value proposition. Agents should spend fewer calls on discovery and more on reasoning or editing.

Harness evaluation: High for coding workflows, medium for BD-only workflows.

### 4.2 Local Project Graph

Source-backed fact:

The README says `codegraph init` creates a local `.codegraph/` directory and builds the full graph.

Analysis:

This makes CodeGraph easy to pilot because it does not require server infrastructure. It also means the initial adoption model is per-project and per-developer rather than centralized.

Harness evaluation: High for PoC, medium for enterprise shared memory.

### 4.3 Auto-sync

Source-backed fact:

The README says auto-sync is enabled by default and watches file changes. It describes native OS watchers: FSEvents, inotify, and ReadDirectoryChangesW. It also describes a debounce window and per-file staleness banners that tell the agent to read a file directly when a result may be stale.

Analysis:

Auto-sync is important because agent-edited repositories change rapidly. If the index becomes stale, graph-based answers become dangerous. CodeGraph's explicit staleness signaling is a useful safety feature.

Harness evaluation: High.

Any Harness using code graphs must treat freshness as a first-class concern.

### 4.4 Benchmark Results

Source-backed fact:

The README reports benchmark results across 7 real-world open-source codebases and 7 languages, comparing Claude Code headless with and without CodeGraph, median of 4 runs per arm. It reports the universal result as 58% fewer tool calls, 22% faster answers, and near-zero file reads.

The README also provides per-repository examples:

| Codebase | Language / size | Reported result |
|---|---|---|
| VS Code | TypeScript, about 10k files | 81% fewer tool calls, 64% fewer tokens |
| Excalidraw | TypeScript, about 640 files | 40% fewer tool calls, 27% faster |
| Django | Python, about 3k files | 77% fewer tool calls, 60% fewer tokens |
| Tokio | Rust, about 790 files | 57% fewer tool calls |
| OkHttp | Java, about 645 files | 50% fewer tool calls |
| Gin | Go, about 110 files | 44% fewer tool calls |
| Alamofire | Swift, about 110 files | 58% fewer tool calls |

Analysis:

The benchmark is relevant but should be treated as vendor-reported. It is useful for hypothesis generation, not final enterprise proof.

Harness evaluation: Medium-High.

Pilot should reproduce a smaller benchmark on the Harness target repositories.

### 4.5 Supported Languages and Routes

Source-backed fact:

The README lists 20+ languages including TypeScript, JavaScript, Python, Go, Rust, Java, C#, VB.NET, PHP, Ruby, C, C++, CUDA, Objective-C, Swift, Kotlin, Scala, Dart, Lua, R, Erlang, COBOL, Solidity, Terraform/OpenTofu, Svelte, Vue, Astro, Liquid, and Pascal/Delphi.

The README also describes framework-aware route detection across frameworks such as Django, Flask, FastAPI, Express, NestJS, Laravel, Drupal, Rails, Spring, Play, Gin/chi/gorilla/mux, Axum/actix/Rocket, ASP.NET, Vapor, React Router, SvelteKit, Vue Router, Nuxt, and Astro.

Analysis:

Framework-aware route detection is especially useful for web application modernization. It lets the graph connect route patterns to handlers/controllers, which is valuable for impact analysis and architecture understanding.

Harness evaluation: High.

This fits the user's WinForms-to-Web-App / BD-to-code roadmap once source code exists.

### 4.6 Mixed iOS / React Native / Expo Bridging

Source-backed fact:

The README describes bridging across Swift/Objective-C, React Native legacy bridge, TurboModules, native-to-JS events, Expo Modules, Fabric components, and legacy Paper view managers. It also lists real codebases used for validation.

Analysis:

This is specialized but shows the tool is designed to cross static-analysis boundaries where ordinary parsing stops.

Harness evaluation: Low-Medium for the current BD Harness unless mobile/React Native becomes part of scope.

### 4.7 Local-only Processing

Source-backed fact:

The README states CodeGraph is 100% local, no data leaves the machine, no API keys, no external services, and uses SQLite database only.

Analysis:

This is important for enterprise source-code constraints.

Harness evaluation: High.

Local-first code intelligence is preferable for confidential client projects.

## 5. Enterprise Evaluation

| Criterion | Rating | Reason |
|---|---:|---|
| Local development fit | High | Simple CLI install, local `.codegraph/`, agent auto-config. |
| Enterprise shared memory fit | Medium | Strong local workflow, but shared cross-repo governance needs validation. |
| Code navigation | High | Designed for surgical context and fewer file reads. |
| Change impact | High | README emphasizes blast radius and impact analysis. |
| Cross-service architecture | Medium | Framework routes are strong; cross-repo enterprise story appears less explicit than codebase-memory-mcp. |
| Security posture | Medium-High | Local-only processing is strong; source code review still needed. |
| Harness fit | Medium-High | Very useful for developer-side agent workflow; not enough alone for full Business-Architecture-Code traceability. |

## 6. Harness Integration

Recommended role:

```text
Developer Workstation
  -> CodeGraph local project graph
  -> MCP / CLI
  -> Claude Code / Cursor / Codex
  -> Coding task / review task
```

In the broader Harness:

```text
Harness Orchestrator
  -> Requirement KB
  -> Architecture KB
  -> CodeGraph for local code context
  -> Git / CI / Test feedback
```

Best-fit use cases:

1. Local codebase onboarding.
2. Reducing grep/read tool calls in Claude Code or Codex.
3. Finding route-to-handler relationships.
4. Understanding blast radius before edits.
5. Early PoC before adopting a heavier shared Code Memory engine.

Not a good fit alone for:

- enterprise-wide architecture knowledge base
- requirement-to-code traceability
- business document interpretation
- long-term cross-team decision memory

## 7. Comparison: CodeGraph vs codebase-memory-mcp

| Dimension | CodeGraph | codebase-memory-mcp |
|---|---|---|
| Best role | Local developer-side code graph | Enterprise Code Memory candidate |
| Setup | CLI / npm package, `codegraph install`, `codegraph init` | Static binary, install command, multiple package managers |
| Local graph | `.codegraph/` per project | SQLite-backed graph, cache + optional `.codebase-memory/graph.db.zst` artifact |
| Language support claim | 20+ languages | 158 Tree-sitter grammars |
| Benchmark scope | 7 repositories, README-reported | 31 repositories in arXiv paper + README benchmarks |
| Cross-repo story | Needs more validation | Explicit `CROSS_*` edges and cross-repo summaries |
| Best Harness stage | Early PoC / local coding workflow | Later enterprise Code Memory layer |

## 8. Risks and Limitations

- Benchmark is README-reported and should be reproduced.
- Source code has not yet been reviewed in this document.
- Enterprise shared-memory model is less clear than local developer usage.
- It does not replace Requirement KB, architecture docs, ADR, or ontology.
- Route/framework inference may include heuristic edges and should be validated before relying on it for critical review.

## 9. Decision Record

### Current Decision

Pilot / Watch.

### Why

CodeGraph looks highly practical for local AI coding workflows. It is likely useful immediately with Claude Code, Cursor, Codex, and similar tools. For the Harness, it is a good lightweight Code Memory candidate, especially before source-code scale and governance requirements justify a heavier engine.

### Adoption Conditions

Adopt for local developer workflow if pilot confirms:

- `codegraph init` and auto-sync are reliable on target repos
- agents actually use CodeGraph instead of falling back to file-crawling subagents
- route and impact analysis results are accurate enough
- local-only security model is acceptable

### Recommended Pilot

1. Install CodeGraph in one local development environment.
2. Initialize a representative repository.
3. Ask architecture questions with and without CodeGraph.
4. Measure tool calls, file reads, time, token usage, and answer quality.
5. Compare with codebase-memory-mcp on the same repository.

## 10. References

Official:

- colbymchenry/codegraph repository: https://github.com/colbymchenry/codegraph
- Official documentation website: https://colbymchenry.github.io/codegraph/
- README sections reviewed: install, supported agents, why CodeGraph, benchmark results, key features, auto-sync, framework-aware routes, mixed iOS / React Native / Expo bridging.

## 11. Self Review

| Criterion | Score | Notes |
|---|---:|---|
| Technical accuracy | 25/30 | Based on official README; source code not fully reviewed. |
| Completeness | 16/20 | Good WIP; needs CLI/MCP tool details and docs review. |
| Harness relevance | 18/20 | Clear local developer-side role. |
| Decision support | 14/15 | Clear Pilot / Watch decision. |
| Reference quality | 7/10 | Official README/docs identified; no independent benchmark. |
| Readability | 5/5 | Structured for decision-making. |
| Total | 85/100 | Useful WIP, not final validated architecture record. |
