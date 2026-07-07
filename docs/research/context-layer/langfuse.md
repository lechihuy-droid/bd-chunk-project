# Langfuse Implementation Research Note

## Status

- **Priority:** P1+
- **Harness Level:** L6 — AgentOps / Observability
- **Research Type:** Implementation evaluation
- **Adoption Status:** Research → Benchmark candidate
- **Official Repo:** https://github.com/langfuse/langfuse
- **Docs:** https://langfuse.com/docs
- **Overall Score:** 9.8 / 10

## Why this matters for BD Harness

BD Harness needs an AgentOps layer before it can be trusted in repeated delivery workflows.

Without observability, the team cannot reliably answer:

- Which agent step failed?
- Which prompt version produced the output?
- Which tool call caused latency or cost spikes?
- Which BD output was generated from which context chunks?
- Did a workflow regression happen after prompt / model / tool changes?

Langfuse should be evaluated as the primary candidate for the BD Harness observability backend.

## Fit to Harness Architecture

Langfuse is not the runtime. It is the runtime operations layer.

It should sit behind the Harness Orchestrator and receive structured events from:

- Workflow runs
- Agent steps
- Tool calls
- Retrieval calls
- Prompt versions
- Model calls
- Evaluator outputs
- Human review gates

```text
BD Harness Runtime
    ↓ emits traces / scores / metadata
Langfuse
    ↓
Trace review / prompt versioning / eval datasets / cost and latency monitoring
```

## Capabilities to evaluate

### 1. Runtime tracing

Map each BD Harness execution to a Langfuse trace:

- `run_id`
- `workflow_id`
- `agent_id`
- `task_id`
- `input_document_id`
- `output_artifact_id`
- `review_status`

### 2. Tool execution tracing

Every tool call should become an observable span:

- GitHub access
- file parsing
- RAG retrieval
- graph query
- Excel extraction
- document generation
- validation / evaluation

### 3. Prompt versioning

Use Langfuse prompt management to track:

- BD generation prompt
- reviewer prompt
- RAG query expansion prompt
- evaluator prompt
- Japanese output quality prompt

### 4. Evaluation pipeline

Use Langfuse datasets and scores to track:

- traceability score
- citation coverage
- hallucination risk
- requirement coverage
- Japanese deliverable quality
- reviewer acceptance rate

### 5. Session replay

Use session replay to debug multi-step BD generation workflows.

This is important when a final BD output looks wrong but the error originated earlier in retrieval, chunking, mapping, or prompt selection.

## BD Harness POC Plan

### POC-1: Minimal trace instrumentation

Goal: instrument one end-to-end BD workflow.

Scope:

1. Ingest a small RD / QA sample.
2. Generate one BD section.
3. Emit trace with agent step, retrieval step, model call, and output artifact metadata.
4. Review the trace in Langfuse.

Success criteria:

- One workflow run appears as a complete trace.
- Each key agent/tool step is visible.
- Cost and latency are visible per model call.
- Metadata includes input source and output artifact link.

### POC-2: Prompt version tracking

Goal: track prompt changes and compare output quality.

Success criteria:

- Two prompt versions can be compared.
- Evaluation scores are attached to both versions.
- Regression can be detected when a prompt gets worse.

### POC-3: Human review + evaluation score

Goal: connect human review result to evaluation data.

Success criteria:

- Human decision is logged as score / metadata.
- Failed outputs can be filtered and replayed.
- The cause of failure can be traced to retrieval, prompt, model, or tool step.

## Open Questions

- Should Langfuse be self-hosted or cloud-hosted for BD Harness?
- What minimum metadata schema should every trace include?
- Which evaluation scores are mandatory before a BD output can pass review?
- How should Langfuse traces link back to GitHub commits, artifacts, and BD review records?
- Should prompt management live in Langfuse, Git, or both?

## Initial Recommendation

Proceed to benchmark.

Langfuse is the strongest current candidate for L6 AgentOps because BD Harness needs production-grade traceability, replay, prompt management, and evaluation history. It should not replace the runtime; it should observe and govern the runtime.
