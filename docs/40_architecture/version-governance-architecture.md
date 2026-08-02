# Harness Hub Versioning Subsystem — Implementation Architecture

**Status:** Revised POC architecture  
**Version:** 0.2  
**Scope:** Integration into the existing Harness Hub application  
**Primary use case:** RD-to-BD generation and Basic Design artifact governance  
**Audience:** System architects, AI platform engineers, backend engineers, workflow engineers, coding agents

---

## 1. Executive Decision

The organization already has a **Harness Hub application**. Therefore, the POC shall not introduce a separate standalone Harness Registry product or a second control-plane UI.

The recommended architecture is to add a bounded **Versioning and Artifact Governance subsystem** inside Harness Hub, while reusing specialized platforms for workflow execution, prompt lifecycle, tracing, evaluation, and binary storage.

```text
Existing Harness Hub
+ Versioning and Artifact Governance module
+ LangGraph Runtime Adapter
+ LangGraph OSS / Agent Server
+ MLflow 3
+ PostgreSQL
+ MinIO or existing S3-compatible storage
+ Git
```

The architecture follows four decisions:

1. **Harness Hub remains the host application and user-facing control plane.**
2. **LangGraph remains the initial execution engine, not the business system of record.**
3. **MLflow owns prompt versions, experiments, traces, and evaluation references.**
4. **Harness Hub owns capability composition, agent/workflow releases, frozen run manifests, artifact revision chains, and approved baselines.**

This is an integration architecture, not a greenfield platform build.

---

## 2. Context and Problem Statement

Harness Hub already provides the surrounding application shell, user experience, workspace context, authentication, model/tool access, and orchestration entry points. The missing capability is a consistent mechanism to answer, for every AI-generated delivery artifact:

1. Which capability, agent, and workflow release generated it?
2. Which exact prompt versions were resolved at execution time?
3. Which tools, model profile, and source-code commit were used?
4. Which RD files or knowledge snapshot were used?
5. Which runtime executed the workflow and where is its checkpoint state?
6. Which output revision was AI-generated, human-edited, regenerated, or imported?
7. Which revision is the active approved project baseline?
8. Why does one output differ from another?

Git alone cannot answer runtime provenance. LangGraph manages workflow execution but should not own prompt publication, release promotion, or BD baselines. MLflow provides strong prompt, trace, experiment, and evaluation capabilities but does not model project artifact revisions, delivery baselines, or reusable business capabilities as first-class Harness concepts.

The new subsystem fills these gaps **inside Harness Hub**.

---

## 3. Revised Architectural Position

### 3.1 Previous interpretation

The original proposal treated the Thin Harness Registry as a small standalone control-plane application with its own UI and API.

### 3.2 Revised interpretation

The existing Harness Hub is already the control plane. The proposed registry functions become internal modules and APIs of Harness Hub:

```text
Harness Hub Control Plane
├── Workspace and Project Context
├── Chat and Task Entry Points
├── Model and Tool Gateway
├── Skill and Workflow Activation
├── Capability Catalog
├── Agent and Workflow Release Management
├── Run Manifest and Lineage
├── Artifact Revision and Baseline Governance
└── Runtime Adapter Ports
```

The subsystem shall reuse Harness Hub authentication, workspace isolation, navigation, configuration, audit identity, and API conventions wherever these already exist.

It shall not duplicate:

- Login or identity management.
- Workspace/project master data.
- Existing model-provider integration.
- Existing tool gateway.
- Existing chat or task UI.
- Existing generic audit infrastructure, when suitable.
- Existing object storage integration, when suitable.

---

