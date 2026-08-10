# ReqKB Ingestion Storage Boundary

**Status:** POC architecture baseline  
**Scope:** Storage ownership, System-of-Record boundary, consistency và publication visibility cho ReqKB ingestion  
**Depends on:** `00_database_review_methodology.md`, `01_design_methodology.md`

---

## 1. Purpose

Tài liệu này chốt **dữ liệu nào thuộc Object Store, Ingestion Catalog DB và ReqKB/Neo4j**, đồng thời định nghĩa các invariant giữa ba store.

Boundary phải giữ ổn định khi workflow thay đổi. Vì vậy tài liệu không model theo G0/G1/G2 cụ thể; các stage chỉ là producer/consumer của abstraction chung:

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

## 2. Rule ghi nhận architecture decision

Mọi decision có ảnh hưởng đến ownership, consistency, version semantics hoặc cross-store behavior phải ghi rõ:

```text
Context
→ Decision
→ Rationale
→ Consequence / Trade-off
```

Không chấp nhận decision dạng:

```text
"dùng X vì best practice"
```

mà không chỉ ra problem đang giải quyết.

### Khi nào phải tạo ADR riêng?

Tạo ADR khi decision:

- thay đổi System of Record;
- thay đổi consistency/publication semantics;
- khóa hệ thống vào một implementation khó đảo ngược;
- có từ hai phương án hợp lý trở lên với trade-off đáng kể;
- ảnh hưởng nhiều module/team hoặc downstream contract.

Các invariant ở tài liệu này là architecture baseline. Khi chọn **cách implement cụ thể** cho một invariant lớn, ADR phải ghi phương án được chọn và vì sao.

---

## 3. Ba storage concern

```text
Object Store
= canonical immutable payload/evidence

Ingestion Catalog DB
= identity, execution, lineage, governance, queryable projections

ReqKB / Neo4j
= published semantic knowledge
```

### Decision SB-01 — một state chỉ có một canonical owner

**Context:** cùng một dữ liệu có thể cần representation ở nhiều store để phục vụ replay, query hoặc semantic traversal.

**Decision:** một logical state chỉ có **một canonical owner**; representation ở store khác phải được định nghĩa là reference, projection hoặc materialization.

**Rationale:** nếu hai store cùng được coi là authoritative, reconciliation không còn deterministic khi dữ liệu lệch nhau.

**Trade-off:** phải duy trì provenance để rebuild projection/materialization từ canonical source.

---

## 4. Canonical data classes

Mỗi data object phải thuộc một trong bốn nhóm.

### A. Canonical Payload

Primary owner: **Object Store**.

Ví dụ:

```text
raw.xlsx
normalized.md
chunks.json
enriched.json
publication-manifest.json
```

### B. Canonical Governance Record

Primary owner: **Catalog DB**.

Ví dụ:

```text
StageExecution
OutputSlot
OutputSet registry
BaselineHistory
ReviewDecision
Publication
```

### C. Rebuildable Projection

Primary owner: artifact/record khác; Catalog DB chỉ giữ query model.

Ví dụ:

```text
SourceUnitProjection
validation summary
artifact metrics
```

Projection phải pin:

```text
source_output_set_id
source_content_hash
projection_schema_version
```

### D. Published Semantic State

Primary owner: **Neo4j/ReqKB** sau khi publication được activate.

Ví dụ:

```text
Requirement node
Function node
semantic edge
published ontology classification
```

---

## 5. Ownership matrix

| Data object | Primary owner | Secondary representation |
|---|---|---|
| Source raw file | Object Store | Catalog DB URI/hash |
| SourceRevision identity | Catalog DB | raw object reference |
| Normalized document | Object Store | OutputSet metadata |
| Parsed document bundle | Object Store | metadata/projection |
| Chunk/SourceUnit bundle | Object Store | queryable DB projection |
| Enrichment bundle | Object Store | optional projection |
| StageExecution | Catalog DB | runtime correlation ref |
| StageInput | Catalog DB | resolves exact input refs |
| OutputSlot / ArtifactSeries | Catalog DB | none |
| OutputSet registry | Catalog DB | points to StoredObjects |
| StoredObject bytes | Object Store | Catalog DB registry |
| BaselineHistory | Catalog DB | none |
| AI recommendation | Catalog DB | large evidence may live Object Store |
| Human decision | Catalog DB | none |
| Publication record | Catalog DB | manifest in Object Store |
| Published semantic nodes/edges | Neo4j | provenance refs to Catalog DB |

