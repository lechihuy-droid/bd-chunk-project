# R05 — Provider Capability and Lifecycle Matrix

```yaml
document_id: HH-RES-R05
version: 0.2
status: Research complete — architecture review required
owner: Execution Platform
verified_at: 2026-07-27
retrieved_at: 2026-07-27T23:03:09+09:00
local_git_sha: a1307b7849a19f06a8cce36373b11c3a0f9ed16d
research_mode: Luna-first structured extraction
normative_targets: [HH-DES-D04, HH-DES-D08]
supersedes: []
related_research: [HH-RES-R02]
```

> Tài liệu này là **research evidence**, không phải coding contract. Capability của sản phẩm chỉ được coi là hỗ trợ khi đồng thời có bằng chứng provider, implementation tương ứng và conformance fixture xanh.
>
> Đây là **living document**. Provider docs, CLI grammar, model catalog và local installation có thể đổi sau `retrieved_at`; mọi claim phải được revalidate theo §14 trước release.

## Revision note

### v0.2 — Evidence audit

- Tách provenance thành `VERIFIED-DOC`, `VERIFIED-HELP`, `VERIFIED-CODE`, `VERIFIED-LIVE`.
- Mọi capability cell có grade `Y/P/N/U/NA` và provenance `DOC/HELP/CODE/LIVE`.
- Bỏ supported-version range chưa qua pinned conformance; dùng `candidate_version` và `supported: null`.
- Hạ Codex session/usage implementation xuống `N/CODE`, live behavior `U/LIVE`.
- Tách NVIDIA hosted API Catalog khỏi local/self-hosted NIM và thay citation embedding bằng LLM/chat reference.
- Thêm evidence snapshot, canonical URLs, test-ID ownership và living-document caveat.

## 1. Executive verdict

Provider layer hiện tại là một chat façade tối thiểu, chưa phải Executor Adapter Layer theo D04.

| Provider | Provider surface đã xác minh | Adapter hiện tại | Readiness |
|---|---|---|---|
| Claude Code CLI | non-interactive, JSON/stream-JSON, resume, model, tool/permission controls, structured output | Có thể launch; parse assistant/result/usage/session; không có token-delta guarantee; cancel chỉ kill tiến trình cha | **Conditional** |
| Codex CLI | non-interactive JSONL, resume, sandbox, model, structured final output | **Không launch được theo config hiện tại**; parser session/usage có khả năng lệch event schema chính thức | **NO-GO** |
| Gemini CLI | non-interactive JSON/stream-JSON, resume, model, tools, usage, exit-code taxonomy | CLI không cài; adapter chỉ đọc plain text, bỏ qua model/session/usage/tool events | **NO-GO** |
| NVIDIA hosted OpenAI-compatible API | chat completion streaming, bearer auth; model-specific capability | Streaming/usage cơ bản hoạt động theo code; không có cancel/deadline, live model discovery, tool mapping hoặc đầy đủ transport error | **Conditional** |

Các kết luận ưu tiên:

1. **VERIFIED-CODE — blocker:** `config.PROVIDERS["codex"]` trỏ tới `C:\Users\HUY\AppData\Local\pnpm\codex`, không tồn tại tại thời điểm kiểm tra. PATH discovery tìm thấy `C:\Users\HUY\AppData\Roaming\npm\codex.CMD`, phiên bản probe `codex-cli 0.144.3`.
2. **VERIFIED-HELP — blocker:** `gemini` không tồn tại trên PATH. Không được coi test giả `gemini-cli 1.2.3` là installed-version evidence.
3. **VERIFIED-CODE — contract gap:** `Provider` protocol chỉ có `status()` và `stream_chat()`; không có lifecycle handle, cancel, deadline, workspace, tool request, request ID hoặc typed provider error (`services/providers/base.py:6-34`).
4. **VERIFIED-CODE — cancellation gap:** timeout/shutdown gọi `Popen.kill()` trên process được spawn, không bảo đảm kill descendant process tree (`services/providers/procs.py:101-137`).
5. **VERIFIED-CODE — environment gap:** cả ba CLI copy toàn bộ `os.environ` và chạy tại `config.ROOT`; không có environment allowlist hoặc execution-scoped workspace.
6. **VERIFIED-CODE — capability truth gap:** status manifest chỉ có `stream`, `resume`, `models`; không thể biểu đạt mức structured output, tools, usage, cancellation, authentication, workspace hay isolation.
7. **PROPOSED:** Gate Phase 3 chỉ mở sau khi mỗi adapter có version-pinned fixture từ chính output protocol của version hỗ trợ, không chỉ fake schema tự định nghĩa.

## 2. Evidence method

### 2.1 Labels

- **VERIFIED-DOC (`DOC`):** official vendor documentation tại URL và retrieval snapshot ghi trong report.
- **VERIFIED-HELP (`HELP`):** local executable discovery hoặc probe an toàn `--version`/`--help`; không phải provider execution.
- **VERIFIED-CODE (`CODE`):** source/config/test local tại `local_git_sha`; fake test chỉ chứng minh parser behavior với fixture giả.
- **VERIFIED-LIVE (`LIVE`):** credentialed provider execution với captured protocol evidence. **Không có LIVE evidence trong campaign này.**
- **INFERRED:** suy luận có chỉ rõ evidence và giới hạn.
- **PROPOSED:** khuyến nghị thiết kế/test, chưa phải hành vi hiện có.
- **UNKNOWN:** chưa đủ evidence; phải fail capability negotiation nếu requirement phụ thuộc claim này.

