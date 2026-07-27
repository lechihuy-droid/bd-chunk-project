# Harness Hub Requirements Baseline v0.1

```yaml
document_id: HH-REQ-BASELINE-001
version: 0.1
status: Draft baseline for owner review
last_updated: 2026-07-27
owner: Harness Hub; product, runtime, backend, security, platform and QA owners to confirm
scope: Entire current Harness Hub in this repository, including control-plane UI APIs and workflow runtime
source_of_truth: Current code/tests for VERIFIED; D01-D08 for TARGET; R07 and open decisions for PROPOSED
implementation_status: Current implementation is not Gate C/D qualified; see REQ-RUN-06, REQ-SEC-08 and release gates
```

## 1. How to read this baseline

This document is a navigable requirements baseline for the Harness Hub that exists in this repository. It deliberately keeps three states separate:

| State | Meaning | Evidence rule |
|---|---|---|
| `VERIFIED` | Observed in `server.py`, services, fixtures or passing repository tests | Describes current behavior; does not imply the target contract is complete |
| `TARGET` | Normative local-v1 contract already stated in D01-D08 | Implementation must close the gap before the relevant release gate |
| `PROPOSED` | Useful requirement or evolution option not committed by the current sources | Owner decision and, where relevant, ADR/security/migration/test approval required |

Each requirement has a stable ID, priority (`MUST`, `SHOULD`, `MAY`), state, acceptance criteria, design references and test references. `MUST` is normative only within its stated state: a `TARGET MUST` is not evidence that the current code satisfies it.

The approved index establishes precedence: approved ADRs and D06 security invariants outrank domain/API/operations plans; implementation is evidence of as-is behavior and does not override target contracts. The design documents are currently `In Review`, so target requirements remain subject to the documented owner gates.

Primary sources: [`00_INDEX.md`](00_INDEX.md), [`01_OVERALL_ASSESSMENT.md`](01_OVERALL_ASSESSMENT.md), [`design/D01_ARCHITECTURE_AND_SCOPE.md`](design/D01_ARCHITECTURE_AND_SCOPE.md) through [`design/D08_TEST_AND_IMPLEMENTATION_PLAN.md`](design/D08_TEST_AND_IMPLEMENTATION_PLAN.md), [`reference/research/R07_RESEARCH_Synthesis_and_ADR_Recommendations.md`](reference/research/R07_RESEARCH_Synthesis_and_ADR_Recommendations.md), [`ARCHITECTURE.md`](../../ARCHITECTURE.md), [`server.py`](../../server.py), `services/`, and `tests/`.

## 2. Product vision and problem

### 2.1 Vision

Harness Hub is a local-first control and orchestration plane for one trusted operator: observe harness runs, sessions and usage; converse with configured providers; define and execute linear AI workflows; govern approvals, agents, skills, memory and artifacts; and expose an inspectable event stream and recovery trail through a web UI and FastAPI backend.

The target architecture is a FastAPI modular monolith on one Windows/local host with in-process services, file-backed runtime data, provider adapters, policy boundaries and SSE. It is not a distributed reliability or multi-tenant product in v0.1.

### 2.2 Problem being solved

The repository already contains many independently useful surfaces—chat, provider catalog, run/evaluation inspection, Git jobs, workflow execution, sessions/replay, usage, skills, memory and governance—but their contracts are uneven. The baseline must make the following visible and testable:

- what an operator can do now and through which API;
- what a run, node attempt, interrupt, event, artifact, provider and approval mean;
- which state transitions and filesystem effects are authoritative;
- where current implementation is weaker than the target local-v1 safety/durability contract;
- which future needs require an owner decision rather than silent scope expansion.

## 3. Stakeholders and personas

These are operational personas inferred from the current product surface and design documents, not commitments to a broader organization model.

| Persona | Need | Current interaction |
|---|---|---|
| Trusted operator | Ask a model, inspect work, start a workflow, respond to approval, read outputs | Web v3 UI and local API; local principal is `local_user` in target design |
| Workflow author | Validate/edit versioned YAML, configure agents/nodes/gates/layout, launch a run | `/api/workflows*`, `services/workflow.py`, workflow UI |
| Run reviewer | Follow progress, inspect state/events, replay, compare outputs, approve/reject | `/api/agent/runs*`, `/api/workflows/runs*`, `/api/runs*`, SSE |
| Harness/eval operator | Trigger suites, inspect logs/MEP, compare runs, verify integrity | `/api/runs/trigger`, `/api/suites*`, `/api/inspect/*`, `/api/integrity` |
| Git-job operator | Submit a brief, approve or reject a bounded job, inspect diff, accept/rollback | `/api/jobs*`, `services/gitjobs.py` |
| Governance/security owner | Review risk decisions, denials, degradation, secrets/path/child/skill behavior | `/api/governance`, `/api/guardrails/*`, audit-oriented services/tests |
| Runtime/platform owner | Maintain provider truth, file durability, recovery and deployment envelope | provider/runtime services, D03/D04/D07/D08 gates |
| Product owner | Decide supported providers, retention, controlled executor, MCP and evolution scope | OD/RD decisions in §12 |

No production identity/RBAC, tenant administrator or remote-worker persona is assumed. Those are `PROPOSED` evolution concerns.

## 4. Scope and non-scope

### 4.1 In scope

- Local FastAPI backend and web-facing API/SSE surface.
- Health, dashboard/read models and operational status.
- Direct provider chat and provider capability/status presentation.
- Existing harness runs, suites, integrity/evaluation inspection and comparisons.
- Git job lifecycle, approvals, diff, accept/rollback/reject and stream.
- Workflow definitions, validation, layout, agent profiles, linear execution and validation nodes.
- Runtime run/thread state, checkpoints, events, interrupts, replay and recovery hardening.
- Child runs and bounded governance.
- Artifacts, manifests/lineage/hash target contract and safe download/read boundary.
- Sessions, replay, usage, pricing/quota readouts and tool/behavior telemetry.
- Skills, skill library/drift/deploy log, memory candidates and governance settings.
- Local policy, CSRF/origin, path/secret/redaction, risk tiers and audit evidence.
- Provider/API/CLI adapters within their explicit capability and security profile.

### 4.2 Explicitly out of current target scope

The following are not current v0.1 product commitments: PostgreSQL, broker queue/outbox, multiple mutable server workers, distributed leases, multi-region/HA/active-active, production multi-tenant identity/RBAC, parallel/fan-out/fan-in/dynamic workflows, remote CLI workers, strong same-user Windows sandbox claims, privileged general tools, network-capable child runs, and MCP. Any addition requires an owner-approved ADR, migration/compatibility plan, threat review and acceptance tests.

