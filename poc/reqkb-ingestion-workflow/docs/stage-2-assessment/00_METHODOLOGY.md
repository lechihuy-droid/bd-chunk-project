# Requirement Assessment Methodology

## 1. Purpose

ReqKB records evidence and source traceability. It describes what the requirement source says, but it does not determine what that requirement means for design.

Stage 2 Assessment fills that gap.

Its purpose is to transform evidence-backed requirement facts into a controlled set of design-relevant characteristics that can be consumed by Design Governance.

```text
Requirement evidence
→ design-relevant characteristics
→ applicable Design Governance
```

Assessment does not create architecture, select technology or generate Basic Design.

## 2. Methodological position

The workflow adopts the separation found in system and software life-cycle thinking promoted by IPA around SLCP: business or mission analysis, stakeholder needs and requirements definition, system requirements definition and architecture definition are related but distinct processes with feedback between them.

This project applies that separation as follows:

```text
Stage 1 — ReqKB
Evidence preparation and semantic source trace

Stage 2 — Assessment
Requirement characterization for design consumption

Stage 3 — Design Governance
Project-specific design decisions and constraints

Stage 4 — Design Planning and BD generation
Artifact planning and controlled document production
```

The project does not claim that its Assessment Framework is an IPA standard. IPA/SLCP is used as a methodological reference for keeping requirement analysis separate from architecture and design definition.

## 3. Core question

Assessment answers:

> What characteristics of this requirement must be made explicit before Design Governance can be applied consistently?

It does not answer:

> Which API, screen, table, pattern or technology should be designed?

## 4. Assessment object

Assessment operates on a requirement evidence set, not necessarily on one isolated SourceUnit.

A requirement evidence set may contain:

- one or more related SourceUnits;
- heading and document context;
- actors, actions, objects, events, conditions and exceptions annotated in ReqKB;
- literal cross-references;
- document version and provenance.

The assessment result is a separate, versioned interpretation. ReqKB remains unchanged.

## 5. Method phases

### Phase A — Frame

Select the requirement evidence set and determine which assessment viewpoints are applicable.

### Phase B — Recognize

Identify candidate characteristics using deterministic rules, approved patterns and controlled LLM interpretation.

### Phase C — Classify

Map recognized characteristics into the stable Assessment Framework taxonomy.

### Phase D — Consolidate

Combine findings across SourceUnits and viewpoints, detect conflicts and preserve unresolved alternatives.

### Phase E — Validate

Verify evidence support, taxonomy conformity and internal consistency.

### Phase F — Review and publish

Route uncertain or conflicting findings to review, then publish an accepted Assessment Result.

## 6. Governing principles

1. **Evidence before inference.** Every characteristic must be supported by ReqKB evidence.
2. **Characteristics, not decisions.** Assessment describes design-relevant properties but does not select a design solution.
3. **Stable framework, replaceable methods.** Viewpoints and output semantics should remain stable while rules, prompts and models evolve.
4. **Explicit uncertainty.** Unknown, conflicting and insufficient-evidence states are valid outputs.
5. **Independent reviewability.** A reviewer must be able to examine Assessment without reading generated BD.
6. **Reusable output.** One accepted assessment can support BD generation, test design and impact analysis.
7. **No silent mutation.** Assessment never rewrites ReqKB facts or hides conflicting source evidence.

## 7. Relationship to Design Governance

Assessment and Design Governance are separate contracts.

```text
Assessment
Input: ReqKB evidence
Output: characteristics

Design Governance
Input: accepted characteristics + project design knowledge
Output: governed design obligations and decisions
```

Example:

```text
Assessment characteristic:
Long-running stateful business process

Design Governance may derive:
Workflow management, compensation, audit and monitoring obligations
```

The second statement belongs to Design Governance, not Assessment.

## 8. Definition of success

The methodology succeeds when:

- architects agree that the assessment exposes the information they normally establish before design;
- the same evidence and framework produce materially consistent results;
- every accepted characteristic has provenance;
- Design Governance can match rules without rereading raw RD prose;
- changing project design rules does not require reassessing unchanged requirement characteristics.
