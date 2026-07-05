# Architecture Notes

This document describes the target architecture for a future BD Harness. It is a planning artifact, not an implementation guide for this repository.

## Target concept

```text
User request or project task
  -> Harness Orchestrator
  -> Specialist roles
  -> Deterministic parsing service
  -> Validation gates
  -> Reviewable BD output
```

## Conceptual layers

1. Orchestration layer: routes jobs and enforces stage order.
2. Registry layer: defines agents, capabilities, and runtime profiles.
3. Data layer: stores raw input, normalized output, and indexes.
4. Ontology layer: controls source labels, requirement types, BD frames, and mapping rules.
5. Runtime layer: should be built in a separate implementation repository.
6. Review layer: blocks unresolved items before client-facing output.

## Runtime boundary

A future sandbox runtime should not access production databases directly. It should use approved connectors, exported files, controlled API endpoints, or cloud sandbox data mirrors.
