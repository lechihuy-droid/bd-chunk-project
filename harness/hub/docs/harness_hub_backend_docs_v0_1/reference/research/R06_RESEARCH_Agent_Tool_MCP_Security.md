# R06 — Agent, Tool and MCP Security

```yaml
document_id: HH-RES-R06
version: 0.1
status: Research complete — architecture review required
owner: Security and Runtime
verified_at: 2026-07-27
research_mode: Luna-first evidence extraction; deep reasoning limited to privilege and policy conclusions
normative_authority: Reference only
normative_targets: [HH-DES-D04, HH-DES-D06, HH-DES-D08]
related_research: [HH-RES-R04, HH-RES-R05]
```

> Tài liệu này là research evidence, không phải coding contract. Các control được đề xuất chỉ trở thành normative sau khi được chấp nhận bằng ADR và merge vào D04/D06/D08.

## 1. Executive verdict

**NO-GO cho tool execution, MCP integration hoặc child-run có quyền write/network trong Gate D với implementation hiện tại.**

Harness Hub đã có một số nền tảng tốt:

- agent profile bắt buộc khai báo permission, risk tier, budget và skill;
- child-run chỉ do lead tạo và có giới hạn số lượng;
- workflow có approval gate;
- Git job có brief signature, TTL, worktree và review diff;
- memory chỉ chuyển từ candidate sang accepted bằng API riêng;
- skill library ghi nhận content hash và drift.

Tuy nhiên, các control này chưa tạo thành một authorization boundary hoàn chỉnh:

1. `allowed_paths`, `allowed_tools`, `skills` và `permission` phần lớn là metadata; provider execution không complete-mediate từng tool/action theo các trường này.
2. Child capability không được tính bằng giao của policy, parent capability và requested capability; parent list rỗng hiện có thể được hiểu là “không giới hạn”.
3. Output từ agent/child/artifact được đưa lại vào workflow context mà không mang nhãn trust/provenance và không có ranh giới dữ liệu–instruction.
4. Skill text được ghép trực tiếp vào system prompt theo tên; hash được tính nhưng không pin vào execution hay approval.
5. Memory acceptance có human action nhưng không lưu actor, source provenance, classification, review rationale, expiry hay immutable content hash.
6. Approval hiện là node/job approval tương đối rộng; chưa bind tới canonical action, exact arguments, target, secret scopes, data class, egress destination và policy/capability version.
7. Provider CLI có thể có tool/plugin/MCP riêng. Theo R04/R05, Hub chưa kiểm soát đầy đủ environment, config roots, process tree, network hoặc normalized tool events.
8. Không tìm thấy MCP client/server implementation trong source được review. Vì vậy mọi claim rằng MCP được sandbox, authorized hoặc audited đều là **UNKNOWN**.

Recommended security invariant:

> Model output, prompt, retrieved content, child output, skill text, memory text và MCP/tool result đều là untrusted data. Không đối tượng nào trong số đó được cấp quyền. Chỉ Policy Enforcement Point deterministic bên ngoài model mới có thể cấp một capability hẹp cho đúng một action canonical đã được validate.

Gate D chỉ mở khi `SEC-AG-*`, `SEC-TOOL-*`, `SEC-SUP-*`, `SEC-MEM-*`, `SEC-MCP-*` và các test Windows bắt buộc từ R04 đều xanh.

## 2. Evidence method và scope

### 2.1 Labels

- **VERIFIED-CODE** — quan sát trực tiếp trong source hoặc test.
- **VERIFIED-DOC** — được nêu trong primary/authoritative source.
- **INFERRED** — kết luận từ evidence; cần adversarial test để nâng độ tin cậy.
- **PROPOSED** — kiến trúc/control được đề xuất, chưa phải behavior hiện tại.
- **UNKNOWN** — chưa có code, official evidence hoặc prototype đủ để kết luận.

Mọi từ như “safe”, “isolated”, “approved”, “read-only” chỉ được dùng theo phạm vi control thực sự chứng minh. Permission ghi trong YAML hoặc prompt không phải OS/application authorization nếu executor không enforce.

### 2.2 Code scope đã review

- `hub/services/runtime_children.py`
- `hub/services/runtime_skills.py`
- `hub/services/skill_library.py`
- `hub/services/runtime_agents.py`
- `hub/services/runtime_policy.py`
- `hub/services/governance.py`
- `hub/services/runtime_memory.py`
- `hub/services/workflow_exec.py`
- `hub/services/gitjobs.py`
- `hub/services/providers/*`
- `hub/server.py`
- tests liên quan child-run, workflow, skills, runtime, governance, Git jobs và providers.

### 2.3 Primary sources

- OWASP GenAI LLM01 Prompt Injection, LLM06 Excessive Agency, LLM07 System Prompt Leakage và OWASP Top 10 for Agentic Applications 2026.
- NIST AI 600-1, Generative AI Profile.
- MCP Authorization specification 2025-06-18 và MCP Security Best Practices.
- Provider documentation chỉ được dùng ở R04/R05 khi liên quan trực tiếp tới tool/config/security surface.

Không thực hiện credentialed provider call, không cài MCP server và không chạy nội dung skill không tin cậy.

## 3. Trust boundaries và data flow

### 3.1 Current logical flow

```text
User/API
  │ objective, messages, selected skill names, approval action
  ▼
Hub API / Workflow Runtime
  │ loads agent YAML + raw SKILL.md + prior node/child output
  ▼
Provider Adapter / CLI or API
  │ model reasoning and provider-internal tools/plugins/MCP may exist
  ▼
Normalized text/reasoning/done/error events
  │
  ├──► runtime events / logs / artifacts
  ├──► parent claims and later workflow prompts
  ├──► memory candidate (via a separate caller)
  └──► future tool/MCP request surface
```

