# Harness Hub Version Governance — Documentation Index

## Documentation flow

```text
00_foundation
    ↓
10_learning/version-governance
    ↓
30_poc/version-governance
    ↓
40_architecture
    ↓
50_sdd/version-governance
    ↓
Implementation
```

## Canonical documents

### Foundation

- `docs/00_foundation/01_engineering_philosophy.md` — engineering philosophy for the whole Harness Hub platform.
- `docs/00_foundation/03_adrs/ADR-009-workflow-centric-ux.md` — accepted UX architecture decision.

### Fast learning

- `docs/10_learning/version-governance/README.md` — learning-package index and reading order.
- `docs/10_learning/version-governance/01_core_concepts.md` — Version Governance core concepts bootcamp.

Planned next documents:

- `02_solution_landscape.md`
- `03_build_decisions.md`
- `04_poc_boundary.md`

### Architecture

- `docs/40_architecture/version-governance-architecture.md` — canonical architecture for version and artifact governance.
- `docs/40_architecture/version-governance-ux-principles.md` — canonical UX principles and acceptance scenarios.

## POC documents

The `docs/30_poc/` directory is reserved for POC-only scope, demo scenarios, acceptance criteria, and rollout plans. Architecture, learning materials, and platform-wide principles must not be stored there.

## SDD documents

The `docs/50_sdd/version-governance/` directory will contain implementation-facing requirements, domain model, data model, API contracts, runtime integration, and test strategy after the four fast-learning documents are complete.

## Archive

Historical finalization records are kept under `docs/archive/` only when they contain approval context not already represented by Git history or ADRs.

## Placement rule

Each topic has one canonical home. Git history records revisions; do not create parallel files named `final`, `updated`, or `v2` unless the document is explicitly a historical approval record.
