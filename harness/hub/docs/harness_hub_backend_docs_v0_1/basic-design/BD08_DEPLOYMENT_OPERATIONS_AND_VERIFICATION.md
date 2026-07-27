# BD08 - Deployment, Operations and Verification

```yaml
document_id: HH-BD-08
version: 0.1
status: In Review
owner: Platform + QA
reviewers: [System Architecture, Runtime, Security]
last_updated: 2026-07-28
depends_on: [BD01_ARCHITECTURE_MODULES_AND_CONFIGURATION.md, BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md, BD04_GATEWAY_EXECUTOR_AND_PROVIDER_ADAPTERS.md, BD05_API_AND_STREAMING.md, BD06_STORAGE_ARTIFACTS_AND_BACKUP.md, BD07_SECURITY_GOVERNANCE_AND_CONTROLLED_EXECUTION.md, ../02_REQUIREMENTS_BASELINE.md, ../design/D07_DEPLOYMENT_SLO_AND_OPERATIONS.md, ../design/D08_TEST_AND_IMPLEMENTATION_PLAN.md]
source: [D07, D08]
```

## 1. Document control

This document owns supported environment, operational objectives, verification evidence and release/migration gates. It synthesizes but does not alter the contracts owned by BD01-BD07.

## 2. Purpose and scope

In scope: single-host local-v1 deployment, config/degraded signals, objectives, deterministic verification, release evidence, migration discipline and production-evolution boundary. Out: production SLA, shared-host HA, database/queue/object storage implementation and automatic retention. Gates A/C/D/E apply as specified. Proposed durability, retention and production envelope need owner sign-off before claims.

## 3. Context and boundary

Supported topology is one local Windows host, one FastAPI/Uvicorn process, in-process services, local files and approved provider calls with browser on loopback. Platform validates startup/config, monitors safe signals and runs restore drills. QA owns test evidence, not business contract mutation. Runtime/Executor/Artifact/Security own their observed behavior; BD08 only aggregates release evidence. Multi-worker mutation, remote worker and shared production deployment are outside this boundary.

## 4. Design overview

```text
validated startup -> local control plane -> structured telemetry/degraded state
change -> contract/version + backup -> migration/compatibility -> deterministic regression + targeted evidence
Gate A -> B -> C -> optional D -> E only with ADRs
```

Current impact: `config.py`, startup/run script, test suite and release documentation. Operational read models consume correlation-safe status only. Provider latency is measured separately from local control-plane objectives.

## 5. Contract inventory

| Contract | Inputs / outputs | Error/side effect | Version/concurrency | Classification |
|---|---|---|---|---|
| Startup/topology | config/root/provider/bind -> valid local process/status | unsafe root/executable/topology fails safe | config revision | internal/restricted refs |
| Operational status | metric/log/scan result -> bounded warning/degraded mode | mutation stops/read-only on store integrity loss | correlation IDs | internal |
| Verification | deterministic fixture/test -> evidence artifact | live provider excluded by default | test ID/revision | internal |
| Release/migration | change manifest + backup -> compatibility/migration/rollback evidence | unversioned break blocks release | schema/API revision | restricted integrity refs |
| Evolution review | need/SLO/ADR/evidence -> approve/reject next topology | no inheritance of local claims | Gate E | internal |

## 6. Behavior flows

Startup: load central config -> validate roots/providers/bind -> enforce one mutable process -> publish safe status. Operation: measure health/read/overhead/event delivery/cancel/recovery/caps; on disk/store/scan/provider fault show component correlation and degrade safely according to owning contract. Release: identify changed contract -> version/compatibility note -> backup -> migration with rollback/idempotency -> full deterministic regression plus target test IDs -> reviewer evidence -> gate decision. Restore drill verifies empty root/hashes/recovery/sample replay and never auto-resumes lost execution.

## 7. Persistence/config/deployment impact

Configuration centralization and restart/audit apply to security-boundary changes. Local engineering objectives are not a production SLA. Retention/deletion is not enabled absent policy. The release record links migration/version/backup/test evidence; durable data layout is owned by BD06. Gate D deploys a separate controlled executor subsystem, not a FastAPI flag. Gate E needs new ADRs for identity, storage, queue, remote execution, load/chaos/security and DR.

## 8. Requirement traceability