## 4. Target Architecture

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                         Existing Harness Hub UI                          │
│                                                                          │
│ Chat | Projects | Capabilities | Agents | Workflows | Runs | Artifacts  │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    Harness Hub Control Plane API                         │
│                                                                          │
│ Existing modules                         New bounded subsystem            │
│ ├── Identity / Workspace                 ├── Capability Catalog           │
│ ├── Model Gateway                        ├── Agent Version Service        │
│ ├── Tool Gateway                         ├── Workflow Release Service     │
│ ├── Chat / Task Service                  ├── Environment Mapping          │
│ └── Existing Audit                       ├── Run Manifest Service         │
│                                          ├── Artifact Revision Service   │
│                                          ├── Baseline Approval           │
│                                          └── Lineage Query Service       │
└───────────────┬───────────────────┬───────────────────┬──────────────────┘
                │                   │                   │
                ▼                   ▼                   ▼
        Runtime Adapter Port      MLflow 3        Object Storage
                │             prompts, traces,    MinIO / S3
                │             eval references     immutable files
                ▼
      LangGraph Runtime Adapter
                │
                ▼
      LangGraph OSS / Agent Server
      threads, runs, checkpoints
                │
                ▼
     Harness Hub Model and Tool Gateways
```

### 4.1 Control plane

Harness Hub is authoritative for:

- Workspace and project context.
- Capability definitions and versions.
- Agent versions.
- Workflow releases.
- Environment-to-release mappings.
- Frozen run manifests.
- Artifact business identity and revision chains.
- Human approvals and active baseline pointers.
- Cross-system lineage references.

### 4.2 Execution plane

LangGraph is responsible for:

- Graph execution.
- State transitions inside the graph.
- Conditional routing.
- Checkpoints.
- Human interrupts and resume operations.
- Node-level retry behavior.
- Runtime thread/run identifiers.

### 4.3 Observability and experiment plane

MLflow is responsible for:

- Prompt Registry.
- Immutable prompt versions.
- Prompt aliases for authoring and experimentation.
- Experiment runs.
- Traces and spans.
- Evaluation datasets and results.
- Auxiliary experiment artifacts.

### 4.4 Artifact storage plane

MinIO, S3, or the existing Harness Hub object store is responsible for immutable file blobs. Harness Hub stores business metadata, content hashes, and storage references.

---

## 5. Architecture Principles

### 5.1 Integrate before creating a new service

A new deployable service shall be created only when Harness Hub module boundaries, scaling, security, or release cadence require it. The POC should start as a modular subsystem in the current backend.

### 5.2 Domain model must not depend on LangGraph classes

Harness Hub domain entities shall use runtime-neutral identifiers and contracts. LangGraph-specific payloads remain inside the LangGraph adapter.

### 5.3 One owner per state category

The same lifecycle shall not be independently maintained in Harness Hub, LangGraph, and MLflow.

### 5.4 Immutable published versions

Published capability versions, agent versions, workflow releases, frozen run manifests, and artifact revisions are immutable.

### 5.5 Mutable pointers, immutable targets

Environment mappings and active baseline pointers may change. Their target releases and revisions remain immutable.

```text
PROD -> workflow release 1.3.0
BD baseline -> artifact revision 4
```

### 5.6 Exact runtime resolution

Aliases may be used while authoring, but a run must store exact immutable component versions.

### 5.7 Fail closed for production execution

A production run must not start when mandatory references cannot be resolved, are revoked, or fail validation.

### 5.8 Capability is the smallest reusable business unit

A workflow is a composition of capabilities. An agent is an execution configuration that realizes one or more capabilities. This avoids treating an agent as the only reuse boundary.

### 5.9 Avoid speculative platform abstractions

The design shall introduce a runtime port and capability model, but the POC implements only one runtime adapter and only the capability behaviors needed by RD-to-BD.

---

## 6. Core Concepts

## 6.1 Capability

A capability describes a reusable business or delivery ability, independent of a particular workflow topology.

Examples:

- Parse RD source.
- Extract API requirements.
- Generate API Basic Design.
- Review naming conventions.
- Validate traceability.
- Produce Excel delivery package.

A capability version declares:

- Input contract.
- Output contract.
- Required resources.
- Quality criteria.
- Compatible agent implementations.
- Optional evaluation references.

Capability does not directly execute. It is realized by an Agent Version or workflow node binding.

## 6.2 Agent Version

An immutable executable composition containing:

- Source-code reference.
- Agent entrypoint.
- Capability versions implemented.
- Exact prompt-version references.
- Tool-version references.
- Model profile.
- Runtime limits.
- Input/output schema references.

## 6.3 Workflow Release

An immutable deployable package containing:

- Workflow source reference.
- Graph entrypoint.
- State-schema version.
- Capability bindings.
- Agent-version bindings.
- Runtime configuration.
- Required model and tool policies.

## 6.4 Frozen Run Manifest

A resolved snapshot generated by Harness Hub before execution. It records exact component versions, input snapshot, selected runtime, model/tool references, and integration identifiers.

## 6.5 Artifact and Artifact Revision

An Artifact is the stable business identity of an output, such as `API Design / Function F001`.

An Artifact Revision is immutable content produced by:

- AI generation.
- Human editing.
- AI regeneration.
- Import.
- System transformation.

## 6.6 Approved Baseline

A mutable pointer to one approved Artifact Revision for a defined artifact business key.

## 6.7 Knowledge Snapshot

For the POC, a knowledge snapshot is intentionally minimal:

- Snapshot ID.
- Source URI or source identifiers.
- Source version or timestamp when available.
- Content hash or manifest hash.
- Created time.

Ontology, vector-index, and graph snapshots remain outside this POC unless the existing Harness Hub already exposes them.

---

## 7. System-of-Record Ownership

| Information | System of record |
|---|---|
| User, workspace, project | Existing Harness Hub |
| Workflow and agent source code | Git |
| Capability definitions and versions | Harness Hub |
| Agent versions and manifests | Harness Hub |
| Workflow releases | Harness Hub |
| Environment-to-release mapping | Harness Hub |
| Frozen run manifest | Harness Hub |
| Runtime thread, checkpoint, node state | LangGraph |
| Prompt versions | MLflow Prompt Registry |
| Traces and evaluation results | MLflow |
| Artifact business identity and revisions | Harness Hub |
| Artifact binary content | MinIO/S3/existing object storage |
| Approved baseline | Harness Hub |
| Model execution | Existing Harness Hub model gateway |
| Tool execution and permissions | Existing Harness Hub tool gateway |

A Harness Hub run record references MLflow and LangGraph identifiers but does not duplicate their complete internal state.

---

## 8. Runtime Abstraction

Harness Hub shall depend on a runtime-neutral port rather than LangGraph SDK types.

```python
class WorkflowRuntimePort(Protocol):
    async def start(self, request: StartRunRequest) -> RuntimeRunRef: ...
    async def resume(self, request: ResumeRunRequest) -> RuntimeRunRef: ...
    async def cancel(self, request: CancelRunRequest) -> None: ...
    async def get_status(self, runtime_run_id: str) -> RuntimeStatus: ...
    async def get_checkpoint(self, runtime_run_id: str) -> CheckpointRef: ...
