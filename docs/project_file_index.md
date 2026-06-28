# BD Chunk Project — Classified File Index and Synthesis

> Purpose: gom các file đã push, phân loại lại, và tổng hợp thành các knowledge items phù hợp để tiếp tục triển khai repo.  
> Audience: PM/BA/Architect/Dev/AI Engineer working on BD Chunk Project.  
> Status: living index; update when new methodology, workflow, registry, ontology, or implementation files are added.

---

## 1. Executive summary

Repo hiện đang có nhiều tài liệu phương pháp luận và registry rời nhau. Nhóm lại thì project đang xoay quanh 8 knowledge items chính:

```text
1. Project Vision & Scope
2. Core Methodology
3. Chunking & Traceability
4. Workflow / Runner / Agent / Tool Architecture
5. Agent & Tool Governance
6. Language & Naming Policy
7. Agent / Skill / Tool Factory
8. Implementation Roadmap
```

Câu chốt:

```text
Raw project sources
→ deterministic extraction
→ traceable chunks
→ ontology-labeled RKB
→ human-gated RKB-ready items
→ governed BD support
```

Project này không phải chatbot RAG. Nó là một AI engineering pipeline có kiểm soát.

---

## 2. File inventory by category

### 2.1 Entry point

| File | Category | Role |
|---|---|---|
| `README.md` | Entry point | Giới thiệu repo, project scope, high-level architecture |
| `docs/project_file_index.md` | Entry point / index | File hiện tại; gom và phân loại tất cả tài liệu đã push |

---

### 2.2 Core methodology

| File | Category | Role |
|---|---|---|
| `docs/methodology.md` | Core methodology | Tài liệu phương pháp luận tổng hợp chính: raw input → RKB → BD support |
| `docs/methodology_addendum.md` | Core methodology addendum | Bổ sung hướng executable workflow contract, MVP, schema, metrics, implementation order |
| `docs/chunking_strategy.md` | Chunking methodology | Chiến lược parse/chunk/normalize/source-unit/RKB-ready gate |

Summary:

```text
methodology.md = tư tưởng tổng thể
methodology_addendum.md = chuyển methodology thành executable workflow
chunking_strategy.md = chi tiết raw → source unit → chunk → RKB candidate
```

---

### 2.3 Workflow / Runner / Agent / Tool architecture

| File | Category | Role |
|---|---|---|
| `docs/workflow_agent_design.md` | Workflow architecture | Thiết kế workflow nhiều agent/tool: problem → methodology → architecture → implementation |
| `docs/agent_tool_contract_methodology.md` | Agent/tool contract | Gom phương pháp luận, define mẫu agent/tool, matrix, runner flow, workflow 1 runner/2 agent/6 tool |
| `docs/agent_design.md` | Agent design | Khái niệm agent card, role/mission/tool permission/prompt timing/handoff |

Summary:

```text
workflow_agent_design.md = thiết kế workflow tổng quát
agent_tool_contract_methodology.md = contract cụ thể cho agent/tool/matrix/runner
agent_design.md = cách định nghĩa agent và prompt/tool boundary
```

---

### 2.4 Language and naming policy

| File | Category | Role |
|---|---|---|
| `docs/language_policy.md` | Language policy | Quy định English/ASCII, Japanese, Vietnamese, Vietnamese no-diacritic |

Summary:

```text
English/ASCII = control language for ID/enum/schema/tool
Japanese = business language for source/requirement/BD output
Vietnamese = creator support note
Vietnamese no-diacritic = non-authoritative quick note only
```

Naming rules are currently discussed in conversation and should become a dedicated file later:

```text
Recommended future file: registry/naming_rules.yaml
Recommended future doc: docs/naming_policy.md
```

---

### 2.5 Agent / Skill / Tool Factory

| File | Category | Role |
|---|---|---|
| `docs/agent_skill_factory_strategy.md` | Factory methodology | Chiến lược tạo nhiều agent/skill/tool từ catalog, template, validator, eval |
| `registry/agent_catalog.yaml` | Registry | Danh mục initial agents |
| `registry/skill_catalog.yaml` | Registry | Danh mục initial skills |
| `registry/tool_profiles.yaml` | Registry | Tool permission profile theo role/risk |

Summary:

```text
agent_skill_factory_strategy.md = cách scale agent/skill/tool
agent_catalog.yaml = agents hiện có / dự kiến
skill_catalog.yaml = reusable skills
tool_profiles.yaml = permission/risk profile
```

---

## 3. Recommended knowledge-item structure

Các file hiện có nên được hiểu thành 8 item quản trị dưới đây.

---

## Item 1 — Project Vision & Scope

### Purpose

Định nghĩa project đang giải quyết vấn đề gì và MVP là gì.

### Key idea

```text
Use AI to support Basic Design, but only through traceable, validated, governed RKB.
```

### Source files

```text
README.md
docs/methodology.md
docs/methodology_addendum.md
```

### Core decisions

