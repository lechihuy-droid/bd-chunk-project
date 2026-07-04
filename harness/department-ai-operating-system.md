# Department AI Operating System

## 1. Context

This document reframes the platform from a narrow BD Harness into a broader department-level AI operating system for an FPT Japan department of approximately 80-100 people.

The objective is to optimize the core management domains of the department, not only delivery artifact generation.

Working thesis:

```text
A department-level AI platform should help the manager run the business, grow the business, build capability, and govern performance.
```

---

## 2. North Star

```text
Department AI Operating System
=
Delivery Excellence
+ People / Resource / Capability Management
+ Operation / Quality / Governance
+ Financial & Commercial Performance
+ Presales / Client Growth / Offering
+ Strategy / Portfolio / Transformation
+
Knowledge / Data Foundation
+ AI Workflow / Agent / Skill Platform
+ Governance / Security / Adoption
```

Positioning statement:

```text
Build a department-level AI operating system that improves delivery productivity, resource utilization, operational control, financial performance, presales capability, and strategic decision-making for an 80-100 person software delivery unit.
```

---

## 3. Six business pillars

## Pillar 1 — Delivery Excellence

Purpose:

```text
Improve delivery productivity, artifact quality, traceability, review readiness, and reduce senior dependency.
```

Scope:

```text
- Requirement / RD
- RCD
- Basic Design
- Detail Design
- Development
- Test
- Review
- Defect / rework
- Delivery quality
```

Example AI use cases:

```text
- RD -> RCD
- RCD -> BD Mapping
- BD Draft Generation
- Review Comment Analyzer
- Test Case Generator
- Defect Pattern Analyzer
- Code Review Assistant
```

Representative KPI:

```text
- Delivery effort
- Cycle time
- Review comments
- Rework
- Defect leakage
- Traceability coverage
- Senior review effort
```

---

## Pillar 2 — People, Resource & Capability Management

Purpose:

```text
Optimize staffing, skill visibility, allocation, training, recruitment demand, onboarding, and backup planning.
```

Scope:

```text
- Resource allocation
- Skill matrix
- Capacity planning
- Training roadmap
- Recruitment demand
- Onboarding
- Backup planning
- Succession planning
```

Example AI use cases:

```text
- Skill Matrix Builder
- Project-to-Resource Matching
- Capacity Forecasting
- Senior Bottleneck Detection
- Skill Gap Analyzer
- Training Recommendation
- Recruitment JD Generator
- Interview Question Generator
- Onboarding Copilot
```

Representative KPI:

```text
- Utilization
- Bench rate
- Staffing lead time
- Skill coverage
- Senior overload index
- Training completion
- Recruitment lead time
- Onboarding time
```

Management note:

```text
Recruitment and HR topics should not be a standalone pillar at department level. They should be handled as part of People, Resource & Capability Management because the department manager's real need is delivery capability planning.
```

---

## Pillar 3 — Operation, Quality & Governance

Purpose:

```text
Improve visibility, control, risk detection, reporting, quality governance, and management cadence across projects.
```

Scope:

```text
- Project health
- Risk / issue
- Quality control
- PMO reporting
- Escalation
- Compliance
- Audit
- Standard process
- Management meetings
```

Example AI use cases:

```text
- Weekly Operation Summary
- Project Health Dashboard
- Risk / Issue Early Warning
- Meeting Note to Action Tracker
- KPI Dashboard
- Quality Trend Analyzer
- Escalation Recommendation
- Audit Evidence Pack
```

Representative KPI:

```text
- Risk detection lead time
- Issue aging
- Schedule variance
- Quality trend
- Report preparation effort
- Escalation response time
- Governance compliance
```

Management note:

```text
Delivery creates project artifacts. Operation controls the delivery system.
```

---

## Pillar 4 — Financial & Commercial Performance

Purpose:

```text
Connect AI transformation to money: revenue, cost, margin, utilization, profitability, forecast, and pricing support.
```

Scope:

```text
- Revenue
- Cost
- Gross margin
- Utilization
- Project profitability
- Budget
- Forecast
- Cost leakage
- Estimate accuracy
```

Example AI use cases:

```text
- Project Margin Analyzer
- Cost Overrun Early Warning
- Estimate vs Actual Analyzer
- Monthly Financial Summary
- Utilization-to-Margin Dashboard
- Revenue / Capacity Forecast
- Pricing Support Assistant
- Commercial Risk Analyzer
```

Representative KPI:

```text
- Gross margin
- Revenue per head
- Cost variance
- Budget variance
- Estimate accuracy
- Utilization-to-margin ratio
- Project profitability
```

Management note:

```text
Finance should be a standalone pillar because it translates AI productivity into leadership language: margin, cost, revenue, and profitability.
```

---

## Pillar 5 — Presales, Client Growth & Offering

Purpose:

```text
Turn internal delivery capability into revenue support, client growth, reusable proposal assets, and AI-enabled differentiation.
```

