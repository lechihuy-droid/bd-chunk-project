# DAY 13 — MICROSOFT AGENT PLATFORM SELECTION

> Certification: AB-100
> Primary blueprint areas: Plan + Design AI-powered business solutions

## Goal

Biết chọn đúng Microsoft platform theo business context thay vì chỉ biết tên sản phẩm.

## Core landscape

```text
Microsoft 365 Copilot
Copilot Studio
Microsoft Foundry
Power Platform
Dynamics 365
Foundry Models / Tools
```

## Module 13.1 — Microsoft 365 Copilot

Phù hợp khi:
- user workflow nằm trong Microsoft 365;
- cần productivity assistance;
- muốn extend trải nghiệm Copilot sẵn có;
- cần leverage Microsoft Graph/work context.

## Module 13.2 — Copilot Studio

Phù hợp khi:
- business users/low-code team tham gia build;
- cần agent tied to business process;
- cần connectors/actions;
- cần governance qua Power Platform environments;
- cần nhanh chóng compose knowledge + action.

## Module 13.3 — Microsoft Foundry

Phù hợp khi:
- custom AI application;
- developer-centric solution;
- model flexibility;
- custom agents/orchestration;
- advanced evaluation/monitoring;
- custom tools/knowledge/runtime integration.

## Module 13.4 — Power Platform

Dùng cho:
- workflow automation;
- connectors;
- Dataverse;
- human approvals;
- business app integration;
- low-code lifecycle.

## Module 13.5 — Dynamics 365

AB-100 kỳ vọng hiểu AI solution có thể trải dài nhiều Dynamics 365 applications và business processes.

Không cần nhớ mọi feature, nhưng phải biết:
- system of record ở đâu;
- process owner là ai;
- data nào là grounding source;
- action nào phải quay lại Dynamics app.

## Selection matrix

| Need | Likely direction |
|---|---|
| M365 productivity extension | Microsoft 365 Copilot |
| Low-code business agent | Copilot Studio |
| Custom developer AI/agent app | Microsoft Foundry |
| Workflow/connectors/approvals | Power Platform |
| CRM/ERP process integration | Dynamics 365 |

Không coi bảng này là luật cứng; enterprise solution thường kết hợp nhiều nền tảng.

## Exam traps

- Chọn Foundry cho mọi agent vì “mạnh hơn”.
- Chọn Copilot Studio cho deep custom runtime chỉ vì low-code dễ dùng.
- Bỏ qua Power Platform khi human approval/workflow là requirement chính.
- Bỏ qua existing Microsoft 365/Dynamics context rồi build app mới hoàn toàn.

## Scenario drill

Một sales organization dùng Dynamics 365 Sales + Teams. Họ muốn agent tóm tắt account context, đề xuất next action, và khi salesperson approve thì cập nhật CRM.

Thiết kế platform composition hợp lý.

## Oral checkpoint

1. Copilot Studio khác Foundry ở architectural fit nào?
2. Khi nào extend Microsoft 365 Copilot tốt hơn custom app?
3. Power Platform đóng vai trò gì trong agentic solution?
4. Dynamics 365 thường là UI, system of record, hay cả hai?
5. Vì sao enterprise solution thường không chỉ dùng một platform?

## PASS

Chọn được platform composition cho 3 scenario và giải thích trade-off theo user workflow, governance, integration, customization.