# D06 — Security and Governance

```yaml
document_id: HH-DES-D06
version: 1.1
status: In Review
owner: Security
depends_on: [D01, D02]
research_sources: [HH-RES-R04, HH-RES-R06, HH-RES-R07]
```

## 1. Security objectives

Ngăn execution vượt workspace/quyền, secret leakage, provider data egress ngoài policy, prompt/tool injection thành hành động, path traversal và CLI process tồn tại ngoài lifecycle. Fail closed khi thiếu context/policy.

## 2. Trust boundaries

```text
Browser input
  | TB1 HTTP/CSRF
FastAPI + Runtime
  | TB2 untrusted model/provider output
Gateway/Adapter
  | TB3 subprocess + workspace + network
CLI process
  | TB4 filesystem artifacts
Runtime store
```

External logs/session files, workflow YAML, uploaded files, provider response và CLI stdout đều untrusted.

## 3. Policy precedence

```text
Hard platform security
  > workspace/operator policy
  > workflow policy
  > agent profile
  > user route hint
  > model/tool suggestion
```

Hard policy không override được bởi Orchestrator, agent confidence hay fallback. Decision có `policy_evaluation_id`, matched rules, effect và safe reason.

## 4. Data classification

`public | internal | confidential | restricted`

| Class | Provider egress | Log/content |
|---|---|---|
| public | approved provider | metadata + allowed content |
| internal | approved provider by default policy | content off by default |
| confidential | explicit provider/data policy | reference/redacted |
| restricted | local-only/default deny | metadata only |

Unknown classification = restricted.

## 5. Secrets

- Secret chỉ từ environment/secret broker abstraction.
- Contract dùng `secret_ref`, không value.
- Minimal env allowlist truyền vào subprocess.
- Redact key/token patterns trong logs/events/errors.
- Không đưa `.env`, credential directories hoặc raw provider body vào artifacts.
- Rotation/revocation không yêu cầu sửa workflow/agent definition.

## 6. HTTP/local deployment controls

- Bind `127.0.0.1` mặc định.
- Validate Host/Origin cho state-changing browser request; CSRF control theo current app.
- CORS deny mặc định.
- Request body/stream size limit.
- Không serve runtime root qua generic static file route.
- Nếu bind non-loopback: NO-GO trước authentication, TLS và access-control ADR.

## 7. Prompt/tool injection controls

- Prompt, model output, retrieved file/web content, child output, skill text, memory và tool/MCP result đều là untrusted data; không đối tượng nào tự mang authority.
- Model output là data, không command.
- Tool/child-run request phải qua typed canonical request, deterministic policy và capability receipt.
- Tool allowlist và path scope lấy từ profile/policy, không từ prompt.
- Missing/empty paths/tools/skills/permission = none; wildcard phải explicit và policy-protected.
- Provider-returned URL/command không tự execute.
- Artifact rendering escape-first; link scheme allowlist.
- Human approval bắt buộc cho quyền write/destructive/external publish theo risk tier.

## 8. CLI threat model

| Threat | Control |
|---|---|
| Command injection | argv array, executable/arg allowlist, no shell interpolation |
| Path traversal/symlink | canonical root, no-follow boundary check |
| Secret theft | minimal env, no secret mounts, redaction |
| Data exfiltration | pre-provisioned/brokered/isolated-worker egress; nếu không có thì deny sensitive data/profile |
| Resource exhaustion | time/CPU/output/file quotas |
| Orphan process | process group/job object, terminate→kill tree |
| Binary/malware output | type/size policy + scan/quarantine |
| Sandbox escape | local v1 does not claim strong sandbox; restricted data denied |
| Supply chain | pin CLI/version/hash where possible; record provenance |
| Interactive prompt | non-interactive flags; unexpected prompt fails |

Same-user read-only CLI là low-assurance application policy, không phải OS/filesystem containment. Job Object không bao phủ mọi brokered process path. Hard disk/file quota không được suy ra từ watcher.

