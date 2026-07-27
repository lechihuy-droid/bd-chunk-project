# BD03 - Runtime State, Events and Recovery

```yaml
document_id: HH-BD-03
version: 0.1
status: In Review
owner: Runtime
reviewers: [Backend, Platform, Security]
last_updated: 2026-07-28
depends_on: [BD02_DOMAIN_WORKFLOW_AND_PROFILE.md, ../02_REQUIREMENTS_BASELINE.md, ../design/D03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md]
source: [D02, D03, D05]
```

## 1. Document control

This document owns Runtime command/state/recovery behavior. BD05 maps it to HTTP/SSE; BD06 owns physical storage and artifact contract; BD04 owns provider execution lifecycle.

## 2. Purpose and scope

In scope: run/thread state, node attempt and interrupt transitions, command concurrency, journal/projection recovery, derived events, checkpoint and cancellation. Out: provider protocol, SSE wire framing, artifact manifest details and a durability SLA. Gate B/C apply. RD-01 and RD-02 are mandatory owner decisions before a Gate C recovery claim.

## 3. Context and boundary

Runtime is the only writer of run/node/interrupt state. API submits commands; Domain provides immutable snapshots; Gateway returns normalized execution results; Store persists projection/journal/checkpoint; Event service exposes derived timeline; Audit is separate in BD07. Runtime MUST NOT call a provider, infer commit order from file timestamps, or replay an ambiguous external side effect.

## 4. Design overview

```text
command(expected version,key) -> Runtime transition -> transaction phase -> projection/checkpoint
                                                        -> derived event -> BD05 SSE
Gateway result ----------------------------------------------------------^ 
```

Current impact points are `runtime_state.py`, `runtime_events.py`, `runtime_checkpoint.py`, `runtime_interrupts.py`, `runtime_reducers.py`, `runtime_validate.py` and `workflow_exec.py`. The migration replaces their implicit coordination only after versioned fixtures are green.

## 5. Contract inventory

| Contract | Inputs / outputs | Error/side effect | Version/concurrency | Classification |
|---|---|---|---|---|
| Command envelope | type, run, expected version, key, hash -> redacted response ref | stale/conflicting key is 409 with no side effect | per-run lock + ledger | internal |
| State transition | current aggregate + allowed trigger -> next aggregate | invalid/terminal transition denied | integer state version | internal |
| Transaction authority | immutable phases -> committed projection/checkpoint | fork/gap/corruption -> recovery-required | hash-chain/checksum | restricted integrity evidence |
| Runtime event | committed transaction -> ordered event | missing derived event regenerates; torn tail quarantines | per-run sequence | internal/redacted |
| Recovery/cancel | startup/cancel command -> safe terminal/decision state | never auto-replay ambiguous provider effect | command idempotency | internal |

## 6. Behavior flows

Happy flow: create with BD02 snapshot -> queue/start -> create attempt -> Gateway/validator result -> persist result reference -> commit projection -> derive event/checkpoint -> terminal. Approval creates an interrupt and blocks launch; resolve uses expected version/key. Duplicate same-hash command returns prior response; conflicting key or stale version returns 409. Restart validates journal chain, completes/aborts recorded phase, marks lost process ambiguous for human/explicit retry, repairs a torn event tail with receipt, and never treats events as state authority. Cancel persists `cancelling`, asks execution boundary to stop, then terminalizes only after tracked execution ends.

## 7. Persistence/config/deployment impact

Target persisted model adds state version, immutable checksummed transaction phases, idempotency ledger references, recovery checkpoint and derived event sequence. Existing JSON/JSONL is not declared compliant. Migration must backup first, be idempotent or rollbackable, quarantine ambiguity and verify replay/hash. Per-run in-process locking only supports BD01 single-process topology. Power-loss/RPO claims are N/A until probe evidence and RD-02 approval.

## 8. Requirement traceability

| REQ/family | State | BD section | D source | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| REQ-RUN-01 | MUST / VERIFIED | §3-6 | D03 §1-3 | bounded run/thread records are create/list/read inspectable and reject invalid root/ID | existing runtime regression | B | Runtime / In Review |
| REQ-RUN-02 | MUST / TARGET | §3-6 | D03 §1-3,10 | only valid transitions occur once; retry creates a distinct attempt | ST-001/002 / unit+integration | B,C | Runtime / In Review |
| REQ-RUN-03 | MUST / VERIFIED | §4-6 | D03 §5,7 | current checkpoint/approval/resume linear golden flow remains regression-safe | E2E-001 / E2E | B | Runtime / In Review |
| REQ-RUN-04 | MUST / TARGET | §4-7 | D03 §4.1,6-8 | stale/conflicting command has no side effect; journal fork/gap fails closed | ST-002, DUR-001 / recovery | C | Runtime / In Review |
| REQ-RUN-05 | MUST / TARGET | §4-7 | D03 §4,7-8 | ordered derived events replay/regenerate; corrupt tail quarantined with repair receipt | EV-001/002, DUR-002 / recovery | C | Runtime / In Review |
| REQ-RUN-06 | MUST / VERIFIED gap | §2, §7, §10 | D03 §8; D07 §7 | release status makes no zero-loss/exactly-once/Gate-C recovery claim without approved evidence | DUR-001/002 / release review | C | Platform + Runtime / In Review |
| REQ-RUN-07 | SHOULD / VERIFIED | §3, §6 | D02 §2 | parsed session replay remains bounded and provenance-aware | existing replay regression | B | Backend / In Review |
| REQ-RUN-08 | SHOULD / VERIFIED | §3, §6 | D07 §5 | usage parsers/caches remain warning-tolerant with correct rollups | existing usage regression | B | Backend / In Review |
| REQ-RUN-09 | MAY / PROPOSED owner-required | §2, §10 | D02 §2; D04 §11 | no shared mutable continuation until privacy/source/retention migration is approved | RD-07 / design review | E | Product + Security + Runtime / Blocked |

## 9. Acceptance and verification

Use `python -m pytest tests -q` plus ST, EV, DUR, OPS and E2E targeted tests. Evidence: command ledger fixture, transition report, crash matrix, repair receipt, recovery scan and cancel demo. Gate C needs approved durability envelope, no direct provider invocation and independent Runtime/Platform review.

## 10. Open decisions and stop conditions

OD-02 selects projection version placement; RD-01 approves journal authority; RD-02 approves the qualified durability envelope. Stop on a request for multi-process writes, automatic external re-execution, event-as-authority, exactly-once claim, schema reinterpretation without migration, or a provider-specific recovery assumption.

## 11. Change log and references

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial Basic Design allocation |

References: `../02_REQUIREMENTS_BASELINE.md`; `../design/D02_DOMAIN_AND_WORKFLOW_CONTRACTS.md`; `../design/D03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md`; `../design/D05_API_AND_STORAGE_CONTRACTS.md`; [BD04](BD04_GATEWAY_EXECUTOR_AND_PROVIDER_ADAPTERS.md), [BD05](BD05_API_AND_STREAMING.md), [BD06](BD06_STORAGE_ARTIFACTS_AND_BACKUP.md).
