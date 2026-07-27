# R04 — Windows CLI Execution Security

| Field | Value |
|---|---|
| Source ID | `HH-RES-R04` |
| Version | 0.2 |
| Date | 2026-07-27 |
| Status | Research — review required |
| Scope | Harness Hub local-v1 on Windows |
| Normative authority | Reference only; ADR/design documents remain authoritative |
| Code baseline | `hub/services` and `hub/tests` inspected 2026-07-27 |

### Revision note

Version 0.2 incorporates cross-review corrections: WFP is treated as privileged infrastructure; Job Object scope is limited to associated `CreateProcess` descendants; file/disk quotas are separated from process quotas; redaction claims are limited to exact known-secret overlap; and the controlled Windows executor is a distinct Gate D milestone rather than ordinary adapter hardening.

## 1. Executive verdict

**NO-GO for enabling workspace-write CLI under Gate D with the current implementation.**

The current wrappers provide useful application-level guardrails, but they do not create a Windows security boundary. The two immediate blockers are:

1. timeout/cancel kills only the process represented by `Popen`; there is no Job Object or verified process-tree cleanup;
2. every provider process inherits a copy of the complete Hub environment and runs under the Hub user's token.

The current `read-only` chat mode may remain available only as a **low-assurance, non-sensitive local feature** while the restrictions in §8 are enforced. It must not be described as OS-isolated, network-denied, secret-isolated, or safe for restricted data.

Recommended Gate D baseline is a **separate privileged executor milestone**, not a small modification to the in-process local adapter:

- pinned native executable launch, or a pinned native runtime plus immutable/hash-pinned JavaScript entrypoint, without `.cmd`/`.bat` mediation for untrusted arguments;
- Windows Job Object with no breakaway, kill-on-close, process/memory/time limits and completion tracking;
- dedicated low-privilege execution identity or an experimentally validated AppContainer/LPAC launcher;
- disposable per-run workspace with ACL/reparse-point controls;
- minimal environment allowlist and scoped provider credential;
- enforceable egress policy installed by an administrator or a separately authenticated privileged broker while Hub remains non-elevated;
- bounded output plus hard file/disk quotas supplied by an isolated quota volume, separate identity/storage broker, or equivalent OS boundary;
- adversarial Windows-specific conformance tests.

Windows Sandbox is a candidate for a stronger future worker profile, but its current automation/I/O/concurrency constraints make it a separate executor design, not a transparent replacement for `subprocess.Popen`.

## 2. Evidence method

Labels used throughout:

- **VERIFIED-CODE** — directly observed in repository source/tests.
- **VERIFIED-DOC** — stated by an authoritative primary source.
- **INFERRED** — conclusion derived from verified evidence; still needs an adversarial test.
- **PROPOSED** — recommended architecture or control.
- **UNKNOWN** — not established by current code, documentation or a completed prototype.

Security language is deliberately narrow. A provider's `read-only`, `plan`, tool-deny or sandbox flag is not treated as a Windows OS security boundary unless the resulting Windows token, filesystem, process-tree and network behavior are independently verified.

## 3. Current implementation evidence

### 3.1 Process creation and termination

- **VERIFIED-CODE:** `ProcessRegistry.spawn` uses `subprocess.Popen(..., shell=False)` with pipes, caller-provided `cwd` and caller-provided `env` (`hub/services/providers/procs.py:68-98`).
- **VERIFIED-CODE:** timeout handling calls `entry.process.kill()` and then waits five seconds (`hub/services/providers/procs.py:101-113`); shutdown `kill_all()` also calls `process.kill()` once per tracked root (`hub/services/providers/procs.py:129-137`).
- **VERIFIED-CODE:** Git jobs independently use plain `Popen`, and timeout calls `stream.process.kill()` (`hub/services/gitjobs.py:141-153`, `hub/services/gitjobs.py:339-357`).
- **VERIFIED-CODE:** the only process tests prove that the root sleeper exits and that the concurrent-root cap works; they do not spawn a child/grandchild or test orphans (`hub/tests/test_providers.py:347-395`).
- **VERIFIED-DOC:** on Windows, Python implements `Popen.kill()` with `TerminateProcess`; a Job Object is the Windows primitive for managing a process group as a unit. A Job Object can terminate associated processes and `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` terminates the associated hierarchy when the last job handle closes.
- **INFERRED, HIGH:** current timeout, cancellation and shutdown do not establish child/grandchild cleanup. A CLI or `cmd.exe` shim can leave descendants running.
- **VERIFIED-DOC / RESIDUAL RISK:** automatic Job inheritance applies to associated processes and descendants created through the normal `CreateProcess` lineage. A process that can use WMI/COM, a service manager, Task Scheduler, another broker, or a separately privileged identity may cause execution outside that Job lineage. Job containment therefore requires a restricted identity that lacks service/task creation and remote-process/broker rights, plus explicit escape tests; it is not a machine-wide execution boundary.

