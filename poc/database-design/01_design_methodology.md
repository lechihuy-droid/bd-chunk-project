# ReqKB Ingestion Database Design Methodology

**Status:** POC architecture baseline  
**Scope:** Persistence và version governance cho ReqKB ingestion  
**Audience:** System Architect, Database Engineer, AI Engineer, Backend Engineer, Coding Agent  
**Goal:** Định nghĩa data architecture độc lập với workflow cụ thể, đủ ổn định khi các step, tool hoặc orchestration thay đổi.

---

## 1. Mục tiêu và phạm vi

Tài liệu này định nghĩa **phương pháp luận thiết kế database/persistence**, không định nghĩa chi tiết workflow ingestion.

Workflow hiện tại có thể gồm classification, conversion, parsing, validation, ontology enrichment, review và publication. Các step này có thể thay đổi mà không được buộc core persistence model phải redesign.

Database architecture chỉ model các khái niệm ổn định:

```text
Source Asset
    ↓
Source Revision
    ↓
Processing Run / Stage Execution
    ↓
Immutable Output Revision
    ↓
Baseline Selection
    ↓
Publication
```

Stage 2 Assessment, retrieval, Gen BD, MLflow experiment tracking và BD artifact governance nằm ngoài scope.

---

## 2. Nguyên tắc thiết kế

### 2.1 Data lifecycle trước, workflow sau

Thứ tự thiết kế:

```text
Data lifecycle
  → Business identity
    → Version semantics
      → Ownership / System of Record
        → Governance transitions
          → Logical model
            → Physical schema
```

Không tạo table trực tiếp từ danh sách node G0/G1/G2 hiện tại.

### 2.2 Execution, artifact, baseline và publication là bốn khái niệm khác nhau

```text
Execution
    ↓ creates
Output Revision
    ↓ may become
Baseline
    ↓ may be
Published
```

Execution `SUCCEEDED` không có nghĩa output đã được tin dùng. Baseline cũng chưa đồng nghĩa đã publish vào ReqKB.

### 2.3 Immutable target, explicit mutable decision

Historical evidence phải append-only:

- Source Revision;
- completed execution facts;
- OutputSet và StoredObject;
- content hash và resolved configuration;
- review/selection decision;
- publication history.

Current state phải được biểu diễn bằng pointer/state rõ ràng, không overwrite historical artifact.

Không dùng `latest`, `/final`, `current.json` làm governance semantics.

### 2.4 Một loại state có một primary owner

Một dữ liệu có thể có reference/projection ở nhiều hệ thống, nhưng phải xác định rõ canonical owner.

---

## 3. Canonical data lifecycle

```text
SourceAsset
   └── SourceRevision
           │
           ├── ProcessingRun
           │      └── StageExecution
           │             ├── StageInput [0..N]
           │             └── OutputSet
           │                    └── StoredObject [1..N]
           │
           └── OutputSlot / ArtifactSeries
                    ├── OutputSet revision A
                    ├── OutputSet revision B
                    └── OutputSet revision C
                              ↑
                         BaselineHistory
                              │
                        Review / Policy
                              │
                         Publication
```

Model này phải support được linear pipeline, DAG, fan-in/fan-out, retry và việc thay đổi stage mà không cần thêm foreign key theo từng workflow node.

---

## 4. Core domain identities

### 4.1 SourceAsset

Business identity ổn định của một nguồn/tài liệu.

```text
SOURCE-001 = Customer Management Requirement Definition
```

### 4.2 SourceRevision

Immutable content revision của SourceAsset.

```text
SOURCE-001
  ├── REV-001 hash=A
  ├── REV-002 hash=B
  └── REV-003 hash=C
```

Raw bytes nằm ở Object Store. Catalog DB giữ identity, hash, URI, type, timestamps và source metadata.

### 4.3 ProcessingRun

Correlation container cho một lần processing/workflow invocation.

Nó **không phải owner của baseline/final state**.

### 4.4 StageExecution

Một lần execution của một processing capability.

```text
stage_execution_id
processing_run_id
stage_type
component_ref
configuration_hash
status
started_at
completed_at
runtime_ref
```

`stage_type` như `CONVERT`, `PARSE`, `ONTOLOGY` chỉ là data/configuration, không phải lý do để tạo table riêng.

### 4.5 StageInput

Một StageExecution có thể consume 0, 1 hoặc nhiều exact input.

```text
stage_execution_input
---------------------
stage_execution_id
input_role
input_ref_type
input_ref_id
input_hash
```

Không dùng một cột `input_output_set_id` cố định vì sẽ coupling schema với linear workflow và không support fan-in.

