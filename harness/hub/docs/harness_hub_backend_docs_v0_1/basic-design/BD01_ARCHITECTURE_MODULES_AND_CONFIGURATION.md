# BD01 - Architecture, Modules and Configuration

```yaml
document_id: HH-BD-01
version: 0.1
status: In Review
owner: System Architecture + Backend
reviewers: [Runtime, Security, Platform]
last_updated: 2026-07-28
depends_on: [../00_INDEX.md, ../02_REQUIREMENTS_BASELINE.md, ../design/D01_ARCHITECTURE_AND_SCOPE.md, ../design/D07_DEPLOYMENT_SLO_AND_OPERATIONS.md]
source: [D01, D07]
```

## 1. Document control

This document owns the local-v1 module and configuration boundary. The requirements baseline remains authoritative for priority and state; this document does not approve an open ADR.

## 2. Purpose and scope

In scope: modular-monolith seams, one-host topology, startup configuration and safe operational correlation. Out of scope: database, broker, multi-worker mutation, remote workers, RBAC and HA. Assumption: one trusted local operator. Gate A validates this package; Gate B validates module contracts; Gate C requires the boundary tests. Any non-loopback or multi-process proposal stops for an ADR and security review.

## 3. Context and boundary

Browser and local API are callers. `server.py` and route modules translate HTTP only; application services coordinate; Runtime owns mutable workflow state; Gateway owns route selection; Executor owns provider lifecycle; Policy decides but never launches; Artifact owns manifest/content access. Configuration is read at startup from `config.py` and validated roots are handed to services. No module may infer permission from a caller path or use an optional dashboard source to make health false.

## 4. Design overview

```text
SPA -> FastAPI routes -> application services -> Runtime -> Gateway -> Executor -> adapter
                               |                  |              |
                               +-> read models    +-> file store  +-> policy capability check
```

Implementation seams: `server.py` remains transport composition; `config.py` remains the central settings source; `services/workflow.py` validates only; `services/workflow_exec.py` becomes a Runtime client of Gateway rather than a provider client. Current `services/runs.py`, `suites.py`, `usage.py`, `board.py` and `governance.py` are read-model surfaces, not `WorkflowRun` children.

## 5. Contract inventory

| Contract | Inputs / outputs | Error and side effect | Version/concurrency | Classification |
|---|---|---|---|---|
| Startup validation | settings, paths, bind address, provider catalogue | reject invalid root/executable or unsupported mutable topology; no partial start | settings revision; one process | internal/restricted for paths |
| Health/read model | request correlation; optional source status | safe status and component warning; read-only | API contract owned by BD05 | internal |
| Module dependency | application call/import boundary | reject bypass in contract test/review | N/A | internal |
| Operational correlation | request/run/execution IDs, durations | structured safe log/event; no prompt/body/secret | bounded fields | internal/restricted refs only |

## 6. Behavior flows

Happy path: load config -> canonicalize roots -> verify loopback/single-process mode -> build routes/services -> emit safe startup status. Validation denial: unresolved root, unsafe bind or unsupported worker mode prevents mutable Runtime startup. Optional provider/dashboard failure yields a component warning while health remains a control-plane result. A module-boundary violation is a failing import/contract check, not a runtime fallback.

## 7. Persistence/config/deployment impact

Persist only versioned configuration references and safe startup/audit records; never secret values. Existing `config.py` and service root configuration are impacted. A security-boundary configuration change requires restart and audit. Compatibility: retain current `/api` route composition; BD05 owns its wire contract. Rollback is configuration rollback plus restart. Database/queue and non-loopback deployment are N/A for local-v1 and require Gate E ADRs.

## 8. Requirement traceability

| REQ/family | State | BD section | D source | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| REQ-PLAT-01 | MUST / VERIFIED | §3-6 | D01 §2-5 | root and health expose safe local control-plane read model | API-001 / regression | A | Backend / In Review |
| REQ-PLAT-02 | MUST / TARGET | §2, §5-7 | D05 §2,8; D07 §1 | unsupported multi-worker/non-loopback mutation is blocked or explicitly requires ADR | OPS-001 / startup contract | B,C | Platform / In Review |
| REQ-PLAT-03 | SHOULD / TARGET | §3-6 | D01 §3; D05 §6 | optional read-model outage is isolated from health | API-001 / integration | B,C | Backend / In Review |
| REQ-PLAT-04 | SHOULD / TARGET | §4-6 | D03 §4; D07 §5 | bounded correlated status has no raw prompt, secret, body or unrestricted path | OPS-002, SEC-002 / integration | C | Platform / In Review |
| REQ-NFR-04 | SHOULD / TARGET | §3-6 | D01 §3-4,9 | import/contract evidence has no API->provider or Runtime->provider bypass | EX-001 / architecture contract | C | System Architecture / In Review |

## 9. Acceptance and verification

Run `python -m pytest tests -q` plus targeted startup, health/read-model and architecture-boundary tests when implemented. Evidence is a sanitized startup report, component-degraded case, import/contract result and reviewer sign-off. Backend and Platform review Gate A/B; Gate C additionally requires no direct Runtime-to-provider path.

## 10. Open decisions and stop conditions

OD-01 decides `/api` versioning and belongs to Backend. Stop if an implementation needs a new configuration authority, non-loopback binding, multi-worker mutable files, a database/queue, raw secret persistence or an undocumented cross-module dependency. Do not turn target module boundaries into VERIFIED merely by rearranging documentation.

## 11. Change log and references

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial Basic Design allocation |

References: `../02_REQUIREMENTS_BASELINE.md`; `../design/D01_ARCHITECTURE_AND_SCOPE.md`; `../design/D07_DEPLOYMENT_SLO_AND_OPERATIONS.md`; [BD02](BD02_DOMAIN_WORKFLOW_AND_PROFILE.md), [BD08](BD08_DEPLOYMENT_OPERATIONS_AND_VERIFICATION.md).
