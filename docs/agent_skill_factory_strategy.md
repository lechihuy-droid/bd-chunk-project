# Agent / Skill Factory Strategy

> Scope: strategy for creating many agents/skills quickly and deploying them safely for the BD Chunk Project.

---

## 1. Core idea

Do not hand-write every agent and skill.

Use an **Agent / Skill Factory**:

```text
Catalog YAML
→ Templates
→ Generator
→ Validator
→ Eval
→ Deploy
```

The goal is to make agents/skills scalable, consistent, reviewable, and safe.

```text
Agent/Skill Factory
= YAML spec
+ Prompt template
+ Tool permission profile
+ Generator
+ Validator
+ Eval gate
+ Deploy script
```

---

## 2. Agent, skill, and tool distinction

```text
Agent = runtime worker with role, mission, tools, guardrails, state, and output contract.
Skill = reusable capability package / SOP that an agent can use.
Tool = deterministic function or script that performs real work.
```

For BD Chunk Project:

```text
Agent = virtual worker
Skill = standard operating procedure / capability
Tool = actual parser, validator, indexer, writer
```

Example:

```text
ExcelSourceParserAgent
uses skill: ingest-excel-source
calls tools: parse_excel_range, validate_source_units, write_jsonl
```

---

## 3. Why a factory is needed

If the project grows to 30-100 agents/skills, manual authoring becomes risky.

Problems:

```text
- duplicate prompts
- inconsistent guardrails
- unclear descriptions
- too many tools exposed to one agent
- missing eval cases
- unsafe write permissions
- difficult deployment
```

Factory pattern solves this by making YAML catalogs the source of truth.

---

## 4. Recommended architecture

```text
registry/
  agent_catalog.yaml
  skill_catalog.yaml
  tool_profiles.yaml
  deployment_targets.yaml

templates/
  agent_prompt.md.j2
  skill.md.j2
  copilot_instruction.md.j2
  eval_case.yaml.j2

scripts/
  generate_agents.py
  validate_agent_specs.py
  validate_skill_specs.py
  deploy_skills.py

agents/
  *.agent.yaml

prompts/
  *.md

.claude/skills/
  <skill-name>/SKILL.md

.github/
  copilot-instructions.md
  instructions/*.instructions.md

evals/
  *.yaml
```

Flow:

```text
Catalog
→ Generate agent/skill files
→ Validate permissions and metadata
→ Run smoke evals
→ Deploy to repo/runtime
```

---

## 5. Agent catalog

`registry/agent_catalog.yaml` should define all agents.

Example:

```yaml
agents:
  - id: file_registry_agent
    name: FileRegistryAgent
    stage: ingest
    role: Register raw files and compute deterministic file metadata.
    mission: Convert raw file paths into file_registry records with file hash and source kind.
    prompt_template: agent_prompt.md.j2
    tool_profile: read_write_registry
    allowed_tools:
      - hash_file
      - detect_file_type
      - register_file
      - write_jsonl
    forbidden_actions:
      - infer_file_hash
      - parse_requirement
      - create_rkb_item
      - create_bd_mapping
    output_schema: FileRegistryResult
    eval_cases:
      - evals/file_registry_basic.yaml

  - id: excel_source_parser_agent
    name: ExcelSourceParserAgent
    stage: ingest
    role: Parse Excel QA/RD sheets into traceable source units.
    mission: Create source_units.jsonl with workbook, sheet, range, and raw text.
    prompt_template: agent_prompt.md.j2
    tool_profile: excel_parse_only
    allowed_tools:
      - parse_excel_range
      - validate_source_units
      - write_jsonl
      - write_exceptions
    forbidden_actions:
      - infer_sheet_name
      - infer_range_a1
      - classify_requirement_type
      - create_bd_mapping
    output_schema: SourceUnitsResult
    eval_cases:
      - evals/excel_parser_traceability.yaml

  - id: ontology_labeler_agent
    name: OntologyLabelerAgent
    stage: rkb
    role: Apply controlled ontology labels to traceable chunks.
    mission: Label chunks using ontology YAML and never invent new labels.
    prompt_template: agent_prompt.md.j2
    tool_profile: label_only
    allowed_tools:
      - load_ontology_yaml
      - apply_ontology_rules
      - validate_ontology_labels
      - write_jsonl
    forbidden_actions:
      - invent_new_label
      - approve_pending_decision
      - create_bd_patch
    output_schema: OntologyLabelingResult
```

