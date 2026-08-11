# ReqKB Lineage Ownership and Publication Boundary

**Status:** POC architecture + implementation contract  
**Audience:** Coding agent / backend developer / workflow implementer / knowledge-graph implementer / reviewer  
**Scope:** Phân loại lineage/provenance và chốt loại nào thuộc Catalog DB, Object Store, ReqKB/Neo4j hoặc observability layer  
**Depends on:** `02_storage_boundary.md`, `03_logical_data_model.md`, `06_data_flow.md`, `07_data_mutation_spec.md`, `09_workflow_integration_guide.md`  
**Architecture relation:** specialization/clarification of `SB-01` and the ownership matrix in `02_storage_boundary.md`; this document does **not** change the current System-of-Record decision.

---

## 1. Purpose

Từ `lineage` dễ bị dùng cho nhiều nghĩa khác nhau.

Trong hệ thống này phải tách ít nhất bốn concern:

```text
1. Execution lineage
   ai/capability nào chạy, bằng runtime/model/config nào

2. Artifact lineage
   exact input nào tạo ra exact output candidate nào

3. Governance/publication lineage
   candidate nào được chọn làm baseline và publication nào đang active

4. Semantic lineage / source provenance
   knowledge entity có quan hệ business/semantic gì
   và knowledge đó có thể giải thích ngược về nguồn nào
```

Nếu gộp bốn loại này vào một graph/database duy nhất, ReqKB sẽ bị trộn giữa:

```text
business knowledge graph
+
workflow execution graph
+
artifact version graph
+
governance history
```

và rất khó xác định store nào là authoritative.

---

# 2. Decision in one screen

```text
FULL TECHNICAL / ARTIFACT / GOVERNANCE LINEAGE
→ Catalog DB is canonical

CANONICAL ARTIFACT BYTES / EVIDENCE
→ Object Store is canonical

PUBLISHED BUSINESS / SEMANTIC LINEAGE
→ ReqKB / Neo4j is canonical for active published semantics

POINTER FROM PUBLISHED KNOWLEDGE BACK TO PROVENANCE
→ ReqKB keeps only the minimum publication/source provenance needed for explainability
→ Catalog DB remains canonical for the full provenance chain

TRACE / EVAL / COST / SPAN DETAILS
→ MLflow or observability layer later
→ Catalog DB keeps only replay/governance-critical references such as trace_ref
```

### Core rule

> ReqKB is **not** the canonical execution-lineage database.

> Catalog DB is **not** the semantic serving graph.

---

# 3. Lineage taxonomy and owner matrix

| Lineage / provenance type | Example | Canonical owner | What may appear in ReqKB? |
|---|---|---|---|
| Source identity | `SourceAsset → SourceRevision` | Catalog DB | optional source identity/reference for explainability |
| Raw source bytes | Excel/PDF/DOCX | Object Store | no bytes; only source/provenance reference if useful |
| Runtime invocation | `ProcessingRun`, runtime correlation | Catalog DB | **No** |
| Capability execution | `StageExecution` | Catalog DB | **No** by default |
| Exact consumed input | `StageInput → SourceRevision/OutputSet` | Catalog DB | **No** by default |
| Artifact producer lineage | `StageExecution → OutputSet` | Catalog DB | **No** by default |
| Artifact membership | `OutputSet → StoredObject` | Catalog DB registry; Object Store bytes | **No** |
| Artifact candidate history | OutputSet A/B/C in one OutputSlot | Catalog DB | **No** |
| Baseline history/current | `BaselineSelection`, `BaselineHead` | Catalog DB | **No** |
| Stale derivation state | current upstream baseline vs historical StageInput | Catalog DB/domain derived | **No** |
| Publication history/current | `Publication`, `PublicationHead` | Catalog DB | publication provenance pointer/reference |
| Published domain entity | Requirement, Function, API, Screen, etc. | ReqKB/Neo4j | **Yes — core content** |
| Published semantic relationship | `Requirement IMPLEMENTED_BY API` | ReqKB/Neo4j | **Yes — core content** |
| Published source-provenance relationship | `Requirement DERIVED_FROM <source anchor>` | ReqKB projection/materialization; canonical source remains Catalog/Object Store | **Yes when explainability requires it** |
| Model trace/span | prompt/model/tool span | MLflow/observability later | normally no |
| Evaluation/cost/token metrics | eval score, latency, token/cost | MLflow/observability later | no |