| REQ/family | State | BD section | D source | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| REQ-OPS-03 | SHOULD / VERIFIED | §3, §6-7 | D07 §2-3 | central config validates root/provider; missing secret is safe; boundary changes restart/audit | OPS-001 / startup | B | Platform / In Review |
| REQ-OPS-04 | SHOULD / TARGET | §3-6 | D07 §5-9; D06 §12 | corruption/auth/policy/disk/gap/mismatch/orphan/startup degradation is visible and safe | OPS-001/002 / operational | C | Platform / In Review |
| REQ-OPS-05 | MAY / PROPOSED owner-required | §2, §7, §10 | D05 §10; D07 §7 | retention/delete/export waits for lifecycle/authorization/audit policy | OD-05, RD-07 / review | C | Product + Security / Blocked |
| REQ-DATA-04 | SHOULD / PROPOSED owner-required | §2, §6-7, §10 | D03 §8; D07 §7 | only exact OS/Python/filesystem probe evidence supports RPO/RTO claim | RD-02, DUR-001/002 / review | C | Runtime + Product / Blocked |
| REQ-NFR-01 | SHOULD / TARGET | §3-6 | D07 §4-5 | local objectives instrumented/reported separately from provider latency, not SLA | OPS-001 / operational | C | Platform / In Review |
| REQ-NFR-02 | MUST / TARGET | §3-6 | D06 §9; D07 §9 | caps/degraded mode preserve safe results, quarantine scan failure, stop unsafe mutation | OPS-001/002 / operational | C | Platform + Security / In Review |
| REQ-NFR-03 | MUST / TARGET | §5-6 | D08 §1,9 | canonical regression stays fake/mock/no credentials; smoke opt-in | regression / deterministic | B,C | QA / In Review |
| REQ-NFR-05 | MAY / PROPOSED owner-required | §2, §7, §10 | D01 §8; D07 §10 | shared-host/HA/DR claim waits for Gate-E topology/ADR/test sign-off | Gate E / review | E | Platform + Product / Blocked |
| REQ-MIG-01 | MUST / TARGET | §5-7 | D02 §8; D07 §8 | public/persisted/security break has version, compatibility/migration/tests/owner review | release checklist / review | B,C | QA + owners / In Review |
| REQ-MIG-02 | MUST / TARGET | §6-7 | D03 §4.1,8; D05 §8,10 | runtime migration backs up, is idempotent/rollbackable, preserves/quarantines ambiguity, verifies replay/hash | DUR-001/002, OPS-002 / recovery | C | Runtime + Platform / In Review |
| REQ-MIG-03 | MUST / TARGET | §6-7 | D05 §1,4 | `/api` and UI compatibility fixtures stay green; duplicate route uses one command service | API-001/002 / contract | C | Backend + Frontend / In Review |
| REQ-MIG-04 | SHOULD / TARGET | §4, §6, §9 | D08 §4 | each staged Gateway/Runtime/provider/artifact/API/security phase gate passes before next | EX/ST/EV/API/AR/SEC / phased | C | Runtime + QA / In Review |
| REQ-MIG-05 | MAY / PROPOSED owner-required | §2, §7, §10 | D01 §8; D07 §10; D08 Gate E | database/queue/object/remote/identity needs ADR, threat, migration/rollback and tests | Gate E / review | E | Architecture + Product / Blocked |

## 9. Acceptance and verification

Canonical command is `python -m pytest tests -q`. Add targeted WF/ST/EV/EX/API/AR/SEC/OPS/E2E/DUR/PROV/WIN/CAP/TOOL/SUP/MEM/MCP tests only as their owner contract is implemented; real provider smoke is explicit opt-in. Evidence package: startup validation, regressions, target fixture report, recovery/cancel/restore demo, safe telemetry/degraded output, migration/rollback note and reviewer sign-off. Gate C requires all local-v1 evidence; Gate D adds controlled-executor evidence; Gate E has separate approval.

## 10. Open decisions and stop conditions

OD-05/RD-02 decide lifecycle and durability claims; RD-08 decides objective versus release target; RD-04/RD-05 govern Gate-D deployment. Stop if a release needs unapproved storage/queue/identity/remote service, changes persisted/API/security boundary without backup/migration/rollback, claims production SLO/DR from local tests, or makes deterministic tests depend on live credentials/network.

## 11. Change log and references

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial Basic Design allocation |

References: `../02_REQUIREMENTS_BASELINE.md`; `../design/D07_DEPLOYMENT_SLO_AND_OPERATIONS.md`; `../design/D08_TEST_AND_IMPLEMENTATION_PLAN.md`; [BD01](BD01_ARCHITECTURE_MODULES_AND_CONFIGURATION.md), [BD03](BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md), [BD07](BD07_SECURITY_GOVERNANCE_AND_CONTROLLED_EXECUTION.md).
