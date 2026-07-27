# BD02 - Domain, Workflow and Profile

```yaml
document_id: HH-BD-02
version: 0.1
status: In Review
owner: Runtime
reviewers: [Backend, Security]
last_updated: 2026-07-28
depends_on: [BD01_ARCHITECTURE_MODULES_AND_CONFIGURATION.md, ../02_REQUIREMENTS_BASELINE.md, ../design/D02_DOMAIN_AND_WORKFLOW_CONTRACTS.md]
source: [D01, D02]
```

## 1. Document control

This is the implementable domain boundary for workflow definitions, profiles, snapshots and skills. State transitions are owned by BD03; execution protocols are owned by BD04.

## 2. Purpose and scope

In scope: schema-v1 validation, linear normalized IR, profile resolution, immutable run inputs and skill identity. Out: graph execution algorithm, provider session persistence, non-linear graph and mutable shared memory. Assumption: definitions and profiles are local files. Gate B applies; non-linear workflow or durable shared session is an owner-required stop.

## 3. Context and boundary

Workflow Registry accepts YAML and layout sidecars, returns a validated canonical definition and errors; it MUST NOT launch nodes. Agent/Profile Registry resolves named profile records. Snapshot builder freezes definition, profile, route and skill identities before Runtime creates a run. Skill discovery reads only configured sources and exposes provenance; skill content has no authority. Runtime consumes snapshots but cannot change their semantic hash.

## 4. Design overview

```text
YAML + layout -> validator -> canonical linear IR -> snapshot builder -> Runtime create-run
profiles + skill catalogue ------------------------------^              |
layout sidecar is UI-only; semantic hash excludes it                     +-> BD03
```

`services/workflow.py`, `runtime_agents.py`, `runtime_skills.py` and `skill_library.py` are current impact points. The future schema layer may be shared by API validation, but its result and path-specific error shape are one domain contract.

## 5. Contract inventory

| Contract | Inputs / outputs | Error/side effect | Version/concurrency | Classification |
|---|---|---|---|---|
| Workflow validation | YAML definition -> canonical IR + all errors | no execution; invalid path-specific errors | `schema_version: 1`; immutable accepted definition | internal |
| Profile resolution | profile ref -> validated provider/model/budget/risk/skill refs | unknown/invalid profile denied | profile hash | internal/restricted refs |
| Run snapshot | canonical definition + resolved profile/route/skills -> immutable snapshot/hash | drift invalidates dependent action | snapshot schema v1 | internal |
| Skill identity | configured source/name -> content hash/provenance/drift state | shadow/drift fail closed or revalidate | `{source,name,content_hash}` | untrusted content |

## 6. Behavior flows

Happy path: parse -> validate required fields and graph invariants -> normalize ordered IR -> resolve agent/profile/skills -> freeze hashes -> hand snapshot to Runtime. Denial: unsupported schema, cycle/branch, bad template, unknown agent, invalid cap or skill returns all deterministic errors and has no run side effect. A later profile/skill edit does not alter the snapshot; detected hash drift invalidates approval/run continuation according to security policy.

## 7. Persistence/config/deployment impact

Persist workflow YAML, layout sidecar separately, profile/skill source metadata and immutable per-run snapshot references. Layout does not enter workflow semantic hash. Breaking semantic changes need a schema version, migration fixtures and rollback path; additive declared fields may be preserved but cannot alter execution. No deployment change is required. Central shared memory/session storage is N/A pending owner decision.

## 8. Requirement traceability

| REQ/family | State | BD section | D source | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| REQ-WF-01 | MUST / VERIFIED | §3-6 | D02 §3-5 | valid YAML gives stable IR; malformed graph/profile/template errors are deterministic | WF-001/002 / contract | B | Runtime / In Review |
| REQ-WF-02 | MUST / TARGET | §2-6 | D02 §3-5,8-10 | schema-v1 rejects unsupported version and all non-linear semantics | WF-001/002 / contract | B,C | Runtime / In Review |
| REQ-WF-03 | MUST / VERIFIED | §3-6 | D02 §6 | valid profiles resolve; invalid tier/skill/profile is denied | existing profile regression / integration | B | Runtime / In Review |
| REQ-WF-04 | MUST / TARGET | §3-7 | D02 §6-8; D03 §7 | editing current definition/profile/skill cannot change replay semantics | SUP-001 / snapshot contract | B,C | Runtime / In Review |
| REQ-WF-05 | SHOULD / VERIFIED | §3-7 | D02 §2 | configured discovery/read/hash/drift is bounded and traversal-safe | existing skill regression / integration | B | Runtime / In Review |
| REQ-WF-06 | MUST / TARGET | §4-7 | D06 §7,10.1 | shadow/hash change fails closed or requires revalidation; content grants no authority | SUP-001 / security | C | Security + Runtime / In Review |
| REQ-WF-07 | MAY / PROPOSED owner-required | §2, §10 | D01 ADR-003; D02 §5 | no implementation until graph/retry/join/migration suite is approved | owner ADR / design review | E | Product + Runtime / Blocked |

## 9. Acceptance and verification

Evidence: valid/invalid schema fixtures, canonical hash fixture, profile/skill drift fixture and existing regression. Run `python -m pytest tests -q` and target WF/SUP contract tests. Runtime owner approves Gate B; Gate C requires frozen snapshots to be used by BD03/BD04 without a bypass.

## 10. Open decisions and stop conditions

Stop for a requested graph branch/join, a new template variable semantic, a shared mutable provider session, or an unapproved skill lifecycle decision (RD-07). Do not add a provider call, security authorization or state mutation to this boundary. Unknown skill provenance remains untrusted and unavailable for activation.

## 11. Change log and references

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial Basic Design allocation |

References: `../02_REQUIREMENTS_BASELINE.md`; `../design/D01_ARCHITECTURE_AND_SCOPE.md`; `../design/D02_DOMAIN_AND_WORKFLOW_CONTRACTS.md`; [BD03](BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md), [BD07](BD07_SECURITY_GOVERNANCE_AND_CONTROLLED_EXECUTION.md).