---

# 4. Execution lineage — Catalog DB only

Execution lineage answers:

> Workflow/runtime đã thực hiện việc gì để tạo kết quả này?

Canonical chain:

```text
ProcessingRun
   ↓
StageExecution
   ↓
StageInput(s)
```

Typical fields/references include:

```text
processing_run_id
stage_execution_id
stage_type
component_ref
configuration_hash
schema_contract_ref
runtime_ref
model_ref
prompt_ref
ruleset_ref
trace_ref
status
started_at
completed_at
```

These belong to **Catalog DB**.

### Do not copy to every ReqKB node

Không mặc định đưa các field sau vào Requirement/Function/API nodes:

```text
processing_run_id
stage_execution_id
runtime_ref
model_ref
prompt_ref
retry history
execution status
```

### Rationale

ReqKB query chủ yếu trả lời:

```text
Requirement này liên quan Function/API/Screen nào?
Knowledge hiện tại nói gì?
Nguồn semantic nào hỗ trợ kết luận này?
```

Không phải:

```text
LangGraph thread nào chạy?
retry lần thứ mấy?
node execution nào fail trước khi thành công?
```

Các câu hỏi sau thuộc Catalog/observability.

---

# 5. Artifact lineage — Catalog DB + Object Store

Artifact lineage answers:

> Exact durable input nào đã tạo ra exact output candidate nào?

Canonical path:

```text
StageExecution
   ├── StageInput → SourceRevision
   └── StageInput → upstream OutputSet
              ↓
        produced OutputSet
              ↓
        StoredObject registry
              ↓
          Object Store
```

## 5.1 Catalog DB owns identity and relationships

Catalog DB giữ:

```text
StageInput exact references
OutputSlot identity
OutputSet candidate identity
producer_execution_id
StoredObject registry
content_hash
resolved_hash
schema/version metadata
```

## 5.2 Object Store owns bytes

Object Store giữ:

```text
raw source bytes
parsed/normalized artifact
chunk bundle
enrichment bundle
design candidate files
evidence/diagnostics
publication manifest
```

ReqKB không lưu artifact bytes và không trở thành source of truth cho candidate history.

---

# 6. Governance lineage — Catalog DB only

Governance lineage answers:

> Trong nhiều candidate, cái nào được chấp nhận và cái nào đang publish?

Canonical chain:

```text
OutputSlot
  ↓
OutputSet candidates
  ↓
BaselineSelection history
  ↓
BaselineHead
  ↓
Publication
  ↓
PublicationHead
```

Catalog DB owns:

```text
latest candidate history
accepted baseline history
who/why selected
optimistic concurrency version
publication lifecycle
previous publication chain
current publication pointer
```

### ReqKB must not infer governance truth

Không được dùng Neo4j để suy ra:

```text
latest OutputSet
current BaselineHead
which candidate was rejected
review history
which execution should rerun
```

ReqKB chỉ expose semantic state đã được publication boundary activate.

---

# 7. Semantic lineage — ReqKB / Neo4j

Semantic lineage answers:

> Knowledge object này liên hệ business/semantic với object khác như thế nào?

Examples:

```text
Requirement R-123
   ├── IMPLEMENTED_BY → API-017
   ├── REALIZED_ON    → Screen-005
   ├── USES_DATA      → Entity-Customer
   └── DEPENDS_ON     → Requirement R-122
```

Các relation này là **published semantic knowledge**, vì vậy ReqKB/Neo4j là serving/canonical owner của active semantic state sau publication.

### Important distinction

```text
Requirement R-123 IMPLEMENTED_BY API-017
= semantic lineage / domain knowledge
→ ReqKB

OUTSET-221 PRODUCED_BY STAGE-310
= technical artifact lineage
→ Catalog DB
```