```

The POC implements:

```text
WorkflowRuntimePort
└── LangGraphRuntimeAdapter
```

The architecture does not require a second runtime. The port exists to prevent LangGraph objects, status names, and persistence schemas from leaking into the Harness Hub domain.

### 8.1 Canonical runtime statuses

Harness Hub uses its own canonical execution statuses:

```text
CREATED
QUEUED
RUNNING
WAITING_APPROVAL
SUCCEEDED
FAILED
CANCELLED
TIMED_OUT
```

The adapter maps LangGraph runtime state into these statuses.

### 8.2 Runtime events

Runtime events sent to Harness Hub must include:

- Event ID.
- Harness run ID.
- Runtime run ID.
- Event type.
- Occurred time.
- Runtime status.
- Optional checkpoint reference.
- Optional artifact registration reference.
- Idempotency key or sequence version.

Duplicate and late events must not silently overwrite terminal state.

---

## 9. Harness Hub Module Boundaries

The new code should be organized as a bounded module rather than scattered through chat, workflow, and artifact controllers.

```text
modules/version_governance/
├── capabilities/
├── agents/
├── workflow_releases/
├── environments/
├── runs/
├── artifacts/
├── approvals/
├── lineage/
├── runtime_ports/
├── integrations/
│   ├── langgraph/
│   ├── mlflow/
│   └── object_storage/
└── audit/
```

If the existing Harness Hub uses different naming conventions, preserve its conventions while maintaining the same ownership boundaries.

### 9.1 Existing modules reused

The subsystem should call existing Harness Hub modules for:

- Workspace/project authorization.
- Model-provider access.
- Tool permissions and invocation.
- Secrets.
- Authentication.
- Common audit actor identity.
- Notifications when available.

### 9.2 Modules not created in the POC

Do not create:

- A second user-management service.
- A second model gateway.
- A second tool registry when Harness Hub already has one.
- A separate workflow designer.
- A generic marketplace.
- A new message bus solely for this subsystem.

---

## 10. Minimal Domain Model

```text
Workspace                  existing Harness Hub entity
└── Project                existing Harness Hub entity
    ├── Capability
    │   └── CapabilityVersion
    ├── Agent
    │   └── AgentVersion
    ├── Workflow
    │   └── WorkflowRelease
    ├── Environment
    │   └── ActiveWorkflowRelease
    ├── ExecutionRun
    │   └── FrozenRunManifest
    └── Artifact
        ├── ArtifactRevision
        └── BaselinePointer
