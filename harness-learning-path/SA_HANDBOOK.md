# SA Handbook — Agent System Architecture for BD Harness

Version: v0.2  
Purpose: Central knowledge base for the BD Chunk / Super Agent Harness architecture.

> **SA Handbook không phải là nơi lưu mọi kiến thức. Đây là nơi chuẩn hóa kiến trúc đã được chấp nhận của dự án.**

---

# 0. Operating Definition

## 0.1 Mission

SA Handbook là **Single Source of Truth** cho kiến trúc của dự án BD Harness.

Nó không thay thế research note, course note, repo review hay raw learning log. Những nội dung đó nằm ở research/reading layer. SA Handbook chỉ lưu phần tri thức đã được **lọc, chuẩn hóa và chấp nhận** để dùng cho thiết kế hệ thống.

## 0.2 What Belongs Here

SA Handbook chỉ nên lưu:

- Canonical architecture của Harness
- Core concepts đã được định nghĩa rõ
- Architecture principles
- Reusable design patterns
- Framework mapping
- Architecture Decision Records (ADR)
- BD Harness methodology
- Governance rules
- Glossary chuẩn của dự án

## 0.3 What Does Not Belong Here

Không đưa trực tiếp các nội dung sau vào SA Handbook:

- Raw paper summary
- Raw course note
- Repo review dài
- Prompt nháp
- Tool experiment log
- Ý tưởng chưa được kiểm chứng
- Chi tiết implementation tạm thời

Những nội dung trên có thể nằm ở `reading/`, `research/`, hoặc learning log. Chỉ khi đã rút ra pattern, principle hoặc decision thì mới đưa vào handbook.

## 0.4 MVP Structure

SA Handbook MVP chỉ cần giữ 10 nhóm nội dung:

```text
1. Purpose
2. Canonical Architecture
3. Core Concepts
4. Architecture Principles
5. Pattern Library
6. Framework Mapping
7. Architecture Decision Records
8. Glossary
9. References
10. Learning Log
```

## 0.5 Learning-to-Handbook Workflow

Khi đọc một repo, course, paper hoặc framework mới, không copy trực tiếp vào handbook. Luôn đi qua workflow sau:

```text
Research / Course / Repo
  ↓
Extract Pattern
  ↓
Compare with Canonical Architecture
  ↓
Update SA Handbook
  ↓
Create ADR if needed
  ↓
Apply to BD Harness
```

## 0.6 Five Questions Before Updating Handbook

Mỗi lần cập nhật handbook, phải trả lời 5 câu hỏi:

1. Học được pattern gì?
2. Pattern này thuộc chapter nào trong SA Handbook?
3. Có cần tạo ADR mới không?
4. Có thay đổi Canonical Architecture không?
5. Có áp dụng được cho BD Harness ở đâu?

Nếu không trả lời được ít nhất một câu rõ ràng, nội dung đó chưa nên đưa vào handbook.

## 0.7 Design Principles

### Framework Independent

Thiết kế kiến trúc trước, chọn framework sau. LangGraph, Claude Code, OpenAI Agents SDK và Microsoft Agent Framework chỉ là implementation options.

### Artifact First

Tri thức quan trọng và deliverable nên tồn tại dưới dạng artifact có thể review, diff và version bằng Git.

### Traceability First

Mọi output quan trọng phải truy vết được về requirement/source.

### Human Review

Không tự động hóa quyết định thiết kế cuối cùng nếu output là tài liệu BD hoặc artifact có ảnh hưởng đến khách hàng.

### Schema First

Ưu tiên giao tiếp giữa agent bằng schema rõ ràng thay vì prompt tự do.

### Small Context

Mỗi agent chỉ nhận lượng context tối thiểu cần thiết cho task của nó.

---

# 1. Purpose

This handbook defines the canonical architecture for an enterprise-grade agent harness that supports Basic Design (BD) generation, review, traceability, and export.

The handbook is intentionally framework-independent.

Frameworks such as LangGraph, Claude Code, OpenAI Agents SDK, and Microsoft Agent Framework should be treated as implementation options, not as the architecture itself.

---

# 2. Canonical Architecture

```text
Goal
  ↓
Input Intake
  ↓
Planner
  ↓
Execution Plan
  ↓
Orchestrator / Runtime
  ↓
Scheduler / Router
  ↓
Agent Pool
  ↓
Artifact Store + Runtime State + Knowledge Base
  ↓
Review / Validation
  ↓
Deliverables
```

## 2.1 Core Principle

The harness should not send raw requirements directly to one large LLM call.

