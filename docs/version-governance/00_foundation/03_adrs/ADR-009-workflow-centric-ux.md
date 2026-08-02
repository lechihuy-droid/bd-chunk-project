# ADR-009 — Workflow-Centric UX over Asset-Centric UX

**Status:** Accepted  
**Scope:** Version Governance UX  
**Decision date:** 2026-08-02

## Context

The governance backend requires first-class asset entities and immutable references for capabilities, agents, prompts, workflow releases, run manifests, artifact revisions, approvals, and lineage.

Presenting those entities as the primary user journey would force users to manually coordinate registry objects and would not match how they perform RD-to-BD work.

## Decision

Harness Hub shall preserve an asset-centric backend model while presenting a workflow-centric user experience centered on:

```text
Project
  -> Workflow
    -> Run
      -> Output
        -> History / Compare / Approve
```

Capability, Agent, Prompt, Tool, Release, Manifest, and Artifact remain first-class backend entities. They are normally reached through workflow, run, or output context and exposed through progressive disclosure.

Version creation, manifest freezing, lineage registration, artifact revision creation, and baseline update should occur automatically behind normal user actions where safe. Publication and environment promotion remain explicit actions.

## Consequences

### Positive

- Lower cognitive load.
- Version governance becomes a platform behavior rather than a separate operational burden.
- Output comparison aligns with the user question: “Why did this output change?”
- Technical provenance remains available without dominating normal workflows.

### Trade-offs

- Frontend views must aggregate data across several domain entities.
- Deep links and permissions must preserve asset-level governance.
- Power users still need technical inspection and catalog paths.

## References

- `docs/40_architecture/version-governance-architecture.md`
- `docs/40_architecture/version-governance-ux-principles.md`
