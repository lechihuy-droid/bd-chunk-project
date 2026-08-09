# AB-100 Day 20 — Monitoring, Telemetry, Tuning, and ROI

> Track: Frontier / Titan Certification Sprint  
> Certificate: AB-100 — Agentic AI Business Solutions Architect  
> Focus: Deploy AI-powered business solutions  
> Study guide baseline: Skills measured as of 2026-07-22

---

# 1. Day 20 Goal

Kết thúc buổi này phải nối được **technical telemetry** với **business outcome**.

Mental model:

```text
Production Usage
      ↓
Telemetry
      ↓
Quality / Reliability Analysis
      ↓
Tuning / Product Improvement
      ↓
Business Outcome
      ↓
ROI Decision
```

AB-100 Solution Architect không chỉ hỏi "agent có chạy không?" mà phải trả lời:

> Agent có tạo giá trị, có đáng duy trì, và improvement nào đáng đầu tư tiếp?

---

# 2. Official Objective Mapping

Map vào study guide:

- recommend process/tools for monitoring agents;
- analyze backlog and user feedback;
- apply AI-based tools to identify issues and perform tuning;
- monitor agent performance and metrics;
- interpret telemetry data for performance/model tuning;
- select ROI criteria including total cost of ownership;
- create ROI analysis for AI-powered business processes.

---

# 3. Four Layers of Monitoring

```text
Layer 1 — Infrastructure
availability / failures / latency

Layer 2 — AI Behavior
quality / safety / groundedness

Layer 3 — Agent Execution
tool use / routing / retries / handoffs

Layer 4 — Business Outcome
adoption / productivity / process success / ROI
```

Một dashboard chỉ có CPU, request count và error rate không đủ cho agentic solution.

---

# 4. Technical Telemetry

Theo dõi ít nhất:

- request volume;
- latency;
- timeout/error rate;
- model/token usage;
- tool-call success;
- retrieval/search health;
- workflow retries;
- agent handoff failures.

Mental model:

```text
Workflow Trace
├── Agent step
├── Model call
├── Retrieval call
├── Tool/action
├── Policy gate
└── Final artifact
```

---

# 5. AI Quality Telemetry

Metrics có thể gồm:

- task completion;
- groundedness;
- relevance;
- safety;
- hallucination/fabrication;
- instruction following;
- answer completeness;
- tool-selection accuracy.

Không có một metric duy nhất đại diện cho "AI quality".

---

# 6. Agent-Specific Metrics

Multi-agent systems cần thêm:

```text
handoff success
routing accuracy
coordination failure
retry loops
agent-to-agent latency
human intervention rate
workflow completion rate
```

Một specialist agent có accuracy cao nhưng handoff contract thường xuyên fail vẫn làm end-to-end solution kém.

---

# 7. Human Feedback and Backlog

Production tuning loop:

```text
Usage
 ↓
Telemetry + User Feedback
 ↓
Failure Categorization
 ↓
Backlog
 ↓
Fix / Tune
 ↓
Regression Eval
 ↓
Release
```

User feedback không thay thế telemetry và eval.
Telemetry cũng không thay thế qualitative feedback.

---

# 8. Root-Cause Mental Model

Khi output sai, không mặc định "model yếu".

Investigate:

```text
Bad Result
├── Bad source data?
├── Retrieval failure?
├── Prompt/instruction issue?
├── Wrong tool selected?
├── Tool result bad?
├── Model limitation?
├── Workflow routing error?
├── Permission/context issue?
└── Evaluation expectation wrong?
```

Solution Architect phải tránh expensive fix cho wrong root cause.

---

# 9. Tuning Options

Tuning không đồng nghĩa fine-tuning model.

Possible interventions:

- improve prompt/instructions;
- improve grounding data;
- change retrieval strategy;
- change tool descriptions/contracts;
- alter workflow/routing;
- change model/model router;
- add policy/human gate;
- fine-tune/customize model only when justified.

Exam trap:

> Quality thấp → custom model/fine-tune ngay.

Thường phải diagnose simpler layers trước.

---

# 10. Model Router and Cost/Quality Optimization