### 3.2 Command resolution and quoting

- **VERIFIED-CODE:** `resolve_cmd` searches `PATH`; on Windows it changes `.cmd`/`.bat` execution into `["cmd", "/c", resolved, ...]` (`hub/services/providers/procs.py:15-31`).
- **VERIFIED-CODE:** prompts are passed as CLI arguments to Claude, Codex and Gemini (`hub/services/providers/claude_cli.py:29-52`, `hub/services/providers/codex_cli.py:29-42`, `hub/services/providers/gemini_cli.py:62-74`).
- **VERIFIED-DOC:** Microsoft documents that `.bat`/`.cmd` execution requires a command interpreter and explicitly warns against the `cmd.exe /c` pattern in the `CreateProcess` documentation. `cmd.exe` assigns special meaning to characters including `&`, `|`, `<`, `>`, parentheses and quotes. Python also documents that batch files can be parsed under shell rules even when the library call uses `shell=False`.
- **INFERRED, HIGH:** wrapping an npm shim in `cmd /c` creates a second parser boundary for untrusted prompt text. A Python argument list alone is not proof that `cmd.exe` receives every prompt byte as inert data.
- **PROPOSED:** resolve provider entrypoints to a pinned native `.exe`, or invoke an immutable/hash-pinned JavaScript entrypoint with a pinned native `node.exe`; reject `.cmd`, `.bat`, UNC and user-writable executable/entrypoint paths for unattended execution. Providers without one approved chain are unsupported. If a batch shim is unavoidable, pass prompt content over stdin or a protected response file supported by the provider and prove quoting with an adversarial corpus.

### 3.3 Environment, credentials and working directory

- **VERIFIED-CODE:** all three chat adapters start with `os.environ.copy()` and execute with `cwd=config.ROOT` (`hub/services/providers/claude_cli.py:166-185`, `hub/services/providers/codex_cli.py:166-185`, `hub/services/providers/gemini_cli.py:94-99`).
- **VERIFIED-CODE:** Git jobs also copy the complete Hub environment before launch (`hub/services/gitjobs.py:545-556`).
- **INFERRED, CRITICAL:** any credential, proxy setting, cloud token, user-profile pointer or executable-search influence present in the Hub environment is available to the child. This contradicts D04/D06's minimal-env contract.
- **INFERRED, HIGH:** running under the Hub user's normal token permits access to resources available to that user unless separately denied by ACL/AppContainer policy. Setting `cwd` does not constrain filesystem access.
- **PROPOSED:** construct the environment from an empty map using an allowlist; provide a job-scoped `TEMP`, `TMP`, `USERPROFILE` and tool config root; inject at most one scoped provider credential reference/value; remove unrelated `*_KEY`, `*_TOKEN`, `*_SECRET`, cloud credentials, SSH/Git credential helpers and inherited proxy variables unless explicitly required.

### 3.4 Provider-level controls

- **VERIFIED-CODE:** Claude is started in `plan` mode with `Edit`, `Write` and `Bash` disallowed (`hub/services/providers/claude_cli.py:29-45`).
- **VERIFIED-CODE:** Codex is passed `-s read-only`, but also `--skip-git-repo-check` (`hub/services/providers/codex_cli.py:29-42`).
- **VERIFIED-CODE:** Gemini is started only with `-p`; current wrapper supplies no sandbox, approval or tool restriction flag (`hub/services/providers/gemini_cli.py:70-74`).
- **VERIFIED-DOC:** Anthropic describes these as Claude Code permission/tool controls. Google documents Gemini CLI sandboxing as optional and the CLI reference currently defaults `--sandbox` to false.
- **INFERRED, HIGH:** application-level options reduce accidental actions but do not protect against a compromised provider binary, dependency, parser, plugin/config extension, inherited credential or Windows access token.
- **INFERRED, HIGH:** under the same Windows user, `read-only` means provider/application policy only. It does not prevent filesystem reads or provide confidentiality containment.

### 3.5 Workspace boundary and reparse points

