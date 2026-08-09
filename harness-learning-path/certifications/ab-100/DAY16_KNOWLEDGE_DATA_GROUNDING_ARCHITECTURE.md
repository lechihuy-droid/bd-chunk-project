# AB-100 Day 16 — Knowledge, Data, and Grounding Architecture

> Track: Frontier / Titan Certification Sprint  
> Certificate: AB-100 — Agentic AI Business Solutions Architect  
> Focus: Design AI-powered business solutions  
> Study guide baseline: Skills measured as of 2026-07-22

---

# 1. Day 16 Goal

Kết thúc buổi này phải có khả năng nhìn một enterprise AI scenario và quyết định:

```text
Business Data
    ↓
Data Readiness
    ↓
Knowledge Source Strategy
    ↓
Grounding / Retrieval
    ↓
Agent / Copilot
    ↓
Business Action
```

Trọng tâm AB-100 không phải hỏi "vector database hoạt động toán học thế nào" mà hỏi:

> Dữ liệu nào nên dùng làm grounding, đặt ở đâu, ai được truy cập, dữ liệu có đủ sạch/tươi/chính xác không, và nền tảng Microsoft nào phù hợp?

---

# 2. Official Objective Mapping

Map trực tiếp vào study guide:

- review grounding data for accuracy, relevance, timeliness, cleanliness, and availability;
- organize business-solution data so it is available to other AI systems;
- determine use of generative AI and knowledge sources in agents;
- design AI/agent components across Microsoft business applications;
- design enterprise integration while respecting security and governance boundaries.

---

# 3. Five Dimensions of Grounding Data

Học thuộc mental model:

```text
Grounding Quality
├── Accuracy
├── Relevance
├── Timeliness
├── Cleanliness
└── Availability
```

## Accuracy

Nguồn có đúng không?

Ví dụ: policy đã được phê duyệt vs draft chưa approve.

## Relevance

Nguồn có phục vụ đúng task không?

Ví dụ: sales agent không cần toàn bộ HR knowledge base.

## Timeliness

Nguồn có đủ mới không?

Ví dụ: pricing agent dùng bảng giá quý trước có thể tạo business error dù retrieval technically đúng.

## Cleanliness

Nguồn có duplicate, conflict, malformed content hoặc metadata kém không?

## Availability

Agent có thể truy cập ổn định, đúng quyền, đúng region và đúng latency requirement không?

---

# 4. Knowledge Is Not Memory

Phân biệt:

```text
Knowledge
= external source of truth

Memory
= retained information from prior interaction/run

Context
= information visible to model now

State
= execution state of current workflow
```

Exam trap:

> "Store customer policy documents in agent memory so all agents can answer policy questions."

Sai mental model. Policy documents là enterprise knowledge/source of truth, không phải conversational memory.

---

# 5. Direct Access vs Retrieval vs Prebuilt Business Data

## Direct Access

Dùng khi:

- scope nhỏ;
- deterministic query tốt hơn semantic retrieval;
- source system đã expose API/action rõ ràng.

Ví dụ:

```text
Agent
 ↓
CRM API
 ↓
Current customer status
```

## Retrieval / Grounding

Dùng khi:

- knowledge lớn;
- unstructured/semi-structured;
- cần semantic lookup;
- knowledge thay đổi thường xuyên.

```text
Agent
 ↓
Retrieve relevant knowledge
 ↓
Grounded response
```

## Prebuilt Business Context

Trong Microsoft stack có các trường hợp nên tận dụng context/knowledge đã nằm trong Microsoft 365, Dynamics 365, Dataverse hoặc platform connector thay vì tự xây pipeline mới.

Architectural principle:

> Reuse governed business data paths before creating another unmanaged knowledge copy.

---

# 6. Knowledge Source Decision Framework

Khi gặp scenario, hỏi theo thứ tự:

```text
1. Source of truth ở đâu?
2. Structured hay unstructured?
3. Real-time hay eventually consistent?
4. Người dùng/agent nào được quyền xem?
5. Có cần semantic retrieval không?
6. Có data residency requirement không?
7. Có cần write-back/action không?
```

Sau đó mới chọn integration pattern.

---