Trust boundaries:

| Boundary | Input is untrusted because | Required security decision |
|---|---|---|
| API → Runtime | user/browser/local process can craft payload | authenticate actor; validate schema and scope |
| File/skill/memory → Prompt | content may be modified or poisoned | provenance, trust label, content pinning, instruction isolation |
| Runtime → Provider | provider sees prompts, context and credential | data/egress policy; minimal secret and capability |
| Provider/model → Runtime | output is probabilistic and attacker-influenced | typed parse; no authority from prose |
| Parent → Child | parent output/objective may contain injection | capability intersection; immutable task packet |
| Child → Parent | child may be compromised or mistaken | treat claim/artifact as untrusted evidence |
| Runtime → Tool/MCP | action mutates external state or reveals data | complete mediation and action-bound approval |
| MCP → Upstream API | MCP server may be a deputy with separate identity | audience validation, separate token, per-client consent |
| Runtime → Persistent memory | content affects future runs | staged review, provenance, expiry and revocation |

### 3.2 Target flow

```text
untrusted content
      │
      ▼
Model proposes TypedActionRequest
      │ no side effect yet
      ▼
Schema + canonicalization
      ▼
Capability intersection
policy ∩ actor ∩ parent ∩ profile ∩ run ∩ tool
      ▼
Deterministic policy decision
      ├── deny → audit
      ├── require approval → exact action preview
      └── allow
             ▼
      Action-bound capability token
             ▼
      Tool/MCP Executor
             ▼
      bounded, labeled ToolResult
             ▼
      untrusted context + audit evidence
```

The LLM may propose an action. It must never mint, widen, interpret or approve its own authority.

## 4. Current implementation evidence

### 4.1 Agent and child-run capability

- **VERIFIED-CODE:** agent profiles require `provider`, `system_prompt`, `skills`, `permission`, `budget` and `risk_tier`; permission is constrained to `read_only|workspace_write`, risk tier to the configured enum (`hub/services/runtime_agents.py:16-17`, `:26-68`).
- **VERIFIED-CODE:** workflow checks only the child profile's coarse `risk_tier` against governance before spawn (`hub/services/workflow_exec.py:290-304`).
- **VERIFIED-CODE:** only a parent with `metadata.agent_id == "lead"` can spawn and there is a maximum child count (`hub/services/runtime_children.py:53-60`).
- **VERIFIED-CODE:** `_ensure_subset` checks child paths/tools only when the parent list is non-empty; an empty parent list returns without restriction (`hub/services/runtime_children.py:16-21`).
- **VERIFIED-CODE:** the child task packet stores requested paths, tools, skills, budget and timeout (`hub/services/runtime_children.py:24-45`, `:62-77`).
- **VERIFIED-CODE:** the workflow spawn call supplies objective, agent ID, budget and skills, but does not supply allowed paths/tools (`hub/services/workflow_exec.py:298-304`).
- **VERIFIED-CODE:** `_run_child` invokes the provider with prompt messages and model only; it does not pass/enforce child allowed paths, allowed tools, skill set, permission, timeout or budget as an execution capability (`hub/services/workflow_exec.py:85-126`).
- **INFERRED, CRITICAL:** child task metadata currently expresses intent, not enforceable least privilege. A provider-internal tool can act with the process/provider authority irrespective of the stored child packet.
- **PROPOSED:** empty capability sets mean “none”, never “unbounded”; wildcard access requires a distinct, policy-protected representation.

### 4.2 Prompt and cross-agent data handling

- **VERIFIED-CODE:** workflow system instructions are sent as a user-role message in both parent and child calls (`hub/services/workflow_exec.py:96-104`, `:261-269`).
- **VERIFIED-CODE:** child objective can interpolate prior node output; raw child output is persisted in `claims.jsonl` and placed in `node_outputs` for later templates (`hub/services/workflow_exec.py:123-132`, `:298-314`).
- **VERIFIED-CODE:** successful child artifact rows are copied into parent state with only `source_run_id` added (`hub/services/runtime_children.py:140-164`).
- **INFERRED, HIGH:** malicious content in a source file, provider result or child output can cross an agent boundary and become instruction-like context. Role labels such as `SYSTEM INSTRUCTIONS:` inside a user message do not enforce privilege.
- **VERIFIED-DOC:** NIST AI 600-1 distinguishes direct and indirect prompt injection and notes that indirect injection can be planted in remotely retrieved data. OWASP LLM06 identifies malicious peer agents and compromised extensions as triggers for excessive agency.
- **PROPOSED:** preserve content as typed evidence with origin/trust labels and delimit it from control instructions; never promote an artifact by trusting metadata supplied by the child.

### 4.3 Skills and supply chain

