# Domain Model

> Superseded by `../../design/D02_DOMAIN_AND_WORKFLOW_CONTRACTS.md`.

**Document type:** Architecture Guideline  
**Version:** 0.1

## 1. Aggregate

- `Workspace`
- `WorkflowDefinition` và `WorkflowVersion`
- `WorkflowRun`
- `NodeRun` và `NodeAttempt`
- `AgentDefinition` và `AgentVersion`
- `SkillDefinition` và `SkillVersion`
- `Artifact` và `ArtifactVersion`
- `ReviewRequest` và `ReviewResult`

## 2. Quan hệ

```mermaid
erDiagram
    WORKSPACE ||--o{ WORKFLOW_DEFINITION : contains
    WORKSPACE ||--o{ AGENT_DEFINITION : contains
    WORKSPACE ||--o{ ARTIFACT : contains
    WORKFLOW_DEFINITION ||--o{ WORKFLOW_VERSION : versions
    WORKFLOW_VERSION ||--o{ WORKFLOW_RUN : instantiated_as
    WORKFLOW_RUN ||--o{ NODE_RUN : contains
    NODE_RUN ||--o{ NODE_ATTEMPT : retries
    AGENT_DEFINITION ||--o{ AGENT_VERSION : versions
    AGENT_VERSION }o--o{ SKILL_VERSION : uses
    ARTIFACT ||--o{ ARTIFACT_VERSION : versions
    ARTIFACT_VERSION ||--o{ REVIEW_REQUEST : reviewed_by
```

## 3. Node types

`INPUT`, `ORCHESTRATOR`, `AGENT`, `REVIEWER`, `GATE`, `AGGREGATE`, `TOOL`, `OUTPUT`, `HUMAN_APPROVAL`.

## 4. Run states

`CREATED`, `QUEUED`, `RUNNING`, `WAITING_FOR_REVIEW`, `WAITING_FOR_USER`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`.

## 5. Reviewer verdict

`GO`, `NO_GO_REPAIRABLE`, `NO_GO_BLOCKING`, `NEED_USER_DECISION`.

## 6. Orchestrator action

`EXECUTE_NODE`, `CONTINUE`, `RETRY_NODE`, `REROUTE_NODE`, `ADD_CONTEXT`, `CHANGE_EXECUTOR`, `REQUEST_USER_INPUT`, `PAUSE_RUN`, `STOP_RUN`.

## 7. Invariants

- Artifact Version là immutable.
- Run phải tham chiếu đúng workflow version.
- Archived artifact vẫn giữ lineage.
- Reviewer không sửa workflow state trực tiếp.
- Orchestrator không được vượt Policy Engine.
