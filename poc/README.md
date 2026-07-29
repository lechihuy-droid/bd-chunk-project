# RD → BD Knowledge Pipeline POC

## 1. Mục tiêu

Xây dựng POC chứng minh một luồng RD → BD hẹp nhưng chạy end-to-end:

```text
RD
→ parse có cấu trúc
→ trích xuất requirement và quan hệ
→ retrieve đúng tri thức liên quan
→ phân tích impact
→ sinh BD draft
→ tạo traceability
→ human review
```

POC không nhằm tự động hóa toàn bộ 600 tài liệu ngay từ đầu. Mục tiêu đầu tiên là chứng minh hệ thống có thể xử lý một module đại diện, sinh draft có căn cứ và giảm effort/review time.

## 2. Quan điểm thiết kế

### BPR / Process-first

Bắt đầu từ bottleneck của quy trình hiện tại, không bắt đầu từ công nghệ. Các pain point cần giải quyết:

- Khó tìm đúng tài liệu và đúng version.
- Impact analysis phụ thuộc senior engineer.
- Copy-paste BD cũ gây thiếu nhất quán.
- Traceability RD → Screen/API/DB yếu.
- Review lặp nhiều vòng và khó kiểm chứng nguồn.

### AI DevOps / Architecture-first

600 tài liệu không phải vấn đề scale lớn; vấn đề chính là semantic, versioning và grounding. Không dùng pipeline đơn giản `PDF → fixed chunk → embedding → top-k → LLM` làm kiến trúc chính.

Kiến trúc mục tiêu:

```text
Document Catalog
→ Deterministic Parser
→ LLM Structured Extraction
→ Lightweight Ontology
→ Entity/Relationship Store
→ Semantic Object Chunking
→ Hybrid Retrieval
→ BD Generation Workflow
→ Traceability + Human Gates
```

## 3. Phạm vi POC

Chọn một module và một business flow có đủ cặp RD–BD lịch sử.

Phạm vi gợi ý:

```text
1 business flow
5–10 RD lịch sử
30–50 tài liệu liên quan
RD → Screen Design + API Design + DB Impact
```

Kết quả tối thiểu cho một requirement mới:

```text
Requirement analysis
→ related documents
→ impacted screens
→ impacted APIs
→ impacted tables
→ BD draft
→ traceability matrix
```

Ngoài scope giai đoạn đầu:

- Ingest toàn bộ 600 tài liệu.
- Multi-agent phức tạp.
- Ontology OWL/RDF học thuật.
- Fine-tuning model.
- Tự động publish BD vào baseline chính.
- UI production hoàn chỉnh.

## 4. Kiến trúc logic

```text
                         ┌─────────────────────┐
                         │ Ontology / Schema   │
                         │ YAML + JSON Schema  │
                         └──────────┬──────────┘
                                    │
Raw Documents                       │
     │                              │
     ▼                              ▼
Document Registry → Parser → Structured Extraction
     │                              │
     │                              ▼
     │                    Entity + Relationship Store
     │                              │
     ▼                              ▼
Semantic Object Chunks → Metadata / Vector Index
                                    │
New RD → Query Understanding → Hybrid Retrieval
                                    │
                                    ▼
                          Impact Analysis Workflow
                                    │
                                    ▼
                     Screen/API/DB Draft Generation
                                    │
                                    ▼
                         Validation + Traceability
                                    │
                                    ▼
                              Human Review
```

## 5. Có cần LLM không?

Không cần LLM cho mọi bước.

### Không dùng LLM khi có thể xác định bằng rule

- Filename và document ID.
- Sheet name, heading, table structure.
- Requirement ID, screen ID, API path.
- DB table/column.
- Version, date, status.
- Template section mapping.

### Dùng LLM cho semantic extraction

- Tóm tắt requirement.
- Nhận diện business rule trong prose.
- Mapping synonym và thuật ngữ không nhất quán.
- Trích xuất implicit relationship.
- Requirement decomposition.
- Similar-design reasoning.
- Impact analysis proposal.

Nguyên tắc:

> Rule first, LLM second, ontology validation last.

LLM phải dùng structured output; không cho sinh entity/relation tự do ngoài schema.

## 6. Lightweight Ontology v0.1

Bắt đầu với 10–15 entity type, không xây ontology đầy đủ ngay từ đầu.

### Entity

- Document
- Requirement
- BusinessRule
- Actor
- Process
- Screen
- ScreenField
- API
- DataObject
- Table
- Column
- Batch
- Interface
- Module
- Version

### Relationship