Workspace-write CLI yêu cầu controlled Windows executor milestone và Gate D. WFP policy phải được admin pre-provision hoặc quản lý qua authenticated privileged broker; Hub vẫn non-elevated. Nếu không có enforceable egress/storage/identity boundary, restricted data và hostile workspace-write bị deny hoặc chuyển Gate E isolated worker.

## 9. Filesystem controls

- Allowed roots cấu hình tập trung.
- Reject empty/root/home/workspace-root destructive target.
- Resolve exact target trước action; preserve user changes.
- Upload/output filename server-generated hoặc sanitized.
- Binary executable output quarantined.
- Artifact scan status phải `passed` trước download/render nếu policy yêu cầu.

## 10. Governance và HITL

Approval task chứa:

- requested action và reason;
- run/node/execution;
- requested scope/tool/path/network;
- risk tier và policy evaluation;
- diff/artifact preview;
- expires_at;
- approve/reject principal và timestamp.

Approval receipt bind canonical action type/args/targets, data classification, secret/egress scope, policy version, capability/tool/skill/schema hashes và expiry. Thay đổi bất kỳ giá trị bind nào invalidates approval. Approval là scope-bound, one-time và không cấp quyền chung cho future attempts; hard deny và OS containment không override được.

## 10.1 Child, skill và memory trust

- Child capability là intersection với parent; child không được tự khai rộng scope. Delegation depth và aggregate budget phải bounded.
- Skill activation dùng `{source,name,content_hash}` đã review; same-name shadowing hoặc hash drift fail closed.
- Skill read-only chỉ nói package không mutate, không có nghĩa nội dung an toàn.
- Accepted memory cần source provenance, reviewer, rationale, scope, classification, immutable hash, expiry/revocation. Memory không chứa executable instruction hoặc authority.

## 10.2 MCP admission

MCP ngoài scope cho đến khi typed tool kernel tồn tại. Khi mở:

- registry pin server identity, transport, tool schema hash và trust state;
- local stdio server chịu cùng Windows isolation profile như CLI;
- remote OAuth validate audience, cấm token passthrough, per-client consent;
- discovery/redirect URL chống SSRF;
- tool description/schema change invalidates prior approval;
- opaque provider-internal MCP/tool route bị deny.

## 11. Audit vs operational event

Runtime event phục vụ UI/replay và có thể chứa operational payload đã redact. Audit record là append-only evidence cho policy denial, approval, permission/security setting, secret access reference, CLI launch/cancel và artifact quarantine.

Audit record có hash chain hoặc tamper-evident mechanism trước production claim. Local v1 tối thiểu ghi append-only file ngoài user-editable artifact tree.

## 12. Incident response

Khi nghi leakage/escape:

1. cancel run và kill tracked process;
2. disable adapter/route;
3. quarantine artifacts/log refs;
4. revoke affected secret;
5. preserve audit evidence;
6. xác định workspace/provider scope;
7. không resume cho đến security review.

## 13. Required tests

- traversal, symlink escape, unsafe filename;
- secret in request/stdout/error/artifact redaction;
- route fallback không bypass data policy;
- injection output không tạo tool/process;
- duplicate/stale approval;
- subprocess timeout/orphan kill;
- output/file/network limits;
- CORS/Host/CSRF/body size;
- restricted data denied cho unapproved provider/CLI.
- empty-scope child escalation, skill shadow/hash drift, memory poisoning;
- approval replay sau action/policy/schema/hash change;
- MCP token passthrough, confused deputy, SSRF, session/schema rug-pull trước khi MCP được bật.

## 14. Acceptance

- Security denial không retry/fallback.
- Mọi privileged action có policy evaluation và audit.
- Không raw secret trong persisted fixtures.
- CLI workspace-write chỉ bật sau Gate D.
- Non-loopback deployment bị chặn hoặc có approved security ADR.
