# Stage 2 — Requirement Assessment Framework

This folder defines the independent assessment stage between ReqKB and Design Governance.

```text
ReqKB
→ Requirement Assessment
→ Design Governance
→ Design Planning
→ Basic Design
```

The stage converts evidence-backed requirement facts into design-relevant characteristics. It does not make design decisions and does not generate BD artifacts.

## Reading order

1. [`00_METHODOLOGY.md`](00_METHODOLOGY.md) — purpose, boundaries and relationship to IPA/SLCP.
2. [`01_FRAMEWORK.md`](01_FRAMEWORK.md) — assessment viewpoints and semantic structure.
3. [`02_INPUTS.md`](02_INPUTS.md) — evidence, standards and knowledge required by assessment.
4. [`03_METHOD.md`](03_METHOD.md) — rule, LLM and hybrid assessment methodology.
5. [`04_OUTPUT_MODEL.md`](04_OUTPUT_MODEL.md) — assessment characteristics, provenance and review state.
6. [`05_PIPELINE.md`](05_PIPELINE.md) — end-to-end processing flow and quality gates.
7. [`06_HUMAN_REVIEW.md`](06_HUMAN_REVIEW.md) — reviewer responsibilities and feedback loop.
8. [`07_IMPLEMENTATION_GUIDE.md`](07_IMPLEMENTATION_GUIDE.md) — phased implementation plan and acceptance criteria.

## Scope boundary

Included:

- requirement characterization from ReqKB evidence;
- assessment viewpoints and standards;
- rule-based and LLM-assisted recognition;
- classification and consolidation;
- provenance, confidence and review;
- reusable assessment output for downstream consumers.

Excluded:

- requirement quality approval;
- architecture or technology selection;
- Design Governance rules;
- API, screen, database or batch design decisions;
- BD generation.