# Harness Releases

## v0.002 — 2026-08-05

- `harness/hub`: fixed the chat drawer/sidebar toggle overlapping the topbar on narrow
  viewports (`.cw-drawer-toggle` had no positioned ancestor), fixed the collapsed sidebar
  covering the main window at drawer width (`.app.sidebar-collapsed > aside` rules were not
  scoped to desktop widths), and fixed a dead-end where a collapsed chat-sessions drawer could
  not be reopened below 1280px. Also gave the drawer inset and z-index stack named CSS
  variables instead of hardcoded values. Continuing work on the file-backed workflow engine,
  run store, artifact library, and approval-interrupt UI already in this folder.
- `harness/version-governance`: new. A freeze-then-execute run governance service — Workflow
  Release, Environment Mapping, Frozen Run Manifest, Execution Run, Artifact/Artifact Revision,
  Approved Baseline, Delivery Lineage, and a deterministic Explain Difference algorithm. Adopts
  LangGraph for execution and MLflow for prompt versioning/tracing; the governance layer itself
  (release, manifest, lineage, diff) is built new. Mounted into the Harness Hub UI via a
  `/api/vgov/*` proxy — no standalone control-plane frontend. See
  `harness/version-governance/USER-GUIDE.html` and `harness/version-governance/50_sdd/` for the
  full requirements/design/build-plan trail. Definition of Done: 12/12 automated checks pass
  (`harness/version-governance/verify_dod.py`).
