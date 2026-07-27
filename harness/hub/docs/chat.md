# Harness Hub Chat

Harness Hub includes a local `#/chat` page for streaming responses through NVIDIA's OpenAI-compatible API at `https://integrate.api.nvidia.com/v1`.

## Setup

Set `NVIDIA_API_KEY` in the environment used to start the Hub. A `.env` file is fine if your launcher loads it before `server.py` starts. The Hub never hardcodes, logs, or displays the key value.

If the key is missing, the chat stream returns an SSE `error` event with:

```json
{"message":"NVIDIA_API_KEY not set in environment","code":null}
```

If NVIDIA rejects authentication, the stream returns:

```json
{"message":"NVIDIA_API_KEY not set / invalid","code":null}
```

The page shows the message inline and does not crash.

## Upstream Errors

NVIDIA API status errors are surfaced in the chat stream as HTTP 200 SSE `error` events with both a clear message and the upstream status code. For example, a retired model that returns HTTP 410 end-of-life detail is shown as:

```json
{"message":"Model 'model-id' is unavailable (HTTP 410): The model has reached its end of life and is no longer available.","code":410}
```

Other mapped statuses include HTTP 404 as `Model 'model-id' not found`, HTTP 429 as `Rate limited`, and other status errors as `Upstream error`. The status detail from NVIDIA is included when present.

When the frontend receives an SSE `error` event with `code: 410`, it marks the current model unavailable for the current browser session, disables that row in the custom model picker with an `(unavailable)` suffix, and switches to the default model or first available catalog row. The unavailable marker is not persisted, so a page reload clears it.

## Models

The model picker is loaded from `/api/chat/models`.

`CHAT_MODEL_CATALOG` contains 20 curated NVIDIA chat models with rank, ID, short name, display label, category, best-for text, strengths, weaknesses, recommended use, and avoid-when guidance.

Default: `nvidia/nemotron-3-super-120b-a12b`

Max tokens per response: `16384`

`CHAT_MODELS` is derived from the catalog with `[row["id"] for row in CHAT_MODEL_CATALOG]`. Backend validation and chat send paths still use `CHAT_MODELS`, so every picker option is the same whitelist used by `POST /api/chat`.

Categories:

| Category | Purpose |
|---|---|
| Primary | Main coding, reasoning, test, rubric, and agent workflows |
| Fast | Fast coding, agent batch, and backup generation |
| Judge | Verifier, hard-case review, scoring, and final planning |
| Cheap | Low-cost filtering, formatting, classification, and simple generation |
| Fallback | Stable backup and efficient long-context/reasoning options |
| Multimodal | General fallback for screenshot or image-related coding inputs |

Catalog:

| Rank | Category | Short name | ID |
|---:|---|---|---|
| 1 | Primary | Nemotron 3 Super 120B | `nvidia/nemotron-3-super-120b-a12b` |
| 2 | Fast | DeepSeek V4 Flash | `deepseek-ai/deepseek-v4-flash` |
| 3 | Primary | Mistral Small 4 119B | `mistralai/mistral-small-4-119b-2603` |
| 4 | Primary | MiniMax M2.7 | `minimaxai/minimax-m2.7` |
| 5 | Primary | Qwen 3.5 122B A10B | `qwen/qwen3.5-122b-a10b` |
| 6 | Judge | GPT-OSS 120B | `openai/gpt-oss-120b` |
| 7 | Fallback | Llama 3.3 70B | `meta/llama-3.3-70b-instruct` |
| 8 | Cheap | Nemotron 3 Nano 30B | `nvidia/nemotron-3-nano-30b-a3b` |
| 9 | Primary | Mistral Medium 3.5 128B | `mistralai/mistral-medium-3.5-128b` |
| 10 | Fast | Step 3.7 Flash | `stepfun-ai/step-3.7-flash` |
| 11 | Primary | MiniMax M3 | `minimaxai/minimax-m3` |
| 12 | Fallback | Nemotron Super 49B v1.5 | `nvidia/llama-3.3-nemotron-super-49b-v1.5` |
| 13 | Judge | DeepSeek V4 Pro | `deepseek-ai/deepseek-v4-pro` |
| 14 | Judge | Nemotron 3 Ultra 550B | `nvidia/nemotron-3-ultra-550b-a55b` |
| 15 | Fallback | Qwen3 Next 80B A3B | `qwen/qwen3-next-80b-a3b-instruct` |
| 16 | Cheap | GPT-OSS 20B | `openai/gpt-oss-20b` |
| 17 | Fast | Step 3.5 Flash | `stepfun-ai/step-3.5-flash` |
| 18 | Multimodal | Llama 4 Maverick | `meta/llama-4-maverick-17b-128e-instruct` |
| 19 | Cheap | Llama 3.1 8B | `meta/llama-3.1-8b-instruct` |
| 20 | Fallback | Nemotron Super 49B v1 | `nvidia/llama-3.3-nemotron-super-49b-v1` |

## Reasoning by model family

`CHAT_REASONING` in `config.py` is a first-match prefix map. Models with no matching entry send no reasoning flag.

- `deepseek*`: sends `extra_body={"chat_template_kwargs":{"thinking":true,"reasoning_effort":"high"}}`
- `qwen*`: sends `extra_body={"chat_template_kwargs":{"thinking":true}}`
- `openai/gpt-oss*`: sends top-level `reasoning_effort="high"`
- `nvidia/*`: prepends the system message `detailed thinking on`
- Other configured model families send no reasoning extras.

