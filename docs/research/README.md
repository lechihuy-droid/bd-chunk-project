# Research Library

This folder is the Technology Decision Library for the BD / Enterprise Harness project.

The goal is not to bookmark tools. The goal is to create source-backed technical research documents that help decide whether a technology should be adopted, piloted, watched, or rejected for the Harness roadmap.

## Current Scope

```text
docs/research/
├── README.md
├── _template.md
├── tool-research-backlog.md
└── code-memory/
    ├── codebase-memory-mcp.md
    ├── codegraph.md
    └── cocoindex.md
```

## Categories

- `code-memory/`: tools that help agents understand source code structure, symbols, call paths, dependencies, blast radius, routes, cross-repo relationships, or keep code/context indexes fresh.
- `workflow/`: agent workflow tools and CLI coding workflows.
- `uiux/`: UI/UX tools useful for Harness frontend or developer experience.
- `papers/`: academic or preprint research that influences architecture decisions.

## Research Standard

Every research document should separate three layers:

1. **Source-backed fact**: what the original README, documentation, paper, or source code says.
2. **Technical analysis**: what the fact means architecturally.
3. **Harness evaluation**: whether the capability matters for the BD / Enterprise Harness project.

## Decision Labels

| Label | Meaning |
|---|---|
| Adopt | Strong candidate for the target architecture. |
| Pilot | Worth testing in a controlled PoC before adoption. |
| Watch | Interesting but not yet needed or not mature enough. |
| Reject | Not suitable for the project constraints. |

## Source Policy

Use original sources first:

- Official GitHub repository / README
- Official documentation website
- Official paper / preprint
- Source code when implementation details matter
- Community sources only as secondary evidence

When a claim is not yet validated, mark it as `Needs validation` instead of treating it as fact.

## Review Rubric

| Criterion | Max Score |
|---|---:|
| Technical accuracy | 30 |
| Completeness | 20 |
| Harness relevance | 20 |
| Decision support | 15 |
| Reference quality | 10 |
| Readability | 5 |
| Total | 100 |

Target quality:

- `>= 90`: usable WIP decision document
- `>= 95`: architect-ready research document
- `< 90`: draft only