## 5. Current VERIFIED baseline

### 5.1 System and deployment

- `server.py` exposes a FastAPI app titled `Harness Hub`, mounts the web-v3 assets when built, starts usage/behavior warmers, reconciles Git-job orphans, and kills tracked provider processes during lifespan shutdown.
- The default HTTP server binds `127.0.0.1`; mutating requests require the configured Hub client header and reject disallowed cross-origin requests. `tests/test_csrf.py` verifies this behavior.
- Configuration, workflows, agents, runtime, suites, logs, skill sources and caches are file-backed through `config.py` and service modules. Runtime state uses JSON and events use JSONL.
- Runtime IDs are validated by kind-specific patterns and paths are resolved under configured roots. Tests cover traversal and boundary rejection.
- Mutable JSON currently uses sibling temp write plus `replace`; the research/design baseline explicitly does not treat this alone as a power-loss durability guarantee.

### 5.2 API surface inventory

| Area | Current routes |
|---|---|
| Health/provider/chat | `/api/health`, `/api/chat/models`, `/api/providers`, `/api/model-classes`, `POST /api/chat` |
| Agents/risk/runtime runs | `/api/agents*`, `/api/risk-tiers`, `/api/agent/runs*` |
| Skills/memory/guardrails | `/api/skills*`, `/api/memory*`, `/api/guardrails/*` |
| Harness runs/jobs | `/api/runs*`, `/api/jobs*`, `/api/suites*`, `/api/integrity` |
| Usage/inspection/behavior | `/api/usage*`, `/api/tools`, `/api/inspect/*`, `/api/usage/cockpit` |
| Skill library | `/api/skill-library*` |
| Workflows | `/api/workflows*`, `/api/workflows/runs*` |
| Board/sessions/replay | `/api/board`, `/api/sessions*` |

The current API mostly returns direct lists/dictionaries and `HTTPException` details. D05 target conventions—schema version, correlation IDs, normalized error objects, `Idempotency-Key`, `If-Match`, cursor semantics and status/error matrix—are not to be inferred as fully implemented merely from route existence.

### 5.3 Current domain behavior

- Workflow validation supports YAML, required fields, agent and node validation, template references, stop caps and a linear IR. `agent` and `validate` node behavior is covered by `services/workflow.py`, `services/runtime_validate.py`, `tests/test_workflow.py`, `tests/test_runtime_validate.py` and `tests/test_workflow_templates.py`.
- Workflow execution currently creates file-backed runs, streams SSE-like events, writes node artifacts, checkpoints, enforces call/time/node budgets, supports approval interruption/resume and can spawn child runs. `services/workflow_exec.py` currently calls `get_provider()` directly; this is an assessed target gap, not a verified Gateway/Executor implementation.
- Runtime state supports threads, runs, status updates, checkpoints, events and interrupts. Current reducers/updates are file-backed and do not yet constitute the D03 transaction-journal/state-version/idempotency authority.
- Runtime artifacts currently write/read node Markdown files under a run artifact root and apply basic name/path boundaries. Immutable content-addressed manifest/version/scan semantics remain target requirements.
- Child-run records include parent linkage, objective, agent, allowed paths/tools, skills, budget, timeout and optional Git job; child completion/failure is reflected in parent state/events. Current subset enforcement has an empty-parent bypass identified by R07 F06 and must not be read as complete mediation.
- Agent profiles are YAML-backed and resolve model classes/providers; skills are discovered from configured source roots and support content hashes, drift reporting, usage lookup and deployment backups/logs. Memory supports listing candidates and accept/reject operations.
- Direct chat validates messages, optional agent/provider/model/session/skills, appends usage events, streams reasoning/delta/done/error events and reports skill truncation. The current provider contract is module-level `status()` and `stream_chat()`.
- Provider modules exist for NVIDIA API, Claude CLI, Codex CLI and Gemini CLI. Tests exercise fake providers/CLI parsers, status, streams, usage and process timeout/concurrency. R07 still classifies Codex and Gemini as NO-GO for target capability claims and Claude as low-assurance conditional until exact evidence and controls are in place.
- Harness runs and suites expose list/detail/artifact/compare/trigger/budget/stream and integrity verification. Git jobs use temporary repo/worktree flows, signed brief/tamper checks, risk/approval gates, event streams and accept/rollback/reject operations.
- Session replay parses Claude/Codex JSONL logs, produces outlines, agent/tool/result views, provenance/trust and risk tiers. Usage parses configured sources with per-file caches, filtering, rollups, provider grouping and pricing/quota cockpit data.

## 6. Key user journeys

### UJ-01 — Check and orient

1. Operator opens the SPA and checks `/api/health`.
2. UI loads providers, model classes, agents, workflows, runs, suites, governance, usage cockpit and board/session summaries.
3. Operator sees unavailable providers and degraded/governance signals as status, not as a false global health failure.

Acceptance: health/read endpoints return deterministic JSON; malformed/missing source files degrade to bounded warnings where current service contracts allow; no secret or unrestricted runtime path is returned.

### UJ-02 — Chat with a configured provider

1. Operator selects provider/model or agent profile and submits user/assistant messages.
2. Backend validates messages, resolves agent/provider/model and selected known skills.
3. Backend streams reasoning/delta/done/error SSE events and records normalized usage.
4. Operator sees provider/session/usage outcome and a safe error if the provider fails.

Target extension: route through Gateway/Executor with capability/policy checks, correlation, bounded retry and normalized lifecycle. Provider failure must not silently fall back after partial output.

### UJ-03 — Define, validate and run a workflow

1. Author loads source/model/layout, edits YAML, validates it and receives all deterministic errors.
2. Valid workflow is saved with backup/compatibility handling.
3. Operator starts a run with an objective; Runtime snapshots definition and agent profile, creates a run and streams progress.
4. Agent nodes execute; validate nodes check output deterministically; artifacts and checkpoints are persisted.
5. Approval gates interrupt the run; the reviewer resumes or rejects it; the run terminates exactly once.

### UJ-04 — Inspect and replay a run

1. Reviewer opens run projection, events, artifacts and usage.
2. Reviewer reconnects to the stream from a cursor and receives replayed then live events.
3. After restart or corrupt/torn derived data, Runtime recovers from the authoritative journal/projection contract, quarantining ambiguity and never replaying an external side effect blindly.

### UJ-05 — Run an eval/suite or compare harness output

1. Operator lists suites and integrity status.
2. Operator triggers a suite/check and follows the stream/budget.
3. Operator reads run detail/artifacts and compares two compatible runs.