### 4.6 OutputSet

Immutable coherent result được tạo bởi một StageExecution.

```text
OUTSET-221
  ├── parsed-document.json
  ├── chunks.json
  └── diagnostics.json
```

Các artifact thuộc cùng một result phải được version/select cùng nhau.

### 4.7 StoredObject

Physical payload thuộc một OutputSet.

```text
stored_object_id
output_set_id
object_role
object_uri
content_hash
schema_version
media_type
```

### 4.8 OutputSlot / ArtifactSeries

Stable identity của **thứ đang được version**.

```text
SLOT-17
source_revision = REV-003
logical_role = CHUNK_SET
```

Một slot có thể có hàng trăm candidate revision:

```text
SLOT-17
  ├── OUTSET-187
  ├── OUTSET-221  ← baseline
  └── OUTSET-240
```

Nếu thiếu OutputSlot/ArtifactSeries, baseline chỉ trả lời “chọn output nào” nhưng không trả lời “baseline của object nào”.

### 4.9 BaselineHistory

Append-only governance record chọn một OutputSet cho một OutputSlot.

```text
baseline_id
output_slot_id
output_set_id
effective_from
effective_to
selection_mode
review_decision_id
created_at
```

`latest output != baseline`.

### 4.10 ReviewDecision

Ghi lại quyết định selection của human/policy và evidence AI recommendation nếu có.

AI có thể recommend; authority do policy quyết định.

### 4.11 Publication

Boundary materialize một accepted baseline sang canonical downstream store, ví dụ Neo4j ReqKB.

Publication tách khỏi execution và baseline selection.

---

## 5. Version và baseline semantics

### 5.1 Không dùng một generic `version` cho mọi thứ

- SourceRevision: source content thay đổi.
- OutputSet revision: execution mới tạo candidate mới.
- Schema version: output contract thay đổi.
- Component/config version: producer behavior thay đổi.
- Baseline revision: governance selection thay đổi.
- Publication revision: canonical published state thay đổi.

### 5.2 Downstream pin exact input

StageExecution không được hiểu là “dùng latest output trước đó”.

Nó phải ghi exact StageInput reference + hash. Nhờ vậy lineage không đổi dù baseline sau đó thay đổi.

### 5.3 Baseline change là append-only

```text
BASE-008 → OUTSET-187   effective T1..T2
BASE-009 → OUTSET-221   effective T2..∞
```

Không update một row baseline duy nhất mãi mãi.

### 5.4 Baseline concurrency phải explicit

Hai actor/process có thể approve cùng một OutputSlot đồng thời.

Dùng optimistic concurrency hoặc equivalent DB constraint:

```text
expected_baseline_version = 8
approve OUTSET-230
→ baseline version 9
```

Write khác vẫn expect version 8 phải fail `CONFLICT`, không last-write-wins.

### 5.5 Selection và publication là hai transition khác nhau

Intermediate artifacts dùng **Baseline Selection**.

Boundary sang ReqKB dùng **Publication/Promotion**.

---

## 6. Storage ownership

### 6.1 Object Store — canonical immutable payload

Primary owner của:

- original DOCX/PDF/XLSX;
- normalized/converted file;
- full parser output;
- chunk bundle;
- enrichment bundle;
- diagnostics/evaluation evidence lớn;
- publication manifest.

Object key chỉ là location, không thể hiện current/final state.

Recommended generic layout:

```text
reqkb/
└── projects/{project_id}/
    └── sources/{source_asset_id}/
        ├── revisions/{source_revision_id}/raw/...
        └── runs/{processing_run_id}/
            └── stages/{stage_execution_id}/...
```

### 6.2 Ingestion Catalog DB — identity, governance, lineage và queryable projection

Primary owner của:

- source/revision identity;
- ProcessingRun/StageExecution facts;
- StageInput lineage;
- OutputSlot, OutputSet, StoredObject registry;
- baseline history;
- review/selection decision;
- publication lifecycle;
- resolved component/config/schema references;
- queryable projection cần cho operations/review.

### 6.3 Queryable projection

Một số artifact lớn cần relational projection để diff/review/query hiệu quả.

Ví dụ chunk/SourceUnit có thể được project vào Catalog DB trong khi full immutable `chunks.json` vẫn canonical ở Object Store.

Rule:

> **Object artifact là source of truth; relational projection là rebuildable.**

Projection row phải giữ source OutputSet/StoredObject ID và content hash để detect divergence và rebuild.

### 6.4 Knowledge Store / Neo4j

Primary owner chỉ cho semantic knowledge đã qua Publication boundary.

