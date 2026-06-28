# Workflow Agent Design — Sequential Multi-Agent / Tool Pipeline

> Scope: basic design for a workflow with multiple agents and deterministic tools running in sequence.  
> Context: BD Chunk Project, especially the first executable workflow `ingest_excel_to_rkb`.

---

## 1. Core idea

A workflow with many agents/tools should be designed as an orchestrated pipeline, not as agents running freely.

```text
User request
→ Workflow Orchestrator
→ Stage 1 Agent + Tool calls
→ Validate output
→ Stage 2 Agent + Tool calls
→ Validate output
→ Stage 3 Agent + Tool calls
→ Human gate if needed
→ Final output
```

Short rule:

```text
Workflow = orchestration
Agent = stage decision worker
Tool = deterministic executor
Validator = quality gate
State = audit trail
Human gate = risk control
```

---

## 2. Core components

A sequential workflow has five main layers:

```text
Workflow
├─ Input contract
├─ Stage sequence
├─ Agent per stage
├─ Tool calls per agent
└─ Output + validation + state
```

For the BD Chunk Project, the first workflow should be:

```text
ingest_excel_to_rkb
├─ Stage 1: Register file
├─ Stage 2: Parse Excel
├─ Stage 3: Validate source units
├─ Stage 4: Build chunks
├─ Stage 5: Label ontology
├─ Stage 6: Review RKB candidates
└─ Stage 7: Write RKB items
```

---

## 3. Standard flow

```mermaid
flowchart TD
    U[User / CLI Request] --> O[Workflow Orchestrator]

    O --> S1[Stage 1: File Registry Agent]
    S1 --> T1[Tool: hash_file]
    S1 --> T2[Tool: detect_file_type]
    S1 --> T3[Tool: register_file]
    T3 --> V1[Validate file registry]

    V1 --> S2[Stage 2: Excel Parser Agent]
    S2 --> T4[Tool: parse_excel_range]
    T4 --> V2[Validate source units]

    V2 -->|valid| S3[Stage 3: Chunk Builder Agent]
    V2 -->|invalid| EX[Exception Queue]

    S3 --> T5[Tool: build_traceable_chunks]
    T5 --> V3[Validate chunks]

    V3 --> S4[Stage 4: Ontology Labeler Agent]
    S4 --> T6[Tool: apply_ontology_rules]
    T6 --> V4[Validate ontology labels]

    V4 --> S5[Stage 5: RKB Reviewer Agent]
    S5 --> HG[Human Gate]
    HG -->|approved| OUT[RKB Items]
    HG -->|needs review| EX
```

---

## 4. Workflow Orchestrator

The Orchestrator is the workflow-level coordinator.

Responsibilities:

```text
- receive user or CLI input
- validate required input fields
- call stages in the defined order
- pass structured outputs from one stage to the next
- stop when validation fails
- write run state
- return a final summary
```

Forbidden actions:

```text
- do not parse Excel directly
- do not invent source ranges
- do not approve requirements by itself
- do not generate BD from raw input
```

The Orchestrator should operate from `workflow.yaml`, not from ad hoc prompt logic.

---

## 5. Stage Agent

Each stage should have exactly one primary responsible agent.

Examples:

```text
FileRegistryAgent        = registers raw files
ExcelSourceParserAgent   = parses Excel into source units
TraceabilityValidatorAgent = validates source provenance
ChunkBuilderAgent        = builds traceable chunks
OntologyLabelerAgent     = applies controlled ontology labels
RKBReviewerAgent         = prepares review and promotes approved RKB items
```

Rule:

```text
One agent should not own too many responsibilities.
```

A stage agent should decide which allowed tool to call, but it must not perform deterministic work itself.

---

## 6. Tool

Tools are executable functions or scripts.

Examples:

```text
hash_file
detect_file_type
register_file
parse_excel_range
validate_source_units
build_traceable_chunks
apply_ontology_rules
write_jsonl
write_exceptions
```

Tool rule:

```text
Same input should produce same output.
```

Forbidden:

```text
Do not ask an LLM to guess workbook_sha256, sheet_name, range_a1, source_granularity, unit_id, chunk_id, or rkb_id.
```

---

## 7. Validator

Validator is the quality gate between stages.

Example after Excel parsing:

```text
If workbook_name is missing → fail
If workbook_sha256 is missing → fail
If sheet_name is missing → fail
If range_a1 is missing → fail
If raw_text is empty → fail
```

Validator result controls workflow movement:

```text
pass → continue to next stage
fail → write exceptions and stop
needs_review → human gate
```

---

## 8. Human gate

