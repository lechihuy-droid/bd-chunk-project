# R07 — Research Synthesis and ADR Recommendations

```yaml
document_id: HH-RES-R07
version: 0.1
status: Proposed synthesis — owner approval required
last_updated: 2026-07-27
sources: [HH-RES-R03, HH-RES-R04, HH-RES-R05, HH-RES-R06]
scope: Harness Hub local-v1
```

## 1. Executive verdict

Research xác nhận kiến trúc local-first vẫn khả thi, nhưng implementation hiện tại chưa đạt Gate C hoặc Gate D theo nghĩa đã định trong bộ thiết kế.

| Gate/capability | Verdict | Lý do chính |
|---|---|---|
| Local file-backed control plane | **Conditional GO** | Chỉ single-process; cần transaction journal, state version, idempotency và crash probes |
| API/NVIDIA read-only chat | **Conditional GO** | Hoạt động cơ bản; chưa có Executor lifecycle/cancel/deadline đầy đủ |
| Claude CLI read-only | **Low-assurance conditional** | Chưa có OS containment, minimal env hoặc process-tree guarantee |
| Codex adapter | **NO-GO** | Configured executable không tồn tại; parser/capability lifecycle drift |
| Gemini adapter | **NO-GO** | Chưa cài; adapter không đáp ứng stream/session/usage contract |
| CLI workspace-write Gate D | **NO-GO** | Chưa có controlled Windows executor subsystem |
| Privileged tool/child write-network | **NO-GO** | Scope hiện là metadata, không complete-mediate action |
| MCP | **NO-GO / future** | Chưa có implementation, registry, auth hoặc mediated tool kernel |

Research làm tăng độ chắc của tài liệu, không làm tăng readiness của code. Readiness nên tách:

- documentation/research baseline: **khoảng 85%** cho local-v1;
- implementation readiness: **khoảng 45–50%** cho Gate C;
- Gate D security readiness: **dưới 25%**.

## 2. Consensus findings

### F01 — File replace không phải durability protocol

`Path.replace` tránh ghi đè trực tiếp nhưng không chứng minh power-loss durability trên Windows/NTFS. State, event, checkpoint và artifact hiện có nhiều primitive/ordering khác nhau.

**Decision direction:** projection + immutable transaction journal là authority; event là derived timeline. Không quảng cáo event sourcing.

### F02 — External side effect luôn có vùng ambiguous

Crash sau provider/process side effect nhưng trước local commit không thể được giải bằng retry mù. Execution cần stable ID, idempotency/reconciliation capability hoặc explicit human retry.

### F03 — Windows process wrapper không phải sandbox

`Popen.kill()` không chứng minh process-tree containment; same-user process có authority rộng; full environment inheritance làm lộ credential scope; watcher không enforce disk/file quota.

### F04 — Controlled Windows executor là subsystem riêng

Job Object, restricted identity/AppContainer, workspace ACL/reparse controls, quota storage và egress provisioning không phải một thay đổi nhỏ trong adapter. Đây là milestone Gate D riêng với installer/privilege/operations ADR.

### F05 — Capability phải phản ánh behavior đã test

Provider status hiện quá hẹp và đôi khi rộng hơn implementation. Capability chỉ được đánh `supported` cho exact tested version/fixture; living provider docs không phải compatibility guarantee.

### F06 — Empty capability không được hiểu là unrestricted

Current child-scope subset helper bỏ kiểm tra khi parent list rỗng. Target semantics phải là missing/empty = none. Wildcard là representation riêng và policy-protected.

### F07 — Model output không có authority

Prompt, skill, memory, child output, tool/MCP result và provider event đều là untrusted data. Chỉ deterministic Policy Enforcement Point có thể cấp capability cho một canonical action.

### F08 — Approval phải bind tới action

Node/job approval hiện quá rộng cho future provider/tool behavior. Approval receipt cần bind action type, canonical args, target, data class, secret/egress scope, policy version, capability hash, skill/tool schema hash và expiry.

## 3. Resolved contradiction

### Recovery authority

`D03` hiện mô tả replay checkpoint + event để dựng state, trong khi R03 chứng minh event hiện không reducer-complete và không atomic với state. Đề xuất thống nhất:

```text
immutable transaction journal + committed run projection
  = recovery authority

runtime events
  = derived UI/diagnostic timeline
  = regenerate được từ committed transaction
```

Nếu tương lai chuyển event sourcing, phải có ADR mới với canonical reducer payload, payload hash, previous hash, retention, migration và deterministic replay tests.

### Windows egress

Hub non-elevated không tự cài WFP policy. Egress enforcement chỉ hợp lệ nếu:

1. admin pre-provision policy; hoặc
2. authenticated least-privilege privileged broker; hoặc
3. isolated worker/network boundary ở Gate E.

Nếu không có một trong ba, Gate D chỉ cho non-sensitive low-assurance profile và không claim network isolation.

## 4. Proposed ADR set

Các ADR dưới đây là **Proposed**, chưa approved.