Neo4j không phải scratch/staging store cho processing execution.

---

## 7. Lineage và reproducibility

Minimum lineage chain:

```text
SourceRevision
   ↓
StageInput(s)
   ↓
StageExecution
   ↓
OutputSet
   ↓
OutputSlot
   ↓
BaselineDecision
   ↓
Publication
```

Completed StageExecution phải pin đủ producer identity để explain/reproduce behavior:

```text
component_ref
code/version ref
configuration_hash
schema_version
ruleset_ref (nếu có)
model_ref / prompt_ref / trace_ref (nếu dùng AI)
```

AI metadata chỉ là extension của execution model, không làm thay đổi persistence architecture.

---

## 8. Consistency, failure và lifecycle rules

### 8.1 Không tạo distributed transaction giả

Không cố transaction xuyên Object Store + relational DB + Neo4j.

Dùng explicit state transition, idempotency, reconciliation và verification.

Register output:

```text
1. write immutable payload
2. compute/verify hash
3. register OutputSet + StoredObject
4. mark StageExecution SUCCEEDED
```

Nếu DB registration fail, object chưa register trở thành orphan candidate để reconciliation/GC xử lý.

### 8.2 Failed execution không phá current baseline

Retry/reprocess fail phải giữ baseline trước đó.

### 8.3 Upstream baseline change tạo staleness, không rewrite history

Downstream executions sinh từ baseline cũ vẫn là historical fact. Application có thể mark derived state stale và recommend/schedule reprocess nhưng không sửa provenance cũ.

### 8.4 Retry và intentional reprocess khác nhau

Retry tránh duplicate side effect cho cùng operation.

Intentional reprocess tạo StageExecution mới và thường tạo OutputSet mới dù source bytes không đổi.

---

## 9. Technology portability

Logical model không được phụ thuộc PostgreSQL-specific feature.

POC có thể dùng:

```text
Catalog DB: SQLite
Object Store: local filesystem hoặc S3-compatible adapter
Knowledge Store: Neo4j
Runtime: LangGraph
```

Scale-up có thể đổi SQLite → PostgreSQL.

Portability nghĩa là **domain/application contract ổn định**. Physical schema, index, locking, isolation, JSON support, pooling, HA và migration strategy có thể khác theo engine.

Recommended boundaries:

```text
CatalogRepository
ObjectStore
KnowledgePublisher
```

Runtime checkpoint và UI state không trở thành domain model của Catalog DB.

---

## 10. Mapping vào ReqKB workflow hiện tại

Workflow hiện tại chỉ là implementation mapping:

| Generic concept | Current ReqKB example |
|---|---|
| SourceRevision | uploaded Excel/DOCX/PDF revision |
| StageExecution | classify / convert / parse / ontology |
| StageInput | raw source, selected normalized document, selected chunk set |
| OutputSlot | classification, normalized document, chunk set, enriched chunk set |
| OutputSet revision | một candidate từ một execution |
| BaselineHistory | candidate được chọn cho một OutputSlot |
| ReviewDecision | auto / AI-recommended / human-approved selection |
| Publication | publish selected enriched representation vào Neo4j ReqKB |

Nếu ngày mai workflow bỏ conversion, thêm validator, split ontology hoặc chạy parallel, core persistence model vẫn phải giữ nguyên.

---

## 11. Architecture acceptance checklist

Chưa được đi sang physical schema nếu chưa trả lời rõ:

- [ ] Stable business identity của từng versioned object là gì?
- [ ] Event nào tạo revision mới?
- [ ] Execution identity có tách khỏi artifact identity không?
- [ ] Mỗi candidate có thuộc một OutputSlot/ArtifactSeries không?
- [ ] StageExecution có support nhiều exact input không?
- [ ] Historical outputs có immutable không?
- [ ] Current baseline có explicit governance record thay vì `latest` không?
- [ ] Baseline history có audit được và concurrency-safe không?
- [ ] Có reconstruct lineage từ SourceRevision đến Publication không?
- [ ] System of Record của mọi representation đã rõ chưa?
- [ ] Relational projection có rebuild được từ canonical artifact không?
- [ ] Failed/retry execution có thể xảy ra mà không corrupt baseline không?
- [ ] Publication có tách khỏi intermediate selection không?
- [ ] Workflow stage thay đổi có tránh core schema redesign không?
- [ ] SQLite/PostgreSQL có nằm sau stable repository contract trong khi physical design vẫn được phép engine-specific không?

Chỉ sau khi các điểm này ổn định mới chốt `02_storage_boundary.md`, logical ERD và physical schema.
