# Harness Layer

This folder contains the declarative control layer for the BD Harness.

Folders:

- registry: catalogs for agents, skills, and runtime profiles.
- workflows: workflow definitions and stage gates.
- policies: governance and guardrail rules.

The Harness defines stage order, allowed responsibilities, and validation gates. Deterministic implementation lives under `src/bd_chunk/`.