| ADR | Decision đề xuất | Gate |
|---|---|---|
| ADR-DR-01 | Projection + immutable transaction journal là local-v1 recovery authority | C |
| ADR-DR-02 | Events là derived timeline; không claim event sourcing | C |
| ADR-DR-03 | Single server process bắt buộc cho mutable file store | C |
| ADR-DR-04 | External side-effect retry cần stable execution ID + reconciliation/idempotency hoặc HITL | C |
| ADR-DR-05 | Provider capability chỉ support exact tested version/fixture | C |
| ADR-DR-06 | Controlled Windows executor là milestone/subsystem riêng | D |
| ADR-DR-07 | Hard egress cần pre-provisioned policy, broker hoặc isolated worker | D/E |
| ADR-DR-08 | Missing/empty capability = none; wildcard explicit | C |
| ADR-DR-09 | Tool action cần typed request + deterministic policy + capability receipt | D |
| ADR-DR-10 | Approval bind canonical action và invalidated khi policy/schema/hash đổi | D |
| ADR-DR-11 | Skill activation pin `{source,name,content_hash}`; memory có provenance/scope/expiry | D |
| ADR-DR-12 | MCP ngoài scope cho đến typed tool kernel và admission/auth design | D/E |

## 5. Normative patch map

| Finding | Document | Required change |
|---|---|---|
| F01/F02 | D03 | Thay event-replay authority bằng transaction journal; thêm ambiguous execution recovery |
| F01 | D05 | Primitive durable write, per-run checkpoint, torn-tail/quarantine, manifest-last qualified |
| F01 | D07 | Hạ RPO claim đến khi crash/power probes pass |
| F03/F04 | D04 | Windows process supervisor, capability profiles, controlled-executor milestone |
| F03/F04 | D06 | Same-user low-assurance; WFP privilege boundary; bounded redaction/quota claims |
| F05 | D04 | Versioned capability manifests, exact conformance status |
| F05 | D08 | Provider-specific fixtures và freshness gate |
| F06/F07 | D04 | Typed ToolRequest/Result/PolicyDecision/CapabilityReceipt |
| F06–F08 | D06 | Complete mediation, action-bound approval, untrusted-content invariant |
| F06–F08 | D08 | Stable security test IDs và phase gates |
| Skill/memory/MCP | D06/D08 | Pinning, provenance, MCP NO-GO/admission tests |

## 6. Implementation sequence

### Phase R0 — Close semantic bypasses

1. Empty child paths/tools/skills = none.
2. No provider/tool execution may infer permission from missing metadata.
3. Fix executable resolution truth; status must report configured/resolved/version separately.

### Phase R1 — Durable local transaction core

1. State version và per-run lock.
2. Immutable/checksummed transaction phase records.
3. Idempotency ledger chỉ lưu response reference/hash/classification.
4. Per-run recovery checkpoint.
5. Derived event regeneration.
6. Crash/torn-tail/orphan probes.

### Phase R2 — Executor Port and provider truth

1. Typed execution lifecycle.
2. Mock adapter conformance.
3. NVIDIA/Claude conditional adapters.
4. Codex path/parser repair then exact-version fixtures.
5. Gemini chỉ sau install/version pin và adapter rewrite.

### Phase R3 — Artifact/API integration

1. Manifest-last publication với qualified durability envelope.
2. Stale/idempotent API commands.
3. SSE cursor từ derived event timeline.

### Phase R4 — Typed tool kernel

1. Canonical ToolRequest.
2. Deterministic policy decision.
3. Action-bound approval.
4. Capability receipt.
5. Một builtin read-only tool trước; không general CLI/MCP.

### Phase R5 — Controlled Windows executor

Chỉ bắt đầu sau approved ADR-DR-06/07 và prototype Job Object/identity/workspace/quota/egress. Đây không phải điều kiện để release local read-only Hub.

## 7. Required research/prototype gates

| Gate | Required proof |
|---|---|
| Gate C durability | R03 probes P01–P10 và crash points C01–C23; accepted power-loss envelope documented |
| Provider adapters | Exact installed version + golden fixture + cancel/error/session tests |
| Gate D process | Job-associated tree tests plus WMI/COM/service/task escape tests |
| Gate D workspace | Separate identity/token + ACL/reparse tests + enforceable storage boundary |
| Gate D egress | Pre-provision/broker/isolated worker proof; no same-process admin mutation |
| Tool/MCP | R06 `SEC-AG/TOOL/SUP/MEM/MCP` suites green |

## 8. Owner decisions

| ID | Decision | Recommended owner |
|---|---|---|
| RD-01 | Approve projection+journal recovery authority | Runtime |
| RD-02 | Accepted local-v1 durability/RPO envelope | Runtime + Product |
| RD-03 | Supported provider set for Gate C | Product + Runtime |
| RD-04 | Có đầu tư controlled Windows executor hay giữ low-assurance read-only | Product + Security |
| RD-05 | Egress enforcement option | Security + Platform |
| RD-06 | Có MCP trong roadmap gần không | Product + Security |
| RD-07 | Skill/memory trust lifecycle và retention | Product + Security |

Coding agent không tự chốt các mục này.

## 9. Research quality assessment

| Report | Review state | Confidence |
|---|---|---|
| R03 | Cross-reviewed, revised v0.2 | High cho code audit/protocol; power-loss guarantee UNKNOWN |
| R04 | Cross-reviewed, revised v0.2 | High cho current gaps; AppContainer/egress compatibility cần spike |
| R05 | Evidence-reviewed, revised v0.2 | High cho local probe/code; provider living docs cần scheduled revalidation |
| R06 | Root-reviewed against code and primary bibliography | High cho current semantic gaps; future MCP shape UNKNOWN |

## 10. Final recommendation

Approve R03–R07 làm research baseline, không phải implementation approval. Merge các invariant và NO-GO condition vào D03–D08 trước khi mở coding phases.

Shortest safe path:

```text
close empty-scope bypass
→ projection+journal runtime
→ mock Executor Port
→ exact provider capability truth
→ immutable artifact/API concurrency
→ typed read-only tool kernel
→ controlled Windows executor only if product still needs it
→ MCP last
```
