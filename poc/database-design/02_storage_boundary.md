# ReqKB Ingestion Storage Boundary

**Status:** POC architecture baseline  
**Scope:** Storage ownership and System-of-Record boundaries for ReqKB ingestion  
**Depends on:** `00_database_review_methodology.md`, `01_design_methodology.md`

---

## 1. Purpose

Tài liệu này chốt **dữ liệu nào thuộc Object Store, Ingestion Catalog DB, và ReqKB/Neo4j**.

Mục tiêu là giữ boundary ổn định ngay cả khi workflow thay đổi.

Không thiết kế theo G0/G1/G2 cụ thể. Các stage chỉ là producer/consumer của các abstraction chung:

```text
SourceRevision
   ↓
StageExecution
   ↓
OutputSet
   ↓
OutputSlot / ArtifactSeries
   ↓
Baseline
   ↓
Publication
```

---

## 2. Ba storage concern

```text
Object Store
= canonical immutable payload/evidence

Ingestion Catalog DB
= identity, execution, lineage, governance, queryable projections

ReqKB / Neo4j
= published semantic knowledge
```

Nguyên tắc:

> Một dữ liệu có thể xuất hiện ở nhiều system dưới dạng reference/projection, nhưng chỉ có một canonical owner.

---

## 3. Object Store — canonical payload store

Object Store là System of Record cho **bytes và structured artifact payload**.

Ví dụ:

- raw Excel/DOCX/PDF;
- normalized Markdown;
- parsed-document JSON;
- chunk bundle;
- enriched chunk bundle;
- diagnostics;
- evaluation evidence;
- publication manifest.

Mỗi StoredObject phải immutable sau khi register.

Logical metadata tối thiểu:

```text
stored_object_id
object_uri
content_hash
media_type
schema_version
size_bytes
created_at
```

Không dùng object key như:

```text
/final/
/current/
/latest/
```

để biểu diễn governance state.

Object key chỉ là storage location.

---

## 4. Ingestion Catalog DB — governance and catalog store

Catalog DB là System of Record cho:

### Identity

```text
SourceAsset
SourceRevision
ProcessingRun
StageExecution
OutputSlot
OutputSet
StoredObject registry
```

### Lineage

```text
StageInput
Execution → OutputSet
OutputSet → StoredObject
OutputSet → OutputSlot
```

### Version governance

```text
BaselineHistory
ReviewRequest
ReviewDecision
Publication
```

### Queryable projections

Catalog DB có thể giữ projection để phục vụ:

- diff;
- search/filter;
- validation;
- review UI;
- lineage query;
- stale detection.

Ví dụ `SourceUnitProjection`:

```text
source_unit_id
output_set_id
unit_type
ordinal
heading_path
content_hash
text_excerpt / text_ref
```

Nhưng projection **không phải canonical payload** nếu source-of-truth đã được chốt là Object Store artifact.

Nếu projection và canonical artifact khác nhau:

```text
Object Store wins
→ projection phải rebuild/reconcile
```

---

## 5. ReqKB / Neo4j — published semantic store

Neo4j chỉ chứa semantic knowledge đã qua Publication boundary.

Ví dụ:

```text
Requirement
Function
BusinessRule
Constraint
Term
SourceUnit semantic representation
semantic relationships
```

Neo4j không được dùng làm:

- scratchpad của parser;
- store cho mọi intermediate candidate;
- workflow execution state;
- review queue;
- baseline history.

Publication là transition:

```text
Baseline OutputSet
      ↓
Publication
      ↓
Neo4j materialization
```

---

## 6. Canonical vs projection rule

Mỗi data object phải được phân loại thành một trong bốn nhóm.

### A. Canonical Payload

Primary owner: Object Store.

Ví dụ:

```text
raw.xlsx
normalized.md
chunks.json
enriched.json
```

### B. Canonical Governance Record

Primary owner: Catalog DB.

Ví dụ:

```text
StageExecution
OutputSlot
BaselineHistory
ReviewDecision
Publication
```

### C. Rebuildable Projection

Primary owner: source artifact khác; DB chỉ giữ query model.

Ví dụ:

```text
SourceUnitProjection
validation summary
artifact metrics
```

Projection phải có:

```text
source_output_set_id
source_content_hash
projection_schema_version
```

để biết nó được build từ đâu.

### D. Published Semantic State

Primary owner: Neo4j.

Ví dụ:

```text
Requirement node
semantic edge
published ontology classification
```

---

## 7. Ownership matrix

| Data object | Primary owner | Secondary representation |
|---|---|---|
| Source raw file | Object Store | Catalog DB URI/hash |
| SourceRevision identity | Catalog DB | raw object reference |
| Normalized document | Object Store | Catalog DB OutputSet metadata |
| Parsed document bundle | Object Store | Catalog DB metadata |
| Chunk/SourceUnit bundle | Object Store | queryable DB projection |
| Enrichment bundle | Object Store | optional queryable projection |
| StageExecution | Catalog DB | runtime correlation ref |
| StageInput | Catalog DB | input artifact URI resolves through OutputSet |
| OutputSlot / ArtifactSeries | Catalog DB | none |
| OutputSet | Catalog DB | points to StoredObjects |
| BaselineHistory | Catalog DB | none |
| AI recommendation | Catalog DB | detailed evidence may live Object Store |
| Human decision | Catalog DB | none |
| Publication record | Catalog DB | publication manifest in Object Store |
| Published semantic nodes/edges | Neo4j | provenance refs back to Catalog DB |

---

## 8. OutputSet and StoredObject boundary

Một `OutputSet` là logical coherent result của một execution.

Ví dụ:

```text
OUTSET-221
  ├── chunks.json
  ├── parsed-document.json
  └── diagnostics.json
```

Catalog DB giữ:

```text
OutputSet
  id
  output_slot_id
  producer_execution_id
  status
  schema_version
```

và:

```text
StoredObject
  id
  output_set_id
  role
  object_uri
  content_hash
```

Object Store giữ bytes thực tế.

Baseline phải trỏ tới `OutputSet`, không trỏ trực tiếp tới file path.

---

## 9. StageInput boundary

StageExecution không được có một field cố định kiểu:

```text
input_output_set_id
```

vì workflow có thể trở thành DAG/fan-in.

Dùng:

```text
StageInput
-----------
stage_execution_id
input_role
input_ref_type
input_ref_id
resolved_hash
ordinal
```

Ví dụ:

```text
StageExecution E-310

INPUT 1
role = PRIMARY_DOCUMENT
ref  = OUTSET-221

INPUT 2
role = TERMINOLOGY
ref  = OUTSET-044

INPUT 3
role = ONTOLOGY_SCHEMA
ref  = SCHEMA-03
```

Nhờ vậy DB không phụ thuộc topology workflow hiện tại.

---

## 10. Baseline ownership

Baseline là governance state trong Catalog DB.

Object Store không biết object nào là current baseline.

Neo4j cũng không phải owner của intermediate baseline.

Logical model:

```text
OutputSlot
   ├── OUTSET-A
   ├── OUTSET-B
   └── OUTSET-C
          ↑
     BaselineHistory
```

Baseline history append-only.

Current baseline là projection/query của history, không phải file `current`.

Concurrent baseline changes phải dùng optimistic concurrency hoặc equivalent compare-and-swap rule.

---

## 11. Publication boundary

Publication dùng exact baseline target.

```text
Publication
-----------
publication_id
source_revision_id
output_slot_id
baseline_id
output_set_id
status
previous_publication_id
published_at
```

Process:

```text
1. resolve exact baseline
2. read canonical artifact from Object Store
3. materialize semantic state into Neo4j idempotently
4. verify
5. write immutable publication manifest
6. activate publication in Catalog DB
```

