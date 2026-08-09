# DAY 21 — AB-100 FULL ARCHITECTURE REVIEW + EXAM READINESS

> Certification: Microsoft Agentic AI Business Solutions Architect (AB-100)
> Role in sprint: Final AB-100 consolidation day before moving into Titan / Frontier Project Ready
> Baseline: 2026-08-09

---

# 1. Day 21 Goal

Không học thêm nhiều concept mới.

Mục tiêu là chứng minh bạn có thể đi từ business problem đến production agentic architecture mà không phụ thuộc vào một sản phẩm Microsoft duy nhất.

Canonical flow:

```text
Business Outcome
      ↓
Process / Pain Point
      ↓
AI Opportunity Assessment
      ↓
Build / Buy / Extend
      ↓
Platform Selection
      ↓
Agent / Workflow Architecture
      ↓
Knowledge + Tools + Integration
      ↓
Security + Responsible AI
      ↓
ALM + Deployment
      ↓
Monitoring + Governance
      ↓
Adoption + ROI
```

PASS nghĩa là bạn có thể giải thích từng decision point và trade-off.

---

# 2. Official AB-100 Mental Model

Microsoft mô tả candidate AB-100 là một solution architect có khả năng thiết kế và triển khai AI-driven business solutions đa dịch vụ, scalable, secure, integrated, với agent-first architecture và multi-agent orchestration.

Vì vậy exam thinking không phải:

> "Feature này nằm ở menu nào?"

Mà là:

> "Với constraint này, architecture nào là phù hợp nhất và tại sao?"

---

# 3. Architecture Review — Layer 1: Business Outcome

Trước khi chọn agent, trả lời:

- Business outcome là gì?
- Process hiện tại tốn thời gian ở đâu?
- Quyết định nào cần judgment?
- Step nào deterministic?
- Step nào cần human accountability?
- Value đo bằng gì?

## Exam trap

Không chọn multi-agent chỉ vì scenario nhắc tới nhiều team.

Multi-agent chỉ hợp lý khi có separation of goals, capabilities, context, permissions, or lifecycle.

---

# 4. Architecture Review — Layer 2: Build / Buy / Extend

Decision tree:

```text
Existing Microsoft capability solves most of requirement?
        │
   Yes ─┴─ No
    ↓       ↓
 Extend   Build custom
```

Consider:

- Microsoft 365 Copilot
- Copilot Studio
- Microsoft Foundry
- Power Platform
- Dynamics 365
- custom application

## Must explain

- Why use Copilot Studio instead of a fully custom Foundry app?
- When does a custom application become justified?
- When should you extend an existing Copilot surface rather than create a new user experience?

---

# 5. Architecture Review — Layer 3: Agentic Architecture

Classify each processing unit:

```text
Deterministic Node
Tool
Single Agent
Specialist Agent
Orchestrator Agent
Human Review
```

Decision checklist:

- Need reasoning?
- Need autonomy?
- Need iterative planning?
- Need its own tools?
- Need its own permission boundary?
- Need independent context/memory?

## Principle

> Do not turn every workflow step into an agent.

Runtime owns execution semantics; agents own reasoning where reasoning is genuinely needed.

---

# 6. Architecture Review — Layer 4: Integration

Tool-facing integration:

```text
Agent
 ↓
MCP / API / Connector
 ↓
Enterprise Capability
```

Agent-to-agent integration:

```text
Agent A
 ↓
A2A / explicit artifact contract
 ↓
Agent B
```

Must distinguish:

- MCP vs A2A
- tool call vs agent handoff
- data retrieval vs action execution
- synchronous call vs long-running workflow

---

# 7. Architecture Review — Layer 5: Knowledge

Decision sequence:

```text
Source of Truth
      ↓
Access Pattern
      ↓
Direct Read / Search / RAG
      ↓
Grounded Context
      ↓
Agent
```

Evaluate source data on:

- accuracy
- relevance
- timeliness
- cleanliness
- availability
- permissions

Do not use RAG by default if the source is small and already available in-context.

---

# 8. Architecture Review — Layer 6: Security + Responsible AI

For every agent/action ask:

```text
Who is the identity?
What can it read?
What can it write?
Which tools can it call?
What action requires approval?
What is audited?
```

