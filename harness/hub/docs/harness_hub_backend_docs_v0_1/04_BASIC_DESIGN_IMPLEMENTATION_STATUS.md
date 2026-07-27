# Harness Hub Basic Design Implementation Status

## Audit metadata

| Field | Value |
|---|---|
| Audit time | 2026-07-28 (Asia/Tokyo) |
| Scope | Current code, tests, configuration and related sources in this repository |
| Design inputs | `02_REQUIREMENTS_BASELINE.md`, `03_BASIC_DESIGN_STRUCTURE.md`, `basic-design/BD01-BD08`, `design/D01-D08` |
| Evidence rule | Code/tests are as-is evidence. Requirements and design documents define expected behavior only. |
| Overall disposition | NOT Gate C/D qualified; substantial PARTIAL coverage with runtime correctness, execution-boundary, security and operations gaps. |

## Method and status standard

I read the baseline and the BD/D documents in dependency order, mapped each of the 77 baseline IDs to its single BD owner, inspected `server.py`, `config.py`, `services/`, provider modules and tests, and ran read-only checks. `IMPLEMENTED` requires code plus a relevant test/evidence path that satisfies the stated acceptance. A code substrate without the target contract or acceptance test is `PARTIAL`. `BLOCKED_DECISION` is used where the requirement is proposed and needs an owner/ADR decision; `NOT_APPLICABLE` is used for uncommitted evolution or explicitly out-of-scope capability. No document statement is treated as implementation evidence.

Allowed statuses are exactly: `IMPLEMENTED`, `PARTIAL`, `NOT_IMPLEMENTED`, `BLOCKED_DECISION`, `NOT_APPLICABLE`.

## Summary by BD

| BD owner | Scope | IMPLEMENTED | PARTIAL | NOT_IMPLEMENTED | BLOCKED_DECISION | NOT_APPLICABLE | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| BD01 | Architecture, modules, configuration | 1 | 4 | 0 | 0 | 0 | 5 |
| BD02 | Domain, workflow, profile | 3 | 3 | 0 | 1 | 0 | 7 |
| BD03 | Runtime state, events, recovery | 3 | 4 | 1 | 1 | 0 | 9 |
| BD04 | Gateway, executor, providers, Git boundary | 3 | 4 | 1 | 2 | 0 | 10 |
| BD05 | API and streaming | 2 | 2 | 0 | 0 | 1 | 5 |
| BD06 | Evaluation, artifacts, data, backup | 3 | 6 | 0 | 2 | 0 | 11 |
| BD07 | Governance and security | 3 | 12 | 1 | 1 | 0 | 17 |
| BD08 | Operations, NFR, migration | 1 | 7 | 1 | 2 | 2 | 13 |
| **Total** | **All 77 requirements** | **19** | **42** | **4** | **9** | **3** | **77** |

`NOT_IMPLEMENTED` is reserved for a committed target whose defining contract is absent even if adjacent legacy substrate exists. Proposed owner-dependent items are not counted as implementation defects.

## Full requirement status matrix

