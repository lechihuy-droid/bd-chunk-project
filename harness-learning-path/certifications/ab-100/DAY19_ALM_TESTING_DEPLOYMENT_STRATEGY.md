# AB-100 Day 19 — ALM, Testing, and Deployment Strategy

> Track: Frontier / Titan Certification Sprint  
> Certificate: AB-100 — Agentic AI Business Solutions Architect  
> Focus: Deploy AI-powered business solutions  
> Study guide baseline: Skills measured as of 2026-07-22

---

# 1. Day 19 Goal

Kết thúc buổi này phải thiết kế được lifecycle từ development đến production cho agentic solution mà không coi prompt/model/knowledge là cấu hình ngoài ALM.

Mental model:

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
CHANGE / ROLLBACK
```

---

# 2. Official Objective Mapping

Map vào study guide:

- manage testing of AI-powered business solutions;
- recommend process and metrics to test agents;
- create validation criteria for custom AI models;
- validate effective Copilot prompt best practices;
- design end-to-end test scenarios across business apps;
- design ALM for data, Copilot Studio agents/connectors/actions, Foundry Agents service, custom models and Dynamics 365 AI components.

---

# 3. What Must Be Versioned?

Agentic systems có nhiều independently changing assets:

```text
Solution Version
├── Agent definition
├── Prompt / instructions
├── Model + model configuration
├── Tool / connector version
├── Knowledge/index version
├── Schema / contract
├── Workflow
├── Policy / guardrail
└── Evaluation dataset
```

Exam trap:

> Chỉ version source code vì model và prompt là runtime config.

Sai. Nếu behavior thay đổi thì change đó cần lifecycle/control tương ứng.

---

# 4. Environment Promotion

```text
DEV
 ↓ build rapidly
TEST
 ↓ functional + eval
UAT / PRE-PROD
 ↓ business validation
PROD
```

Không nên manually recreate solution ở mỗi environment nếu platform hỗ trợ managed promotion/deployment artifacts.

Architectural requirements:

- configuration separation;
- secret separation;
- connector/environment binding;
- approved data sources;
- traceable release version.

---

# 5. Testing Layers

## Layer 1 — Deterministic tests

Kiểm tra:

- schemas;
- tool contracts;
- routing rules;
- authorization policies;
- workflow conditions.

## Layer 2 — Agent behavioral evaluation

Kiểm tra:

- task completion;
- groundedness;
- relevance;
- safety;
- instruction following;
- tool selection.

## Layer 3 — Integration tests

Kiểm tra:

```text
Agent ↔ Tool
Agent ↔ Knowledge
Agent ↔ Other Agent
Agent ↔ Business App
```

## Layer 4 — End-to-End business scenario

Kiểm tra outcome từ user intent đến business result.

---

# 6. Golden Dataset / Regression Set

Một agent không có deterministic output, nhưng vẫn cần regression discipline.

```text
Representative Inputs
       ↓
Expected criteria / reference behavior
       ↓
Agent Run
       ↓
Metrics / Judge / Human review
       ↓
Pass / Fail threshold
```

Dataset nên bao gồm:

- normal cases;
- edge cases;
- risky inputs;
- prompt injection attempts;
- permission scenarios;
- known prior failures.

---

# 7. Prompt Change Is a Release Change

Prompt nhỏ có thể đổi behavior lớn.

Do đó:

```text
Prompt Change
 ↓
Version
 ↓
Evaluation
 ↓
Approval if required
 ↓
