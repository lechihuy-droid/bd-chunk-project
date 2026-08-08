# Stage 2 — Requirement Assessment

Stage 2 defines the controlled assessment boundary between evidence-backed requirements and downstream design governance.

## Position in the overall flow

```text
Stage 1 — ReqKB
Evidence + source trace + lightweight requirement ontology

        ↓

Stage 2 — Requirement Assessment
Design-relevant characteristics

        ↓

Stage 3 — Design Governance + Design Planning
Design obligations + artifact plan

        ↓

Stage 4 — Basic Design Generation
Artifact generation + evidence traceability
```

## Why Stage 2 exists

ReqKB preserves what the source says. It is the evidence source of truth.

Design Governance needs more than raw evidence: it needs a stable, reviewable characterization of the requirement under design-relevant viewpoints.

Stage 2 exists to create that characterization without making design decisions.

```text
ReqKB evidence
→ Requirement Assessment
→ Design-relevant characteristics
```

Assessment results are derived knowledge. They never replace or rewrite ReqKB evidence.

## Architecture boundary

Stage 2 is an independently versioned processing capability with its own input contract, output contract, methodology, quality policy and review lifecycle.

It is not defined as an AI agent or prompt.

An implementation may use deterministic rules, LLM-assisted interpretation, workflow orchestration and human review, but these are execution mechanisms under the Assessment methodology rather than the methodology itself.

## Stage contracts

### Stage 1 → Stage 2

**Contract: Requirement Evidence Set**

A bounded set of accepted ReqKB evidence required to assess one logical requirement or requirement scope.

The evidence set may include multiple SourceUnits when meaning is distributed across a requirement, condition, exception, business rule or referenced context.

### Stage 2 → Stage 3

**Contract: Assessment Result / Characteristic Set**

A versioned set of design-relevant characteristics supported by ReqKB evidence and evaluated under a known Assessment Standard.

Stage 3 consumes accepted characteristics. It must not treat Assessment results as source evidence.

### Stage 3 → Stage 4

**Contract: Design Obligations + Artifact Plan**

Stage 3 converts accepted characteristics and project Design Governance into design obligations and an artifact plan. Stage 4 uses that plan to generate BD artifacts and retrieves ReqKB evidence for authoritative source traceability.

## Core principles

1. **ReqKB remains the evidence source of truth.** Assessment is derived interpretation.
2. **Assessment characterizes; it does not design.** Technology, architecture, API, screen, database and batch decisions belong downstream.
3. **Evidence before inference.** Every accepted characteristic must be traceable to a Requirement Evidence Set.
4. **The processing capability is independent from the execution mechanism.** Rules, LLMs, agents and human review may evolve without changing the Stage 2 responsibility.
5. **No unsupported result is preferable to a guessed result.** Unknown, conflicting and not-ready states are valid outcomes.
6. **Assessment must be reviewable and reproducible.** Every result must identify the evidence version, Assessment Standard version and execution configuration that produced it.
7. **Downstream consumers must not bypass Design Governance.** Assessment characteristics are inputs to Stage 3, not direct design instructions for BD generation.

## Assessment subject

The default unit of assessment is a **Requirement Evidence Set**, not an individual SourceUnit.

This avoids assuming that one parsed chunk contains the complete meaning required for design characterization.

Assessment may aggregate multiple SourceUnits while preserving provenance to every contributing source.

## Outcome states

Stage 2 must be able to complete without forcing a characteristic decision.

At minimum, the methodology must distinguish these logical outcomes:

```text
ASSESSED
UNKNOWN
CONFLICTING
REVIEW_REQUIRED
INPUT_NOT_READY
```

The detailed semantics and transition rules are defined in the Assessment Standard, Pipeline and Quality documents.

## Reproducibility principle

An Assessment Result is meaningful only in the context of the versions that produced it.

Conceptually, a result is derived from:

```text
Requirement Evidence Set version
+ Assessment Framework / Standard version
+ Assessment Knowledge version
+ execution configuration
→ Assessment Result
```

Changing evidence, framework, knowledge or execution configuration may require reassessment. The implementation approach will define the exact invalidation policy.

## Feedback boundary

Stage 2 may discover that its input cannot be assessed reliably, for example because source context is incomplete, references are unresolved or evidence conflicts.

In those cases Stage 2 does not repair ReqKB silently.

```text
Assessment
├── accepted result → Stage 3
└── source/evidence issue → ReqKB review or human resolution
```

## Downstream consumers

The primary consumer of accepted Assessment Results is Stage 3 — Design Governance + Design Planning.

Other future consumers may reuse accepted characteristics for analysis such as testing or impact assessment, but BD generation must not bypass Stage 3 and convert Assessment characteristics directly into design decisions.

## Document set

1. [`00_ASSESSMENT_METHODOLOGY.md`](00_ASSESSMENT_METHODOLOGY.md) — why Assessment exists and its methodological boundary.
2. [`01_ASSESSMENT_FRAMEWORK.md`](01_ASSESSMENT_FRAMEWORK.md) — viewpoints and characteristic structure.
3. [`02_ASSESSMENT_INPUT.md`](02_ASSESSMENT_INPUT.md) — Requirement Evidence Set, standard and assessment knowledge inputs.
4. [`03_ASSESSMENT_STANDARD.md`](03_ASSESSMENT_STANDARD.md) — validity, classification and evidence requirements.
5. [`04_ASSESSMENT_METHOD.md`](04_ASSESSMENT_METHOD.md) — rule-based, LLM-assisted and hybrid execution methods.
6. [`05_ASSESSMENT_OUTPUT.md`](05_ASSESSMENT_OUTPUT.md) — Assessment Result and Characteristic Set contract.
7. [`06_ASSESSMENT_PIPELINE.md`](06_ASSESSMENT_PIPELINE.md) — end-to-end processing and lifecycle.
8. [`07_QUALITY_AND_HUMAN_REVIEW.md`](07_QUALITY_AND_HUMAN_REVIEW.md) — quality gates, uncertainty and human review.
9. [`08_IMPLEMENTATION_APPROACH.md`](08_IMPLEMENTATION_APPROACH.md) — phased implementation and automation strategy.

## Current documentation status

This branch establishes and iteratively refines the Stage 2 methodology. Each document is developed and reviewed separately before the methodology is considered implementation-ready.
