# BD Harness Documentation Library

This repository is a documentation and planning library for the BD-focused Harness project.

Primary use:

- Architecture notes
- Project plans
- Workflow definitions
- Ontology drafts
- Governance notes
- Delivery playbooks
- Agent and capability design references

Runtime implementation should live in a separate repository when the project moves from planning to build.

## Target concept

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

## Recommended structure

```text
docs/                 methodology, glossary, architecture, plans
harness/              Harness design references
harness/registry/     agent, capability, and runtime profile drafts
harness/workflows/    workflow and stage-gate drafts
ontology/             labels, requirement types, BD frames, mapping rules
data/                 placeholder folders only
src/                  deprecated placeholder only
tests/                deprecated placeholder only
```

## Design principles

1. Raw files should pass through traceability control before BD generation.
2. Provenance should be locked before LLM-assisted interpretation.
3. Source IDs, RKB IDs, and BD frame IDs should be deterministic.
4. Ontology and mapping rules should be controlled before generation.
5. Human review remains mandatory before client-facing BD output.

## Main reading path

1. `docs/architecture.md`
2. `docs/methodology.md`
3. `docs/glossary.md`
4. `harness/workflows/bd_requirement_to_basic_design.yaml`
5. `harness/registry/agent_catalog.yaml`
6. `harness/registry/capability_catalog.yaml`
7. `ontology/mapping_rules.yaml`

## Migration note

Earlier commits contained a small Python/CLI skeleton. This repo has now been repurposed as a documentation-only planning library. Runtime files remain only as deprecated placeholders when deletion is unavailable.
