# Test Strategy and Acceptance

> Superseded by `../../design/D08_TEST_AND_IMPLEMENTATION_PLAN.md`.

| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-TEST-001 |
| Version | 0.2 |
| Status | Draft — merged from research |
| Depends on | Runtime, Gateway, Executor, API, CLI, Artifact and Security designs |
| Research sources | HH-RES-R01, HH-RES-R02 |
| Last updated | 2026-07-27 |

## 1. Test levels

- Unit: schemas, state transitions, routing, policy, parsers, error maps.
- Contract: chung cho mọi Gateway/Executor adapter.
- Integration: runtime + gateway + fake executor; HTTP/CLI fake backends.
- End-to-end: workflow, review, retry/fallback, artifact, cancellation/recovery.
- Security: boundary, injection, secret, policy and isolation.
- Compatibility: API/OpenAPI, CLI/provider versions, saved workflow versions.

Không gọi provider/CLI thật trong default CI; real-provider smoke là manual/explicit.

## 2. Golden workflow

```text
Input
→ Agent 1 execution
→ immutable artifact v1
→ deterministic/reviewer result
  ├─ GO → Agent 2 → final artifact → completed
  ├─ NO_GO_REPAIRABLE → new attempt/route → review again
  ├─ NEED_USER_DECISION → human task → resume
  └─ NO_GO_BLOCKING → stop/fail
```

## 3. Gateway tests

- deterministic routing với cùng registry/policy/request;
- hard policy override explicit model;
- capability filtering;
- unavailable primary tạo approved fallback plan;
- fallback exhaustion;
- no fallback cho security/auth/contract error;
- no silent fallback after partial stream;
- client disconnect → cancel;
- normalized routing error/evidence;
- prompt/secret không xuất hiện trong telemetry.

## 4. Executor conformance suite

Mọi adapter phải pass:

- schema/version validation;
- capability claims đúng hành vi;
- idempotent submit/cancel;
- ordered events và exactly-one-terminal-event;
- success/failure/partial output;
- normalized error taxonomy;
- timeout/deadline;
- cancellation cleanup;
- usage semantics;
- secret redaction;
- provider extension validation.

Capability được khai báo nhưng không pass corresponding test là release blocker.

## 5. API executor tests

- fake HTTP success, streaming SSE và non-stream;
- malformed JSON/SSE;
- 429 + Retry-After, 502/503/504 bounded retry;
- 400/401/403/404/410/422 no retry;
- timeout/abort;
- tool-call event normalization;
- usage/cost mapping;
- provider request/session IDs;
- output validation and redaction.

## 6. CLI executor tests

- fake process output và non-zero exit;
- parser với ANSI/Unicode/malformed protocol;
- explicit cancel và idle/global timeout;
- kill entire parent/child process tree;
- orphan reconciliation;
- path traversal/symlink escape;
- command injection qua argument/filename;
- minimal environment và secret scan;
- output/resource cap;
- CLI version compatibility;
- session resume/loss;
- cleanup failure warning.

## 7. Runtime/recovery tests

- valid/invalid run/node/attempt transitions;
- duplicate command/event không chạy node hai lần;
- retry tạo attempt mới và giữ evidence cũ;
- stale expected version trả conflict;
- restart ở trước/sau executor terminal event;
- cancellation propagation tới child/executor;
- retry exhausted → human task;
- state replay tạo đúng final state.

## 8. Artifact tests

- immutable version;
- checksum/tamper detection;
- lineage tới workflow/run/node/attempt/agent/skill/model;
- archive/restore/compare;
- partial output không publish như approved final;
- traversal và unauthorized read.

## 9. API tests

- OpenAPI snapshot/schema;
- request/response/error/status contracts;
- Idempotency-Key same hash and conflict hash;
- If-Match stale write;
- SSE event schema/replay;
- compatibility routes cho UI hiện tại.

## 10. Security tests

- cross-workspace/path denied;
- restricted data/provider denied;
- policy conflict fail closed;
- unauthorized reviewer/approval;
- secret absent from all evidence;
- CLI sandbox/boundary;
- fallback không bypass policy;
- malicious tool/output cannot execute directly.

## 11. Prototype validations

Trước production CLI:

- verify stream-json behavior theo supported CLI versions;
- pipe vs PTY requirement;
- kill-tree behavior trên Windows/Linux target;
- workspace isolation effectiveness;
- Claude/Codex/NVIDIA event normalization;
- structured output compatibility.

PoC result phải được ghi thành evidence/ADR, không biến giả định research thành contract.

## 12. Release gates

### Local MVP

- Gateway routing + Executor conformance xanh.
- API and CLI fake adapters xanh.
- GO/NO-GO/HITL/retry/cancel/recovery xanh.
- Artifact version/lineage xanh.
- Critical security and secret scan xanh.

### Production

- approved CLI threat model/sandbox;
- load/capacity tests;
- backup/restore;
- SLO/alerting;
- incident and recovery runbook;
- no open P0 security/contract issue.

## 13. Traceability

Mỗi acceptance criterion phải map:

```text
Requirement/ADR
→ contract/schema
→ implementation task
→ test ID
→ runtime evidence
```