Scope:

```text
- Proposal
- Estimation
- RFP response
- Client pain analysis
- Account strategy
- Delivery case study
- Solution offering
- AI-enabled delivery pitch
```

Example AI use cases:

```text
- Proposal Copilot
- RFP Analyzer
- Estimation Assistant
- Client Pain Point Analyzer
- Account Strategy Assistant
- Case Study Generator
- AI Delivery Offering Builder
- Presales Knowledge Base
```

Representative KPI:

```text
- Proposal preparation time
- Estimation accuracy
- Win-rate support
- Reuse rate of proposal assets
- Number of packaged offerings
- Account expansion opportunities
```

Management note:

```text
If the BD Harness proves value internally, it can become an AI-enabled delivery methodology for presales and client differentiation.
```

---

## Pillar 6 — Strategy, Portfolio & Transformation

Purpose:

```text
Support department-level strategy, capability roadmap, investment prioritization, use case portfolio, and transformation progress.
```

Scope:

```text
- Department strategy
- Capability roadmap
- AI transformation roadmap
- Investment prioritization
- Use case portfolio
- Service offering strategy
- Market / client trend analysis
- Quarterly business review
```

Example AI use cases:

```text
- Department Strategy Assistant
- Use Case Portfolio Prioritizer
- Capability Roadmap Builder
- QBR Pack Generator
- Investment Prioritization Assistant
- Market / Client Trend Synthesizer
- Transformation Progress Tracker
```

Representative KPI:

```text
- Strategic initiative progress
- Capability maturity
- Use case ROI
- Reusable asset count
- Offering pipeline
- Transformation adoption
```

---

## 4. Three cross-cutting foundations

## Foundation A — Knowledge & Data Layer

Purpose:

```text
Create the data and knowledge substrate that feeds all six business pillars.
```

Examples:

```text
- Project documents
- Delivery artifacts
- Resource data
- Skill data
- Financial data
- Operation reports
- Proposal assets
- Lessons learned
```

---

## Foundation B — AI Workflow / Agent / Skill Platform

Purpose:

```text
Provide reusable workflow, skill, and agent capabilities across all business pillars.
```

Examples:

```text
- Workflow templates
- Skill Library
- Agent Runtime
- Human Gate
- Validation Engine
- Traceability Graph
- Export tools
```

---

## Foundation C — Governance, Security & Adoption

Purpose:

```text
Make the AI operating system safe, trusted, auditable, and adoptable by the department.
```

Examples:

```text
- Access control
- Data boundary
- Audit log
- Human approval
- AI usage policy
- Change management
- Training
```

---

## 5. One-page model

```text
                    Department Leadership
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
  Run the Business    Grow the Business   Build the Capability
        │                   │                   │
 ┌──────┴──────┐      ┌─────┴─────┐       ┌─────┴─────┐
 │ Delivery    │      │ Presales  │       │ People    │
 │ Operation   │      │ Offering  │       │ Capability│
 │ Finance     │      │ Client    │       │ Strategy  │
 └─────────────┘      └───────────┘       └───────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
 Knowledge/Data      AI Workflow Platform    Governance/Adoption
```

---

## 6. Recommended sequencing

The department should not build all pillars at once.

Recommended wave plan:

```text
Wave 1 — Delivery Productivity
Start with AI-assisted Basic Design Harness because the pain is clear, output is structured, and value can be measured.

Wave 2 — Operation Visibility
Add weekly operation summary, project health dashboard, and risk/issue early warning.

Wave 3 — People / Resource Optimization
Add skill matrix, capacity forecast, staffing recommendation, and training gap analysis.

Wave 4 — Financial / Commercial Performance
Connect delivery and resource data to margin, cost, estimate accuracy, and profitability.

Wave 5 — Presales / Offering
Turn internal AI delivery capability into proposal assets, RFP support, case studies, and client-facing differentiation.

Wave 6 — Strategy / Transformation
Use the accumulated evidence and data to drive department strategy, portfolio prioritization, and capability roadmap.
```

---

## 7. Management guidance

For a middle manager, the right pitch is not:

```text
I want to build a big AI platform.
```

The better pitch is:

```text
I want to run a department-level AI transformation roadmap. We start with one measurable delivery use case, then expand into operation visibility, resource optimization, financial performance, presales enablement, and strategy execution.
```

---

## 8. Initial priority recommendation

Recommended first priority:

```text
Pillar 1 — Delivery Excellence
Use case: AI-assisted Basic Design Harness
```

Reason:

```text
- Pain is visible.
- Output is structured.
- KPI can be measured.
- Human review model is clear.
- It creates reusable AI workflow and skill assets.
- It can later feed operation, resource, finance, presales, and strategy pillars.
```

---

## 9. Final principle

```text
Start with one narrow, measurable delivery use case.
Design the architecture as a department AI operating system.
Scale only when value, trust, data, and governance are proven.
```