| REQ ID | BD owner | Expected state/priority | Implementation status | Evidence path:symbol/test | Gap | Confidence |
|---|---|---|---|---|---|---|
| REQ-PLAT-01 | BD01 | MUST / VERIFIED | IMPLEMENTED | `server.py:health,index`; `tests/test_api.py::test_health`; `tests/test_ui_v3.py` | None observed for stated local entrypoint/health acceptance. | High |
| REQ-PLAT-02 | BD01 | MUST / TARGET | PARTIAL | `server.py:lifespan`; `config.py`; `tests/test_csrf.py` | Loopback/default exists, but startup does not enforce one mutable worker or non-loopback ADR/TLS gate. | High |
| REQ-PLAT-03 | BD01 | SHOULD / TARGET | PARTIAL | `server.py:api_providers,api_runs,api_suites,api_governance,api_usage_cockpit,api_board`; `tests/test_api.py`, `test_cockpit.py`, `test_board.py` | Read surfaces exist, but optional-source isolation and provider-outage health contract are not fully tested/normalized. | Medium |
| REQ-PLAT-04 | BD01 | SHOULD / TARGET | PARTIAL | `server.py:_sse`; `services/runtime_events.py`; runtime/API tests | Streams exist, but correlation IDs, bounded structured logs and complete redaction contract are absent. | High |
| REQ-CHAT-01 | BD04 | MUST / VERIFIED | IMPLEMENTED | `server.py:api_chat`; `services/chat.py`; `tests/test_chat.py`, `test_providers.py` | None material against current acceptance. | High |
| REQ-CHAT-02 | BD04 | MUST / TARGET | NOT_IMPLEMENTED | `services/workflow_exec.py:get_provider`; `services/providers/*`; `tests/test_workflow_exec.py` | No typed ExecutionRequest/Event/Result/Error Port/Gateway; Runtime still resolves provider directly. | High |
| REQ-CHAT-03 | BD04 | MUST / TARGET | PARTIAL | `services/providers/__init__.py:list_providers,status`; `tests/test_providers.py` | Status reports availability/version in places, but no pinned conformance fixture/provenance truth or eligibility enforcement. | High |
| REQ-CHAT-04 | BD04 | MUST / TARGET | PARTIAL | `services/chat.py`; `services/providers/*`; `tests/test_chat.py`, `test_providers.py` | Current errors/retry behavior is provider-specific; no pre-launch typed policy/classification/capability decision or no-fallback contract. | High |
| REQ-CHAT-05 | BD04 | SHOULD / TARGET | PARTIAL | `server.py:api_chat`; `tests/test_chat.py`, `test_replay.py` | Chat can use provider session hints, but persisted Hub thread/run independence is not established by a target contract test. | Medium |
| REQ-CHAT-06 | BD04 | MAY / PROPOSED owner-required | BLOCKED_DECISION | `tests/test_providers.py` fake CLI/API fixtures only | Provider set, cadence, credentials and data policy require owner decision. | High |
| REQ-EVAL-01 | BD06 | MUST / VERIFIED | IMPLEMENTED | `server.py:api_runs,api_run,api_run_artifact,api_suites,api_integrity`; `services/runs.py,suites.py,integrity.py`; `tests/test_runs.py`, `test_suites.py`, `test_compare.py`, `test_integrity.py` | None material against current acceptance. | High |
| REQ-EVAL-02 | BD06 | MUST / VERIFIED | IMPLEMENTED | `server.py:api_trigger,api_run_stream`; `services/trigger.py`; `tests/test_api.py::test_trigger_streams_mocked_subprocess` | None material against current fake-trigger acceptance. | High |
| REQ-EVAL-03 | BD06 | SHOULD / TARGET | PARTIAL | `server.py` evaluation routes; `services/runs.py,inspect_evals.py`; `tests/test_api.py` | Existing surfaces work, but shared safe error/correlation/lifecycle normalization is not implemented. | High |
| REQ-EVAL-04 | BD06 | SHOULD / PROPOSED owner-required | BLOCKED_DECISION | `services/inspect_evals.py`; `tests/test_usage_parsers.py` | Retention, trust, privacy and replay guarantees are not owner-defined. | High |
| REQ-GIT-01 | BD04 | MUST / VERIFIED | IMPLEMENTED | `server.py:api_create_job,api_job,api_job_stream,api_job_diff`; `services/gitjobs.py`; `tests/test_gitjobs.py`, `test_api.py` | None material against current lifecycle acceptance. | High |
| REQ-GIT-02 | BD04 | MUST / VERIFIED | IMPLEMENTED | `services/verify.py,governance.py,risk.py`; `tests/test_gitjobs.py`, `test_governance.py`, `test_verify.py` | None material against current governance acceptance. | High |
| REQ-GIT-03 | BD04 | MUST / TARGET | PARTIAL | `services/gitjobs.py`; `tests/test_gitjobs.py` | Separate legacy surface is present, but controlled-executor boundary and explicit low-assurance/NO-GO signaling are not a typed contract. | High |
| REQ-GIT-04 | BD04 | SHOULD / PROPOSED owner-required | BLOCKED_DECISION | `services/gitjobs.py` | Shared Executor ownership, compatibility, rollback and threat model require decision. | High |
| REQ-WF-01 | BD02 | MUST / VERIFIED | IMPLEMENTED | `services/workflow.py`; `tests/test_workflow.py`, `test_workflow_templates.py` | None material against current linear validator/IR acceptance. | High |
| REQ-WF-02 | BD02 | MUST / TARGET | PARTIAL | `services/workflow.py`; `tests/test_workflow.py` | Linear/cycle/agent/template/cap checks exist, but frozen schema-v1 all-error contract and full graph rejection matrix are not complete. | High |
| REQ-WF-03 | BD02 | MUST / VERIFIED | IMPLEMENTED | `services/runtime_agents.py`; `tests/test_runtime_agents.py`, `test_workflow_templates.py` | None material against current profile CRUD/resolution acceptance. | High |
| REQ-WF-04 | BD02 | MUST / TARGET | PARTIAL | `services/workflow_exec.py:create_workflow_run_stream`; `services/runtime_agents.py`; `tests/test_workflow_templates.py` | Run creation does not prove immutable definition/profile/route/skill snapshots and replay equivalence. | High |
| REQ-WF-05 | BD02 | SHOULD / VERIFIED | IMPLEMENTED | `services/runtime_skills.py,skill_library.py`; `tests/test_runtime_skills.py`, `test_skill_library.py`, `test_chat.py` | Current discovery/hash/drift/deploy behavior is covered for the stated profile. | High |
| REQ-WF-06 | BD02 | MUST / TARGET | PARTIAL | `services/runtime_skills.py,skill_library.py`; `tests/test_runtime_skills.py`, `test_skill_library.py` | Hash/source metadata exists, but shadowing/drift does not invalidate approvals/runs through a fail-closed lifecycle. | High |
| REQ-WF-07 | BD02 | MAY / PROPOSED owner-required | BLOCKED_DECISION | `services/workflow.py` rejects non-linear semantics; `tests/test_workflow.py` | Non-linear/reusable graph semantics require owner decision and new contracts. | High |
| REQ-RUN-01 | BD03 | MUST / VERIFIED | IMPLEMENTED | `services/runtime_state.py`; `server.py:api_agent_runs,api_agent_run`; `tests/test_runtime.py`, `test_api.py` | None material against current record/list/read acceptance. | High |
| REQ-RUN-02 | BD03 | MUST / TARGET | PARTIAL | `services/runtime_state.py,runtime_reducers.py,runtime_interrupts.py`; `tests/test_runtime.py` | State transitions exist, but Runtime is not backed by the D03 authoritative command/state-machine/idempotency contract. | High |
| REQ-RUN-03 | BD03 | MUST / VERIFIED | IMPLEMENTED | `services/workflow_exec.py,runtime_checkpoint.py,runtime_events.py`; `tests/test_workflow_exec.py`, `test_runtime_validate.py`, `test_runtime.py` | Current linear golden/approval/validation behavior is covered. | High |
| REQ-RUN-04 | BD03 | MUST / TARGET | NOT_IMPLEMENTED | `services/runtime_state.py,runtime_checkpoint.py`; `tests/test_runtime.py` | No state version, per-run lock, idempotency ledger, expected-version command or checksummed transaction journal evidence. | High |
| REQ-RUN-05 | BD03 | MUST / TARGET | PARTIAL | `services/runtime_events.py`; `tests/test_runtime.py`, `test_runtime_validate.py` | JSONL events are emitted/read, but are not demonstrably derived/regenerable with torn-tail quarantine and repair receipts. | High |
| REQ-RUN-06 | BD03 | MUST / VERIFIED gap | PARTIAL | `services/runtime_state.py`; `tests/test_runtime.py`; `01_OVERALL_ASSESSMENT.md` is status context, not code evidence | Current replace/JSONL behavior has no crash-matrix enforcement; durability claims remain conditional. | High |
| REQ-RUN-07 | BD03 | SHOULD / VERIFIED | IMPLEMENTED | `services/replay.py`; `tests/test_replay.py`, `test_provenance.py`, `test_behavior.py` | None material against current parser/provenance acceptance. | High |
| REQ-RUN-08 | BD03 | SHOULD / VERIFIED | PARTIAL | `services/usage.py,pricing.py,behavior.py`; `tests/test_usage_parsers.py`, `test_usage_cache.py`, `test_cockpit.py`, `test_pricing.py` | Implementation exists, but the current quota aggregation acceptance test fails. | High |
| REQ-RUN-09 | BD03 | MAY / PROPOSED owner-required | BLOCKED_DECISION | `server.py:api_chat`; `tests/test_chat.py` | Durable cross-provider continuation/shared memory semantics require owner decision. | High |
| REQ-GOV-01 | BD07 | MUST / VERIFIED | IMPLEMENTED | `services/runtime_children.py`; `tests/test_childrun.py`, `test_runtime.py` | None material against current bounded child-run acceptance. | High |
| REQ-GOV-02 | BD07 | MUST / TARGET | PARTIAL | `services/runtime_children.py`; `tests/test_childrun.py` | Empty parent capability can become unrestricted; intersection/none semantics and CAP-001 are not closed. | High |
| REQ-GOV-03 | BD07 | MUST / VERIFIED | IMPLEMENTED | `services/risk.py,runtime_policy.py,governance.py`; `tests/test_risk.py`, `test_governance.py`, `test_api.py` | None material against current decision/degradation acceptance. | High |
| REQ-GOV-04 | BD07 | MUST / TARGET | PARTIAL | `services/runtime_interrupts.py,verify.py,gitjobs.py`; `tests/test_childrun.py`, `test_gitjobs.py` | Approval is not proven bound to all canonical action/target/hash/expiry fields as one-time receipt. | High |
| REQ-GOV-05 | BD07 | MUST / TARGET | PARTIAL | `services/runtime_events.py,governance.py`; governance/API tests | Operational events exist, but separate append-only tamper-evident audit evidence is not present. | High |
| REQ-GOV-06 | BD07 | MUST / TARGET | PARTIAL | `services/inform.py,risk.py,runtime_policy.py`; `tests/test_inform.py`, `test_risk.py`, `test_verify.py` | Some input sanitization and policy checks exist; no typed canonical action kernel proves untrusted content cannot execute. | High |
| REQ-GOV-07 | BD07 | MAY / PROPOSED owner-required | BLOCKED_DECISION | No MCP implementation; `tests/` has no MCP admission suite | MCP/tool enablement requires owner ADR and typed kernel/security tests. | High |
| REQ-ART-01 | BD06 | MUST / VERIFIED | IMPLEMENTED | `services/runtime_artifacts.py`; `tests/test_runtime_artifacts.py`, `test_runtime_validate.py`, `test_api.py` | None material against current path-bounded write/list/read acceptance. | High |
| REQ-ART-02 | BD06 | MUST / TARGET | PARTIAL | `services/runtime_artifacts.py`; `tests/test_runtime_artifacts.py` | Plain node Markdown files exist, but immutable versioned manifest, SHA-256, scan status and manifest-last visibility do not. | High |
| REQ-ART-03 | BD06 | SHOULD / TARGET | PARTIAL | `server.py:api_workflow_run_artifact,api_run_artifact`; `services/runtime_artifacts.py`; artifact tests | Boundary checks exist, but manifest-backed authorization/classification/render rules are absent. | High |
| REQ-ART-04 | BD06 | MAY / PROPOSED owner-required | BLOCKED_DECISION | `services/runtime_artifacts.py` per-run local files | Central object/index, deduplication and retention semantics require owner decision. | High |
| REQ-OPS-01 | BD07 | MUST / VERIFIED | IMPLEMENTED | `services/runtime_memory.py,runtime_policy.py`; `server.py:api_memory*`; `tests/test_runtime.py` | None material against current candidate/governance inspection acceptance. | High |
| REQ-OPS-02 | BD07 | MUST / TARGET | PARTIAL | `services/runtime_memory.py`; `tests/test_runtime.py` | Candidate acceptance lacks complete provenance/reviewer/rationale/scope/classification/hash/expiry/revocation and dependency invalidation. | High |
| REQ-OPS-03 | BD08 | SHOULD / VERIFIED | IMPLEMENTED | `config.py`; `tests/test_runtime_agents.py`, `test_boundary.py`, `test_csrf.py` | Current centralized paths/providers and safe missing-route behavior are covered for present scope. | Medium |
| REQ-OPS-04 | BD08 | SHOULD / TARGET | PARTIAL | `services/runtime_state.py,runtime_events.py,providers/procs.py`; `server.py:health`; tests across runtime/providers | No unified degraded-state model for corruption, event gaps, artifact mismatch, orphan process and low disk. | High |
| REQ-OPS-05 | BD08 | MAY / PROPOSED owner-required | BLOCKED_DECISION | `config.py` and file-backed stores have no retention/delete contract | Lifecycle, privacy export, deletion authorization and audit need product/security decision. | High |
| REQ-API-01 | BD05 | MUST / VERIFIED | IMPLEMENTED | `server.py`; `tests/test_api.py`, `test_ui_v3.py`, `test_boundary.py` | Existing `/api` compatibility and basic validation are covered. | High |
| REQ-API-02 | BD05 | MUST / TARGET | PARTIAL | `server.py` direct dict/`HTTPException` routes; `tests/test_api.py` | No standard envelope/schema version/correlation/cursor/Idempotency-Key/If-Match contract or complete 409/422 side-effect tests. | High |
| REQ-API-03 | BD05 | MUST / VERIFIED | IMPLEMENTED | `server.py:api_chat,api_agent_run,api_job_stream,api_run_stream,api_workflow_run`; `tests/test_chat.py`, `test_workflow_exec.py`, `test_gitjobs.py` | Current stream endpoints and terminal/error events are covered. | High |
| REQ-API-04 | BD05 | MUST / TARGET | PARTIAL | `server.py:api_agent_run_events`; `services/runtime_events.py`; runtime tests | Events can be read/streamed, but no Last-Event-ID replay-before-live, heartbeat, bounded slow-client buffer or event regeneration contract. | High |
| REQ-API-05 | BD05 | MAY / PROPOSED owner-required | NOT_APPLICABLE | Existing `server.py` `/api` routes; `tests/test_api.py` | `/api/v1` migration is an owner decision, not a current implementation defect. | High |
| REQ-DATA-01 | BD06 | MUST / TARGET | PARTIAL | `config.py`; `services/runtime_state.py,runtime_artifacts.py,skill_library.py`; `tests/test_boundary.py`, `test_runtime_artifacts.py`, `test_skill_library.py` | Common traversal checks exist, but symlink/junction/reparse, broad-target and all-surface adversarial coverage is incomplete. | High |
| REQ-DATA-02 | BD06 | MUST / TARGET | PARTIAL | `services/runtime_state.py,runtime_events.py`; `tests/test_runtime.py` | ISO timestamps exist, but aggregate integer versions, immutable snapshots and retry evidence are not implemented as a shared schema. | High |
| REQ-DATA-03 | BD06 | MUST / TARGET | PARTIAL | `config.py` file roots; runtime/artifact services | No backup/restore command or evidence for manifests/audit, hash verification, recovery scan and no-auto-resume restore. | High |
| REQ-DATA-04 | BD08 | SHOULD / PROPOSED owner-required | BLOCKED_DECISION | `services/runtime_state.py` current file writes; no R03 probe suite | Durability/RPO/RTO envelope needs owner-approved OS/filesystem probes and claims. | High |
| REQ-SEC-01 | BD07 | MUST / VERIFIED baseline + TARGET hardening | PARTIAL | `server.py:_csrf_guard`; `tests/test_csrf.py` | Loopback/CSRF/origin controls pass, but non-loopback security ADR gate, body/stream limits and static-serving hardening are not complete. | High |
| REQ-SEC-02 | BD07 | MUST / TARGET | PARTIAL | `services/runtime_policy.py,risk.py`; `tests/test_risk.py`, `test_governance.py` | Classification vocabulary and provider/egress enforcement are not implemented as a route decision contract. | High |
| REQ-SEC-03 | BD07 | MUST / TARGET | PARTIAL | `config.py`; `services/providers/*`; `tests/test_chat.py`, `test_providers.py` | Environment/API key handling and error tests exist, but complete minimal-env/redaction/no-raw-body fixture coverage is absent. | High |
| REQ-SEC-04 | BD07 | MUST / TARGET | PARTIAL | `services/inform.py,risk.py,verify.py`; `tests/test_inform.py`, `test_verify.py` | Untrusted-input checks exist, but typed tool request, capability receipt and approval invalidation are absent. | High |
| REQ-SEC-05 | BD07 | MUST / TARGET | PARTIAL | `services/providers/procs.py`; `tests/test_providers.py` | Timeout/concurrency tests exist, but no enforceable process-tree/argv/env/workspace/scan controls or exact executable receipt. | High |
| REQ-SEC-06 | BD07 | MUST / TARGET | NOT_IMPLEMENTED | `services/providers/*`; `tests/test_providers.py` | No separate controlled Windows executor, restricted identity, disposable workspace, hard quota, egress broker or escape tests. | High |
| REQ-SEC-07 | BD07 | MUST / TARGET | PARTIAL | `services/governance.py,runtime_policy.py,gitjobs.py`; `tests/test_governance.py`, `test_gitjobs.py` | Governance decisions exist, but append-only privileged audit and operational incident-response path are incomplete. | High |
| REQ-SEC-08 | BD07 | MUST / VERIFIED gap | PARTIAL | `services/providers/__init__.py`; `tests/test_providers.py`, `test_childrun.py`, `test_runtime_skills.py`, `test_runtime.py` | Some conditional behavior is tested, but no single release/status guard denies all unsupported provider/child/memory/skill/tool/MCP claims. | High |
| REQ-NFR-01 | BD08 | SHOULD / TARGET | PARTIAL | `server.py:health`; `services/usage.py,behavior.py`; `tests/test_cockpit.py`, `test_perf_skill_lookup.py` | Some read/perf/quota signals exist, but target latency, SSE, cancellation, recovery, active-run and artifact metrics are not instrumented end-to-end. | Medium |
| REQ-NFR-02 | BD08 | MUST / TARGET | PARTIAL | `services/runtime_state.py,runtime_artifacts.py,providers/procs.py`; runtime/provider tests | Limits and errors exist, but no unified safe-degradation/quarantine/read-only behavior for all caps and corrupt stores. | High |
| REQ-NFR-03 | BD08 | MUST / TARGET | PARTIAL | `tests/` fake providers/fixtures; `tests/test_providers.py`, `test_workflow_exec.py`; read-only pytest run | Deterministic tests use fakes/mocks and no live credentials, but the canonical suite is not currently green and requires environment plugin isolation. | High |
| REQ-NFR-04 | BD01 | SHOULD / TARGET | PARTIAL | `server.py`; `services/workflow.py,workflow_exec.py,runtime_state.py,providers/*`; `tests/test_workflow_exec.py` | Ownership seams exist, but direct Runtime→provider path violates the required boundary. | High |
| REQ-NFR-05 | BD08 | MAY / PROPOSED owner-required | NOT_APPLICABLE | No shared-host/HA/DR implementation in current scope | Production availability/load/DR/HA envelope is explicitly Gate E evolution. | High |
| REQ-MIG-01 | BD08 | MUST / TARGET | PARTIAL | `server.py`, workflow/config services; `tests/test_api.py`, `test_workflow.py` | Compatibility tests exist, but no enforced contract/version/migration review gate for every breaking API/schema/security change. | High |
| REQ-MIG-02 | BD08 | MUST / TARGET | NOT_IMPLEMENTED | `services/runtime_state.py,runtime_events.py,runtime_checkpoint.py`; `tests/test_runtime.py` | Current JSON/JSONL has no versioned projection/journal migration, backup-before-migrate, quarantine or rollback evidence. | High |
| REQ-MIG-03 | BD08 | MUST / TARGET | PARTIAL | `server.py`; `tests/test_api.py`, `test_ui_v3.py`, `test_chat.py` | `/api` and UI compatibility exists, but standardized errors, idempotency and duplicate-resume command routing do not. | High |
| REQ-MIG-04 | BD08 | SHOULD / TARGET | PARTIAL | `services/workflow_exec.py:get_provider`; `tests/test_workflow_exec.py`, `test_providers.py` | Staged migration has not reached Gateway/Executor; direct provider lookup remains. | High |
| REQ-MIG-05 | BD08 | MAY / PROPOSED owner-required | NOT_APPLICABLE | Current file-backed local services; no database/queue/object-store worker | Remote/shared-host evolution is not a current requirement without ADR, migration and rollback approval. | High |

