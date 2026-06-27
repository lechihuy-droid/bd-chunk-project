# Methodology Addendum — From Methodology to Executable Workflow

> This addendum supplements `docs/methodology.md`.  
> Purpose: convert the methodology into executable workflow contracts, implementation boundaries, MVP scope, metrics, and governance rules.  
> Audience: AI architect, BD creator, implementation engineer, project manager.

---

## 1. Why this addendum exists

`docs/methodology.md` defines the complete conceptual model:

```text
Raw Input
→ Source Units
→ Traceable Chunks
→ Ontology
→ RKB
→ Index
→ BD Mapping
```

This addendum defines how to turn that methodology into something that can be:

```text
- executed
- tested
- audited
- measured
- deployed
- improved safely
```

The main shift:

```text
Documentation methodology
→ Executable contracts
→ Validated workflow
→ Measurable business outcome
```

---

## 2. Critical design correction

Do not continue adding methodology only.

The next step is to create executable workflow contracts.

Correct next layer:

```text
docs/methodology.md
→ workflows/ingest_excel_to_rkb/workflow.yaml
→ schemas/*.schema.json
→ evals/*.yaml
→ src implementation
```

Wrong next layer:

```text
more prompts
more abstract agents
more diagrams
more generic factory design
```

The project should now move from explanation to contract.

---

## 3. Target MVP boundary

The first MVP must be narrow.

Recommended MVP:

```text
Input:
  QA票 Excel for one business domain

Transformation:
  Excel → Source Units → Traceable Chunks → Ontology Labels → RKB Items

Output:
  RKB-ready items + exception queue + review summary

Optional Phase 2 output:
  One BD section draft: 業務ルール / 例外処理
```

Example MVP domain:

```text
Domain: 売掛金消込
Domain code: KESHI
Input: qa_keshikomi.xlsx / QA票 / B12:E30
Output: RKB items for business rules, exception rules, validation rules, and state transitions
```

Do not include in MVP:

```text
- all RD/QA/Legacy sources
- full BD document generation
- GraphRAG
- full vector DB
- 50 agents
- full skill factory automation
- complex UI
```

MVP rule:

```text
Prove one Excel QA → RKB workflow before expanding to multi-source BD generation.
```

---

## 4. Executable workflow folder

Create the first workflow as a product slice:

```text
workflows/
  ingest_excel_to_rkb/
    workflow.yaml
    README.md

    schemas/
      input.schema.json
      file_registry.schema.json
      source_unit.schema.json
      traceable_chunk.schema.json
      rkb_candidate.schema.json
      rkb_item.schema.json
      exception.schema.json
      output.schema.json

    examples/
      request.example.json
      file_registry.example.jsonl
      source_units.example.jsonl
      traceable_chunks.example.jsonl
      rkb_candidates.example.jsonl
      rkb_items.example.jsonl
      exceptions.example.jsonl
      summary.example.md

    evals/
      happy_path.yaml
      missing_sheet_name.yaml
      missing_range_a1.yaml
      missing_provenance_blocked.yaml
      pending_decision_blocked.yaml
      ontology_label_controlled.yaml
      multi_behavior_needs_split.yaml

    agents/
      file_registry.agent.yaml
      excel_source_parser.agent.yaml
      traceability_validator.agent.yaml
      chunk_builder.agent.yaml
      ontology_labeler.agent.yaml
      rkb_reviewer.agent.yaml

    prompts/
      file_registry.md
      excel_source_parser.md
      traceability_validator.md
      chunk_builder.md
      ontology_labeler.md
      rkb_reviewer.md
```

This folder is the first executable contract for the project.

---

## 5. Workflow contract

`workflow.yaml` must be the source of truth for execution order.

Minimum structure:

```yaml
id: ingest_excel_to_rkb
name: Ingest Excel to RKB
version: 0.1.0
owner: bd-chunk-project

purpose: >
  Convert Excel QA/RD sheets into traceable source units,
  traceable chunks, ontology-labeled RKB candidates, and RKB-ready items.

mvp_scope:
  input_source_type: excel
  source_kind:
    - QA
    - RD
  output_until: RKB_READY
  bd_generation: false

input_contract:
  required:
    - file_path
    - source_kind
    - sheet_name
    - range_a1
    - domain_code
  optional:
    - module_name
    - chunking_mode
    - header_rows

output_contract:
  files:
    - data/index/file_registry.jsonl
    - data/outputs/source_units.jsonl
    - data/outputs/traceable_chunks.jsonl
    - data/outputs/rkb_candidates.jsonl
    - data/outputs/rkb_items.jsonl
    - data/outputs/exceptions.jsonl
  metrics:
    - traceability_rate
    - source_unit_count
    - chunk_count
    - rkb_candidate_count
    - rkb_ready_count
    - needs_review_count
    - exception_count

stages:
  - id: register_file
    agent: FileRegistryAgent
    tools:
      - hash_file
      - detect_file_type
      - register_file
    outputs:
      - file_registry_record

  - id: parse_excel
    agent: ExcelSourceParserAgent
    tools:
      - parse_excel_range
      - validate_source_units
    inputs:
      - file_registry_record
      - sheet_name
      - range_a1
    outputs:
      - source_units

  - id: build_chunks
    agent: ChunkBuilderAgent
    tools:
      - build_traceable_chunks
      - detect_multi_behavior
      - detect_ambiguity_terms
    outputs:
      - traceable_chunks

  - id: label_ontology
    agent: OntologyLabelerAgent
    tools:
      - load_ontology_yaml
      - apply_ontology_rules
      - validate_ontology_labels
    outputs:
      - rkb_candidates

  - id: review_rkb
    agent: RKBReviewerAgent
    human_gate: true
    outputs:
      - rkb_items

stop_conditions:
  - missing_file_path
  - missing_sheet_name
  - missing_range_a1
  - traceability_rate_below_1
  - invalid_ontology_label
  - unresolved_conflict

guardrails:
  forbidden_inference:
    - file_sha256
    - workbook_sha256
    - sheet_name
    - range_a1
    - source_granularity
    - chunk_id
    - rkb_id
  if_missing_required_input: NEEDS_INPUT
  if_validation_failed: STOP_AND_WRITE_EXCEPTION
```

---

## 6. Schema-first implementation

Before implementing tools, define schemas.

Required schemas:

```text
schemas/file_registry.schema.json
schemas/source_unit.schema.json
schemas/traceable_chunk.schema.json
schemas/rkb_candidate.schema.json
schemas/rkb_item.schema.json
schemas/exception.schema.json
```

Reason:

```text
Schema is the contract between agent, tool, validator, RKB, and BD mapper.
```

Without schemas, each tool may output a different shape, causing downstream instability.

Schema rule:

```text
No schema = no implementation.
No validation = no RKB promotion.
```

---

## 7. Minimum schema requirements

### 7.1 Source unit required fields

```text
unit_id
file_id
source_type
raw_text
source.workbook_name
source.workbook_sha256
source.sheet_name
source.range_a1
source.source_granularity
status
```

For Excel, these fields are mandatory:

```text
workbook_name
workbook_sha256
sheet_name
range_a1
source_granularity
```

### 7.2 Traceable chunk required fields

```text
chunk_id
source_unit_ids
raw_text
normalized_text_ja
content_hash
source
status
warnings
review_required
```

### 7.3 RKB item required fields

```text
rkb_id
chunk_id
artifact_type
raw_text_ja
normalized_text_ja
requirement_statement_ja_or_artifact_ref
ontology
source
status
confidence
conflict_flag
review_required
lifecycle_status
```

### 7.4 Exception required fields

```text
exception_id
stage
reason
source_ref_or_input_ref
recommended_action
blocking
created_at
```

---

## 8. Run state and audit trail

Workflow state must be stored outside the conversation.

Recommended structure:

```text
data/runs/
  run-YYYYMMDD-HHMMSS-<workflow_id>/
    run.yaml
    inputs.json
    stage_status.json
    metrics.json
    outputs/
      file_registry.jsonl
      source_units.jsonl
      traceable_chunks.jsonl
      rkb_candidates.jsonl
      rkb_items.jsonl
      exceptions.jsonl
    logs/
      agent_steps.jsonl
      tool_calls.jsonl
      validation_results.jsonl
      human_decisions.jsonl
```

