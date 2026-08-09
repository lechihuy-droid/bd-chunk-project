# AB-100 Day 18 — Governance, Environment Strategy, and AI Center of Excellence

> Track: Frontier / Titan Certification Sprint  
> Certificate: AB-100 — Agentic AI Business Solutions Architect  
> Focus: Plan + Deploy AI-powered business solutions  
> Study guide baseline: Skills measured as of 2026-07-22

---

# 1. Day 18 Goal

Chuyển mental model từ **một agent tốt** sang **một enterprise agent portfolio được govern tốt**.

```text
Single Agent
   ↓
Team Solution
   ↓
Agent Portfolio
   ↓
Enterprise Governance
   ↓
AI Center of Excellence
```

AB-100 yêu cầu architect không chỉ thiết kế solution mà còn định nghĩa cách tổ chức quản lý, scale, kiểm soát và cải tiến AI lâu dài.

---

# 2. Official Objective Mapping

Map vào study guide:

- include elements of the Microsoft AI Center of Excellence;
- design governance for agents;
- create cohesive environment strategy for AI-powered solutions;
- create ALM/governance strategies across Copilot Studio, Foundry and business apps;
- guide organizations toward AI-forward operating models.

---

# 3. Governance Mental Model

```text
Governance
├── Who may build?
├── What may be built?
├── Which data may be used?
├── Which models/tools are approved?
├── How is risk classified?
├── How is deployment approved?
├── How is usage monitored?
└── How are agents retired?
```

Governance không phải chỉ là security policy.

Security hỏi: "ai được truy cập gì?"
Governance hỏi rộng hơn: "solution này được tạo, thay đổi, vận hành và retire theo luật nào?"

---

# 4. AI Center of Excellence — Purpose

CoE không nhất thiết là một team viết mọi agent.

Mental model:

```text
AI CoE
├── Standards
├── Reference architectures
├── Approved platforms/models
├── Security/governance patterns
├── Reusable components
├── Evaluation standards
├── Enablement / training
├── FinOps / cost guidance
└── Portfolio oversight
```

CoE nên **enable + govern**, không trở thành bottleneck cho mọi change nhỏ.

---

# 5. Centralized vs Federated Governance

## Fully centralized

Ưu:
- consistency;
- control.

Nhược:
- bottleneck;
- domain teams chậm.

## Fully decentralized

Ưu:
- tốc độ;
- domain autonomy.

Nhược:
- duplication;
- inconsistent security;
- khó audit.

## Federated model

```text
Central CoE
→ policies / standards / shared capabilities

Domain Teams
→ business-specific solutions within guardrails
```

Đây thường là mental model cân bằng hơn cho enterprise scale.

---

# 6. Environment Strategy

Phải tách rõ:

```text
DEV
 ↓
TEST
 ↓
UAT / PRE-PROD
 ↓
PROD
```

Environment separation áp dụng cho:

- agent definitions;
- connectors/actions;
- models/model configs;
- prompts;
- knowledge/indexes;
- secrets;
- test data;
- telemetry.

Exam trap:

> Dùng cùng production agent và knowledge source cho testing để đảm bảo realistic.

Sai nếu gây data/security/change-control risk.

---

# 7. Agent Registry / Portfolio View

Enterprise nên biết ít nhất:

```text
Agent ID
Owner
Business purpose
Risk classification
Platform
Model
Tools
Knowledge sources
Permissions
Environment
Version
Status
Last evaluation
```

Nếu organization không biết có bao nhiêu agent đang hoạt động, governance gần như không tồn tại.

---

# 8. Lifecycle Governance

```text
Idea
 ↓
Assessment
 ↓
Prototype
 ↓
Security / Responsible AI Review
 ↓
Test / Evaluation
 ↓
Approval
 ↓
Production
 ↓
Monitor
 ↓
Change / Retire
```

Retirement là một lifecycle stage thật.