```

### 10.1 Capability version example

```yaml
capability_id: generate-api-basic-design
version: 1.0.0
status: PUBLISHED
input_schema: rd-api-requirement/v1
output_schema: api-basic-design/v2
quality_rules:
  - complete-required-sections
  - preserve-source-traceability
implemented_by:
  - agent: bd-api-writer
    minimum_version: 1.2.0
```

### 10.2 Agent version example

```yaml
agent_id: bd-api-writer
version: 1.2.0
status: PUBLISHED
capabilities:
  - generate-api-basic-design@1.0.0
source:
  repository: lechihuy-droid/bd-runtime
  commit: e6a42f1
  entrypoint: agents.bd_api_writer:agent
prompts:
  system:
    registry: mlflow
    name: bd-api-system
    version: 4
  drafting:
    registry: mlflow
    name: bd-api-drafting
    version: 7
tools:
  - tool_id: rd-reader
    version: 1.0.0
model_profile:
  id: high-accuracy-design
  version: 1
runtime:
  max_iterations: 5
  timeout_seconds: 600
output_schema: api-basic-design/v2
```

### 10.3 Workflow release example

```yaml
workflow_id: rd-to-bd-api
release_version: 1.3.0
status: PUBLISHED
source:
  repository: lechihuy-droid/bd-runtime
  commit: a8c917f
  entrypoint: workflows.rd_to_bd_api:graph
runtime:
  adapter: langgraph
  state_schema: rd-to-bd-state/v2
  max_run_seconds: 1800
bindings:
  parse_rd:
    capability: parse-rd-source@1.0.0
    agent: rd-parser@1.1.0
  generate_bd:
    capability: generate-api-basic-design@1.0.0
    agent: bd-api-writer@1.2.0
  review_bd:
    capability: review-api-basic-design@1.0.0
    agent: bd-reviewer@1.0.0