- **VERIFIED-CODE:** skill sources include user and project directories (`hub/services/skill_library.py:29-44`).
- **VERIFIED-CODE:** the library computes SHA-256 over all skill files and exposes source/hash/drift metadata (`hub/services/skill_library.py:90-106`, `:171-185`, `:381-405`).
- **VERIFIED-CODE:** agent validation checks that the skill name exists, not that a particular source/hash is approved (`hub/services/runtime_agents.py:41-48`).
- **VERIFIED-CODE:** chat resolves a requested name, reads the first matching `SKILL.md`, and directly concatenates its raw content into the system prompt, subject only to a character cap (`hub/server.py:121-158`, `hub/services/skill_library.py:367-378`).
- **VERIFIED-CODE:** duplicate skill names across sources are represented in drift output, but `read_skill_content(name)` returns the first match according to configured source iteration (`hub/services/skill_library.py:369-375`).
- **VERIFIED-CODE:** deploy copies a skill tree into another configured source and logs source ID, target and path; no signature/trust approval is enforced in this function (`hub/services/skill_library.py:434-477`).
- **INFERRED, HIGH:** same-name shadowing, post-selection mutation or an unreviewed project skill can alter the effective high-priority instructions without changing the agent profile.
- **PROPOSED:** activation identifier must be `{source, name, content_hash}`; run creation pins that identity; hash mismatch fails closed. “Read-only skill” means the skill package itself is not modified, not that its instructions are safe.

### 4.4 Memory

- **VERIFIED-CODE:** memory enters a pending candidate list and only an explicit accept transition copies the raw candidate text/metadata into `memory.jsonl` (`hub/services/runtime_memory.py:46-83`).
- **VERIFIED-CODE:** API exposes separate accept/reject endpoints (`hub/server.py:353-380`).
- **VERIFIED-CODE:** accepted records include candidate ID, text, timestamp and caller-supplied metadata; no reviewer identity, source trust, rationale, expiry or content hash is mandatory (`hub/services/runtime_memory.py:74-83`).
- **VERIFIED-DOC:** OWASP ASI06 describes persistent memory/context poisoning as malicious or misleading data influencing future reasoning, planning or tool use.
- **INFERRED, HIGH:** human acceptance reduces accidental persistence but does not prove the reviewer saw the source or understood embedded instructions. A socially engineered candidate can become a durable control-plane influence.
- **PROPOSED:** memory stores scoped facts/preferences with provenance, never executable instructions or authority; retrieval preserves trust and source labels.

### 4.5 Policy and approval

- **VERIFIED-CODE:** command policy classifies a command into one coarse tier and denies it only if that tier is in `effective_blocked_tiers()` (`hub/services/runtime_policy.py:31-44`).
- **VERIFIED-CODE:** default governance blocks configured tiers, adds network at degradation 2, execute at 3 and all non-read tiers at 4 (`hub/services/governance.py:56-73`).
- **VERIFIED-CODE:** workflow approval gate stores node ID, rendered prompt and objective before provider execution (`hub/services/workflow_exec.py:247-259`).
- **VERIFIED-CODE:** Git jobs begin `awaiting-approval`; brief integrity and TTL are checked before launch (`hub/services/gitjobs.py:382-429`, `:496-517`).
- **VERIFIED-CODE:** Git jobs copy the complete process environment and launch a CLI with workspace-write after approval (`hub/services/gitjobs.py:545-556`); R04 classifies this as a critical secret/authority gap.
- **VERIFIED-CODE:** `allow_override=True` can bypass a blocked tier check (`hub/services/gitjobs.py:536-543`; `hub/tests/test_gitjobs.py:240-276`).
- **INFERRED, HIGH:** current approval authorizes a broad node or job, not an exact future tool action. The action target and side effects may be chosen later by model/provider behavior.
- **PROPOSED:** approval cannot override OS containment, secret boundaries, data classification, tool schema or provider capability. Override is permitted only for an explicitly overridable business policy.

### 4.6 Provider and MCP surface

- **VERIFIED-CODE:** no production MCP client/server/authorization implementation was found in reviewed `hub/services` and tests.
- **VERIFIED-CODE:** provider protocol exposes `status()` and `stream_chat()` but no typed tool request, action handle, authorization context or MCP identity (`hub/services/providers/base.py:6-34`; R05 §1–4).
- **VERIFIED-CODE:** provider adapters do not normalize provider tool events into policy-mediated requests; Claude denies only selected tools, Codex uses a provider sandbox flag, Gemini has no reviewed tool restriction (R04 §3.4; R05 capability matrix).
- **INFERRED, CRITICAL:** a CLI-discovered plugin/MCP/tool could execute outside Hub policy unless provider config roots and tools are disabled/allowlisted and every action is surfaced through a mediated protocol.
- **VERIFIED-DOC:** MCP security guidance states that local MCP servers run with the same privileges as the client unless separately sandboxed; it recommends minimal privileges and restricted filesystem/network access.
- **UNKNOWN:** which future MCP transport, server registry, OAuth mode, discovery mechanism and tool schemas Harness intends to support.

## 5. Abuse-case catalogue

