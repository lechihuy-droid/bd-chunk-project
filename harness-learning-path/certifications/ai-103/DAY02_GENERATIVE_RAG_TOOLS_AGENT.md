# AI-103 DAY 2 — GENERATIVE AI, RAG, TOOLS, AGENTS

> Track: Frontier / Titan 21-day certification sprint  
> Certificate: AI-103 — Azure AI Apps and Agents Developer Associate  
> Day focus: the highest-value generative AI + agentic concepts  
> Learning mode: voice-first, concept-first, exam-oriented

---

# 1. Day 2 Goal

Day 2 tập trung vào phần cốt lõi nhất của AI-103: xây generative AI application và agentic solution có grounding, tools, memory, orchestration, safeguards và evaluation.

Kết thúc buổi học phải giải thích được flow sau mà không nhìn note:

```text
Application
  ↓
Foundry Project
  ↓
Model / Agent
  ↓
Prompt + Context
  ↓
Knowledge / RAG
  ↓
Tool Calling
  ↓
State / Memory
  ↓
Workflow / Multi-Agent
  ↓
Safeguards
  ↓
Evaluation / Trace
```

---

# 2. Module 2.1 — Generative AI Application Anatomy

## Mental model

Một generative AI application không chỉ là một prompt gọi model.

```text
User / System Input
      ↓
Application Logic
      ↓
Model / Agent
      ↓
Context + Tools + Knowledge
      ↓
Structured / Unstructured Output
      ↓
Validation + Evaluation
```

## Phải phân biệt

### Model application

Model nhận input và trả output.

### Agentic application

Agent có goal, instructions, tools, context, state, memory và execution behavior để hoàn thành task.

### Workflow application

Workflow xác định thứ tự chạy, branch, retry, checkpoint, human approval và deterministic control.

## Oral question

> Một application gọi LLM hai lần liên tiếp đã phải là agent chưa? Vì sao?

### Expected answer direction

Không. Số lần gọi model không quyết định tính agentic. Cần xem hệ thống có goal-directed behavior, tool use, state, decision loop hoặc autonomous reasoning hay không.

---

# 3. Module 2.2 — Prompt vs Context

## Core distinction

```text
Prompt / Instruction
= model phải làm gì

Context
= thông tin model đang có để làm việc đó
```

Prompt tốt không cứu được context sai.

Context tốt nhưng instruction mơ hồ cũng tạo output không ổn định.

## Prompt structure

```text
Goal
+
Context
+
Constraints
+
Expected Output
```

## Example — RD Parser

```text
Goal:
Extract atomic requirements.

Context:
Current RD section + metadata.

Constraints:
Do not invent missing facts.
Preserve source traceability.

Expected Output:
RequirementBlock JSON objects.
```

## Exam trap

Đừng chọn “rewrite prompt” nếu root cause thật sự là retrieval/context bị thiếu hoặc source sai.

---

# 4. Module 2.3 — Structured Output and Contracts

## Mental model

```text
Agent Output
     ↓
Output Contract
     ↓
Structural Validation
     ↓
Semantic / Domain Validation
     ↓
Accepted Artifact
```

## Structural validation

Kiểm tra:

- required fields;
- types;
- enum values;
- JSON shape;
- schema compatibility.

## Semantic / domain validation

Kiểm tra:

- source fidelity;
- business correctness;
- consistency giữa các fields;
- requirement có thực sự tồn tại trong source hay không;
- output có vi phạm domain rule hay không.

## Important correction

Contract có thể mô tả cả structural obligations và semantic obligations.

Nhưng schema/Pydantic chủ yếu enforce phần machine-checkable. Domain validator chịu trách nhiệm cho business/source correctness.

## Oral question

> Parser trả đủ mọi field nhưng `original_text` không tồn tại trong source document. Lỗi này thuộc structural hay semantic validation?

Expected: semantic/domain validation.

---

# 5. Module 2.4 — RAG and Grounding

## Canonical RAG flow

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

## RAG solves what problem?

RAG giúp model sử dụng knowledge bên ngoài model weights tại thời điểm inference.

Dùng khi knowledge:

- lớn;
- thay đổi thường xuyên;
- enterprise-specific;
- không muốn nhét toàn bộ vào prompt;
- cần traceability / grounding.

## Không phải lúc nào cũng cần RAG

Nếu một file nhỏ đã được cung cấp đầy đủ và vừa context window thì direct read có thể đơn giản và đáng tin hơn.

## Search modes

### Keyword search

Phù hợp exact term, mã, tên field, identifier.

### Vector search

Phù hợp semantic similarity.

### Semantic search

Dùng semantic ranking/understanding để tăng relevance.

### Hybrid search

Kết hợp keyword + vector để tận dụng cả exact match và semantic similarity.

## Exam trap

Nếu scenario vừa cần exact identifier vừa cần semantic recall, hybrid search thường hợp lý hơn pure vector.

---

# 6. Module 2.5 — Knowledge vs Context vs Memory

```text
Knowledge
= external source of truth

Context
= information supplied to current model call

Memory
= information intentionally retained for future reuse
```

Example:

```text
Enterprise RD repository
→ Knowledge

Top 5 retrieved RD chunks sent to model
→ Context

User-approved naming convention stored for next sessions
→ Memory
```

## Oral question

> RAG result được đưa vào prompt của model. Nó là knowledge hay context?

Answer: source/index là knowledge; retrieved content khi đưa vào current call trở thành context.

---

# 7. Module 2.6 — Tools and Function Calling

## Mental model

```text
Agent
  ↓
Select Tool
  ↓
Tool Call
  ↓
External Operation / Data
  ↓
Tool Result
  ↓
Agent Continues Reasoning
```