Instead, it should:

```text
Raw Input
  ↓
Planner creates Chunking Plan
  ↓
Chunking Agent creates Structured Chunks
  ↓
Planner creates Execution Plan
  ↓
Specialized Agents create artifacts
  ↓
Reviewer validates traceability and quality
```

---

# 3. Planner

## Definition

Planner converts a high-level goal into an execution plan.

## Responsibilities

- Goal decomposition
- Task generation
- Dependency analysis
- Parallelization strategy
- Context partitioning strategy
- Agent/model/tool matching
- Review gate definition
- Re-planning when inputs change or tasks fail

## Planner Output Example

```yaml
goal: Generate Basic Design
execution_plan:
  - id: chunk_rd
    agent: chunking_agent
    depends_on: []
  - id: build_screen_specs
    agent: screen_agent
    depends_on: [chunk_rd]
  - id: build_api_specs
    agent: api_agent
    depends_on: [chunk_rd]
  - id: build_db_specs
    agent: db_agent
    depends_on: [chunk_rd]
  - id: validate_traceability
    agent: review_agent
    depends_on: [build_screen_specs, build_api_specs, build_db_specs]
```

## Design Rule

Planner decides what should happen. It should not directly execute every task.

---

# 4. Orchestrator

## Definition

Orchestrator executes the plan produced by the Planner.

## Responsibilities

- Dispatch tasks
- Route work to agents
- Track task status
- Manage retries
- Manage timeout
- Manage checkpoints
- Resume interrupted workflows
- Trigger human approval gates
- Merge agent outputs

## Design Rule

Planner thinks. Orchestrator runs.

---

# 5. Scheduler / Router

## Definition

Scheduler decides when and where a task should run.

Router decides which agent, model, tool, or workflow branch should receive a task.

## Routing Criteria

- Artifact type: Screen, API, DB, Batch, IF, Report
- Required tool: Excel parser, Git, browser, DB, test runner
- Required model capability: reasoning, coding, translation, extraction
- Cost budget
- Context size
- Priority
- Human review policy

---

# 6. State

## Definition

State is the current condition of the workflow.

State includes:

- Input metadata
- Plan
- Current task status
- Intermediate outputs
- Agent status
- Runtime metadata
- Validation results
- References to artifacts
- Deliverables

## Important Distinction

```text
Deliverable ∈ State
State ≠ Deliverable
```

Deliverables are part of state, but state is broader.

## Example

```yaml
goal: Generate BD
plan_status: running
chunks_status: complete
screen_specs_status: running
api_specs_status: pending
review_status: pending
artifacts:
  - specs/screen/login.md
  - specs/api/login_api.md
runtime:
  retry_count: 1
  current_agent: screen_agent
```

---

# 7. Artifact Store

## Definition

Artifact Store holds the working products created by agents.

Examples:

```text
/specs/screen/login.md
/specs/api/login_api.md
/specs/db/user_table.md
/chunks/rd_chunks.jsonl
/reviews/traceability_report.md
/deliverables/basic_design.xlsx
```

## Why Artifact-Centric Design Matters

Artifacts are easier to:

- Version with Git
- Review by humans
- Diff between versions
- Reuse across agents
- Export into client deliverables
- Link to source requirements

## Design Rule

Use runtime state for coordination. Use artifacts for durable knowledge and work products.

---

# 8. Workspace

## Definition

Workspace is the execution environment where agents read and write artifacts.

For coding agents, the workspace is usually a Git repository.

For BD Harness, the workspace should include:

```text
workspace/
├── input/
├── chunks/
├── specs/
├── mappings/
├── reviews/
├── exports/
└── logs/
```

## Git Role

Git can be used as:

- Version control
- Diff layer
- Checkpoint mechanism
- Human review surface
- Rollback mechanism

---

# 9. Memory vs Knowledge Base

## Memory

Memory is runtime or long-term information used to improve future agent behavior.

Examples:

- User preferences
- Project conventions
- Past decisions
- Reusable patterns

## Knowledge Base

Knowledge Base is curated, reliable, project-level knowledge.

Examples:

- RD facts
- QA clarifications
- Business glossary
- Ontology
- Traceability map
- Architecture decisions

## Design Rule

For BD work, prefer curated KB over vague conversational memory.

---

# 10. Skill Library

## Definition

A skill is a reusable capability that combines instructions, procedures, schemas, and tool usage patterns.

## Initial BD Harness Skill Library