Promotion
```

Không chỉnh production prompt trực tiếp mà không trace nếu solution có governance requirement.

---

# 8. Model Change Is Not Transparent

Đổi model có thể ảnh hưởng:

- output quality;
- tool calling;
- latency;
- token cost;
- safety;
- supported modality;
- context window;
- regional availability.

Vì vậy model upgrade cần regression test, không chỉ config switch.

---

# 9. Tool / Connector ALM

Tool/action change có thể nguy hiểm hơn prompt change vì nó ảnh hưởng external side effect.

Version/validate:

- input schema;
- output contract;
- auth mode;
- permission scope;
- error behavior;
- idempotency;
- backward compatibility.

Exam scenario:

> Agent được update tool schema nhưng production prompt/tool description chưa đồng bộ.

Risk: bad invocation / runtime failure. ALM phải promote compatible versions together.

---

# 10. Knowledge ALM

Knowledge cũng có lifecycle:

```text
Source version
 ↓
Ingestion
 ↓
Index build
 ↓
Validation
 ↓
Publish / Swap
```

Cần kiểm tra:

- freshness;
- completeness;
- access control;
- index health;
- source provenance.

Không deploy agent mới mà quên dependency vào knowledge version.

---

# 11. Deployment Strategies

Concepts cần biết:

## Staged deployment

Rollout từng environment/nhóm user.

## Pilot / limited audience

Giảm blast radius.

## Feature flags / controlled enablement

Tách deployment khỏi enablement.

## Rollback

Phải có khả năng quay về known-good configuration/version.

Agentic solution cần rollback cả:

- agent/prompt;
- model config;
- tool integration;
- workflow;
- possibly knowledge index.

---

# 12. Approval Gates

Không phải mọi change đều human approval.

Risk-based:

```text
Low-risk prompt formatting
→ automated eval may suffice

High-risk tool permission change
→ security + business approval
```

Deployment gate nên dựa vào measurable criteria, không chỉ subjective confidence.

---

# 13. Test Metrics

Technical:

- pass/fail rate;
- tool-call success;
- latency;
- token usage;
- error rate.

AI quality:

- groundedness;
- relevance;
- safety;
- task completion;
- hallucination/fabrication rate.

Business:

- process success;
- human rework;
- escalation rate;
- cycle-time change.

---

# 14. Scenario Drills

## Scenario A

Prompt update improves average answer quality but increases unsafe outputs on rare legal queries.

Không promote chỉ vì average score tăng. Release gate phải cover risk-critical metrics.

## Scenario B

New model rẻ hơn 40%.

Không switch production ngay. Re-run regression/evals + latency/tool compatibility + policy validation.

## Scenario C

New connector action changes required field names.

Version compatibility + coordinated deployment needed.

## Scenario D

Knowledge source was updated but index refresh failed.

Monitoring/deployment process cần detect stale index before user impact.

---

# 15. Exam Traps

1. **Code deploy = full solution deploy** — sai với AI assets.
2. **Model upgrade luôn backward compatible** — sai.
3. **Prompt change không cần versioning** — sai.
4. **Only happy-path tests** — không đủ.
5. **Evaluation chỉ trước go-live** — phải continuous/regression.
6. **Rollback chỉ source code** — agentic dependencies rộng hơn.

---

# 16. Oral Checkpoint

1. Những artifact nào phải version trong agentic ALM?
2. Deterministic test khác behavioral evaluation thế nào?
3. Tại sao model change cần regression?
4. Tool schema change tạo risk gì?
5. Knowledge ALM gồm những bước nào?
6. Golden dataset dùng để làm gì?
7. Feature flag khác deployment thế nào?
8. Khi nào cần human approval gate?
9. Rollback agentic solution cần rollback những gì?
10. Vì sao business metrics phải nằm trong testing strategy?

## PASS CONDITION

- 8/10 oral questions;
- thiết kế được DEV→TEST→PROD flow;
- nêu được version/dependency matrix cho agent, prompt, model, tool, knowledge.

---

# 17. Mapping to BD Chunk / Harness

```text
RunManifest
├── workflow_version
├── agent_version
├── prompt_version
├── model_config_version
├── tool_version
├── schema_version
├── knowledge_version
└── eval_dataset_version
```

Day 19 output: **Agentic ALM + Release Gate Design**.