### UJ-06 — Govern a Git job

1. Operator submits a non-empty brief and allowed agent.
2. System creates a bounded job/worktree, runs available checks, exposes status/diff/stream and applies risk/expiry/tamper controls.
3. Operator approves where allowed, then accepts, rolls back or rejects; orphan processes are reconciled on startup.

This journey is a current Git-job product surface, not a substitute for the D04 Executor contract.

### UJ-07 — Review sessions, usage and skills

1. Operator lists Claude/Codex sessions and opens replay with provenance and risk tiers.
2. Operator filters/rolls up usage by source/model/time/provider and views pricing/quota cockpit.
3. Operator inspects skills, hashes/drift/deploy log, uses a validated skill in chat, and reviews/accepts/rejects memory candidates.

### UJ-08 — Handle an unsafe or degraded action

1. Policy evaluates risk/path/data/provider/child/tool/action context.
2. Hard denial cannot be overridden by model confidence or fallback; the decision is recorded.
3. On suspected leakage/escape, operator cancels/kills tracked work, disables the route, quarantines evidence and waits for security review before resume.

## 7. Requirements by capability

### 7.1 Platform, health and dashboard

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-PLAT-01 | MUST / VERIFIED | Serve a local FastAPI control plane and web entrypoint, with health and core read models available. | `GET /` serves the built SPA when present; `/api/health` returns `ok`, configured root, runs directory and port; `tests/test_api.py::test_health`, `tests/test_ui_v3.py`. | D01 §2–§5; `server.py`; API-001 |
| REQ-PLAT-02 | MUST / TARGET | Default to one local process and loopback binding for mutable runtime state. | Startup/config rejects or clearly marks unsupported multi-worker mutation; non-loopback execution is blocked absent approved authentication/TLS/access-control ADR. | D05 §2, §8; D07 §1, §8; D06 §6; OPS-001 |
| REQ-PLAT-03 | SHOULD / TARGET | Present dashboard/read models for provider availability, runs, suites/integrity, governance, usage, tools, sessions and board without coupling them to `WorkflowRun`. | Read endpoints remain usable when one optional source is absent; provider outage does not make Hub health globally false. | D01 §3; D05 §6; D07 §9; `tests/test_api.py`, `test_cockpit.py`, `test_board.py` |
| REQ-PLAT-04 | SHOULD / TARGET | Expose structured correlation and safe operational status across requests, runs, executions, provider calls and SSE. | Logs/events contain IDs and durations but no raw prompt, secret, provider body or unrestricted host path; operational warnings are bounded. | D03 §4; D07 §5; D06 §11; OPS-002, SEC-002 |

### 7.2 Chat and providers

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-CHAT-01 | MUST / VERIFIED | Validate chat messages, provider/model/agent/session/skill references and stream user-visible reasoning/delta/done/error outcomes. | Invalid message roles/content/unknown references return 400; fake provider tests observe ordered stream and usage; provider/upstream errors are SSE errors rather than an unhandled 500. | `server.py`, `services/chat.py`; `tests/test_chat.py`, `test_providers.py` |
| REQ-CHAT-02 | MUST / TARGET | Route workflow/provider execution through a Runtime Gateway and Executor Port; Runtime must not call provider protocol directly. | `ExecutionRequest/Event/Result/Error` schemas exist; mock adapter and at least one API adapter conform; `workflow_exec.py` has no direct provider lookup after migration. | D01 §4, §7; D04 §1–§6; D08 Phase 1/3; EX-001 |
| REQ-CHAT-03 | MUST / TARGET | Publish provider capability truth separately for configured executable, resolved executable, observed version, candidate version, supported exact fixture and evidence provenance. | `supported=true` only follows a pinned conformance fixture; unknown/uninstalled/mismatched provider is explicit and cannot be selected as eligible. | D04 §3, §12; R07 F05; `tests/test_providers.py`; PROV-001 |
| REQ-CHAT-04 | MUST / TARGET | Apply policy, data classification, capability and limits before launch; classify failures and retry only bounded transient transport/rate-limit failures owned by the adapter. | No eligible route returns a normalized error; auth/policy/validation/capability/contract failures never fallback; partial output never silently falls back. | D04 §4, §7; D06 §3–§4; EX-002; SEC-002 |
| REQ-CHAT-05 | SHOULD / TARGET | Preserve a default-stateless provider session model; provider session IDs are references/hints, not source of truth. | Losing a provider session does not lose a persisted Hub run/thread; sticky CLI session/shared mutable memory are not required in local v1. | D04 §11; D02 §2; `tests/test_chat.py`, `test_replay.py` |
| REQ-CHAT-06 | MAY / PROPOSED owner-required | Add a scheduled real-provider smoke/conformance job for approved provider versions. | Product/runtime owners define provider set, freshness interval, credentials and data policy; deterministic CI remains fake/mock-only. | D08 §1, Phase 3; R07 RD-03 |

### 7.3 Harness runs, evaluations and suites

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-EVAL-01 | MUST / VERIFIED | List and inspect existing harness runs, suites, logs/MEP, artifacts, budgets and integrity; support compatible run comparison. | Existing endpoints return their service contracts; unknown suite/run/artifact and cross-suite compare are rejected; integrity reports tampering. | `server.py`, `services/runs.py`, `suites.py`, `inspect_evals.py`, `integrity.py`; `test_runs.py`, `test_suites.py`, `test_compare.py`, `test_integrity.py`, API-001 |
| REQ-EVAL-02 | MUST / VERIFIED | Trigger a suite/check and stream subprocess/evaluation progress with budget status. | Unknown suite is rejected; mocked trigger emits stream and budget; process timeout/concurrency limits are enforced. | `services/trigger.py`; `tests/test_api.py`, `test_providers.py` |
| REQ-EVAL-03 | SHOULD / TARGET | Normalize run/evaluation errors, correlation and lifecycle without conflating legacy harness runs with workflow runtime aggregates. | Read/trigger APIs adopt shared safe error/correlation conventions when changed; migration does not silently reinterpret legacy files as workflow state. | D05 §6; D01 §4; API-001 |
| REQ-EVAL-04 | SHOULD / PROPOSED owner-required | Define retention, reproducibility and provenance guarantees for external evaluation logs. | Product/QA/security specify source trust, retention, privacy and replay guarantees; until then expose current best-effort parsing and warnings only. | D06 §4, §11; D07 §7; OD-05/RD-07 |