- `describes`
- `belongs_to`
- `supersedes`
- `implemented_by`
- `governed_by`
- `invokes`
- `contains`
- `reads`
- `writes`
- `affects`
- `references`

Mọi entity/relation phải có:

- Source document.
- Page/section/sheet/cell.
- Confidence.
- Extraction method.
- Document version.
- Review status.

## 7. Document Catalog

Không embed trước khi có inventory và version governance.

Metadata tối thiểu:

| Field | Mô tả |
|---|---|
| document_id | ID duy nhất |
| document_name | Tên file/tài liệu |
| document_type | RD, Screen BD, API BD, DB BD... |
| system | Hệ thống |
| module | Module |
| submodule | Submodule |
| version | Phiên bản |
| status | Draft, active, obsolete... |
| owner | Owner |
| language | Ngôn ngữ |
| source_path | Nguồn |
| updated_at | Ngày cập nhật |
| supersedes | Tài liệu bị thay thế |
| related_requirement | Requirement liên quan |

Tài liệu chưa xác định được active version không được đưa vào retrieval production path.

## 8. Golden Dataset

Chọn 30–50 tài liệu để tạo `Golden Dataset v0`:

- 5–10 RD.
- BD tương ứng.
- Screen/API/DB design.
- Business rules.
- Change requests.
- Một số obsolete documents để kiểm tra filtering.

Mỗi RD phải có expected trace:

```text
REQ-001
→ SCR-LOGIN
→ API-AUTH-01
→ T_USER
→ BR-SEC-03
```

Golden dataset được dùng cho extraction, retrieval, impact analysis và generation evaluation.

## 9. Parse và extraction

### Deterministic layer

- Excel/DOCX/PDF parser.
- Template mapping.
- Heading/table/cell extraction.
- Regex cho IDs, API paths, table names.
- Version và status detection.

### LLM layer

LLM nhận ontology + schema và trả JSON có cấu trúc:

```json
{
  "document": {
    "id": "RD-001",
    "type": "RequirementDefinition",
    "version": "1.2",
    "module": "Authentication"
  },
  "entities": [
    {
      "id": "REQ-101",
      "type": "Requirement",
      "name": "Account lock after failed login",
      "source_location": "section 3.2",
      "confidence": 0.94
    }
  ],
  "relationships": []
}
```

Sau extraction cần validator kiểm tra:

- Entity type có hợp lệ không.
- Quan hệ source/target có được ontology cho phép không.
- Có source evidence không.
- Có duplicate/conflict không.
- Version nào được ưu tiên.

## 10. Semantic Object Chunking

Không dùng fixed-token chunking làm chiến lược chính.

Chunk theo object:

- Requirement chunk.
- Business Rule chunk.
- Screen chunk.
- API chunk.
- Table chunk.
- Sequence chunk.
- Validation chunk.

Ví dụ API chunk phải giữ cùng nhau:

```text
API ID
method/path
purpose
request
response
validation
errors
authentication
related requirements
related screens
source evidence
```

Mỗi chunk có metadata phục vụ filter:

```text
entity_type
entity_id
module
document_type
document_version
status
source_location
```

## 11. Knowledge Store

POC có thể dùng stack đơn giản:

```text
Raw document storage: filesystem/object storage
Metadata and relationships: PostgreSQL
Vector index: pgvector hoặc Qdrant
Graph: relation tables trước; Neo4j chỉ khi traversal phức tạp hơn
```

Không cần triển khai graph database ngay tuần đầu. Quan hệ có thể lưu dạng:

```text
source_entity
relationship_type
target_entity
evidence
confidence
```

## 12. Hybrid Retrieval

Retrieval order:

1. Exact ID search.
2. Active-version/status filter.
3. Module/document-type filter.
4. Entity relationship expansion.
5. Vector similarity search.
6. Reranking.
7. Context assembly.

Pipeline:

```text
New RD
→ detect module/entities
→ metadata filter
→ exact match
→ relationship expansion
→ vector search
→ rerank
→ evidence package
```

Retriever phải trả evidence package, không chỉ text chunks.

## 13. BD Generation Workflow

Không dùng một prompt duy nhất để sinh toàn bộ BD.

Tách thành các bước:

1. Requirement understanding.
2. Requirement decomposition.
3. Ambiguity/assumption detection.
4. Similar-design retrieval.
5. Impact analysis.
6. Screen proposal.
7. API proposal.
8. DB impact proposal.
9. Cross-artifact consistency validation.
10. Traceability generation.
11. Human review.
12. Render vào template BD hiện tại.

Artifact trung gian:

```text
requirement-analysis.json
retrieval-evidence.json
impact-analysis.json
screen-draft.json
api-draft.json
db-impact.json
traceability-matrix.json
validation-report.json
```

## 14. Human Gates

### Gate 1 — Requirement interpretation

BA xác nhận scope, actor, business rule, assumption và ambiguity.

### Gate 2 — Impact analysis

Architect xác nhận impacted screen, API, DB và NFR.

### Gate 3 — BD draft

Designer/engineer xác nhận field, validation, API contract, data mapping và business logic.

### Gate 4 — Publish

Reviewer phê duyệt trước khi trở thành baseline. AI không tự publish vào repository tài liệu chính.

## 15. KPI

### Retrieval

- Recall@5 / Recall@10.
- Precision@5.
- Correct-document rate.
- Correct-version rate.

### Extraction

- Entity precision/recall.
- Relationship precision/recall.
- Source-grounding accuracy.

### Generation

- Requirement coverage.
- Traceability completeness.
- Design correctness.
- Unsupported statement rate.
- Reviewer correction count.

### Business

- Draft effort reduction.
- Review effort reduction.
- Search time reduction.
- Review cycle reduction.
- Design defect reduction.

POC target ban đầu:

```text
Retrieval Recall@10 ≥ 85%
Traceability completeness ≥ 90%
Unsupported statement rate < 5%
Draft effort reduction 30–50%
Review effort reduction 20–30%
```

## 16. Roadmap 12 tuần

### Tuần 1–2: Scope và discovery

- Chọn module/business flow.
- Map as-is process.
- Chọn KPI.
- Inventory tài liệu.
- Chọn golden dataset.
- Phân tích RD/BD templates.

### Tuần 3–4: Knowledge model

- Ontology v0.1.
- Metadata schema.
- Extraction schema.
- Versioning rules.
- Source citation rules.
- Chunking guidelines.

### Tuần 5–6: Parse và extract

- Parse Excel, Word, PDF.
- Structured extraction.
- LLM semantic extraction.
- Validation.
- Extraction benchmark.

### Tuần 7–8: Retrieval

- Exact/metadata search.
- Vector search.
- Relation expansion.
- Reranker.
- Retrieval benchmark.

### Tuần 9–10: BD generation

- Requirement analysis.
- Impact analysis.
- Screen/API/DB draft.
- Traceability matrix.
- Template rendering.

### Tuần 11: User test

- Chạy 5–10 requirement thực tế.
- So sánh với quy trình manual.
- Thu thập corrections và reviewer feedback.

### Tuần 12: Assessment

- Đánh giá KPI.
- Gap analysis.
- Scale-up architecture.
- Cost/effort estimate.
- Go/no-go decision.

## 17. Việc cần hoàn tất trong 5 ngày đầu

### Ngày 1

- Chọn 1 module.
- Chọn 1 business flow.
- Chọn loại BD đầu ra chính.

### Ngày 2

- Thu thập 5 RD.
- Thu thập BD tương ứng.
- Thu thập 5–10 tài liệu hỗ trợ.

### Ngày 3

- Tạo document inventory.
- Xác định active/obsolete version.
- Mapping document relationships.

### Ngày 4

- Workshop BA + architect + reviewer.
- Chốt entity, relationship, decision points và review criteria.

### Ngày 5

Hoàn tất:

```text
POC scope
Golden dataset v0
Ontology v0.1
Metadata schema v0.1
KPI baseline
```

## 18. Thứ tự ưu tiên

```text
1. Scope
2. Golden dataset
3. Document catalog
4. Metadata/version governance
5. Extraction schema
6. Lightweight ontology
7. Parser
8. Retrieval
9. Traceability
10. BD generation
11. Agent orchestration
```

## 19. Definition of Done cho POC

POC đạt yêu cầu khi một requirement mới có thể đi qua luồng sau:

```text
Requirement mới
→ hệ thống hiểu và phân rã requirement
→ retrieve đúng tài liệu/version liên quan
→ xác định đúng screen/API/DB impact
→ sinh BD draft có evidence
→ tạo traceability RD → BD
→ reviewer kiểm chứng và sửa được từng quyết định
→ đo được effort và quality so với baseline manual
```

## 20. Cấu trúc folder đề xuất

```text
poc/
├── README.md
├── 01-scope/
├── 02-document-inventory/
├── 03-golden-dataset/
├── 04-ontology/
├── 05-schemas/
├── 06-parser/
├── 07-chunking/
├── 08-retrieval/
├── 09-generation/
├── 10-evaluation/
└── samples/
```

Folder rỗng không được Git theo dõi; các thư mục sẽ được tạo dần khi có artifact tương ứng.