| ID | Abuse case | Attack chain | Current control | Gap | Severity |
|---|---|---|---|---|---|
| AG-T01 | Indirect prompt → tool execution | malicious repo/artifact text tells model to invoke write/network tool | prompt labels; coarse risk | content can influence action selection; no typed mediation | Critical |
| AG-T02 | Tool-result injection | tool/MCP result contains instructions to call another tool or reveal secrets | none observed | result re-enters model as undifferentiated content | High |
| AG-T03 | Parent-child confused deputy | parent gives child benign objective containing attacker-controlled output; child uses broader authority | lead-only spawn; risk tier | child capability metadata not enforced | Critical |
| AG-T04 | Child capability escalation | parent scope empty; child requests paths/tools or provider uses implicit tools | subset helper | empty parent means unrestricted check; workflow omits scopes | Critical |
| AG-T05 | Artifact laundering | child labels arbitrary path/result as artifact; parent treats it as trusted claim | adds `source_run_id` | no schema, hash, path, trust or content scan before promotion | High |
| AG-T06 | Secret propagation | Hub env/secret enters provider, stdout, child claim, log or later prompt | partial sanitizer/redaction intent | full environment; raw outputs/events | Critical |
| AG-T07 | Egress by deputy | injected content makes model/tool send context to approved-looking endpoint | governance `network` tier | no destination/data binding or enforceable egress | Critical |
| AG-T08 | Skill shadowing/poisoning | malicious same-name project skill wins lookup or changes after selection | content hash and drift visibility | activation by name; no trust/signature/hash pin | High |
| AG-T09 | Skill package side-load | deployed skill includes malicious referenced script/config | backup + deploy log | no package policy, signature, allowlist or review receipt | High |
| AG-T10 | Memory poisoning | injected text becomes candidate; user accepts vague summary; future runs treat it as instruction | explicit accept/reject | no provenance/reviewer/scope/expiry; raw text retained | High |
| AG-T11 | Approval replay/scope drift | approval for one prompt reused after args, target, policy or skill hash changes | job TTL and brief signature | no canonical action/capability/policy hash binding | Critical |
| AG-T12 | Approval fatigue | many low-context prompts cause user to approve harmful action | HITL gate | no grouping, risk summary, novelty signal or rate limit | High |
| AG-T13 | MCP token passthrough | client token forwarded to downstream API | not implemented | future architecture unspecified | Critical when MCP enabled |
| AG-T14 | MCP confused deputy | malicious MCP client reuses proxy consent/static client | not implemented | per-client consent/identity absent | Critical when MCP enabled |
| AG-T15 | MCP SSRF/discovery abuse | malicious metadata points OAuth discovery to internal host | not implemented | URL/network validation absent | High when remote MCP enabled |
| AG-T16 | MCP schema/tool rug pull | approved server changes tool description/schema after approval | not implemented | no server/tool hash pin or change invalidation | High |
| AG-T17 | Cross-run session authority | provider session resumes with prior tools/context/credentials | provider session optional | capability equality on resume not proven | High |
| AG-T18 | Unbounded delegation | child output triggers further work/cost or repeated approvals | max child and agent budgets | no delegation depth, aggregate tool/egress budget | Medium/High |

## 6. Required authorization and capability model

### 6.1 Policy precedence

**PROPOSED ADR candidate: `ADR-SEC-AG-001 Deterministic Complete Mediation`.**

Effective capability:

```text
hard platform policy
∩ data-class policy
∩ authenticated actor grants
∩ parent-run capability
∩ agent-profile capability
∩ workflow-node requirement
∩ provider/tool manifest
∩ current degradation policy
∩ approval receipt (when required)
```

Rules:

1. Every set is explicit. Missing/empty means no capability.
2. A child cannot receive a capability absent from the parent.
3. Prompt/model/tool output cannot add an element to any set.
4. Deny takes precedence. Approval cannot override a hard deny.
5. Capability is action/resource-specific, time-bounded, single-use by default and tied to one run/attempt.
6. Resume/retry requires the same or narrower capability hash. Any policy, skill, server schema or target change invalidates prior approval.
7. Tool executor checks the capability immediately before the side effect; planning-time checks alone are insufficient.

### 6.2 Typed action request

```json
{
  "schema": "hh.tool-request/1",
  "request_id": "trq_...",
  "run_id": "run_...",
  "attempt_id": "att_...",
  "actor": {"user_id": "local-user", "agent_id": "reviewer"},
  "parent_run_id": "run_parent_or_null",
  "source": {
    "node_id": "implement",
    "model_output_event_id": "evt_...",
    "untrusted_input_refs": ["artifact:sha256:..."]
  },
  "tool": {"server_id": "builtin.fs", "name": "write_file", "schema_hash": "sha256:..."},
  "action": "write",
  "arguments": {"path": "hub/example.py", "content_ref": "artifact:sha256:..."},
  "resources": {
    "paths": ["hub/example.py"],
    "egress_destinations": [],
    "secret_refs": [],
    "data_classes": ["internal"]
  },
  "limits": {"calls": 1, "bytes_read": 0, "bytes_written": 4096, "seconds": 10},
  "idempotency_key": "...",
  "capability_hash": "sha256:...",
  "policy_version": "policy-...",
  "requested_at": "..."
}
```

Requirements:

- canonical JSON serialization before hashing/approval;
- tool-specific strict schema; unknown fields rejected;
- path/URL/identifier canonicalization before policy evaluation;
- raw shell and arbitrary URL fetch are not baseline tools;
- `secret_ref` resolves inside executor only and value never returns to model;
- request contains provenance of untrusted inputs that influenced it;
- tool cannot alter target/args after decision;
- result includes same request ID, capability hash, actual resources touched and bounded evidence.

### 6.3 Decision and capability receipt

```json
{
  "schema": "hh.policy-decision/1",
  "decision_id": "pd_...",
  "request_hash": "sha256:...",
  "decision": "allow|deny|require_approval",
  "matched_rules": ["data.internal.egress-deny"],
  "reasons": ["network destination is not allowlisted"],
  "overridable": false,
  "policy_version": "policy-...",
  "evaluated_at": "..."
}
```

An allow decision produces a non-transferable capability receipt bound to:

- actor, run, attempt and parent run;
- exact tool/server/schema;
- canonical action/arguments/resource set;
- data class and secret references;
- policy and capability manifest versions;
- expiry, call count and idempotency key.

The receipt is consumed by the executor, not shown to or editable by the model.

## 7. Parent-child security contract

**PROPOSED ADR candidate: `ADR-SEC-AG-002 Child Capability Intersection`.**