---

## 6. Object Store boundary

Object Store là System of Record cho **bytes và structured artifact payload**.

Ví dụ:

- raw Excel/DOCX/PDF;
- normalized Markdown;
- parsed/chunk bundles;
- enrichment bundles;
- diagnostics/evaluation evidence;
- publication manifest.

Không dùng object key như:

```text
/final/
/current/
/latest/
```

để biểu diễn governance state. Object key chỉ là storage location.

### Decision SB-02 — StoredObject immutable sau khi register

**Context:** cùng source có thể trải qua hàng trăm execution/reprocess; overwrite làm mất provenance và replayability.

**Decision:** một `StoredObject` sau khi register thành công là immutable. Reprocess tạo object mới.

**Rationale:** hash, lineage và historical comparison chỉ đáng tin nếu target không bị mutate sau registration.

**Trade-off:** storage tăng theo history; retention/GC phải xử lý riêng.

### Integrity lifecycle

Không coi object là usable ngay khi bắt đầu upload.

Logical lifecycle:

```text
WRITING
  ↓
WRITTEN
  ↓ verify existence/hash/schema
VERIFIED
  ↓ register as member of OutputSet
AVAILABLE
```

Một `OutputSet` chỉ được **eligible for baseline** khi mọi required `StoredObject` đã `VERIFIED/AVAILABLE`.

### Decision SB-03 — verify trước baseline eligibility

**Context:** nếu Catalog DB expose OutputSet trước khi object upload/hash/schema hoàn tất, reviewer hoặc downstream stage có thể chọn artifact chưa usable.

**Decision:** baseline eligibility phụ thuộc integrity check của toàn bộ required object trong OutputSet.

**Rationale:** loại race condition giữa storage write và governance selection.

**Trade-off:** cần explicit status/integrity metadata và reconciliation cho incomplete writes.

---

## 7. Ingestion Catalog DB boundary

Catalog DB là System of Record cho:

### Identity

```text
SourceAsset
SourceRevision
ProcessingRun
StageExecution
OutputSlot
OutputSet registry
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

Catalog DB có thể giữ projection phục vụ:

- diff;
- search/filter;
- validation;
- review UI;
- lineage query;
- stale detection.

Ví dụ:

```text
SourceUnitProjection
--------------------
source_unit_id
output_set_id
unit_type
ordinal
heading_path
content_hash
text_excerpt / text_ref
```

### Decision SB-04 — Object artifact canonical, relational content projection rebuildable

**Context:** SourceUnit/chunk cần query nhanh nhưng full parser artifact cũng cần replay chính xác.

**Decision:** full artifact trong Object Store là canonical payload; `SourceUnitProjection` trong Catalog DB là rebuildable query projection.

**Rationale:** tránh hai canonical copies trong khi vẫn giữ khả năng diff/search/review bằng SQL.

**Trade-off:** phải có projection build/reconcile process.

Nếu hai representation khác nhau:

```text
Object Store artifact wins
→ projection rebuild/reconcile
```

---

## 8. OutputSet, OutputSlot và StageInput boundary

### OutputSet

`OutputSet` là một coherent logical result của một execution.

```text
OUTSET-221
  ├── chunks.json
  ├── parsed-document.json
  └── diagnostics.json
```

Catalog DB giữ logical registry; Object Store giữ bytes.

Baseline trỏ tới `OutputSet`, không trỏ file path.

### OutputSlot / ArtifactSeries

`OutputSlot` trả lời:

> Các OutputSet này là các revision/candidate của logical artifact nào?

Ví dụ:

```text
OutputSlot = CHUNK_SET for REV-003
   ├── OUTSET-187
   ├── OUTSET-221
   └── OUTSET-240