- **VERIFIED-CODE:** `resolve_in_root` resolves a candidate and checks lexical ancestry of the resolved path (`hub/services/boundary.py:8-31`).
- **VERIFIED-CODE:** tests cover a normal in-root path and `..` traversal only (`hub/tests/test_boundary.py:11-18`).
- **VERIFIED-CODE:** Git jobs verify the recorded worktree path equals the expected path, then run Codex in that worktree (`hub/services/gitjobs.py:122-130`, `hub/services/gitjobs.py:156-168`).
- **VERIFIED-DOC:** NTFS reparse points alter normal path behavior. Microsoft documents that opening without `FILE_FLAG_OPEN_REPARSE_POINT` normally follows a symbolic-link target, and that file APIs differ in how they handle links.
- **INFERRED, HIGH:** a check based on `Path.resolve()` is useful validation but is not a durable capability. A writable path component can be exchanged for a junction/symlink after validation, and provider processes are not forced through `resolve_in_root`.
- **PROPOSED:** reject reparse points in every ancestor and target of the execution root before launch; open sensitive paths by handle with reparse-safe flags; keep parent directories non-writable by the execution identity; rescan before artifact collection; quarantine any output path whose final handle is outside the approved volume/root.

### 3.6 Network and resource controls

- **VERIFIED-CODE:** no reviewed source creates Windows Firewall/WFP rules or an AppContainer network capability.
- **VERIFIED-CODE:** governance can classify/block a `network` tier as degradation rises, but this is an application decision rather than OS egress enforcement (`hub/services/governance.py:56-73`).
- **VERIFIED-CODE:** current process controls cap elapsed time and number of concurrent root processes only (`hub/services/providers/procs.py:77-81`, `hub/services/providers/procs.py:101-113`).
- **VERIFIED-CODE:** `services/sandbox_manager.py` source is absent; only a compiled cache file exists, so no current enforceable behavior can be reviewed.
- **VERIFIED-DOC:** Windows Filtering Platform supports filtering per application, user and connection; ALE layers can authorize outbound connection creation using application and user identity.
- **VERIFIED-DOC / INFERRED:** installing or mutating WFP/Windows Firewall policy is privileged host administration. Hub must remain non-elevated; enforcement therefore requires rules pre-provisioned by an administrator or a separately authenticated privileged broker with a narrow job-scoped API.
- **INFERRED, HIGH:** D04/D06 requirements for deny-by-default egress, CPU/output/file quotas and process-tree cleanup are not implemented. Job Objects can enforce process/memory/CPU/time limits, but neither a watcher nor a Job Object creates hard file-count, bytes-written or free-disk quotas.

### 3.7 Output and audit handling

- **VERIFIED-CODE:** provider stderr is read and may be returned directly as an error message (`hub/services/providers/claude_cli.py:230-252`, `hub/services/providers/codex_cli.py:239-261`, `hub/services/providers/gemini_cli.py:120-132`).
- **VERIFIED-CODE:** Git job stdout/stderr is appended to a local log as received (`hub/services/gitjobs.py:215-218`, `hub/services/gitjobs.py:339-357`).
- **INFERRED, HIGH:** output is unbounded and unredacted at the process boundary. A malicious/noisy CLI can exhaust disk or return secrets to logs/API clients before later artifact inspection. Redaction can remove exact known secret values and selected structured fields; it cannot guarantee removal of arbitrary transformed, encoded or previously unknown secrets.

## 4. Threat matrix

| ID | STRIDE | Threat / abuse case | Current control | Gap | Required control | Severity |
|---|---|---|---|---|---|---|
| WCLI-T01 | E/D | associated child/grandchild survives timeout/shutdown, or execution escapes through WMI/COM/service/task broker | root `Popen.kill()` | no tree membership, zero-active confirmation or restricted broker rights | Job Object plus restricted identity and escape tests | Critical |
| WCLI-T02 | I | child reads unrelated Hub/provider/cloud secrets | complete inherited environment | no allowlist/scoping | empty-base env, scoped credential, dedicated profile | Critical |
| WCLI-T03 | E/T | prompt metacharacters cross `.cmd`/`cmd /c` parser | `shell=False`, list args | explicit shell still introduced | native pinned executable; stdin; adversarial quoting tests | High |
| WCLI-T04 | E/I | provider reads user profile, SSH, Git, browser or other repos | provider self-policy | normal user token has broad access | restricted identity/AppContainer plus ACL | Critical |
| WCLI-T05 | T | junction/symlink escapes workspace or redirects output | one-time `Path.resolve()` | TOCTOU and provider bypass | reparse rejection, handle-based verification, protected parents | High |
| WCLI-T06 | I | unrestricted egress/exfiltration to arbitrary endpoint | governance labels | no OS enforcement | admin-pre-provisioned WFP, authenticated privileged broker, AppContainer or Gate E isolated worker | Critical for restricted data |
| WCLI-T07 | D | output pipe/log/disk exhaustion | wall timeout | no byte/file/disk/memory bounds | bounded ring buffers and Job process limits; quota volume/separate identity or broker for hard file/disk bounds | High |
| WCLI-T08 | E | malicious executable selected through PATH/config | `shutil.which` | user-writable path and no identity verification | absolute allowlist, signer/hash/version provenance | High |
| WCLI-T09 | T/I | project-local provider config/plugin expands tools or loads secrets | provider flags | config discovery not isolated | clean config root; deny project config unless approved | High |
| WCLI-T10 | R/I | stdout/stderr leaks secrets; audit cannot prove containment | raw logging | no boundary redaction/provenance | exact known-secret overlap redaction, structured-field removal, truncation and launch-policy audit | High |
| WCLI-T11 | E | Hub runs elevated; child inherits effective authority | none observed | privilege inheritance | startup NO-GO when elevated; restricted launch token | Critical |
| WCLI-T12 | T | post-run scan misses writes outside worktree | Git diff | filesystem access is broader than diff | OS access boundary and external-write canary tests | High |

