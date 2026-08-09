# FRONTIER / TITAN — 21-DAY CERTIFICATION LEARNING PATH

## Objective

Hoàn thành learning path nền tảng hướng tới Microsoft **Frontier Transformation Engineer / Titan learning journey** theo thứ tự:

```text
AI-103
Azure AI Apps and Agents Developer Associate
        ↓
GH-300
GitHub Copilot
        ↓
Integrated Hands-on
AI Agent + Agentic Development
        ↓
AB-100
Agentic AI Business Solutions Architect
        ↓
Titan / Project Ready / Frontier
```

---

## Learning Strategy

Không chia đều thời gian cho ba certificate.

```text
AI-103      = Technical foundation
GH-300      = Agentic development workflow
AB-100      = Architecture + enterprise integration
```

### Phân bổ 21 ngày

| Stage | Thời gian |
|---|---:|
| AI-103 Concept Rush | 3 ngày |
| GH-300 Concept Rush | 3 ngày |
| AI-103 + GH-300 Hands-on | 4 buổi |
| AB-100 Intensive | 11 ngày |
| **Tổng** | **21 ngày** |

---

## Nguyên tắc

> AI-103 và GH-300 học nhanh để lấy vocabulary + mental model + exam readiness.  
> AB-100 là phần cần đào sâu vì đây là tầng Solution Architecture của Frontier journey.

---

# PHASE 1 — AI-103 RUSH

## DAY 1 — AI Foundations + Foundry + Agent Anatomy

### Objective

Hiểu kiến trúc tổng thể trước khi đi vào Microsoft implementation.

## Core Mental Model

```text
Model
 ↓
Tool Calling
 ↓
Agent
 ↓
Workflow
 ↓
Multi-Agent
 ↓
Agent Runtime / Platform
```

## Phân biệt cốt lõi

- LLM vs Agent
- Agent vs Tool
- Agent vs Workflow Node
- State vs Memory
- Context vs Knowledge
- API vs MCP
- Agent Framework vs Agent Service
- Harness vs Foundry

## Microsoft Foundry

```text
Microsoft Foundry
├── Project
├── Model
├── Model Deployment
├── Endpoint
├── SDK
├── Knowledge
├── Tools
├── Agent Service
└── Evaluation / Monitoring
```

### Critical distinction

```text
Harness
= architectural/runtime pattern surrounding agents

Foundry
= Microsoft's platform for building and operating AI solutions
```

## Agent Anatomy

```text
Agent
├── Role
├── Goal
├── Model
├── Instructions
├── Input Contract
├── Output Contract
├── Tools
├── Knowledge
├── State / Memory
├── Guardrails
└── Evaluation
```

## Day 1 checkpoint

Giải thích được:

1. Model khác Agent thế nào?
2. Tool khác Agent thế nào?
3. Workflow Node có bắt buộc là Agent không?
4. State khác Memory thế nào?
5. Foundry khác Harness thế nào?
6. Agent Framework khác Agent Service thế nào?

---

# DAY 2 — Generative AI + RAG + Tools + Agent

## Generative AI

- model selection
- prompts/instructions
- structured output
- grounding
- context management
- evaluation

## Contracts

```text
Agent Output
     ↓
Output Contract
     ↓
Structural Validation
     ↓
Domain Validation
```

### Phân biệt

```text
Structural validation
= đúng schema/type/required fields

Semantic validation
= đúng theo business/source thực tế
```

## RAG

```text
Source
 ↓
Ingest
 ↓
Chunk
 ↓
Index
 ↓
Retrieve
 ↓
Context
 ↓
Model / Agent
```

## Tools

```text
Agent
 ↓
Tool Selection
 ↓
Tool Call
 ↓
External Action/Data
 ↓
Tool Result
 ↓
Agent Reasoning
```

## MCP

```text
Agent
 ↓
MCP Client
 ↓
MCP Server
 ↓
Tools / Resources
```

## Day 2 checkpoint

- RAG khác Memory
- Tool khác Knowledge
- API khác MCP
- Contract khác Validator

---

# DAY 3 — AI-103 EXAM BREADTH

## Multi-Agent

```text
Agent A
   ↓
Agent B
```

```text
       Supervisor
      /     |     \
Agent A  Agent B  Agent C
```

## Responsible AI / Security

- identity
- RBAC
- managed identity
- secret handling
- permissions
- content safety
- grounding
- guardrails
- monitoring

## Computer Vision / Multimodal

- image understanding
- multimodal models
- image/video inputs
- content understanding

## Language / Speech

- entity extraction
- sentiment
- summarization
- translation
- speech-to-text
- text-to-speech

## Information Extraction

