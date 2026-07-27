# Coding Agent Implementation Plan

> Superseded by `../../design/D08_TEST_AND_IMPLEMENTATION_PLAN.md`.

**Document type:** Implementation Spec  
**Version:** 0.1

## 1. Quy tắc task

Mỗi task phải có objective, docs to read, allowed files, forbidden changes, acceptance criteria, tests và expected output.

## 2. Phase 0 — Foundation

- Repository structure.
- Config, logging, test, lint/type-check.
- Health endpoint và CI.

## 3. Phase 1 — Domain & Persistence

- Implement entities và repositories.
- Database migrations.
- Artifact/version/archive.

## 4. Phase 2 — Runtime Core

- State machine.
- Run coordinator.
- Event append và idempotency.
- Dependency scheduler.
- Pause/resume/cancel/recovery.

## 5. Phase 3 — Executor Contract

- Typed request/result/error.
- Executor port.
- Mock executor.
- Golden workflow chạy bằng mock.

## 6. Phase 4 — API Executor

- Provider adapter 1.
- Streaming, timeout, cancel, usage.
- Provider adapter 2 để chứng minh abstraction.

## 7. Phase 5 — CLI Executor

- Process supervisor.
- Sandbox workspace.
- File diff và output collection.

## 8. Phase 6 — Review & Orchestrator

- Review manager.
- Human review task.
- Orchestrator bridge và action allow-list.

## 9. Phase 7 — API/UI Integration

- Workflow, run, artifact và event stream APIs.

## 10. Prompt template cho coding agent

```markdown
# Task
Implement Runtime Node State Machine.

## Read
- docs/05_BD_Workflow_Runtime.md
- docs/04_Domain_Model.md

## Allowed files
- src/domain/runtime/**
- src/application/runs/**
- tests/runtime/**

## Forbidden
- Do not change API contracts.
- Do not call model providers.

## Acceptance
- All transitions implemented.
- Invalid transition raises DomainError.
- Duplicate event is idempotent.
- Unit tests cover all branches.
```
