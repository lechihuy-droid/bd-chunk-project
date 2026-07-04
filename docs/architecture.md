# Architecture

The project is structured as a file-based Harness MVP.

```text
User / CLI Job
  -> Harness Orchestrator
  -> Specialist Skills
  -> Deterministic Python Pipeline
  -> Validation Gates
  -> Reviewable BD Output
```

## Layers

1. Orchestration layer: routes jobs and enforces stage order.
2. Registry layer: defines agents, skills, and tool profiles.
3. Data layer: stores raw input, normalized output, and indexes.
4. Ontology layer: controls source labels, requirement types, BD frames, and mapping rules.
5. Runtime layer: executes deterministic parsing, chunking, validation, indexing, and BD generation.
6. Review layer: blocks unresolved items before client-facing output.

## Runtime boundary

The sandbox runtime should not access production databases directly. It should use approved connectors, exported files, controlled API endpoints, or cloud sandbox data mirrors.