### 7.1 Spawn request

Child spawn must be a typed request with:

- objective as untrusted task data;
- parent run/attempt/node identity;
- requested agent/profile version;
- requested paths, tools, skills, provider, data classes and egress;
- per-child and aggregate delegation budgets;
- maximum depth;
- immutable source refs for parent outputs included;
- `use_gitjob` separated as a privileged execution request, not a boolean hidden in task data.

Runtime calculates the child capability intersection. It never accepts the child's or model's self-declared risk tier as authority.

### 7.2 Child input

- Parent/model output is wrapped as `UntrustedEvidence`, not concatenated with system instructions.
- The child's trusted control prompt is loaded from a pinned profile/skill bundle.
- Child receives references to allowed artifacts, not an unrestricted parent state dump.
- If the provider cannot preserve trusted-control versus untrusted-data roles, the adapter declares that limitation and the workflow cannot use it for privileged child actions.

### 7.3 Child output

- Claims are typed: statement, evidence refs, confidence, producer, provider/model/version and content hash.
- Artifact promotion re-resolves and verifies the child-owned path, content hash, media type, size, malware/secret policy and provenance.
- Parent never automatically treats child prose as a command, approval or policy fact.
- A failed or compromised child cannot alter parent capability, approval state or memory.

### 7.4 Delegation limits

- v1 default maximum depth: 1;
- maximum children and aggregate calls/time/cost inherited from parent;
- no child spawning unless explicitly enabled by workflow policy;
- child cannot request a provider, tool or egress class broader than parent;
- cancellation cascades to children and their tool executions;
- terminal parent waits for or cancels all children.

## 8. Skill supply-chain contract

**PROPOSED ADR candidate: `ADR-SEC-SUP-001 Pinned Trusted Skills`.**

### 8.1 Trust states

```text
discovered → quarantined/unreviewed → reviewed → approved → revoked
```

Only `approved` skills may enter a privileged agent prompt. Discovery and hash calculation do not imply approval.

Skill identity:

```json
{
  "source": "codex_user",
  "name": "example",
  "version": "declared-or-local",
  "content_hash": "sha256:...",
  "publisher": "local-user-or-package",
  "trust_state": "approved",
  "review_receipt": "sr_...",
  "capability_requirements": {
    "tools": ["builtin.fs.read"],
    "paths": ["hub/docs/**"],
    "network": []
  }
}
```

### 8.2 Activation requirements

- agent/workflow references full skill identity, never bare name;
- duplicate name is an error unless source/hash are pinned;
- run snapshots the approved skill manifest and hash;
- hash change invalidates agent profile cache and existing approval;
- skill content is delimited and explicitly labeled as third-party instructions;
- referenced scripts/assets are included in the package hash and reviewed;
- skill cannot declare authority; declared capabilities are requirements evaluated by policy;
- deploy requires source/destination review, overwrite preview and approval;
- rollback/revocation prevents new activation and identifies affected runs.

### 8.3 Supply-chain checks

- reject reparse links, absolute/out-of-package references and unexpected executable types;
- scan secrets and dangerous command patterns as signals, not proof of safety;
- record source URL/commit/signature when installed from external source;
- maintain allowlisted publisher/source policy;
- run static and sandboxed behavioral review before approval for executable helpers;
- expose drift and provenance to approver.

## 9. Memory security contract

**PROPOSED ADR candidate: `ADR-SEC-MEM-001 Provenance-bound Memory`.**

### 9.1 Memory schema

```json
{
  "memory_id": "mem_...",
  "kind": "user_preference|project_fact|decision|temporary_observation",
  "text": "...",
  "scope": {"user": "local-user", "project": "harness", "agent": null},
  "source_refs": ["run:.../artifact:sha256:..."],
  "producer": {"type": "user|agent|tool", "id": "..."},
  "trust": "user_asserted|verified|untrusted",
  "content_hash": "sha256:...",
  "review": {"actor": "...", "decision": "accept", "rationale": "...", "at": "..."},
  "created_at": "...",
  "expires_at": "...",
  "supersedes": null,
  "revoked_at": null
}
```

### 9.2 Rules

- model-generated candidates default to `untrusted`;
- reviewer sees exact text, provenance, source excerpt and downstream scope;
- do not accept imperative content such as “always run”, “ignore policy” or credentials as memory;
- accepted memory never changes authorization or approval requirements;
- retrieval preserves labels and uses a separate data section in prompts;
- project/user scopes cannot leak across tenants/projects;
- expiry is mandatory for observations and provider/tool state;
- edit creates a new version; revocation is auditable;
- bulk accept and auto-accept are disabled for model/tool-generated candidates;
- anomaly detection/rate limits flag repeated or near-duplicate poisoning attempts.

## 10. MCP security contract

No MCP implementation exists in the reviewed baseline. This section defines admission criteria, not current behavior.

**PROPOSED ADR candidate: `ADR-SEC-MCP-001 MCP as Untrusted Tool Boundary`.**

### 10.1 Registry and server identity

Each server must have:

- stable server ID, owner and transport;
- exact executable/hash for local `stdio`, or exact HTTPS origin for remote;
- approved tool/resource/prompt schemas and schema hashes;
- required filesystem/network/secret/data scopes;
- version and revalidation date;
- trust state and incident contact;
- launch isolation profile for local server;
- authentication/authorization profile for remote server.

Unregistered dynamic server discovery is disabled in local-v1.

### 10.2 Local `stdio` servers

