# BD06 - Storage, Artifacts and Backup

```yaml
document_id: HH-BD-06
version: 0.1
status: In Review
owner: Backend + Runtime + Platform
reviewers: [Security, QA]
last_updated: 2026-07-28
depends_on: [BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md, ../02_REQUIREMENTS_BASELINE.md, ../design/D05_API_AND_STORAGE_CONTRACTS.md]
source: [D02, D03, D05, D07]
```

## 1. Document control

This document owns validated local persistence layout, artifact publication and backup/restore boundary. Runtime transaction semantics are referenced from BD03; security admission is referenced from BD07.

## 2. Purpose and scope

In scope: canonical path resolver, file-backed records, immutable artifact manifests, legacy evaluation evidence boundary and backup/restore. Out: central object store, retention deletion commitment, distributed store and execution routing. Gate B/C apply. Any content-addressed central index or data-life-cycle action stops for owner approval.

## 3. Context and boundary

All caller paths are IDs/relative names resolved beneath configured roots. Runtime supplies committed state references; Artifact service alone publishes readable manifest-backed versions; evaluation services inspect legacy run/suite files without reinterpreting them as WorkflowRun. Backup service copies the declared durable set to a validated destination. Storage MUST NOT route providers, decide policy, expose orphan content or use cache/temp/raw secrets as backup inputs.

## 4. Design overview

```text
validated ID/path -> canonical resolver -> runtime/eval/artifact record
Runtime committed result -> staged content -> scan -> immutable manifest-last -> readable artifact
durable set -> backup -> empty validated restore -> hash/recovery/replay verification
```

Current impact: `runtime_state.py`, `runtime_artifacts.py`, `runs.py`, `suites.py`, `inspect_evals.py`, `integrity.py` and configured roots. Physical record details remain detailed-design work; this BD fixes ownership and publication order.

## 5. Contract inventory

| Contract | Inputs / outputs | Error/side effect | Version/concurrency | Classification |
|---|---|---|---|---|
| Path resolver | validated ID/relative path -> canonical allowed target | traversal/root/home/symlink/reparse/unsafe name denied | configured root revision | internal/restricted |
| Artifact publication | staged bytes + lineage -> immutable manifest/version/hash | scan failure/orphan -> quarantine; manifest is visibility authority | manifest schema/version | classified content |
| Eval evidence | legacy suite/run/log request -> bounded inspection/comparison | incompatible/unknown denied; no reinterpretation as Runtime | legacy compatibility | internal |
| Backup/restore | declared durable set -> backup receipt/restore report | excludes cache/temp/secret; no auto-resume lost execution | backup manifest/hash | restricted |

## 6. Behavior flows

Happy artifact path: Runtime commits result reference -> service writes staged content under run boundary -> computes hash/type/size -> scans -> writes immutable manifest last -> list/read resolves only that manifest. Rewriting creates a new version, never overwrite. Denial/quarantine hides content. Eval path validates suite/run compatibility then reads current bounded evidence; trigger stream preserves budget/process status but remains separate from Runtime. Restore stops server, restores to empty validated root, verifies hashes and recovery scan, replays sample and does not resume a lost execution.

## 7. Persistence/config/deployment impact

Target layout uses configured roots, UTC timestamps, schema versions and aggregate integer version from BD03. Durable set: workflows, agents/policy config, runtime threads/runs/events/checkpoints, manifests/content and audit evidence; excluded: caches, temporary execution directories and raw secret files. Existing file stores migrate incrementally, backup first and retain/quarantine ambiguity. Central object store, dedupe and deletion are N/A pending OD-04/OD-05. Single-host file assumptions come from BD01.

## 8. Requirement traceability

| REQ/family | State | BD section | D source | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| REQ-EVAL-01 | MUST / VERIFIED | §3-6 | D05 §6 | existing runs/suites/logs/integrity/comparison remain bounded; incompatible/unknown denied | existing eval regression | B | Backend / In Review |
| REQ-EVAL-02 | MUST / VERIFIED | §3, §6 | D05 §6 | known suite trigger streams mocked progress/budget; timeout/concurrency enforced | existing trigger regression | B | Backend / In Review |
| REQ-EVAL-03 | SHOULD / TARGET | §3-6 | D01 §4; D05 §6 | shared safe error/correlation does not reinterpret legacy files as runtime aggregate | API-001 / integration | C | Backend / In Review |
| REQ-EVAL-04 | SHOULD / PROPOSED owner-required | §2, §7, §10 | D06 §4,11; D07 §7 | external log retention/provenance stays best-effort until owner policy | OD-05, RD-07 / review | C | Product + QA + Security / Blocked |
| REQ-ART-01 | MUST / VERIFIED | §3-6 | D05 §7-9 | current run-bound artifact list/read rejects bad run/name/traversal | existing artifact regression | B | Runtime / In Review |
| REQ-ART-02 | MUST / TARGET | §4-7 | D02 §2,7; D05 §8-10 | immutable hash/version/lineage/scan manifest is sole visible record | AR-001 / integration | C | Runtime + Security / In Review |
| REQ-ART-03 | SHOULD / TARGET | §3-6 | D06 §7,9 | only scanned manifest-backed allowed content renders/downloads | SEC-001/002 / adversarial | C | Security + Backend / In Review |
| REQ-ART-04 | MAY / PROPOSED owner-required | §2, §7, §10 | D05 §9-10; D07 §10 | central index/object store/deletion waits for lineage/privacy/backup ADR | OD-04/05 / design review | E | Product + Security / Blocked |
| REQ-DATA-01 | MUST / TARGET | §3-6 | D01 invariant 4; D05 §7; D06 §9 | all runtime/artifact/workflow/skill/suite/job paths reject escapes | SEC-001 / adversarial | C | Backend + Security / In Review |
| REQ-DATA-02 | MUST / TARGET | §5-7 | D02 §2,6; D03 §3 | schema rejects invalid ID/time/version; snapshots/retry evidence remains immutable | WF-001, ST-001 / contract | B,C | Runtime / In Review |
| REQ-DATA-03 | MUST / TARGET | §4-7 | D05 §10; D07 §7 | empty-root restore verifies hashes/replay/artifact and no lost auto-resume | OPS-002 / operational | C | Platform + QA / In Review |

## 9. Acceptance and verification

Run `python -m pytest tests -q` plus AR-001, SEC-001/002, OPS-002 and targeted eval/integrity tests. Evidence: manifest hash fixture, quarantine receipt, backup inventory, restore report and sampled replay/hash verification. Runtime/Security/Platform jointly review Gate C.

## 10. Open decisions and stop conditions

OD-04 chooses per-run versus central artifact index; OD-05/RD-07 govern retention/lifecycle. Stop on an absolute user-controlled path, orphan exposure, skipped scan, raw secret backup, automatic deletion, store migration without backup/rollback or a claim that file storage supports distributed writers.

## 11. Change log and references

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial Basic Design allocation |

References: `../02_REQUIREMENTS_BASELINE.md`; `../design/D05_API_AND_STORAGE_CONTRACTS.md`; `../design/D07_DEPLOYMENT_SLO_AND_OPERATIONS.md`; [BD03](BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md), [BD07](BD07_SECURITY_GOVERNANCE_AND_CONTROLLED_EXECUTION.md), [BD08](BD08_DEPLOYMENT_OPERATIONS_AND_VERIFICATION.md).