## Critical gaps

1. **Runtime direct provider path (P0):** `services/workflow_exec.py` calls `get_provider()` directly. There is no typed Gateway/Executor Port or adapter conformance boundary. This blocks REQ-CHAT-02, REQ-NFR-04, REQ-MIG-04 and Gate C.
2. **State, journal, idempotency and recovery (P0):** `services/runtime_state.py`, `runtime_events.py` and `runtime_checkpoint.py` use JSON/JSONL/file replacement without state-version commands, per-run locking, idempotency ledger, immutable checksummed transaction phases, derived-event regeneration or torn-tail repair. This blocks REQ-RUN-02/04/05/06, REQ-DATA-02/03 and REQ-MIG-02.
3. **Provider capability truth (P0):** provider status and fake/CLI tests exist, but configured/resolved/candidate/observed versions, exact fixture support and evidence provenance are not one eligibility contract. REQ-CHAT-03 and REQ-SEC-08 remain conditional.
4. **API/SSE (P0):** routes return direct dictionaries/`HTTPException`; there is no schema-versioned envelope, correlation/error matrix, Idempotency-Key, If-Match or resumable per-run SSE with Last-Event-ID/heartbeat/replay repair. This blocks REQ-API-02/04 and the API portion of Gate C.
5. **Artifact manifest (P1):** `services/runtime_artifacts.py` writes node Markdown under run roots, but no immutable versioned manifest with media type/size/hash/lineage/scan/manifest-last visibility exists. This blocks REQ-ART-02/03 and AR-001.
6. **Child/tool/skill/memory/MCP (P0):** child empty-scope intersection is bypassable; typed action/capability receipts, action-bound approvals, skill drift invalidation, memory provenance/expiry and MCP admission are missing. This blocks REQ-GOV-02/04/06/07, REQ-WF-06, REQ-OPS-02 and REQ-SEC-04/08.
7. **Windows controlled executor (P0/Gate D):** provider process timeout/concurrency is not a controlled Windows sandbox. No restricted identity, disposable workspace, hard quota, brokered/pre-provisioned egress or WMI/COM/service/task-scheduler escape suite exists. REQ-SEC-05/06 remains no-go for hostile/restricted workspace-write.
8. **Operations/migration (P1):** no unified degraded-state/alert model, backup/restore drill, durability probe matrix, versioned runtime migration, retention policy or owner-gated release enforcement. A full regression run also has the current quota aggregation failure.