- treat server process as arbitrary code running with client privilege;
- launch under the R04 Windows supervisor and a narrower capability than the calling agent;
- minimal environment; no host secret store/profile;
- explicit filesystem and egress policy;
- only client-created private pipe/stdio; no unauthenticated localhost listener;
- bound message size, call count, time, output and process tree;
- schema or executable hash drift disables the server pending review.

### 10.3 Remote HTTP/OAuth servers

MCP specification requirements adopted as hard controls:

- inbound access token must be intended for the MCP server; validate issuer, audience, expiry and scopes;
- never pass the client token through to an upstream API;
- obtain a separate upstream token scoped to that API;
- per-user, per-client consent for proxy servers; display exact third-party scopes and redirect URI;
- exact redirect URI matching, CSRF `state`, secure single-use/short-lived state;
- sessions are routing state, never authentication;
- HTTPS except explicitly approved loopback development;
- protect OAuth metadata discovery against SSRF: destination allowlist, DNS/IP validation, redirect revalidation, block internal/metadata ranges;
- bind session IDs to authenticated user and use cryptographically random IDs;
- revoke tokens/consent when server identity or scope changes.

### 10.4 Tool descriptions and results

- tool description is untrusted metadata, not policy;
- schema is normalized and hashed before admission;
- unknown/dynamic tools are denied;
- destructive/write/external-publish actions always receive tool-specific policy;
- result is typed, size-bounded, provenance-labeled and sanitized for display;
- text inside a tool result cannot directly trigger a second tool call;
- chained calls consume separate capability receipts and budgets.

## 11. Scope-bound approval

**PROPOSED ADR candidate: `ADR-SEC-APR-001 Action-bound Approval Receipt`.**

### 11.1 Approval preview

The approver must see:

- human-readable action and irreversible effects;
- exact tool/server identity and version/hash;
- normalized targets: files, repository, account, recipients, URLs;
- write/delete/publish/execute/network classification;
- data classes leaving the host and destination;
- secret references used, never secret values;
- untrusted source(s) that influenced the proposal;
- diff/preview where applicable;
- capability expiry and whether action is retryable/idempotent;
- why approval is required and which policies remain non-overridable.

### 11.2 Receipt binding

Approval is bound to the canonical request hash, actor, approver, run/attempt, tool schema hash, skill bundle hash, policy version, provider identity, expiry and maximum uses.

Any change in arguments, target, destination, secret, data class, skill/server/provider hash or policy invalidates it.

Approval cannot be:

- inferred from natural-language user text;
- supplied by agent/model/tool;
- inherited by a child;
- reused across runs;
- applied to an unknown future action;
- used to disable Windows containment, redaction or audit.

### 11.3 Fatigue controls

- default-deny repeated identical denied requests;
- group only identical low-risk actions with explicit item count and target list;
- never batch destructive, publish, secret or new-destination approvals;
- rate-limit prompts per run/tool;
- show novelty warnings for first-use server/tool/destination;
- provide reject-and-block-for-run;
- expire pending approvals and cancel downstream work;
- monitor approval rate, reversal rate and repeated model pressure.

## 12. Secret propagation and egress

Controls inherited from R04/R05 and extended here:

1. Tool request carries only `secret_ref`; resolver injects the minimum secret after policy approval.
2. Secret is scoped to server/action/destination/run and expires promptly.
3. Parent cannot give raw secret to child; child receives a new narrower reference if permitted.
4. Secret values never enter model prompt, task packet, command args, artifact, event, error or audit.
5. Provider/MCP/tool stdout and structured result pass through streaming redaction before UI/persistence.
6. Egress policy binds destination plus data class, not only a generic `network` tier.
7. Redirects, DNS rebinding and alternate IPs are re-evaluated at connection time.
8. Exfiltration can occur through filenames, URLs, DNS, error messages and tool arguments; byte/field-level limits and content inspection are required.
9. If destination enforcement is unavailable, restricted data cannot be sent and privileged network tools are NO-GO.

## 13. Test catalogue and normative mapping

Existing D08 `SEC-001` and `SEC-002` are too broad to prove the agentic controls. Keep them as release rollups and add the following stable IDs.

