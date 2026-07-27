# BD07 - Security, Governance and Controlled Execution

```yaml
document_id: HH-BD-07
version: 0.1
status: In Review
owner: Security + Execution Platform
reviewers: [Runtime, Platform, Backend]
last_updated: 2026-07-28
depends_on: [BD02_DOMAIN_WORKFLOW_AND_PROFILE.md, BD04_GATEWAY_EXECUTOR_AND_PROVIDER_ADAPTERS.md, BD06_STORAGE_ARTIFACTS_AND_BACKUP.md, ../02_REQUIREMENTS_BASELINE.md, ../design/D06_SECURITY_AND_GOVERNANCE.md]
source: [D01, D04, D06, D07]
```

## 1. Document control

This document owns security invariants, policy/governance controls and the boundary for controlled Windows execution. It may constrain every other BD; it does not redefine their state, API or storage contracts.

## 2. Purpose and scope

In scope: local HTTP guardrails, classification, secret/redaction, typed capability/action/approval, child/skill/memory/MCP admission, audit/incident response and controlled CLI Gate D boundary. Out: multi-tenant RBAC, a production sandbox claim, remote workers and automatic MCP enablement. Gate B/C cover local policy; Gate D is mandatory for hostile/restricted workspace-write. Any missing policy/identity/egress enforcement is a deny/stop condition.

## 3. Context and boundary

Untrusted inputs include prompt/model/provider/CLI/retrieved/child/skill/memory/tool/MCP content. Policy receives typed action plus classification, scope and capability receipt, returns allow/deny and reason; it MUST NOT launch a process. Approval binds a canonical action and exact context, not a broad future permission. Gateway/Executor consume approved route/action plan. Audit is append-only evidence outside user-editable artifact tree. Current policy/governance/risk/child/memory/skill services are evidence, not proof of the target invariant.

## 4. Design overview

```text
untrusted content -> typed request -> classification + policy + capability intersection
                                     -> deny | action-bound approval -> Executor
security action -> append-only audit -> incident response / quarantine
CLI write request -> Gate-D supervisor boundary or deny
```

The authorization result includes policy evaluation ID, matched safe reason, scope/hashes/expiry and a capability receipt. Missing or empty scope means none. Static allowlists, classification and hard platform policy may only narrow permission.

## 5. Contract inventory

| Contract | Inputs / outputs | Error/side effect | Version/concurrency | Classification |
|---|---|---|---|---|
| HTTP/local control | origin/header/body/stream/bind -> allow/deny | deny before mutation | configured security revision | public/internal |
| Policy decision | typed action, classification, scope/capability -> receipt/deny | no fallback/implicit grant | policy hash | restricted metadata |
| Approval receipt | canonical target/args/run/execution/hashes/expiry -> one-time resolve | changed/stale/duplicate invalid | receipt ID + expiry | restricted |
| Trust lifecycle | child/skill/memory/MCP identity/provenance -> eligible/ineligible | missing/poisoned/drift denied | hash/schema/trust revision | untrusted -> classified |
| Audit/incident | security action/reference -> tamper-evident record/response | cancel/disable/quarantine/revoke; no auto resume | audit sequence/hash chain | restricted |
| Controlled executor | approved allowlisted launch -> supervised result | deny without identity/workspace/quota/egress evidence | exact executable/version | restricted |

## 6. Behavior flows

For any privileged action: canonicalize target -> classify data -> intersect parent/profile/workflow/platform capabilities -> evaluate policy -> either deny/audit or create approval -> verify receipt unchanged/one-time -> hand exact plan to Executor -> audit launch/result. Child delegation starts with intersection; empty list never expands. Skill hash/shadow drift and memory expiry/revocation invalidate dependent permission. Injection-shaped output stays data and cannot create an action. Incident: cancel/kill tracked process, disable route, quarantine artifacts/log references, revoke secret, preserve audit and wait for security review. CLI workspace-write is denied unless Gate-D supervisor, restricted identity, disposable workspace, enforceable quota and privileged egress boundary all pass.

## 7. Persistence/config/deployment impact

Persist only safe policy/approval/audit references, hashes, classification and outcome; secrets stay environment/secret-broker references with minimal allowlisted environment. Security-boundary config restart/audit is required. Audit is separate from operational Runtime events. Controlled Windows executor is a separate deployment subsystem: Hub remains non-elevated; WFP requires admin pre-provisioning or authenticated broker, otherwise use Gate-E isolated worker/deny. No generic runtime-root static serving or raw provider body persistence.

## 8. Requirement traceability

