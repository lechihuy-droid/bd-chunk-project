# Assessment Methodology

## 1. Purpose

Requirement Assessment exists to make the pre-design interpretation of requirements explicit, governed and reusable.

Stage 1 ReqKB preserves what the source says. Stage 3 Design Governance and Design Planning decide what the project must design. Stage 2 sits between them and answers a deliberately narrower question:

> Which characteristics of the requirement must be understood before design governance can make an informed design decision?

The methodology is therefore purpose-first. It does not begin by asking how accurately an LLM can classify requirements. It begins by establishing why an assessment is needed, what must be assessed, and whether those assessment items are sufficient for downstream design reasoning.

```text
Stage 1 — ReqKB
Requirement Evidence Set
        ↓
Stage 2 — Requirement Assessment
Design-relevant Characteristic Set
        ↓
Stage 3 — Design Governance + Design Planning
Design Obligations + Artifact Plan
        ↓
Stage 4 — Basic Design Generation
```

## 2. Why Assessment exists

A ReqKB is an evidence layer. Parsing, metadata, source traceability and lightweight ontology make requirement evidence retrievable and governable, but they do not by themselves establish the distinctions an architect uses before selecting a design response.

For example, source evidence may establish that a manager approves a purchase request under a stated condition. Before deciding any solution, an architect may need to understand whether the requirement represents approval behavior, whether business state changes, whether multiple actors participate, whether an authorization boundary exists, or whether an external system is involved.

Those are not yet design decisions. They are design-relevant characteristics of the requirement.

Without Stage 2, a downstream generative component is forced to combine several responsibilities:

```text
Understand evidence
+ decide what matters for design
+ characterize the requirement
+ recall design governance
+ choose design responses
+ plan artifacts
+ generate BD
```

That coupling makes the reasoning difficult to challenge, govern, reproduce and improve independently.

Stage 2 separates the question **"What must we understand about this requirement?"** from **"What should we design because of it?"**

## 3. Methodology logic: WHY → WHAT → SUFFICIENCY → STANDARD → EXECUTION

The Assessment methodology follows this order deliberately:

```text
WHY
Why does the distinction matter to design reasoning?
        ↓
WHAT
What assessment items or dimensions must be examined?
        ↓
SUFFICIENCY
Do those items cover the distinctions needed downstream?
        ↓
STANDARD
What makes a classification valid for each item?
        ↓
EXECUTION
How do Human / Rule / LLM apply the standard?
        ↓
QUALITY
Was the result correct, repeatable and useful?
```

This order is an architectural constraint.

The project must not optimize classification accuracy or LLM repeatability before establishing that the Assessment Framework is assessing the right things.

A system can classify an irrelevant taxonomy perfectly and still provide little value to design.

## 4. Relationship to human architecture work

A human Solution Architect rarely moves directly from raw requirement text to final design. Before choosing a solution, the architect establishes an internal model of the requirement: behavior, interaction, state, information, boundaries, controls, constraints and other concerns relevant to the design problem.

That intermediate interpretation is often implicit and may vary significantly between architects.

Stage 2 externalizes the part of this reasoning that should be systematic:

```text
Human workflow
Read evidence
→ determine what matters
→ recognize characteristics
→ apply design knowledge
→ plan solution
→ document design

Project workflow
ReqKB
→ Assessment Framework
→ Characteristic Set
→ Design Governance + Planning
→ BD Generation
```

Assessment does not attempt to replace architectural judgment. It creates a governed semantic input on which architectural judgment and design governance can operate.

## 5. Assessment Framework: WHAT must be assessed

The Assessment Framework defines the set of assessment items or dimensions through which requirement evidence must be examined.

Examples may eventually include interaction, process/state, information, integration, control, functional behavior and quality constraints. The definitive set is intentionally not defined in this methodology document; it belongs in `01_ASSESSMENT_FRAMEWORK.md`.

Every proposed assessment item must answer two questions before it is accepted into the Framework:

1. **What distinction does this item allow us to observe in requirement evidence?**
2. **Why does that distinction matter to downstream design reasoning?**

An item must not be included merely because it is easy to classify, commonly found in requirement documents, or technically interesting.

The Framework should contain the minimum set of distinctions necessary to support downstream design governance without collapsing materially different requirement situations into the same assessment result.

## 6. Sufficiency before correctness

Before asking whether individual classifications are correct, the project must establish whether the Framework itself is sufficiently complete for its intended purpose.

Framework sufficiency asks:

> Are there requirement situations that require materially different downstream design consideration but that the current Assessment Framework cannot distinguish?

If yes, the Framework is under-specified.

The opposite failure is also possible. A Framework may introduce many distinctions that do not affect downstream reasoning. Such a Framework is over-specified and creates classification cost without design value.

The target is therefore not maximum taxonomy coverage. The target is **purposeful coverage**.

Two practical tests govern Framework sufficiency:

### 6.1 Missing-distinction test

If two requirement situations need materially different design consideration but the Framework represents them identically, a relevant assessment dimension or classification may be missing.

### 6.2 Irrelevant-distinction test

