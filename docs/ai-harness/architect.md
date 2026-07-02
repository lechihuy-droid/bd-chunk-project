# Solution Architecture — Declarative Super Agent Harness

## 1. Architecture intent

The Declarative Super Agent Harness is an enterprise AI orchestration architecture designed to convert unstructured project knowledge into governed, traceable, and reusable delivery artifacts.

For the BD project context, the Harness supports the transformation of:

```text
RD / QA / Meeting Notes / Legacy Documents
  -> Structured Requirements
  -> RCD
  -> BD Mapping
  -> BD Drafts
  -> Validation Report
  -> Client-ready Excel Delivery Pack
```

The architecture is based on one core principle:

```text
Separate what the system does from how the runtime executes it.
```

This means workflow, agents, skills, policies, and evaluation rules are not hardcoded. They are defined as declarative assets and interpreted by the Harness Runtime.

---

## 2. Target architecture overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. Experience Layer                                                          │
│    Project Cockpit | Visual Workflow Builder | Skill Library | Review Console│
└──────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. Declarative Configuration Layer                                           │
│    workflow.yaml | agent.yaml | SKILL.md | policy files | eval files         │
└──────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. Intelligent Harness Runtime                                               │
│    Workflow Orchestrator | Agent Runtime | Skill Runtime | Model/Tool Router │
└──────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. Shared Substrate & Knowledge Layer                                        │
│    Shared Sandbox | Blackboard State | Knowledge Base | Traceability Graph   │
└──────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 5. Governance, Validation & Artifact Layer                                   │
│    Human Gates | Validation Engine | Audit & Metrics | Final Artifacts       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer 1 — Experience Layer

The Experience Layer is the workspace used by project teams.

### Main components

| Component | Purpose |
|---|---|
| Project Cockpit | Shows project status, input readiness, artifact progress, risks, and KPIs. |
| Visual Workflow Builder | Allows users to drag/drop agents, skills, human gates, and workflow edges. |
| Skill Library UI | Shows available skills, versions, quality scores, usage history, and test status. |
| Review & Traceability Console | Allows users to inspect AI output, evidence, source references, and approve/reject results. |

### Key design choice

The UI does not directly execute AI logic. It produces declarative configuration files that are executed by the runtime.

```text
Visual Canvas -> Workflow Compiler -> workflow.yaml / agent.yaml / skill references
```

---

## 4. Layer 2 — Declarative Configuration Layer

This layer converts business-level workflow design into machine-readable configuration.

### Configuration assets

| Asset | Role |
|---|---|
| `workflow.md` | Human-readable workflow definition. Describes phases, verification rules, recovery rules, and stopping conditions. |
| `workflow.yaml` | Runtime-readable workflow definition. Defines nodes, edges, conditions, inputs, outputs, and human gates. |
| `agent.yaml` | Defines agent role, goal, context scope, tool permissions, skill access, and termination rule. |
| `SKILL.md` | Defines a reusable skill package with purpose, rules, input/output schemas, examples, tests, and failure modes. |
| `policy.md` | Defines governance rules such as evidence requirement, access control, and human review policy. |
| `eval.yaml` | Defines validation rules such as coverage, consistency, and traceability checks. |

### Example workflow model

```yaml
workflow_id: bd_generation_v1
phases:
  - id: ingest
    agent: rd_parser_agent
    skills:
      - skills/rd_parse/SKILL.md
    output: parsed_requirements.json

  - id: build_rcd
    agent: rcd_builder_agent
    skills:
      - skills/rcd_extract/SKILL.md
      - skills/gap_detection/SKILL.md
    input: parsed_requirements.json
    output: rcd_candidate.json

  - id: human_gate_1
    type: human_review
    reviewer_role: BA
    required_status: approved

  - id: bd_mapping
    agent: bd_mapping_agent
    input: rcd_approved.json
    output: bd_mapping.jsonl

  - id: bd_fanout
    type: parallel
    children:
      - screen_bd_agent
      - api_bd_agent
      - db_bd_agent
      - batch_if_bd_agent

  - id: validation
    agent: consistency_review_agent

  - id: human_gate_2
    type: human_review
    reviewer_role: Architect
    required_status: approved

  - id: export
    agent: excel_export_agent
```

---

## 5. Layer 3 — Intelligent Harness Runtime

This is the execution core of the architecture.

### Runtime responsibilities

```text
1. Read workflow.yaml and related configuration files.
2. Build a stateful execution graph.
3. Execute each phase through the assigned agent.
4. Load only the required skill when needed.
5. Route model calls to GPT, Claude, Gemini, or local models.
6. Execute tools such as Excel parser/writer, DB reader, Git search, or artifact exporter.
7. Create sub-agents for large or parallel tasks.
8. Persist outputs into shared filesystem and blackboard state.
9. Pause at human gates.
10. Run validation and export final artifacts.
```

