# ReqKB Ingestion Database Design Methodology

**Status:** POC architecture baseline  
**Scope:** Stage 1 — ReqKB ingestion only  
**Audience:** System Architect, AI Engineer, Backend Engineer, Coding Agent, Product/UI Engineer  
**Goal:** Định nghĩa phương pháp luận quản lý source, execution run, intermediate outputs, baseline selection và promotion từ input document vào ReqKB.

---

## 1. Scope của tài liệu

Tài liệu này chỉ thiết kế persistence và version governance cho **Stage 1 — Ingestion**.

```text
STAGE 1 — INGESTION

Input Document
      ↓
G0 — Intake / Classification / Marking
      ↓
G1A — Convert / Normalize when needed
      ↓
G1B — Parse / Build Chunks (SourceUnits)
      ↓
G2 — Light Ontology Enrichment
      ↓
G3 — Promotion / Publish
      ↓
ReqKB
```

Các phase sau nằm ngoài scope:

```text
STAGE 2 — Assessment
ReqKB → requirement quality/readiness assessment

STAGE 3 — Retrieval & Generation
ReqKB + Assessment → Retrieve Context → Generate BD
```

MLflow, BD artifact governance, prompt evaluation và generation trace không thuộc core persistence model của tài liệu này.

---

## 2. Vấn đề cần giải quyết

Một input Excel/DOCX/PDF có thể được xử lý hàng chục hoặc hàng trăm lần:

```text
REV-003
  ├── convert run 001 → MD-A
  ├── convert run 002 → MD-B
  ├── convert run 003 → MD-C
  └── ...
```

Sau đó mỗi MD lại có thể được parse nhiều lần:

```text
MD-B
  ├── parse run 101 → ChunkSet-A
  ├── parse run 102 → ChunkSet-B
  └── parse run 103 → ChunkSet-C
```

Vấn đề không chỉ là lưu tất cả output. Hệ thống phải luôn trả lời được:

1. Source revision nào đang được xử lý?
2. Có những execution run nào đã xảy ra?
3. Mỗi run tạo output gì và output nằm ở đâu?
4. Output nào hiện được coi là **chuẩn** để stage sau sử dụng?
5. Ai hoặc policy nào đã chọn output đó?
6. AI đã recommend candidate nào và dựa trên evidence nào?
7. Output chuẩn hiện tại được tạo từ input/run/component version nào?
8. Candidate nào cuối cùng được publish vào ReqKB?

Do đó ingestion cần **version governance cho intermediate artifacts**, không chỉ version ở output cuối.

---

## 3. Core mental model

Phân biệt bốn khái niệm:

```text
Execution
    ↓
Candidate Output
    ↓
Selection / Baseline
    ↓
Next Stage
```

và ở boundary cuối:

```text
G2 Baseline
    ↓
G3 Promotion
    ↓
Canonical ReqKB
```

### 3.1 Run

`Run` / `StageRun` là một lần execution.

Nó trả lời:

> Hệ thống đã chạy cái gì, khi nào, bằng component/config nào, trên input nào?

### 3.2 Output

`StageOutput` / `OutputSet` là kết quả immutable do run tạo ra.

Nó trả lời:

> Execution đó đã sản xuất artifact nào?

### 3.3 Baseline

`StageBaseline` là output đã được chấp nhận làm input chuẩn cho stage tiếp theo.

Nó trả lời:

> Trong nhiều candidate output, workflow hiện đang tin dùng output nào?

### 3.4 Promotion

`Promotion` chỉ dùng cho việc publish G2 baseline vào canonical ReqKB.

Nó trả lời:

> Candidate đã được chấp nhận và materialize vào ReqKB chưa?

**Run thành công không đồng nghĩa output được baseline. Baseline không đồng nghĩa đã được promote vào ReqKB.**

---

## 4. Nguyên tắc thiết kế nền tảng

### 4.1 Lifecycle-first, schema-second

Thứ tự thiết kế:

```text
Workflow lifecycle
  → Data states
    → Ownership
      → Identity
        → Version semantics
          → Governance transition
            → Logical model
              → Physical schema
```