Nếu publication fail:

```text
previous active publication remains valid
```

---

## 12. Runtime boundary

LangGraph/runtime không phải storage owner của ingestion governance.

Runtime giữ:

```text
checkpoint
current node
interrupt/resume
retry state
```

Catalog DB giữ:

```text
execution identity
registered output
baseline decision
publication state
```

Chỉ correlation bằng reference:

```text
processing_run.runtime_ref
stage_execution.runtime_ref
```

---

## 13. Duplication rules

Duplication chỉ được phép nếu có mục đích rõ ràng.

### Cho phép

```text
Object Store full artifact
+
Catalog DB searchable projection
```

nếu projection cần cho query/review.

### Không cho phép

Hai store cùng được coi là canonical cho cùng một state.

Ví dụ reject:

```text
chunks.json canonical
+
source_unit table cũng canonical
```

mà không có reconciliation rule.

Mỗi projection phải rebuild được từ canonical source.

---

## 14. Failure and reconciliation

Không dùng distributed transaction giữa Object Store, Catalog DB và Neo4j.

### Object written, DB registration failed

```text
→ orphan object
→ reconciliation/GC later
```

### DB registered, object missing/corrupt

```text
→ integrity error
→ output set cannot become baseline
```

### Publication partially writes Neo4j

```text
→ publication remains IN_PROGRESS/FAILED
→ rerun idempotently using same publication identity
→ active previous publication remains unchanged
```

System cần background reconciliation/job sau POC, nhưng schema phải hỗ trợ detection ngay từ đầu.

---

## 15. Technology independence

Logical ownership không phụ thuộc implementation.

POC:

```text
Catalog DB   = SQLite
Object Store = local filesystem / MinIO
Knowledge    = Neo4j
```

Scale-up:

```text
SQLite       → PostgreSQL
Filesystem   → S3/MinIO
Neo4j        → same adapter boundary
```

Domain contract giữ ổn định; physical schema/index/locking strategy có thể thay đổi theo engine.

---

## 16. Current ReqKB mapping

Workflow hiện tại chỉ là một mapping example:

| Generic concept | Current ReqKB example |
|---|---|
| StageExecution | classify / convert / parse / ontology |
| OutputSlot | classification / normalized document / chunks / enrichment |
| OutputSet | một candidate result của từng stage |
| Baseline | candidate được chọn để downstream consume |
| Publication | publish selected enriched output vào Neo4j |

Nếu workflow đổi, storage model không đổi.

---

## 17. Review checklist

Trước khi sang logical ERD, phải xác nhận:

- [ ] Mỗi data object có primary owner duy nhất.
- [ ] Canonical payload và queryable projection được phân biệt rõ.
- [ ] Projection có source hash/version để rebuild.
- [ ] Object Store không chứa governance semantics bằng folder name.
- [ ] Baseline thuộc Catalog DB.
- [ ] Baseline trỏ tới OutputSet, không trỏ file path.
- [ ] StageExecution hỗ trợ 0..N inputs.
- [ ] Publication pin exact baseline/output set.
- [ ] Neo4j chỉ chứa published semantic state.
- [ ] Runtime state không bị dùng thay governance state.
- [ ] Failure giữa các store có reconciliation strategy.
- [ ] Logical ownership không phụ thuộc SQLite/PostgreSQL/S3 implementation.

---

## 18. Handoff sang tài liệu tiếp theo

Tài liệu tiếp theo:

```text
03_logical_data_model.md
```

phải chuyển các invariant ở đây thành entity/relationship/cardinality cụ thể, đặc biệt:

```text
SourceAsset
SourceRevision
ProcessingRun
StageExecution
StageInput
OutputSlot
OutputSet
StoredObject
BaselineHistory
ReviewDecision
Publication
```

Chưa viết physical DDL trước khi logical model này được review qua Gate A–C của `00_database_review_methodology.md`.