Human gate should be risk-based, not universal.

Trigger human review for:

```text
- PENDING_DECISION
- TECHNICAL_INFERENCE
- conflict_flag = true
- low confidence
- multi_behavior_row
- ambiguity terms such as 別途確認 / 未定 / 必要に応じて
- before RKB_READY promotion
- before BD mapping or BD generation
```

Human gate protects correctness and prevents pending/inferred items from becoming source facts.

---

## 9. Basic `workflow.yaml`

A workflow should be declared as data.

```yaml
id: ingest_excel_to_rkb
name: Ingest Excel to RKB
version: 0.1.0

input_contract:
  required:
    - file_path
    - source_kind
    - sheet_name
    - range_a1
    - domain_code

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
    - rkb_ready_count
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
    validator: validate_file_registry

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
    validator: validate_source_units

  - id: build_chunks
    agent: ChunkBuilderAgent
    tools:
      - build_traceable_chunks
      - detect_multi_behavior
      - detect_ambiguity_terms
    inputs:
      - source_units
    outputs:
      - traceable_chunks
    validator: validate_traceable_chunks

  - id: label_ontology
    agent: OntologyLabelerAgent
    tools:
      - load_ontology_yaml
      - apply_ontology_rules
      - validate_ontology_labels
    inputs:
      - traceable_chunks
    outputs:
      - rkb_candidates
    validator: validate_ontology_labels

  - id: review_rkb
    agent: RKBReviewerAgent
    human_gate: true
    inputs:
      - rkb_candidates
    outputs:
      - rkb_items

stop_conditions:
  - missing_file_path
  - missing_sheet_name
  - missing_range_a1
  - traceability_rate_below_1
  - invalid_ontology_label
  - unresolved_conflict
```

`workflow.yaml` is the orchestration contract. The runner should execute it stage by stage.

---

## 10. Basic agent config

Example `agents/excel_source_parser.agent.yaml`:

```yaml
name: ExcelSourceParserAgent
stage: parse_excel

role: >
  Parse Excel QA/RD sheets into traceable source units.

mission: >
  Convert registered Excel rows or blocks into source_units.jsonl.
  Preserve workbook, sheet, range, and raw text.

input_contract:
  required:
    - file_path
    - file_id
    - workbook_sha256
    - sheet_name
    - range_a1
    - source_kind
    - domain_code

allowed_tools:
  - parse_excel_range
  - validate_source_units
  - write_jsonl
  - write_exceptions

forbidden_actions:
  - infer_sheet_name
  - infer_range_a1
  - classify_requirement_type
  - normalize_requirement_text
  - create_rkb_item
  - create_bd_mapping

output_contract:
  files:
    - data/outputs/source_units.jsonl
    - data/outputs/exceptions.jsonl
  metrics:
    - source_unit_count
    - invalid_unit_count
    - traceability_rate

stop_conditions:
  - missing_sheet_name
  - missing_range_a1
  - traceability_rate_below_1
```

Agent config is not only prompt. It is role, permission, contract, and guardrail.

---

## 11. Tool contract

Example `tools/tool_contracts.yaml`:

```yaml
tools:
  parse_excel_range:
    description: Parse Excel range into row-level source units.
    input_schema:
      required:
        - file_path
        - workbook_sha256
        - sheet_name
        - range_a1
        - chunking_mode
    output_schema:
      required:
        - source_units
      source_unit_required_fields:
        - unit_id
        - raw_text
        - workbook_name
        - workbook_sha256
        - sheet_name
        - range_a1
        - source_granularity

  validate_source_units:
    description: Validate source unit provenance and raw text.
    input_schema:
      required:
        - source_units
    output_schema:
      required:
        - valid_units
        - invalid_units
        - traceability_rate
```

Tool contracts prevent agents from calling tools with vague or incomplete inputs.

---

## 12. Workflow state

Workflow state must be stored outside chat memory.

Recommended run folder:

