# Super Agent Runtime Plans

Folder nay chi chua plan/review de apply vao Harness Hub. Tai lieu goc tu ben ngoai nam trong `../../refer/`.

## Latest

Latest plan: [`v0.2-langgraph-integrated.md`](v0.2-langgraph-integrated.md)

Ly do latest: v0.2 giu ket luan DeerFlow nhung them LangGraph-compatible substrate: typed state, reducers, checkpoints, interrupts/resume, streaming event taxonomy, va assistants/threads/runs vocabulary.

## Version table

| Version | File | Status | Date | Notes |
|---|---|---|---|---|
| `v0.2` | `v0.2-langgraph-integrated.md` | latest | 2026-07-04 | LangGraph-integrated plan; use this for implementation. |
| `v0.1` | `v0.1-deerflow-baseline.md` | superseded | 2026-07-04 | DeerFlow baseline; retained for rationale/history. |

## Update rules

1. New plan versions use `vMAJOR.MINOR-short-name.md`.
2. Do not edit old versions for semantic changes; create a new version instead.
3. Only fix typos/links in old versions.
4. When a new version is created, update:
   - `README.md`
   - `latest.md`
   - `CHANGELOG.md`
   - `MANIFEST.json`
   - the `Status` metadata inside affected plan files
5. `refer/` remains source material only. No Hub implementation plan should live in `refer/`.