## Actionable priorities by dependency

| Priority | Dependency-ordered action | Mapping |
|---|---|---|
| P0.1 | Close contract fixtures and empty-scope child semantics; define typed action/capability/approval receipt and provider capability truth. | REQ-GOV-02, REQ-GOV-04, REQ-GOV-06, REQ-SEC-04, REQ-CHAT-03, REQ-WF-06; CAP-001, TOOL-001, SUP-001, PROV-001 |
| P0.2 | Implement Gateway/Executor Port, mock adapter and one API adapter; remove Runtime direct provider lookup; add no-fallback/partial-stream contract tests. | REQ-CHAT-02, REQ-CHAT-04, REQ-GIT-03, REQ-NFR-04, REQ-MIG-04; EX-001/002 |
| P0.3 | Implement state version, per-run command lock, idempotency ledger, expected-version checks, transaction journal and recovery/quarantine rules; add crash/torn-tail probes. | REQ-RUN-02/04/05/06, REQ-DATA-02/03, REQ-MIG-02; ST-001/002, EV-001/002, DUR-001/002, OPS-001/002 |
| P0.4 | Add API envelope/error/correlation/idempotency/If-Match contracts and resumable SSE replay/heartbeat/slow-client behavior. | REQ-PLAT-04, REQ-API-02/04, REQ-MIG-03; API-001/002 |
| P1.1 | Add immutable artifact manifests, content hash/version/lineage, scan/quarantine and manifest-backed authorization. | REQ-ART-02/03, REQ-DATA-01; AR-001, SEC-001/002 |
| P1.2 | Add classification/secret-redaction/audit evidence, safe degraded state, backup/restore and startup/runtime operational alerts. | REQ-PLAT-03/04, REQ-OPS-02/04, REQ-SEC-01/02/03/07/08, REQ-NFR-01/02 |
| P1.3 | Fix the observed quota aggregation regression, then rerun the canonical suite in a supported clean environment. | REQ-RUN-08, REQ-NFR-03 |
| P2.1 | Obtain owner decisions for real-provider smoke, eval provenance/retention, Git Executor ownership, non-linear workflows, cross-provider sessions, MCP, artifact index, lifecycle and durability envelope. | REQ-CHAT-06, REQ-EVAL-04, REQ-GIT-04, REQ-WF-07, REQ-RUN-09, REQ-GOV-07, REQ-ART-04, REQ-OPS-05, REQ-DATA-04 |
| P2.2 | Only after an approved Gate D ADR, build the separate controlled Windows executor and escape/quota/egress test package. | REQ-SEC-05/06; WIN-001 |
| P2.3 | Preserve current `/api` compatibility while documenting/versioning any future `/api/v1` or storage/worker evolution with migration and rollback. | REQ-API-05, REQ-NFR-05, REQ-MIG-01/03/05 |

