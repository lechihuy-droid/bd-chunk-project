# Detailed Design — CLI Executor

> Superseded by `../../design/D04_GATEWAY_EXECUTOR_AND_PROVIDERS.md` and D06.

| Thuộc tính | Giá trị |
|---|---|
| Document ID | HH-DD-CLIEXEC-001 |
| Version | 0.2 |
| Status | Draft — merged from research |
| Implementation readiness | Conditional — threat model and sandbox mode must be approved |
| Depends on | Unified Executor Contract v0.2, Security and Governance |
| Research source | HH-RES-R02 |
| Last updated | 2026-07-27 |

## 1. Mục tiêu

CLI Executor chạy approved CLI process trong workspace được cấp, normalize stdout/stderr/protocol thành Executor events, quản lý timeout/cancel/process tree và thu output evidence.

Chat CLI chạy trực tiếp trên host hiện tại là trusted-personal mode, không đồng nghĩa workflow CLI Executor đã đạt sandbox production.

## 2. Composition

```text
CliExecutor
  ├─ ProcessSupervisor
  ├─ CliProtocol / OutputParser
  ├─ SessionManager (optional)
  ├─ WorkspaceHandle
  ├─ CredentialInjector
  └─ ArtifactCollector
```

Provider và transport tách biệt: Claude/Codex protocol có thể dùng chung ProcessSupervisor nhưng parser/session rules riêng. Dùng pipe mặc định; PTY chỉ khi capability/use case yêu cầu và đã test.

## 3. Workspace layout

```text
runtime/runs/{run_id}/{node_id}/{attempt_no}/
  input/
  workspace/
  output/
  logs/stdout.log
  logs/stderr.log
  manifest/request.json
  manifest/result.json
  manifest/file-diff.json
```

Runtime chuẩn bị `WorkspaceRef`; adapter không clone/pull repository. Executor chỉ làm việc trong resolved workspace boundary.

## 4. Lifecycle

```text
ACCEPTED
→ PREPARING workspace/env/credential refs
→ STARTING process
→ RUNNING and emitting events
→ COMPLETING output/parser/scan
→ COMPLETED | FAILED | CANCELLED | TIMED_OUT
→ CLEANING_UP
→ CLOSED
```

Cancel có thể đến trong preparing/starting/running. Cleanup luôn chạy và cleanup error chỉ thêm warning/audit, không thay terminal business result.

## 5. Process supervisor

- launch bằng argument array, `shell=False`;
- resolve executable từ allow-list;
- stdin/stdout/stderr có encoding và output-size cap;
- theo dõi PID/process tree;
- deadline và idle timeout riêng;
- concurrency/resource cap;
- non-zero exit map thành `PROCESS` hoặc provider-specific error;
- phát terminal event đúng một lần;
- startup reconciliation phát hiện/kết thúc orphan process.

## 6. Cancellation

```text
cancel requested
→ graceful terminate process group
→ wait bounded grace period
→ force-kill entire tree
→ close pipes
→ collect safe partial evidence
→ cleanup
→ execution.cancelled
```

Cancel idempotent. Timeout dùng cùng cleanup path nhưng terminal status là `TIMED_OUT`.

## 7. Output parsing

- Parser version gắn với CLI/version range.
- ANSI/control characters được sanitize.
- Structured output chỉ tin khi CLI flag/protocol bảo đảm.
- Unknown/malformed output tạo `PARSE` error và lưu raw output bằng protected reference.
- Provider session/usage/tool events map sang catalogue chung nhưng không bịa capability không có.

## 8. Session

Stateless one-shot mặc định. Resume chỉ dùng nếu capability manifest khai báo và đã qua compatibility test.

- session ID opaque, scoped theo run/workspace/provider;
- có expiry;
- không chia sẻ process/session giữa workspace;
- mất session không làm mất runtime state;
- không xây session pool trong MVP.

## 9. Filesystem, network và secrets

- deny path traversal, symlink escape, parent/home/other workspace;
- read/write allow-list tách biệt;
- network deny-by-default cho workflow CLI executor;
- secret chỉ inject từ reference ngay trước launch;
- không truyền secret qua command line;
- child process nhận environment tối thiểu, không kế thừa toàn bộ host env;
- stdout/stderr/artifacts phải qua redaction/scan.

## 10. Isolation modes

| Mode | Dùng cho | Trạng thái |
|---|---|---|
| `trusted_host` | local personal chat/PoC, no untrusted code | Có risk waiver rõ ràng |
| `restricted_process` | MVP workflow nội bộ | OS user, workspace boundary, caps; chưa đủ multi-tenant |
| `container` | untrusted workflow execution | Target trước production |
| `microvm` | high-risk/multi-tenant | Future |

Không hạ yêu cầu sandbox production chỉ vì research cho phép host process MVP.

## 11. Artifact và evidence

Executor thu:

- exit code/signal;
- stdout/stderr references;
- file diff;
- output manifest/checksum;
- CLI/provider version;
- duration/resource usage;
- security scan result.

Chỉ allowed output được đề xuất thành artifact; Runtime/Artifact Service persist version.

## 12. Conformance và security tests

- fake process success/non-zero/malformed output;
- stream parser với ANSI/Unicode;
- timeout và explicit cancel;
- kill parent + child process tree;
- orphan reconciliation;
- traversal/symlink escape;
- command injection filename/argument;
- environment/secret redaction;
- output size/resource cap;
- CLI version compatibility;
- session resume/loss;
- cleanup failure.

## 13. Acceptance

- Cancel/timeout không để orphan process.
- Không đọc/ghi ngoài workspace policy.
- Secret không xuất hiện trong argv/log/event/artifact.
- Claude và Codex adapter pass cùng conformance suite nhưng giữ protocol riêng.
- File diff/output evidence truy vết tới execution/attempt.