Không bắt đầu bằng việc chọn PostgreSQL/SQLite rồi tạo bảng theo output hiện tại.

### 4.2 Immutable targets, mutable/current pointers

Các historical targets phải immutable:

- Source Revision;
- completed Stage Run facts;
- Output Set;
- content hash;
- component/config version;
- baseline decision history;
- promotion history.

Thứ được phép thay đổi là pointer/state hiện tại:

- current baseline;
- review status;
- current active promotion;
- runtime status.

Không overwrite artifact cũ bằng `current.json` hoặc `final.json`.

### 4.3 Latest không có nghĩa là baseline

Ví dụ:

```text
OUT-220 PASS
OUT-221 PASS  ← current baseline
OUT-222 PASS  ← newest
```

Stage sau vẫn phải dùng `OUT-221` cho đến khi có một baseline decision mới.

### 4.4 Baseline là governance decision

Baseline không được suy ra từ file name, timestamp hoặc `MAX(run_id)`.

Baseline phải có explicit record cho biết:

- candidate nào được chọn;
- decision được tạo bởi ai/policy nào;
- AI recommendation là gì;
- reason/evidence;
- thời điểm có hiệu lực;
- baseline trước đó là gì.

### 4.5 Promotion tách khỏi G2

Không dùng pattern:

```text
G2 ontology output → write active Neo4j immediately
```

G2 phải tạo candidate/baseline trước. G3 là boundary publication riêng.

---

## 5. Workflow chuẩn của Stage 1

```text
Input
  ↓
Source Revision
  ↓
G0 Intake / Classification
  ↓
G0 selection policy
  ↓
G1A Convert / Normalize
  ↓
Convert OutputSet candidates
  ↓
Convert Baseline Gate
  ↓
G1B Parse / Chunk
  ↓
ChunkSet candidates
  ↓
Parse Baseline Gate
  ↓
G2 Light Ontology Enrichment
  ↓
Enriched ChunkSet candidates
  ↓
Ontology Baseline Gate
  ↓
G3 Promotion / Publish
  ↓
ReqKB
```

Baseline gate không nhất thiết dừng human ở mọi stage. Gate luôn tồn tại ở logical level nhưng policy có thể auto-select.

---

## 6. G0 — Intake / Classification / Marking

G0 không parse nội dung sâu. Mục tiêu là xác định cách tài liệu sẽ được xử lý.

Ví dụ output:

```text
source_revision = REV-003
file_type = XLSX
document_role = REQUIREMENT_DEFINITION
language = JA
parser_profile = excel_rd
classification_confidence = 0.97
```

G0 có thể sử dụng:

- file extension / MIME type;
- source location;
- naming convention;
- project metadata;
- lightweight AI classification khi role không rõ.

### G0 selection policy

Thông thường:

```text
file type deterministic + role confidence high
→ AUTO_SELECT
```

Nếu document role không chắc chắn:

```text
AI recommendation
→ human review
→ approve classification baseline
```

Raw bytes vẫn nằm Object Store. Classification state là queryable governance data trong Ingestion Catalog DB.

---

## 7. G1A — Convert / Normalize

Không phải format nào cũng cần convert. Ví dụ Excel có thể được normalize thành Markdown/structured representation trước khi chunking.

```text
REV-003 XLSX
    ↓
Convert Run C-001
    ↓
document.md
```

Nhiều run có thể tạo nhiều candidate:

```text
C-001 → MD-A
C-002 → MD-B
C-003 → MD-C
```

Object Store giữ tất cả. `ConvertBaseline` xác định candidate nào G1B phải consume.

Stage sau **không được lấy latest MD**.

---

## 8. G1B — Parse / Chunk

Parser consume exact Convert Baseline hoặc raw source baseline nếu conversion không cần thiết.

```text
input_output_set = MD-B
       ↓
Parse Run P-103
       ↓
ChunkSet-103
```

Chunk/SourceUnit là đơn vị processing quan trọng của ReqKB.

Ví dụ:

```text
SU-001
unit_type = HEADING
heading_path = ["3", "3.1"]
text = "Customer Search"

SU-002
unit_type = REQUIREMENT_TEXT
text = "User can search customer by name"
```

