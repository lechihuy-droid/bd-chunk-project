# DAY 14 — SINGLE vs MULTI-AGENT ARCHITECTURE

> Certification: AB-100 — Agentic AI Business Solutions Architect
> Official skills baseline: as of 2026-07-22
> Primary blueprint areas: Plan + Design AI-powered business solutions

## Goal

Biết khi nào một agent là đủ, khi nào cần multi-agent, và khi nào workflow deterministic tốt hơn cả hai.

```text
Business Capability
  ↓
Can one bounded agent own the goal?
  ├─ yes → Single Agent
  └─ no
      ↓
Can deterministic workflow separate the steps?
  ├─ yes → Workflow + specialist capabilities
  └─ no / reasoning across domains
      ↓
Multi-Agent
```

## Official objectives mapped

AB-100 expects the architect to:
- design agentic-first solutions;
- design multi-agent orchestrated solutions;
- create cross-platform AI architecture;
- select where agents, copilots, and deterministic business-process components belong.

## Module 14.1 — Single-agent fit

Use one agent when:
- goal is cohesive;
- tools are bounded;
- context can fit one working scope;
- one policy boundary is acceptable;
- specialization does not materially improve quality.

Benefits:
- simpler observability;
- lower latency;
- lower coordination cost;
- easier security and testing.

## Module 14.2 — Why multi-agent?

Multi-agent is justified by architectural separation, not fashion.

Valid reasons:
- distinct domain expertise;
- different tool/permission boundaries;
- parallel independent work;
- reviewer/approver separation;
- context isolation;
- ownership by different business capabilities.

## Module 14.3 — Patterns

### Sequential

```text
A → B → C
```

Use when outputs naturally become downstream inputs.

### Parallel

```text
      ┌→ A ─┐
Input ┤     ├→ Merge
      └→ B ─┘
```

Use when tasks are independent and latency matters.

### Handoff

```text
Agent A → Agent B
```

Use when ownership changes based on domain/state.

### Reviewer

```text
Builder → Reviewer
           ├─ Approve
           └─ Revise
```

Use when generation and validation should be separated.

### Supervisor

```text
       Supervisor
      /    |     \
     A     B      C
```

Use when dynamic task assignment genuinely requires reasoning.

## Module 14.4 — Runtime vs Orchestrator Agent

```text
Workflow Runtime
= state transitions, retries, persistence, deterministic routing

Orchestrator Agent
= reasoning about which specialist/capability to use when rules are insufficient
```

Exam/architecture trap: do not let an LLM own every execution decision when deterministic workflow semantics are safer.

## Module 14.5 — Security and cost implications

Every extra agent increases:
- identity/permission surface;
- context-transfer risk;
- observability complexity;
- latency;
- token/model cost;
- failure modes.

Therefore:

> Multi-agent must earn its complexity.

## Scenario drill

Design a solution for order exception handling:
- retrieve order/customer context;
- assess policy exception;
- calculate financial impact;
- request human approval if above threshold;
- update ERP.

Classify each step as deterministic node, tool, agent, or human gate.

## Oral checkpoint

1. What is the strongest reason to split one agent into multiple agents?
2. Why is specialization alone not always enough?
3. What should the workflow runtime own?
4. When is a supervisor agent justified?
5. What new risks appear when adding agents?
6. In a reviewer pattern, why separate builder and reviewer?

## PASS

Explain one end-to-end business process and justify every component as single agent, specialist agent, deterministic workflow node, tool, or human step.