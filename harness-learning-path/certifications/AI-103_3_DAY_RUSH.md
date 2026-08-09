# AI-103 — 3-DAY CERTIFICATION RUSH

> Certification: **Microsoft Certified: Azure AI Apps and Agents Developer Associate**  
> Exam: **AI-103 — Developing AI Apps and Agents on Azure**  
> Track role: **Certificate #1** in the Frontier / Titan 21-day certification sprint  
> Baseline: 2026-08-09  
> Official skills measured: **as of 2026-04-16**

---

# 1. Objective

Trong 3 ngày, mục tiêu không phải mastery toàn bộ Azure AI engineering.

Mục tiêu là tạo đủ **exam vocabulary + mental model + architecture recognition + code literacy** để:

1. hiểu toàn bộ scope AI-103;
2. nhận diện đúng Microsoft Foundry service / pattern theo scenario;
3. giải thích được agentic solution end-to-end;
4. đọc được Python/SDK snippets ở mức exam;
5. chuẩn bị chuyển sang GH-300 và 4 integrated hands-on sessions;
6. có nền tảng đủ chắc để bước tiếp vào AB-100.

```text
AI-103
= Foundry foundation
+ Generative AI
+ Agents
+ RAG / Search
+ Multimodal
+ Text / Speech
+ Information Extraction
+ Security / Responsible AI
+ Evaluation / Operations
```

---

# 2. Official Exam Blueprint

AI-103 hiện đánh giá 5 nhóm kỹ năng:

| Official skill area | Weight |
|---|---:|
| Plan and manage an Azure AI solution | 25–30% |
| Implement generative AI and agentic solutions | 30–35% |
| Implement computer vision solutions | 10–15% |
| Implement text analysis solutions | 10–15% |
| Implement information extraction solutions | 10–15% |

## Exam profile

Microsoft mô tả candidate là Azure AI Engineer có khả năng:

- build AI solutions;
- manage AI solutions;
- deploy agents and AI solutions;
- use Microsoft Foundry;
- develop applications using Python;
- work with Azure AI, generative AI, and Azure services.

Exam duration hiện được Microsoft công bố là **120 minutes**.

Microsoft certification exams require a score of **700 or higher** to pass.

---

# 3. Rush Strategy

Không chia nội dung theo thứ tự course 4 ngày của Microsoft.

Ta nén lại theo dependency:

```text
DAY 1
Platform + Architecture
        ↓
DAY 2
Generative AI + Agentic Core
        ↓
DAY 3
Breadth + Security + Operations + Exam Review
```

Tỷ lệ ưu tiên:

```text
45% Agentic + Generative AI
25% Foundry architecture / operations
30% Vision + Text + Information Extraction
```

Lưu ý: tỷ lệ học không hoàn toàn giống tỷ lệ exam vì agentic concepts là prerequisite để hiểu nhiều scenario khác.

---

# 4. Learning Mode

3 ngày đầu ưu tiên **voice-first / concept-first**.

Không yêu cầu API key.

Không yêu cầu build production app ngay.

Mỗi concept học theo cycle:

```text
Official Objective
      ↓
Mental Model
      ↓
Microsoft Terminology
      ↓
Explain by Voice
      ↓
Scenario Question
      ↓
Exam-style Checkpoint
```

Python chỉ học ở mức:

- đọc SDK code;
- nhận biết client / project / model / agent / tool;
- hiểu async/function/tool schema;
- đọc structured-output snippets;
- hiểu exception/error handling ở mức khái niệm.

Implementation thực tế được dời sang **4 integrated hands-on sessions** sau GH-300.

---

# DAY 1 — FOUNDRY, MODEL, AGENT, PLATFORM

## Day 1 Goal

Kết thúc ngày 1 phải hiểu được:

```text
Azure / Foundry Platform
        ↓
Model
        ↓
Agent
        ↓
Tools / Knowledge
        ↓
Workflow
        ↓
Multi-Agent
        ↓
Runtime / Monitoring / Security
```

---

## Module 1.1 — Model Selection

Official AI-103 objective yêu cầu chọn model phù hợp cho task.

Phân biệt:

- Large Language Model — LLM
- Small Language Model — SLM
- Code model
- Multimodal model
- Foundry Tools

### Mental model

```text
Task Requirement
      ↓
Modality
      ↓
Reasoning Complexity
      ↓
Latency / Cost
      ↓
Model Choice
```

### Phải trả lời được

- Vì sao không phải lúc nào model lớn hơn cũng tốt hơn?
- Khi nào cần multimodal model?
- Khi nào task có thể dùng small model?
- Model choice ảnh hưởng latency/cost thế nào?