```

### StageInput

StageExecution phải hỗ trợ 0..N inputs thay vì một fixed `input_output_set_id`.

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

PRIMARY_DOCUMENT → OUTSET-221
TERMINOLOGY      → OUTSET-044
ONTOLOGY_SCHEMA  → SCHEMA-03
```

### Decision SB-05 — multi-input generic lineage

**Context:** workflow hiện tại có thể tuyến tính nhưng tương lai có DAG/fan-in hoặc stage cần nhiều context nguồn.

**Decision:** model input như collection có role, không hard-code một upstream FK.

**Rationale:** giữ persistence model ổn định khi workflow topology thay đổi.

**Trade-off:** logical model linh hoạt hơn nhưng physical schema phải vẫn bảo vệ referential integrity; không được triển khai thành free-form `type + string id` không constraint.

`03_logical_data_model.md` phải chốt controlled reference model cho `StageInput`.

---

## 9. Baseline ownership và stale semantics

Baseline là governance state trong Catalog DB.

```text
OutputSlot
   ├── OUTSET-A
   ├── OUTSET-B
   └── OUTSET-C
          ↑
     BaselineHistory
```

Baseline history append-only. Current baseline là query/projection của history.

Concurrent baseline changes phải dùng optimistic concurrency / compare-and-swap, không last-write-wins.

### Decision SB-06 — baseline change làm downstream derivation detectably stale

**Context:** downstream OutputSet được tạo từ exact upstream input. Khi upstream baseline đổi, output cũ vẫn là historical evidence hợp lệ nhưng không còn đại diện cho current lineage.

**Decision:** Catalog layer phải có khả năng xác định downstream derivation là `STALE` hoặc derive stale state từ lineage.

**Rationale:** nếu không có stale semantics, workflow có thể tiếp tục sử dụng artifact được sinh từ baseline cũ mà user không biết.

**Trade-off:** cần lineage query/event processing; không tự động đồng nghĩa phải rerun ngay.

Responsibility boundary:

```text
Catalog DB/domain
= xác định artifact nào stale

Runtime/orchestrator
= quyết định/schedule rerun theo policy
```

---

## 10. Publication và ReqKB visibility

Neo4j chỉ chứa semantic knowledge đã qua Publication boundary.

Neo4j không phải:

- parser scratchpad;
- intermediate candidate store;
- workflow state store;
- review queue;
- baseline history store.

Publication pin exact baseline/output set:

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

### Publication process

```text
1. resolve exact baseline
2. read canonical artifact from Object Store
3. materialize candidate semantic state idempotently
4. verify candidate materialization
5. write immutable publication manifest
6. activate publication
7. supersede previous publication where applicable
```

### Decision SB-07 — publication phải invisible cho downstream cho tới activation

**Context:** write Neo4j có thể partial-fail. Nếu downstream nhìn thấy nodes/edges mới trước khi verify/activate, active ReqKB có thể bị contamination dù Catalog DB vẫn giữ publication cũ active.

**Decision:** semantic changes của publication mới **không được trở thành visible active knowledge trước activation**.

**Rationale:** giữ atomicity ở business/read semantics dù không có distributed transaction.

**Trade-off:** cần version/namespace/shadow-write strategy trong Neo4j.

Tài liệu này **không chốt implementation**. Các phương án có thể gồm:

```text
A. publication_id/version tagging + active-filter
B. shadow namespace/subgraph rồi switch pointer
C. versioned semantic records + release activation
```

Khi chọn A/B/C phải tạo ADR riêng vì đây là cross-store consistency decision dài hạn.

### Decision SB-08 — Publication khác KnowledgeState/Release

**Context:** ReqKB có thể đồng thời chứa active knowledge từ nhiều SourceRevision. Một publication thường chỉ cập nhật một phần của knowledge base.