### SourceUnit persistence rule

Giữ hai representation khác nhau:

```text
Object Store
= full immutable parser artifact / parsed-document.json / chunks.json

Ingestion Catalog DB
= queryable SourceUnit projection cần cho diff, validation, review và lineage
```

Không bắt buộc relational DB trở thành canonical full-text document store; nhưng SourceUnit identity/hash/structure phải query được mà không phải deserialize toàn bộ historical artifact mỗi lần.

---

## 9. G2 — Light Ontology Enrichment

G2 enrich SourceUnit để ReqKB có semantic structure đủ dùng cho Assessment/Retrieval sau này.

Ví dụ:

```text
SU-002
  semantic_type = FUNCTIONAL_REQUIREMENT
  domain = CUSTOMER
  capability = SEARCH
  modality = CAN
```

Có thể thêm lightweight relations:

```text
SU-002 ──belongs_to──> Customer Search
SU-003 ──constrains──> SU-002
```

G2 **không được mặc định coi là full ontology construction engine**.

Output là `EnrichedChunkSet` candidate.

Nếu G2 dùng LLM, vẫn áp dụng cùng governance model:

```text
StageRun
→ Candidate OutputSet
→ AI/Rule Evaluation
→ Baseline Gate
```

Có thể pin thêm:

```text
model_ref
prompt_ref
ruleset_ref
ontology_schema_version
configuration_hash
trace_ref (optional)
```

MLflow có thể tích hợp sau cho AI trace/evaluation nhưng không phải owner của ingestion lifecycle.

---

## 10. Baseline Gate

Baseline Gate là version-governance boundary giữa các stage.

### 10.1 Baseline Gate có ba mode

```text
AUTO_SELECT
AI_RECOMMEND
HUMAN_REQUIRED
```

Policy được xác định theo stage, risk, confidence và validation results.

Ví dụ POC:

| Handoff | Default policy |
|---|---|
| G0 classification → G1 | AUTO khi deterministic/confidence cao |
| Convert → Parse | AUTO nếu structural validation pass |
| Parse → G2 | AI_RECOMMEND; human khi quality thấp hoặc diff lớn |
| G2 → G3 | AI_RECOMMEND / HUMAN_REQUIRED |
| G3 → ReqKB | HUMAN_REQUIRED trong POC |

### 10.2 AI chỉ recommend, policy quyết định authority

AI Reviewer có thể tạo recommendation:

```text
recommended_output = OUT-221
confidence = 0.91
reasons:
- heading coverage 100%
- table coverage 98%
- orphan chunks 0
- validator errors 0
```

AI recommendation không đồng nghĩa human approval.

Policy có thể cho phép auto-select nếu risk thấp và threshold đạt yêu cầu.

### 10.3 Baseline history phải append-only

Không overwrite một row baseline duy nhất.

```text
BASE-008
stage = PARSE
output = OUT-187
effective_from = T1
effective_to = T2

BASE-009
stage = PARSE
output = OUT-221
effective_from = T2
effective_to = NULL
```

Current baseline là record có `effective_to IS NULL` hoặc tương đương.

---

## 11. G3 — Promotion / Publish

G3 consume **G2 baseline chính xác**, không consume latest G2 output.

```text
G2 baseline OUT-310
       ↓
Promotion PROM-007
       ↓
materialize Neo4j
       ↓
verify
       ↓
ACTIVE promotion / ReqKB version
```

Promotion record phải pin:

```text
promotion_id
source_revision_id
ingestion_run_id
selected_g2_output_set_id
previous_promotion_id
status
promoted_at
promoted_by
```

### Promotion states

```text
PENDING
IN_PROGRESS
ACTIVE
FAILED
SUPERSEDED
```

`SUCCEEDED ingestion run` chỉ nghĩa pipeline hoàn tất kỹ thuật. `ACTIVE promotion` mới nghĩa output đang được ReqKB sử dụng.

---

## 12. Storage ownership

POC sử dụng ba persistence concerns.

### 12.1 Object Store — immutable payload/evidence

Giữ:

- raw DOCX/PDF/XLSX;
- converted Markdown/normalized payload;
- full parsed document;
- chunk bundle;
- diagnostics;
- enriched chunk bundle;
- evaluation/review evidence bundle nếu lớn;
- promotion manifest.

### 12.2 Ingestion Catalog DB — control, governance và queryable projection

Giữ:

- source identity/revision;
- ingestion/stage runs;
- exact input/output references;
- output set registry;
- stage baseline history;
- AI recommendation/review decision;
- SourceUnit queryable projection;
- component/config/schema versions;
- promotion state;
- lineage pointers.

Tên `Ingestion Catalog DB` được dùng thay cho `Metadata DB` vì DB không chỉ chứa metadata thuần túy; nó còn chứa structured projection cần query cho ingestion operations.

### 12.3 Neo4j — promoted ReqKB

Giữ semantic nodes/relationships đã được G3 publish.

Neo4j không phải staging database cho G0/G1/G2.

---

## 13. Object Store layout

Recommended logical key structure:

```text
reqkb/
└── projects/{project_id}/
    └── sources/{source_document_id}/
        ├── revisions/{source_revision_id}/
        │   └── raw/
        │       └── requirement.xlsx
        │
        └── runs/{ingestion_run_id}/
            ├── g0/
            │   └── classification.json
            ├── g1-convert/
            │   ├── document.md
            │   └── diagnostics.json
            ├── g1-parse/
            │   ├── parsed-document.json
            │   ├── chunks.json
            │   └── diagnostics.json
            ├── g2/
            │   └── enriched-chunks.json
            └── g3/
                └── promotion-manifest.json
```

Folder/key không biểu diễn current/final state.

Không dùng:

```text
/final/
/current/
/latest/
```

để quyết định governance state.

---

## 14. Core logical data model

Physical schema sẽ được đặc tả ở tài liệu sau. Logical model tối thiểu:

```text
SourceDocument
  └── SourceRevision
        └── IngestionRun
              └── StageRun
                    ├── StageOutputSet
                    │     └── StageOutput
                    └── AI Recommendation / Review

SourceRevision + StageType
  └── StageBaseline History
        └── selected StageOutputSet

G2 StageBaseline
  └── Promotion
        └── ReqKB active state
```

Suggested entities:

```text
source_document
source_revision

ingestion_run
stage_run
stage_output_set
stage_output

stage_baseline
review_request
review_decision

document_classification
source_unit
source_unit_enrichment

promotion
```

---

## 15. StageRun input must pin exact upstream baseline

Không lưu input chỉ bằng `source_revision_id` nếu stage consume output trung gian.

Ví dụ Parse Run:

```text
stage_run_id = PARSE-221
stage_type = PARSE
input_output_set_id = CONVERT-OUT-087
input_hash = abc123
parser_version = v4
```

G2:

```text
stage_run_id = ONT-310
input_output_set_id = CHUNKSET-221
```

Nhờ đó lineage deterministic:

```text
REV-003
  ↓
Convert RUN-87
  ↓
MD OUTSET-087  ← baseline
  ↓
Parse RUN-221
  ↓
CHUNKSET-221   ← baseline
  ↓
G2 RUN-310
  ↓
ENRICHED-310   ← baseline
  ↓
PROM-007
  ↓
ReqKB
```

---

## 16. OutputSet thay vì chỉ Output

Một stage thường tạo nhiều artifact liên quan.

Ví dụ Parse:

```text
OUTSET-221
  ├── parsed-document.json
  ├── chunks.json
  └── diagnostics.json
```

Baseline nên trỏ tới `OutputSet`, không trỏ rời từng file.

`StageOutputSet` đại diện cho một coherent result của một StageRun.

`StageOutput` đại diện cho từng physical artifact trong set.

---

## 17. Review và AI recommendation model

### review_request

Logical fields:

```text
review_id
source_revision_id
stage_run_id
review_type
status
recommended_output_set_id
recommendation_score
recommendation_summary
recommendation_evidence_ref
created_at
resolved_at
```

### review_decision

```text
decision_id
review_id
decision                # APPROVE | REJECT | SELECT_OTHER
selected_output_set_id
decided_by
decision_reason
decided_at
```

### stage_baseline

