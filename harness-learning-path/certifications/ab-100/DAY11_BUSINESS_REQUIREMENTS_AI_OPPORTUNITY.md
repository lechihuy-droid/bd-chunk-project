# DAY 11 — BUSINESS REQUIREMENTS → AI OPPORTUNITY

> Certification: AB-100 — Agentic AI Business Solutions Architect
> Official skills baseline: as of 2026-07-22
> Primary blueprint area: Plan AI-powered business solutions (25–30%)

## Goal

Chuyển từ tư duy “có agent thì làm gì?” sang “business problem nào thực sự đáng dùng AI/agent?”.

```text
Business Problem
  ↓
Process
  ↓
Decision / Repetition / Knowledge Work
  ↓
AI Opportunity
  ↓
Agent Opportunity
```

## Official objectives mapped

- Assess use of agents in task automation, data analytics, and decision-making.
- Review grounding data for accuracy, relevance, timeliness, cleanliness, and availability.
- Organize business-solution data so other AI systems can use it.

## Module 11.1 — Start from business outcome

Không bắt đầu bằng model hay platform.

Hỏi:
- KPI nào cần cải thiện?
- cycle time nào quá dài?
- decision nào cần nhiều context?
- tác vụ nào lặp lại?
- đâu là bottleneck do con người phải tổng hợp thông tin?

## Module 11.2 — Automation vs Copilot vs Agent

```text
Deterministic automation
= rule rõ, input/output ổn định

Copilot
= hỗ trợ người dùng ra quyết định / tạo nội dung

Agent
= goal-directed, có thể chọn tool, reasoning, iterate, act
```

Exam trap: không biến mọi automation thành agent.

## Module 11.3 — Data readiness

Grounding data phải được đánh giá theo:
- accuracy;
- relevance;
- timeliness;
- cleanliness;
- availability;
- ownership;
- access boundaries.

```text
Bad Grounding Data
→ Bad Agent Decision
```

## Module 11.4 — Opportunity scoring

Đánh giá use case theo:
- business value;
- feasibility;
- data readiness;
- autonomy risk;
- integration complexity;
- measurable outcome.

## Scenario drill

Một bộ phận tài chính mất 2 ngày để tổng hợp số liệu từ 4 hệ thống, sau đó chuyên gia mới quyết định ngoại lệ.

Hãy tách:
1. phần deterministic automation;
2. phần retrieval/grounding;
3. phần AI reasoning;
4. phần human decision giữ lại.

## Oral checkpoint

1. Vì sao không nên bắt đầu architecture từ model?
2. Khi nào rule-based automation tốt hơn agent?
3. Data readiness gồm những dimension nào?
4. Một use case agent tốt phải đo được outcome gì?
5. Human-in-the-loop nên giữ ở đâu trong process có rủi ro?

## PASS

Trả lời rõ 4/5 câu và phân tích được một business process mà không nhảy ngay sang tool/model.