Example `run.yaml`:

```yaml
run_id: run-20260628-001
workflow_id: ingest_excel_to_rkb
status: NEEDS_REVIEW
started_at: 2026-06-28T10:00:00+09:00

input:
  file_path: data/raw/qa_keshikomi.xlsx
  source_kind: QA
  sheet_name: QA票
  range_a1: B12:E30
  domain_code: KESHI

stage_status:
  register_file: completed
  parse_excel: completed
  validate_source_units: completed
  build_chunks: completed
  label_ontology: completed
  review_rkb: needs_human_review

metrics:
  source_unit_count: 19
  valid_source_unit_count: 17
  invalid_source_unit_count: 2
  traceability_rate: 1.0
  rkb_ready_count: 13
  needs_review_count: 4
```

Audit rule:

```text
Every agent decision, tool call, validation result, and human approval must be reproducible from run logs.
```

---

## 9. Human gates

Human review should be risk-based, not universal.

Required human gates:

```text
1. Missing input
2. Missing provenance
3. Ambiguous requirement
4. Multiple behaviors in one chunk
5. PENDING_DECISION
6. TECHNICAL_INFERENCE
7. Conflict between sources
8. Low confidence ontology label
9. Before RKB_READY promotion
10. Before BD mapping or BD generation
```

Workflow config example:

```yaml
human_gates:
  - id: review_missing_input
    trigger:
      - missing_sheet_name
      - missing_range_a1
    action: request_user_input

  - id: review_rkb_candidates
    trigger:
      - ambiguity_flags_not_empty
      - conflict_flag_true
      - source_label_pending_decision
      - confidence_low
    action: require_bd_creator_decision

  - id: approve_rkb_ready
    trigger:
      - before_rkb_ready_promotion
    action: require_approval
```

Important:

```text
Human gates protect requirement correctness.
They should not be bypassed for speed.
```

---

## 10. Labeling method transparency

Ontology labeling must record how each label was produced.

Recommended fields:

```json
{
  "labeling_method": "rule_based | llm_suggested | human_approved",
  "labeling_confidence": "high | medium | low",
  "labeling_reason": "Matched keyword 不一致 and requirement_type rule EXCEPTION_RULE.",
  "review_required": false
}
```

Rules:

```text
Rule-based high confidence labels can proceed if validation passes.
LLM-suggested labels require confidence and validation.
Low-confidence labels require human review.
Human-approved labels must be logged in human_decisions.jsonl.
```

This prevents hidden semantic drift.

---

## 11. ID and naming governance

Add a naming registry, not only naming rules.

Recommended file:

```text
registry/naming_rules.yaml
```

Recommended runtime registry:

```text
data/index/id_registry.jsonl
```

Purpose:

```text
- prevent duplicate IDs
- keep stable RKB IDs
- track superseded versions
- trace generated IDs back to source
```

ID stability rule:

```text
SRC ID identifies parsed source unit.
CHK ID may be hash-based and deterministic.
RKB ID should be stable business ID.
MAP ID identifies relationship between RKB item and BD frame.
```

Example:

```json
{
  "id": "RKB-KESHI-EXC-002",
  "id_type": "RKB",
  "domain_code": "KESHI",
  "created_from_chunk_id": "CHK-KESHI-QA-7F91A2",
  "version": 1,
  "status": "active"
}
```

---

## 12. Metrics and success criteria

The MVP must be measured.

### 12.1 Technical metrics

```text
traceability_rate
source_unit_count
valid_source_unit_count
invalid_source_unit_count
chunk_count
multi_behavior_count
ambiguity_count
ontology_label_success_rate
ontology_label_needs_review_rate
rkb_ready_rate
exception_rate
```

### 12.2 Quality metrics

```text
auto_label_precision
human_correction_rate
pending_decision_block_rate
conflict_detection_rate
BD citation coverage
source coverage per BD section
```

### 12.3 Business metrics

