# D08 — Test and Implementation Plan

```yaml
document_id: HH-DES-D08
version: 1.1
status: In Review
owner: Backend + QA
depends_on: [D01, D02, D03, D04, D05, D06, D07]
research_sources: [HH-RES-R03, HH-RES-R04, HH-RES-R05, HH-RES-R06, HH-RES-R07]
```

## 1. Test strategy

- Unit: schema, transition, routing, error/redaction, artifact hash.
- Contract: workflow, executor adapters, API/SSE.
- Integration: Runtime→Gateway→mock adapter→artifact/event.
- E2E: workflow + approval/resume + recovery.
- Adversarial: traversal, injection, duplicate/stale/out-of-order.
- Operational: restart, backup/restore, cancellation, quotas.

Provider tests mặc định dùng fake/mock; real provider smoke là opt-in và không chạy trong deterministic suite.

## 2. Golden flow

```text
validate versioned workflow
→ create run and snapshots
→ execute agent through Gateway/mock adapter
→ persist artifact v1
→ deterministic validation
→ approval interrupt
→ idempotent resume
→ execute remaining node
→ terminal state + replay + artifact verification
```

Golden flow phải chạy không import provider internals từ Runtime.

## 3. Requirement-to-test matrix

| Test ID | Requirement | Level | Expected |
|---|---|---|---|
| WF-001 | linear schema valid | contract | normalized IR stable |
| WF-002 | branch/cycle/unknown agent invalid | contract | all errors returned |
| ST-001 | state transition table | unit/property | invalid edge rejected |
| ST-002 | duplicate/stale command | integration | no duplicate execution |
| EV-001 | ordered envelope/replay | integration | same final projection |
| EV-002 | gap/corrupt/late event | recovery | quarantine/fail closed |
| EX-001 | adapter conformance | contract | normalized event/result |
| EX-002 | partial stream fallback | integration | no silent fallback |
| EX-003 | timeout/cancel | integration | terminal + process cleanup |
| API-001 | status/error/idempotency | contract | documented responses |
| API-002 | SSE reconnect | integration | resume after cursor |
| AR-001 | immutable artifact/hash | integration | no overwrite |
| SEC-001 | traversal/symlink | adversarial | denied |
| SEC-002 | secret/injection/egress | adversarial | redact/no execution |
| OPS-001 | restart during attempt | recovery | no duplicate artifact |
| OPS-002 | backup/restore | operational | replay/hash succeed |
| E2E-001 | golden workflow | E2E | succeeded after HITL |
| DUR-001 | transaction chain crash matrix | recovery | no fork/gap/silent loss |
| DUR-002 | event regeneration/torn-tail repair | recovery | derived timeline restored |
| PROV-001 | configured/resolved/version truth | contract | exact evidence reported |
| WIN-001 | associated process tree + escape paths | adversarial | contained/denied or profile NO-GO |
| CAP-001 | empty child capability | security | means none, never unrestricted |
| TOOL-001 | typed action + capability receipt | security | no execution without exact receipt |
| SUP-001 | skill source/hash drift | security | invalidates run/approval |
| MEM-001 | memory provenance/scope/expiry | security | poisoned/unscoped record denied |
| MCP-001 | MCP admission/auth/schema | security | disabled until all controls pass |

## 4. Phase plan

### Phase 0 — Contract fixtures

Deliver:

- workflow schema v1 + fixtures;
- execution/event/error schema fixtures;
- pure transition table/tests;
- no runtime behavior migration yet.
- close empty-scope child/tool/skill bypass;
- provider status separates configured/resolved executable and candidate version.

Gate: `WF-*`, `ST-001` green and existing tests unchanged.

### Phase 1 — Executor Port vertical slice

Deliver:

- Executor Port types;
- mock adapter;
- internal Gateway/router;
- one workflow node through new path;
- correlation/redaction skeleton.

Gate: `EX-001`, golden two-node test and provider failure tests green.