Không dùng cùng một edge vocabulary để trộn hai concern này.

---

# 8. Source provenance inside ReqKB — projection, not full lineage copy

Một published knowledge entity cần khả năng trả lời:

> Kết luận này đến từ đâu?

ReqKB được phép/khuyến nghị giữ **minimum provenance pointer** để từ semantic entity đi về publication/source context.

## 8.1 Minimum requirement

Mỗi published semantic node/edge phải có khả năng resolve về exact `Publication` đã materialize nó.

Physical representation có thể là:

```text
publication_id property
```

hoặc:

```text
(:SemanticEntity)-[:PUBLISHED_IN]->(:PublicationRef)
```

hoặc publication namespace/version tagging.

Cách vật lý cuối cùng phụ thuộc Neo4j publication strategy; invariant là:

```text
published semantic record
→ exact Publication must be recoverable
```

## 8.2 Optional source-level provenance

Nếu real workflow tạo stable source locator, published semantic object có thể giữ:

```text
source_asset_id
source_revision_id
source_unit_id / source_anchor
page / section / heading path / range
```

**chỉ khi các identity/locator đó có semantics ổn định trong workflow thật**.

Không invent `source_unit_id` ở Neo4j nếu workflow/artifact contract thật chưa có stable SourceUnit identity.

## 8.3 Canonical owner remains outside ReqKB

Ngay cả khi ReqKB có:

```text
source_revision_id = REV-004
source_anchor = 3.1.2
```

canonical source revision identity vẫn ở Catalog DB và canonical source/artifact bytes vẫn ở Object Store.

Neo4j copy là provenance projection để query/explain nhanh.

---

# 9. Deep trace path — how to answer “where did this knowledge come from?”

Expected cross-store trace:

```text
ReqKB semantic node / edge
        ↓
recover publication_id
        ↓
Catalog DB: Publication
        ↓
BaselineSelection
        ↓
OutputSet
        ↓
producer StageExecution
        ↓
StageInput(s)
        ↓
SourceRevision / upstream OutputSet
        ↓
StoredObject / raw_object_ref
        ↓
Object Store canonical payload
```

Optional observability extension:

```text
StageExecution.trace_ref
        ↓
MLflow / trace backend
        ↓
model/tool spans, eval, latency, token/cost
```

This is the canonical **full explainability path**.

---

# 10. What goes into ReqKB vs what stays out

## 10.1 Put into ReqKB

### Required semantic content

```text
domain entities
published semantic properties
published semantic relationships
active publication visibility/version information required by Neo4j strategy
```

### Provenance sufficient for explainability

```text
publication reference — required to be recoverable
source identity/source locator — optional based on real workflow contract
semantic DERIVED_FROM/SOURCED_FROM edge — optional when useful to users/querying
```

## 10.2 Do NOT put into ReqKB by default

```text
ProcessingRun history
StageExecution history
StageInput graph
OutputSlot candidate history
all OutputSet candidates
StoredObject registry
runtime_ref
retry/checkpoint history
BaselineSelection history
BaselineHead
review queue/history
stale derivation graph
prompt/model/ruleset execution metadata
MLflow spans/evaluation records
```

### Exception rule

Một technical provenance field chỉ được duplicate vào ReqKB nếu có một **concrete semantic query/latency requirement** chứng minh cần nó.

Nếu duplicate:

```text
Catalog DB remains canonical
ReqKB value is a projection/cache/reference
```

---

# 11. Publication contract for lineage

Publication service must distinguish:

```text
A. semantic payload to materialize
B. provenance metadata/pointers to attach
C. technical lineage that remains only in Catalog DB
```

Recommended publication output contract:

```text
PublicationMaterialization
├── semantic_nodes[]
├── semantic_edges[]
├── provenance
│   ├── publication_id
│   ├── optional source refs / locators
│   └── optional semantic source-provenance edges
└── manifest
```

Not:

```text
PublicationMaterialization
└── entire ProcessingRun/StageExecution/OutputSet graph
```

---

# 12. Example

Assume:

```text
Requirement.xlsx REV-004
→ parse/enrich workflow
→ accepted output OUTSET-221
→ PUB-009
→ Requirement R-123 published
```

## Catalog DB

```text
REV-004
  ↓ StageInput
STAGE-310
  ↓ produces
OUTSET-221
  ↓ selected by
BASELINE-008
  ↓ published by
PUB-009 ACTIVE
```

## Object Store

```text
raw requirement.xlsx
parsed-document.json
requirements.json
publication-manifest.json
```

## ReqKB

```text
(:Requirement {id: "R-123", ...})
   -[:IMPLEMENTED_BY]-> (:API {id: "API-017"})

and publication provenance sufficient to resolve:
R-123 → PUB-009

optionally:
R-123 → source REV-004 / stable source anchor
```

ReqKB does **not** need:

```text
STAGE-310 node
OUTSET-221 node
BASELINE-008 node
LangGraph runtime node
```

for normal semantic serving.

---

# 13. Real workflow integration rules

When applying this to the actual workflow/app, add a lineage classification column to the workflow-specific inventory.

Recommended mapping table:

| Real data/relation | Lineage class | Canonical owner | Publish to ReqKB? | Why |
|---|---|---|---:|---|
| `<item>` | execution / artifact / governance / semantic / source-provenance / observability | `<store>` | Yes/No | `<query/recovery reason>` |

For every real workflow output, coding agent must decide:

```text
Is this business semantic knowledge?
→ ReqKB after publication

Is this exact execution/artifact provenance?
→ Catalog DB

Is this canonical payload/evidence?
→ Object Store

Is this only trace/evaluation telemetry?
→ observability layer
```

Do not decide storage based on whether the information can technically be represented as a Neo4j node/edge.

---

# 14. Acceptance tests

## Test A — semantic query does not require execution graph in Neo4j

A normal query such as:

```text
Requirement R-123 implemented by what API?
```

must be answered by ReqKB without loading Catalog execution history.

## Test B — deep provenance can cross back to Catalog

Starting from published Requirement R-123, system can resolve:

```text
R-123
→ Publication
→ BaselineSelection
→ OutputSet
→ StageExecution
→ exact StageInputs
→ SourceRevision
```

## Test C — runtime history can be deleted/archived independently of semantic graph

ReqKB semantic topology must not rely on runtime checkpoint IDs as domain identity.

## Test D — rerun does not pollute semantic graph

Creating OUTSET-A, OUTSET-B, OUTSET-C must not automatically create three active semantic versions in ReqKB.

Only activated Publication controls visible semantic state.

## Test E — publication failure preserves both sides correctly

If new Neo4j materialization fails:

```text
Catalog: new Publication = FAILED
Catalog: previous PublicationHead unchanged
ReqKB: previous active semantic state remains visible
```

---

# 15. Decision rationale and ADR threshold

## Current decision

This document clarifies the already accepted storage boundary:

```text
Catalog DB
= canonical technical/artifact/governance lineage

ReqKB
= canonical active published semantic knowledge
  + minimum provenance projection/reference
```

No new ADR is required because this does not move a System of Record; it specializes `SB-01` and the existing ownership matrix in `02_storage_boundary.md`.

## Create a new ADR if later deciding any of these

```text
Neo4j becomes authoritative for technical execution lineage
Catalog DB no longer owns exact StageInput/OutputSet provenance
full execution graph is replicated into ReqKB as a supported product contract
publication provenance representation becomes a hard external API contract
one graph database is chosen as canonical owner for both workflow and semantic lineage
```

Those would materially change ownership/consistency and require explicit trade-off analysis.

---

# 16. Final rule for coding agent

```text
Execution happened how?          → Catalog DB
Artifact came from what input?    → Catalog DB
Which candidate was accepted?     → Catalog DB
Where are the actual bytes?       → Object Store
What does the business knowledge mean / connect to? → ReqKB
Which published knowledge came from which publication/source? → ReqKB pointer/projection
Need the full proof chain?         → follow pointer back to Catalog DB
Need model spans/eval/cost?        → MLflow/observability later
```

The goal is **cross-store traceability without cross-store ownership ambiguity**.