Controls:

- least privilege
- managed identity / secure authentication
- environment isolation
- secrets management
- prompt-injection defenses
- data-loss controls
- human approval for high-risk actions
- auditability
- data residency / compliance

Core principle:

> Agent autonomy must not exceed the permission boundary.

---

# 9. Architecture Review — Layer 7: ALM + Deployment

Lifecycle:

```text
DEV
 ↓
TEST
 ↓
EVALUATE
 ↓
APPROVE
 ↓
DEPLOY
 ↓
MONITOR
 ↓
TUNE / ROLLBACK
```

Version independently:

- agent
- prompt/instruction
- model configuration
- tool
- schema
- knowledge/index
- evaluation dataset
- workflow

Exam trap:

"Prompt update" is still a production change and can require testing/evaluation.

---

# 10. Architecture Review — Layer 8: Monitoring + Business Value

Technical signals:

- success/error rate
- task completion
- groundedness
- tool-call success
- latency
- token/cost use
- safety events
- human escalation rate

Business signals:

- adoption
- cycle-time reduction
- quality improvement
- employee/customer impact
- operational cost
- TCO
- ROI

Must connect technical telemetry to business outcome.

---

# 11. Full Scenario Drill

Scenario:

A large enterprise wants to transform requirements documents into solution-design artifacts. Requirements contain sensitive data. Several specialist teams contribute to validation and design. Some steps are deterministic, while ambiguous decisions require AI reasoning. High-impact generated artifacts must be approved before publication.

Design an architecture.

## Expected reasoning sequence

1. Define business outcome and acceptance metrics.
2. Identify deterministic vs reasoning steps.
3. Decide existing product vs custom/extended architecture.
4. Select Foundry / Copilot Studio / Power Platform / M365 surfaces as appropriate.
5. Define agent boundaries.
6. Define tool/MCP boundaries.
7. Define knowledge and grounding approach.
8. Define contracts/handoffs.
9. Define identity and permission model.
10. Insert human approval at high-risk gate.
11. Define ALM/versioning.
12. Define telemetry/evaluation.
13. Define governance ownership.
14. Define ROI/adoption measurement.

---

# 12. Oral Checkpoint — 15 Questions

Without notes, answer:

1. Why start from business outcome instead of from an agent?
2. Build vs Buy vs Extend — what drives the decision?
3. Copilot Studio vs Foundry — what is the architectural distinction?
4. When is a workflow node not an agent?
5. When is multi-agent justified?
6. MCP vs A2A?
7. RAG vs direct source access?
8. State vs memory vs knowledge?
9. Why should runtime own deterministic execution?
10. How do you apply least privilege to agents?
11. How do you reduce prompt-injection risk?
12. What must be versioned in an agentic system?
13. What would you monitor in production?
14. How do technical metrics map to ROI?
15. What does a Center of Excellence govern?

## PASS CONDITION

- 13/15 clear answers: READY
- 10–12: REVIEW WEAK AREAS
- <10: DO NOT RUSH THE EXAM

---

# 13. Final AB-100 Exam Heuristics

When stuck in a scenario:

1. Protect business/security constraints first.
2. Prefer supported, governed platform capabilities over unnecessary custom complexity.
3. Use deterministic workflows where deterministic logic is sufficient.
4. Use agents where reasoning/autonomy adds clear value.
5. Apply least privilege and explicit approval to sensitive actions.
6. Ground AI in trusted data.
7. Treat monitoring/evaluation as architecture, not afterthought.
8. Include ALM and governance from design time.
9. Optimize for measurable business outcomes, not maximum AI sophistication.

---

# 14. Exit From Certification Sprint

After completing Day 21:

```text
AI-103
  +
GH-300
  +
AB-100
   ↓
Foundational certification layer complete conceptually
   ↓
Move to Titan / Frontier Project Ready
```

The next stage is not another normal exam-prep unit. It is delivery readiness: hands-on Project Ready learning/assessments plus delivery-pattern fluency such as Center of Excellence and Hypervelocity Engineering.

---

# 15. Official References

- AB-100 study guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ab-100
- Microsoft Partner Frontier engineer skilling: https://partner.microsoft.com/zh-cn/blog/article/skilling-updates-2026-issue-5
