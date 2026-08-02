# Harness Hub Version Governance — UX Refinement v1.1

**Status:** Final UX refinement  
**Scope:** User experience for version control inside the existing Harness Hub platform  
**Architecture impact:** None to the approved v1.0 backend architecture  
**Primary users:** AI engineers, solution architects, workflow designers, reviewers, project leads

---

## 1. Decision

The approved backend remains asset-centric and continues to manage capability versions, agent versions, workflow releases, frozen run manifests, artifact revisions, approvals, and lineage.

The user experience shall be workflow-centric.

```text
System model                         User mental model
------------                         -----------------
Capability                           Project
Agent                                Workflow
Prompt                               Run
Workflow Release                     Output
Run Manifest                         History
Artifact Revision
```

Users should not need to understand or navigate a registry as a separate product area during normal work. Version governance is exposed contextually from the Harness Hub surfaces where users design, run, review, compare, and approve AI workflows and outputs.

Core principle:

> Architecture is asset-centric; user experience is workflow-centric.

---

## 2. UX Goals

The UX shall enable users to:

1. Change a workflow, node, prompt, or agent without manually coordinating version records.
2. Understand which workflow state produced an output.
3. Compare outputs in business terms rather than raw manifests.
4. See a chronological history of changes, runs, reviews, and approvals.
5. Roll back or restore an earlier published workflow state with confidence.
6. Access exact technical provenance only when deeper inspection is required.

The UX shall minimize the cognitive cost of:

- Prompt version numbers.
- Agent version numbers.
- Release manifests.
- Runtime identifiers.
- Content hashes.
- Registry-specific terminology.

These details remain available through progressive disclosure.

---

## 3. Primary User Journey

The primary journey is:

```text
Project
  -> Workflow
      -> Run
          -> Output
              -> History / Compare / Approve
```

Version-management objects are accessed within this context:

```text
Workflow
├── Nodes
│   ├── Agent configuration
│   ├── Prompt
│   ├── Tools
│   └── Model profile
├── Published states
├── Runs
├── Outputs
└── Activity history
```

A user should not need to move between separate Prompt Registry, Agent Registry, Release Registry, and Artifact Registry screens to complete the normal RD-to-BD workflow.

---

## 4. Interaction Principles

### 4.1 Registry invisible by default

Version governance should operate automatically behind normal actions.

```text
Save workflow change
  -> create draft revision automatically

Publish workflow
  -> validate and create immutable workflow release

Start run
  -> resolve exact component versions and freeze run manifest

Generate output
  -> create immutable artifact revision

Approve output
  -> record approval and move baseline pointer atomically
```

The UI may report what occurred, but should not require the user to manually create each technical object.

### 4.2 Progressive disclosure

The default view presents workflow, run, and output concepts.

Technical detail is revealed in layers:

```text
Output
  -> Run summary
      -> Workflow state
          -> Node configuration
              -> Agent version
                  -> Prompt version / tool version / model profile
                      -> Frozen manifest / content hash / external IDs
```

### 4.3 Meaningful labels before version numbers

Every published state should support a human-readable change title and summary.

Example:

```text
Workflow release 1.4.0
Improve API naming consistency

Changes
- Updated writer prompt
- Added naming validation node
- RD source unchanged
```

The version identifier remains visible but is secondary to the change intent.

### 4.4 Business objects before technical artifacts

The UI should present:

- API Design — Customer Search.
- Screen Design — Order Entry.
- DB Design — Customer Master.

It should not lead with generic labels such as `Artifact 01J...` or `Revision 8`.

### 4.5 Safe automation

Automatic version creation must not silently publish changes to production.

The distinction remains:

```text
Save       -> draft revision
Test       -> test run using resolved draft state
Publish    -> immutable approved release
Rollback   -> move environment pointer to earlier release
```

---

## 5. Workflow-Centric Experience

## 5.1 Workflow overview

A workflow overview should surface:

- Current status: Draft, In review, Published, Deprecated.
- Active DEV and PROD releases.
- Last meaningful change.
- Recent runs.
- Outputs requiring review.
- Latest approved outputs.
- Warnings about unresolved or revoked dependencies.

Example:

```text
RD to API Basic Design

PROD: 1.3.0 — Stable API generation
DEV:  1.4.0 — Improve naming consistency

Recent activity
- Draft prompt changed by Huy
- Test run succeeded
- API Design F001 awaiting review
```

## 5.2 Workflow node editing

Prompt, agent, tool, and model configuration should be edited within the selected workflow node context.