If a distinction never changes which design concerns must be considered downstream, its inclusion in Stage 2 must be challenged.

These tests evaluate the Framework, not the execution engine.

## 7. Assessment Standard: what makes a classification valid

Once the Framework defines what must be assessed, the Assessment Standard defines what valid classification means within each assessment item.

For each governed classification, the Standard should eventually define concepts such as:

- semantic definition;
- positive criteria;
- exclusion criteria;
- minimum evidence expectations;
- ambiguous or insufficient-evidence conditions;
- conflicting-evidence handling;
- relationship to neighboring classifications.

For example, the Framework may decide that `Process / State Characteristic` is worth assessing. The Standard then defines how evidence is validly classified as `Stateful`, `Stateless`, `Unknown`, or another approved value.

This separation is intentional:

```text
Assessment Framework
WHAT matters?
        ↓
Assessment Standard
What does a valid classification mean?
        ↓
Assessment Method
How is the classification performed?
```

## 8. Correctness comes after sufficiency

Correctness is evaluated only after the Framework and Standard are defined.

A classification is not correct merely because it conforms to a schema or because multiple assessors agree with one another.

Assessment correctness has at least three aspects:

### 8.1 Evidence fidelity

The characteristic must be supported by the governed Requirement Evidence Set. Plausibility is not evidence.

### 8.2 Classification validity

The evidence must satisfy the approved meaning and criteria of the selected classification.

### 8.3 Boundary validity

The result must remain a requirement characteristic rather than introducing a downstream design choice.

For example:

```text
"The interaction is approval-oriented"
→ valid Stage 2 characteristic

"Use a workflow engine"
→ Stage 3 design decision, not Assessment
```

## 9. Repeatability comes after correctness

Repeatability asks whether independent qualified assessors applying the same Framework and Standard to the same governed evidence reach materially equivalent semantic conclusions.

Repeatability is not identical to deterministic output.

Two LLM executions or two human assessors may use different wording while reaching the same governed classification.

Conversely, high agreement does not prove correctness. A poorly designed Framework can make humans and AI consistently produce the same wrong or incomplete result.

Therefore:

> Repeatability is necessary for scalable automation, but it is not a substitute for Framework sufficiency or classification correctness.

## 10. Decision relevance

A characteristic exists in Stage 2 because it represents a distinction that downstream design governance may need to consider.

Decision relevance does not mean Stage 2 specifies the design response.

For example:

```text
Assessment dimension:
Process / State

Why it matters:
Stateful and stateless behavior create materially different design concerns.

Not allowed in Stage 2:
Stateful → use workflow engine.
```

The first statement justifies why the dimension belongs in Assessment. The second is a Design Governance rule and belongs in Stage 3.

This boundary allows the project to test whether an assessment item is useful without embedding design decisions into the Assessment Framework.

## 11. Assessment subject and evidence boundary

Assessment operates on a `Requirement Evidence Set`, not automatically on one SourceUnit.

A Requirement Evidence Set is the smallest governed collection of ReqKB evidence that provides sufficient context to assess one requirement concern. It may contain a single SourceUnit or multiple structurally related SourceUnits such as a requirement statement, condition, exception, referenced business rule or terminology evidence.

The evidence set remains traceable to ReqKB. Assessment is derived knowledge and never becomes the factual source of truth.

## 12. Assessment responsibility boundary

Assessment may:

- examine evidence through approved Framework items;
- recognize candidate characteristics;
- classify them according to the Assessment Standard;
- consolidate findings across evidence;
- expose ambiguity, conflict or insufficient information;
- preserve evidence and classification basis;
- route uncertain cases for governed review.

Assessment must not:

- select architecture or technology;
- decide that a Screen, API, Batch, Database table or other artifact must exist;
- apply Design Governance rules;
- produce Design Obligations;
- repair canonical ReqKB evidence;
- infer missing facts because they make a design convenient;
- generate Basic Design content.

## 13. Logical assessment process

Only after WHY, WHAT, sufficiency and classification standards are governed does execution begin.

```text
1. Frame
   Resolve the Assessment Subject and evidence boundary.

2. Examine
   Apply the relevant Assessment Framework items.

3. Recognize
   Identify candidate characteristics from evidence.

4. Classify
   Apply governed classification criteria.

5. Consolidate
   Merge equivalent findings and expose conflicts.

6. Validate
   Check evidence fidelity, classification validity and boundary validity.

7. Review / Publish
   Resolve governed review cases and publish accepted results.
```

The process is implementation-neutral. Human assessment, deterministic rules, LLM-assisted interpretation or hybrid execution may implement it.

## 14. Quality model

Stage 2 quality must not be represented by a single generic `accuracy` score.

The methodology distinguishes four quality questions:

### 14.1 Framework sufficiency

Are we assessing the distinctions that downstream design reasoning actually needs?

### 14.2 Correctness

Did we characterize the governed evidence correctly according to the Framework and Standard?

### 14.3 Repeatability

Can independent qualified assessors or approved execution methods reach materially equivalent semantic results?

### 14.4 Decision relevance

Does the assessed distinction matter to downstream design consideration without prescribing the design solution?