```text
Document
 ↓
OCR / Layout
 ↓
Structured Extraction
 ↓
Search / Retrieval
 ↓
Agent Reasoning
```

## AI-103 Gate

```text
Foundry
 ↓
Model
 ↓
Agent
 ↓
Tools + Knowledge
 ↓
RAG / Memory
 ↓
Workflow / Multi-Agent
 ↓
Security / Evaluation
 ↓
Production
```

---

# PHASE 2 — GH-300 CONCEPT RUSH

## DAY 4 — GitHub Copilot Fundamentals

```text
Developer
 ↓
GitHub Copilot
 ↓
Code / Explanation / Test / Review
```

## Responsible Use

- hallucination
- insecure code
- IP considerations
- validation
- human accountability

## DAY 5 — Prompt + Context Engineering

### Prompt

```text
Goal
+
Context
+
Constraints
+
Expected Output
```

### Context Engineering

```text
Prompt = instruction
Context = information model uses to execute instruction
```

## Copilot Agent Mode

```text
Task
 ↓
Plan
 ↓
Inspect repository
 ↓
Modify files
 ↓
Run tools/tests
 ↓
Evaluate
 ↓
Iterate
```

## DAY 6 — GitHub Agentic Development

- Agent Mode
- Agent Sessions
- Sub-agents
- MCP
- repo instructions
- testing
- governance

## Architecture

```text
Developer
    ↓
Coding Agent
    ↓
Repository
    ├── Instructions
    ├── Code
    ├── Tests
    └── MCP integrations
```

## GH-300 Gate

- Copilot Chat vs Agent Mode
- Prompt vs Context
- MCP usage
- Sub-agent role
- Human review necessity

---

# PHASE 3 — FOUR INTEGRATED HANDS-ON SESSIONS

## SESSION 1 — DESIGN ONE AGENT

```text
RD Parser Agent
```

```text
Role
Goal
Input
Output
Tools
Knowledge
State
Memory
Guardrails
Evaluation
```

## SESSION 2 — TOOL + RAG + MCP

```text
Parser Agent
     │
     ├── read_document
     ├── search_requirement
     └── retrieve_context
```

```text
Agent
 ↓
MCP
 ↓
Tool ecosystem
```

## SESSION 3 — WORKFLOW + MULTI-AGENT

```text
RD
 ↓
Parser
 ↓
Validator
 ↓
Builder
 ↓
Reviewer
```

## SESSION 4 — COPILOT + AGENT WORKFLOW

```text
Architect
 ↓
Define Agent Contract
 ↓
GitHub Copilot
 ↓
Generate implementation
 ↓
Tests
 ↓
Review
 ↓
Evaluation
 ↓
Deploy
```

---

# PHASE 4 — AB-100 INTENSIVE

## Mental shift

```text
AI-103 → Build Agent
GH-300 → Engineer with AI
AB-100 → Architect enterprise AI systems
```

## DAY 11 — BUSINESS → AI OPPORTUNITY

```text
Business Problem
 ↓
Process
 ↓
Decision Points
 ↓
AI Opportunity
 ↓
Agent Opportunity
```

## DAY 12 — BUILD vs BUY vs EXTEND

- M365 Copilot
- Copilot Studio
- Foundry
- Power Platform
- Dynamics 365

## DAY 13 — PLATFORM LANDSCAPE

- M365 Copilot
- Copilot Studio
- Foundry
- Agent Service
- Power Platform

## DAY 14 — SINGLE vs MULTI-AGENT

```text
Supervisor
 ├── Specialist A
 ├── Specialist B
 └── Specialist C
```

## DAY 15 — MCP + A2A

```text
Agent → Tool = MCP
Agent → Agent = A2A
```

## DAY 16 — KNOWLEDGE ARCHITECTURE

```text
Enterprise Data
 ↓
Knowledge Layer
 ↓
Retrieval
 ↓
Agent
```

## DAY 17 — SECURITY

- identity
- permissions
- secrets
- prompt injection
- audit

## DAY 18 — GOVERNANCE

```text
Agent → Portfolio → Enterprise Governance
```

## DAY 19 — ALM

```text
DEV → TEST → EVAL → PROD → MONITOR
```

## DAY 20 — MONITORING + ROI

- latency
- quality
- cost
- adoption
- ROI

## DAY 21 — FINAL ARCHITECTURE REVIEW

```text
Business → Assessment → Platform → Agent Design → Knowledge → MCP → Security → Governance → ROI
```

---

# CERTIFICATION TARGET

## Checkpoint 1

- AI-103 exam

## Checkpoint 2

- GH-300 exam

## Checkpoint 3

- AB-100 exam

---

# FINAL OUTCOME

```text
Build Agent
+
Engineer with Agent
+
Architect Enterprise AI Systems
```
