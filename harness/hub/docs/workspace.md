> **SUPERSEDED 2026-07-29.** Route `#/workspace` không còn tồn tại — `web-v3/src/pages/index.tsx` không đăng ký nó. Giữ lại để truy vết.

# Workspace Route

`#/workspace` is a full-bleed AI Workspace surface inside Harness Hub. It mounts
`window.HubWorkspace` into the normal SPA content root, then `app.js` toggles
`body.route-workspace` so the hub header/sidebar are hidden and the workspace
owns the full `100vw x 100vh` viewport.

Real backend wiring:

- Model catalog: `GET /api/chat/models`; the top-bar selector uses the returned
  `catalog` rows and defaults to the returned `default` model.
- Providers: `GET /api/providers`; each chat owns its `provider` (default
  `nvidia`) and `sessionId` (default `null`). The provider selector is unlocked
  only while the active chat has no messages. CLI providers show a read-only
  badge and version; the model selector is shown only for NVIDIA.
- Chat: `POST /api/chat` sends `{ provider, messages, model? , session_id? }`
  with `X-Hub-Client: harness-hub`; `model` is NVIDIA-only and `session_id` is
  included after a stream `done` event supplies one. Assistant output streams
  from SSE `reasoning`, `delta`, `done`, and `error` events.
- Workspace chat state is in-memory only, so provider and session IDs are not
  persisted across route remounts.

Client-side mock/demo wiring:

- Files and uploads.
- Artifacts, artifact generation, section actions, versions, context selection,
  and export status.
- Export copy/share/download actions, except copy may use the browser clipboard
  when available.

Route isolation:

- Workspace tokens are scoped to `.ws-root`; HUD tokens in `styles-hub.css` are
  not redefined.
- Leaving `#/workspace` calls `HubWorkspace.unmount()`, aborts any active chat
  stream, clears timers, and removes `body.route-workspace` through the router
  class toggle.