```text
Node: Generate API Basic Design
├── Capability: Generate API BD
├── Agent: BD API Writer
├── Prompt: Draft API Design
├── Tools: RD Reader, Naming Validator
└── Model: High Accuracy Design
```

The user can inspect version history for each child object without leaving the workflow context.

## 5.3 Save behavior

Saving a node or workflow change creates or updates a draft definition.

The UI should show:

- Unsaved changes.
- Draft saved.
- Change summary required before review or publish.
- Whether the draft differs from DEV or PROD.

A save must not mutate an immutable published release.

## 5.4 Publish behavior

Publishing should resemble a release-review flow:

```text
Review changes
  -> Validate dependencies
  -> Run required tests/evaluations
  -> Enter release title and notes
  -> Publish immutable release
  -> Optionally promote to environment
```

The UI should describe impact:

- Prompt changed.
- Agent changed.
- Workflow topology changed.
- Input/output contract changed.
- Existing outputs are not modified.

---

## 6. Run Experience

## 6.1 Run summary

A run page should prioritize:

- Workflow and project.
- Input source.
- Status and elapsed time.
- Generated outputs.
- Review state.
- High-level reason for failure or waiting state.

Exact component versions should appear in a collapsible `Execution details` section.

## 6.2 Frozen state indication

The user should see a clear statement:

> This run used a frozen workflow state. Later workflow changes do not alter this run's provenance.

## 6.3 Re-run options

The UX shall distinguish:

- Re-run with the same frozen configuration.
- Run with the latest draft.
- Run with the current DEV release.
- Run with the current PROD release.

The selected option must be explicit before execution.

---

## 7. Output-Centric Experience

## 7.1 Output overview

An output page should display:

- Business name and type.
- Current approved baseline.
- Latest revision.
- Review status.
- Source workflow and run.
- Revision history.
- Actions: Compare, Regenerate, Upload revision, Review, Approve.

## 7.2 Revision presentation

Revision entries should use human-readable origin labels:

```text
Revision 1 — AI generated
Revision 2 — Edited by reviewer
Revision 3 — AI regenerated from updated RD
Revision 4 — Approved baseline
```

Technical IDs remain available in detail views.

## 7.3 Approval

Approving an output must clearly state:

- Which revision becomes baseline.
- Which previous baseline is superseded.
- Which workflow/run produced the revision.
- Whether unresolved warnings remain.

The baseline action must be explicit and auditable.

---

## 8. Activity Timeline

The default history representation should be an activity timeline rather than isolated version lists.

Example:

```text
10:15  RD source updated by BA
10:22  Writer prompt draft changed by Huy
10:28  Workflow 1.4.0 published to DEV
10:31  Test run completed
10:34  API Design F001 revision 3 generated
11:05  Reviewer uploaded revision 4
11:20  Revision 4 approved as baseline
```

Each timeline item should link to the relevant object while preserving a single chronological story.

Filters may include:

- Workflow changes.
- Runs.
- Outputs.
- Reviews and approvals.
- Environment promotions.

Raw audit logs remain a deeper administrative view and are not the default user history.

---

## 9. Explain Difference

`Explain Difference` is a primary user-facing capability backed by frozen manifests and lineage.

The comparison result should answer:

> Why is this output different from the other output?

Example:

```text
Output B differs from Output A because:

Changed
- RD source: revision 12 -> 13
- Writer prompt: version 7 -> 8

Unchanged
- Workflow topology: 1.3.0
- Agent: BD API Writer 1.2.0
- Model profile: High Accuracy Design 1
- Naming validator: 1.0.0

Human changes
- Output B contains reviewer edits after generation
```

The UI should classify differences into:

- Input changes.
- Workflow changes.
- Prompt changes.
- Agent/tool/model changes.
- Runtime configuration changes.
- Human edits.

A raw manifest diff may be available under `Technical details`.

---

## 10. Rollback and Restore Experience

Rollback should be expressed in user terms:

```text
Restore PROD to:
1.3.0 — Stable API generation
```

Before confirmation, show:

- Current PROD release.
- Target release.
- Meaningful differences.
- Known impact.
- Confirmation that historical runs and outputs remain unchanged.

Rollback moves an environment pointer; it does not delete newer releases.

For draft authoring, `Restore as new draft` should create a new mutable draft based on an earlier published version rather than modifying historical data.

---

## 11. Conceptual Information Architecture

This refinement does not prescribe the global navigation of Harness Hub. It defines contextual organization for this capability.

```text
Project context
└── Workflow
    ├── Design
    │   └── Nodes and embedded resources
    ├── Runs
    ├── Outputs
    ├── Activity
    └── Settings / published states
```