## Commands/checks run

- `rg --files docs/harness_hub_backend_docs_v0_1 server.py config.py services tests` — inventory of requested docs/source/tests.
- `rg -o "REQ-[A-Z0-9-]+" docs/harness_hub_backend_docs_v0_1/02_REQUIREMENTS_BASELINE.md | Sort-Object -Unique` — baseline ID inventory; `REQ-BASELINE-001` is document metadata, leaving 77 requirement IDs.
- `rg -n "^def test_|^    def test_" tests --glob '*.py'` — test inventory.
- `rg -n "get_provider|ExecutionRequest|Executor|Gateway|idempot|journal|If-Match|Idempotency|Last-Event|manifest|sha256|scan|audit|child|memory|skill|MCP|sandbox|JobObject|WMI|COM|backup|restore|correlation|event" server.py config.py services tests` — implementation evidence sweep.
- `python -m pytest tests -q` — could not start under Python 3.14 because `pytest` is unavailable.
- `py -3.11 -m pytest tests -q` — could not start with auto-loaded `hydra` plugin due Python 3.11 dataclass incompatibility.
- `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; py -3.11 -m pytest tests -q` — 234 passed, 1 failed, 1 warning in 83.89s. Failure: `tests/test_pricing.py::test_cockpit_quota_pct_and_zero_quota`; warning: optional `inspect_ai` unavailable while reading a fixture.

## Audit limitations

This is an as-is implementation audit, not a code change or Gate approval. The full repository suite was not green in the available environments. No live provider, network smoke, crash/power-loss probe, backup/restore drill, Windows escape test, load/soak test or security penetration test was run. Existing documents were read for contract/acceptance and design ownership only; they were not counted as implementation evidence.

## QA result

The matrix contains the 77 baseline IDs exactly once; the status totals are 19 `IMPLEMENTED`, 42 `PARTIAL`, 4 `NOT_IMPLEMENTED`, 9 `BLOCKED_DECISION`, and 3 `NOT_APPLICABLE`, totaling 77. Status vocabulary is limited to the five allowed values. Markdown tables, inline code, and fenced command snippets are balanced and use repository-relative paths.