---

## 6. Skill catalog

`registry/skill_catalog.yaml` should define reusable skills.

Example:

```yaml
skills:
  - id: ingest-excel-source
    command_name: ingest-excel-source
    description: >
      Parse registered Excel QA/RD files into traceable source units.
      Use when the user asks to ingest Excel, parse QA票, or create source_units.jsonl.
    stage: ingest
    invocation: manual_or_auto
    paths:
      - "data/raw/**/*.xlsx"
      - "src/bd_chunk/ingest/**"
    allowed_tools:
      - Read
      - Bash
      - Write
    disallowed_tools:
      - WebFetch
    prompt_template: skill.md.j2
    supporting_files:
      - examples/source_unit.example.json
      - scripts/validate_source_units.sh

  - id: review-rkb-candidates
    command_name: review-rkb-candidates
    description: >
      Review RKB candidates and summarize Ready, Needs Review, Pending, Conflict,
      and Exception items before BD mapping.
    stage: review
    invocation: manual_only
    allowed_tools:
      - Read
      - Write
    disallowed_tools:
      - Bash
```

Guideline:

```text
Description must be specific.
Avoid broad descriptions like "helps with BD project".
```

---

## 7. Tool profiles

Do not assign tool permissions ad hoc.

Use tool profiles.

`registry/tool_profiles.yaml`:

```yaml
tool_profiles:
  read_only:
    allowed:
      - Read
      - Grep
    disallowed:
      - Bash
      - Write

  parse_excel:
    allowed:
      - Read
      - Bash
      - Write
    constraints:
      - only_run_scripts_under: scripts/
      - only_write_under:
          - data/outputs/
          - data/index/

  review_only:
    allowed:
      - Read
      - Write
    disallowed:
      - Bash

  bd_generation:
    allowed:
      - Read
      - Write
    constraints:
      - only_write_under:
          - data/outputs/
```

Rule:

```text
Skill/agent does not choose tools freely.
It uses reviewed tool_profile.
```

---

## 8. Prompt template

Use one standard template for many agents.

`templates/agent_prompt.md.j2`:

```md
# {{ agent.name }}

## Role
{{ agent.role }}

## Mission
{{ agent.mission }}

## Allowed tools
{% for tool in agent.allowed_tools %}
- {{ tool }}
{% endfor %}

## Forbidden actions
{% for action in agent.forbidden_actions %}
- {{ action }}
{% endfor %}

## Output contract
Return only valid output matching schema: `{{ agent.output_schema }}`.

## Guardrails
- Do not invent provenance.
- Do not infer workbook/sheet/range.
- If required data is missing, return NEEDS_INPUT.
- If validation fails, stop downstream processing.
```

`templates/skill.md.j2`:

```md
---
name: {{ skill.command_name }}
description: {{ skill.description }}
allowed-tools: {{ skill.allowed_tools | join(", ") }}
disallowed-tools: {{ skill.disallowed_tools | join(", ") }}
{% if skill.paths %}
paths:
{% for path in skill.paths %}
  - "{{ path }}"
{% endfor %}
{% endif %}
---

# {{ skill.command_name }}

## Purpose
{{ skill.description }}

## Procedure
{{ skill.procedure }}

## Output
{{ skill.output_contract }}

## Safety
- Do not invent source metadata.
- Do not continue if validation fails.
```

---

## 9. Deployment targets

### 9.1 Repo-level deployment

Fastest target for this repo:

```text
agents/*.agent.yaml
prompts/*.md
.claude/skills/<skill-name>/SKILL.md
.github/copilot-instructions.md
.github/instructions/*.instructions.md
AGENTS.md
```

### 9.2 Runtime deployment

Use later when tools and flow are stable:

```text
OpenAI Agents SDK runner
Google ADK runtime
custom Typer CLI runner
```

### 9.3 CI/CD deployment

Each catalog update should run:

```text
1. generate files
2. lint YAML
3. lint prompts
4. check duplicate descriptions
5. check allowed tools
6. run smoke evals
7. package skills
8. deploy
```

---

