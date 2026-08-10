# ReqKB Ingestion Database Design Methodology

**Status:** POC architecture baseline  
**Scope:** ReqKB ingestion phase — từ source document đến knowledge được promote  
**Audience:** System Architect, AI Engineer, Backend Engineer, Coding Agent  
**Goal:** Định nghĩa phương pháp luận để quyết định dữ liệu nào phải được version, lưu ở đâu, liên kết thế nào và khi nào được promote vào ReqKB.

---

## 1. Vì sao cần một phương pháp luận riêng?

ReqKB ingestion không phải một thao tác `read file -> insert database`.

Một source document đi qua nhiều trạng thái:

```text
Source
  -> Convert
    -> Parse
      -> Validate / Repair
        -> Ontology Build / Tag
          -> Knowledge Candidate
            -> Promote
              -> Canonical Knowledge
```

Mỗi bước có thể:

- dùng component version khác nhau;
- sinh output trung gian;
- fail và retry;
- được re-run khi parser/validator/ontology thay đổi;
- dùng LLM hoặc deterministic logic;
- tạo dữ liệu chưa đủ tin cậy để đưa trực tiếp vào knowledge base.

Nếu chỉ thiết kế database từ danh sách field hoặc từ output cuối cùng của parser, hệ thống sẽ sớm gặp các vấn đề:

- không replay được ingestion;
- không biết output nào được tạo bởi component version nào;
- intermediate data bị ghi đè;
- Neo4j chứa cả candidate và canonical knowledge;
- khó rollback khi một run lỗi;
- khó giải thích knowledge hiện tại đến từ source revision nào;
- DB bị dùng đồng thời như file store, workflow state store và knowledge store.

Do đó thiết kế phải bắt đầu từ **data lifecycle và ownership**, không bắt đầu từ PostgreSQL, SQLite hay Neo4j.

---

## 2. Nguyên tắc nền tảng

### 2.1 Design từ lifecycle trước, schema sau

Thứ tự quyết định bắt buộc:

```text
Business lifecycle
  -> Data states
    -> Ownership
      -> Identity / versioning
        -> Persistence boundary
          -> Logical data model
            -> Physical database schema
```

Không chọn database trước rồi ép lifecycle vào schema của database đó.

---

### 2.2 Một loại state chỉ có một primary owner

POC sử dụng ba lớp persistence khác nhau:

```text
Object Store
= payload và intermediate processing artifacts

Metadata DB
= identity, run state, stage state, lineage metadata, promotion metadata

ReqKB / Neo4j
= canonical semantic knowledge đã được promote
```

Một dữ liệu có thể có reference ở nhiều hệ thống, nhưng chỉ có một primary owner.

Ví dụ:

```text
parsed blocks JSON
Primary owner: Object Store
Metadata DB: object_uri + hash + schema_version
Neo4j: không lưu
```

```text
Requirement node đã promote
Primary owner: Neo4j
Metadata DB: snapshot / promotion reference
Object Store: candidate artifact trước promotion
```

---

### 2.3 Payload khác metadata

Payload là nội dung có thể lớn hoặc cần replay:

- DOCX/PDF/Excel gốc;
- converted Markdown;
- parsed document JSON;
- validated JSON;
- ontology candidate JSON;
- debug bundle cần giữ lại.

Các payload này ưu tiên Object Store.

Metadata là dữ liệu điều khiển và truy vết:

- source ID;
- revision ID;
- ingestion run ID;
- stage status;
- component version;
- content hash;
- object URI;
- timestamps;
- promotion status;
- knowledge snapshot reference.

Các metadata này thuộc Metadata DB.

Quy tắc:

> Không đưa payload lớn vào Metadata DB chỉ vì SQL query thuận tiện hơn.

Có thể lưu một số field nhỏ, indexed hoặc denormalized để phục vụ query, nhưng không biến chúng thành canonical copy thứ hai của payload.

---

### 2.4 Intermediate output không phải canonical knowledge

Output từ parser, validator hoặc ontology builder vẫn là **processing artifact**.

```text
ParsedDocument
ValidatedDocument
OntologyCandidate
```

chưa tự động tương đương với:

```text
ReqKB canonical graph
```

Cần một boundary rõ ràng:

```text
Knowledge Candidate
      ↓
Promotion Gate
      ↓
Canonical Knowledge
```

