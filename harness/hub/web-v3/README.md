# Harness Hub web-v3

React 19 + TypeScript + Vite frontend for Harness Hub.

## Prerequisites

- Node.js 20+
- `pnpm` (recommended via Corepack)
- Harness Hub backend running at `http://127.0.0.1:8799`

## Development

From this directory:

```powershell
corepack enable
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://127.0.0.1:5173`. The Vite development server proxies `/api` requests to the local Hub backend.

## Validate and build

```powershell
pnpm lint
pnpm build
```

`pnpm build` writes the static app to `dist/`. Start the Python Hub backend afterwards to serve that build at `http://127.0.0.1:8799`.

The dashboard uses same-origin `/api` requests; no frontend environment variables are required for the default local setup.