```

### 10.4 Frozen run manifest example

```json
{
  "run_id": "run_01J...",
  "workspace_id": "ws_bd",
  "project_id": "project_bd_poc",
  "environment": "PROD",
  "workflow": {
    "id": "rd-to-bd-api",
    "release_version": "1.3.0",
    "git_commit": "a8c917f"
  },
  "capabilities": {
    "generate_bd": "generate-api-basic-design@1.0.0"
  },
  "agents": {
    "generate_bd": "bd-api-writer@1.2.0"
  },
  "prompts": {
    "bd-api-system": 4,
    "bd-api-drafting": 7
  },
  "tools": {
    "rd-reader": "1.0.0"
  },
  "model_profile": "high-accuracy-design@1",
  "knowledge_snapshot": {
    "id": "ks_01J...",
    "manifest_hash": "sha256:..."
  },
  "runtime": {
    "type": "langgraph",
    "runtime_run_id": null,
    "thread_id": null,
    "checkpoint_ref": null
  },
  "observability": {
    "mlflow_run_id": null,
    "mlflow_trace_id": null
  }
}
```

Resolved component fields are immutable. Runtime and observability references may be appended through dedicated integration records without mutating the resolved release content.

---

## 11. Minimal Persistence Model

Reuse the existing Harness Hub PostgreSQL database for the POC unless isolation or operational constraints require a separate database.

Recommended tables:

```text
capability
capability_version
agent
agent_version
agent_capability
workflow
workflow_release
workflow_release_binding
environment_release
execution_run
run_component
runtime_reference
knowledge_snapshot
artifact
artifact_revision
artifact_baseline
approval
audit_event or existing audit table
outbox_event
```

Existing `workspace` and `project` tables must be referenced rather than recreated.

### 11.1 Core constraints

1. Published versions and releases are immutable.
2. `capability_version(capability_id, version)` is unique.
3. `agent_version(agent_id, version)` is unique.
4. `workflow_release(workflow_id, release_version)` is unique.
5. One active release exists per project and environment.
6. Run idempotency key is unique within project scope.
7. Every run component uses an exact version.
8. Artifact revision numbers are unique within an artifact.
9. Only one active baseline exists per artifact business key.
10. Every persisted content blob has a SHA-256 hash.

### 11.2 Run component representation

```text
run_component
-------------
run_id
component_type
component_id
component_version
component_hash
external_registry
external_reference
```

Component types:

```text
WORKFLOW
CAPABILITY
AGENT
PROMPT
TOOL
MODEL_PROFILE
STATE_SCHEMA
KNOWLEDGE_SNAPSHOT
```

---

## 12. Integration Contracts

## 12.1 Harness Hub to MLflow

Harness Hub must be able to:

- Resolve a prompt name and version.
- Validate that an exact prompt version exists.
- Retrieve prompt metadata required for manifest display.
- Store MLflow run and trace IDs.
- Link evaluation results to a Harness run or release candidate.

Harness Hub shall not copy complete trace payloads into its relational database.

## 12.2 Harness Hub to LangGraph

The LangGraph adapter must be able to:

- Start a run from a frozen manifest.
- Resume a paused run.
- Cancel a run.
- Retrieve normalized status.
- Retrieve thread/run/checkpoint references.
- Receive or poll terminal status.
- Register output artifact references.

## 12.3 Harness Hub to object storage

The artifact service must support:

- Upload intent or signed upload URL.
- Content hash verification.
- Immutable object key.
- Metadata registration after successful upload.
- Authorized download.
- Optional existing malware/quarantine pipeline reuse.

Recommended key pattern:

```text
{workspace_id}/{project_id}/{artifact_business_key}/{revision_id}/{filename}
```

## 12.4 Harness Hub model and tool gateways

LangGraph nodes shall invoke models and approved tools through Harness Hub gateways where technically feasible. This preserves existing provider abstraction, permission policy, logging, and cost controls.

Direct provider access from a workflow should be treated as a documented exception.

---

## 13. Main Execution Flow

```text
User starts RD-to-BD from Harness Hub
  -> Harness Hub resolves project and environment
  -> Environment resolves exact Workflow Release
  -> Release resolves Capability and Agent Versions
  -> Agent Versions resolve exact MLflow Prompt Versions
  -> Harness Hub validates tool and model access
  -> Harness Hub freezes Run Manifest
  -> LangGraph Runtime Adapter starts execution
  -> LangGraph executes through Harness model/tool gateways
  -> MLflow records trace and evaluation references
  -> Runtime registers generated Artifact Revision
  -> Harness Hub records lineage and terminal status
  -> Reviewer creates or uploads Human Revision
  -> Reviewer approves revision
  -> Harness Hub atomically moves Baseline Pointer
```

### 13.1 Run authority

Harness Hub owns the business run lifecycle. LangGraph owns runtime execution state.

LangGraph events request or report transitions; Harness Hub validates and persists canonical transitions.

### 13.2 Frozen manifest rule

No runtime adapter may replace resolved workflow, capability, agent, prompt, tool, model-profile, or knowledge-snapshot versions after execution starts.

---

## 14. State Models

### 14.1 Capability, agent, and workflow publication

```text
DRAFT -> IN_REVIEW -> PUBLISHED
                   -> REJECTED