```text
baseline_id
source_revision_id
stage_type
output_set_id
effective_from
effective_to
created_by_decision_id
selection_mode           # AUTO | AI_POLICY | HUMAN
```

Baseline history là immutable governance evidence.

---

## 18. Workflow runtime integration

LangGraph quản lý runtime execution state:

```text
current node
checkpoint
interrupt/resume
retry
workflow state
```

Ingestion Catalog DB quản lý business/governance state:

```text
stage output registered
baseline selected
review pending
promotion active
```

Không dùng LangGraph checkpoint làm system of record cho baseline.

Correlation:

```text
ingestion_run.runtime_ref
stage_run.runtime_ref
```

### Human review flow

```text
Stage executes
   ↓
Candidate OutputSet
   ↓
Evaluate / Recommend
   ↓
Baseline Policy
   ├── auto → create StageBaseline → continue
   └── review → create ReviewRequest
                    ↓
                interrupt()
                    ↓
              human decision
                    ↓
            create StageBaseline
                    ↓
                 resume
```

---

## 19. AI-native UI/UX mapping

User không thao tác trực tiếp với database tables.

Application nên có bốn surface chính:

```text
Workflow Canvas
Artifact / Compare View
Review Inbox
AI Copilot / Chat
```

### 19.1 Workflow Canvas

Hiển thị trạng thái:

```text
G1 Parse
✓ execution completed
4 candidates
★ AI recommends OUTSET-221
Baseline: waiting approval
```

Canvas trả lời: **workflow đang ở đâu và gate nào đang chặn?**

### 19.2 Artifact / Compare View

Mặc định compare:

```text
Current Baseline
vs
AI Recommended Candidate
```

Ví dụ:

```text
Current OUTSET-187
Candidate OUTSET-221

+18 chunks
-4 chunks
3 heading paths corrected
validator errors: 4 → 0
```

Không bắt user duyệt hàng trăm historical runs theo danh sách phẳng.

### 19.3 Review Inbox

Hiển thị các `review_request.status = OPEN`.

User có thể:

```text
Approve recommended baseline
Select another candidate
Reject / request rerun
```

### 19.4 AI Copilot / Chat

Chat hỗ trợ reasoning/explanation:

```text
“Vì sao recommend OUTSET-221?”
“So với baseline hiện tại section 3.2 thay đổi gì?”
“Chọn candidate này làm baseline.”
```

Button và chat command phải gọi cùng application command, ví dụ:

```text
ApproveStageBaseline(
  source_revision_id,
  stage_type,
  output_set_id,
  actor,
  reason
)
```

UI/chat không được ghi DB trực tiếp.

---

## 20. Application architecture

```text
                         FRONTEND

 Workflow Canvas | Artifact Compare | Review Inbox | AI Chat
                           │
                           ▼
                    APPLICATION API
                           │
       ┌───────────────────┼────────────────────┐
       ▼                   ▼                    ▼
  Workflow Service   Baseline Service     Review Service
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
                    Domain Commands
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
 Ingestion Catalog DB   Object Store    LangGraph Runtime
          │
          └──────────── G3 Promotion ────────────→ Neo4j
```

Representative commands:

```text
StartIngestion
RunStage
RegisterOutputSet
RecommendBaseline
ApproveBaseline
RejectCandidate
CompareOutputs
PromoteToReqKB
ResumeWorkflow
```

---

## 21. Status semantics

### StageRun

```text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

### ReviewRequest

```text
OPEN
IN_REVIEW
RESOLVED_APPROVE
RESOLVED_REJECT
RESOLVED_SELECT_OTHER
```

### Baseline

Không cần `FINAL`.

Baseline history dùng effective interval hoặc active flag có constraint để đảm bảo một current baseline cho mỗi `(source_revision, stage_type, baseline_scope)`.

### Promotion

```text
PENDING
IN_PROGRESS
ACTIVE
FAILED
SUPERSEDED
```

Terminology rule:

> Không dùng `final` cho run/output. Dùng `selected baseline` cho intermediate artifacts và `active promotion` cho ReqKB publication.

---

## 22. Replay, retry và reprocess

### Retry

Retry cùng operation phải tránh duplicate logical side effects.

### Reprocess

Reprocess có chủ đích phải tạo new StageRun/OutputSet ngay cả khi source không đổi.

```text
REV-003
  ├── PARSE-201 parser-v3
  ├── PARSE-221 parser-v4
  └── PARSE-240 parser-v4 + config-B