```text
- Không generate BD trực tiếp từ raw documents.
- MVP đầu tiên là Excel QA/RD → RKB-ready items.
- BD generation là workflow sau, không phải workflow đầu tiên.
- Quality bar: Excel-derived chunks phải trace về workbook/sheet/range.
```

---

## Item 2 — Core Methodology

### Purpose

Định nghĩa phương pháp luận tổng thể từ raw input đến governed BD support.

### Source files

```text
docs/methodology.md
docs/methodology_addendum.md
docs/chunking_strategy.md
```

### Methodology stack

```text
Schema-first engineering
+ provenance-aware RAG
+ ontology engineering
+ workflow orchestration
+ human-in-the-loop governance
+ evaluation-driven LLMOps
```

### Canonical flow

```text
Raw Input
→ File Registry
→ Source Units
→ Traceable Chunks
→ Normalized Requirement Candidates
→ Ontology-Labeled RKB Candidates
→ RKB Ready Items
→ BD Mapping / BD Patch later
```

---

## Item 3 — Chunking & Traceability

### Purpose

Đảm bảo mọi dữ liệu dùng cho RKB có provenance rõ.

### Source files

```text
docs/chunking_strategy.md
docs/methodology.md
```

### Key artifacts

```text
file_registry.jsonl
source_units.jsonl
traceable_chunks.jsonl
rkb_candidates.jsonl
rkb_items.jsonl
exceptions.jsonl
```

### Core rules

```text
- Parser deterministic trước, LLM sau.
- Excel provenance lấy bằng parser, không lấy bằng LLM.
- Chunk theo business boundary, không chỉ theo token size.
- Mỗi chunk phải giữ workbook_name, workbook_sha256, sheet_name, range_a1.
- traceability_rate phải = 1.0 trước khi đi tiếp.
```

---

## Item 4 — Workflow / Runner / Agent / Tool Architecture

### Purpose

Định nghĩa cách workflow chạy theo stage, ai điều phối, agent nào gọi tool nào.

### Source files

```text
docs/workflow_agent_design.md
docs/agent_tool_contract_methodology.md
docs/agent_design.md
```

### Core pattern

```text
Runner
→ Agent
→ Tool
→ Artifact
→ Review Gate / Validator
→ Runner
→ Next Agent
```

### Concrete simple flow

```text
Input
→ Runner
→ Agent 1: IngestAgent
→ Tool 1: hash_file
→ Tool 2: parse_excel_range
→ Tool 3: build_traceable_chunks
→ Artifacts A
→ Review Gate A
→ Agent 2: OntologyRkbAgent
→ Tool 4: apply_ontology_rules
→ Tool 5: validate_rkb_items
→ Tool 6: write_outputs
→ Artifacts B
→ Output
```

### Core rule

```text
Workflow first, contract first, tool first, prompt last.
```

---

## Item 5 — Agent & Tool Governance

### Purpose

Đảm bảo agent không vượt quyền và tool không có side effect ngoài kiểm soát.

### Source files

```text
docs/agent_tool_contract_methodology.md
docs/workflow_agent_design.md
registry/tool_profiles.yaml
```

### Governance layers

```text
Agent Card
Tool Card
Agent-Tool Governance Matrix
Artifact Ownership Matrix
Risk / Human Gate Matrix
Runner enforcement
```

### Core rules

```text
- Agent chỉ được gọi tool có trong allowed_tools.
- Tool không trong matrix = forbidden by default.
- Write permission phải explicit.
- Validator pass trước khi artifact thành official.
- Human gate required cho pending/conflict/low confidence/technical inference.
```

### Recommended future files

```text
registry/agent_tool_governance.yaml
registry/artifact_ownership.yaml
registry/human_gate_matrix.yaml
```

---

## Item 6 — Language & Naming Policy

### Purpose

Định nghĩa ngôn ngữ nào dùng ở layer nào để vừa dễ code, vừa đúng business Japanese, vừa hỗ trợ creator dùng Vietnamese.

### Source files

```text
docs/language_policy.md
```

### Core policy

```text
English/ASCII = control language
Japanese = business language
Vietnamese = creator support language
Vietnamese no-diacritic = non-authoritative quick note only
```

### Recommended field suffixes

```text
*_id       stable machine ID
*_code     stable machine code
*_ja       Japanese official business text
*_en       English support label/description
*_vi       Vietnamese internal note with diacritics
*_vi_ascii Vietnamese internal no-diacritic quick note
```

---

## Item 7 — Agent / Skill / Tool Factory

### Purpose

Scale từ vài agent/tool sang nhiều reusable agents/skills/tools mà vẫn có contract và eval.

### Source files

```text
docs/agent_skill_factory_strategy.md
registry/agent_catalog.yaml
registry/skill_catalog.yaml
registry/tool_profiles.yaml
```

### Core flow

```text
Catalog YAML
→ Templates
→ Generator
→ Validator
→ Eval
→ Deploy
```

### Current registry role

```text
agent_catalog.yaml = danh sách agents
skill_catalog.yaml = reusable skills
tool_profiles.yaml = permission/risk profiles
```

### Recommendation

