# Harness Hub Version Governance Architecture — v1.0 Final

**Status:** FINAL  
**Effective date:** 2026-08-02  
**Canonical architecture document:** `docs/poc/minimal-agent-version-registry-implementation-architecture.md`  
**Target application:** Existing Harness Hub  
**Primary use case:** RD-to-BD POC

---

## 1. Final Decision

The architecture described in the canonical document is approved as the implementation baseline for the POC.

This is **not** a standalone registry product. It is a bounded **Versioning and Artifact Governance subsystem** integrated into the existing Harness Hub control plane.

The approved stack is:

```text
Existing Harness Hub
+ Capability / Agent / Workflow Release modules
+ Runtime-neutral WorkflowRuntimePort
+ LangGraphRuntimeAdapter
+ LangGraph OSS / Agent Server
+ MLflow 3
+ PostgreSQL
+ MinIO, S3, or existing compatible object storage
+ Git
```

---

## 2. Locked Architectural Decisions

The following decisions are final for the POC:

1. Harness Hub remains the host application, user-facing control plane, and owner of workspace/project context.
2. No second control-plane UI or standalone Thin Registry application will be created.
3. The new capability is implemented first as a modular bounded subsystem in the existing Harness Hub backend.
4. LangGraph is the initial workflow execution engine, but Harness Hub domain entities must not depend on LangGraph SDK classes or persistence schemas.
5. A runtime-neutral `WorkflowRuntimePort` separates the Harness Hub domain from the LangGraph adapter.
6. MLflow is the system of record for prompt versions, prompt aliases used during authoring, experiments, traces, and evaluation references.
7. Git is the system of record for workflow, agent, tool, schema, and evaluator source code.
8. Harness Hub owns Capability Versions, Agent Versions, Workflow Releases, environment mappings, Frozen Run Manifests, Artifact Revision chains, approvals, baselines, and cross-system lineage references.
9. Object storage owns immutable binary and document blobs; Harness Hub stores metadata, hashes, provenance, and business identity.
10. Published versions, releases, frozen manifests, and artifact revisions are immutable.
11. Environment and baseline records are mutable pointers to immutable targets.
12. Production execution resolves and records exact component versions; aliases are not retained as runtime resolution inputs.
13. Capability is the smallest reusable business-level unit. Workflow is a composition; Agent Version is an executable implementation configuration.
14. PostgreSQL is sufficient for POC lineage and dependency queries. No graph database is introduced.
15. Transactional outbox and idempotent processing are sufficient for the POC. Kafka or another event bus is deferred.
16. Knowledge Snapshot remains minimal in the POC: source identifiers or URI, version/timestamp when available, and content/manifest hash.
17. Evaluation execution remains external to the governance subsystem. Harness Hub registers requests, references, results, and gate decisions.
18. Existing Harness Hub identity, workspace isolation, model gateway, tool gateway, audit conventions, and storage integration must be reused where available.

---

## 3. POC Implementation Boundary

### Included

- Capability catalog and immutable capability versions.
- Agent definitions and immutable Agent Versions.
- Workflow definitions and immutable Workflow Releases.
- Exact prompt references resolved from MLflow.
- DEV and PROD environment-to-release mapping.
- Frozen Run Manifest creation before runtime execution.
- LangGraph runtime adapter for start, resume, cancel, status, and checkpoint reference.
- Run linkage to LangGraph and MLflow identifiers.
- Knowledge Snapshot reference and hash.
- Artifact business identity and immutable revisions.
- AI-generated, human-edited, regenerated, imported, and transformed revision provenance.
- Approval records and one active baseline per artifact business key.
- Basic upstream lineage and run-manifest comparison.
- Audit of publication, promotion, execution registration, approval, and baseline change.

### Deferred

- Standalone registry service or separate registry frontend.
- Multiple workflow runtime implementations.
- Generic enterprise asset framework.
- Generic multi-level policy engine.
- Graph database.
- Kafka, NATS, or another event-streaming platform.
- Bidirectional Git synchronization.
- Custom tracing backend.
- Custom evaluation runtime.
- LLM-generated semantic diff as a required feature.
- Embedded Excel or PDF co-authoring.
- Cross-workspace asset sharing.
- Multi-region deployment.
- Advanced ontology, vector-index, and graph snapshot governance unless already available in Harness Hub.

---

## 4. Implementation Gate

Coding may start only after Phase 0 confirms the current Harness Hub extension points:

- Existing backend module structure.
- Workspace/project identifiers and authorization model.
- Database and migration framework.
- Model gateway and tool gateway contracts.
- Existing workflow/run representation.
- Existing artifact/object-storage handling.
- Audit event conventions.
- UI routing and navigation extension points.
- Whether MLflow and LangGraph are already integrated.

Where an existing Harness Hub capability satisfies the canonical architecture, the implementation must extend it rather than duplicate it.

---

## 5. Final Acceptance Position

The POC is successful when Harness Hub can demonstrate this complete vertical slice:

```text
Publish Capability Version
  -> Publish Agent Version
  -> Publish Workflow Release
  -> Map environment to release
  -> Resolve exact MLflow prompt versions
  -> Freeze Run Manifest
  -> Execute through LangGraphRuntimeAdapter
  -> Register generated BD Artifact Revision
  -> Upload a human-edited revision
  -> Approve and set active baseline
  -> Display upstream lineage
  -> Compare two manifests and identify changed components
```

The incremental implementation should remain within the code-size guardrail defined by the canonical architecture. Any feature that materially expands the subsystem beyond the approved POC boundary requires a new architecture decision record.

---

## 6. Supersession Rule

This v1.0 finalization record and the canonical architecture document together form the approved POC baseline.

Changes to locked decisions must be proposed through an ADR and must not be introduced silently by a coding agent or implementation team.
