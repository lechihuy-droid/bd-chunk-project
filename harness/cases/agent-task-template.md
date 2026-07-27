# Agent Task Case Template

Use this template when converting a real workspace task into a repeatable harness case.

## Case Metadata

- ID:
- Owner:
- Subsystem:
- Created:
- Source task:
- Risk level: low | medium | high

## Goal

State the observable end state.

## Starting Context

List files, docs, data, or prior handoff that the agent must read.

## Allowed Actions

List commands, directories, and write boundaries.

## Disallowed Actions

List raw folders, secrets, destructive commands, or scope exclusions.

## Expected Evidence

List traces, reports, tests, screenshots, logs, or output files expected after completion.

## Rubric

Use `harness/rubrics/agent-task-rubric.json` unless this case needs a custom rubric.

## Repair Notes

If the case fails, record the minimal repair target and the evidence that proves the failure.