## 5. Windows isolation options

| Option | Process tree | Filesystem | Network | Identity/secrets | Compatibility | Assessment |
|---|---|---|---|---|---|---|
| Provider `plan`/`read-only`/tool deny | No OS guarantee | same-user filesystem remains readable unless ACL denies | generally provider-defined | same user/env | High | Application policy/defense in depth only |
| `CREATE_NEW_PROCESS_GROUP` | Enables console control signaling | None | None | same token | Medium | Graceful cancel aid, not containment |
| Job Object | Strong unit lifecycle; process/memory/CPU limits | None by itself | None by itself | same token unless combined | High; nested-job cases need tests | Mandatory supervisor primitive |
| Restricted token + dedicated desktop + ACL | Inherits only if combined with Job | ACL-based, configurable | requires privileged WFP/firewall infrastructure | removes privileges/SIDs; dedicated profile possible | Medium; CLI auth/config needs prototype | Separate Gate D executor candidate |
| AppContainer/LPAC + Job | Stronger process/resource boundary | capability/DACL based | capability based | isolated identity/credentials | Unknown for all target CLIs | Preferred experiment; adopt only after compatibility tests |
| Dedicated local user + ACL + pre-provisioned WFP/broker | Job still required | good if workspace parents protected | per-app/user WFP possible through privileged infrastructure | isolated user profile | Medium/high | Separate Gate D executor milestone |
| Windows Sandbox | VM/kernel isolation, disposable | mapped folders RO/RW | networking can be disabled | separate sandbox account | Low for current streaming: one instance; CLI exec has I/O/session constraints | Future isolated executor, not transparent MVP wrapper |
| Hyper-V/remote worker | Strong VM boundary | explicit transfer | explicit virtual network | separate guest credentials | Lowest/most operational cost | Gate E / restricted workloads |

Important limitations:

- **VERIFIED-DOC:** a Job Object manages and limits a process group, but security access must be set per process on modern Windows. It is not a filesystem or network sandbox.
- **RESIDUAL RISK:** Job membership does not cover execution requested through out-of-job WMI/COM servers, services, scheduled tasks or other brokers. The run identity must lack those rights; tests must verify denial. The claimed guarantee is limited to associated process descendants.
- **VERIFIED-DOC:** `CreateRestrictedToken` can disable SIDs, delete privileges and add restricting SIDs; Microsoft also warns that restricted applications should not share the default desktop with unrestricted applications.
- **VERIFIED-DOC:** AppContainer requires a profile, capabilities and `STARTUPINFOEX` security attributes. Compatibility with Node-based provider CLIs and their authentication stores is **UNKNOWN** until prototyped.
- **VERIFIED-DOC:** Windows Sandbox networking is enabled by default; mapped write folders persist host changes. The current Sandbox CLI supports automation on Windows 11 24H2+, but command I/O retrieval and active-session requirements constrain Harness streaming. It also currently permits only one Sandbox instance.
- **PROPOSED:** do not treat Docker Desktop Linux containers as a Windows-native guarantee without a separate mount, daemon/socket, credential and egress threat model.

## 6. Required process-supervisor protocol

**PROPOSED ADR candidate: `ADR-WIN-001 Windows CLI Supervisor`.**

1. Refuse launch when Hub is elevated or when the configured executable is not an approved absolute local path.
2. Create a Job Object and apply limits before untrusted code can run:
   - `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`;
   - no `BREAKAWAY_OK` or `SILENT_BREAKAWAY_OK`;
   - active-process, per-job memory and CPU/time limits;
   - completion port or equivalent active-process notifications.