If NVIDIA rejects request-level reasoning extras with `openai.BadRequestError`, the backend retries once without `extra_body` and without reasoning params. A Nemotron system prompt is kept because it is a normal chat message.

## Streaming Behavior

The backend uses the official `openai` Python SDK with:

```python
OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY"])
```

Reasoning tokens and answer tokens are separate streams. The chat page renders reasoning in a dim collapsible block and renders answer text in the normal assistant bubble. If no reasoning events arrive, the reasoning block is not shown.

## Chat UI

The `#/chat` page is a full-height HUD chat inside the Hub shell. The toolbar stays at the top of the chat panel, the transcript scrolls in the middle, and the composer stays at the bottom.

- The model picker replaces the plain select. It has category quick filters (`All`, `Primary`, `Fast`, `Judge`, `Cheap`, `Fallback`, `Multimodal`), a compact dropdown button, and a searchable popup.
- The dropdown list shows only each model's short display label, for example `#02 DeepSeek V4 Flash - Fast coding batch`. Search matches short name, full ID, or category.
- The selected model detail panel shows short name, category badge, full ID in monospace, best-for text, strengths, weaknesses, recommended use, and avoid-when guidance.
- The full model ID can be copied from the inline `Copy` button or the footer `Copy model ID` button. If the Clipboard API is unavailable, the fallback text field is selected.
- The picker writes the selected model ID to `chatState.model`, persists it as `model` and `selectedModelId` in `harness-hub-chat`, and drives the `POST /api/chat` request body.
- `+ New chat` clears the visible transcript and removes the `harness-hub-chat` localStorage record.
- `Export v` opens a dropdown under the Export button and downloads the transcript as Markdown (`chat-YYYYMMDD-HHMMSS.md`) or JSON (`chat-YYYYMMDD-HHMMSS.json`). The menu closes on outside click or Escape.
- `Copy transcript` copies the same Markdown text used by the Markdown export. If the clipboard API is unavailable, the page selects the text in a fallback field.
- The empty state offers example prompt chips. Selecting one fills and focuses the composer; it does not send or call the API.
- Each assistant message has hover/focus icon actions for `Copy`; the last assistant message also has `Regenerate`, which drops that assistant turn and re-streams from the immediately preceding user message with the currently selected model.
- Reasoning, when streamed by the model, stays plain text in a collapsed `Show thinking` details block.
- While streaming, `Send` becomes `Stop` and aborts the active fetch. The assistant bubble shows a live streaming indicator.
- The transcript autoscrolls while the user is near the bottom. If the user scrolls up, new tokens do not force-scroll and a `Jump to latest` button returns to the newest message.
- `Enter` sends and `Shift+Enter` inserts a newline. The composer shows a live character count.
- The selected model and transcript are persisted in localStorage under `harness-hub-chat`; corrupt stored JSON is ignored and cleared.

## Usage Notes

Each completed assistant turn shows input and output token usage under the reply. The backend also appends a best-effort JSONL usage record to:

```text
harness/hub/.cache/chat_usage.jsonl
```

Records use the same usage event shape as the AI Usage page: `ts`, `source`, `model`, token fields, `total_tokens`, and `calls`. NVIDIA does not provide cache token concepts for this path, so `cache_read_tokens` and `cache_creation_tokens` are recorded as `0`.

## API

### `GET /api/chat/models`

Returns:

```json
{
  "models": ["nvidia/nemotron-3-super-120b-a12b", "..."],
  "default": "nvidia/nemotron-3-super-120b-a12b",
  "catalog": [
    {
      "rank": 1,
      "id": "nvidia/nemotron-3-super-120b-a12b",
      "shortName": "Nemotron 3 Super 120B",
      "label": "#01 Nemotron 3 Super 120B - Primary balanced",
      "category": "Primary",
      "bestFor": "Primary bulk coding/reasoning",
      "strengths": ["Balanced coding", "Reasoning", "Planning", "Tool calling", "1M context"],
      "weaknesses": ["Heavier than flash/nano models"],
      "recommendedUse": "Generate coding tests, reference solutions, rubrics, and reasoning-heavy outputs.",
      "avoidWhen": "Simple formatting, classification, dedupe, or very cheap batch jobs."
    }
  ]
}
```

### `POST /api/chat`

Request body:

```json
{
  "model": "nvidia/nemotron-3-super-120b-a12b",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

Response: `text/event-stream`

Events:

```text
event: reasoning
data: {"text":"partial reasoning"}

event: delta
data: {"text":"partial answer"}

event: done
data: {"usage":{"input_tokens":12,"output_tokens":5,"total_tokens":17},"model":"nvidia/nemotron-3-super-120b-a12b"}
```

Invalid models return HTTP 400. Missing or invalid NVIDIA authentication returns HTTP 200 with an SSE error event:

```text
event: error
data: {"message":"NVIDIA_API_KEY not set in environment","code":null}
```

Upstream NVIDIA API status errors also return HTTP 200 with an SSE error event:

```text
event: error
data: {"message":"Model 'model-id' is unavailable (HTTP 410): end-of-life detail","code":410}
```