**Decision:** `Publication` biểu diễn một publish operation/change; khái niệm **whole-ReqKB active state** (`KnowledgeState`/`KnowledgeRelease`) là concept khác.

**Rationale:** tránh coi một document-level publication là identity của toàn bộ KB state.

**Trade-off:** POC có thể chưa cần materialize `KnowledgeRelease`, nhưng logical model không được khóa publication thành aggregate root của toàn ReqKB.

Nếu downstream sau này cần reproducible snapshot của toàn ReqKB, `KnowledgeState/Release` phải được thiết kế riêng và có ADR nếu semantics phức tạp.

---

## 11. Runtime boundary

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
stale state
publication state
```

Chỉ correlation bằng reference:

```text
processing_run.runtime_ref
stage_execution.runtime_ref
```

### Decision SB-09 — runtime state tách khỏi governance state

**Context:** runtime framework có thể thay đổi, checkpoint có lifecycle/retention khác business governance record.

**Decision:** checkpoint không là System of Record cho baseline/publication/lineage.

**Rationale:** persistence governance phải sống được khi thay LangGraph hoặc rehydrate workflow bằng runtime khác.

**Trade-off:** phải duy trì correlation giữa runtime execution và domain execution.

---

## 12. Cross-store consistency và reconciliation

Không dùng distributed transaction giữa Object Store, Catalog DB và Neo4j.

### Decision SB-10 — explicit state transition + idempotency + reconciliation

**Context:** ba store có transaction model khác nhau; distributed transaction làm tăng coupling và operational complexity cho POC/pilot.

**Decision:** dùng explicit status transitions, idempotent operations, integrity verification và reconciliation.

**Rationale:** failure trở thành observable/recoverable state thay vì cố đạt atomic transaction xuyên nhiều technology.

**Trade-off:** hệ thống phải có reconciliation/GC process và transient inconsistency phải được model rõ.

### Failure cases

**Object written, DB registration failed**

```text
→ orphan object
→ reconciliation/GC
```

**DB registered, object missing/corrupt**

```text
→ integrity error
→ OutputSet not eligible for baseline
```

**Publication partially writes Neo4j**

```text
→ new publication remains non-active
→ retry/repair idempotently
→ previous active knowledge remains visible
```

Schema phải hỗ trợ detection từ đầu; automated reconciliation job có thể triển khai sau POC.

---

## 13. Security / workspace boundary

Storage boundary phải có logical isolation scope ngay từ đầu.

```text
Workspace / Project
   ├── SourceAsset
   ├── SourceRevision
   ├── StageExecution
   ├── OutputSlot / OutputSet
   ├── Baseline
   └── Publication
```

### Decision SB-11 — mọi persistence object phải thuộc một isolation scope

**Context:** ReqKB app có thể phục vụ nhiều project/workspace; nếu scope không tồn tại trong logical model, thêm multi-project sau này sẽ gây data-leak risk và migration lớn.

**Decision:** mọi governed object phải resolve được về `workspace_id/project_id` hoặc equivalent tenant boundary.

**Rationale:** authorization và storage isolation phải có anchor ở data model, không chỉ dựa vào UI filtering.

**Trade-off:** thêm scope propagation vào keys/queries; POC single-project vẫn phải giữ conceptual field/boundary.

Implementation của IAM/RLS/Neo4j tenant isolation nằm ngoài scope doc này.

---

## 14. Technology independence

Logical ownership không phụ thuộc implementation.

POC:

```text
Catalog DB   = SQLite
Object Store = local filesystem / MinIO
Knowledge    = Neo4j
```

Scale-up có thể:

```text
SQLite       → PostgreSQL
Filesystem   → S3/MinIO
```

Domain contract giữ ổn định; physical schema/index/locking/isolation strategy được phép khác theo engine.

### Decision SB-12 — portability ở contract, không phải physical schema

**Rationale:** SQLite và PostgreSQL có concurrency, locking, indexing và migration capability khác nhau. Ép physical design giống hệt nhau tạo false portability.

---

## 15. Current ReqKB mapping

Workflow hiện tại chỉ là mapping example:

| Generic concept | Current ReqKB example |
|---|---|
| StageExecution | classify / convert / parse / ontology |
| OutputSlot | classification / normalized document / chunks / enrichment |
| OutputSet | một candidate result của stage |
| Baseline | candidate được chọn để downstream consume |
| Publication | publish selected semantic candidate vào ReqKB |

Nếu workflow đổi, storage model không đổi.

---

## 16. Architecture invariants

Các invariant sau phải được giữ khi sang logical/physical design:

```text
INV-01
Một logical state chỉ có một canonical owner.