Neo4j không được dùng như workflow scratchpad cho mọi output trung gian.

---

### 2.5 Immutable evidence, append-only history

Các object sau sau khi được register phải được coi là immutable:

- source revision bytes;
- stage output đã hoàn thành;
- content hash;
- component version dùng trong stage run;
- completed ingestion run facts;
- promoted knowledge snapshot identity.

Nếu xử lý lại, tạo run/output mới thay vì overwrite.

Mental model:

```text
old immutable state
      ↓
new run
      ↓
new immutable state
```

Không dùng:

```text
parsed/current.json
```

rồi overwrite nhiều lần mà không còn provenance.

---

## 3. Data lifecycle chuẩn của ReqKB ingestion

### 3.1 Source Document

`SourceDocument` là business identity ổn định của tài liệu.

Ví dụ:

```text
Customer Management Requirement Definition
```

Nó không đại diện cho bytes cụ thể của một lần upload.

---

### 3.2 Source Revision

Mỗi thay đổi nội dung tạo một `SourceRevision` mới.

Ví dụ:

```text
DOC-001
  ├── REV-001 hash=A
  ├── REV-002 hash=B
  └── REV-003 hash=C
```

Source Revision trỏ tới raw object trong Object Store.

Source Revision là đơn vị đầu vào của ingestion.

---

### 3.3 Ingestion Run

`IngestionRun` là một lần xử lý cụ thể của một Source Revision bằng một pipeline configuration cụ thể.

```text
ING-1001
source_revision = REV-003
pipeline_release = ingestion-1.4.0
```

Cùng `REV-003` có thể có nhiều ingestion run nếu parser, validator hoặc ontology thay đổi.

---

### 3.4 Stage Run

Mỗi công đoạn là một execution record độc lập:

```text
ING-1001
  ├── STG-01 CONVERT
  ├── STG-02 PARSE
  ├── STG-03 VALIDATE
  ├── STG-04 ONTOLOGY_BUILD
  └── STG-05 PROMOTE
```

Stage Run lưu execution facts, không lưu toàn bộ output payload.

Tối thiểu cần biết:

- stage type;
- status;
- component name/version;
- input references;
- output references;
- start/end time;
- error information;
- retry/attempt number nếu cần.

---

### 3.5 Stage Output

Stage có thể sinh một hoặc nhiều immutable output.

Ví dụ:

```text
PARSE
  -> parsed_document.json
  -> parser_diagnostics.json
```

Metadata DB chỉ register:

```text
output_id
stage_run_id
output_type
object_uri
content_hash
schema_version
```

Bytes thực tế thuộc Object Store.

---

### 3.6 Knowledge Candidate

Ontology builder/tagger tạo structured candidate cho graph.

Ví dụ:

```text
knowledge-candidate.json

Requirement REQ-001
Function FUNC-010
Constraint CST-003
relationships...
```

Candidate vẫn có thể bị reject hoặc reprocess.

Do đó Candidate thuộc processing lifecycle, không phải canonical ReqKB.

---

### 3.7 Promotion

Promotion là business/data-governance transition:

```text
Candidate
   -> validate promotion conditions
   -> materialize canonical knowledge
   -> register snapshot/reference
```

Promotion phải tách khỏi ontology build để tránh pattern:

```text
LLM output -> write Neo4j immediately
```

Đây là anti-pattern vì generation và publication trở thành cùng một transaction logic.

---

### 3.8 Knowledge Snapshot

`KnowledgeSnapshot` là identity của trạng thái knowledge đã được công nhận để downstream workflow sử dụng.

Ví dụ:

```text
KB-012
```

Generation workflow sau này pin:

```text
knowledge_snapshot = KB-012
```

thay vì sử dụng khái niệm mơ hồ:

```text
latest ReqKB
```

Chi tiết physical implementation của snapshot trong Neo4j sẽ được quyết định ở tài liệu Knowledge Promotion / Lineage; methodology chỉ yêu cầu snapshot phải có identity và provenance ổn định.

---

## 4. Storage ownership methodology

Đối với mỗi data object, trả lời tuần tự năm câu hỏi.

### Question 1 — Đây là content hay control metadata?

Nếu là bytes/content lớn hoặc structured payload cần replay:

```text
-> Object Store
```