PUBLISHED -> DEPRECATED -> ARCHIVED
PUBLISHED -> REVOKED
```

`DEV` and `PROD` are environment mappings, not version lifecycle states.

### 14.2 Run lifecycle

```text
CREATED -> QUEUED -> RUNNING
RUNNING -> WAITING_APPROVAL
RUNNING -> SUCCEEDED
RUNNING -> FAILED
RUNNING -> CANCELLED
RUNNING -> TIMED_OUT
WAITING_APPROVAL -> RUNNING
WAITING_APPROVAL -> FAILED
WAITING_APPROVAL -> CANCELLED
```

Terminal states:

```text
SUCCEEDED
FAILED
CANCELLED
TIMED_OUT
```

Late events after a terminal state are retained for audit but do not silently replace the terminal state.

### 14.3 Artifact revision lifecycle

```text
CREATED -> IN_REVIEW -> APPROVED
                     -> REJECTED
APPROVED -> SUPERSEDED
```

Approval and baseline selection remain separate operations.

---

## 15. Harness Hub API Extensions

These paths are illustrative and should follow existing Harness Hub conventions.

### 15.1 Capabilities

```text
POST /projects/{projectId}/capabilities
POST /capabilities/{capabilityId}/versions
POST /capability-versions/{versionId}/publish
GET  /capabilities/{capabilityId}/versions
```

### 15.2 Agent versions

```text
POST /projects/{projectId}/agents
POST /agents/{agentId}/versions
POST /agent-versions/{versionId}/publish
GET  /agent-versions/{versionId}
```

### 15.3 Workflow releases

```text
POST /projects/{projectId}/workflows
POST /workflows/{workflowId}/releases
POST /workflow-releases/{releaseId}/publish
PUT  /projects/{projectId}/environments/{environment}/release
```

### 15.4 Runs

```text
POST /projects/{projectId}/runs
GET  /runs/{runId}
POST /runs/{runId}/resume
POST /runs/{runId}/cancel
POST /runs/{runId}/runtime-events
GET  /runs/{runId}/lineage
POST /runs/compare
```

### 15.5 Artifacts

```text
POST /projects/{projectId}/artifacts
POST /artifacts/{artifactId}/revisions
POST /artifact-revisions/{revisionId}/approve
PUT  /artifacts/{artifactId}/baseline
GET  /artifacts/{artifactId}/revisions
```

---

## 16. UI Integration into Harness Hub

Do not build a separate registry UI. Add focused views into existing Harness Hub navigation.

Minimum POC UI:

1. **Capability and Agent Catalog** — version list and dependencies.
2. **Workflow Release Detail** — bindings and environment mapping.
3. **Run Detail** — frozen manifest, LangGraph reference, MLflow trace link, generated artifacts.
4. **Artifact Revision View** — revision history, source run, approval, and active baseline.
5. **Manifest Comparison** — differences between two runs or releases.

Existing chat or task screens should display the active workflow release and resulting artifact revision without reproducing the full governance UI.

---

## 17. Deployment Topology

### 17.1 Preferred POC topology

```text
Existing Harness Hub frontend
Existing Harness Hub backend
  └── Versioning and Artifact Governance module
