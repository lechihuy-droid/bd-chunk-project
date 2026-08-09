# GH-300 DAY 4 — GITHUB COPILOT FUNDAMENTALS + RESPONSIBLE USE

> Track: Frontier / Titan 21-day certification sprint  
> Certificate: GH-300 — GitHub Copilot  
> Day focus: conceptual foundation before prompt/context and agent mode  
> Learning mode: voice-first, scenario-first, exam-oriented

---

# 1. Day 4 Goal

Sau 3 ngày AI-103, mindset chuyển từ:

```text
Build an AI Agent
```

sang:

```text
Use AI to engineer software safely and productively
```

Kết thúc Day 4 phải hiểu GitHub Copilot như một development capability, không chỉ là autocomplete.

Mental map:

```text
Developer Intent
      ↓
Repository / IDE Context
      ↓
GitHub Copilot
      ↓
Suggestion / Chat / Edit / Agentic Action
      ↓
Developer Review
      ↓
Code / Tests / Docs / Review Outcome
```

---

# 2. Module 4.1 — What GitHub Copilot Is

GitHub Copilot hỗ trợ developer trong software development lifecycle thông qua AI-assisted interaction với code và repository context.

## Capability classes

- inline code completion;
- chat / question answering;
- code explanation;
- refactoring;
- test generation;
- documentation assistance;
- code review assistance;
- multi-file edits;
- agentic execution modes;
- CLI / terminal assistance;
- context-aware repository work.

## Important distinction

```text
Copilot
≠ compiler
≠ test runner
≠ source of truth
≠ autonomous authority
```

Copilot tạo đề xuất hoặc thực hiện agentic actions trong phạm vi được cấp, nhưng developer vẫn chịu trách nhiệm xác minh kết quả.

---

# 3. Module 4.2 — Completion vs Chat vs Edit vs Agentic Mode

## Inline completion

```text
Current file context
      ↓
Code suggestion
```

Tốt cho:

- boilerplate;
- predictable code continuation;
- repetitive patterns;
- small local implementation.

## Chat

```text
Question + Context
      ↓
Explanation / Suggestion / Code
```

Tốt cho:

- explanation;
- architecture questions;
- debugging guidance;
- code understanding;
- targeted generation.

## Multi-file edit capability

Dùng khi change ảnh hưởng nhiều file nhưng vẫn theo instruction tương đối rõ.

## Agentic mode

```text
Task
 ↓
Inspect
 ↓
Plan
 ↓
Edit
 ↓
Run tool/test
 ↓
Observe result
 ↓
Iterate
```

Đây là bước quan trọng nối GH-300 với AI-103 agent concepts.

## Oral question

> Khi nào nên dùng inline completion thay vì agent mode?

Expected direction: task nhỏ, local, deterministic/predictable, không cần inspect nhiều file hay iterative execution.

---

# 4. Module 4.3 — Developer Remains Accountable

AI-generated code có thể:

- compile nhưng sai business logic;
- pass simple tests nhưng fail edge cases;
- chứa insecure pattern;
- dùng obsolete API;
- hallucinate package/function;
- violate repository conventions;
- create licensing/IP concerns depending on use and context.

## Core principle

> AI accelerates engineering judgment; it does not replace engineering judgment.

Developer phải review:

```text
Correctness
Security
Maintainability
Performance
Tests
Repository conventions
Business intent
```

---

# 5. Module 4.4 — Responsible AI in Software Engineering

## Risk classes

### Hallucination

Copilot có thể generate API/function không tồn tại hoặc logic nghe hợp lý nhưng sai.

### Insecure code

Ví dụ:

- hard-coded secret;
- weak input validation;
- unsafe deserialization;
- overly broad permission;
- SQL injection pattern;
- insecure auth flow.

### Sensitive data exposure

Không đưa secrets/private data vào context nếu policy không cho phép.

### Over-reliance

Developer không được merge code chỉ vì AI nói “looks good”.

## Exam mindset

Nếu question hỏi best practice cho AI-generated code → review + tests + security validation thường quan trọng hơn “trust model because repository context was provided”.

---

# 6. Module 4.5 — Validation Loop

Canonical engineering loop:

```text
Generate
 ↓
Inspect
 ↓
Test
 ↓
Static / Security Check
 ↓
Review
 ↓
Accept / Revise
```

Đây là equivalent software-engineering của agent evaluation loop.

## Mapping to AI-103

```text
AI-103 Agent Output
      ↓
Validator / Evaluation

GH-300 Generated Code
      ↓
Tests / Review / Security Checks
```

Cả hai đều cần external verification.

---

# 7. Module 4.6 — Repository Context

Copilot quality phụ thuộc context mà tool/IDE cung cấp.

Potential context:

- current file;
- open files;
- selected code;
- repository structure;
- referenced files;
- instructions;
- documentation;
- terminal/test output;
- issue/task description.

## Principle

```text
Better relevant context
≠ more context indiscriminately
```

Context phải đúng scope và relevant.

## Oral question

