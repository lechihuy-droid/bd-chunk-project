# Harness Hub Version Governance — Finalization Record v1.0

**Status:** Historical approval record  
**Effective date:** 2026-08-02  
**Canonical architecture:** `docs/40_architecture/version-governance-architecture.md`  
**Canonical UX principles:** `docs/40_architecture/version-governance-ux-principles.md`

## Final decision

The approved POC baseline integrates Versioning and Artifact Governance into the existing Harness Hub control plane rather than introducing a standalone registry product.

Locked decisions include:

- Harness Hub remains the host application and system of record for capability, agent, workflow release, frozen run manifest, artifact revision, approval, baseline, and lineage references.
- LangGraph is the initial execution runtime behind a runtime-neutral adapter.
- MLflow owns prompt versions, experiments, traces, and evaluation references.
- Git owns workflow, agent, tool, schema, and evaluator source code.
- Object storage owns immutable binary and document blobs.
- Published versions, workflow releases, run manifests, and artifact revisions are immutable.
- Environment mappings and baselines are mutable pointers to immutable targets.
- PostgreSQL, transactional outbox, and idempotent processing are sufficient for the POC.
- Capability is the smallest reusable business-level unit.

## Purpose of this record

This file is retained only as an approval and supersession record. Implementation teams and coding agents must use the canonical architecture and UX documents above rather than this historical summary.