| REQ/family | State | BD section | D source | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| REQ-GOV-01 | MUST / VERIFIED | §3-6 | D06 §10.1 | bounded lead-only child packet/linkage/isolation/merge remains regression-safe | existing child regression | B | Runtime / In Review |
| REQ-GOV-02 | MUST / TARGET | §3-6 | D04 §10; D06 §7,10.1 | child intersection cannot expand paths/tools/data/egress; empty means none | CAP-001 / security | C | Security + Runtime / In Review |
| REQ-GOV-03 | MUST / VERIFIED | §3-6 | D06 §10 | current risk/denial/degradation state is inspectable | existing governance regression | B | Security / In Review |
| REQ-GOV-04 | MUST / TARGET | §4-6 | D06 §10 | changed target/action/policy/schema/skill invalidates one-time approval | SEC-002 / security | C | Security / In Review |
| REQ-GOV-05 | MUST / TARGET | §3-7 | D03 §4; D06 §11-12 | privileged action has safe policy ID plus append-only audit, separate from event | SEC-002 / integration | C | Security / In Review |
| REQ-GOV-06 | MUST / TARGET | §3-6 | D06 §7 | untrusted content cannot launch action; only typed approved request can | TOOL-001, SEC-002 / adversarial | C | Security / In Review |
| REQ-GOV-07 | MAY / PROPOSED owner-required | §2, §5-7, §10 | D04 §10; D06 §10.2 | MCP/privileged/write/network tools remain disabled until admission/auth/schema/egress tests and ADRs pass | MCP-001 / security | D | Product + Security / Blocked |
| REQ-OPS-01 | MUST / VERIFIED | §3-6 | D06 §10.1 | memory candidate accept/reject and governance inspection validate IDs/current behavior | existing runtime/API regression | B | Backend / In Review |
| REQ-OPS-02 | MUST / TARGET | §3-7 | D06 §10.1 | memory needs provenance/reviewer/scope/classification/hash/expiry and grants no authority | MEM-001 / security | C | Security + Runtime / In Review |
| REQ-SEC-01 | MUST / VERIFIED baseline + TARGET hardening | §3-7 | D05 §2; D06 §6 | loopback/CSRF/origin/CORS/body/stream/static-root denial is observable | SEC-002 / adversarial | B,C | Security + Backend / In Review |
| REQ-SEC-02 | MUST / TARGET | §3-6 | D04 §4; D06 §3-4 | unknown is restricted; routing/egress/fallback cannot weaken class | SEC-002 / security | C | Security + Execution Platform / In Review |
| REQ-SEC-03 | MUST / TARGET | §5-7 | D04 §2,8-9; D06 §5 | no secret appears in request/stdout/error/event/artifact; env is minimal | SEC-002 / adversarial | C | Security / In Review |
| REQ-SEC-04 | MUST / TARGET | §3-6 | D04 §10; D06 §7 | injection cannot execute; missing capability denies; changed receipt invalidates | TOOL-001, CAP-001 / security | C | Security / In Review |
| REQ-SEC-05 | MUST / TARGET | §5-7 | D04 §9; D06 §8 | allowlisted argv/env/workspace/time/output/tree/scan/version evidence or explicit low-assurance NO-GO | EX-003, WIN-001 / adversarial | D | Execution Platform + Security / In Review |
| REQ-SEC-06 | MUST / TARGET | §2, §5-7 | D04 §9; D06 §8 | hostile workspace-write denied until restricted identity/workspace/quota/egress/escape tests pass | WIN-001 / adversarial | D | Platform + Security / In Review |
| REQ-SEC-07 | MUST / TARGET | §5-7 | D06 §10-12; D07 §6 | audit evidence and cancel/disable/quarantine/revoke/preserve/review incident path tested | SEC-002, OPS-001 / operational | C,D | Security + Platform / In Review |
| REQ-SEC-08 | MUST / VERIFIED gap | §2, §7, §10 | D06 §8,10; assessment §4-7 | release/status denies unsupported production-safety claims and advertises gates | PROV-001, CAP-001, MCP-001 / review | C,D | Security / In Review |

## 9. Acceptance and verification

Run deterministic `python -m pytest tests -q`, then CAP/TOOL/SUP/MEM/MCP, SEC and WIN targeted tests as applicable. Evidence: policy decision/approval fixtures, redaction scan, child escalation denial, audit/incident drill, and Gate-D installation/escape/quota/egress evidence. Security owner signs Gate C; Security and Platform sign Gate D.

## 10. Open decisions and stop conditions

RD-04 chooses controlled executor investment; RD-05 chooses enforceable egress model; RD-06 decides MCP roadmap; RD-07 governs trust lifecycle. Stop/deny when policy is unavailable, content is untyped, scope is empty, secret would persist, containment is unproven, a process needs elevation, or a task requests provider-internal tool/MCP passthrough. Never claim same-user CLI is a sandbox.

## 11. Change log and references

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial Basic Design allocation |

References: `../02_REQUIREMENTS_BASELINE.md`; `../design/D06_SECURITY_AND_GOVERNANCE.md`; `../design/D04_GATEWAY_EXECUTOR_AND_PROVIDERS.md`; [BD04](BD04_GATEWAY_EXECUTOR_AND_PROVIDER_ADAPTERS.md), [BD06](BD06_STORAGE_ARTIFACTS_AND_BACKUP.md), [BD08](BD08_DEPLOYMENT_OPERATIONS_AND_VERIFICATION.md).