| Test ID | Scenario | Expected result | Target docs |
|---|---|---|---|
| SEC-AG-001 | child requests path/tool absent from parent | spawn denied; empty parent means none | D04, D06, D08 |
| SEC-AG-002 | workflow spawn omits capability scope | no privileged execution; explicit capability required | D04, D08 |
| SEC-AG-003 | injected parent output tells child to widen scope | request denied; evidence retained as untrusted | D06, D08 |
| SEC-AG-004 | child returns fake approval/policy decision | ignored; no capability issued | D06, D08 |
| SEC-AG-005 | child artifact path/hash/type forged | quarantine; parent state not promoted | D04, D06, D08 |
| SEC-AG-006 | aggregate depth/call/time budget exceeded | further delegation denied/cancelled | D04, D08 |
| SEC-TOOL-001 | unknown tool/unknown schema field | deny before execution | D04, D08 |
| SEC-TOOL-002 | args mutate after policy decision | request hash mismatch; deny | D06, D08 |
| SEC-TOOL-003 | tool result contains second-tool instruction | rendered as untrusted data; no automatic call | D06, D08 |
| SEC-TOOL-004 | exact path/URL canonicalization variants | same policy target or fail closed | D04, D06, D08 |
| SEC-TOOL-005 | retry of non-idempotent action | no duplicate side effect | D04, D08 |
| SEC-APR-001 | approval replay in another run/child | rejected | D06, D08 |
| SEC-APR-002 | target/args/destination changes after approval | receipt invalid | D06, D08 |
| SEC-APR-003 | skill/tool/policy hash changes after approval | receipt invalid | D06, D08 |
| SEC-APR-004 | model text claims user approved | ignored; pending approval remains | D06, D08 |
| SEC-APR-005 | approval expired or already consumed | rejected idempotently | D06, D08 |
| SEC-APR-006 | override attempts to disable hard containment | rejected as non-overridable | D06, D08 |
| SEC-SUP-001 | duplicate skill name in two sources | ambiguous activation rejected | D06, D08 |
| SEC-SUP-002 | skill changes after run/approval pin | hash mismatch; execution stops | D06, D08 |
| SEC-SUP-003 | skill package contains link/out-of-root executable | quarantine | D06, D08 |
| SEC-SUP-004 | unreviewed skill selected for privileged agent | activation denied | D06, D08 |
| SEC-MEM-001 | model candidate contains imperative injection | cannot become executable authority; flagged | D06, D08 |
| SEC-MEM-002 | accept without reviewer/provenance/scope | validation fails | D06, D08 |
| SEC-MEM-003 | expired/revoked memory retrieved | excluded; audit records decision | D06, D08 |
| SEC-MEM-004 | project-scoped memory requested cross-project | denied | D06, D08 |
| SEC-MCP-001 | token wrong audience | request rejected before tool handling | D04, D06, D08 |
| SEC-MCP-002 | client token passed to upstream | conformance failure; no request | D04, D06, D08 |
| SEC-MCP-003 | malicious OAuth metadata targets loopback/internal/metadata IP | discovery blocked | D04, D06, D08 |
| SEC-MCP-004 | consent reused for another client/scope | fresh consent required | D06, D08 |
| SEC-MCP-005 | session ID without valid actor token | rejected | D04, D06, D08 |
| SEC-MCP-006 | server executable/tool schema hash drifts | server disabled pending review | D04, D06, D08 |
| SEC-MCP-007 | local MCP tries filesystem/egress outside scope | OS/tool policy denies; evidence recorded | D04, D06, D08 |
| SEC-MCP-008 | oversized/malicious tool result | truncated/quarantined; no instruction execution | D04, D06, D08 |
| SEC-SEC-001 | raw secret travels parent → child → log/artifact | canary absent everywhere; run fails closed | D06, D08 |
| SEC-EGR-001 | internal data sent to new domain/redirect | denied; no bytes leave approved boundary | D04, D06, D08 |

Additional required properties:

- fuzz typed request canonicalization and parser;
- property-test capability intersection: result is never broader than any parent set;
- generate adversarial prompt/tool-result/skill/memory corpus;
- inject cancellation/crash between decision, approval, token issuance and side effect;
- test concurrent/replayed requests;
- assert audit contains IDs/hashes/reasons but no secret or unrestricted content;
- combine every privileged tool test with the R04 descendant cleanup, environment and filesystem escape tests.

## 14. ADR recommendations

| ADR | Decision | Priority | Depends on |
|---|---|---:|---|
| ADR-SEC-AG-001 | deterministic complete mediation and typed action requests | P0 | D04 gateway/executor contract |
| ADR-SEC-AG-002 | child capability intersection; empty means none; max depth 1 | P0 | runtime child schema |
| ADR-SEC-APR-001 | action-bound, single-use approval receipt | P0 | actor identity and audit |
| ADR-SEC-SUP-001 | skill identity pinned by source/name/hash and trust state | P0 before privileged skills | skill registry |
| ADR-SEC-MEM-001 | provenance-bound scoped memory; no imperative authority | P0 before memory retrieval into agents | memory schema |
| ADR-SEC-MCP-001 | MCP is an untrusted tool boundary; registry-only v1 | P0 before any MCP enablement | R04 supervisor, auth design |
| ADR-SEC-EGR-001 | destination + data-class egress policy | P0 for network tools | R04 Windows egress prototype |
| ADR-SEC-AUD-001 | separate audit records for proposal, decision, approval and execution | P0 | D03 event durability decisions |

Recommended initial v1 limitation:

- builtin typed read tools only;
- no arbitrary shell/fetch tool;
- no dynamic MCP;
- no remote MCP until authenticated actor model exists;
- local MCP disabled until R04 supervisor and per-server isolation pass;
- child depth 1 and no child tool execution by default;
- skills may guide analysis, but privileged activation requires pinned approved hash;
- memory can be viewed/curated but cannot change authorization.

## 15. Implementation sequence

### Phase S0 — Close semantic bypasses

1. Change empty parent capability semantics to none.
2. Require workflow to provide explicit child path/tool/skill scope.
3. Prevent privileged child run until executor actually consumes the scope.
4. Mark child/artifact/output as untrusted with source hashes.
5. Disable provider-discovered tools/plugins/MCP/config where adapter can do so.

Gate: `SEC-AG-001..005`.

### Phase S1 — Typed tool kernel

1. Add typed request/result/decision schemas.
2. Implement canonicalization and capability intersection.
3. Add policy enforcement immediately before side effect.
4. Create action-bound approval receipts and audit records.
5. Implement one granular builtin read tool as conformance reference.

Gate: `SEC-TOOL-*`, `SEC-APR-*`.

### Phase S2 — Skill and memory trust

1. Pin skill source/name/hash in agent/run.
2. Add trust/review/revocation workflow.
3. Add provenance-bound memory schema and retrieval labels.
4. Build poisoning tests.

Gate: `SEC-SUP-*`, `SEC-MEM-*`.

### Phase S3 — MCP admission, if still required