3. Create the child suspended using a minimal explicit handle list; avoid inheriting unrelated handles.
4. Assign the suspended child to the Job Object; fail closed on assignment failure, including unexpected parent-job constraints.
5. Apply the selected restricted token/AppContainer and mitigation policy.
6. Resume only after job assignment, stdout/stderr limits, workspace ACL and pre-provisioned/broker-confirmed egress policy are ready.
7. On cancel: close stdin/request graceful stop for a short bounded grace interval; then `TerminateJobObject`.
8. Do not mark terminal until the Job reports zero active processes and streams are drained/truncated.
9. Close the final Job handle in all failure/shutdown paths; persist launch and cleanup evidence after removing exact known-secret overlaps and sensitive structured fields.

This avoids the create-then-assign race for normal associated process descendants. It does not contain execution delegated through an authorized external broker; restricted identity rights and `SEC-WIN-021..024` address that residual risk.

## 7. Command, environment and workspace contract

### 7.1 Command

- executable selected from an absolute allowlist;
- accept either a pinned native executable or pinned native runtime plus immutable/hash-pinned script entrypoint; otherwise provider is unsupported;
- reject `.cmd`, `.bat`, UNC paths and executable/runtime/entrypoint paths writable by the run identity;
- record resolved runtime and entrypoint paths, versions, signer/hash and policy version;
- never form a PowerShell or `cmd.exe` command string from prompt/workspace/model input;
- provider prompt should use stdin or a native argument protocol whose parser corpus is tested;
- enforce argument count and total command-line length before launch.

### 7.2 Environment

Start from empty and allow only:

- `SystemRoot`, `WINDIR`, explicit tool/runtime paths;
- run-scoped `TEMP`, `TMP`, `USERPROFILE`, config/cache directories;
- deterministic encoding/locale variables;
- one approved scoped provider credential or broker reference;
- explicit proxy only when the network policy requires it.

Never inherit the Hub's complete `PATH`, `HOME`/profile, Git/SSH credential variables, arbitrary cloud tokens or tool configuration roots.

### 7.3 Workspace

- create a disposable worktree/copy under a non-reparse, non-user-substitutable parent;
- execution identity receives only required read/write ACLs;
- reject any reparse point in input tree for the strict profile, or materialize a link-free copy;
- deny access to `.git` internals where not required; Git operations go through an approved broker when possible;
- use pre/post manifests and soft threshold monitoring for detection; do not label them hard quotas;
- require a quota volume, separate restricted identity/storage broker, or equivalent OS-enforced boundary when hard file-count/bytes/free-disk protection is required;
- verify artifact final handles and volume/root before promotion;
- quarantine unexpected file types, alternate data streams and paths.

## 8. Minimum safe profiles

### 8.1 `windows-cli-readonly-low-assurance`

Permitted only for public/internal-non-sensitive input.

Required:

- provider-native read-only/plan/tool-deny flags;
- pinned native executable or pinned native runtime plus immutable/hash-pinned JavaScript entrypoint;
- Job Object protocol in §6;
- minimal environment and run-scoped profile;
- disposable read-only materialized workspace with reparse points rejected;
- scoped provider credential;
- bounded stdout/stderr and no raw output persistence;
- no elevated Hub;
- explicit acknowledgement that same-user read-only is application policy rather than filesystem confidentiality;
- explicit acknowledgement that provider network access is required and arbitrary-egress denial is not established.

Until WFP/AppContainer egress and identity isolation are implemented, this profile is **not permitted** for restricted secrets, proprietary multi-repo context or untrusted executable content.

### 8.2 `windows-cli-workspace-write-controlled`

This is a separately built, privileged-infrastructure-backed Gate D executor. It is not enabled by merely adding flags to the current local adapter. Remain disabled until all Gate D requirements pass:

- everything in the read-only profile;
- dedicated low-privilege user or validated AppContainer/LPAC;
- ACL-isolated disposable worktree with protected parent;
- provider/tool command allowlist and non-interactive approval policy;
- deny-by-default egress with approved provider destinations through administrator-pre-provisioned WFP policy or a separately authenticated privileged broker; Hub remains non-elevated;
- no host credential-store mount; job-scoped credential only;
- hard process count, memory, CPU/wall and output limits; hard file/disk limits only through a quota volume, restricted storage identity/broker or equivalent OS facility;
- before/after manifest, Git diff, secret scan and quarantine;
- Job reports zero active descendants before review/promotion;
- adversarial tests demonstrate denial of the scoped destructive/out-of-workspace cases; residual risks and tested Windows/provider versions remain documented even when `allow_override` is true.