```

History được giữ để benchmark/debug/audit.

### Baseline change

Không rerun downstream tự động một cách mơ hồ.

Khi upstream baseline đổi:

```text
Convert baseline OUT-087 → OUT-091
```

hệ thống phải xác định downstream baseline/run nào trở thành stale và tạo explicit reprocessing decision/event.

Chi tiết stale propagation sẽ được đặc tả ở tài liệu implementation/schema tiếp theo.

---

## 23. Failure semantics

Một failed candidate không được phá baseline hiện tại.

Ví dụ:

```text
PARSE baseline = OUTSET-221

PARSE-240 starts
→ execution FAIL

Result:
- PARSE-240 = FAILED
- diagnostics retained
- OUTSET-221 remains current baseline
- G2 current baseline/history remains unchanged
```

Tương tự G3:

```text
Current active promotion = PROM-006
PROM-007 fails
→ PROM-006 remains active
```

---

## 24. Transaction / consistency methodology

Không tạo distributed transaction giả giữa Object Store + Catalog DB + Neo4j.

Register output:

```text
1. write immutable artifacts to Object Store
2. calculate/verify hash
3. register OutputSet + Output records
4. mark StageRun SUCCEEDED
```

Nếu DB registration fail sau khi object được write, object trở thành orphan candidate và được reconciliation/GC xử lý sau.

Baseline selection:

```text
1. validate candidate is eligible
2. close previous baseline effective interval
3. insert new StageBaseline
4. resolve ReviewDecision if applicable
5. emit/resume workflow transition
```

Các DB mutations của bước 1–4 nên nằm trong một relational transaction.

Promotion:

```text
1. create Promotion = IN_PROGRESS
2. read exact G2 baseline OutputSet
3. materialize Neo4j idempotently
4. verify materialization
5. write promotion manifest
6. set Promotion = ACTIVE
7. supersede previous active promotion
```

---

## 25. Technology selection

Methodology không khóa PostgreSQL.

### POC

```text
Ingestion Catalog DB: SQLite
Object Store: local filesystem adapter hoặc MinIO
ReqKB: Neo4j
Runtime: LangGraph
```

### Scale-up

Chuyển sang PostgreSQL khi có:

- concurrent workers/writers;
- service tách process/machine;
- audit/query workload lớn;
- production backup/HA;
- stronger concurrency control requirements.

Domain contract nên portable:

```text
IngestionRepository
  ├── SQLite adapter
  └── PostgreSQL adapter