## Tool contract

Tool nên có:

- name;
- purpose;
- input schema;
- output contract;
- permissions;
- error semantics;
- timeout behavior.

## Examples

```text
read_document(document_id)
search_requirements(query)
get_schema(schema_name)
create_artifact(payload)
```

## Tool vs Knowledge

Tool thực hiện bounded operation.

Knowledge là source dùng để retrieve/reference.

Một search service có thể được expose như tool để agent truy cập knowledge.

## Exam trap

Không chọn LLM reasoning để thay thế operation deterministic có API/tool rõ ràng.

---

# 8. Module 2.7 — API vs MCP

## API

Service-specific interface để gọi capability.

## MCP

Standardized protocol/interface pattern giúp AI application/agent discover và gọi tools/resources theo một contract chung.

```text
Agent
  ↓
MCP Client
  ↓
MCP Server
  ↓
Tools / Resources
```

## Important

MCP không phải agent.

MCP không thay workflow runtime.

MCP không đồng nghĩa A2A.

## Oral question

> Nếu một service đã có REST API, tại sao vẫn có thể expose nó qua MCP?

Expected direction: chuẩn hóa discovery/tool contract/integration cho agent ecosystem, giảm coupling với service-specific implementation.

---

# 9. Module 2.8 — Conversation Tracking, State and Memory

## Conversation tracking

Agent cần biết current conversation/run đang ở đâu.

```text
Conversation History
       ↓
Current Context
       ↓
Agent Decision
       ↓
Optional Memory Update
```

## State

Current execution status.

Examples:

- current document id;
- current workflow stage;
- validation status;
- pending approval.

## Memory

Reusable information across later turns/runs.

Examples:

- user preference;
- approved terminology;
- prior decisions;
- learned stable facts.

## Exam trap

Không lưu toàn bộ raw history mãi mãi nếu không cần. Memory phải intentional và scoped.

---

# 10. Module 2.9 — Multi-Agent Orchestration

AI-103 cần nhận diện orchestrated multi-agent solution.

## Sequential

```text
A → B → C
```

Use when output A là prerequisite cho B.

## Parallel

```text
   ┌→ B
A ─┤
   └→ C
```

Use khi B/C độc lập.

## Supervisor

```text
      Supervisor
      /   |   \
     A    B    C
```

Use khi cần reasoning để chọn specialist.

## Reviewer pattern

```text
Builder
   ↓
Reviewer
 ├─ approve
 └─ revise
```

## Architectural rule

```text
Workflow Runtime
= owns deterministic execution semantics

LLM Agent
= owns reasoning where reasoning is needed
```

Không nên để LLM tự kiểm soát mọi branch nếu graph rule đủ xác định.

---

# 11. Module 2.10 — Safeguards and Human Approval

## Mental model

```text
Agent Action
   ↓
Risk / Policy Gate
   ├── Allowed → Execute
   └── Sensitive → Human Approval
```

Human approval là runtime/workflow state transition.

Không chỉ là instruction kiểu “ask user before doing X”.

## Sensitive examples

- write/delete operation;
- external message;
- irreversible change;
- privileged data access;
- expensive action;
- regulated decision.

---

# 12. Module 2.11 — Evaluation and Observability

## Quality dimensions

- relevance;
- correctness;
- groundedness;
- hallucination/fabrication;
- safety;
- task completion;
- tool correctness.

## Trace model

```text
Run Trace
├── Model Call
├── Tool Call
├── Retrieval
├── Token Usage
├── Latency
├── Safety Signal
└── Agent Decision
```

## Root-cause mindset

Nếu output sai, hỏi:

1. prompt sai?
2. context sai?
3. retrieval sai?
4. tool result sai?
5. model reasoning sai?
6. validator thiếu?
7. workflow route sai?

---

# 13. Day 2 Exam Traps

1. RAG không phải Memory.
2. MCP không phải Agent.
3. Tool không phải Knowledge.
4. Prompt tốt không thay thế grounding.
5. Structural validation không chứng minh business correctness.
6. Multi-agent không mặc định tốt hơn single-agent.
7. Human approval phải nằm trong control flow.
8. Deterministic routing nên giữ deterministic khi có thể.

---

# 14. Day 2 Voice Checkpoint

Không nhìn note, trả lời:

1. Prompt khác Context thế nào?
2. RAG khác Memory thế nào?
3. Tool khác Knowledge thế nào?
4. API khác MCP thế nào?
5. Structural khác semantic validation thế nào?
6. Khi nào direct read tốt hơn RAG?
7. Khi nào hybrid search phù hợp?
8. Vì sao workflow runtime không nên giao hết cho LLM?
9. Human approval nên được model hóa thế nào?
10. Trace giúp debug agent ra sao?

## PASS CONDITION

- 8/10 câu trả lời rõ nghĩa;
- không nhầm RAG/Memory;
- không nhầm MCP/A2A;
- giải thích được deterministic workflow vs agent reasoning.

---

# 15. Hands-on Mapping

Day 2 chưa yêu cầu API key.

Các concept sẽ được kiểm chứng ở integrated hands-on:

```text
RD Parser Agent
  ↓
Output Contract
  ↓
RAG / Direct Read Decision
  ↓
Tool / MCP Interface
  ↓
Validator
  ↓
Workflow
```

---

# 16. Final Day 2 Sentence

> Agent tốt không chỉ reasoning tốt; nó phải được grounding đúng, gọi đúng tool, tuân thủ contract, chạy trong workflow có kiểm soát và có thể được evaluate/trace.