```text
data/runs/
  run-20260628-001/
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

Example `stage_status.json`:

```json
{
  "run_id": "run-20260628-001",
  "workflow_id": "ingest_excel_to_rkb",
  "status": "NEEDS_REVIEW",
  "stages": {
    "register_file": "completed",
    "parse_excel": "completed",
    "build_chunks": "completed",
    "label_ontology": "completed",
    "review_rkb": "needs_human_review"
  }
}
```

State enables:

```text
- resume
- audit
- failure diagnosis
- tool call trace
- validation trace
- human approval trace
```

---

## 13. Agent-to-agent handoff

Do not pass long free-text summaries between agents. Pass structured data or file paths.

Stage 1 output:

```json
{
  "file_registry_record": {
    "file_id": "sha256:abc123",
    "file_path": "data/raw/qa_keshikomi.xlsx",
    "file_type": "excel",
    "source_kind": "QA",
    "workbook_sha256": "abc123"
  }
}
```

Stage 2 input:

```json
{
  "file_registry_record": "...",
  "sheet_name": "QA票",
  "range_a1": "B12:E30",
  "chunking_mode": "row"
}
```

Stage 2 output:

```json
{
  "source_units_path": "data/outputs/source_units.jsonl",
  "traceability_rate": 1.0,
  "source_unit_count": 19,
  "invalid_unit_count": 0
}
```

Rule:

```text
Agent-to-agent handoff = structured data.
Not chat-style prose.
```

---

## 14. Error handling

Each stage must declare failure modes.

```yaml
failure_modes:
  missing_input:
    status: NEEDS_INPUT
    stop: true

  validation_failed:
    status: FAILED_VALIDATION
    stop: true
    write_to: data/outputs/exceptions.jsonl

  low_confidence:
    status: NEEDS_REVIEW
    stop: false
    human_gate: true

  unresolved_conflict:
    status: NEEDS_REVIEW
    stop: true
    human_gate: true
```

Rule:

```text
If required data is missing or validation fails, do not guess. Stop or send to review.
```

---

## 15. Workflow folder structure

Recommended folder:

```text
workflows/
  ingest_excel_to_rkb/
    workflow.yaml
    README.md

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

    tools/
      tool_contracts.yaml
      tool_permissions.yaml

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
      source_units.example.jsonl
      traceable_chunks.example.jsonl
      rkb_candidates.example.jsonl
      summary.example.md

    evals/
      happy_path.yaml
      missing_sheet_name.yaml
      missing_range_a1.yaml
      missing_provenance_blocked.yaml
      pending_decision_blocked.yaml
      ontology_label_controlled.yaml
```

For smaller workflows:

```text
workflows/
  ingest_excel_to_rkb/
    workflow.yaml
    README.md
    schemas/
    examples/
    evals/
```

---

## 16. Basic runner pseudo-code

```python
def run_workflow(workflow, request):
    run_state = create_run_state(workflow["id"], request)

    validate_input(workflow["input_contract"], request)

    context = {
        "request": request,
        "outputs": {},
        "metrics": {},
    }

    for stage in workflow["stages"]:
        update_stage_status(run_state, stage["id"], "running")

        agent = load_agent(stage["agent"])
        tool_results = agent.run_stage(
            stage=stage,
            context=context,
        )

        validation_result = run_validator(
            stage.get("validator"),
            tool_results,
        )

        write_tool_logs(run_state, stage, tool_results)
        write_validation_logs(run_state, stage, validation_result)

        if not validation_result["passed"]:
            write_exceptions(validation_result["errors"])
            update_stage_status(run_state, stage["id"], "failed")
            return {
                "status": "failed",
                "failed_stage": stage["id"],
                "errors": validation_result["errors"],
            }

        context["outputs"][stage["id"]] = tool_results
        update_stage_status(run_state, stage["id"], "completed")

        if stage.get("human_gate"):
            review_result = request_human_review(tool_results)
            write_human_decisions(run_state, review_result)

            if not review_result["approved"]:
                update_stage_status(run_state, stage["id"], "needs_review")
                return {
                    "status": "needs_review",
                    "stage": stage["id"],
                    "review_items": review_result["items"],
                }

    final_summary = build_summary(context)
    update_run_status(run_state, "completed")

    return {
        "status": "completed",
        "summary": final_summary,
    }
```

Core loop:

```text
for each stage:
  load agent
  agent calls allowed tools
  validate result
  if fail → stop
  if human gate → ask review
  if pass → next stage
```

---

## 17. Recommended workflow roadmap

Do not start with `generate_full_bd`.

Start with:

```text
ingest_excel_to_rkb
```

This proves:

```text
Excel QA票
→ source_units with provenance
→ traceable_chunks
→ controlled ontology labels
→ RKB-ready items
→ clear exception queue
```

Then add:

```text
map_rkb_to_bd_section
```

Then add:

```text
generate_bd_patch
```

---

## 18. Final rule

The basic design of a sequential multi-agent workflow is:

```text
workflow.yaml defines stage order
each stage has one responsible agent
agent only calls allowed tools
tools produce deterministic outputs
validators check outputs
state records progress and audit logs
human gates stop risky cases
only a passed stage can trigger the next stage
```

Final sentence:

```text
Workflow first, contract first, tool first, prompt last.
```
