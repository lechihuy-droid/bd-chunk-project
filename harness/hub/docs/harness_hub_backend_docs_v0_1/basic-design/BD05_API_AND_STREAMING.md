# BD05 - API and Streaming

```yaml
document_id: HH-BD-05
version: 0.1
status: In Review
owner: Backend
reviewers: [Runtime, Security, Frontend]
last_updated: 2026-07-28
depends_on: [BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md, BD04_GATEWAY_EXECUTOR_AND_PROVIDER_ADAPTERS.md, ../02_REQUIREMENTS_BASELINE.md, ../design/D05_API_AND_STORAGE_CONTRACTS.md]
source: [D03, D04, D05, D06]
```

## 1. Document control

This document owns HTTP/SSE transport contracts. It maps to Runtime and Gateway contracts but does not own their state or provider lifecycle.

## 2. Purpose and scope

In scope: existing `/api` compatibility, request/error/collection/command envelopes and SSE connection/replay semantics. Out: WebSocket, a public API-v1 decision, business state transitions and storage authority. Gate B/C apply. Any public-prefix migration stops for OD-01.

## 3. Context and boundary

SPA and local operator call FastAPI routes. Route handlers validate and map; application command service submits BD03 commands; read service returns bounded projections; SSE reads committed BD03 events. API MUST NOT call a provider or write Runtime files directly. Security middleware enforces local HTTP controls from BD07 before a state-changing command reaches a handler.

## 4. Design overview

```text
HTTP request -> route validation -> command/read facade -> Runtime or read model -> JSON envelope
SSE connect -> cursor validation -> committed event replay -> live subscription -> heartbeat/terminal
```

Current impact: `server.py` route inventory and current chat/workflow/Git streams. Migration centralizes duplicate resume routes onto one command facade without changing current UI path behavior.

## 5. Contract inventory

| Contract | Inputs / outputs | Error/side effect | Version/concurrency | Classification |
|---|---|---|---|---|
| JSON response | UTF-8/UTC body -> schema/correlation/data or safe error | 400/404/409/422 mapping; no trace/raw body | schema version + cursor | public..restricted redacted |
| State command | body, `Idempotency-Key`, `If-Match` -> accepted/result ref | command facade only; conflict has no side effect | BD03 command version | internal |
| Collection | validated filter/cursor -> bounded page/next cursor | unknown/malformed filter denied | cursor contract | internal |
| Runtime SSE | Last-Event-ID -> replay then live event stream | error after headers is SSE error; slow client bounded | per-run sequence | redacted |
| Legacy stream | existing chat/workflow/Git stream -> valid event stream | preserves terminal/error behavior | compatibility contract | internal |

## 6. Behavior flows

Happy command: validate body/header -> authorize/security check -> submit one command -> map accepted/complete result with correlation. Stale version or conflicting key maps to 409 and has no state side effect. Runtime SSE validates run/cursor, replays missing committed sequences before live delivery, sends heartbeat, bounds slow-client buffer and emits terminal/error event. If a derived event is missing, BD03 repairs/regenerates before transport exposes it. Invalid ID/path/payload is rejected before service access.

## 7. Persistence/config/deployment impact

No API handler owns persistence; response schema references BD03/BD06 records. Persisted cursors are event sequences, not client session state. Preserve `/api` and UI compatibility during incremental envelope changes. Breaking path/schema changes require a version/compatibility period, fixtures and migration note. Loopback/CSRF/body/stream limits are configured by BD01/BD07. WebSocket is N/A for local-v1.

## 8. Requirement traceability

| REQ/family | State | BD section | D source | Acceptance observable | Test ID / level | Gate | Owner/status |
|---|---|---|---|---|---|---|---|
| REQ-API-01 | MUST / VERIFIED | §3-6 | D05 §1,6 | current `/api` UI compatibility remains; invalid IDs/traversal/malformed payload denied | existing API/UI regression | B | Backend / In Review |
| REQ-API-02 | MUST / TARGET | §4-6 | D05 §1,4 | documented safe envelope/statuses; stale/key conflict has no side effect | API-001, ST-002 / contract | B,C | Backend / In Review |
| REQ-API-03 | MUST / VERIFIED | §3-6 | D05 §5 | current chat/run/workflow/Git endpoints emit valid SSE terminal/error under fakes | API-002 / integration | B | Backend / In Review |
| REQ-API-04 | MUST / TARGET | §4-7 | D03 §4,7; D05 §5 | reconnect replay-before-live has no state effect; heartbeat/buffer/error rules observable | API-002, EV-001/002 / integration | C | Backend + Runtime / In Review |
| REQ-API-05 | MAY / PROPOSED owner-required | §2, §7, §10 | D05 §1 | prefix change waits for owner compatibility/version decision | OD-01 / design review | B | Backend + Product / Blocked |

## 9. Acceptance and verification

Run `python -m pytest tests -q`, then API-001/API-002 and UI compatibility fixtures. Evidence: status/error matrix, idempotency/stale no-side-effect result, SSE reconnect transcript and bounded-client test. Backend/Frontend review Gate B; Runtime co-reviews Gate C replay behavior.

## 10. Open decisions and stop conditions

OD-01 determines `/api` versus `/api/v1`. Stop for a new public path, WebSocket, direct file mutation, provider call, unbounded stream buffering, security bypass, or wire-schema break without compatibility and owner review.

## 11. Change log and references

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-07-28 | Initial Basic Design allocation |

References: `../02_REQUIREMENTS_BASELINE.md`; `../design/D05_API_AND_STORAGE_CONTRACTS.md`; [BD03](BD03_RUNTIME_STATE_EVENTS_AND_RECOVERY.md), [BD04](BD04_GATEWAY_EXECUTOR_AND_PROVIDER_ADAPTERS.md), [BD07](BD07_SECURITY_GOVERNANCE_AND_CONTROLLED_EXECUTION.md).