`allow_override` may approve a business action; it must never disable OS containment.

If privileged egress infrastructure is unavailable, arbitrary-egress denial moves to an isolated worker under Gate E. In that deployment, Gate D can authorize only explicitly non-sensitive workloads; it cannot claim restricted-data or arbitrary-egress containment.

## 9. NO-GO conditions

Reject CLI launch when any condition holds:

1. Hub or launcher is elevated.
2. Job Object creation, limit setup, suspended assignment or completion tracking fails.
3. Executable resolves through `.cmd`/`.bat`, UNC, network share, unapproved hash/signer, or a directory writable by the run identity.
4. Environment cannot be reduced to the approved allowlist.
5. Workspace/root is home, drive root, repository parent, contains an unapproved reparse point, or has a writable ancestor enabling replacement.
6. Required egress restriction cannot be installed and verified for data above the permitted classification.
7. Provider requires a broad user credential store or unrelated secrets.
8. Run identity can write outside its disposable workspace or read a canary secret outside allowed roots.
9. Required output, memory or process limits cannot be enforced; or a workload requiring hard file/disk quotas lacks a quota volume/restricted storage boundary. Soft watcher detection is not sufficient.
10. Provider/sandbox version differs from the conformance-approved manifest.
11. Existing orphan from a prior run is unresolved.
12. Audit, exact known-secret overlap redaction, structured sensitive-field removal or truncation pipeline is unavailable.

## 10. Incident cleanup

1. Stop accepting new CLI work and mark affected executor degraded.
2. Close stdin and issue the provider-specific graceful cancel only within a bounded grace interval.
3. Call `TerminateJobObject`; close Job handles; wait for zero active processes.
4. If zero-active cannot be proven, keep executor quarantined and escalate to operator/host restart. Do not kill by process name.
5. Ask the authenticated privileged broker to revoke job-scoped WFP/firewall policy only after the process tree is gone; verify rollback by rule ID. Non-elevated Hub never mutates host firewall policy directly.
6. Freeze workspace, stdout/stderr tail, executable provenance, policy version and process/accounting metadata. Redact before persistence.
7. Scan and quarantine artifacts; do not auto-promote or commit.
8. Compare external canary locations and egress/audit telemetry for escape indicators.
9. Revoke/rotate the job-scoped credential and any credential plausibly inherited under the old full-environment behavior.
10. Record incident scope and denial; keep Gate D disabled until the failing threat test is added and passes.

## 11. Windows-specific test catalogue

| Test ID | Scenario | Required assertion | Maps to |
|---|---|---|---|
| `SEC-WIN-001` | root spawns child and grandchild, then timeout | Job reaches zero active; all PIDs dead | `EX-003`, `SEC-*` |
| `SEC-WIN-002` | child attempts Job breakaway | creation/escape denied or launch fails closed | `EX-003` |
| `SEC-WIN-003` | Hub shutdown during active tree | kill-on-close removes full tree | `OPS-002` |
| `SEC-WIN-004` | prompt corpus with `&|<>^()%!\"`, Unicode and trailing slashes | exact byte/argument delivery; no marker command runs | `SEC-002` |
| `SEC-WIN-005` | configured `.cmd`, `.bat`, UNC and user-writable executable | launch denied | `EX-001`, `SEC-002` |
| `SEC-WIN-006` | environment seeded with canary keys/tokens | child sees allowlist only | `SEC-002` |
| `SEC-WIN-007` | child reads canary in user profile/SSH/Codex/Claude config | access denied | `SEC-002` |
| `SEC-WIN-008` | junction/symlink inside workspace targets outside file | read/write/artifact promotion denied | `SEC-001` |
| `SEC-WIN-009` | attacker swaps checked directory for junction between validation/use | handle/root verification denies operation | `SEC-001` |
| `SEC-WIN-010` | provider connects to unapproved IPv4/IPv6/loopback/LAN endpoint | connection blocked and audited | `SEC-002` |
| `SEC-WIN-011` | provider connects only to approved broker/provider | succeeds without general egress | `SEC-002`, `EX-001` |
| `SEC-WIN-012` | stdout/stderr flood and no-newline stream | truncation/backpressure; Hub remains responsive | `EX-003`, `SEC-*` |
| `SEC-WIN-013` | fork bomb/process burst | active-process limit enforced; tree removed | `SEC-*` |
| `SEC-WIN-014` | memory/CPU/wall quota breach | deterministic terminal reason and cleanup | `EX-003` |
| `SEC-WIN-015` | file-count/byte/disk quota breach | hard-quota profile blocks further writes; soft profile only alarms/quarantines and is not reported as enforcement | `SEC-*`, `OPS-*` |
| `SEC-WIN-016` | known secret printed across chunk boundaries/stdout/stderr | exact known-secret overlap is removed before log/API persistence; transformed/unknown secret remains residual risk | `SEC-002` |
| `SEC-WIN-017` | project-local malicious provider settings/plugin | clean config root prevents load | `SEC-002` |
| `SEC-WIN-018` | run under elevated Hub | startup/launch denied | `SEC-*` |
| `SEC-WIN-019` | nested parent Job / CI host | assignment behavior detected; no uncontained fallback | `EX-003` |
| `SEC-WIN-020` | cancellation while artifact file is open | tree gone; incomplete file quarantined | `EX-003`, `AR-001` |
| `SEC-WIN-021` | child requests process creation through WMI/COM | restricted identity denies request; no out-of-job payload runs | `SEC-*`, `EX-003` |
| `SEC-WIN-022` | child attempts service creation/start | service-control rights denied and audited | `SEC-*` |
| `SEC-WIN-023` | child attempts scheduled-task creation/run | Task Scheduler rights denied and audited | `SEC-*` |
| `SEC-WIN-024` | child invokes an approved external broker with unapproved payload | broker authentication/authorization denies it; Job cleanup claim remains correctly scoped | `SEC-*` |