Nếu là trạng thái, ID, relation hoặc pointer:

```text
-> Metadata DB
```

---

### Question 2 — Đây đã là canonical knowledge chưa?

Nếu chưa pass promotion:

```text
-> không vào Neo4j canonical graph
```

Nếu đã promoted:

```text
-> Neo4j
```

---

### Question 3 — Có cần replay/debug chính xác không?

Nếu có, output phải immutable và có:

```text
content_hash
schema_version
producer/component version
input references
```

---

### Question 4 — Dữ liệu thay đổi bằng mutation hay new revision?

Evidence và output lịch sử:

```text
new revision / new run
```

Mutable operational pointer có thể update:

```text
active source revision
current run status
active knowledge snapshot pointer
review state
```

Pointer được phép mutable; target lịch sử phải immutable.

---

### Question 5 — Ai cần query dữ liệu này?

Nếu query chủ yếu phục vụ orchestration/governance:

```text
Metadata DB
```

Nếu query phục vụ semantic retrieval/traversal:

```text
Neo4j
```

Nếu query chỉ cần load/replay artifact:

```text
Object Store by URI/key
```

---

## 5. Decision matrix

| Data | Primary store | Reason |
|---|---|---|
| Original DOCX/PDF/Excel | Object Store | Immutable source evidence |
| Converted Markdown/text | Object Store | Intermediate replayable payload |
| Parsed document / SourceUnit payload | Object Store | Parser output; can be regenerated/versioned |
| Validation result bundle | Object Store | Detailed processing evidence |
| Ontology candidate | Object Store | Candidate before promotion |
| Source identity/revision metadata | Metadata DB | Governance and lookup |
| Ingestion run | Metadata DB | Pipeline lifecycle |
| Stage run | Metadata DB | Operational state and lineage |
| Stage output URI/hash | Metadata DB | Pointer to immutable payload |
| Component versions | Metadata DB | Reproducibility |
| Promotion record | Metadata DB | Governance transition |
| Knowledge snapshot metadata | Metadata DB | Stable downstream reference |
| Canonical Requirement/Function/Rule nodes | Neo4j | Semantic graph query |
| Canonical semantic relationships | Neo4j | Graph traversal |

---

## 6. Identity methodology

Mỗi layer cần identity riêng; không tái sử dụng một ID cho nhiều lifecycle.

Recommended IDs:

```text
source_document_id
source_revision_id
ingestion_run_id
stage_run_id
stage_output_id
knowledge_candidate_id
promotion_id
knowledge_snapshot_id
```

Ví dụ lineage:

```text
DOC-001
  ↓
REV-003
  ↓
ING-1001
  ↓
STG-04 ONTOLOGY_BUILD
  ↓
OUT-440 knowledge-candidate.json
  ↓
PROM-008
  ↓
KB-012
```

Không dùng file path hoặc Git SHA làm business identity chính.

Hashes phục vụ integrity/deduplication; IDs phục vụ lifecycle identity.

---

## 7. Versioning methodology

Không phải mọi object đều dùng cùng một kiểu version.

### Source Revision

Version theo thay đổi source content.

```text
source content hash changed
-> new SourceRevision
```

### Pipeline / Component Version

Pin exact version của converter/parser/builder/validator/ontology component đã chạy.

### Schema Version

Output contract phải có `schema_version` riêng với component version.

Parser v4 có thể vẫn emit schema v2.

### Knowledge Snapshot Version

Sinh khi một candidate/set candidate được promote thành trạng thái canonical có thể downstream pin.

Do đó không tạo một generic `version` column để đại diện tất cả lifecycle.

---

## 8. Replay và idempotency

Database design phải hỗ trợ hai capability khác nhau.

### Idempotent retry

Retry cùng operation không được tạo duplicate logical output ngoài ý muốn.

Có thể sử dụng operation key dạng:

```text
source_revision_id
+ pipeline_release
+ stage_type
+ component_version
+ relevant configuration hash
```

### Intentional reprocess

Reprocess có chủ đích phải tạo run mới dù source bytes không đổi.

Ví dụ:

```text
REV-003
  -> ING-1001 parser-v3
  -> ING-1015 parser-v4
```

Cả hai giữ nguyên để benchmark/debug/audit.

Idempotency không được ngăn intentional reprocessing.

---

## 9. Failure semantics