INV-02
Historical payload/output không overwrite; reprocess tạo revision/output mới.

INV-03
OutputSet không eligible for baseline trước khi required objects pass integrity verification.

INV-04
Baseline luôn pin exact OutputSet, không suy ra từ latest/file path.

INV-05
Upstream baseline change phải làm downstream derivation detectably stale.

INV-06
Publication mới không visible như active knowledge trước activation.

INV-07
Publication operation và whole-ReqKB active state là hai concept khác nhau.

INV-08
Runtime checkpoint không là governance System of Record.

INV-09
Cross-store failure phải observable và recoverable bằng idempotency/reconciliation.

INV-10
Mọi governed object phải thuộc một workspace/project isolation scope.
```

---

## 17. ADR candidates / triggers

Không cần ADR cho mọi field/table. Các điểm sau **bắt buộc ADR trước implementation decision cuối cùng**:

| Topic | Vì sao cần ADR |
|---|---|
| Neo4j publication visibility strategy | Có nhiều phương án đúng, ảnh hưởng query semantics và rollback |
| Whole-ReqKB `KnowledgeState/Release` semantics | Ảnh hưởng reproducibility của Stage 2/3 và multi-document state |
| StageInput physical reference strategy | Cần cân bằng extensibility với relational referential integrity |
| Tenant/workspace isolation implementation | Ảnh hưởng security, query model và physical key/index design |

ADR phải ghi ít nhất:

```text
Context
Options considered
Decision
Why this option
Rejected alternatives and why
Consequences
Migration / rollback implication
```

---

## 18. Review checklist

Trước khi sang logical ERD:

- [ ] Mỗi data object có primary owner duy nhất.
- [ ] Canonical payload và query projection được phân biệt rõ.
- [ ] Projection có source hash/version để rebuild.
- [ ] StoredObject lifecycle ngăn incomplete artifact trở thành baseline.
- [ ] Baseline trỏ tới OutputSet, không trỏ file path/latest.
- [ ] Baseline update có concurrency semantics.
- [ ] StageExecution hỗ trợ 0..N inputs nhưng vẫn có plan bảo vệ referential integrity.
- [ ] Baseline change có stale semantics cho downstream lineage.
- [ ] Publication pin exact baseline/output set.
- [ ] Publication mới không visible trước activation.
- [ ] Publication và whole-KB state không bị nhập làm một.
- [ ] Neo4j chỉ chứa published semantic state.
- [ ] Runtime state tách khỏi governance state.
- [ ] Cross-store failure có reconciliation strategy.
- [ ] Workspace/project isolation có anchor trong data model.
- [ ] Mọi architecture decision lớn có rationale/trade-off; implementation choice lớn có ADR trigger.

---

## 19. Handoff sang tài liệu tiếp theo

`03_logical_data_model.md` phải chuyển các invariant trên thành entity, relationship, cardinality và constraint cụ thể:

```text
Workspace / Project
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

Ngoài ra `03` phải làm rõ:

1. controlled reference model cho `StageInput`;
2. integrity/eligibility state của OutputSet;
3. optimistic concurrency cho baseline;
4. stale lineage representation;
5. relation giữa Publication và future KnowledgeState/Release;
6. workspace/project scoping.

Chưa viết physical DDL trước khi logical model được review qua Gate A–C của `00_database_review_methodology.md`.