These dimensions must be evaluated separately because a system can be highly repeatable but systematically wrong, correct but inconsistent, or correct and repeatable while assessing distinctions that provide no downstream value.

## 15. Uncertainty and non-results

Assessment does not guarantee that every input produces a Characteristic Set.

Valid stage outcomes include:

- `ASSESSED` — supported governed characteristics are available;
- `UNKNOWN` — valid evidence does not support the required characterization;
- `CONFLICTING` — governed evidence supports incompatible findings;
- `REVIEW_REQUIRED` — qualified judgment is required;
- `INPUT_NOT_READY` — the ReqKB evidence set is not suitable for assessment.

No supported classification is preferable to an unsupported confident classification.

## 16. Provenance, versioning and reproducibility

Every published Assessment Result must identify enough governed context to explain how it was produced, including the evidence baseline and applicable Framework, Standard, knowledge and execution versions.

The goal is operational reproducibility rather than bit-for-bit deterministic generation.

A result is derived knowledge and may require reassessment when its evidence, Framework, Standard, classification taxonomy or materially relevant execution policy changes.

Stage 2 must never silently mutate source evidence or erase conflicting evidence.

## 17. Feedback to Stage 1

If Assessment cannot proceed because the evidence itself is structurally or semantically defective, Stage 2 routes the issue back to ReqKB governance.

Examples include unresolved references, incorrect SourceUnit boundaries, superseded evidence, conflicting source revisions or unresolved terminology required for interpretation.

Stage 2 records the problem; it does not repair canonical evidence itself.

## 18. Relationship to Stage 3

Stage 3 consumes governed Assessment Results:

```text
Requirement Evidence
        ↓
Assessment Characteristic Set
        ↓
Design Rule Matching
        ↓
Design Obligations
        ↓
Design Planning
        ↓
Artifact Plan
```

Stage 3 may use architecture principles, organization standards, Design Rules, patterns, existing designs and expert decisions. Those assets are excluded from Stage 2 because they represent design knowledge and can bias requirement characterization toward a preferred solution.

When Stage 4 requires factual support, it retrieves authoritative evidence from ReqKB through the trace chain rather than treating the Assessment Result as replacement evidence.

## 19. Validation sequence for the methodology

The project should validate Stage 2 in the following order:

```text
1. Purpose validation
   Do we agree why Assessment exists?

2. Framework sufficiency validation
   Are we assessing the right and sufficient distinctions?

3. Standard validation
   Are the classifications and criteria semantically sound?

4. Human correctness validation
   Can qualified reviewers apply them correctly to real requirements?

5. Human repeatability validation
   Do independent reviewers reach materially equivalent conclusions?

6. Downstream relevance validation
   Do the resulting distinctions support meaningful Design Governance reasoning?

7. Automation validation
   Can Rule / LLM / Hybrid execution reproduce the validated methodology at acceptable quality?
```

Automation is deliberately last.

The project must not use model performance to compensate for an unresolved Framework or Standard.

## 20. Methodology completion gate

Stage 2 methodology is ready to govern implementation only when a reviewed sample of real project requirements demonstrates all of the following:

- the purpose and boundary of Assessment are understood by Requirement, Architecture and AI Engineering stakeholders;
- the Framework covers the material pre-design distinctions needed for the target BD scope;
- proposed dimensions can justify why they matter downstream;
- classification criteria are sufficiently clear to evaluate correctness;
- qualified human reviewers can apply the Framework and Standard with acceptable semantic agreement;
- unresolved cases can be represented without forced classification;
- Design Governance can consume the Characteristic Set without requiring Stage 2 to make design decisions;
- automation can be evaluated against a validated human baseline rather than against an unvalidated taxonomy.

The governing principle is:

> First determine why and what to assess. Then prove that the Framework is sufficient. Then define what correct classification means. Only after that optimize repeatability and automation.

## 21. Review model for subsequent Stage 2 documents

Every subsequent Stage 2 document should be challenged from two deliberately different perspectives before it is treated as stable.

### BPR / management-consulting perspective

Challenge whether the document is purpose-driven, complete enough for the business/design decision, minimally sufficient, understandable to qualified practitioners and free of process or taxonomy that does not create downstream value.

Typical questions include:

- Why is this needed?
- What decision or distinction does it enable?
- What is missing?
- What can be removed without losing value?
- How would we know the process is working?

### AI Engineering perspective

Challenge whether the same methodology can be represented explicitly enough to execute, evaluate, version and scale through deterministic rules, LLMs or hybrid systems without hiding semantic ambiguity inside prompts.

Typical questions include:

- Is the input contract explicit?
- Are classification criteria machine-interpretable enough to test?
- Can uncertainty and conflict be represented?
- Can results be traced and reproduced?
- Can we separate methodology defects from model defects?

Neither perspective is authoritative by itself. The BPR perspective protects purpose, sufficiency and usefulness; the AI Engineering perspective protects explicitness, testability, repeatability and operational scalability. Stage 2 should be accepted only where both views can be reconciled without violating the SA boundary between requirement characterization and design decision.