### 7.4 Git jobs

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-GIT-01 | MUST / VERIFIED | Provide create, inspect, stream, approve, accept, rollback, reject and diff operations for configured Git jobs. | Brief/agent validation, 404s, lifecycle, diff and mocked streams pass; temp repo/worktree behavior is bounded. | `server.py`, `services/gitjobs.py`; `tests/test_gitjobs.py`, `test_api.py` |
| REQ-GIT-02 | MUST / VERIFIED | Apply risk, expiry, brief-signature/tamper and destructive-tier governance to job approval. | Destructive/expired/tampered jobs are denied unless the explicit current override contract allows it; denials update governance/degradation state. | `services/verify.py`, `governance.py`, `risk.py`; `test_gitjobs.py`, `test_governance.py`, `test_verify.py` |
| REQ-GIT-03 | MUST / TARGET | Treat Git jobs as a separate legacy/application surface until they satisfy D04/D06 typed Executor and controlled-executor contracts. | No requirement claims Git-job subprocesses are a production sandbox or substitutes them for Runtime Gateway; any workspace-write claim is Gate D only. | D05 §6; D04 §9; D06 §8; WIN-001 |
| REQ-GIT-04 | SHOULD / PROPOSED owner-required | Decide whether Git jobs remain a separate operator feature or migrate onto the shared Executor Port. | Product/runtime/security approve ownership, compatibility, rollback and threat model before code shares execution infrastructure. | D01 §4; D04 §1; OD-03/RD-04 |

### 7.5 Workflows, agents and skills

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-WF-01 | MUST / VERIFIED | Maintain versioned YAML workflow definitions with validation, normalized linear IR and layout sidecar. | Valid fixtures produce stable ordered IR; cycle, branch, unknown agent, invalid caps, bad template and malformed nodes are rejected with deterministic errors; layout does not change semantics. | `services/workflow.py`; `tests/test_workflow.py`, `test_workflow_templates.py`; WF-001/002 |
| REQ-WF-02 | MUST / TARGET | Freeze workflow schema v1: one start/end, linear chain, `agent`/`validate` nodes, explicit stop caps, supported checks and rejected unsupported graph semantics. | Validator rejects unsupported schema versions, branch/cycle/disconnected/self-edge/unknown agent/unresolved template and returns all path-specific errors; valid schema fixtures are compatible. | D02 §3–§5, §8–§10; WF-001/002 |
| REQ-WF-03 | MUST / VERIFIED | Support agent profiles with provider/model/system prompt/budget/risk/skill references and CRUD/list/read resolution. | Valid YAML profiles load; model classes resolve; invalid tier/skill/profile is rejected; API CRUD and list behavior remain regression-safe. | `services/runtime_agents.py`; `tests/test_runtime_agents.py`, `test_workflow_templates.py` |
| REQ-WF-04 | MUST / TARGET | Snapshot immutable workflow definition, agent profile, provider route and relevant skill hashes at run creation. | Editing current definitions/profiles/skills after run creation cannot alter replay or execution semantics; snapshot/hash fixtures reproduce the original result. | D02 §6–§8; D03 §7; SUP-001 |
| REQ-WF-05 | SHOULD / VERIFIED | Provide skill discovery, content read, source/hash/drift visibility, usage and deploy backup/log behavior. | Configured sources are scoped; duplicate sources collapse safely; drift/deploy/traversal tests pass; chat only activates known names and caps prompt content. | `services/runtime_skills.py`, `skill_library.py`; `test_runtime_skills.py`, `test_skill_library.py`, `test_chat.py` |
| REQ-WF-06 | MUST / TARGET | Pin active skill identity as `{source,name,content_hash}` and invalidate approvals/runs on shadowing or hash drift. | Same-name shadowing and content change fail closed or require revalidation; no skill text grants authority. | D06 §7, §10.1; R07 ADR-DR-11; SUP-001 |
| REQ-WF-07 | MAY / PROPOSED owner-required | Support non-linear workflows, reusable subgraphs or visual semantic branching. | Product/runtime approve graph semantics, state/event/retry/join contracts, migration and dedicated test suite before schema expansion. | D01 ADR-003; D02 §5; OD/RD owner decision |

### 7.6 Runs, sessions, replay and usage

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-RUN-01 | MUST / VERIFIED | Create/list/read runtime runs and threads with bounded IDs, state, metadata, messages, artifacts, checkpoints and events. | Runtime APIs and service tests create/read/list valid records; invalid IDs and outside-root paths fail; current state remains inspectable. | `services/runtime_state.py`; `tests/test_runtime.py`, `test_api.py` |
| REQ-RUN-02 | MUST / TARGET | Make Runtime the sole writer of run/node/interrupt state and enforce the D03 run/attempt/interrupt state machines. | Every valid transition is accepted once; invalid/terminal transitions are rejected; retry creates a distinct attempt; late/duplicate events cannot mutate terminal state. | D01 §4/§6; D03 §1–§3, §10; ST-001/002 |
| REQ-RUN-03 | MUST / VERIFIED | Provide workflow checkpointing, event emission, approval interruption and resume/reject behavior for current linear flows. | Golden/two-node, approval, resume, validation-fail and child-run tests pass; terminal SSE follows persisted state update. | `workflow_exec.py`, runtime services; `test_workflow_exec.py`, `test_runtime_validate.py`, `test_runtime.py`, E2E-001 |
| REQ-RUN-04 | MUST / TARGET | Use state version, per-run lock, idempotency ledger, expected-version commands and immutable checksummed transaction phases as local-v1 recovery authority. | Same key/same hash replays response; same key/different hash and stale version are 409 without side effect; fork/gap/corruption fails closed to recovery-required. | D03 §4.1/§6–§8; D05 §8; R07 ADR-DR-01–04; ST-002, DUR-001 |
| REQ-RUN-05 | MUST / TARGET | Treat runtime events as a derived, ordered UI/diagnostic timeline, regenerable from committed transactions; repair torn/corrupt tails explicitly. | Event sequence is per-run and resumable; missing events regenerate; corrupt/torn tail is quarantined with repair receipt; event replay never becomes state authority. | D03 §4/§7–§8; D05 §5/§8; EV-001/002, DUR-002 |
| REQ-RUN-06 | MUST / VERIFIED gap | Do not claim current file replace, checkpoint or JSONL behavior provides power-loss zero-loss, exactly-once external execution, or Gate C recovery readiness. | Release notes and status use the approved durability envelope only after R03 probes/crash matrix and owner sign-off; current assessment remains conditional/no-go for claims. | 01 assessment §2/§4; D03 §8; D07 §7; R07 F01/F02; DUR-001/002 |
| REQ-RUN-07 | SHOULD / VERIFIED | List Claude/Codex sessions and replay parsed outlines, messages/tool calls/results, provenance/trust and risk tiers. | Existing parsers handle fixtures, duplicate/unknown/traversal cases safely and report bounded summaries. | `services/replay.py`; `tests/test_replay.py`, `test_provenance.py`, `test_behavior.py` |
| REQ-RUN-08 | SHOULD / VERIFIED | Aggregate usage from configured chat/provider/Claude/Codex/Inspect sources with filters, per-file cache, token totals, pricing and cockpit/quota signals. | Parser warnings do not crash collection; source/model/since filters and rollups remain correct; unpriced models are explicit. | `services/usage.py`, parsers, `pricing.py`; `test_usage_parsers.py`, `test_usage_cache.py`, `test_cockpit.py`, `test_pricing.py` |
| REQ-RUN-09 | MAY / PROPOSED owner-required | Define durable cross-provider session continuation and shared mutable memory semantics. | Product/security/runtime define source of truth, privacy/classification, provider loss behavior, retention and migration before implementation. | D04 §11; D02 §2; RD-07 |

