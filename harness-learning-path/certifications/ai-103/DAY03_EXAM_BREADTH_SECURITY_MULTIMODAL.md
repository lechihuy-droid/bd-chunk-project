# AI-103 DAY 3 — EXAM BREADTH, SECURITY, MULTIMODAL, EXTRACTION

> Track: Frontier / Titan 21-day certification sprint  
> Certificate: AI-103 — Azure AI Apps and Agents Developer Associate  
> Day focus: close all non-agentic exam gaps + exam consolidation  
> Learning mode: voice-first, scenario-first, exam-oriented

---

# 1. Day 3 Goal

Day 3 không đào sâu thêm một agent pattern mới. Mục tiêu là phủ đủ breadth của AI-103 để tránh lệch syllabus.

Kết thúc ngày 3 phải nhìn được một Azure AI solution end-to-end:

```text
Plan
 ↓
Select Model / Service
 ↓
Build
 ↓
Ground / Extract / Understand
 ↓
Secure
 ↓
Deploy
 ↓
Monitor
 ↓
Evaluate
 ↓
Operate
```

Các nhóm cần đóng gap:

- Responsible AI + security;
- computer vision / multimodal;
- text analysis / speech;
- information extraction;
- deployment / scaling / monitoring;
- Python/SDK literacy;
- final exam reasoning.

---

# 2. Module 3.1 — Responsible AI

## Mental model

Responsible AI không phải một filter đặt ở cuối pipeline.

```text
Design
 ↓
Data / Context
 ↓
Model
 ↓
Agent / Tool
 ↓
Output
 ↓
Monitoring
```

Risk controls phải xuất hiện xuyên suốt lifecycle.

## Concepts cần nắm

- harmful content;
- prompt injection / manipulation;
- hallucination / fabrication;
- privacy;
- bias / unfair outcomes;
- human oversight;
- grounding;
- transparency;
- auditability.

## Exam mindset

Nếu scenario hỏi cách giảm hallucination từ enterprise knowledge, ưu tiên grounding/retrieval/evaluation thay vì chỉ “thêm system prompt”.

Nếu action có hậu quả lớn, cân nhắc approval / human oversight.

---

# 3. Module 3.2 — Identity, Access and Secrets

## Core model

```text
Agent / App Identity
       ↓
Authorization Policy
       ↓
Allowed Resource / Tool
```

## Concepts

### Managed Identity

Giúp workload authenticate với Azure resource mà không phải hard-code secret.

### RBAC

Xác định identity nào được phép làm gì trên resource nào.

### Secret handling

Không hard-code key/token trong source code.

### Least privilege

Agent chỉ nên có đúng permission cần cho role.

## Example

```text
Parser Agent
→ read source documents

Builder Agent
→ read source + write generated artifact

Reviewer
→ read artifact + findings
```

## Exam trap

Không cấp broad admin access chỉ vì triển khai nhanh hơn.

---

# 4. Module 3.3 — Network, Data and Governance Awareness

Ở mức AI-103 cần hiểu rằng production AI solution có boundary về:

- data access;
- private/public connectivity;
- resource permissions;
- logging/audit;
- content safety;
- data residency/compliance considerations.

Không cần biến Day 3 thành khóa network engineering, nhưng phải nhận ra security là architecture requirement.

---

# 5. Module 3.4 — Computer Vision and Multimodal

## Multimodal mental model

```text
Text
Image
Audio
Video
  ↓
Multimodal / Specialized AI Service
  ↓
Understanding / Generation / Extraction
```

## Phải nhận diện use case

### Image understanding

- describe visual content;
- identify entities/objects;
- answer questions about images;
- reason across text + image.

### Image generation

Generate new visual content from instructions.

### Video / richer multimodal

Use model/service phù hợp khi input không chỉ là text.

## Decision rule

Nếu requirement phụ thuộc information nằm trong hình/chart/layout, text-only model với plain extracted text có thể làm mất signal quan trọng.

---

# 6. Module 3.5 — Content Understanding

Content Understanding giúp chuyển unstructured/multimodal content thành representation có cấu trúc để downstream AI reasoning sử dụng.

## Mental model

```text
Document / Image / Audio / Video
       ↓
Content Understanding
       ↓
Structured Fields / Markdown / Semantic Representation
       ↓
Search / Agent / Workflow
```