```text
BD draft cycle time
manual extraction effort reduction
review rework rate
client review issue count
requirement omission count
```

### 12.4 MVP target values

Initial target:

```text
traceability_rate = 100%
rkb_ready_rate >= 70%
auto_label_precision >= 85%
human_correction_rate <= 20%
exception_rate explainable = 100%
BD output source citation coverage = 100% when BD generation starts
```

No metric means no proof of value.

---

## 13. Build vs defer decisions

Not every correct idea belongs in MVP.

| Component | MVP | Phase 2+ |
|---|---:|---:|
| Excel parser | Yes | Improve |
| File registry | Yes | Improve |
| Source units | Yes | Yes |
| Traceable chunks | Yes | Yes |
| Rule-based ontology | Yes | Yes |
| LLM labeling | Limited | Yes |
| BM25 | Simple | Improve |
| Vector index | Manifest only | Yes |
| Agent factory | Skeleton only | Yes |
| GraphRAG | No | Maybe |
| Full BD generation | No | Yes |
| Human review UI | Simple table | Workflow UI |

Rule:

```text
Correct but non-essential components should be deferred.
```

---

## 14. Implementation order

Recommended order:

```text
1. naming_rules.yaml
2. workflow.yaml for ingest_excel_to_rkb
3. source_unit.schema.json
4. traceable_chunk.schema.json
5. rkb_item.schema.json
6. exception.schema.json
7. happy path eval
8. failure path evals
9. deterministic Excel parser
10. traceability validator
11. chunk builder
12. rule-based ontology labeler
13. RKB writer
14. simple review summary
15. only then agent/skill factory generator
```

Do not build first:

```text
- full skill factory
- vector DB
- GraphRAG
- multi-source parser
- BD generation UI
```

---

## 15. Eval gate

Every workflow must have at least these evals:

```text
happy_path.yaml
missing_required_input.yaml
missing_provenance_blocked.yaml
pending_decision_not_ready.yaml
ontology_label_must_be_controlled.yaml
multi_behavior_needs_split.yaml
```

Example:

```yaml
id: missing_range_should_stop
workflow: ingest_excel_to_rkb

input:
  file_path: data/raw/qa_keshikomi.xlsx
  source_kind: QA
  sheet_name: QA票
  range_a1: null
  domain_code: KESHI

expected:
  status: NEEDS_INPUT
  stopped_at: parse_excel
  must_not_create:
    - data/outputs/source_units.jsonl
    - data/outputs/rkb_items.jsonl
```

Rule:

```text
No eval = no deploy.
No source provenance = fail.
Dangerous tool permission = fail.
```

---

## 16. Operating model

A real BD workflow needs clear human roles.

| Role | Responsibility |
|---|---|
| BA | Check source meaning, source kind, ambiguity, client intent |
| SE / Architect | Approve design impact and BD mapping logic |
| Developer | Maintain parser, validators, schemas, and tests |
| PM | Monitor cycle time, RKB-ready rate, and exceptions |
| Client reviewer | Confirm pending decisions and scope changes |
| AI operator | Run workflow, inspect exceptions, prepare review summary |

The tool should not become a private assistant for one person only. It must support team workflow and auditability.

---

## 17. Anti-patterns

Avoid:

```text
One giant prompt reads all files and generates BD.
LLM guesses Excel range.
Vector DB becomes the source of truth.
Pending decisions become requirements.
Every agent has every tool.
Every skill can write anywhere.
No run state.
No evals.
No metrics.
No human approval before RKB_READY.
```

Correct pattern:

```text
Workflow first.
Contract first.
Schema first.
Tool first.
Prompt last.
```

---

## 18. Final recommendation

The project already has a strong methodology backbone.

The next maturity step is:

```text
methodology.md
→ methodology_addendum.md
→ workflow.yaml
→ schemas
→ evals
→ deterministic tools
→ run state
→ measurable MVP
```

Final statement:

```text
The system should not be judged by how impressive the agent prompt is.
It should be judged by whether every RKB item is traceable, validated, reviewable, measurable, and safe to use for BD mapping.
```