### 2.2 Probe policy và kết quả

Chỉ chạy discovery, `--version` và `--help`; không login, không gọi model, không dùng credential và không cài package.

| Probe | Kết quả | Label |
|---|---|---|
| `claude --version` | `2.1.220 (Claude Code)` | VERIFIED-HELP |
| `claude --help` | Có `-p`, `stream-json`, `--include-partial-messages`, `--resume`, model, JSON Schema, permissions/tools | VERIFIED-HELP |
| `codex --version` | `codex-cli 0.144.3`; có cảnh báo không dọn được stale temp/không tạo PATH alias | VERIFIED-HELP |
| `codex exec --help` | Có `--json`, `resume`, `-s read-only|workspace-write|danger-full-access`, `-C`, `--output-schema`, `--model` | VERIFIED-HELP |
| configured Codex executable | Không tồn tại | VERIFIED-CODE |
| `gemini` discovery | Không tìm thấy | VERIFIED-HELP |
| NVIDIA call | Không chạy vì credentialed network call ngoài policy | UNKNOWN-LIVE |

### 2.3 Evidence snapshot

| Item | Snapshot |
|---|---|
| Retrieval time | `2026-07-27T23:03:09+09:00` |
| Local source base commit | `a1307b7849a19f06a8cce36373b11c3a0f9ed16d`; uncommitted working-tree state is evidenced separately by cited paths/lines |
| Branch ref read from `.git/HEAD` | `refs/heads/agent/lucida-local-rag-v0-1` |
| Claude resolved by Python `shutil.which` | `C:\Users\HUY\AppData\Roaming\npm\claude.CMD` |
| Claude candidate version | `2.1.220` |
| Codex configured executable | `C:\Users\HUY\AppData\Local\pnpm\codex` — absent |
| Codex resolved on PATH | `C:\Users\HUY\AppData\Roaming\npm\codex.CMD` |
| Codex candidate version | `0.144.3` |
| Gemini resolved executable/version | `None` / `None` |
| NVIDIA endpoint/profile | Hosted API Catalog, `https://integrate.api.nvidia.com/v1`; static configured model catalog; observed `2026-07-27` |

### 2.4 Local code evidence

| Evidence | Vị trí |
|---|---|
| Provider protocol/status/event façade | `hub/services/providers/base.py:6-34` |
| Static registry bốn provider | `hub/services/providers/__init__.py:7-23` |
| Claude argv/parser | `hub/services/providers/claude_cli.py:29-51`, `:166-256` |
| Codex argv/parser | `hub/services/providers/codex_cli.py:29-41`, `:97-260` |
| Gemini argv/parser | `hub/services/providers/gemini_cli.py:55-138` |
| NVIDIA adapter | `hub/services/providers/nvidia_api.py:13-51` |
| NVIDIA OpenAI client | `hub/services/chat.py:16-18`, `:174-231` |
| CLI process supervisor | `hub/services/providers/procs.py:15-137` |
| Provider config/routing | `hub/config.py:345-379` |
| Fake adapter tests | `hub/tests/test_providers.py:23-425` |

## 3. Capability semantics

Ma trận dùng `GRADE/PROVENANCE`:

- `Y`: provider surface và adapter đều thực hiện.
- `P`: provider hỗ trợ nhưng adapter chỉ thực hiện một phần.
- `N`: adapter không hỗ trợ.
- `U`: chưa xác minh.
- `NA`: không áp dụng.
- `DOC`, `HELP`, `CODE`, `LIVE`: provenance như §2.1; có thể ghép `DOC+CODE`.

“Streaming” được tách thành:

1. `event_stream`: có nhiều event có cấu trúc trong lúc chạy;
2. `text_delta`: có partial text chunk thực sự;
3. `line_stream`: chỉ đọc stdout theo dòng, không mang nghĩa token/message delta.

Không được khai báo chung `stream: true` nếu chưa nói rõ loại.

## 4. Full capability matrix — product adapter as implemented

