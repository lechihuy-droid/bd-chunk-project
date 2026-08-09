# DAY 6–DAY 10 — CERTIFICATION + INTEGRATED HANDS-ON INDEX

This block closes GH-300 concept learning and integrates AI-103 + GH-300 before the AB-100 phase.

```text
DAY 6
GH-300 Agentic Development + Privacy + Architecture
        ↓
DAY 7
Hands-On 1 — Design One Application Agent
        ↓
DAY 8
Hands-On 2 — Tool + RAG + MCP Integration
        ↓
DAY 9
Hands-On 3 — Workflow + Multi-Agent Orchestration
        ↓
DAY 10
Hands-On 4 — Copilot + Agentic SDLC Integration
        ↓
DAY 11
AB-100 Solution Architect Phase
```

## Files

### Day 6 — GH-300

- [`gh-300/DAY06_AGENTIC_DEVELOPMENT_PRIVACY_ARCHITECTURE.md`](./gh-300/DAY06_AGENTIC_DEVELOPMENT_PRIVACY_ARCHITECTURE.md)

Focus:

- Agent Mode mental model
- agent sessions
- subagents
- MCP
- Copilot data/context architecture
- privacy/content exclusions
- safeguards
- testing/review
- developer productivity

### Day 7 — Integrated Hands-On 1

- [`hands-on/DAY07_DESIGN_ONE_AGENT.md`](./hands-on/DAY07_DESIGN_ONE_AGENT.md)

Focus:

- role/goal
- input/output contracts
- agent vs tool boundary
- knowledge/state/memory
- guardrails
- evaluation

### Day 8 — Integrated Hands-On 2

- [`hands-on/DAY08_TOOL_RAG_MCP_INTEGRATION.md`](./hands-on/DAY08_TOOL_RAG_MCP_INTEGRATION.md)

Focus:

- tool contract
- direct read vs RAG
- keyword/vector/hybrid search
- MCP boundary
- permission model
- retry/result validation
- untrusted retrieved content

### Day 9 — Integrated Hands-On 3

- [`hands-on/DAY09_WORKFLOW_MULTI_AGENT_ORCHESTRATION.md`](./hands-on/DAY09_WORKFLOW_MULTI_AGENT_ORCHESTRATION.md)

Focus:

- agent/tool/node classification
- workflow runtime vs orchestrator
- sequential/parallel/handoff/reviewer/supervisor
- state/contracts
- retry/revision
- HITL
- multi-agent evaluation

### Day 10 — Integrated Hands-On 4

- [`hands-on/DAY10_COPILOT_AGENTIC_SDLC_INTEGRATION.md`](./hands-on/DAY10_COPILOT_AGENTIC_SDLC_INTEGRATION.md)

Focus:

- application agent vs coding agent
- context engineering
- task decomposition
- subagents
- test/evaluation strategy
- security review
- change-scope control
- versioning
- PR/review workflow

---

# Exit Gate Before AB-100

You should be able to explain this full stack verbally:

```text
Business Goal
     ↓
Application Agent Contract
     ↓
Tools / Knowledge / MCP
     ↓
Workflow Runtime
     ↓
Multi-Agent / Human Gate
     ↓
Evaluation / Trace / Security
     ↓
Coding-Agent-Assisted SDLC
```

And distinguish:

```text
Agent being built
≠
Coding agent building it

Tool capability
≠
Tool permission

Workflow control
≠
LLM reasoning

RAG
≠
Memory

MCP
≠
A2A
```

Passing this block means the learning path is ready to shift from engineer-level questions to AB-100 solution-architecture questions.