Model routing mental model:

```text
Request
 ↓ classify complexity / modality / risk
Model Router
 ├── small/cheap model
 ├── general model
 └── advanced model
```

Goal:

```text
required quality
at acceptable latency
at acceptable cost
```

Không phải luôn route sang model mạnh nhất.

---

# 11. Total Cost of Ownership

TCO có thể gồm:

```text
Model/API consumption
+ Search / retrieval
+ Storage / indexing
+ Tool/API usage
+ Engineering / ALM
+ Monitoring
+ Security / governance
+ Human review
+ Support / operations
+ Training / adoption
```

ROI analysis chỉ dùng token cost là quá hẹp.

---

# 12. Business Value Metrics

Tùy use case:

- cycle-time reduction;
- cost per case;
- resolution time;
- employee hours saved;
- conversion/revenue impact;
- error/rework reduction;
- customer satisfaction;
- adoption/utilization;
- compliance/risk reduction.

Architect phải chọn metric gắn với original business problem.

---

# 13. ROI Mental Model

```text
Business Benefit
- Total Cost of Ownership
= Net Value
```

Nhưng cần tính cả baseline.

Ví dụ:

```text
Before AI:
20 min / case

After AI:
8 min / case

Benefit:
12 min saved × case volume × labor value
```

Sau đó trừ:

- platform cost;
- human review cost;
- implementation/operation cost.

---

# 14. Adoption vs Value

High adoption không tự động = high ROI.

Ví dụ:

```text
90% employees use agent
but
outputs require 2x rework
```

Adoption metric phải đi cùng business outcome và quality.

Ngược lại low adoption có thể là UX/change-management issue dù technical quality tốt.

---

# 15. Scenario Drills

## Scenario A

Latency tăng gấp đôi nhưng model quality không đổi.

Investigate:
- model latency;
- retrieval;
- tool latency;
- orchestration loops;
- new logging/network dependency.

Không mặc định scale model deployment trước.

## Scenario B

Groundedness giảm sau knowledge refresh.

Investigate source/index/retrieval pipeline trước prompt/model.

## Scenario C

Agent giảm 40% handling time nhưng human approval workload tăng mạnh.

ROI phải tính human review cost và process bottleneck.

## Scenario D

Small model xử lý 80% requests đủ tốt; 20% complex requests cần strong model.

Model routing có thể tối ưu TCO mà giữ required quality.

---

# 16. Exam Traps

1. **Infrastructure monitoring = agent monitoring** — không đủ.
2. **Fine-tuning là default response cho quality issue** — sai.
3. **Token cost = TCO** — quá hẹp.
4. **Adoption = ROI** — sai.
5. **Average score tốt là đủ** — risk-critical segments có thể fail.
6. **Model latency là nguyên nhân duy nhất của end-to-end latency** — sai.
7. **User feedback thay được systematic evaluation** — sai.

---

# 17. Oral Checkpoint

1. Bốn layer monitoring là gì?
2. Multi-agent cần metric nào ngoài model quality?
3. Tại sao bad result không đồng nghĩa bad model?
4. Tuning có những lựa chọn nào trước fine-tuning?
5. Model router tạo giá trị thế nào?
6. TCO gồm những nhóm chi phí nào?
7. Adoption khác business value thế nào?
8. ROI phải so với baseline như thế nào?
9. Khi groundedness giảm sau index refresh, investigate gì trước?
10. Human review ảnh hưởng ROI như thế nào?

## PASS CONDITION

- 8/10 oral questions;
- giải được root cause cho 4/5 incident scenarios;
- build được một ROI model có cả benefit + TCO.

---

# 18. Mapping to BD Chunk / Harness

```text
Harness Telemetry
├── workflow_completion
├── parse_accuracy
├── validation_findings
├── tool_success
├── retrieval_quality
├── human_review_rate
├── cycle_time
├── token/model cost
└── artifact rework rate
```

Business layer:

```text
RD→BD cycle time
manual effort saved
review effort
rework reduction
defect leakage
cost per generated BD
```

Day 20 output: **Telemetry + ROI Scorecard**.