## BD Chunk mapping

```text
RD PDF
├── paragraphs
├── tables
├── diagrams
└── metadata
      ↓
understanding / extraction
      ↓
Requirement representation
```

## Exam trap

Nếu task cần giữ layout/table/structure, đừng mặc định plain OCR text là đủ.

---

# 7. Module 3.6 — Text Analysis

## Typical capabilities

- entity extraction;
- key phrases / topics;
- summarization;
- sentiment / opinion;
- classification;
- language detection;
- translation-related scenarios;
- safety/moderation depending on service/scenario.

## Mental model

```text
Raw Text
  ↓
Text Analysis
  ↓
Structured Signal
  ↓
Application / Workflow
```

## Example

Customer feedback pipeline:

```text
Feedback
 ↓
Language
 ↓
Sentiment
 ↓
Entities / Topics
 ↓
Routing / Dashboard
```

## Exam trap

Nếu requirement chỉ cần deterministic text analytics capability, không phải lúc nào cũng cần general-purpose LLM agent.

---

# 8. Module 3.7 — Speech

## Capabilities

```text
Speech-to-Text
Text-to-Speech
Speech Translation / Voice Scenarios
```

## Decision examples

Meeting transcription → speech-to-text.

Voice assistant response → text-to-speech.

Real-time multilingual voice workflow → speech + translation capability.

## Exam mindset

Chọn modality/service theo input-output requirement, không theo sở thích framework.

---

# 9. Module 3.8 — Information Extraction

Đây là phần rất gần RD → BD.

## Canonical flow

```text
Document
 ↓
OCR / Layout / Content Understanding
 ↓
Structured Extraction
 ↓
Normalize
 ↓
Index / Search
 ↓
Agent / Downstream Workflow
```

## Extraction vs Generation

```text
Extraction
= lấy facts/structure từ source

Generation
= tạo output mới dựa trên instruction/context
```

Không dùng generative reasoning để thay extraction deterministic nếu service chuyên dụng giải quyết tốt hơn.

## Source fidelity

Extraction solution cần giữ:

- page/section;
- offsets / source references nếu có;
- field confidence;
- original text/value;
- structure/layout khi cần.

---

# 10. Module 3.9 — Search and Index Health

Knowledge/RAG production phụ thuộc cả retrieval layer.

Monitor:

- indexing success;
- freshness;
- query quality;
- relevance;
- latency;
- failed ingestion;
- stale data.

## Root-cause example

Agent trả lời sai không nhất thiết do model.

Nếu index cũ hoặc chunking sai → context sai → model có thể reasoning đúng trên dữ liệu sai.

---

# 11. Module 3.10 — Deployment, Scaling and Quotas

## Lifecycle

```text
Code / Config
 ↓
CI/CD
 ↓
Deployment
 ↓
Traffic
 ↓
Monitor
 ↓
Scale / Tune
```

## Concepts

- model deployment;
- endpoint;
- quota;
- rate limit;
- capacity;
- latency;
- retries;
- cost.

## Exam trap

Nếu errors xuất hiện dưới high traffic, kiểm tra quota/rate-limit/capacity trước khi kết luận model có vấn đề.

---

# 12. Module 3.11 — Evaluation in Production

## Offline evaluation

Dùng dataset/test cases trước release.

## Online/production monitoring

Theo dõi real traffic và behavior.

## Metrics

```text
Quality
Groundedness
Safety
Latency
Cost
Tool Success
Retrieval Quality
Task Completion
```

## Regression mindset

Prompt/model/tool/index thay đổi đều có thể tạo regression.

Không chỉ version code.

---

# 13. Module 3.12 — Python / SDK Literacy

AI-103 không phải coding challenge, nhưng candidate cần đọc được code và nhận diện concepts.

## Phải nhận ra

```python
client = ...
project = ...
model = ...
agent = ...
result = ...
```

và hiểu:

- client initialization;
- credentials;
- model/agent invocation;
- structured output;
- tool/function definition;
- async/await concept;
- exception handling;
- SDK object lifecycle.

## Không cần rush

- thuật toán phức tạp;
- advanced Python internals;
- framework-specific magic.

## Voice question

> `await` trong agent code gợi ý điều gì về execution?