> Vì sao đưa toàn bộ repository vào context không luôn tốt hơn?

Expected: noise, token/context limits, irrelevant information, conflicting patterns, privacy/security concerns.

---

# 8. Module 4.7 — Human-in-the-Loop for Coding Agents

Agentic coding có thể edit files và run tools, nhưng high-impact actions vẫn cần review/control.

## Example

```text
Coding Agent
   ↓
Proposed change
   ↓
Tests
   ↓
Human Review
   ↓
Merge / Reject
```

## Critical distinction

```text
Coding Agent
= agent helping build software

Application Agent
= agent being built as part of product
```

GitHub Copilot Agent có thể build RD Parser Agent, nhưng hai agent có role và lifecycle khác nhau.

---

# 9. Module 4.8 — Copilot Across the SDLC

Think beyond code generation.

```text
Requirement
 ↓
Understand codebase
 ↓
Design
 ↓
Implement
 ↓
Test
 ↓
Review
 ↓
Document
 ↓
Maintain
```

Copilot có thể hỗ trợ ở nhiều stage, nhưng governance và validation thay đổi theo stage.

## Example

Debugging:

```text
Error + Logs + Relevant Code
      ↓
Copilot Analysis
      ↓
Hypothesis
      ↓
Developer verifies
      ↓
Fix + Test
```

---

# 10. Module 4.9 — Security and Privacy Awareness

## Security mindset

Copilot không nên được cấp context hoặc permissions vượt nhu cầu task.

Potential controls:

- organization policy;
- repository policy;
- content exclusion / context controls where supported;
- secret scanning;
- code scanning;
- branch protection;
- review requirement;
- least privilege for tools.

## Mapping from AI-103

```text
AI Agent least privilege
        ↕
Coding Agent least privilege
```

Same principle, different environment.

---

# 11. Module 4.10 — Productivity Without Quality Regression

GH-300 không chỉ quan tâm “generate faster”.

Good productivity means:

```text
Faster delivery
+
maintained/improved quality
+
controlled security risk
+
maintainability
```

Bad productivity:

```text
More code generated
but
more defects / review burden / security issues
```

## Metric thinking

Useful signals can include:

- time-to-complete task;
- review cycle time;
- test coverage impact;
- defect rate;
- adoption;
- developer satisfaction;
- security findings.

---

# 12. Day 4 Scenario Drills

## Scenario A

Task: implement one obvious getter method matching existing pattern.

Best mode likely: inline completion.

Why: local, predictable, low-complexity.

## Scenario B

Task: refactor authentication across five files, run tests, fix failures.

Best mode likely: agentic/multi-file workflow with human review.

## Scenario C

Copilot generates code using a package that does not exist.

Classification: hallucination / validation failure.

Action: verify dependency/docs, correct code, test.

## Scenario D

Copilot suggests hard-coded API key.

Action: reject; use appropriate secret management mechanism.

## Scenario E

Agent changes repository code and reports tests pass.

Do not assume correctness. Inspect actual test results/change diff and apply normal engineering review.

---

# 13. Day 4 Exam Traps

1. Copilot output is not automatically trusted because it was generated from repository context.
2. More context is not always better context.
3. Agent mode is not required for every task.
4. Human accountability remains even when agent runs tests.
5. AI-generated tests can also be wrong or incomplete.
6. Generated code still requires security scanning/review.
7. Productivity is not equal to number of generated lines.
8. Coding agent and application agent are different concepts.
9. Repository policy and organization governance matter.
10. Do not expose sensitive data unnecessarily to AI context.

---

# 14. Day 4 Voice Checkpoint

Không nhìn note, trả lời:

1. GitHub Copilot khác compiler thế nào?
2. Inline completion khác Chat thế nào?
3. Khi nào Agent Mode có lợi hơn completion?
4. Vì sao AI-generated code vẫn phải review?
5. Nêu ba loại risk của AI-generated code.
6. Repository context ảnh hưởng output thế nào?
7. Vì sao “more context” không luôn tốt hơn?
8. Coding Agent khác Application Agent thế nào?
9. Human-in-the-loop trong coding workflow nằm ở đâu?
10. Productivity với Copilot nên được hiểu như thế nào?

## PASS CONDITION

- 8/10 câu rõ nghĩa;
- không xem Copilot là source of truth;
- phân biệt được completion/chat/agentic mode;
- hiểu developer accountability.

---

# 15. Connection to Day 5

Day 4 trả lời câu hỏi:

> Copilot là gì và dùng nó có trách nhiệm ra sao?

Day 5 sẽ trả lời:

> Làm thế nào để Copilot nhận đúng intent và đúng context để thực hiện task?

```text
Day 4
Copilot Capability
      ↓
Day 5
Prompt + Context Engineering
```

---

# 16. Final Day 4 Sentence

> GitHub Copilot là AI development capability giúp tăng tốc SDLC, nhưng chất lượng cuối cùng vẫn phụ thuộc context, validation, security controls và engineering judgment của con người.