### Phase 2 — Runtime command/event hardening

Deliver:

- state version, idempotency ledger;
- command/event envelopes;
- immutable transaction journal + per-run recovery checkpoint;
- duplicate/stale handling;
- derived-event regeneration và crash/torn-tail repair.

Gate: `ST-002`, `EV-*`, `OPS-001` green.

### Phase 3 — Provider adapters

Deliver:

- current API/CLI provider wrappers implement Executor contract;
- capability manifest/error map;
- exact tested version/fixture; untested candidate không `supported=true`;
- bounded retry/cancel.

Gate: adapter conformance; Runtime no direct `get_provider`.

### Phase 4 — Artifact/API

Deliver:

- immutable artifact manifest/version/hash;
- API standardized error/concurrency;
- SSE cursor replay.

Gate: `API-*`, `AR-001`, UI compatibility tests.

### Phase 5 — Security/operations

Deliver:

- typed read-only tool kernel, deterministic policy và action-bound approval;
- skill/memory provenance/hash lifecycle;
- audit records;
- backup/restore and operational alerts.

Gate: `CAP/TOOL/SUP/MEM-*`, `SEC-*`, `OPS-002`; privileged tool/MCP chưa được bật.

### Phase 6 — Controlled Windows executor (optional)

Deliver only after approved ADR:

- native Job supervisor + escape tests;
- restricted identity và disposable workspace boundary;
- hard quota storage primitive;
- admin pre-provisioned/authenticated-broker egress;
- minimal environment, exact known-secret redaction và incident cleanup.

Gate D before any hostile/restricted workspace-write. Nếu product không cần, giữ phase này ngoài local-v1.

## 5. Task template

```text
Task:
Contract IDs:
As-is evidence:
Target behavior:
Allowed files:
Forbidden changes:
Input/output/error/state:
Data classification and permissions:
Migration/compatibility:
Test IDs and command:
Rollback:
Stop conditions:
Human reviewer:
```

## 6. Mandatory stop conditions

Coding agent dừng và báo khi:

- cần chốt OD/ADR;
- contract/schema mâu thuẫn;
- cần dependency, database, queue, remote service hoặc permission mới;
- cần breaking API/persisted format;
- cần mở workspace/network/secret scope;
- test failure nằm ngoài allowed files;
- user changes trùng vùng cần sửa.

Không được “fix” bằng cách hạ test, bỏ security check hoặc thêm silent fallback.

## 7. Definition of Done

- code map rõ đến contract/requirement ID;
- unit + contract + relevant integration tests xanh;
- no real provider in deterministic tests;
- schema/migration/backward compatibility verified;
- logs/events không secret;
- docs/change log updated;
- unrelated user changes preserved;
- reviewer xác nhận acceptance và rollback.

## 8. Release gates

### Gate C — Local v1

- `WF/ST/EV/EX/API/AR/SEC/OPS/E2E` required tests xanh.
- Existing Hub regression suite xanh.
- No direct Runtime→provider path.
- Backup/restore và cancel/recovery demo pass.
- R03 crash matrix/probes pass trong approved durability envelope.
- Provider `supported` chỉ cho exact fixture-pinned version.
- Empty child capability escalation đóng.

### Gate D — CLI controlled

- executable/path/env/egress allowlist;
- process tree kill;
- output/file quota;
- secret/artifact scan;
- threat tests green.
- WFP/egress privilege bootstrap không nằm trong elevated Hub process.
- WMI/COM/service/task-scheduler escape tests và storage quota enforcement xanh.
- Skill/memory/tool capability tests xanh.

### Gate E — Production evolution

- approved identity/storage/queue/deployment ADRs;
- migration + rollback;
- load/soak/chaos/security tests;
- SLO/alert/DR owner sign-off.

## 9. Verification commands

Canonical backend regression command:

```powershell
python -m pytest tests -q
```

Khi implementation bắt đầu, thêm targeted contract tests nhưng không thay regression command bằng subset.