Không build full factory trước MVP. Chỉ giữ registry/template skeleton, tập trung workflow đầu tiên.

---

## Item 8 — Implementation Roadmap

### Purpose

Biến methodology thành executable implementation.

### Source files

```text
docs/methodology_addendum.md
docs/workflow_agent_design.md
docs/agent_tool_contract_methodology.md
```

### Recommended build order

```text
1. Create workflow.yaml for ingest_excel_to_rkb
2. Create schemas for source_unit, traceable_chunk, rkb_candidate, rkb_item, exception
3. Create agent/tool governance matrices
4. Implement hash_file
5. Implement parse_excel_range with openpyxl
6. Implement validate_source_units
7. Implement build_traceable_chunks
8. Implement Review Gate A
9. Implement apply_ontology_rules
10. Implement validate_rkb_items
11. Implement write_outputs
12. Add evals for happy path and failure path
13. Add run state logging
```

### Build now

```text
- deterministic Excel parser
- provenance validator
- source unit model
- traceable chunk builder
- rule-based ontology labeler
- simple Review Gate A
- run state / logs / metrics
```

### Defer

```text
- full BD generation
- GraphRAG
- complex vector DB
- UI
- large agent factory
- full auto mapping without human gate
```

---

## 4. File-to-item mapping

| File | Item 1 Vision | Item 2 Methodology | Item 3 Chunking | Item 4 Workflow | Item 5 Governance | Item 6 Language | Item 7 Factory | Item 8 Roadmap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `README.md` | Yes | Partial | Partial | Partial | No | No | No | Partial |
| `docs/methodology.md` | Yes | Yes | Yes | Partial | Partial | Partial | Partial | Yes |
| `docs/methodology_addendum.md` | Yes | Yes | Partial | Yes | Yes | No | Partial | Yes |
| `docs/chunking_strategy.md` | No | Yes | Yes | Partial | Partial | No | No | Partial |
| `docs/agent_design.md` | No | Partial | No | Yes | Yes | No | Partial | Partial |
| `docs/agent_skill_factory_strategy.md` | No | Partial | No | Partial | Yes | No | Yes | Partial |
| `docs/workflow_agent_design.md` | Yes | Yes | Partial | Yes | Yes | No | No | Yes |
| `docs/agent_tool_contract_methodology.md` | No | Yes | Partial | Yes | Yes | No | Partial | Yes |
| `docs/language_policy.md` | No | Partial | No | No | Partial | Yes | No | No |
| `registry/agent_catalog.yaml` | No | No | No | Yes | Yes | No | Yes | Partial |
| `registry/skill_catalog.yaml` | No | No | Partial | Partial | Partial | No | Yes | Partial |
| `registry/tool_profiles.yaml` | No | No | No | Partial | Yes | No | Yes | Partial |

---

## 5. Recommended next consolidation

Current docs are useful, but some are overlapping. Suggested next cleanup:

### Keep as canonical

```text
docs/methodology.md
docs/workflow_agent_design.md
docs/agent_tool_contract_methodology.md
docs/language_policy.md
docs/project_file_index.md
```

### Keep as detailed references

```text
docs/chunking_strategy.md
docs/agent_design.md
docs/agent_skill_factory_strategy.md
docs/methodology_addendum.md
```

### Add next

```text
registry/naming_rules.yaml
registry/agent_tool_governance.yaml
registry/artifact_ownership.yaml
registry/human_gate_matrix.yaml
workflows/ingest_excel_to_rkb/workflow.yaml
workflows/ingest_excel_to_rkb/schemas/*.schema.json
workflows/ingest_excel_to_rkb/evals/*.yaml
```

---

## 6. Canonical reading order

For a new AI engineer or developer, read in this order:

```text
1. README.md
2. docs/project_file_index.md
3. docs/methodology.md
4. docs/methodology_addendum.md
5. docs/chunking_strategy.md
6. docs/workflow_agent_design.md
7. docs/agent_tool_contract_methodology.md
8. docs/language_policy.md
9. registry/agent_catalog.yaml
10. registry/skill_catalog.yaml
11. registry/tool_profiles.yaml
```

For implementation, read in this order:

```text
1. docs/agent_tool_contract_methodology.md
2. docs/workflow_agent_design.md
3. docs/chunking_strategy.md
4. docs/language_policy.md
5. registry/tool_profiles.yaml
6. registry/agent_catalog.yaml
7. registry/skill_catalog.yaml
```

---

## 7. Final synthesis

The pushed files can be summarized into one operating model:

```text
BD Chunk Project is a controlled AI engineering pipeline.

It converts Japanese requirement sources into traceable, validated,
ontology-labeled RKB items through deterministic tools, schema-first contracts,
agent/tool permission matrices, review gates, and human approval for risky cases.

Only after RKB is validated should downstream BD mapping or BD generation run.
```

Final rule:

```text
Raw input is not source of truth for generation.
Traceable RKB is the source of truth.
Runner enforces workflow policy.
Agent decides within boundary.
Tool executes with contract.
Validator checks correctness.
Human gate protects official promotion.
```