Expected direction: asynchronous operation; code có thể chờ I/O/model/tool call mà không block theo cách synchronous thông thường.

---

# 14. Module 3.13 — Architecture Selection Scenarios

## Scenario A

Requirement: hỏi đáp trên policy repository lớn, tài liệu cập nhật hàng tuần, cần citation.

Likely pattern:

```text
Search / RAG + grounding + evaluation
```

Không fine-tune chỉ để cập nhật knowledge hàng tuần.

## Scenario B

Requirement: đọc invoice/scanned form, extract fields, giữ page reference.

Likely pattern:

```text
OCR / layout / content extraction
→ structured fields
```

## Scenario C

Requirement: agent cần gọi API xóa record, nhưng phải có manager approval.

Likely pattern:

```text
Agent decision
→ policy gate
→ human approval
→ tool execution
```

## Scenario D

Requirement: support text + screenshot trong cùng conversation.

Likely pattern:

```text
Multimodal model / visual understanding
```

---

# 15. AI-103 Full Mental Map

```text
PLAN / MANAGE
├── model choice
├── infrastructure
├── deployment
├── quota / cost
├── security
└── monitoring

GENERATIVE + AGENTIC
├── prompts/context
├── RAG
├── tools
├── memory
├── agent
├── multi-agent
├── safeguards
└── evaluation

VISION
├── image understanding
├── multimodal
└── content understanding

TEXT / SPEECH
├── entities
├── sentiment
├── summary
├── translation
└── speech

INFORMATION EXTRACTION
├── OCR
├── layout
├── structured extraction
├── indexing
└── search/retrieval
```

---

# 16. Day 3 Exam Traps

1. “Use bigger model” không phải default fix.
2. Fine-tuning không phải cách tốt nhất để đưa frequently changing enterprise knowledge vào model.
3. Plain OCR không luôn đủ khi layout/table quan trọng.
4. General LLM không thay mọi specialized AI service.
5. Managed Identity tốt hơn hard-coded secret cho Azure workload authentication.
6. RBAC/least privilege quan trọng với agent tools.
7. Model quality không phải metric production duy nhất.
8. Retrieval/index failure có thể trông giống model hallucination.
9. Human approval phải nằm trong workflow.
10. Deployment issue có thể là quota/rate-limit/capacity issue.

---

# 17. Final AI-103 Voice Checkpoint

Không nhìn tài liệu, trả lời 15 câu:

1. Khi nào chọn SLM thay vì LLM lớn?
2. Foundry khác Agent Service thế nào?
3. RAG khác fine-tuning cho changing knowledge thế nào?
4. Hybrid search giải quyết gì?
5. Tool khác knowledge thế nào?
6. Managed Identity giải quyết vấn đề gì?
7. RBAC dùng để làm gì?
8. Khi nào cần multimodal model?
9. OCR khác Content Understanding ở mức mental model thế nào?
10. Extraction khác generation thế nào?
11. Vì sao index health ảnh hưởng agent quality?
12. Offline eval khác production monitoring thế nào?
13. Quota/rate limit ảnh hưởng app thế nào?
14. Human approval nên đặt ở đâu?
15. Một production agent solution cần monitor những gì ngoài answer quality?

## PASS CONDITION

- ≥ 12/15 rõ nghĩa;
- không nhầm RAG/fine-tuning;
- không nhầm extraction/generation;
- hiểu least privilege;
- hiểu model + retrieval + tool + runtime đều có thể là root cause.

---

# 18. AI-103 Exit Gate

Trước khi chuyển GH-300, phải có thể kể bằng lời flow này trong 3–5 phút:

```text
Business Task
  ↓
Choose Azure AI / Foundry capability
  ↓
Choose Model
  ↓
Ground / Extract / Retrieve
  ↓
Agent + Tools
  ↓
Workflow / Approval
  ↓
Security
  ↓
Deploy
  ↓
Evaluate / Monitor
```

Nếu kể được flow và giải thích trade-off ở mỗi bước, phần conceptual AI-103 rush hoàn tất.

---

# 19. Next Step

Sau Day 3:

```text
AI-103 Concept Rush Complete
        ↓
GH-300 Day 4
GitHub Copilot Fundamentals + Responsible Use
```

Không thực hành API ngay. Implementation được giữ cho 4 integrated hands-on sessions sau GH-300.