Một failed run không được phá trạng thái knowledge đang active.

Pattern:

```text
Current canonical KB = KB-011

ING-1001 starts
  -> convert PASS
  -> parse PASS
  -> validate PASS
  -> ontology FAIL

Result:
- ING-1001 = FAILED
- intermediate outputs retained
- KB-011 remains active
- no partial canonical promotion
```

Promotion là boundary quan trọng nhất.

Không để từng parser/ontology stage ghi trực tiếp vào active Neo4j graph theo kiểu incremental side-effect không có rollback boundary.

---

## 10. Transaction methodology

Không cố tạo một distributed transaction xuyên Object Store + Metadata DB + Neo4j.

POC ưu tiên **explicit state transition + idempotency**.

Ví dụ register stage output:

```text
1. write immutable payload to Object Store
2. calculate/verify hash
3. insert StageOutput metadata
4. mark StageRun completed
```

Nếu step 3 fail, object chưa được register có thể được garbage-collect/reconciled sau.

Promotion:

```text
1. create Promotion record = IN_PROGRESS
2. materialize candidate into Neo4j idempotently
3. verify materialization
4. create/register KnowledgeSnapshot
5. mark Promotion = COMPLETED
6. optionally move active-snapshot pointer
```

Chi tiết consistency/reconciliation sẽ được specification trong implementation documents.

---

## 11. LLM-enabled stage methodology

Ontology Builder có thể sử dụng LLM sau này. Điều này không làm thay đổi storage model.

Stage Run vẫn là:

```text
ONTOLOGY_BUILD
```

Nhưng có thể bổ sung component references:

```text
MODEL
PROMPT
TOOL
CODE
RULESET
```

Ví dụ:

```text
STG-04
component = ontology-builder 0.4.0
model_ref = model-profile-x
prompt_ref = ontology-builder/v5
ruleset_ref = ontology-rules/v3
```

Nếu tích hợp MLflow trong tương lai, Metadata DB chỉ lưu stable external reference như `trace_ref` hoặc `prompt_ref`; không duplicate MLflow internal data model.

Nguyên tắc:

> MLflow integration là observability/experiment concern của AI-enabled stage, không phải nền tảng của ingestion persistence model.

---

## 12. Database technology selection

Phương pháp luận không khóa PostgreSQL.

Domain/application layer phụ thuộc vào repository contract, không phụ thuộc database engine.

```text
ReqKBMetadataRepository
      │
      ├── SQLite adapter      # POC
      └── PostgreSQL adapter  # pilot / scale-up
```

### POC recommendation

```text
Metadata DB: SQLite
Object Store: local filesystem adapter hoặc MinIO
Knowledge Store: Neo4j
```

SQLite phù hợp khi:

- một process hoặc ít writer;
- local POC;
- deployment đơn giản quan trọng hơn horizontal scale.

### Scale-up trigger

Chuyển PostgreSQL khi:

- nhiều worker concurrent;
- cần stronger operational isolation;
- cần production backup/HA;
- query/audit workload tăng;
- service deployment tách process/machine.

Việc chuyển DB không được yêu cầu thay đổi domain model hoặc LangGraph workflow contract.

---

## 13. Quan hệ với LangGraph

LangGraph quản lý **workflow execution state**.

Metadata DB quản lý **business/ingestion lifecycle metadata**.

Không copy toàn bộ LangGraph state vào Metadata DB.

Ví dụ:

```text
LangGraph
- current node
- checkpoint state
- interrupt/resume state

Metadata DB
- ING-1001
- PARSE completed
- OUT-123 registered
- promotion status
```

Nếu cần correlation:

```text
ingestion_run.runtime_ref = langgraph thread/run reference
```

Runtime-specific schema không trở thành domain schema của ReqKB.

---

## 14. Quan hệ với tài liệu persistence hiện tại

Tài liệu `poc/reqkb-ingestion-workflow/docs/05_PERSISTENCE_AND_INCREMENTAL_INGESTION.md` hiện mô tả PostgreSQL như system of record và lưu trực tiếp `source_units`, validation results và ontology annotations.

Bộ `poc/database-design/` phát triển boundary này theo hướng:

```text
Old mental model
PostgreSQL = source + processing + metadata system of record

New mental model
Object Store = source/intermediate payload system of record
Metadata DB = ingestion governance and lineage system of record
Neo4j = promoted semantic knowledge system of record
```