1. Decide local stdio versus remote HTTP use cases separately.
2. Implement registry and schema pinning.
3. Apply R04 supervisor to local server.
4. Implement OAuth audience/resource/consent and SSRF controls for remote server.
5. Normalize MCP calls into the same typed tool kernel.

Gate: `SEC-MCP-*`, `SEC-EGR-001`, all applicable R04 Gate D tests.

## 16. NO-GO conditions

Reject privileged agent/tool/MCP execution when:

1. action is derived only from model prose rather than a valid typed request;
2. parent/user/profile/policy capability cannot be calculated explicitly;
3. parent scope is empty/unknown;
4. tool/server/schema/executable or skill hash is unknown, unapproved or changed;
5. request target, destination or data class cannot be canonicalized;
6. required approval is missing, expired, reused or bound to different content;
7. model/tool/child supplies the approval or policy decision;
8. secret must be placed in prompt, command argument, artifact or broad environment;
9. egress destination cannot be constrained for the data class;
10. provider hides tool actions that policy must mediate;
11. local MCP/CLI cannot meet R04 process, identity, environment and filesystem controls;
12. remote MCP token audience, per-client consent or SSRF protection is absent;
13. skill or memory provenance is missing for privileged use;
14. audit/redaction is unavailable;
15. untrusted tool/child result would be automatically executed or persisted as trusted memory.

## 17. UNKNOWN gaps

| Unknown | Why it matters | Resolution |
|---|---|---|
| Authenticated user/approver identity model | approval and MCP consent cannot be safely bound to a header-only local client | architecture decision + API auth threat model |
| Exact future tool catalogue | least privilege needs action/resource schemas | inventory intended use cases before tool kernel design |
| MCP transport/use cases | local and remote threats differ materially | separate ADR per transport |
| Provider config/plugin/MCP discovery behavior under current wrappers | hidden tools may bypass Hub mediation | version-pinned empirical fixtures from R05 |
| Whether child `skills` are expected to affect workflow execution | currently stored but not activated in `_run_child` | product/runtime decision |
| How accepted memory is retrieved into prompts | ingestion exists; reviewed path did not establish a canonical retrieval path | trace usage and add integration test before enablement |
| Actor separation on a single-user local Hub | OS user may be adequate for some local-v1 actions but not delegated OAuth consent | define local actor and session guarantees |
| Redaction coverage for structured/binary/streaming outputs | secret can leak before post-processing | canary-based end-to-end tests |
| Artifact trust/signature model | parent currently accepts child metadata | define immutable manifest and promotion protocol |
| Egress enforcement on Windows | required for restricted data | complete R04 WFP/AppContainer prototype |
| Approval UX resistance to fatigue | security depends on understandable preview | usability/adversarial study with measured approval quality |

## 18. Mapping summary

### D04 — Gateway, Executor and Providers

Add:

- typed `ToolRequest`, `ToolResult`, `PolicyDecision`, capability receipt;
- provider/tool/MCP manifest with schema hashes;
- child capability intersection and delegation lifecycle;
- MCP registry/transport boundary;
- secret resolver and egress binding;
- fail-closed behavior when provider tool events are opaque.

### D06 — Security and Governance

Add:

- untrusted-content invariant;
- policy precedence and non-overridable controls;
- action-bound approval;
- skill/memory trust lifecycle;
- MCP OAuth/confused-deputy/token-passthrough/SSRF rules;
- proposal/decision/approval/execution audit chain;
- explicit NO-GO conditions.

### D08 — Test and Implementation Plan

Replace broad confidence from `SEC-002` alone with the stable IDs in §13 and enforce phase gates in §15.

## 19. Primary-source bibliography

1. [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm012025-prompt-injection/)
2. [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
3. [OWASP LLM07:2025 System Prompt Leakage](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/)
4. [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/download/52117/)
5. [OWASP ASI06 discussion: Memory Is a Feature. It Is Also an Attack Surface](https://genai.owasp.org/2026/05/13/memory-is-a-feature-it-is-also-an-attack-surface/)
6. [NIST AI 600-1: Generative Artificial Intelligence Profile](https://doi.org/10.6028/NIST.AI.600-1)
7. [MCP Authorization specification 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
8. [MCP Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)

Key source-grounded conclusions:

- **VERIFIED-DOC:** OWASP LLM06 recommends minimizing extension functionality, permissions and autonomy; it requires downstream authorization/complete mediation rather than model judgment.
- **VERIFIED-DOC:** OWASP LLM07 states that system prompts are not secrets or reliable authorization controls; privilege checks must be deterministic and external to the LLM.
- **VERIFIED-DOC:** NIST recommends provenance, inventories, human oversight roles, adversarial testing, third-party risk controls and incident response across the GAI value chain.
- **VERIFIED-DOC:** MCP forbids token passthrough, requires access-token audience validation and identifies per-client consent, SSRF, session hijacking and local-server privilege as explicit risks.

## 20. Final recommendation

Approve R06 as the security research baseline with a **NO-GO** on privileged tools/MCP today. Implement the narrow typed tool kernel before integrating any general-purpose tool or MCP server. Treat child-run, skills and memory as separate supply/trust boundaries, not prompt features.

The shortest safe path is:

```text
explicit child scope
→ typed builtin read tool
→ deterministic policy
→ action-bound approval
→ pinned skills + provenance memory
→ local MCP under R04 isolation
→ remote MCP only after actor/OAuth/SSRF controls
```

This sequence keeps local-v1 small while removing the main confused-deputy and capability-escalation paths before they become compatibility commitments.
