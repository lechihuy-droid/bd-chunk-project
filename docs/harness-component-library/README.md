# Harness Component Library

## Purpose

This library extends the existing Harness learning path without changing its day-by-day structure.

The learning path remains the stable study sequence. The component library captures reusable architectural concepts, while the reference layer records external source material and the design layer records decisions specific to the BD Harness.

```text
Learning Path
    ↓
Component Library
    ↓
External References
    ↓
BD Harness Design
```

## Repository Layers

```text
docs/
├── harness-learning/                 # Existing day-by-day learning path
├── harness-component-library/        # Reusable Harness capabilities and patterns
├── harness-references/               # External source notes and provenance
└── harness-design/                   # Our own architecture and implementation decisions
```

## Rules

1. Do not reorder or rewrite completed learning days merely because a new source is added.
2. A reference document is not automatically an architecture standard.
3. Component notes must distinguish:
   - source-backed content;
   - architectural inference;
   - BD Harness-specific decisions.
4. Learning-day documents may link to components, but components must remain reusable outside a single day.
5. External source names must not be presented as official endorsement when the material is independently compiled.

## Initial Components

| Component | Purpose | Learning-path relationship |
|---|---|---|
| Workflow patterns | Reusable orchestration patterns | Used after Day 3 |
| Ratchet execution loop | Inspect–propose–execute–evaluate–keep/revert loop | Advanced runtime/evaluation material |
| Execution DAG | Parallel agent experiment lineage and traversal | Multi-agent scaling material |
| Knowledge graph memory | Entity, relation, provenance and subgraph retrieval | Memory/context material |
| Dynamic workflow | Runtime-generated orchestration with fresh-context workers | Workflow/runtime material |

## Source Status

The document titled **“Andrej Karpathy — From 1 Loop to 1,000 Agents: The Graph Engineering Manual”** is treated as an independently compiled synthesis, not as an official Karpathy or Anthropic publication.

Its useful concepts are decomposed into component notes and traced back to their underlying sources where possible.