---

## Module 1.2 — Microsoft Foundry Landscape

Nắm các khái niệm:

```text
Microsoft Foundry
├── Project
├── Model Catalog / Model Choice
├── Model Deployment
├── Endpoint
├── SDK / Connectors
├── Tools
├── Knowledge / Search
├── Agent Service
├── Evaluation
└── Monitoring
```

### Distinction cần thuộc

```text
Model
≠
Agent
≠
Agent Framework
≠
Agent Service
≠
Foundry Platform
```

### Foundry vs Harness

```text
Harness
= architectural/runtime pattern surrounding an LLM/agent

Microsoft Foundry
= Microsoft platform providing services to build, deploy,
  evaluate, secure, and operate AI solutions
```

Foundry có thể cung cấp nhiều capability của một harness, nhưng hai khái niệm không đồng nhất.

---

## Module 1.3 — Agent Anatomy

Canonical agent model:

```text
Agent
├── Role
├── Goal
├── Model
├── Instructions
├── Input Contract
├── Output Contract
├── Tools
├── Knowledge
├── Conversation / State
├── Memory
├── Guardrails
└── Evaluation
```

### Core distinctions

#### Model vs Agent

```text
Model
= generates / reasons from input

Agent
= goal-directed system that uses a model plus tools,
  instructions, context, state, and control behavior
```

#### Tool vs Agent

```text
Tool
= capability invoked to perform a bounded operation

Agent
= decides how/when capabilities are used toward a goal
```

#### Workflow Node vs Agent

```text
Node
= execution step

Node may be:
- deterministic function
- tool
- agent
- validator
- human review
```

Không biến mọi node thành agent.

---

## Module 1.4 — State, Context, Memory, Knowledge

Phân biệt 4 khái niệm:

```text
Context
= information available to the model now

State
= current execution state of the workflow/run

Memory
= information intentionally retained for later reuse

Knowledge
= external source of truth available for retrieval/use
```

### Example

```text
Current requirement being processed
→ State

Text sent into current LLM call
→ Context

User preference stored across sessions
→ Memory

Enterprise requirement repository
→ Knowledge
```

---

## Module 1.5 — Azure AI Solution Setup

Official objectives yêu cầu hiểu:

- Azure infrastructure for AI apps;
- deployment options;
- model deployments;
- agent deployments;
- CI/CD integration.

### Mental model

```text
Source Code
 ↓
CI/CD
 ↓
Foundry Project
 ↓
Model / Agent Deployment
 ↓
Application
 ↓
Monitor
```

Không cần code CI/CD trong rush phase, nhưng phải hiểu lifecycle.

---

## Module 1.6 — Operations Basics

Official objectives:

- quotas;
- scaling;
- rate limits;
- cost footprint;
- model performance;
- drift;
- safety events;
- grounding quality;
- search index health.

### Exam mental model

```text
Production AI System
├── Availability
├── Latency
├── Cost
├── Quality
├── Safety
├── Grounding
└── Search Health
```

Một AI system production không chỉ được đánh giá bằng "câu trả lời có hay không".

---

# DAY 1 CHECKPOINT

Không nhìn note, giải thích bằng lời:

1. Foundry khác Harness thế nào?
2. Model khác Agent thế nào?
3. Tool khác Agent thế nào?
4. Workflow node có bắt buộc là agent không?
5. Context, State, Memory, Knowledge khác nhau thế nào?
6. Agent Service khác Agent Framework thế nào?
7. Vì sao production AI cần quota, rate limit và cost monitoring?

## PASS CONDITION

Có thể trả lời 6/7 câu rõ nghĩa mà không dùng keyword mơ hồ.

---

# DAY 2 — GENERATIVE AI, RAG, TOOLS, AGENTS

## Day 2 Goal

Đây là ngày quan trọng nhất vì nhóm **Generative AI and Agentic Solutions chiếm 30–35% exam**.

Kết thúc ngày 2 phải hiểu:

```text
Prompt / Model
      ↓
RAG / Grounding
      ↓
Tool Calling
      ↓
Agent
      ↓
Memory
      ↓
Workflow
      ↓
Multi-Agent
      ↓
Evaluation
```

---

## Module 2.1 — Generative AI Application

Official objectives:

- deploy/consume LLMs, SLMs, code and multimodal models;
- RAG;
- workflows;
- tool-augmented flows;
- multistep reasoning;
- model/app evaluation;
- SDK/connectors;
- connect app to Foundry project.

### Mental model

```text
Application
 ↓
Foundry Project
 ↓
Model / Agent
 ↓
Tools + Knowledge
 ↓
Result
```