Existing PostgreSQL
Existing model/tool gateways
LangGraph Agent Server
MLflow server
MinIO or existing S3-compatible storage
```

### 17.2 Separate-service extraction criteria

Extract the subsystem into a separate service only when one or more conditions become true:

- Independent release cadence is required.
- Lineage queries materially affect Harness Hub latency.
- Runtime events require independent scaling.
- Security policy requires isolated storage or credentials.
- Multiple applications consume the registry domain.
- Ownership moves to a separate platform team.

Until then, a modular monolith boundary is preferred.

---

## 18. Reliability and Consistency

### 18.1 Idempotency

Run creation and runtime event ingestion require idempotency keys.

### 18.2 Optimistic concurrency

Use a version column or equivalent for:

- Run-state transitions.
- Environment-release pointer changes.
- Baseline pointer changes.

### 18.3 Transactional outbox

Use the existing Harness Hub outbox when available. Otherwise add an `outbox_event` table for reliable publication of:

- Release promoted.
- Run created.
- Run completed.
- Artifact revision created.
- Baseline changed.

Kafka, NATS, or another event broker is not required for the POC.

### 18.4 Integration degradation

- If MLflow is unavailable, production release validation and production execution requiring prompt resolution must fail closed.
- If LangGraph is unavailable, run creation may remain `QUEUED` only when queue semantics are explicitly supported; otherwise fail before execution.
- If object storage is unavailable, artifact revision registration must not report success.
- Historical Harness Hub metadata must remain queryable when external systems are temporarily unavailable.

---

## 19. Security and Isolation

Reuse Harness Hub authorization and project isolation.

The subsystem must enforce:

- Workspace/project ownership on every command and query.
- Role checks for publish, promote, approve, and baseline changes.
- Short-lived object-storage access.
- Secret references rather than raw secrets in manifests.
- Audit actor, time, previous target, and new target for pointer changes.
- Tool permission validation before starting production execution.
- No direct LangGraph access to production databases unless exposed through approved Harness Hub tools or connectors.

Artifact upload should reuse existing malware scanning, MIME validation, size limits, and quarantine capability when available.

---

## 20. POC Scope

### 20.1 In scope

- Integration into one existing Harness Hub deployment.
- One workspace model already supplied by Harness Hub.
- Project-scoped capability, agent, workflow release, run, and artifact records.
- Prompt version resolution through MLflow.
- One LangGraph runtime adapter.
- One RD-to-BD workflow.
- Basic capability bindings.
- Frozen run manifests.
- Artifact revision chain and one active baseline.
- Basic lineage and manifest comparison.
- Existing model/tool gateway reuse.
- Outbox-based integration events.

### 20.2 Out of scope

- Standalone registry application.
- A second Harness UI.
- Multiple runtime implementations.
- Generic runtime marketplace.
- Visual workflow builder.
- Graph database.
- Bidirectional Git synchronization.
- General-purpose policy engine.
- Complex ontology snapshot management.
- Cross-workspace asset sharing.
- Embedded Excel/PDF co-authoring.
- Custom trace backend.
- Custom evaluation execution engine.
- Kafka or Temporal solely for this POC.

---

## 21. Implementation Phases

### Phase 0 — Harness Hub integration discovery

- Map existing Harness Hub modules.
- Identify existing workspace/project, model gateway, tool gateway, audit, object store, and job abstractions.
- Record integration decisions as ADRs.
- Confirm whether MLflow and LangGraph will run locally or as managed services.

**Exit:** No duplicate subsystem is planned for an existing Harness capability.

### Phase 1 — Domain and persistence foundation

- Capability and Capability Version.
- Agent and Agent Version.
- Workflow and Workflow Release.
- Environment mapping.
- Immutable version validation.
- Existing authorization integration.

**Exit:** A release can bind exact capability, agent, prompt, tool, and source versions.

### Phase 2 — Runtime integration

- Runtime port.
- LangGraph adapter.
- Frozen run manifest.
- Idempotent run creation.
- Runtime event normalization.
- LangGraph and MLflow references.

**Exit:** Harness Hub can start and track one RD-to-BD run without leaking LangGraph domain objects.

### Phase 3 — Artifact governance

- Artifact and revisions.
- Object-store integration.
- Human revision upload.
- Approval.
- Atomic baseline switch.
- Basic lineage.

**Exit:** A generated BD can be revised and approved while preserving complete history.

### Phase 4 — Comparison and hardening

- Run-manifest comparison.
- Release comparison.
- Revocation checks.
- Outbox worker.
- Recovery and integration-failure tests.
- POC dashboards and audit views.

**Exit:** The POC satisfies all acceptance criteria.

---

## 22. Acceptance Criteria

### AC-01 — No duplicate control plane

Given the existing Harness Hub, when the subsystem is deployed, then users access capability, release, run, and artifact governance through Harness Hub rather than a separate application.

### AC-02 — Capability binding

Given a published capability version and compatible agent version, when a workflow release is published, then the release stores exact immutable capability and agent references.

### AC-03 — Runtime neutrality

Given a Harness Hub run, when LangGraph executes it, then Harness Hub records only canonical runtime status and adapter-owned external references; no LangGraph class or persistence object is required by the core domain.

### AC-04 — Exact prompt resolution

Given an MLflow prompt alias, when a run is frozen, then the manifest stores the exact MLflow prompt version rather than only the alias.

### AC-05 — Frozen release resolution

Given an environment mapped to workflow release 1.3.0, when a run starts, then all capability, agent, prompt, tool, model, source, and knowledge references are persisted before runtime execution.

### AC-06 — Existing gateway reuse

Given a LangGraph node requiring an LLM or tool, when it executes, then it uses the Harness Hub model/tool gateway unless an approved exception is recorded.

### AC-07 — Artifact lineage

Given an artifact revision, when lineage is requested, then Harness Hub displays its source run, workflow release, capability and agent versions, prompt versions, knowledge snapshot, runtime reference, and MLflow trace reference.

### AC-08 — Human revision

Given an AI-generated revision, when a reviewer uploads a modified document, then a new immutable revision is created with `HUMAN_EDITED` origin and a parent revision reference.

### AC-09 — Atomic baseline change

Given an approved new revision and an existing baseline, when an authorized reviewer changes the baseline, then only one active baseline exists and the previous baseline remains historical.

### AC-10 — Manifest comparison

Given two outputs created by different runs, when compared, then Harness Hub identifies changed workflow, capability, agent, prompt, tool, model-profile, source commit, or knowledge-snapshot references.

### AC-11 — Fail closed

Given a missing or revoked mandatory version reference, when a production run is requested, then Harness Hub rejects the run before calling LangGraph.

### AC-12 — Idempotent runtime events

Given the same LangGraph completion event delivered more than once, when Harness Hub processes it, then business state and artifact metadata are not duplicated.

---

## 23. Code-Size Guardrail

Because Harness Hub already exists, the incremental production-code target should be lower than the previous standalone estimate.

| Area | Incremental production LOC |
|---|---:|
| Harness Hub backend modules | 4,000–7,000 |
| Harness Hub UI extensions | 2,000–4,000 |
| LangGraph adapter and workers | 1,500–3,000 |
| MLflow and object-store integration | 1,000–2,000 |
| Migrations/configuration | 500–1,000 |
| **Total incremental production code** | **9,000–17,000** |

Test code target:

```text
7,000–14,000 LOC
```

If implementation exceeds approximately 17,000 production LOC for this POC, review for:

- Duplicating Harness Hub functionality.
- Building generic policy or asset frameworks.
- Over-generalizing runtime support.
- Building custom MLflow, tracing, or storage behavior.
- Expanding UI beyond the five required views.

LOC is a scope guardrail, not a quality target.

---

## 24. ADRs Required Before Coding

1. **ADR-001 — Harness Hub module integration boundary.**
2. **ADR-002 — Capability versus agent responsibilities.**
3. **ADR-003 — Harness Hub versus LangGraph run-state ownership.**
4. **ADR-004 — MLflow prompt and evaluation ownership.**
5. **ADR-005 — Object storage reuse versus dedicated MinIO.**
6. **ADR-006 — Existing model/tool gateway invocation from LangGraph.**
7. **ADR-007 — Existing audit/outbox reuse.**
8. **ADR-008 — Criteria for future service extraction.**

---

## 25. Final Recommendation

Implement the proposal as an internal **Versioning and Artifact Governance subsystem of Harness Hub**, not as a separate product.

The recommended POC stack is:

```text
Existing Harness Hub
├── Capability Catalog
├── Agent Version Management
├── Workflow Release Management
├── Frozen Run Manifests
├── Artifact Revision and Baseline Governance
└── Runtime Adapter Port

External / specialized components
├── Git                     source versioning
├── LangGraph Agent Server  workflow execution and checkpoints
├── MLflow 3                prompt versions, traces, evaluations
└── MinIO / S3              immutable artifact content
```

This design incorporates the two-SA debate without over-expanding the POC:

- **Capability** becomes a first-class reusable business unit.
- **LangGraph** is isolated behind a small runtime adapter.
- **Harness Hub** is explicitly the control plane and host application.
- **MLflow** is reused rather than replicated.
- **Knowledge Snapshot** remains minimal but traceable.
- **PostgreSQL** remains sufficient; no graph database is introduced.
- **Transactional outbox** is used before introducing an event broker.
- **Release** remains the deployable unit.
- **Artifact Revision** remains the immutable delivery-history unit.

The architecture is intentionally extensible but implements only one runtime, one delivery workflow, and the minimum governance needed to prove reproducibility and controlled BD output lifecycle.