### 7.7 Child runs, approvals and governance

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-GOV-01 | MUST / VERIFIED | Support bounded child-run creation, parent linkage, task packet, child completion/failure, artifact merge and optional Git-job association. | Lead-only spawn, count/timeout/budget constraints, child isolation and parent outcome tests pass; failed child can be isolated per current contract. | `services/runtime_children.py`; `tests/test_childrun.py`, `test_runtime.py` |
| REQ-GOV-02 | MUST / TARGET | Define child authority as the intersection of parent capability, child profile, workflow policy and hard platform policy; missing/empty capability means none. | Empty parent lists cannot become unrestricted; a child cannot expand paths/tools/data/egress; CAP-001 and adversarial tests pass. | D04 §10; D06 §7/§10.1; R07 F06; CAP-001 |
| REQ-GOV-03 | MUST / VERIFIED | Expose risk tiers, guardrail decisions, denials and degradation status for current policy/governance behavior. | Decisions/denials are inspectable; degradation increases on denials and recovers only according to configured clean streak; risk tests pass. | `services/risk.py`, `runtime_policy.py`, `governance.py`; `test_risk.py`, `test_governance.py`, `test_api.py` |
| REQ-GOV-04 | MUST / TARGET | Bind every privileged approval to canonical action, exact args/targets, run/node/execution, data/secret/egress scope, policy/tool/skill/schema hashes and expiry. | Changed action, policy, schema, skill/content or target invalidates approval; duplicate/stale/replayed approvals have no new effect; approval is one-time and scope-bound. | D06 §10; R07 F08/ADR-DR-10; `test_childrun.py`, `test_gitjobs.py`, SEC-002 |
| REQ-GOV-05 | MUST / TARGET | Keep operational runtime events separate from append-only audit evidence for denials, approvals, settings, secret references, CLI launch/cancel and quarantine. | Security-sensitive actions have policy evaluation ID and audit record; raw secrets are absent; audit evidence is tamper-evident before production claims. | D03 §4; D06 §11–§12; D08 Phase 5; SEC-002 |
| REQ-GOV-06 | MUST / TARGET | Treat prompt, model output, retrieved content, child output, skill, memory, tool and MCP content as untrusted data with no authority. | Injection-shaped content cannot create a process/tool action; only typed canonical requests approved by deterministic policy can execute. | D06 §7; R07 F07; TOOL-001, SEC-002 |
| REQ-GOV-07 | MAY / PROPOSED owner-required | Enable MCP or privileged/write/network tools. | Remains disabled until typed tool kernel, registry/admission/auth/schema pinning, SSRF/egress/isolation tests and owner ADRs pass; otherwise route is denied. | D04 §10; D06 §10.2; D08 MCP-001; R07 ADR-DR-09/12, RD-06 |

### 7.8 Artifacts

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-ART-01 | MUST / VERIFIED | Write, list and read current workflow/run artifacts under the run boundary, with sanitized names and traversal rejection. | Node output can be listed/read; bad run/name/traversal is rejected; direct artifact tests pass. | `services/runtime_artifacts.py`; `tests/test_runtime_artifacts.py`, `test_runtime_validate.py`, `test_api.py` |
| REQ-ART-02 | MUST / TARGET | Publish artifacts as immutable versioned manifests with media type, size, SHA-256, run/node/attempt lineage, scan status and manifest-last visibility. | Rewriting an existing artifact creates a new version; hash/version is stable; content is scanned before exposure; orphan content is quarantined and never exposed as a manifest. | D02 §2/§7; D05 §8–§10; AR-001, SEC-002 |
| REQ-ART-03 | SHOULD / TARGET | Keep artifact download/rendering within authorization, classification, path and safe-link rules; never treat arbitrary workspace files as artifacts. | Only manifest-backed content is readable/renderable; restricted/quarantined content is denied; workspace path is not user-controlled absolute path. | D02 §7; D04 §2; D06 §7/§9; SEC-001/002 |
| REQ-ART-04 | MAY / PROPOSED owner-required | Introduce central content-addressed artifact index/object storage or retention deletion. | Artifact owner/product/security define lineage, deduplication, retention, privacy, backup and migration semantics; until then use per-run local target. | D05 §9–§10; OD-04/05; D07 §10 |

### 7.9 Memory, settings and governance operations

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-OPS-01 | MUST / VERIFIED | Allow operators to inspect memory and accept/reject candidate records, and inspect guardrail/governance state. | Candidate accept/reject validates IDs and persists expected current behavior; API tests cover runtime APIs. | `services/runtime_memory.py`, `runtime_policy.py`; `tests/test_runtime.py`, `test_api.py` |
| REQ-OPS-02 | MUST / TARGET | Accepted memory must have source provenance, reviewer/rationale, scope, classification, immutable hash and expiry/revocation; memory is never executable authority. | Unscoped/poisoned/expired memory is denied or excluded; changes invalidate dependent approval; MEM-001 passes. | D06 §10.1; R07 ADR-DR-11; MEM-001 |
| REQ-OPS-03 | SHOULD / VERIFIED | Keep configuration and deployment settings centralized, validate writable roots/providers at startup, and require restart/audit for security-boundary changes. | Missing route secret is reported without value; invalid roots/executables fail safe; settings are not silently expanded at runtime. | `config.py`; D07 §2–§3; D06 §5–§6; OPS-001 |
| REQ-OPS-04 | SHOULD / TARGET | Provide operator-visible degraded states for runtime corruption, provider auth/policy failures, disk low, event gaps, artifact mismatch, orphan process and startup validation failure. | Alerts/log warnings identify component/run/correlation and remediation; mutation stops or becomes read-only when store integrity is unsafe. | D07 §5–§9; D06 §12; OPS-001/002 |
| REQ-OPS-05 | MAY / PROPOSED owner-required | Define retention/deletion, privacy export and operator data lifecycle controls. | Product/security specify active-run protection, legal/privacy needs, cache vs backup set, deletion authorization and audit; no auto-delete is assumed before OD-05. | D05 §10; D07 §7; OD-05/RD-07 |