### Suggested engine

LangGraph is suitable because it maps well to workflow topology:

```text
Visual Node -> LangGraph Node
Visual Edge -> LangGraph Edge
Human Gate -> Interrupt / Approval State
Shared Blackboard -> Graph State
Sub-agent -> Child node or child graph
```

---

## 6. Layer 4 — Shared Substrate & Knowledge Layer

This layer provides controlled shared memory and working space.

### Why this layer matters

Agents should not coordinate by unrestricted free-form chat. That pattern is difficult to audit and can amplify hallucination.

Instead, agents coordinate through:

| Component | Purpose |
|---|---|
| Shared Sandbox | Isolated project filesystem for inputs, intermediate outputs, final artifacts, and logs. |
| Blackboard State | Structured state representing current phase, approved RCD, open issues, validation results, and handoff status. |
| Knowledge Base | Searchable project knowledge, RD chunks, QA notes, design standards, and approved decisions. |
| Traceability Graph | Relationship graph connecting source documents, RCD items, BD sections, validation issues, and final outputs. |

### Coordination model

```text
Agent A writes structured output -> Shared State / Filesystem
Agent B reads approved structured output -> Continues next phase
Validation Agent reads all outputs -> Produces validation report
Human Reviewer approves/rejects -> Runtime continues or retries
```

---

## 7. Layer 5 — Governance, Validation & Artifact Layer

This layer ensures AI output can be used in enterprise delivery.

### Human gates

Typical BD gates:

```text
Gate 1: BA approves RCD before BD generation.
Gate 2: Architect reviews BD direction and consistency.
Gate 3: Client reviewer approves final delivery pack if required.
```

### Validation checks

| Check | Objective |
|---|---|
| Coverage check | Ensure all approved RCD items are addressed in BD artifacts. |
| Consistency check | Detect contradictions between screen, API, DB, batch, and IF designs. |
| Traceability check | Ensure every generated BD item has a source reference. |
| Conflict detection | Detect unresolved decisions, duplicate rules, or incompatible assumptions. |
| Format check | Ensure output conforms to Excel/template requirements. |

### Final artifacts

The system should generate:

- RCD.
- BD mapping file.
- Screen BD.
- API BD.
- DB BD.
- Batch/IF BD.
- Validation report.
- Review comment package.
- Excel delivery pack.
- Audit log.

---

## 8. Sub-agent architecture

For large workflows, the Lead Agent can create specialist sub-agents.

```text
Lead BD Agent
  ├── Screen BD Agent
  ├── API BD Agent
  ├── DB BD Agent
  ├── Batch / IF BD Agent
  └── Consistency Review Agent
```

Each sub-agent receives a child task packet:

```json
{
  "parent_task_id": "bd_generation_001",
  "child_task_id": "screen_bd_agent_001",
  "role": "Screen Basic Design Agent",
  "goal": "Generate screen BD draft from approved RCD and BD mapping.",
  "context_scope": [
    "rcd_approved.json",
    "bd_mapping.jsonl",
    "screen_template.xlsx"
  ],
  "skills": [
    "skills/screen_bd/SKILL.md",
    "skills/traceability_check/SKILL.md"
  ],
  "tools_allowed": [
    "read_file",
    "write_excel",
    "search_kb"
  ],
  "output_contract": {
    "file": "artifacts/screen_bd_draft.xlsx",
    "must_include": [
      "screen_id",
      "screen_name",
      "field_list",
      "validation_rule",
      "source_ref"
    ]
  }
}
```

---

## 9. Core architectural principles

### 1. Declarative over hardcoded

Workflow, agents, skills, policies, and evaluation rules should be defined as version-controlled files.

### 2. Human-gated by design

AI can draft, validate, and propose. Critical requirement and design decisions require human approval.

### 3. Shared substrate over agent chat

Agents coordinate through files, state, and traceability graph instead of unrestricted chat.

### 4. Progressive disclosure

The runtime initially loads only skill metadata. Full `SKILL.md`, schema, examples, and scripts are loaded only when needed.

### 5. Traceability first

Every generated BD item must link back to source requirement, QA item, meeting note, approved decision, or source cell.

### 6. Version-controlled intelligence

Workflow, skill, prompt, policy, and evaluation logic should be treated as software assets.

---

## 10. Architecture summary

```text
Declarative Super Agent Harness
=
Experience Layer
+ Declarative Configuration Layer
+ Intelligent Harness Runtime
+ Shared Substrate & Knowledge Layer
+ Governance / Validation / Artifact Layer
```

For BD delivery:

```text
BD AI Harness
=
RD/RCD/BD workflow
+ reusable skill packages
+ lead-agent and sub-agent orchestration
+ shared blackboard and sandbox
+ human review gates
+ traceability matrix
+ Excel artifact export
```
