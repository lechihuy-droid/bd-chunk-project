# DAY 15 — MCP + A2A + ENTERPRISE INTEGRATION

> Certification: AB-100 — Agentic AI Business Solutions Architect
> Official skills baseline: as of 2026-07-22
> Primary blueprint areas: Design + Deploy AI-powered business solutions

## Goal

Phân biệt rõ integration giữa agent với tool/data và integration giữa agent với agent.

```text
Agent → Tool / Resource
        MCP

Agent → Agent
        A2A
```

## Official objectives mapped

AB-100 audience profile explicitly expects expertise with:
- Model Context Protocol (MCP);
- Agent2Agent (A2A);
- secure/scalable cross-platform AI solutions;
- multi-agent orchestration;
- data and model security boundaries.

## Module 15.1 — MCP mental model

MCP standardizes how AI applications/agents discover and use external capabilities/resources.

Think in terms of:
- tool/resource exposure;
- schemas;
- discovery;
- client/server boundary;
- authentication/authorization;
- error handling;
- auditability.

```text
Agent
  ↓
MCP Client
  ↓
MCP Server
  ├─ Tool A
  ├─ Tool B
  └─ Resource C
```

MCP is not business orchestration by itself.

## Module 15.2 — A2A mental model

A2A addresses agent-to-agent collaboration.

Architecture concerns:
- capability discovery;
- task handoff;
- identity;
- context transfer;
- output contract;
- state isolation;
- trust boundary;
- failure semantics.

```text
Agent A
  ↓ task + contract
Agent B
  ↓ result
Agent A / Workflow
```

## Module 15.3 — MCP vs API

```text
API
= service-specific interface

MCP
= standardized agent/tool integration protocol layer
```

MCP can sit in front of APIs; it does not eliminate APIs.

## Module 15.4 — MCP vs A2A

```text
Need capability execution / resource access?
→ MCP/tool integration

Need another autonomous agent to own a task?
→ A2A/agent collaboration
```

Exam trap: a database/search/tool does not become an agent just because an agent calls it.

## Module 15.5 — Enterprise integration architecture

Consider layers:

```text
User / Business App
      ↓
Agent / Copilot Layer
      ↓
Workflow / Orchestration
      ↓
MCP / APIs / Connectors
      ↓
Systems of Record
```

Examples of systems of record:
- Dynamics 365;
- Dataverse;
- ERP/CRM;
- document repositories;
- third-party line-of-business systems.

## Module 15.6 — Identity and least privilege

Every integration must answer:
- Which identity is acting?
- What data can it read?
- What action can it execute?
- Is user delegation required?
- How is the action audited?

```text
Agent autonomy
≤ permission boundary
```

## Module 15.7 — Context minimization

Do not transfer all context across every boundary.

Send only:
- task-specific data;
- required source references;
- approved metadata;
- contract-defined outputs.

Benefits:
- lower leakage risk;
- lower token/cost footprint;
- simpler audit;
- better isolation.

## Scenario drill

A customer-service agent needs to:
1. search policy documents;
2. fetch CRM account information;
3. ask a specialist billing agent to analyze disputed charges;
4. create a case update after human approval.

Identify:
- which interactions are tools/MCP;
- which interaction is A2A;
- where human approval belongs;
- which identity/permission should be used.

## Oral checkpoint

1. MCP solves what class of problem?
2. A2A solves what class of problem?
3. Why does MCP not replace APIs?
4. When should a capability stay a tool instead of becoming an agent?
5. What data should be transferred during an A2A handoff?
6. Why must agent autonomy remain inside permission boundaries?

## PASS

Draw/explain one enterprise agent architecture containing at least one system of record, one tool/MCP integration, one agent-to-agent handoff, and one security boundary.