### 7.10 API and SSE

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-API-01 | MUST / VERIFIED | Preserve existing `/api` routes for current UI compatibility while validating request types and mapping common not-found/permission/value failures. | Existing API regression tests and SPA tests pass; invalid IDs, traversal and malformed payloads are rejected. | D05 §1/§6; `server.py`; `tests/test_api.py`, `test_ui_v3.py` |
| REQ-API-02 | MUST / TARGET | Standardize JSON API envelopes: UTF-8/UTC, schema version, correlation ID, safe error code/message/details, cursor collections, `Idempotency-Key` and `If-Match` for state commands. | Contract tests verify status 200/202/400/404/409/422 behavior, no stack trace/raw body/secret/host path, and no side effect on stale/idempotency conflict. | D05 §1/§4; API-001; ST-002 |
| REQ-API-03 | MUST / VERIFIED | Provide SSE for current chat, run, workflow and Git-job streams. | Current stream endpoints emit valid text/event-stream data and terminal/error events under fake/mocked sources. | `server.py`; `tests/test_chat.py`, `test_workflow_exec.py`, `test_gitjobs.py`, API-002 |
| REQ-API-04 | MUST / TARGET | Make runtime SSE resumable from persisted per-run sequence using `Last-Event-ID`, with replay-before-live, heartbeat, bounded slow-client buffer and error-after-headers semantics. | Reconnect has no lost/duplicated state effect; a committed transaction with missing derived event regenerates first; terminal stream is present. | D03 §4/§7; D05 §5; API-002, EV-001/002 |
| REQ-API-05 | MAY / PROPOSED owner-required | Change public path prefix from `/api` to `/api/v1`. | Backend/UI owner decides OD-01; if adopted, provide compatibility period or migration and schema/version note. | D05 §1; OD-01 |

## 8. Data, security and non-functional requirements

### 8.1 Data and persistence

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-DATA-01 | MUST / TARGET | Use validated IDs and canonical relative paths under configured roots; reject traversal, root/home/destructive broad targets, symlink/junction/reparse escapes and unsafe filenames. | Boundary/adversarial tests pass for runtime, artifacts, workflows, skills, suites and job paths. | D01 invariant 4; D05 §7/§11; D06 §9; `test_boundary.py`, `test_runtime_artifacts.py`, `test_skill_library.py`, SEC-001 |
| REQ-DATA-02 | MUST / TARGET | Persist timestamps as UTC ISO-8601 and mutable aggregate versions as integers incrementing once per successful command; preserve immutable snapshots and retry evidence. | Schema fixtures reject invalid IDs/timestamps/version changes; replay does not depend on current definitions. | D02 §2/§6; D03 §3; WF-001, ST-001 |
| REQ-DATA-03 | MUST / TARGET | Back up workflows, agents/policy config, runtime threads/runs/events/checkpoints, artifact manifests/content and audit evidence; exclude caches, temp execution dirs and raw secret files. | Restore into an empty validated root, verify hashes, run recovery scan, replay sample and verify artifact hash without auto-resuming lost execution. | D05 §10; D07 §7; OPS-002 |
| REQ-DATA-04 | SHOULD / PROPOSED owner-required | Define accepted local durability/RPO/RTO envelope. | Runtime/Product approve exact supported OS/Python/filesystem probes and only publish claims supported by R03 P01–P10/C01–C23 evidence; proposed manual restore objective is not an SLA until approved. | D03 §8; D07 §7; R07 RD-02 |

### 8.2 Security and governance invariants

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-SEC-01 | MUST / VERIFIED baseline + TARGET hardening | Apply loopback default, CSRF/client-header/origin controls, CORS deny by default, body/stream limits and no generic runtime-root static serving. | `tests/test_csrf.py` passes; forbidden cross-origin/missing-header mutation is rejected; non-loopback is blocked or has approved security ADR. | D05 §2; D06 §6; D07 §1; SEC-002 |
| REQ-SEC-02 | MUST / TARGET | Use classification `public/internal/confidential/restricted`; unknown is restricted; route/egress/provider selection cannot weaken classification policy. | Restricted data is denied to unapproved provider/CLI; fallback cannot bypass policy; policy decision records matched rules and safe reason. | D04 §4; D06 §3–§4; SEC-002 |
| REQ-SEC-03 | MUST / TARGET | Keep secrets in environment/secret-broker references only; pass minimal allowlisted env; redact known secrets from logs/events/errors/artifacts; never persist `.env` or raw provider body. | Fixtures and adversarial tests contain no raw secret leakage in request, stdout, error, event or artifact. | D04 §2/§8–§9; D06 §5; SEC-002 |
| REQ-SEC-04 | MUST / TARGET | Treat model/provider/CLI output and retrieved content as untrusted; typed tool requests, deterministic policy and exact capability receipts are required before action. | Injection content does not launch a tool/process; missing/empty permission is none; approval/capability changes invalidate execution. | D04 §10; D06 §7; TOOL-001, CAP-001, SEC-002 |
| REQ-SEC-05 | MUST / TARGET | Restrict CLI executable/argv/env/workspace, avoid shell interpolation, cap time/output, terminate process tree, scan/quarantine output and record exact executable/version. | CLI conformance and adversarial tests pass, or the profile is explicitly low-assurance/NO-GO; no network/filesystem containment claim is made from `Popen.kill()` or a watcher. | D04 §9; D06 §8; R07 F03/F04; EX-003, WIN-001 |
| REQ-SEC-06 | MUST / TARGET | Keep Hub non-elevated; controlled Windows executor is a separate Gate D subsystem requiring restricted identity, disposable workspace, enforceable quota and pre-provisioned/brokered/isolated egress. | Hostile/restricted workspace-write is denied until all controls and escape tests pass; WMI/COM/service/task-scheduler escape paths are tested. | D04 §9; D06 §8; D08 Phase 6; R07 ADR-DR-06/07; WIN-001 |
| REQ-SEC-07 | MUST / TARGET | Record append-only audit evidence for privileged/security actions and use incident response: cancel/kill, disable route, quarantine, revoke secret, preserve evidence, security review before resume. | Audit rows have action/context/policy evaluation and safe references; incident path is operationally testable; no automatic unsafe resume. | D06 §10–§12; D07 §6; SEC-002, OPS-001 |
| REQ-SEC-08 | MUST / VERIFIED gap | Do not claim current same-user CLI, provider adapter, child scope, memory, skill, tool or MCP behavior is production-safe beyond its tested profile. | Status/release docs show conditional/NO-GO evidence and owner gates; unsupported capability is denied, not silently advertised. | 01 assessment §4–§7; R07 §1–§3; PROV-001, CAP-001, SUP-001, MEM-001, MCP-001 |