Objects such as Capability, Agent, Prompt, Tool, Release, Manifest, and Artifact remain first-class backend entities, but they should normally be reached through workflow, run, or output context.

Dedicated catalog or administrative views may exist for power users, reuse management, and governance administration. They are secondary paths, not the default journey.

---

## 12. UX Requirements

### UX-001 — Contextual versioning

Users shall be able to inspect and change prompt/agent configuration from the workflow node where it is used.

### UX-002 — Automatic draft versioning

Saving a changed definition shall preserve history without requiring manual version-number entry.

### UX-003 — Explicit publication

Publishing an immutable workflow release shall require an explicit action and change summary.

### UX-004 — Exact run provenance

Each run shall expose a readable configuration summary and an optional full manifest.

### UX-005 — Output history

Each business output shall show all immutable revisions and the active baseline.

### UX-006 — Activity timeline

Users shall be able to view workflow, run, output, review, and promotion events in one chronological timeline.

### UX-007 — Explain Difference

Users shall be able to compare two outputs or runs and receive categorized causes of change.

### UX-008 — Progressive disclosure

Internal IDs, hashes, external registry references, and raw manifests shall not dominate default screens.

### UX-009 — Meaningful release metadata

Published workflow states shall include a human-readable title, description, and change summary.

### UX-010 — Safe rollback

Users shall be able to restore an environment to an earlier release without modifying or deleting immutable history.

### UX-011 — Source clarity

Every revision shall indicate whether it was AI-generated, human-edited, regenerated, imported, or transformed.

### UX-012 — No duplicated management flow

Users shall not need to perform the same publish/version action independently in Harness Hub and MLflow.

---

## 13. POC UX Acceptance Scenarios

### AC-UX-01 — Edit prompt in workflow context

Given a workflow node uses prompt version 7, when a user edits and saves the prompt, then Harness Hub creates a draft prompt state and displays the workflow as changed without modifying version 7.

### AC-UX-02 — Publish workflow state

Given a valid workflow draft, when a user reviews and publishes it, then an immutable workflow release is created with a meaningful title and exact component references.

### AC-UX-03 — Run with frozen configuration

Given a published workflow release, when a run starts, then the user can see which release was used and can open the exact frozen execution details.

### AC-UX-04 — Review revision chain

Given an AI-generated output followed by a human-edited upload, when the user opens the output, then both revisions are shown chronologically with their origin and only one may be the active baseline.

### AC-UX-05 — Explain output change

Given two outputs generated from manifests that differ only by RD revision and prompt version, when the user selects Explain Difference, then the UI identifies those two changes and reports workflow, agent, tool, and model as unchanged.

### AC-UX-06 — Roll back production

Given PROD points to release 1.4.0, when an authorized user restores PROD to 1.3.0, then the pointer changes, the action is recorded, and runs generated under 1.4.0 remain unchanged and accessible.

### AC-UX-07 — Progressive detail

Given a user opens a run, then the default view shows workflow, input, output, and status; exact prompt/tool IDs and hashes are available only through execution details.

---

## 14. ADR-009 — Workflow-Centric UX over Asset-Centric UX

### Status

Accepted for POC v1.1.

### Context

The governance backend requires asset-level entities and immutable version references. Presenting these entities as the primary navigation would force users to coordinate prompts, agents, releases, runs, and artifacts manually and would not match how they perform RD-to-BD work.

### Decision

Harness Hub shall preserve an asset-centric backend model while presenting a workflow-centric user experience centered on Project, Workflow, Run, Output, and History.

Asset catalogs and technical detail remain available through progressive disclosure and administrative views.

### Consequences

Positive:

- Lower cognitive load.
- Faster workflow editing and testing.
- Versioning becomes an automatic platform behavior.
- Provenance is available without dominating the interface.
- Output comparison aligns with user questions.

Trade-offs:

- The frontend must aggregate data from multiple domain entities.
- Deep links and permission checks must preserve object-level governance.
- Power users still require catalog and technical inspection paths.

---

## 15. Relationship to Architecture v1.0

This document refines user interaction only.

It does not change:

- Harness Hub as control plane.
- LangGraph as initial execution runtime.
- MLflow ownership of prompt versions, traces, experiments, and evaluations.
- Git ownership of source code.
- Object storage ownership of file blobs.
- Capability, Agent Version, Workflow Release, Frozen Run Manifest, Artifact Revision, and Baseline domain concepts.
- Immutability, idempotency, outbox, or system-of-record rules.

Implementation specifications shall treat this document as the UX companion to the approved architecture baseline.