Tests must run on supported Windows editions/filesystems, not only mocked `Popen`. At minimum include NTFS on Windows 11 and the actual Python/provider-launch architecture. Provider network calls may remain fake; the OS containment behavior must be real.

## 12. Prototype plan

### Spike A — Job supervisor

Build a small native/ctypes launcher fixture that creates a suspended process, assigns it to a Job, resumes it and tracks completion. Use a fixture tree that spawns via native `.exe`, `cmd.exe` and Node. Demonstrate `SEC-WIN-001/002/003/013/019/021..024`.

Exit criterion: no descendant survives 1,000 timeout/cancel iterations and all failure paths close handles.

### Spike B — restricted identity

Compare:

1. dedicated local user + ACL + Job + WFP;
2. restricted token + dedicated desktop + ACL + Job;
3. AppContainer/LPAC + Job.

Probe provider version/status, authentication, TLS/DNS, config/cache, workspace read/write and streaming. Record every granted capability. Do not weaken host ACLs globally.

Exit criterion: select the least-privilege profile that runs each required provider; unsupported providers remain disabled rather than falling back to normal user execution.

### Spike C — command boundary

Resolve each installed provider to its native entrypoint and pass a generated adversarial argument corpus. Include batch shim comparison only to prove rejection/unsafe cases.

Exit criterion: prompt bytes are delivered exactly without a command marker side effect, or prompt transport moves to stdin.

### Spike D — egress

Prototype administrator-pre-provisioned WFP/ALE policy or a separately authenticated privileged policy broker; Hub remains non-elevated. Test provider endpoint success and block arbitrary Internet, LAN, loopback and IPv6 paths. If no robust privileged enforcement is feasible, record Gate D as non-sensitive-only and move arbitrary-egress containment to the Gate E isolated worker.

Exit criterion: policy is fail-closed, rule lifecycle is tied to job ID, and crash cleanup is independently recoverable.

## 13. ADR recommendations

| ADR | Recommendation | Decision needed |
|---|---|---|
| `ADR-WIN-001` | Adopt suspended-launch Windows Job supervisor, scoped to associated descendants; restrict WMI/COM/service/task rights | Before any Gate D implementation |
| `ADR-WIN-002` | Build a separate dedicated-user/ACL/WFP-broker or AppContainer/LPAC executor after Spike B | Before workspace-write |
| `ADR-WIN-003` | Prohibit batch shims; allow only pinned native executable or pinned runtime + immutable/hash-pinned JS entrypoint | Before controlled read-only claim |
| `ADR-WIN-004` | Define reparse-safe materialized workspace and artifact promotion | Before workspace-write |
| `ADR-WIN-005` | Define admin-pre-provisioned/authenticated-broker egress enforcement; otherwise Gate D is non-sensitive and containment moves to Gate E | Before restricted data or workspace-write |
| `ADR-WIN-006` | Define environment/credential allowlist and per-run profile layout | Immediate |
| `ADR-WIN-007` | Treat Windows Sandbox/remote worker as separate executor capability | Gate E or restricted workload track |