```text
Requirement Chunking Skill
RD Fact Extraction Skill
QA Classification Skill
Pending Decision Detection Skill
Screen Design Skill
API Design Skill
DB Design Skill
Batch Design Skill
Interface Design Skill
Traceability Review Skill
Japanese BD Writing Skill
Excel Export Skill
```

## Skill vs Agent vs Tool

| Concept | Meaning |
|---|---|
| Skill | Reusable procedure or capability |
| Agent | Actor that performs a task using model + tools + skills |
| Tool | External function or system the agent can call |

---

# 11. Tool Registry

## Definition

Tool Registry is the controlled list of external functions available to agents.

## Example Tools

```text
Excel parser
Markdown writer
Git operations
Browser automation
DB schema reader
Mermaid diagram generator
Validation checker
Exporter
```

## Design Rule

Agents should not have unlimited tool access. Tool access should be scoped by task role.

---

# 12. Agent Pool

## Initial Agent Types for BD Harness

```text
Input Intake Agent
Chunking Agent
Classification Agent
Ontology Agent
Planner Agent
Screen Design Agent
API Design Agent
DB Design Agent
Batch Design Agent
Review Agent
Traceability Agent
Export Agent
```

## Agent Design Rule

Each agent should have:

- Clear responsibility
- Bounded context
- Tool permissions
- Input schema
- Output schema
- Review policy

---

# 13. Human Review

## Why Human Review Is Required

BD output is a client-facing engineering artifact. The harness must not fully automate final decisions without human review.

## Review Gates

```text
After chunking
After classification
After open question detection
Before BD generation
After BD generation
Before final export
```

## Review Criteria

- Traceability to source
- No unsupported assumptions
- Pending decisions flagged
- Japanese business writing quality
- Consistency across Screen/API/DB/Batch specs
- Completeness against requirement scope

---

# 14. Traceability

## Goal

Every generated BD artifact should be traceable back to source material.

## Example Source Reference

```text
RD.xlsx#要件一覧!B12:H18
QA票.xlsx#QA!C21:F25
meeting_notes.md#2026-07-05-section-3
```

## Traceability Chain

```text
Source Document
  ↓
Chunk
  ↓
Requirement Fact
  ↓
Artifact Spec
  ↓
BD Deliverable Section
  ↓
Review Evidence
```

---

# 15. Framework Mapping

| Concept | LangGraph | Claude Code | OpenAI Agents SDK | Microsoft Agent Framework |
|---|---|---|---|---|
| State | Typed state object | Workspace/files/Git diff/session | Context/session/thread items/external DB | Session/workflow state |
| Node | Graph node | Tool call/file edit/subtask | Agent/tool/handoff | Agent/workflow step |
| Planner | Custom node/subgraph | Planning mode/task decomposition | Agent with structured output | Agent/workflow planning logic |
| Orchestrator | StateGraph runtime | CLI loop + tool runtime | Runner/handoff control | Workflow orchestration |
| Artifact | State field or file | Repository files | Tool output/file/external store | Files/resources/business artifacts |
| Checkpoint | Checkpointer | Git commit/diff/workspace | Session persistence/external storage | Workflow/session persistence |
| Human Review | Interrupt / human-in-loop | Git diff / approval / PR | Guardrail / approval tool | Approval workflow |
| Tool | LangChain tool | CLI/tool/MCP/hook | Function tool / hosted tool | Connector/action/tool |
| Skill | Custom prompt/procedure | Skill/custom command | Agent instruction/tool package | Reusable agent capability |

---

# 16. Architecture Decisions

## ADR-001 — Use Canonical Architecture First

Decision: Define Planner, Orchestrator, State, Artifact Store, Skill Library, Tool Registry, and Agent Pool independently from any framework.

Reason: Prevent framework lock-in and allow mapping to LangGraph, Claude Code, OpenAI Agents SDK, or Microsoft stack later.

## ADR-002 — Use Hybrid State + Artifact Design

Decision: Runtime state manages coordination; durable work products are stored as artifacts.

Reason: BD work requires traceability, review, versioning, and export. Files are better for durable artifacts; state is better for execution control.

## ADR-003 — Treat SA Handbook as Project KB

Decision: This handbook is the central KB for architecture concepts, decisions, framework mappings, and BD Harness design rules.

Reason: Avoid fragmented learning notes and create a reusable design base for future implementation.

---

# 17. Next Updates

Add these sections after Week 01:

- Planner input/output schema
- Chunking plan schema
- Execution plan schema
- Runtime state schema
- Artifact naming convention
- BD traceability schema
- Agent permission model
- Human review checklist
- Evaluation metrics
- Cost/token tracking model
