# DAY 12 — BUILD vs BUY vs EXTEND + AI STRATEGY

> Certification: AB-100
> Primary blueprint area: Plan AI-powered business solutions (25–30%)

## Goal

Biết chọn chiến lược thay vì mặc định custom-build.

```text
Requirement
  ↓
Buy / Use Prebuilt?
  ↓ no
Extend Existing Microsoft Copilot?
  ↓ no
Build Custom Agent / Model?
```

## Official objectives mapped

- Design strategy for building AI and agents in business solutions.
- Develop use cases for prebuilt agents.
- Determine when to build custom agents or extend Microsoft 365 Copilot.
- Determine when custom AI models should be created.
- Analyze whether to build, buy, or extend AI components.
- Implement/use model routing concepts to select a suitable model.
- Define prompt-library and prompt-engineering guidance.

## Module 12.1 — Buy

Ưu tiên buy/prebuilt khi:
- capability đã commodity;
- time-to-value quan trọng;
- customization thấp;
- governance/support cần chuẩn vendor.

## Module 12.2 — Extend

Extend khi existing Copilot/Dynamics/Power Platform đã nằm đúng user workflow nhưng cần:
- custom knowledge;
- actions;
- connectors;
- business rules;
- domain prompts.

## Module 12.3 — Build

Build custom khi:
- workflow đặc thù;
- control/runtime riêng;
- custom orchestration;
- deep integration;
- unique IP/process;
- strict performance/security boundary.

## Module 12.4 — Custom model vs general model

Không fine-tune/custom-model chỉ vì prompt chưa tốt.

Decision order:
1. prompt/context;
2. RAG/grounding;
3. tool augmentation;
4. model routing;
5. customization/fine-tuning nếu có justification.

## Module 12.5 — Model Router

```text
Request
  ↓
Classifier / Router
  ├─ simple → low-cost model
  ├─ reasoning → stronger model
  └─ multimodal → multimodal model
```

Mục tiêu: quality/cost/latency balance.

## Module 12.6 — Prompt library governance

Prompt library cần:
- owner;
- version;
- approved patterns;
- test cases;
- security guidance;
- deprecated prompts;
- domain examples.

## Scenario drill

Doanh nghiệp đã dùng Microsoft 365 Copilot và muốn một agent nội bộ trả lời policy + tạo request sang hệ thống HR.

Phân tích: buy, extend, hay build? Tại sao?

## Oral checkpoint

1. Khi nào extend tốt hơn build?
2. Khi nào custom model là overkill?
3. Model router giải quyết trade-off gì?
4. Prompt library vì sao là governance asset?
5. Build/buy/extend nên dựa trên tiêu chí nào?

## PASS

Phân tích được ít nhất 2 scenario với reasoning business + architecture, không dựa trên sở thích công nghệ.