## 14. Design-document patch map

This report does not modify normative documents. After review:

| Finding | Target | Required change |
|---|---|---|
| Job-based tree lifecycle | D04 §CLI adapter; D07 cancellation/SLO | specify suspended assignment, zero-active terminal condition and no-breakaway |
| Minimal environment and identity | D04 request/executor; D06 secrets/threat model | define allowlist and restricted execution identity |
| Batch shim/parser risk | D04 command builder | prohibit `.cmd`/`.bat` for untrusted arguments or require stdin/proven transport |
| Reparse/TOCTOU controls | D04 workspace; D06 path policy | handle/reparse-safe protocol, protected parent and artifact verification |
| Enforceable egress | D04 network policy; D06 governance; D08 Gate D/E | require admin-pre-provisioned/authenticated-broker policy; otherwise Gate D non-sensitive and arbitrary-egress containment moves to Gate E |
| Quotas/output redaction | D04 supervisor; D06 logging; D07 operations | separate Job process limits, hard storage quotas and soft detection; exact known-secret redaction only |
| Windows threat tests | D08 Gate D | add `SEC-WIN-001..024` beneath `SEC-*`, `EX-003`, `OPS-*` |
| Current Gate status | D08 Gate D | retain NO-GO until mandatory test subset passes |

## 15. Open questions and confidence

| Question | Status |
|---|---|
| Can each target provider authenticate and stream under AppContainer/LPAC? | **UNKNOWN** — Spike B |
| Can provider-only egress be expressed robustly despite CDN/DNS endpoint changes? | **UNKNOWN** — likely needs a broker rather than static IP allowlist |
| Do installed Node/npm provider packages expose stable native entrypoints that avoid batch shims? | **UNKNOWN** — Spike C and R05 |
| Will parent Job constraints in developer terminals/CI permit nested Job assignment? | **UNKNOWN** — test `SEC-WIN-019` |
| Can the restricted identity reliably deny WMI/COM/service/task-scheduler escape paths for every supported Windows build? | **UNKNOWN** — tests `SEC-WIN-021..024` |
| Can the deployment pre-provision WFP or operate a narrow authenticated privileged broker without elevating Hub? | **UNKNOWN** — Spike D; otherwise Gate E |
| Which storage mechanism supplies true file/disk quota enforcement? | **UNKNOWN** — watcher/manifest remains soft detection |
| Is Windows Sandbox streaming integration acceptable? | **LOW confidence / currently unsuitable** due documented I/O and concurrency limitations |
| Does current `Path.resolve()` block static links? | **MEDIUM confidence**; it does not solve TOCTOU or constrain child syscalls |
| Is root-only process cleanup insufficient? | **HIGH confidence** |
| Is full environment inheritance a secret-isolation violation? | **HIGH confidence** |

Revalidate this report when Python, Windows support baseline, provider CLI major version, execution identity or sandbox implementation changes.

## 16. Primary sources

Accessed 2026-07-27:

1. Microsoft, [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).
2. Microsoft, [`JOBOBJECT_BASIC_LIMIT_INFORMATION`](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information).
3. Microsoft, [`SetInformationJobObject`](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-setinformationjobobject).
4. Microsoft, [Creating Processes](https://learn.microsoft.com/en-us/windows/win32/procthread/creating-processes).
5. Microsoft, [`CreateProcess`](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).
6. Microsoft, [Process Creation Flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags).
7. Microsoft, [`CreateRestrictedToken`](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-createrestrictedtoken).
8. Microsoft, [AppContainer isolation](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation).
9. Microsoft, [Launch an AppContainer](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer).
10. Microsoft, [Windows Filtering Platform](https://learn.microsoft.com/en-us/windows/win32/fwp/about-windows-filtering-platform).
11. Microsoft, [Application Layer Enforcement](https://learn.microsoft.com/en-us/windows/win32/fwp/application-layer-enforcement--ale-).
12. Microsoft, [Reparse Points](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points).
13. Microsoft, [Symbolic Link Effects on File System Functions](https://learn.microsoft.com/en-us/windows/win32/fileio/symbolic-link-effects-on-file-systems-functions).
14. Microsoft, [`cmd`](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd).
15. Microsoft, [Windows Sandbox configuration](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file).
16. Microsoft, [Windows Sandbox CLI](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli).
17. Python Software Foundation, [`subprocess` documentation](https://docs.python.org/3/library/subprocess.html).
18. Anthropic, [Claude Code CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage).
19. Google, [Gemini CLI reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/cli-reference.md).
20. Google, [Gemini CLI sandboxing](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/sandbox.md).