# 7. Retrieval Mental Model for Solution Architects

Không cần đi sâu implementation, nhưng phải hiểu:

```text
Source
 ↓
Ingestion / Connector
 ↓
Index / Knowledge Layer
 ↓
Retrieve
 ↓
Grounding Context
 ↓
Agent
```

Các khái niệm cần nhận diện:

- keyword search;
- semantic search;
- vector search;
- hybrid retrieval;
- metadata filtering;
- source citation/traceability.

AB-100 architect cần quan tâm nhiều hơn đến:

```text
quality
security
freshness
ownership
cost
traceability
```

hơn là embedding implementation chi tiết.

---

# 8. Data Organization for Other AI Systems

Enterprise anti-pattern:

```text
Agent A owns private copy of data
Agent B owns another copy
Agent C owns another copy
```

Kết quả:

- stale data;
- conflicting truth;
- duplicated governance;
- cost tăng;
- audit khó.

Preferred pattern:

```text
Governed Data / Knowledge Layer
        ↓
Shared controlled access
        ↓
Agent A / Agent B / Agent C
```

Nhưng "shared" không có nghĩa là tất cả agent có full access.

---

# 9. Grounding Security Boundary

Grounding layer phải preserve authorization.

```text
User Identity
      ↓
Agent Identity / Delegation
      ↓
Access Policy
      ↓
Knowledge Source
      ↓
Only authorized context returned
```

Exam trap:

> Retrieval result đã lọc đúng semantic relevance nên không cần authorization filter.

Sai. Relevance không thay thế access control.

---

# 10. Scenario Drill

## Scenario A

Enterprise policy documents nằm trong Microsoft 365 và thay đổi hàng tuần. Người dùng chỉ được xem policy theo business unit.

Architectural answer phải bao gồm:

- reuse governed enterprise knowledge path;
- freshness/update strategy;
- authorization trimming;
- grounding rather than copying everything into prompts;
- traceability/source citation.

## Scenario B

Agent phải trả current inventory quantity theo SKU.

Tốt hơn:

```text
Deterministic business-system query/action
```

thay vì semantic RAG trên inventory export.

## Scenario C

Agent cần tìm relevant design standards từ 20,000 documents.

Tốt hơn:

```text
search/retrieval + metadata + grounding
```

thay vì đưa toàn bộ documents vào model context.

---

# 11. Exam Traps

1. **RAG cho mọi dữ liệu** — sai; transactional data thường hợp API/query hơn.
2. **Memory = knowledge** — sai.
3. **Copy enterprise data sang agent-specific store mặc định** — tăng governance risk.
4. **Semantic relevance = authorization** — sai.
5. **Grounding tốt nhưng data stale** — vẫn là bad architecture.
6. **Chọn platform trước khi biết source of truth** — đảo dependency.

---

# 12. Oral Checkpoint

Không nhìn note, trả lời:

1. Năm tiêu chí đánh giá grounding data là gì?
2. Knowledge khác memory thế nào?
3. Khi nào direct API/query tốt hơn RAG?
4. Vì sao timeliness là architecture concern?
5. Tại sao shared knowledge không đồng nghĩa shared full permission?
6. Source of truth ảnh hưởng kiến trúc agent thế nào?
7. Metadata filtering dùng để giải quyết vấn đề gì?
8. Vì sao không nên copy cùng enterprise data vào mỗi agent?
9. Transactional data và unstructured knowledge nên tích hợp khác nhau thế nào?
10. Grounding layer phải preserve security bằng cách nào?

## PASS CONDITION

- 8/10 câu trả lời rõ ràng;
- phân biệt được knowledge/memory/context/state;
- chọn đúng direct query vs retrieval trong ít nhất 4/5 scenario.

---

# 13. Mapping to BD Chunk / Harness

```text
RD / Standards / Templates
       ↓
Governed Knowledge Layer
       ↓
Retriever / Source Access
       ↓
Parser / Builder / Reviewer
```

Kiến trúc phải giữ:

- source provenance;
- document version;
- access boundary;
- retrieval trace;
- freshness;
- artifact-to-source traceability.

Day 16 output: **Knowledge Architecture Decision Matrix** cho capstone.