```

Tuy nhiên physical schema/index/locking/isolation strategy có thể khác giữa SQLite và PostgreSQL. Portability áp dụng cho domain/application contract, không có nghĩa chỉ đổi connection string.

---

## 26. Decision matrix

| Data | Primary owner | Notes |
|---|---|---|
| Original DOCX/PDF/XLSX | Object Store | immutable evidence |
| Converted MD/normalized payload | Object Store | immutable candidate artifact |
| Parsed document/chunk bundle | Object Store | full replay artifact |
| Enriched chunk bundle | Object Store | G2 candidate artifact |
| Diagnostics/evaluation bundle | Object Store | if large/detailed |
| Source identity/revision | Catalog DB | governance identity |
| Classification | Catalog DB | queryable G0 state |
| Ingestion/Stage runs | Catalog DB | execution facts |
| OutputSet/Output URI/hash | Catalog DB | artifact registry |
| SourceUnit projection | Catalog DB | diff/review/lineage queries |
| Baseline history | Catalog DB | version governance |
| AI recommendation/review decision | Catalog DB + evidence ref | governance/audit |
| Promotion record | Catalog DB | publication lifecycle |
| Canonical semantic nodes/edges | Neo4j | only after G3 |
| Promotion manifest | Object Store | immutable publication evidence |

---

## 27. Anti-patterns

### AP-01 — Latest output wins

```text
SELECT latest run
→ use as next stage input
```

**Reject.** Next stage consumes explicit current baseline.

### AP-02 — `/final` folder as governance

**Reject.** Object Store key không quyết định current state.

### AP-03 — Overwrite intermediate artifacts

**Reject.** New run → new immutable OutputSet.

### AP-04 — Successful run = approved output

**Reject.** Execution success và baseline selection là hai states khác nhau.

### AP-05 — AI recommendation = approval

**Reject.** AI recommends; policy defines whether selection can be automatic or requires human authority.

### AP-06 — G2 writes directly to active Neo4j

**Reject.** G3 Promotion là publication boundary.

### AP-07 — LangGraph checkpoint as governance DB

**Reject.** Runtime state và baseline/promotion state có owners khác nhau.

### AP-08 — UI writes database directly

**Reject.** Canvas, review UI và chat đều gọi domain/application commands.

---

## 28. Design review checklist

Một implementation ingestion chỉ được chấp nhận khi trả lời rõ:

- [ ] SourceDocument và SourceRevision khác nhau thế nào?
- [ ] Raw bytes có immutable hash/URI không?
- [ ] G0 classification có identity/version/evidence không?
- [ ] G1A/G1B pin exact input baseline không?
- [ ] Mỗi StageRun có exact component/config/schema version không?
- [ ] Mỗi OutputSet immutable không?
- [ ] Một stage có thể giữ hàng trăm candidate mà không mất provenance không?
- [ ] Current baseline có explicit DB record không?
- [ ] Latest output có bị dùng ngầm thay baseline không?
- [ ] Baseline history có append-only/effective history không?
- [ ] AI recommendation và human decision có trace được không?
- [ ] SourceUnit có queryable projection cho diff/review không?
- [ ] Baseline change có thể xác định downstream stale state không?
- [ ] G3 chỉ consume exact G2 baseline không?
- [ ] Failed run/promotion có giữ current baseline/ReqKB active state không?
- [ ] Object Store không dùng `/final` để quyết định state không?
- [ ] LangGraph checkpoint có tách khỏi governance record không?
- [ ] UI/chat có gọi cùng domain commands không?
- [ ] SQLite/PostgreSQL có được che sau repository boundary không?

---

## 29. Baseline architecture sau tài liệu này

```text
                             STAGE 1 — INGESTION

Input Document
      │
      ▼
Source Revision ───────────────────────────────┐
      │                                        │
      ▼                                        │
G0 Classification                             │
      │                                        │
      ▼                                        │
G1A Convert ──→ Candidate OutputSets ──→ Baseline Gate
      │                                        │
      ▼                                        │
G1B Parse ───→ ChunkSet Candidates ───→ Baseline Gate
      │                                        │
      ▼                                        │
G2 Ontology ─→ Enriched Candidates ───→ Baseline Gate
      │                                        │
      ▼                                        │
G3 Promotion                                  │
      │                                        │
      ▼                                        │
     ReqKB                                     │
                                               │
Object Store  ← immutable payloads ────────────┤
Catalog DB    ← runs/outputsets/baselines ─────┤
LangGraph     ← execution/checkpoint ──────────┘
```

Core rule:

> **Execution tạo candidate. Evaluation/AI đánh giá candidate. Policy quyết định authority. Baseline ghi nhận output được chấp nhận. Stage tiếp theo chỉ consume exact baseline. G3 mới publish vào ReqKB.**

---

## 30. Output cho tài liệu tiếp theo

Tài liệu tiếp theo:

```text
02_storage_boundary.md
```

phải chốt cụ thể:

1. entity nào thuộc Object Store / Catalog DB / Neo4j;
2. mapping G0/G1A/G1B/G2/G3 theo read/write responsibility;
3. SourceUnit và enrichment projection lưu tới mức nào trong relational DB;
4. OutputSet/Object key conventions;
5. baseline/review/promotion ownership;
6. duplicate/denormalization rules;
7. stale propagation khi upstream baseline thay đổi;
8. boundary contract để Stage 2 Assessment consume ReqKB mà không phụ thuộc ingestion internals.

Chỉ sau khi storage boundary này được khóa mới thiết kế physical relational schema.