Các nguyên tắc tốt của tài liệu hiện tại vẫn được giữ:

- append-only history;
- atomic activation/promotion;
- stale assertion handling;
- explicit reprocessing policy;
- idempotency;
- component version tracking;
- failed ingestion không thay active state.

Việc mapping cụ thể các entity cũ như `source_units`, `validation_results`, `ontology_annotations` sang storage boundary mới sẽ được xử lý ở các tài liệu tiếp theo, không sửa âm thầm trong tài liệu methodology này.

---

## 15. Anti-patterns

### AP-01 — Neo4j as staging database

Parser/ontology output được ghi thẳng vào canonical graph rồi sửa dần.

**Reject.** Candidate phải tách khỏi canonical knowledge.

### AP-02 — Database as file system

Lưu toàn bộ DOCX, converted text và large parsed JSON trực tiếp vào relational DB không có lý do query rõ ràng.

**Reject cho POC baseline.** Dùng Object Store + metadata reference.

### AP-03 — Overwrite intermediate output

Mỗi run ghi đè `parsed.json` của run trước.

**Reject.** Intermediate output phải gắn run/stage identity.

### AP-04 — Generic version column

Một `version` đại diện document version, parser version, schema version và knowledge version.

**Reject.** Lifecycle khác nhau cần version semantics khác nhau.

### AP-05 — LangGraph state as ingestion database

Dùng checkpoint làm persistent business record của ingestion.

**Reject.** Runtime state và ingestion governance state là hai concern khác nhau.

### AP-06 — Immediate LLM-to-KB write

Ontology Builder dùng LLM và ghi trực tiếp result vào active Neo4j graph.

**Reject.** LLM output phải tạo candidate và đi qua promotion gate.

---

## 16. Design review checklist

Một thiết kế DB ingestion chỉ được chấp nhận khi trả lời rõ:

- [ ] Business identity của source document là gì?
- [ ] Khi nào tạo Source Revision mới?
- [ ] Ingestion Run khác Source Revision thế nào?
- [ ] Mỗi stage có execution identity riêng không?
- [ ] Intermediate output có immutable URI/hash không?
- [ ] Payload lớn có bị duplicate trong Metadata DB không?
- [ ] Candidate knowledge được tách khỏi canonical graph chưa?
- [ ] Promotion có explicit state và failure boundary không?
- [ ] Downstream có thể pin Knowledge Snapshot cụ thể không?
- [ ] Có truy ngược KB snapshot về source revision và stage outputs được không?
- [ ] Retry có idempotent không?
- [ ] Intentional reprocess có tạo run riêng không?
- [ ] Failed ingestion có giữ nguyên active knowledge không?
- [ ] Component/schema versions có được pin độc lập không?
- [ ] Storage engine có replaceable qua port/adapter không?
- [ ] LangGraph runtime state có bị leak vào domain model không?

---

## 17. Baseline architecture sau tài liệu này

```text
                           ReqKB Ingestion

Source File
    │
    ▼
Object Store: RAW
    │
    ▼
Convert -> Parse -> Validate -> Ontology Build
    │          │          │           │
    └──────────┴──────────┴───────────┘
               │
               ▼
      Object Store intermediates
               │
               │ URI / hash / version
               ▼
          Metadata DB
      Source / Run / Stage / Lineage
               │
               ▼
        Knowledge Candidate
               │
          Promotion Gate
               │
               ▼
              Neo4j
       Canonical ReqKB Knowledge
               │
               ▼
       Knowledge Snapshot ID
```

---

## 18. Output cho tài liệu tiếp theo

Tài liệu tiếp theo phải đặc tả **storage boundary** chi tiết hơn:

```text
02_storage_boundary.md
```

Nó phải chốt:

1. ownership matrix cho từng data object hiện có trong ingestion workflow;
2. dữ liệu nào nằm Object Store, Metadata DB và Neo4j;
3. trường hợp nào được phép denormalize/duplicate;
4. source-of-truth rules;
5. read/write responsibility của từng pipeline stage;
6. mapping từ các object hiện tại như `SourceUnit`, validation result và ontology annotation sang kiến trúc ba-store.

Chỉ sau khi boundary này được khóa mới thiết kế physical relational schema.