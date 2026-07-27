# Security and Governance

> Superseded by `../../design/D06_SECURITY_AND_GOVERNANCE.md`.

| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-SEC-001 |
| Version | 0.2 |
| Status | Draft — merged from research |
| Depends on | Architecture Principles, Runtime Gateway, Executor Contract |
| Research sources | HH-RES-R01, HH-RES-R02 |
| Last updated | 2026-07-27 |

## 1. Mục tiêu

Bảo vệ boundary giữa user/runtime, Gateway, provider API và untrusted CLI process; fail closed với model, tool, filesystem, network, credential và budget decisions.

## 2. Trust boundaries

```text
Trusted application/runtime
→ policy and gateway boundary
→ restricted executor boundary
→ external provider / untrusted CLI / tool
```

Model output, tool output, CLI stdout/file và user-supplied workspace đều là untrusted input.

## 3. Policy precedence

```text
Hard platform policy
→ workspace/data policy
→ workflow/run/node restrictions
→ permitted explicit user/agent preference
→ routing cost/latency preference
```

Lower level chỉ được siết chặt hơn. Conflict, missing policy hoặc unknown capability fail closed. Run phải pin policy version.

## 4. Data classification

`PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`.

- Registry mô tả provider/residency/retention capability.
- Gateway loại provider không phù hợp classification.
- `RESTRICTED` mặc định không gửi public provider nếu chưa có explicit approved policy.

## 5. Secrets

- Business state/request chỉ giữ credential reference.
- Resolve ngay trước execution.
- Không truyền secret qua argv, prompt, artifact, URL hoặc log.
- Child process nhận minimal environment.
- Authorization headers, env values và provider raw payload phải redact.
- Secret resolution và denial được audit.

## 6. Gateway threats và controls

| Threat | Control |
|---|---|
| Unauthorized model/provider | registry allow-list + policy check |
| Budget/token abuse | bounded limits, quota decision, usage evidence |
| Prompt/metadata injection | typed schema; metadata không tạo command |
| Silent fallback/data egress | approved fallback plan + classification check |
| Sensitive logging | prompt/output off by default + redaction |
| Client disconnect resource leak | cancellation propagation |
| Malformed provider output | strict parser/output validation |

Gateway không tự thực thi tool từ model output.

## 7. CLI threats và controls

| Threat | Control |
|---|---|
| Command injection | argument array, `shell=False`, executable allow-list |
| Path traversal/symlink escape | resolved workspace boundary, read/write allow-list |
| Home/other project access | deny mount/access by default |
| Network exfiltration | network deny-by-default, destination allow-list |
| Fork bomb/resource exhaustion | process/CPU/RAM/output/time caps |
| Orphan process | process-group supervision and reconciliation |
| Secret leakage | minimal env, no argv secret, stdout/artifact scan |
| Malicious generated files | quarantine/scan before artifact publication |

## 8. Isolation levels

- Local trusted chat MAY dùng host process với documented personal-mode risk.
- Workflow execution với untrusted files/code cần restricted process hoặc container.
- Multi-user/production CLI executor MUST có approved threat model và sandbox acceptance.
- MicroVM/gVisor là future option, không mặc định MVP.

## 9. Human approval

Bắt buộc khi:

- mở rộng filesystem/network/tool permission;
- gửi restricted data tới provider mới;
- vượt hard budget;
- deploy/xóa/ghi đè dữ liệu quan trọng;
- reviewer trả blocking conflict;
- routing/fallback cần action ngoài approved plan.

Decision lưu actor, time, reason, scope, before/after version, correlation và audit event.

## 10. Runtime event, operational log và audit

- Runtime event điều khiển/replay workflow.
- Execution event mô tả backend attempt.
- Operational log phục vụ debug.
- Audit event ghi security/policy/human actions và append-only.

Không dùng operational log làm audit source duy nhất.

## 11. Required security tests

- policy precedence và fail-closed;
- provider/data-classification denial;
- raw secret scan trên log/event/artifact;
- command injection và malicious filenames;
- traversal + symlink escape;
- unauthorized model/tool;
- process-tree cleanup;
- network/filesystem policy;
- duplicate/stale approval;
- routing fallback không bypass policy.

## 12. Acceptance

- Không module bypass Gateway/Policy/Executor boundary.
- Không secret trong prompt, argv, event, log hoặc artifact.
- CLI không thoát workspace/network policy.
- Human/security decision truy vết được.
- Security denial không tự retry hoặc fallback.
