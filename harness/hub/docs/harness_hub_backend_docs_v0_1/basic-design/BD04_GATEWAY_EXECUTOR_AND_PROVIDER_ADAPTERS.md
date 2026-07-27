# BD04 - Gateway, Executor and Provider Adapters

```yaml
document_id: HH-BD-04
version: 0.1
status: In Review
owner: Execution Platform
reviewers: [Runtime, Security, Backend]
last_updated: 2026-07-28
depends_on: [BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md, ../02_REQUIREMENTS_BASELINE.md, ../design/D04_GATEWAY_EXECUTOR_AND_PROVIDERS.md]
source: [D03, D04, D06]
```

## 1. Document control

This is the execution boundary for chat/workflow provider calls and legacy Git-job position. Security policy and controlled execution constraints remain authoritative in BD07.

## 2. Purpose and scope

In scope: Gateway route plan, normalized Executor Port, API/CLI/mock adapters, capability evidence, retry/cancel/error lifecycle and Git-job separation. Out: Runtime state, approval/audit policy implementation, production sandbox and MCP enablement. Gate B/C apply; any workspace-writing CLI requires Gate D and approved decisions.

## 3. Context and boundary

Runtime submits an immutable request; Gateway evaluates candidate capability plus policy outcome and produces a route plan; Executor runs exactly one plan and returns normalized events/result/error; adapters translate only provider transport/protocol. Gateway MUST NOT mutate run state; Executor MUST NOT create business artifact records; adapter MUST NOT choose workflow retry/fallback; Runtime MUST NOT use direct provider protocol. Current `services/chat.py` and `services/providers/*` are adapter-facing evidence; `workflow_exec.py` is migration impact and `gitjobs.py` remains separate until approved.

## 4. Design overview

```text
Runtime/chat -> ExecutionRequest -> Gateway(route+policy) -> Executor -> mock|API|CLI adapter
                         ^                  |                    |
                     capabilities       normalized events       capability evidence
```

The request carries correlation, snapshot refs, classification, limits and capability receipt; it does not carry an untrusted executable command. Gateway eligibility is deterministic and denial is a normalized result, never a fallback.

## 5. Contract inventory

| Contract | Inputs / outputs | Error/side effect | Version/concurrency | Classification |
|---|---|---|---|---|
| Execution request | snapshot, content refs, limits, classification, capability -> route plan | no eligible route is normalized denial | schema v1; immutable request | public..restricted |
| Execution event/result | lifecycle/progress refs -> ordered normalized event/final result | partial output is explicit; no silent fallback | execution ID/correlation | redacted refs |
| Capability evidence | configured/resolved executable, observed/candidate version, fixture/provenance -> eligibility | unknown/mismatch is ineligible | pinned fixture revision | internal |
| Adapter lifecycle | route plan -> launch/stream/cancel/error | bounded transient retry only; process lifecycle delegated | execution ID | restricted env refs |
| Git boundary | legacy job command -> existing lifecycle | not advertised as Gateway/sandbox | separate compatibility surface | internal |

## 6. Behavior flows

Happy path: validate request -> apply classification/capability/limit/policy -> choose eligible evidence-backed route -> launch adapter -> normalize ordered events -> return one result. API adapter maps upstream events/errors; CLI adapter receives an allowlisted plan only and reports exact executable/version. Adapter retries only declared transient transport/rate-limit failures; auth, policy, validation, capability and contract failures do not retry/fallback. Cancellation reaches adapter lifecycle and reports normalized terminal outcome. Git-job routes retain current governance but do not inherit controlled-executor guarantees.

## 7. Persistence/config/deployment impact

Persist request/result references, route decision, capability evidence reference and safe execution correlation; BD03 owns run state and BD07 owns audit. Provider configuration is validated at startup by BD01. Migration stages: fixtures -> mock port -> Runtime path -> one API adapter -> conformance evidence -> CLI only within its security profile. Preserve current chat API compatibility through BD05. CLI workspace write, provider smoke scheduling and Git migration are not automatic changes.

## 8. Requirement traceability

| REQ/family | State | BD section | D source | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| REQ-CHAT-01 | MUST / VERIFIED | §3-6 | D04 §5-6 | invalid chat references return safe 400; fake stream has ordered delta/done/error | existing chat/provider regression | B | Backend / In Review |
| REQ-CHAT-02 | MUST / TARGET | §3-6 | D01 §4,7; D04 §1-6 | request/event/result/error schemas and mock+API conformance exist; Runtime has no provider lookup | EX-001 / contract | B,C | Execution Platform / In Review |
| REQ-CHAT-03 | MUST / TARGET | §4-6 | D04 §3,12 | supported flag only from exact pinned fixture; unknown/mismatch cannot route | PROV-001 / contract | C | Execution Platform / In Review |
| REQ-CHAT-04 | MUST / TARGET | §3-6 | D04 §4,7; D06 §3-4 | denial/no eligible route normalized; forbidden classes never retry/fallback | EX-002, SEC-002 / integration | C | Execution Platform + Security / In Review |
| REQ-CHAT-05 | SHOULD / TARGET | §3-7 | D04 §11 | provider session loss does not lose Hub persisted run/thread | adapter session regression | C | Execution Platform / In Review |
| REQ-CHAT-06 | MAY / PROPOSED owner-required | §7, §10 | D08 Phase 3 | real smoke remains opt-in until provider/data/credential cadence is approved | RD-03 / release review | C | Product + Runtime / Blocked |
| REQ-GIT-01 | MUST / VERIFIED | §3, §6 | D04 §9 | current job lifecycle/diff/stream bounded and regression-safe | existing gitjobs regression | B | Backend / In Review |
| REQ-GIT-02 | MUST / VERIFIED | §3, §6 | D06 §10 | risk/expiry/tamper/destructive governance denial remains observable | existing governance regression | B | Security / In Review |
| REQ-GIT-03 | MUST / TARGET | §2-3, §7 | D04 §9; D06 §8 | no Git subprocess is claimed as Runtime Gateway or production sandbox | WIN-001 / boundary review | D | Security + Backend / In Review |
| REQ-GIT-04 | SHOULD / PROPOSED owner-required | §7, §10 | D01 §4; D04 §1 | sharing Executor waits for owner threat/compatibility/rollback decision | OD-03, RD-04 / design review | D | Product + Security + Runtime / Blocked |

## 9. Acceptance and verification

Run deterministic `python -m pytest tests -q`, EX/PROV contract fixtures and cancellation/error tests. Evidence: capability manifest with provenance, mock stream transcript, normalized error fixture and source review showing Runtime has no direct provider lookup. Gate D evidence is separate and cannot be inferred from adapter conformance.

## 10. Open decisions and stop conditions

RD-03 selects official Gate-C provider set; OD-03/RD-04 govern workspace-writing/legacy Git evolution. Stop if an adapter needs a new secret, network destination, executable, direct Runtime mutation, silent fallback, privilege, raw body persistence or a claim of Windows isolation. MCP and privileged/write/network tools stay denied pending BD07 gates.

## 11. Change log and references

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial Basic Design allocation |

References: `../02_REQUIREMENTS_BASELINE.md`; `../design/D04_GATEWAY_EXECUTOR_AND_PROVIDERS.md`; `../design/D06_SECURITY_AND_GOVERNANCE.md`; [BD03](BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md), [BD07](BD07_SECURITY_GOVERNANCE_AND_CONTROLLED_EXECUTION.md).