---

## Module 2.2 — Prompt vs Context

```text
Prompt / Instruction
= what the model should do

Context
= information supplied so the model can do it
```

Prompt quality không thể bù cho context thiếu hoặc sai.

### Prompt structure

```text
Goal
+
Context
+
Constraints
+
Expected Output
```

---

## Module 2.3 — Structured Output and Contracts

```text
Agent Output
      ↓
Output Contract
      ↓
Structural Validation
      ↓
Domain Validation
```

### Structural validation

Kiểm tra:

- required fields;
- type;
- schema;
- shape.

### Semantic / domain validation

Kiểm tra:

- source fidelity;
- business rule;
- meaning;
- cross-field consistency.

### Important correction

Output contract có thể mô tả cả structural và semantic obligations.

Nhưng schema/Pydantic chỉ enforce được phần machine-checkable; domain validator chịu trách nhiệm cho business/source correctness.

---

## Module 2.4 — RAG

Canonical flow:

```text
Source
 ↓
Ingest
 ↓
Chunk
 ↓
Enrich
 ↓
Index
 ↓
Retrieve
 ↓
Grounded Context
 ↓
Model / Agent
```

### Phải phân biệt

- keyword search;
- semantic search;
- vector search;
- hybrid search.

### Decision question

Khi nào dùng RAG?

```text
Large / external / changing knowledge
→ Retrieval

Small document already available in context
→ Direct read may be enough
```

RAG không phải default cho mọi file.

---

## Module 2.5 — Tools and Function Calling

```text
Agent
 ↓
Choose Tool
 ↓
Tool Call
 ↓
External Operation
 ↓
Tool Result
 ↓
Reasoning Continues
```

Tool contract cần có:

- name;
- purpose;
- input schema;
- output shape;
- permissions;
- error semantics.

Official AI-103 expects integration with:

- APIs;
- knowledge stores;
- search;
- Content Understanding;
- custom functions.

---

## Module 2.6 — MCP Mental Model

MCP không phải một skill area riêng có weight trong AI-103 blueprint, nhưng là kiến thức integration hữu ích cho Frontier track.

```text
Agent
 ↓
MCP Client
 ↓
MCP Server
 ↓
Tools / Resources
```

Phân biệt:

```text
API
= service-specific interface

MCP
= standardized protocol/interface pattern for exposing
  tools/resources to AI applications/agents
```

Không nhầm MCP với A2A.

---

## Module 2.7 — Agent Memory and Conversation Tracking

Official objectives yêu cầu:

- define conversation-tracking approach;
- integrate conversation memory.

Mental model:

```text
Conversation History
        ↓
Current Context
        ↓
Agent Decision
        ↓
Optional Memory Update
```

Không copy toàn bộ history mãi mãi.

Memory phải phục vụ task, không chỉ lưu mọi thứ.

---

## Module 2.8 — Multi-Agent Orchestration

Official AI-103 explicitly includes orchestrated multi-agent solutions.

Patterns cần nhận diện:

```text
Sequential
A → B → C
```

```text
Parallel
   ┌→ B
A ─┤
   └→ C
```

```text
Supervisor
      S
    / | \
   A  B  C
```

```text
Reviewer
Builder → Reviewer
          ├─ approve
          └─ revise
```

### Architectural principle

```text
Workflow Runtime
= owns execution semantics

LLM Agent
= owns reasoning where reasoning is needed
```

Không giao toàn bộ execution control cho LLM nếu deterministic routing đủ.

---

## Module 2.9 — Safeguards and Approval Flows

Official objectives include autonomous/semi-autonomous workflows with safeguards and approval controls.

```text
Agent Action
 ↓
Risk / Policy Gate
 ├── Allowed → Execute
 └── Sensitive → Human Approval
```

Human approval là workflow control, không phải chỉ là prompt.

---

## Module 2.10 — Evaluation and Observability

Evaluation dimensions:

- fabrication/hallucination;
- relevance;
- quality;
- safety;
- grounding;
- tool correctness;
- task completion.

Observability:

```text
Trace
├── Model Call
├── Tool Call
├── Token Usage
├── Latency
├── Safety Signal
└── Agent Decision
```

Official objectives also include error analysis, tracing, token analytics, safety signals, and latency breakdowns.

---

# DAY 2 CHECKPOINT

Giải thích được:

1. Prompt khác Context thế nào?
2. RAG khác Memory thế nào?
3. Tool khác Knowledge thế nào?
4. API khác MCP thế nào?
5. Structural validation khác semantic validation thế nào?
6. Khi nào workflow node nên deterministic thay vì agent?
7. Multi-agent orchestration giải quyết gì mà single agent không giải quyết tốt?
8. Human approval nằm ở agent prompt hay runtime/workflow?

## PASS CONDITION

7/8 câu rõ ràng, kèm ít nhất một example.

---

# DAY 3 — EXAM BREADTH, SECURITY, RESPONSIBLE AI, REVIEW

## Day 3 Goal

Ngày 3 đảm bảo không mắc lỗi phổ biến: học Agent rất sâu nhưng bỏ mất 30–45% exam còn lại.

---

# Module 3.1 — Responsible AI

Official objectives:

- safety filters;
- guardrails;
- risk detection;
- content moderation;
- safety evaluation;
- explanation tooling;
- trace logging;
- provenance metadata;
- approval workflows;
- oversight modes;
- constraints;
- tool-access controls.

### Mental model

```text
Input
 ↓
Safety / Policy
 ↓
Agent / Model
 ↓
Tool Permission
 ↓
Output Safety
 ↓
Audit / Trace
```

Responsible AI không phải một final output filter duy nhất.

Nó trải xuyên lifecycle.

---

# Module 3.2 — Security

Official objectives include:

- managed identity;
- private networking;
- keyless credentials;
- role policies.

### Security mental model

```text
Identity
 ↓
Authorization
 ↓
Resource Access
 ↓
Tool Access
 ↓
Audit
```

Principle:

> Agent autonomy must not exceed its permission boundary.

---

# Module 3.3 — Computer Vision: 10–15%

## Generation / Editing

Know conceptually:

- text-to-image;
- reference-media generation;
- text-to-video;
- image editing;
- inpainting;
- masks;
- prompt-driven modification;
- video editing.

## Multimodal Understanding

Understand:

- visual context analysis;
- captions;
- visual question answering;
- alt text;
- accessibility descriptions;
- Content Understanding;
- video analysis;
- object/component/region identification.

## Multimodal Safety

Know:

- unsafe visual content filtering;
- indirect prompt injection through image text;
- watermark/policy/brand requirements.

---

# Module 3.4 — Text Analysis: 10–15%

Know how to choose/recognize solutions for:

- entity extraction;
- topic extraction;
- summarization;
- structured JSON output;
- sentiment;
- tone;
- safety/sensitive content;
- translation;
- domain summarization;
- domain extraction.

## Speech

Know:

- speech-to-text;
- text-to-speech;
- speech modality for agents;
- custom speech models;
- reasoning from audio;
- speech translation.

---

# Module 3.5 — Information Extraction: 10–15%

Đây là phần rất gần với RD → BD use case.

## Retrieval and Grounding Pipeline

```text
Document / Image / Audio / Video
             ↓
           Ingest
             ↓
       OCR / Enrichment
             ↓
           Index
             ↓
Semantic / Vector / Hybrid Search
             ↓
        Grounded Context
             ↓
      Workflow / Agent
```

Official objectives include:

- ingest/index content;
- semantic search;
- hybrid search;
- vector search;
- enrichment skills;
- OCR;
- connect retrieval to workflows and agent tools.

## Document Extraction

Know:

```text
Document
 ↓
OCR
 ↓
Layout Analysis
 ↓
Field Extraction
 ↓
Grounded Structured Representation
 ↓
Agent / RAG
```

Content Understanding can produce structured or markdown outputs for downstream reasoning.

---

# Module 3.6 — Optimization and Operationalization

Official AI-103 objectives include:

- prompt engineering;
- model parameters;
- reflection;
- self-critique loops;
- tracing;
- token analytics;
- safety signals;
- latency breakdowns;
- multi-model orchestration;
- hybrid LLM/rules engines.

### Important mental model

```text
LLM
+
Rules
+
Tools
+
Workflow
```

Production AI is often hybrid, not "LLM does everything".

---

# Module 3.7 — Python / SDK Literacy

AI-103 candidate profile expects Python experience.

Trong 3-day rush, cần đọc được pseudo-code / real code ở mức sau:

```python
client = ...
project = ...
model = ...
agent = ...
result = agent.run(...)
```

Phải nhận ra:

- client initialization;
- authentication;
- model deployment reference;
- agent creation/configuration;
- tool declaration;
- structured output;
- exception/error handling;
- result evaluation.

Không cần thuộc SDK method names bằng trí nhớ nếu objective đang kiểm tra architecture choice.

---

# 5. DAY 3 FINAL REVIEW

## Whiteboard test

Không nhìn note, nói lại architecture:

```text
Business / App Requirement
        ↓
Choose Foundry Service
        ↓
Choose Model
        ↓
Deployment
        ↓
Agent / Workflow
        ↓
Tools + Knowledge
        ↓
RAG / Search / Extraction
        ↓
Security / Guardrails
        ↓
Evaluation / Trace
        ↓
Production Monitoring
```

Nếu nói được từng layer và giải thích "tại sao layer này tồn tại", mental model đã đạt.

---

# 6. EXAM-STYLE DECISION FRAMEWORK

Khi gặp scenario, không nhảy ngay vào product name.

Dùng sequence:

```text
1. What is the task?
2. What modality?
3. Does it need external knowledge?
4. Does it need action/tool use?
5. Does it need autonomous decisions?
6. Does it need workflow orchestration?
7. What security boundary exists?
8. How will quality be evaluated?
9. How will it be monitored in production?
```

Sau đó mới chọn Foundry capability.

---

# 7. HIGH-PRIORITY CONFUSION PAIRS

Phải thuộc rõ:

| A | B |
|---|---|
| Model | Agent |
| Agent | Tool |
| Agent | Workflow Node |
| Context | Memory |
| State | Memory |
| Knowledge | Memory |
| RAG | Fine-tuning |
| Vector Search | Semantic Search |
| Hybrid Search | Vector Search |
| Structural Validation | Domain Validation |
| Agent Framework | Agent Service |
| Foundry | Harness |
| API | MCP |
| Runtime Control | Agent Reasoning |
| Guardrail | Evaluation |
| Authentication | Authorization |
| OCR | Content Understanding |

---

# 8. FOUR HANDS-ON ITEMS DEFERRED UNTIL AFTER GH-300

Không cố nhồi implementation vào 3-day rush.

AI-103 concepts sẽ được kiểm chứng sau GH-300 qua 4 sessions:

## Hands-on 1 — Design One Agent

```text
RD Parser Agent
```

Define:

- role;
- goal;
- input/output;
- tools;
- knowledge;
- memory;
- guardrails;
- evaluation.

## Hands-on 2 — Tool + RAG + MCP

```text
Agent
 ↓
Tool / MCP
 ↓
Retrieval
 ↓
Grounded Result
```

## Hands-on 3 — Workflow + Multi-Agent

```text
Parser
 ↓
Validator
 ↓
Builder
 ↓
Reviewer
```

Classify every step as:

- agent;
- deterministic node;
- tool;
- human gate.

## Hands-on 4 — Copilot Builds the Agent

```text
Architect
 ↓
Agent Contract
 ↓
GitHub Copilot / Coding Agent
 ↓
Implementation
 ↓
Tests
 ↓
Review / Eval
```

---

# 9. 3-DAY EXIT CRITERIA

AI-103 rush phase được coi là complete khi:

- [ ] Explain Foundry architecture without notes.
- [ ] Explain Model vs Agent vs Tool vs Workflow.
- [ ] Explain State vs Context vs Memory vs Knowledge.
- [ ] Explain RAG and search options.
- [ ] Explain function/tool calling.
- [ ] Explain orchestrated multi-agent patterns.
- [ ] Explain safeguards / HITL.
- [ ] Explain evaluation and observability.
- [ ] Recognize computer vision and multimodal scenarios.
- [ ] Recognize text/speech scenarios.
- [ ] Explain information extraction with OCR/layout/Content Understanding.
- [ ] Explain managed identity / RBAC / keyless / private networking conceptually.
- [ ] Read simple Python/SDK snippets without needing to write from scratch.
- [ ] Complete one full oral mock review of all five official skill areas.

---

# 10. FINAL AI-103 MENTAL MODEL

```text
PLAN
Choose model + Foundry services
        ↓
BUILD
Generative App / Agent / Workflow
        ↓
GROUND
Search + RAG + Content Understanding
        ↓
ACT
Tools + Functions + Multi-Agent
        ↓
PROTECT
Identity + Security + Guardrails
        ↓
EVALUATE
Quality + Safety + Grounding
        ↓
OPERATE
Trace + Cost + Scale + Monitoring
```

If this chain is clear, AI-103 stops being a list of Azure products and becomes one coherent architecture.

---

# 11. Official Microsoft References

- AI-103 Study Guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103
- Certification: https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-apps-and-agents-developer-associate/
- Course AI-103T00-A: https://learn.microsoft.com/en-us/training/courses/ai-103t00
- Azure AI developer resources: https://learn.microsoft.com/en-us/azure/developer/ai/

> Re-check the official study guide immediately before booking the exam because Microsoft periodically updates exam objectives.