| Capability | Claude CLI | Codex CLI | Gemini CLI | NVIDIA hosted |
|---|---:|---:|---:|---:|
| Installed/configured launch | `Y/HELP+CODE` | `N/HELP+CODE` | `N/HELP+CODE` | `U/LIVE` |
| Non-interactive invocation | `Y/HELP+CODE` | `P/HELP+CODE` | `P/DOC+CODE` | `Y/CODE` |
| Structured event output requested | `Y/HELP+CODE` | `Y/HELP+CODE` | `N/CODE` | `Y/CODE` |
| Event parser implemented | `P/CODE` | `P/CODE` | `N/CODE` | `Y/CODE` |
| True partial text delta | `U/LIVE` | `U/LIVE` | `N/CODE` | `Y/DOC+CODE` |
| Final structured output/schema | `N/CODE` | `N/CODE` | `N/CODE` | `N/CODE` |
| Model override passed | `Y/HELP+CODE` | `Y/HELP+CODE` | `N/CODE` | `Y/CODE` |
| Model discovery | `N/CODE` | `N/CODE` | `N/CODE` | `P/DOC+CODE` |
| Session ID captured | `Y/CODE` | `N/CODE` (`U/LIVE`) | `N/CODE` | `NA/CODE` |
| Resume passed | `Y/HELP+CODE` | `Y/HELP+CODE` | `N/CODE` | `NA/CODE` |
| System prompt | `Y/HELP+CODE` | `P/CODE` | `P/CODE` | `Y/CODE` |
| Usage captured | `Y/CODE` | `N/CODE` (`U/LIVE`) | `N/CODE` | `Y/CODE` |
| Cost captured | `N/CODE` | `N/CODE` | `N/CODE` | `N/CODE` |
| Provider request ID | `N/CODE` | `N/CODE` | `N/CODE` | `N/CODE` |
| Tool event normalized | `N/CODE` | `N/CODE` | `N/CODE` | `N/CODE` |
| Tool execution restricted | `P/HELP+CODE` | `P/HELP+CODE` | `N/CODE` | `NA/CODE` |
| Workspace scoped per execution | `N/CODE` | `N/CODE` | `N/CODE` | `NA/CODE` |
| Minimal environment | `N/CODE` | `N/CODE` | `N/CODE` | `NA/CODE` |
| Explicit client cancel | `N/CODE` | `N/CODE` | `N/CODE` | `N/CODE` |
| Explicit timeout | `P/CODE` | `P/CODE` | `P/CODE` | `U/CODE+LIVE` |
| Descendant cleanup | `N/CODE` | `N/CODE` | `N/CODE` | `NA/CODE` |
| Error taxonomy mapping | `P/CODE` | `P/CODE` | `P/CODE` | `P/CODE` |
| Auth health check | `N/CODE` | `N/CODE` | `N/CODE` | `P/CODE` |
| Output size/backpressure cap | `N/CODE` | `N/CODE` | `N/CODE` | `N/CODE` |
| Compatibility/version gate | `N/CODE` | `N/CODE` | `N/CODE` | `N/CODE` |

### 4.1 Important distinction

Provider documentation describes what a provider surface **can** do. The table above describes what Harness **currently does**. Gateway capability negotiation MUST use the second kind of truth.

## 5. Claude Code CLI

### 5.1 Official and probe-verified provider surface

- **VERIFIED-DOC+HELP:** `claude -p` is non-interactive; `--output-format` supports `text`, `json`, `stream-json`.
- **VERIFIED-DOC+HELP:** resume is available with `--resume`/`-r`; model override and append-system-prompt are documented and present in candidate help.
- **VERIFIED-HELP:** `--include-partial-messages` explicitly requests partial chunks with print + stream-JSON on candidate `2.1.220`.
- **VERIFIED-DOC+HELP:** tool controls include `--tools`, allowed/disallowed tools and permission modes.
- **VERIFIED-HELP:** `--json-schema` is present for structured output validation.
- **VERIFIED-DOC+HELP:** auth can use Anthropic Console OAuth, Claude plan login, Bedrock or Vertex; candidate help also exposes `--bare`, whose Anthropic auth is restricted to explicit API key/helper.

Official references:

- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Claude Code authentication](https://code.claude.com/docs/en/authentication)
- [Run Claude Code programmatically](https://code.claude.com/docs/en/headless)

### 5.2 Current adapter behavior

Invocation:

```text
claude -p <prompt>
  --output-format stream-json
  --verbose
  --permission-mode plan
  --disallowed-tools Edit
  --disallowed-tools Write
  --disallowed-tools Bash
  [--model <model>]
  [--append-system-prompt <prompt>]
  [-r <session-id>]
```

- **VERIFIED-CODE:** assistant text, result usage, result error and `session_id` are parsed from the adapter's assumed fixture schema.
- **VERIFIED-CODE:** only latest user message is sent; earlier transcript relies on provider session.
- **VERIFIED-CODE:** no `--include-partial-messages`; therefore `assistant` records cannot be advertised as token-level deltas.
- **INFERRED:** repeated assistant messages may be emitted as `delta`, but each can be a whole assistant message rather than partial text.
- **VERIFIED-CODE:** denying three tools does not prove all remaining tools/plugins/MCP/hooks are disabled.
- **VERIFIED-CODE+HELP:** adapter inherits user/project settings and full environment. It does not use candidate `--bare`, `--safe-mode`, explicit `--tools ""`, strict MCP config, or setting-source isolation.
- **UNKNOWN:** behavior when resuming a session originally created with different tools/settings/model.

### 5.3 Proposed manifest

```json
{
  "adapter_id": "claude-cli",
  "transport": "process",
  "version": {"candidate_version": "2.1.220", "supported": null, "conformance_fixture": null},
  "output": {
    "protocol": "claude-stream-json",
    "event_stream": true,
    "partial_text": false,
    "usage": true,
    "structured_final": false
  },
  "sessions": {"mode": "provider_reference", "resume": true},
  "model_override": true,
  "tools": {"normalized": false, "profile": "plan-deny-edit-write-bash"},
  "workspace": {"access": "host-visible", "execution_scoped": false},
  "cancel": "parent_process_only",
  "readiness": "conditional"
}
```

`partial_text` chỉ được nâng lên `true` sau fixture dùng `--include-partial-messages` và parser content-block delta.

## 6. Codex CLI

### 6.1 Official and probe-verified provider surface

- **VERIFIED-DOC+HELP:** `codex exec` là documented non-interactive surface.
- **VERIFIED-DOC+HELP:** `--json` phát JSONL; documented event families gồm `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.*`, `error`.
- **VERIFIED-DOC+HELP:** `codex exec resume <SESSION_ID>` và `--last` hỗ trợ resume.
- **VERIFIED-DOC+HELP:** sandbox modes gồm `read-only`, `workspace-write`, `danger-full-access`.
- **VERIFIED-HELP:** `-C/--cd`, `--model`, `--output-schema` và `--ephemeral` có trong candidate help.
- **VERIFIED-DOC:** auth hỗ trợ ChatGPT login, API key và access token; credentials có thể nằm ở keyring hoặc `$CODEX_HOME/auth.json`.

Official references:

- [OpenAI Codex non-interactive mode](https://developers.openai.com/codex/noninteractive)
- [OpenAI Codex CLI reference](https://developers.openai.com/codex/cli/reference)
- [OpenAI Codex authentication](https://developers.openai.com/codex/auth)
- [OpenAI Codex security](https://developers.openai.com/codex/security)

### 6.2 Current adapter behavior and drift

Intended invocation:

```text
codex exec -s read-only --skip-git-repo-check --json
  [-m <model>]
  [resume <session-id>]
  "FRESH START\n\n<prompt>"
```

- **VERIFIED-CODE+HELP — blocker:** configured executable path does not exist. `status()` will not fall back to the working PATH candidate.
- **VERIFIED-CODE+HELP:** options precede `resume`, consistent with candidate `0.144.3` help.
- **VERIFIED-CODE:** parser extracts text from `item.completed` items and some delta shapes.
- **VERIFIED-CODE+DOC:** implementation session capture is `N/CODE`: parser expects top-level `session_id` or `conversation_id`, but documented protocol identifies `thread.started`; exact live field remains `U/LIVE`.
- **VERIFIED-CODE+DOC:** implementation usage capture is `N/CODE`: parser only accepts `token_count`, while documented JSONL completion surface uses `turn.completed`; exact candidate payload remains `U/LIVE`.
- **INFERRED — high risk:** current fake fixture can pass while live usage remains zero and new session ID remains `None`.
- **VERIFIED-HELP+CODE:** read-only sandbox constrains model-generated shell writes; it does not by itself prove user config, plugins, MCP, hooks, network or context discovery are disabled.
- **VERIFIED-CODE:** adapter does not pass `--ignore-user-config`, `--ephemeral`, `--strict-config`, `-C` or `--output-schema`.
- **VERIFIED-CODE:** system prompt is embedded only for a new session; on resume the argument is silently unused by `_build_cmd`.

### 6.3 Proposed manifest

```json
{
  "adapter_id": "codex-cli",
  "transport": "process",
  "version": {"candidate_version": "0.144.3", "configured": null, "supported": null, "conformance_fixture": null},
  "output": {
    "protocol": "codex-exec-jsonl",
    "event_stream": true,
    "partial_text": "unknown",
    "usage": false,
    "structured_final": false
  },
  "sessions": {"mode": "thread_reference", "resume_argv": true, "capture_id": false, "live_schema": "unknown"},
  "model_override": true,
  "tools": {"normalized": false, "sandbox": "read-only"},
  "workspace": {"access": "read-only-policy", "execution_scoped": false},
  "cancel": "parent_process_only",
  "readiness": "no-go"
}
```

Readiness chỉ đổi sau khi sửa executable resolution và lưu golden JSONL captured từ một approved, credentialed smoke run riêng.

## 7. Gemini CLI

### 7.1 Official provider surface

- **VERIFIED-DOC:** `-p` chạy headless.
- **VERIFIED-DOC:** `--output-format json` trả response/stats/error; `stream-json` trả JSONL với `init`, `message`, `tool_use`, `tool_result`, `error`, `result`.
- **VERIFIED-DOC:** documented exit codes: `0` success, `1` general/API error, `42` input error, `53` turn-limit exceeded.
- **VERIFIED-DOC:** `--resume` supports latest/index/UUID; `--model` selects model.
- **VERIFIED-DOC:** auth supports existing cached sign-in for headless, `GEMINI_API_KEY`, hoặc Vertex AI credentials.
- **VERIFIED-DOC:** tool approval, allowed tools, sandbox and workspace trust are separately configurable.

Official references:

- [Google Gemini CLI headless mode](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/headless.md)
- [Google Gemini CLI configuration and flags](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md)
- [Google Gemini CLI authentication](https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/authentication.mdx)
- [Google Gemini CLI sandbox](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/sandbox.md)

### 7.2 Current adapter behavior

Invocation:

```text
gemini -p "<last 4000 characters of reconstructed transcript>"
```

- **VERIFIED-HELP — blocker:** CLI không được cài/discover trên host.
- **VERIFIED-CODE:** `model` và `session_id` được nhận ở function signature nhưng không được đưa vào argv.
- **VERIFIED-CODE:** adapter không yêu cầu JSON/stream-JSON; mỗi dòng plain stdout bị phát thành `delta`.
- **VERIFIED-CODE:** usage luôn là zero và session luôn `None`.
- **VERIFIED-CODE:** transcript bị cắt theo 4000 ký tự, có thể cắt giữa message/role; đây không phải provider-native session semantics.
- **VERIFIED-CODE:** không pass sandbox, approval mode, allowed tools hoặc extension/MCP restriction.
- **VERIFIED-CODE+DOC:** capability hiện ghi `resume: false`, trái với documented provider surface nhưng đúng với implementation adapter.
- **UNKNOWN:** version sẽ được cài; không được pin schema cho đến khi có version thực.

### 7.3 Proposed manifest

```json
{
  "adapter_id": "gemini-cli",
  "transport": "process",
  "version": {"candidate_version": null, "supported": null, "conformance_fixture": null},
  "output": {
    "protocol": "plain-text-lines",
    "event_stream": false,
    "partial_text": false,
    "usage": false,
    "structured_final": false
  },
  "sessions": {"mode": "none", "resume": false},
  "model_override": false,
  "tools": {"normalized": false, "restricted": false},
  "workspace": {"access": "host-visible", "execution_scoped": false},
  "cancel": "parent_process_only",
  "readiness": "no-go"
}
```

Target adapter nên chuyển sang `--output-format stream-json`, parse toàn bộ event taxonomy, pass model/resume và fail closed theo exit code.

## 8. NVIDIA hosted API Catalog vs local NIM

### 8.1 Provider/protocol surface

- **VERIFIED-DOC:** hosted API Catalog exposes `POST https://integrate.api.nvidia.com/v1/chat/completions`; model-specific references document bearer credentials and SSE partial deltas.
- **VERIFIED-DOC:** local/self-hosted NIM LLM exposes an OpenAI-compatible API and `GET /v1/models`; recent NIM reference also documents health/version endpoints.
- **VERIFIED-DOC:** hosted feature shape is model/profile-specific. A tool-capable model page cannot establish tools for every model in the static Harness catalog.
- **UNKNOWN-LIVE:** no hosted request, model/profile response, auth health, request ID or usage shape was observed.
- **UNKNOWN:** hosted API Catalog and local NIM release do not have proven full capability parity; they remain separate transport profiles.

Evidence snapshot:

| Profile | Endpoint/model source | Observed date | Provenance |
|---|---|---:|---|
| Harness hosted | `https://integrate.api.nvidia.com/v1`; static `config.CHAT_MODELS` | 2026-07-27 | CODE |
| NVIDIA hosted catalog | `/v1/chat/completions`; catalog/model pages | 2026-07-27 | DOC |
| Local/self-hosted NIM | deployment-specific base URL and loaded model; `/v1/models` | 2026-07-27 | DOC |
| Actual hosted model/profile | Not executed | 2026-07-27 | U/LIVE |

Official references:

- [NVIDIA hosted LLM API catalog](https://docs.api.nvidia.com/nim/reference/llm-apis)
- [NVIDIA hosted chat-completions model reference](https://docs.api.nvidia.com/nim/reference/openai-gpt-oss-20b-infer)
- [NVIDIA local/self-hosted NIM LLM API reference](https://docs.nvidia.com/nim/large-language-models/latest/reference/api-reference.html)
- [NVIDIA local/self-hosted NIM quickstart](https://docs.nvidia.com/nim/large-language-models/latest/get-started/quickstart.html)

### 8.2 Current adapter behavior

- **VERIFIED-CODE:** base URL cố định `https://integrate.api.nvidia.com/v1`; OpenAI Python client nhận `NVIDIA_API_KEY`.
- **VERIFIED-CODE:** request dùng `chat.completions.create`, `stream=true`, `stream_options.include_usage=true`.
- **VERIFIED-CODE:** content, reasoning content và final usage được normalize theo SDK object shape mà code kỳ vọng.
- **VERIFIED-CODE:** status chỉ kiểm tra biến môi trường có giá trị, không probe auth/model/health.
- **VERIFIED-CODE:** model list lấy từ static `config.CHAT_MODELS`, không gọi live model endpoint.
- **VERIFIED-CODE:** adapter không gửi tool definitions, không normalize tool calls.
- **VERIFIED-CODE:** auth/status errors và `ValueError` được map; generic connection/timeout exceptions từ SDK không được adapter bắt thành `ChatEvent`.
- **VERIFIED-CODE:** không có execution handle/cancel. SDK request timeout/retry policy không được cấu hình hoặc ghi vào manifest.
- **UNKNOWN:** request ID, exact retry count và cancellation behavior của dependency version đang cài.

### 8.3 Proposed manifest

```json
{
  "adapter_id": "nvidia-hosted-openai",
  "transport": "https",
  "version": {
    "profile": "nvidia-hosted-api-catalog",
    "endpoint": "https://integrate.api.nvidia.com/v1",
    "candidate_model": null,
    "observed_at": "2026-07-27",
    "supported": null,
    "conformance_fixture": null
  },
  "output": {
    "protocol": "chat-completions-stream",
    "event_stream": true,
    "partial_text": true,
    "usage": true,
    "structured_final": false
  },
  "sessions": {"mode": "stateless", "resume": false},
  "model_override": true,
  "model_catalog": "configured-static",
  "tools": {"normalized": false},
  "workspace": {"access": "none"},
  "cancel": "none",
  "readiness": "conditional"
}
```

## 9. Lifecycle and cancellation matrix

| Stage | Claude | Codex | Gemini | NVIDIA |
|---|---|---|---|---|
| Availability | `--version` | configured `--version` fails | `--version` unavailable | env key only |
| Build request | argv array, then Windows shim wrapper | argv array, missing target | argv array | OpenAI client request |
| Start | ProcessRegistry | ProcessRegistry | ProcessRegistry | generator begins HTTP |
| Stream | JSON line parse | JSON line parse | plain stdout lines | SDK chunks |
| Complete | result + exit code | success event + exit code | exit code | stream exhausted |
| Timeout | watcher kills parent | same | same | not explicit |
| User cancel | absent | absent | absent | absent |
| Shutdown | `kill_all()` parent only | same | same | no active-request registry |
| Cleanup evidence | unregister entry | unregister entry | unregister entry | client lifetime implicit |

**PROPOSED:** D04 `cancel: best_effort` phải được chia thành:

- `request_cancel`: adapter nhận signal;
- `transport_abort`: HTTP stream/socket đóng;
- `process_root_terminated`;
- `process_tree_terminated`;
- `cleanup_verified`.

Hiện không adapter nào đạt đủ năm mức.

## 10. Authentication, workspace and tools

| Dimension | Claude | Codex | Gemini | NVIDIA |
|---|---|---|---|---|
| Auth surface | cached OAuth/subscription/API/enterprise | cached ChatGPT/API key/access token | cached Google/API key/Vertex | env bearer key |
| Adapter injects scoped credential | No | No | No | Reads process env |
| Full parent env inherited | Yes | Yes | Yes | process env used by SDK |
| CWD | `config.ROOT` | `config.ROOT` | `config.ROOT` | NA |
| Provider-native safety selected | plan + deny 3 tools | read-only sandbox | none | tools absent |
| User/project config isolation | No | No | No | NA |
| Tool events exposed to Runtime | No | No | No | No |

`config.ROOT` resolves to the parent of `harness`, not a per-run workspace. Vì vậy “read-only” không đồng nghĩa “chỉ thấy đúng input artifact”; provider vẫn có thể đọc context ngoài run scope theo behavior/config của chính CLI.

**PROPOSED minimum read-only profile:**

1. canonical per-execution workspace/CWD;
2. minimal environment allowlist plus provider credential reference;
3. disable implicit extensions/plugins/MCP/hooks/memory where supported;
4. explicit provider-native read-only/plan/tool allowlist;
5. process-tree supervision;
6. output byte/event caps;
7. record effective CLI version, argv profile hash and capability-manifest hash.

## 11. Normalized error mapping

| Raw signal | Target category | Retryable | Current coverage |
|---|---|---:|---|
| Missing executable | `PROVIDER_UNAVAILABLE` | No until config changes | status only |
| Candidate version outside conformed allowlist | `CAPABILITY_MISMATCH` | No | absent |
| Auth/login/key invalid | `AUTH_FAILED` | No | Claude partial; NVIDIA partial; others generic |
| Invalid argv/input | `INVALID_REQUEST` | No | generic nonzero |
| Provider/model unavailable | `MODEL_NOT_FOUND`/`PROVIDER_UNAVAILABLE` | policy-dependent | NVIDIA 404/410 message only |
| Rate limit | `RATE_LIMITED` | Yes with bound/retry-after | NVIDIA status code only |
| Network/reset/DNS | `TRANSPORT_ERROR` | Yes bounded | NVIDIA may escape; CLI generic |
| Deadline | `DEADLINE_EXCEEDED` | No at adapter result | CLI parent timeout only |
| User cancellation | `CANCELLED` | No | absent |
| Malformed JSONL | `MALFORMED_OUTPUT` | No | malformed lines silently skipped |
| Nonzero CLI exit | `PROCESS_EXITED` | depends | generic error event |
| Descendant remains | `PROCESS_LOST` | No | not detected |
| Output cap | `OUTPUT_LIMIT` | No | absent |
| Tool/sandbox denial | `SANDBOX_DENIED`/`POLICY_DENIED` | No | not normalized |

**VERIFIED-CODE discrepancy:** malformed JSON lines are silently ignored in Claude/Codex parsers. Nếu process exit `0` và không có recognized success/error event, adapter vẫn có thể phát `done` với empty output/usage. Conformance phải cấm false success này.

## 12. Conformance fixtures

Deterministic suite dùng checked-in sanitized JSONL/text fixtures; real provider smoke là opt-in và không thuộc regression mặc định.

### 12.1 Shared fixtures — proposed IDs

Các ID `R05-P-*` dưới đây là research-local placeholders. Chúng **không phải D08 canonical test IDs** cho đến khi owner cập nhật D08; mọi mapping mới phải ghi `NEW TEST ID REQUIRED`.

| Proposed ID | Fixture | Assertion |
|---|---|---|
| `R05-P-001` | capability manifest schema | mọi field required, không boolean `stream` mơ hồ |
| `R05-P-002` | candidate/conformed version | unconformed candidate fail trước launch |
| `R05-P-003` | normal stream | ordered start/content/usage/completed |
| `R05-P-004` | empty successful process | không được false-success nếu protocol đòi result |
| `R05-P-005` | malformed/interleaved line | warning hoặc `MALFORMED_OUTPUT`, không silently erase terminal truth |
| `R05-P-006` | provider error event + exit 0 | normalized failure, không usage success append |
| `R05-P-007` | nonzero exit + stdout | failure takes precedence |
| `R05-P-008` | timeout with child process | entire tree gone, terminal exactly once |
| `R05-P-009` | cancel before/during/after completion | deterministic terminal/cleanup |
| `R05-P-010` | output/event limit | bounded memory and `OUTPUT_LIMIT` |
| `R05-P-011` | secret-bearing stderr | redacted safe message/reference |
| `R05-P-012` | session create/resume | ID capture and correct argv, no cross-workspace resume |
| `R05-P-013` | model override | exact model in effective request |
| `R05-P-014` | tool event | normalize request without executing outside policy |
| `R05-P-015` | unknown event/version drift | preserve diagnostic ref, fail per compatibility policy |

### 12.2 Provider fixtures

Claude:

- init → assistant text → result success with usage/session;
- `is_error=true` result;
- partial content blocks when `--include-partial-messages` enabled;
- tool-use event under plan/deny policy;
- resume with lost/invalid session.

Codex:

- exact sanitized JSONL from a candidate version promoted by pinned conformance, containing `thread.started`, item events and `turn.completed`;
- `turn.failed`, top-level `error`, command/tool item;
- resume grammar and thread ID capture;
- usage location asserted against the pinned fixture schema, not invented `token_count`.

Gemini:

- `init`, `message`, `tool_use`, `tool_result`, non-fatal `error`, final `result`;
- exit codes 1/42/53;
- stats/usage and session ID;
- model and resume argv;
- trusted/untrusted workspace policy.

NVIDIA:

- streamed text/reasoning/usage;
- no-choices usage chunk;
- 401/403, 404/410, 429 with retry-after, 5xx;
- connection reset/malformed chunk;
- model-specific tool support mismatch;
- cancellation closes stream.

### 12.3 Tests hiện có không đủ làm conformance

`hub/tests/test_providers.py` chứng minh unit behavior đối với fake scripts và mock NVIDIA generator, gồm version parse, argv, basic delta/result/error, timeout root-process và concurrency cap. Nó **không** chứng minh:

- live protocol compatibility;
- true partial streaming;
- process-tree cleanup;
- user cancellation;
- environment/workspace/tool isolation;
- output caps/backpressure;
- current Codex session/usage schema;
- Gemini structured stream/resume/usage;
- NVIDIA transport cancellation/retry.

## 13. Disagreements and refinements to R02

| R02 claim/recommendation | R05 evidence | Resolution |
|---|---|---|
| MVP provider set là Claude, Codex, NVIDIA | Registry thêm Gemini | D04 phải coi Gemini là experimental/no-go đến khi adapter mới pass |
| CLI streaming có thể dùng stream flag | Claude/Codex request structured stream; Gemini adapter không dùng documented stream-JSON; true partial delta chưa chứng minh | Tách event stream khỏi token delta |
| Cancel qua SIGTERM→SIGKILL/process tree | code chỉ `Popen.kill()` root process | Giữ là target design, không mô tả current capability |
| Runtime inject credential context; adapter không tự tìm | CLI adapters kế thừa full env và provider tự đọc cached credential/config | Current implementation trái target; cần env/auth profile |
| Workspace do Runtime chuẩn bị | cả ba CLI chạy ở shared `config.ROOT` | Chưa thực hiện |
| Structured JSON, ví dụ Codex JSON-RPC | official current surface là `codex exec --json` JSONL event stream, không nên gọi JSON-RPC | Sửa thuật ngữ/protocol |
| Không ép CLI support structured output | cả ba documented CLI surfaces đều có structured mode; Gemini adapter chưa dùng | Structured transport nên required cho adapter được product tuyên bố hỗ trợ |
| Adapter bounded retry | code không implement explicit retry cho CLI; NVIDIA phụ thuộc SDK default chưa pin | Retry capability là UNKNOWN/absent |
| Plugin adapters | registry là static module map | R02 là future design, không current fact |
| Claude/Codex host process đủ cho local MVP | missing kill-tree/env/workspace isolation và implicit config | Chỉ read-only experimental; không đạt Gate D |

R02 vẫn có giá trị về ports-and-adapters, lifecycle và conformance direction. R05 thay thế các claim provider-specific chưa version/evidence-pinned.

## 14. Freshness and reverification policy

### 14.1 Pinning

Mỗi launch record:

- adapter ID/version;
- resolved executable absolute path và file hash khi thực tế;
- CLI/API version;
- protocol version/fixture set;
- effective safety profile hash;
- model ID;
- capability manifest hash.

Không dùng `models: null` hoặc unbounded “latest CLI” làm production claim.

### 14.2 Revalidation triggers

Re-run official-doc review + safe help/version probe khi:

- CLI minor/major version đổi;
- parser gặp unknown event;
- official docs/changelog đổi output/session/auth/sandbox;
- provider model deprecated/removed;
- SDK dependency version đổi;
- OS/process supervisor đổi;
- safety profile hoặc tool policy đổi.

### 14.3 Cadence

| Surface | Cadence tối đa | Extra trigger |
|---|---:|---|
| CLI version/help | 30 ngày | executable/version change |
| Official provider docs | 60 ngày | parser incident/changelog |
| NVIDIA model catalog | trước mỗi release | 404/410/deprecation |
| Credential/auth profile | 90 ngày | provider policy change |
| Golden protocol fixture | mỗi conformed/pinned version | unknown event |

UNKNOWN capability tự động trở thành ineligible nếu request yêu cầu capability đó.

## 15. D04 and D08 patch map

| Finding | D04 target | D08/test ownership | Priority |
|---|---|---|---:|
| Capability manifest quá hẹp | §3: typed manifest + confidence/version | `NEW TEST ID REQUIRED`; proposed `R05-P-001/002` | P0 |
| Codex configured path missing | §9 executable resolution/version pin | `NEW TEST ID REQUIRED`; proposed `R05-P-002` + startup-health fixture | P0 |
| Codex event schema drift | §5 event/result, provider profile | `NEW TEST ID REQUIRED`; proposed `R05-P-003/012/015` | P0 |
| Gemini plain output/no model/resume/usage | §9 provider parser | `NEW TEST ID REQUIRED`; proposed Gemini protocol fixture set | P0 |
| No lifecycle cancel handle | §5/§9 cancel semantics | Existing `EX-003` plus `NEW TEST ID REQUIRED`; proposed `R05-P-009` | P0 |
| Root-only kill | §9 process supervisor | Existing `EX-003` plus `NEW TEST ID REQUIRED`; proposed `R05-P-008` | P0 |
| Shared root/full environment | §9 workspace/env contract | Existing `SEC-001/002`; provider-specific fixture ID required | P0 |
| False success on malformed/empty stream | §5/§6 terminal/error rules | `NEW TEST ID REQUIRED`; proposed `R05-P-004/005/006` | P0 |
| Provider-native config/tool leakage | §9 safety profile | Existing `SEC-002` plus `NEW TEST ID REQUIRED`; proposed `R05-P-014` | P0 |
| NVIDIA no explicit timeout/cancel/error map | §8 HTTP adapter | `NEW TEST ID REQUIRED`; proposed `R05-P-007/009` + hosted error fixture | P1 |
| No request ID/cost/tool normalization | §5 result, §8/§9 adapters | `NEW TEST ID REQUIRED`; proposed `R05-P-014` + accounting fixture | P1 |
| No live model discovery/freshness | §3 capability/model catalog | `NEW TEST ID REQUIRED`; proposed release-freshness gate | P1 |

## 16. Recommended implementation order

1. Replace `Provider` façade with versioned adapter manifest + execution handle, nhưng giữ compatibility shim cho current chat API.
2. Centralize executable resolution and candidate/conformance gate; repair Codex config before any adapter migration.
3. Introduce protocol-specific parsers fed only by checked-in golden fixtures.
4. Upgrade Gemini to structured stream, model/resume/usage/error handling; keep disabled until installed version passes.
5. Add execution-scoped CWD, minimal env and provider safety profiles.
6. Implement cancellation and Windows process-tree cleanup from R04; do not advertise cancel before that.
7. Add explicit NVIDIA timeout/transport-abort/error mapping and live/catalog validation strategy.
8. Run optional credentialed smoke separately with explicit user approval, sanitize output, rồi mới promote candidate thành supported version.

## 17. Go/no-go

### Gate Phase 3 — Provider adapters

**NO-GO** as a complete four-provider set.

- Claude: conditional pilot for read-only chat after parser/output-limit/process cleanup tests.
- Codex: NO-GO until executable resolution and protocol fixture/session/usage parsing are fixed.
- Gemini: NO-GO until installed, version-pinned and rewritten around stream-JSON.
- NVIDIA: conditional read-only chat; NO-GO for tools, cancel guarantee or production retry semantics.

### Gate D — Controlled CLI

**NO-GO** for every CLI adapter until R04 controls exist: execution-scoped workspace, minimal env, process-tree termination, quotas, explicit tool/config isolation and adversarial tests.

## 18. Open questions

1. Codex `0.144.3` exact JSONL fields for thread ID and usage — needs one explicitly approved credentialed smoke capture.
2. Claude partial-message event schema under installed `2.1.220` — same requirement.
3. Gemini candidate version to detect after installation, rồi pin only after conformance.
4. NVIDIA hosted API request ID, timeout, retry and cancellation behavior under the installed OpenAI SDK.
5. Whether product wants provider-native sessions at all, or stateless reconstructed context as v1 default.
6. Whether provider CLIs may load user/project plugins, MCP, hooks and memory; recommended default is deny unless explicitly approved.

Confidence:

- Local source/config/test assessment: **high**.
- CLI official surface and safe local help/version: **high** for Claude/Codex, **medium** for Gemini because not installed.
- Live provider event schemas/runtime auth health: **UNKNOWN-LIVE** by design; no credentialed call was made.
- NVIDIA protocol overview: **medium**; hosted endpoint behavior must not be assumed identical to every local NIM release.