Phải xử lý:
- credential revoke;
- tool access revoke;
- knowledge access revoke;
- archive audit data;
- user communication;
- dependency migration.

---

# 9. Risk-Tiered Governance

Không cần cùng mức approval cho mọi agent.

Ví dụ:

```text
Tier 1 — Low Risk
Draft / summarize public content

Tier 2 — Medium Risk
Internal recommendations / business actions

Tier 3 — High Risk
Financial, HR, legal, irreversible actions
```

Governance controls tăng theo risk:

- evaluation depth;
- human approval;
- security review;
- monitoring;
- audit retention.

---

# 10. Reuse vs Proliferation

Bad pattern:

```text
Every team builds
its own prompt library
its own connector
its own RAG pipeline
its own evaluation rules
```

Preferred enterprise pattern:

```text
Shared approved capabilities
        ↓
Domain-specific composition
```

CoE nên thúc đẩy reusable assets:

- prompt library;
- tool/connectors;
- evaluation datasets;
- policy gates;
- reference architectures;
- templates.

---

# 11. Model / Tool Governance

Governance questions:

- model nào được approve?
- preview model có được production không?
- tool nào được connect?
- external MCP server có trust level nào?
- third-party agent/service được phép xử lý data gì?
- model/router change cần approval nào?

Agentic architecture mở rộng attack/governance surface vì agent không chỉ generate text mà còn **act**.

---

# 12. Cost Governance / FinOps

Enterprise governance phải quan tâm:

```text
Token usage
Model choice
Agent loop depth
Tool/API cost
Retrieval cost
Storage/index cost
Human review cost
```

Một agent accurate nhưng loop 20 lần cho mỗi task có thể không viable về TCO.

---

# 13. Scenario Drills

## Scenario A

50 business units muốn build Copilot/agents.

Solution tốt không phải "CoE build tất cả" mà nên:

- central policy/reference architecture;
- approved platforms/tools;
- domain ownership;
- risk tiering;
- portfolio inventory;
- shared evaluation/governance patterns.

## Scenario B

Một low-risk internal summarizer cần 4 approval committees trước mỗi prompt change.

Governance quá nặng có thể phá adoption. Chọn controls proportional to risk.

## Scenario C

Một external MCP integration mới được thêm bởi domain team.

Cần review:
- trust;
- authentication;
- permissions;
- data movement;
- audit;
- lifecycle owner.

---

# 14. Exam Traps

1. **Governance = security** — quá hẹp.
2. **CoE phải build mọi solution** — sai.
3. **Một governance process cho mọi risk tier** — thiếu proportionality.
4. **Chỉ inventory production agents** — shadow/prototype agents cũng cần visibility tùy policy.
5. **Retire agent = delete code** — chưa đủ.
6. **Decentralize để tăng tốc mà không guardrails** — tạo agent sprawl.

---

# 15. Oral Checkpoint

1. Governance khác security thế nào?
2. AI CoE nên làm gì?
3. Federated governance model hoạt động thế nào?
4. Vì sao environment separation quan trọng với agentic systems?
5. Agent registry nên lưu những metadata gì?
6. Risk-tiered governance giải quyết vấn đề gì?
7. Vì sao retirement cần governance?
8. CoE giảm duplication bằng cách nào?
9. External MCP server tạo governance concern nào?
10. Cost governance cho agent khác app thông thường ở đâu?

## PASS CONDITION

- 8/10 oral questions;
- architect được centralized/federated responsibilities;
- tạo được một 3-tier risk model cho capstone.

---

# 16. Mapping to BD Chunk / Harness

Day 18 output:

```text
BD Chunk AI Governance Model
├── Agent Registry
├── Risk Tier
├── Owner
├── Approved Tools
├── Knowledge Policy
├── Eval Requirement
├── Human Gate Requirement
└── Lifecycle Status
```

Mục tiêu: Harness không chỉ chạy agent; nó phải hỗ trợ **governed agent lifecycle**.