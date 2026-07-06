# Tool Research Backlog

This backlog tracks tools that may affect the Enterprise Harness architecture. It is intentionally decision-oriented: each item should eventually become a technical research document or be rejected with a short reason.

## Code Memory

| Tool | Priority | Status | Current Decision | Next Action |
|---|---:|---|---|---|
| codebase-memory-mcp | High | WIP research document created | Pilot | Validate official README claims against source code and run a small PoC on a sample repo. |
| CodeGraph | High | WIP research document created | Pilot / Watch | Test as a lightweight local developer-side code memory layer. |

## Current Focus

### codebase-memory-mcp

Why it matters:

- Persistent code knowledge graph through MCP.
- Strong fit for Code Memory layer in the target Harness.
- Official README claims high-scale indexing, cross-service linking, cross-repo intelligence, 14 MCP tools, local execution, static binary distribution, and team-shared graph artifact.
- The arXiv preprint reports 83% answer quality versus 92% for file-by-file exploration, with 10x fewer tokens and 2.1x fewer tool calls across 31 repositories.

Primary sources:

- Official repository: https://github.com/DeusData/codebase-memory-mcp
- Paper: https://arxiv.org/abs/2603.27277

Research questions:

- How reliable are the graph relationships in real enterprise code?
- How well does incremental indexing work with active agent edits?
- How should a Harness orchestrator decide when to use graph query versus vector/RAG query?
- Should `.codebase-memory/graph.db.zst` be committed in enterprise projects?

### CodeGraph

Why it matters:

- Lightweight local code graph for AI coding agents.
- Official README positions it as semantic code intelligence for Claude Code, Cursor, Codex, OpenCode, Gemini, Antigravity, Kiro, and others.
- Focuses on surgical context, fewer tool calls, auto-sync, local SQLite, route detection, impact analysis, and local-only processing.
- Benchmark in README reports median results across 7 open-source codebases, including 58% fewer tool calls, 22% faster answers, and near-zero file reads.

Primary sources:

- Official repository: https://github.com/colbymchenry/codegraph
- Official docs: https://colbymchenry.github.io/codegraph/

Research questions:

- Is CodeGraph better suited as a local developer tool rather than shared enterprise memory?
- How does its graph model compare with codebase-memory-mcp?
- What are the practical limits of auto-sync and framework-aware route detection?
- Should it be used as a stepping stone before adopting a heavier Code Memory engine?

## Next Candidates

These are not yet researched in this repo:

| Tool | Category | Priority | Reason |
|---|---|---:|---|
| Sourcegraph / Cody | Code Memory / Search | Medium | Mature enterprise code search and assistant ecosystem. |
| ast-grep | Code Analysis | Medium | Structural search and codemod candidate. |
| Tree-sitter | Code Parsing | High | Foundational parser technology behind many code graph tools. |
| Neo4j | Knowledge Graph | Medium | Candidate for cross-layer Business-Architecture-Code graph. |