### 8.3 Non-functional and operations

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-NFR-01 | SHOULD / TARGET | Measure health, cached read API, workflow overhead, persisted event-to-SSE delivery, cancel observation, recovery scan, active runs, SSE clients and artifact/output caps against owner-approved local objectives. | D07 initial objectives are instrumented and reported as engineering targets, not production SLAs; provider latency is separated from Hub SLO. | D07 §4–§5; OPS-001 |
| REQ-NFR-02 | MUST / TARGET | Degrade safely: reject new runs at active/disk/provider caps, preserve results through telemetry/cache failures, quarantine when scan unavailable and stop mutation on corrupt/unavailable runtime store. | Degraded paths are observable and tested; no fail-open artifact exposure or silent state mutation. | D07 §9; D06 §9; OPS-001/002 |
| REQ-NFR-03 | MUST / TARGET | Use deterministic tests with fake/mock providers; real provider smoke is opt-in and excluded from the deterministic regression suite. | `python -m pytest tests -q` remains canonical; no test requires live credentials/network; targeted contract tests add coverage without replacing regression. | D08 §1, §9; all `tests/` |
| REQ-NFR-04 | SHOULD / TARGET | Preserve module ownership boundaries: API does not call providers, workflow registry does not execute, Runtime owns state, Gateway owns route plan, Executor owns lifecycle, Policy does not execute, Artifact does not route. | Import/contract tests and code review show no new bypass; direct Runtime→provider path is absent at Gate C. | D01 §3–§4, §9; D08 Gate C |
| REQ-NFR-05 | MAY / PROPOSED owner-required | Set a supported shared-host/production availability, load, DR and HA envelope. | Platform/product approve Gate E topology, identity, storage, queue, object store, observability, load/soak/chaos/security tests and SLO/DR sign-off. | D01 §8; D07 §10; D08 Gate E |

## 9. Migration and compatibility requirements

| ID | Priority/state | Requirement | Acceptance criteria | Refs |
|---|---|---|---|---|
| REQ-MIG-01 | MUST / TARGET | Any public API, persisted schema, workflow schema, state machine or security-boundary change updates its owner contract, increments version when breaking, supplies compatibility/migration notes, maps tests and receives owner review. | A release cannot contain an unversioned breaking change or silently reinterpret existing local files. | 00_INDEX §5–§6; D02 §8; D07 §8 |
| REQ-MIG-02 | MUST / TARGET | Migrate runtime state incrementally to versioned projection/journal/checkpoint without treating current JSON/JSONL as already compliant. | Backup precedes migration; migration is idempotent or rollbackable; old files are quarantined/preserved where recovery is ambiguous; post-migration replay/hash checks pass. | D03 §4.1/§8; D05 §8/§10; DUR-001/002, OPS-002 |
| REQ-MIG-03 | MUST / TARGET | Preserve `/api` and existing UI behavior while adding schema/error/idempotency/SSE contracts. | Compatibility fixtures and UI tests remain green; duplicate resume routes call one application command service. | D05 §1/§4; `server.py`; API-001/002 |
| REQ-MIG-04 | SHOULD / TARGET | Migrate Runtime from direct provider calls to Gateway/Executor in staged phases: fixtures → mock port → runtime command/event hardening → provider conformance → artifacts/API → security/ops. | Each D08 phase gate is green before the next; no silent fallback or broadening of permissions is used to pass tests. | D08 §4; R07 §6 |
| REQ-MIG-05 | MAY / PROPOSED owner-required | Migrate from file-backed local v1 to database/queue/object storage/remote worker/multi-user identity. | New ADR covers need/SLO, ownership, failure model, security/threat review, compatibility, migration, rollback and acceptance tests; no current requirement assumes it. | D01 §8; D07 §10; D08 Gate E |

## 10. Release scopes and gates

| Release/scope | Included outcome | Exit criteria | Explicit exclusions |
|---|---|---|---|
| Current repository baseline | Existing Hub surfaces remain discoverable and regression-safe | `python -m pytest tests -q`; current UI/API/provider/workflow/Git/session/usage tests pass | No claim of target durability, Gateway purity or production sandbox |
| Phase 0 — Contract fixtures | Versioned workflow/execution/event/error fixtures; close empty-capability semantic bypass; provider status truth | `WF-*`, `ST-001`, provider truth fixtures green; existing tests unchanged | No runtime migration yet |
| Phase 1 — Executor Port | One workflow node through Gateway/mock adapter with normalized lifecycle | `EX-001`, golden two-node and provider failure tests green | No privileged tools/MCP; no controlled CLI claim |
| Phase 2 — Runtime hardening | State version, lock, idempotency, journal/checkpoint, derived events and repair | `ST-002`, `EV-*`, `OPS-001`, `DUR-*` green within owner-approved envelope | No exactly-once external side effects without evidence/reconciliation |
| Phase 3 — Provider conformance | API/CLI wrappers implement Executor contract and exact capability evidence | adapter conformance, version fixtures, cancel/error/session tests; Runtime no direct provider lookup | Codex/Gemini remain denied if evidence is absent |
| Phase 4 — Artifact/API | Immutable manifest/version/hash, normalized API concurrency/errors, resumable SSE | `API-*`, `AR-001`, UI compatibility green | No central object store/retention commitment |
| Phase 5 — Security/operations | Typed read-only tool kernel, action-bound approval, skill/memory provenance, audit, backup/restore | `CAP/TOOL/SUP/MEM-*`, `SEC-*`, `OPS-002` green | Privileged tools, network write, MCP disabled |
| Gate C — Local v1 | Qualified single-process local control plane and workflow runtime | `WF/ST/EV/EX/API/AR/SEC/OPS/E2E` plus regression, backup/restore, cancel/recovery demo, durability evidence, exact provider fixtures | Multi-worker/distributed, power-loss zero-loss and production sandbox claims |
| Gate D — CLI controlled (optional) | Controlled Windows executor | Executable/path/env/egress/quota/process-tree/escape/scan/skill-memory-tool tests and approved ADRs green | Must remain outside scope if product does not need workspace-write |
| Gate E — Production evolution | Authenticated/shared/distributed/remote operations | Approved identity/storage/queue/deployment ADRs, migration/rollback, load/soak/chaos/security tests and SLO/DR sign-off | Never inferred from local-v1 results |

