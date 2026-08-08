# Assessment Methodology

## 1. Purpose

Requirement Assessment exists to create a controlled semantic bridge between evidence-backed requirements and downstream design governance.

Stage 1 ReqKB preserves what the source says. Stage 3 Design Governance + Design Planning decides what the project must design. Stage 2 sits deliberately between them and answers a narrower question:

> What design-relevant characteristics can be established from the requirement evidence before any design solution is selected?

Assessment therefore converts requirement evidence into explicit, reviewable characteristics. It does not create APIs, screens, tables, components, architecture patterns, technologies or Basic Design content.

```text
Stage 1 — ReqKB
Requirement Evidence Set
        ↓
Stage 2 — Requirement Assessment
Assessment Result / Characteristic Set
        ↓
Stage 3 — Design Governance + Design Planning
Design Obligations + Artifact Plan
        ↓
Stage 4 — Basic Design Generation
```

## 2. Problem statement

A ReqKB prepared from source documents is still an evidence layer. Even when SourceUnits have metadata, validation results and lightweight ontology annotations, the evidence does not yet expose all characteristics needed by a design process.

For example, ReqKB may establish that a manager approves a purchase request under a stated condition. A designer may recognize that the behavior is approval-oriented, stateful and multi-actor. Those characteristics matter because downstream governance may apply different rules to different kinds of behavior.

If the system skips Assessment and sends ReqKB directly to a generative model, one component is forced to perform several responsibilities at once:

```text
Understand evidence
+ characterize requirement
+ recall design standards
+ choose design decisions
+ plan artifacts
+ write BD
```

That coupling makes results difficult to reproduce, review, govern and improve independently.

Assessment separates the characterization responsibility from the design responsibility.

## 3. Methodological position

This project uses IPA guidance around System and Software Life Cycle Processes (SLCP) and Common Frame as methodological references for process separation and common terminology. IPA describes SLCP as a lifecycle framework covering system and software activities without prescribing one development methodology. Common Frame 2013 also incorporates requirement-definition concepts from ISO/IEC/IEEE 29148.

The project adopts the following principle from that lifecycle thinking:

> Requirement analysis and design or architecture definition are related, but they should remain distinguishable responsibilities with explicit outputs and feedback between them.

The Stage 2 Assessment Framework defined by this project is not an IPA standard and must not be represented as one. IPA/SLCP provides a reference for separation of concerns; the assessment viewpoints, taxonomy, rules and automation methods are project-specific assets.

Other requirement-engineering, systems-engineering or architecture references may inform the Assessment Framework later, but each adopted concept must be documented explicitly rather than silently treated as part of IPA.

## 4. Relationship to the human architect workflow

A human Solution Architect rarely moves directly from raw requirement text to a final design. Before choosing a solution, the architect normally establishes an internal understanding of the requirement: what behavior is involved, who interacts, whether state changes, what information is affected, which boundaries are crossed, and which quality concerns are explicit.

This reasoning is usually implicit and varies between people.

Stage 2 makes that intermediate understanding explicit and reviewable:

```text
Human workflow
Read evidence
→ recognize characteristics
→ apply design knowledge
→ plan solution
→ document design

Project workflow
ReqKB
→ Assessment
→ Design Governance + Planning
→ BD Generation
```

The goal is not to replace architectural judgment with classification. The goal is to externalize the repeatable part of pre-design interpretation so that later design decisions have a stable input.

## 5. Assessment subject

Assessment operates on a `Requirement Evidence Set`, not automatically on one SourceUnit.

A Requirement Evidence Set is the smallest governed collection of ReqKB evidence that provides sufficient context to characterize one requirement concern. It may contain:

- one SourceUnit;
- a requirement statement plus its condition or exception;
- a requirement plus an explicitly referenced business rule;
- several SourceUnits whose meaning is structurally dependent;
- related evidence needed to resolve a pronoun, term or cross-reference.

The evidence set remains fully traceable to ReqKB. Assessment does not copy the evidence into a new source of truth.

## 6. Assessment responsibility

Assessment may:

- identify design-relevant characteristics supported by evidence;
- classify those characteristics using the approved Assessment Framework;
- combine findings from multiple evidence items;
- expose ambiguity, conflict or insufficient information;
- record provenance, method and version information;
- request human review when automation cannot produce a supported result.

Assessment must not:

- select a technology or architecture pattern;
- decide that a Screen, API, Batch, Database table or other design artifact must exist;
- apply project Design Governance rules;
- turn a characteristic into a design obligation;
- rewrite or correct ReqKB evidence;
- infer missing facts merely because they would make a design convenient;
- generate Basic Design prose.

A simple boundary test is:

```text
"This is a stateful approval interaction"
→ Assessment characteristic

"Use a workflow engine and store approval history"
→ Design Governance / Design Planning
```

## 7. Method phases

Assessment is defined as a capability with several logical phases. The phases do not imply a specific tool, agent framework or implementation technology.

### 7.1 Frame

Resolve the Assessment Subject and construct the bounded Requirement Evidence Set.

The purpose is to ensure that subsequent interpretation receives sufficient but controlled context.

### 7.2 Examine

Evaluate the evidence through the applicable Assessment Framework viewpoints.

This establishes which concerns need characterization without yet deciding their values.

### 7.3 Recognize

Identify candidate characteristics using approved methods such as deterministic rules, terminology knowledge, pattern recognition, LLM-assisted interpretation or human judgment.

