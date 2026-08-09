# AB-100 Day 17 — Security, Responsible AI, Risk, and Compliance

> Track: Frontier / Titan Certification Sprint  
> Certificate: AB-100 — Agentic AI Business Solutions Architect  
> Focus: Deploy AI-powered business solutions  
> Study guide baseline: Skills measured as of 2026-07-22

---

# 1. Day 17 Goal

Kết thúc buổi này phải architect được một agentic solution sao cho autonomy không vượt khỏi security boundary.

Mental model:

```text
Identity
 ↓
Authorization
 ↓
Data / Tool Access
 ↓
Agent Action
 ↓
Policy / Guardrail
 ↓
Audit / Monitoring
```

Core principle:

> Agent capability is not permission. Permission must be explicitly granted and governed.

---

# 2. Official Objective Mapping

Map vào AB-100 study guide:

- design security for agents;
- design governance for agents;
- design model security;
- analyze vulnerabilities and mitigations, including prompt manipulation;
- review adherence to Responsible AI principles;
- validate data residency and movement compliance;
- design access controls on grounding data and model tuning;
- design audit trails for changes to models and data.

---

# 3. Security Surface of an Agentic Solution

```text
Agentic Solution
├── User identity
├── Agent identity
├── Model access
├── Tool permissions
├── Knowledge permissions
├── Secrets
├── Network boundary
├── Prompt / instruction surface
├── Data movement
└── Audit trail
```

Không chỉ bảo vệ API key.

---

# 4. Identity and Least Privilege

Bad pattern:

```text
All agents
   ↓
One shared service account
   ↓
All enterprise tools
```

Preferred principle:

```text
Agent Role
   ↓
Minimum required identity/permission
   ↓
Specific tool/data boundary
```

Ví dụ:

```text
Parser Agent   → read RD only
Builder Agent  → read RD + write draft artifact
Reviewer Agent → read artifacts + findings
Publisher      → publish only after approval
```

---

# 5. User Identity vs Agent Identity

Hai câu hỏi khác nhau:

1. User có quyền yêu cầu action này không?
2. Agent/service có quyền thực thi action này không?

Một design tốt có thể cần:

```text
User
 ↓ authenticates
Application / Agent
 ↓ authorization context
Tool / Data Source
```

Exam trap:

> Vì user đã đăng nhập, agent có thể dùng toàn bộ quyền của service account.

Sai. Service permission vẫn phải least privilege và ideally preserve user/business authorization context.

---

# 6. Prompt Manipulation / Prompt Injection

Threat mental model:

```text
Untrusted Input
      ↓
Attempts to override instructions
      ↓
Agent reasoning
      ↓
Potential tool/data misuse
```

Mitigation không chỉ là "system prompt mạnh hơn".

Architectural controls:

- separate trusted instructions from untrusted content;
- validate/sanitize inputs where applicable;
- constrain tool permissions;
- require approval for high-risk actions;
- retrieve only authorized data;
- validate tool arguments/results;
- monitor suspicious behavior;
- use deterministic policy gates around critical actions.

---

# 7. Responsible AI

Solution Architect phải đánh giá:

```text
Fairness
Reliability & Safety
Privacy & Security
Inclusiveness
Transparency
Accountability
```

Trong exam scenario, Responsible AI không chỉ là content filter.

Ví dụ:

- user cần biết khi nào đang tương tác với AI;
- high-impact decision cần human accountability;
- evaluation phải bao gồm harmful/unfair outcomes;
- audit trail phải cho phép điều tra decision path.

---

# 8. Human Approval as Security Control

```text
Low-risk action
→ automatic

High-risk / irreversible action
→ approval gate
```

Ví dụ:

```text
Draft recommendation → automatic
Send customer contract → approval
Delete production data → approval / deterministic control
```

Principle:

> Human-in-the-loop belongs in workflow/runtime control, not merely in agent instructions.

---

# 9. Data Residency and Movement

Phải biết hỏi:

```text
Where is source data stored?
Where is it processed?
Where is model hosted?
Where are logs/traces stored?
Does data cross region/tenant boundary?
```

Data residency không chỉ áp dụng source database; prompts, retrieved context, traces, evaluation datasets và tuning data cũng có thể tạo movement risk.

---

# 10. Grounding and Tuning Access Controls

Phân biệt:

```text
Grounding data
= source used at inference/retrieval time

Tuning data
= data used to adapt/customize model behavior
```

Cả hai cần:

- access control;
- approved data ownership;
- sensitivity review;
- lineage;
- audit.

---

# 11. Audit Trail

A production agentic system nên trace:

```text
Who
requested what
when
using which agent/model/version
with which knowledge/tool
what action occurred
what approval happened
what result was produced
```

Audit trail khác application debug log.

Debug log giúp engineer sửa lỗi.
Audit trail giúp accountability/compliance/investigation.

---

# 12. Model Security

Architectural questions:

- ai nào được deploy model?
- ai được thay model/version/config?
- tuning data được bảo vệ thế nào?
- endpoint exposed ở đâu?
- model change có approval/version trace không?
- fallback/model router có thể route sang model vi phạm policy không?

---

# 13. Scenario Drills

## Scenario A — HR Agent

Agent đọc employee data và đề xuất promotion.

Architecture phải xem xét:

- sensitive data access;
- fairness;
- explainability/transparency;
- human decision ownership;
- audit trail;
- least privilege.

## Scenario B — Customer Support Agent

Knowledge source chứa cả public docs và internal-only escalation playbooks.

Không cho agent retrieve tất cả rồi "hy vọng prompt không leak".

Phải enforce access at knowledge/retrieval boundary.

## Scenario C — Procurement Agent

Agent có tool `approve_purchase`.

Nếu business threshold > $10,000 cần manager approval, policy này phải nằm trong deterministic authorization/workflow gate.

---

# 14. Exam Traps

1. **System prompt = security boundary** — sai.
2. **Content safety = Responsible AI đầy đủ** — sai.
3. **User authenticated = agent can access everything** — sai.
4. **Logs = audit trail automatically** — không đủ.
5. **Prompt injection solved by instruction hierarchy only** — sai.
6. **Data residency chỉ concern database** — sai.
7. **Agent autonomy nên tối đa để tăng productivity** — không phải architecture goal.

---

# 15. Oral Checkpoint

1. Agent capability khác agent permission thế nào?
2. User identity khác agent/service identity thế nào?
3. Vì sao prompt injection là architecture problem chứ không chỉ prompt problem?
4. Sáu nhóm Responsible AI principles cần nhớ là gì?
5. Khi nào HITL trở thành security control?
6. Grounding data và tuning data khác nhau thế nào?
7. Audit trail cần ghi gì?
8. Data residency phải kiểm tra ở những lớp nào?
9. Vì sao tool permission phải least privilege?
10. Một deterministic policy gate tốt hơn LLM decision trong trường hợp nào?

## PASS CONDITION

- 8/10 oral questions;
- giải đúng 4/5 scenario về access/prompt injection/HITL;
- không dùng "prompt" như security control duy nhất.

---

# 16. Mapping to BD Chunk / Harness

```text
User
 ↓
Workflow Runtime
 ↓ policy gate
Agent
 ↓
Allowed Tools / Knowledge
 ↓
Artifact
 ↓
Review / Approval
 ↓
Audit Trail
```

Day 17 output: **Security & Responsible AI Boundary Map**.