## 11. Traceability matrix

The detailed tables above are the primary traceability. This compact matrix maps the requirement families to current implementation, design contracts and required test/gate evidence.

| Family | Stable IDs | Current evidence | Normative design | Test refs / gate |
|---|---|---|---|---|
| Platform/dashboard | PLAT-01..04 | `server.py`, `config.py`, API/UI tests | D01, D05, D07 | API/UI, OPS |
| Chat/providers | CHAT-01..06 | `services/chat.py`, `services/providers/*`, provider/chat tests | D04, D06, D08 | EX, PROV, SEC |
| Evals/suites | EVAL-01..04 | `runs.py`, `suites.py`, `trigger.py`, `inspect_evals.py`, integrity tests | D05, D07 | API, OPS |
| Git jobs | GIT-01..04 | `gitjobs.py`, verify/governance/risk tests | D04, D06 | SEC, WIN, owner ADR |
| Workflows/agents/skills | WF-01..07 | `workflow.py`, `runtime_agents.py`, `runtime_skills.py`, skill tests | D02, D04, D06 | WF, SUP |
| Runs/recovery | RUN-01..09 | `runtime_*`, `workflow_exec.py`, runtime/replay/usage tests | D02, D03, D05, D07 | ST, EV, DUR, OPS |
| Child/approval/governance | GOV-01..07 | `runtime_children.py`, `runtime_policy.py`, `governance.py`, child/Git tests | D04, D06 | CAP, TOOL, SEC, MEM, MCP |
| Artifacts | ART-01..04 | `runtime_artifacts.py`, artifact tests | D02, D05 | AR, SEC |
| API/SSE | API-01..05 | route inventory in `server.py`, API/chat/workflow/job tests | D05 | API, EV |
| Data/security/NFR | DATA-01..04, SEC-01..08, NFR-01..05 | boundary/CSRF/provider/process/governance tests | D01, D04, D06, D07 | SEC, WIN, OPS, Gate C/D/E |
| Migration | MIG-01..05 | current compatibility tests and file-backed services | 00_INDEX, D02, D03, D05, D08 | migration/release gates |

### 11.1 Test ID legend

`WF-001/002`, `ST-001/002`, `EV-001/002`, `EX-001/002/003`, `API-001/002`, `AR-001`, `SEC-001/002`, `OPS-001/002`, `E2E-001`, `DUR-001/002`, `PROV-001`, `WIN-001`, `CAP-001`, `TOOL-001`, `SUP-001`, `MEM-001`, `MCP-001` are the stable target test IDs defined by D08. Existing test function names in `tests/` are current evidence; a target ID is not considered green until the D08 acceptance behavior is implemented and verified.

Canonical regression command:

```powershell
python -m pytest tests -q
```

## 12. Open gaps and owner decisions

### 12.1 Decisions already recorded in the design baseline

- FastAPI modular monolith and local file-backed v1 remain the selected architecture.
- Workflow v1 remains linear; unsupported graph semantics are rejected.
- Runtime is the only owner of workflow state; Gateway routes but does not own state/retry.
- SSE is the one-way stream transport; WebSocket is outside v1.
- Security denial, auth, validation, capability and contract errors do not retry/fallback.
- Local CLI is restricted/low-assurance, not a production sandbox; workspace-write requires Gate D.
- Research informs gaps and gates but does not expand scope.

### 12.2 Owner-required decisions

| ID | Decision | Owner | Needed before |
|---|---|---|---|
| OD-01 | Keep `/api` with media/schema version or introduce `/api/v1` | Backend/product | API contract hardening |
| OD-02 | Store optimistic version in `run.json` or separate command ledger | Runtime | Transition/idempotency refactor |
| OD-03 | Reuse current provider CLI path or build separate workspace-writing executor | Runtime + security | Gate D planning |
| OD-04 | Per-run artifact manifests or central content-addressed index | Artifact owner | Artifact migration |
| OD-05 | Retention of runtime/events/artifacts/local logs | Product + security | Local-v1 release/backup policy |
| RD-01 | Approve projection + immutable journal as recovery authority | Runtime | Phase 2 |
| RD-02 | Approve local durability/RPO envelope for supported OS/filesystem | Runtime + product | Gate C claims |
| RD-03 | Approve provider set for Gate C | Product + runtime | Provider migration |
| RD-04 | Invest in controlled Windows executor or keep low-assurance read-only | Product + security | Gate D |
| RD-05 | Select pre-provisioned WFP, authenticated broker or Gate E isolated worker for egress | Security + platform | Any egress/isolation claim |
| RD-06 | Include MCP in near-term roadmap | Product + security | Typed MCP/admission design |
| RD-07 | Define skill/memory trust lifecycle, retention and revocation | Product + security | Phase 5 |
| RD-08 | Set local engineering targets as release objectives versus non-SLA guidance | Platform + product | Gate C release notes |

Agents/coders must stop and request clarification when a task depends on one of these choices, requires a new database/queue/remote service/permission, expands filesystem/network/secret scope, changes a public schema without migration, or needs a security claim not backed by the relevant gate.

## 13. Baseline acceptance and maintenance

This baseline is accepted for documentation only when D01–D08 are internally consistent, every open issue has an owner, and the index links remain valid. It becomes an implementation contract only after the relevant design documents and owner decisions are approved.

On every material change:

1. update the owning contract and this baseline requirement state/reference;
2. distinguish as-is evidence from target/proposed behavior;
3. version breaking API/schema/state/security changes;
4. add or update D08 test IDs and acceptance fixtures;
5. document migration/rollback and data classification;
6. preserve unrelated user changes and do not weaken tests or security checks to make a gate green.

### 13.1 Current overall readiness statement

The current repository is a strong substrate for a local-first Harness Hub and has broad functional coverage, but the overall assessment and R07 synthesis place implementation readiness at approximately 45–50% for Gate C and below 25% for Gate D. The safe release posture is therefore: current read/chat/workflow/Git/session/usage features may be used according to their tested local profiles; target durability, exact provider capability, complete mediation, controlled CLI isolation and production evolution remain gated requirements rather than present guarantees.