## 10. Bulk creation workflow

CLI concept:

```bash
bdagent generate \
  --agent-catalog registry/agent_catalog.yaml \
  --skill-catalog registry/skill_catalog.yaml \
  --out .

bdagent validate \
  --agents agents/ \
  --skills .claude/skills/ \
  --tools registry/tool_profiles.yaml

bdagent eval \
  --evals evals/ \
  --target local

bdagent deploy \
  --target repo
```

Flow:

```text
Catalog
→ Generate
→ Validate
→ Eval
→ Deploy
```

Adding 20 skills should mean adding 20 records to `skill_catalog.yaml`, not manually creating 20 folders.

---

## 11. Validation before deploy

Mandatory checks:

```text
[ ] agent id unique
[ ] skill command unique
[ ] description is specific
[ ] description not duplicated across skills
[ ] allowed_tools belongs to allowlist
[ ] tool_profile exists
[ ] output_schema exists
[ ] eval_cases exist
[ ] no Bash for review-only skill
[ ] no Write for read-only skill
[ ] no automatic invocation for dangerous skill
[ ] no suspicious phrases like "ignore previous instructions"
```

Validation rule:

```text
No eval = no deploy.
No source provenance = fail.
Dangerous tool permission = fail.
```

---

## 12. Evaluation strategy

Every agent/skill should have at least one smoke eval.

Example `evals/excel_parser_traceability.yaml`:

```yaml
id: excel_parser_traceability
agent: ExcelSourceParserAgent
input:
  file_path: fixtures/qa_keshikomi.xlsx
  sheet_name: QA票
  range_a1: B12:E13
expected:
  traceability_rate: 1.0
  required_fields:
    - workbook_name
    - workbook_sha256
    - sheet_name
    - range_a1
  forbidden:
    - requirement_type
    - target_bd_frame_id
```

Minimum eval set:

```text
- Excel parse success
- Missing range should fail
- Pending decision blocked
- Ontology label must be from controlled vocabulary
- Review-only skill cannot use Bash
```

---

## 13. Recommended rollout for BD Chunk Project

Do not create 50 agents first.

Use:

```text
Few core agents
+ many small skills
+ strict deterministic tools
```

### Core agents

```text
1. OrchestratorAgent
2. FileRegistryAgent
3. SourceParserAgent
4. TraceabilityValidatorAgent
5. ChunkBuilderAgent
6. RKBReviewerAgent
```

### Initial skills

```text
ingest-excel-source
ingest-markdown-source
detect-excel-merged-cells
build-traceable-chunks
detect-ambiguity-terms
label-ontology
normalize-ears-ja
review-rkb-candidates
build-bm25-index
build-semantic-manifest
```

Recommendation:

```text
Agent ít, skill nhiều, tool strict.
```

---

## 14. One-week implementation plan

### Day 1 — Catalogs and templates

```text
registry/agent_catalog.yaml
registry/skill_catalog.yaml
registry/tool_profiles.yaml
templates/*.j2
```

### Day 2 — Generator

```text
scripts/generate_agents.py
scripts/validate_agent_specs.py
scripts/validate_skill_specs.py
```

### Day 3 — Core agents

```text
orchestrator
file_registry
source_parser
traceability_validator
chunk_builder
rkb_reviewer
```

### Day 4 — Initial skills

```text
ingest-excel-source
build-traceable-chunks
label-ontology
review-rkb-candidates
build-bm25-index
```

### Day 5 — Smoke evals

```text
Excel parse success
Missing range fail
Pending decision blocked
Ontology label controlled
```

### Day 6 — Repo deployment

```text
.claude/skills/
.github/copilot-instructions.md
.github/instructions/
agents/
prompts/
```

### Day 7 — Runtime PoC

```text
CLI command
or OpenAI Agents SDK runner
or ADK local runtime
```

---

## 15. Final recommendation

For `bd-chunk-project`, use this operating model:

```text
6 core agents
+ 10-20 project skills
+ deterministic tools
+ YAML catalog
+ generator
+ validation gate
+ smoke evals
+ repo-level deployment first
+ runtime SDK deployment later
```

Final sentence:

```text
To create agents/skills at scale, do not write prompts manually.
Build a factory: catalog → template → validate → eval → deploy.
```