### 7.4 Classify

Map recognized candidates into the controlled Assessment Standard and characteristic taxonomy.

Recognition and classification are intentionally distinct: language recognition methods may evolve while the downstream semantic contract remains stable.

### 7.5 Consolidate

Combine findings across the evidence set, preserve supporting evidence, merge equivalent findings and expose incompatible findings instead of silently choosing one.

### 7.6 Validate

Check that every characteristic is allowed by the current standard, supported by evidence and internally consistent with the rest of the Assessment Result.

### 7.7 Review and publish

Route unresolved cases according to review policy. Only accepted results are published for automatic consumption by Stage 3.

## 8. Governing principles

### 8.1 Evidence before inference

Every accepted characteristic must be traceable to the Requirement Evidence Set. Model plausibility is not evidence.

### 8.2 Characteristics, not design decisions

Assessment describes properties relevant to design. It never selects the design response.

### 8.3 ReqKB remains authoritative

ReqKB is the evidence source of truth. Assessment is derived knowledge and can be invalidated or regenerated without changing ReqKB.

### 8.4 Stable semantics, replaceable execution

Assessment Framework, Standard and output meaning should change conservatively. Rules, prompts, models and orchestration may evolve independently.

### 8.5 Explicit uncertainty

Unknown, conflicting and insufficient-evidence outcomes are legitimate results. No supported characteristic is preferable to an unsupported confident answer.

### 8.6 Reproducibility and provenance

Every published Assessment Result must identify the evidence baseline and the versions of the standard, knowledge and execution configuration that produced it.

The objective is not bit-for-bit deterministic LLM output. The objective is operational reproducibility: a reviewer must be able to explain which inputs and governed versions led to the result.

### 8.7 Independent reviewability

A reviewer must be able to assess the validity of a characteristic without reading generated BD or accepting downstream design decisions.

### 8.8 Reusability

Assessment output should describe requirement characteristics independently of one specific artifact type. The same accepted result may support Design Governance, impact analysis, test design or other approved consumers.

### 8.9 No silent mutation

Neither automated methods nor human review may silently rewrite source evidence or erase conflicting evidence. Corrections are represented as new derived results or Stage 1 feedback.

## 9. Outcome semantics

Assessment does not guarantee that every input becomes a Characteristic Set.

At the stage level, valid outcomes include:

- `ASSESSED` — a supported Assessment Result is available;
- `UNKNOWN` — the evidence is valid but does not support a required characterization;
- `CONFLICTING` — the evidence supports incompatible findings that cannot be consolidated safely;
- `REVIEW_REQUIRED` — governed human judgment is required;
- `INPUT_NOT_READY` — the ReqKB evidence set is structurally or semantically insufficient for assessment.

Failure to characterize is not automatically a processing failure. It may be a legitimate statement about the evidence.

## 10. Feedback to Stage 1

Assessment must provide a controlled feedback route when the problem belongs to ReqKB rather than to interpretation.

Examples include:

- unresolved source reference;
- missing context caused by an incorrect SourceUnit boundary;
- invalid or superseded evidence;
- conflicting source revisions;
- missing terminology resolution required to interpret the evidence.

Stage 2 records the issue and routes it to the appropriate Stage 1 review or remediation process. Stage 2 must not repair canonical evidence itself.

## 11. Relationship to Stage 3

Stage 3 consumes only governed Stage 2 outputs.

```text
Assessment Result
        ↓
Characteristic Set
        ↓
Design Rule Matching
        ↓
Design Obligations
        ↓
Design Planning
        ↓
Artifact Plan
```

Stage 3 may use project architecture, standards, design rules, existing designs and human design decisions. Those inputs are intentionally excluded from Stage 2 because they can bias characterization toward a preferred solution.

A downstream BD generator must not use Assessment Results as a shortcut around Design Governance. When factual evidence is required for BD content, Stage 4 retrieves the authoritative SourceUnits from ReqKB through the assessment and planning trace.

## 12. Change and invalidation model

An Assessment Result is derived from a defined baseline and may become stale even when its text has not changed.

Reassessment must be considered when any governing dependency changes, including:

- Requirement Evidence Set or source revision;
- Assessment Framework or Standard;
- characteristic taxonomy;
- Assessment Knowledge or rule set;
- model, prompt or execution policy where the change can materially affect interpretation;
- accepted human review decision.

Stage 2 therefore treats Assessment Results as versioned derived knowledge rather than permanent facts.

## 13. Success criteria

The methodology is successful when:

- architects agree that the Characteristic Set captures the repeatable information they establish before making design decisions;
- different approved execution methods produce materially consistent classifications for clear cases;
- every accepted characteristic can be traced to evidence and a governed assessment baseline;
- ambiguous cases are surfaced rather than hidden by confident generation;
- Stage 3 can apply Design Governance without repeatedly rereading raw RD prose for basic characterization;
- design-rule changes do not require reassessment when the underlying requirement characteristics remain unchanged;
- requirement or assessment changes invalidate downstream results in a controlled and traceable manner.

## 14. Methodology completion gate

This methodology is ready to govern implementation only after the project has demonstrated it on a reviewed sample of real requirements.

Before automation is considered authoritative, the project should be able to show that human reviewers can apply the same Assessment Framework to the sample and reach sufficiently consistent Characteristic Sets. Disagreement at this level indicates that the framework or standard requires refinement before adding more automation.
