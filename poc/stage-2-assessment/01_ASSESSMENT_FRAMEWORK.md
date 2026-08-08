# Assessment Framework

## 1. Purpose

The Assessment Framework defines **what must be examined in requirement evidence before Design Governance is applied, and why each assessment item matters**.

It is the governed scope of Stage 2 interpretation.

The Framework does not define Design Rules, architecture decisions, artifact plans, prompts, model behavior or implementation technology. It establishes the minimum set of design-relevant distinctions that Stage 2 must make visible to downstream consumers.

```text
Requirement Evidence Set
        ↓
Assessment Framework
WHAT must be examined?
WHY does each distinction matter?
        ↓
Assessment Standard
What classifications are valid?
        ↓
Assessment Method
How are they recognized and classified?
```

The Framework must be validated before the project optimizes classification accuracy or automation.

## 2. Framework design question

The primary design question is:

> What must a Solution Architect understand about a requirement before applying project-specific Design Governance?

This question is intentionally different from:

> What should the solution look like?

The first belongs to Stage 2. The second belongs to Stage 3.

The Framework therefore captures **pre-design distinctions**, not design responses.

## 3. Framework unit: Assessment Item

An `Assessment Item` is a governed question or dimension used to examine a Requirement Evidence Set.

Every Assessment Item must define, at minimum:

- **Name** — the concern being examined;
- **Question** — what the assessor is trying to establish;
- **Why it matters** — why the distinction is relevant to downstream design reasoning;
- **Scope** — what kinds of evidence or requirement concerns the item applies to;
- **Boundary** — what the item explicitly does not decide;
- **Expected characteristic family** — the semantic kind of output the item may produce;
- **Applicability** — whether the item is universal or conditional.

The Framework intentionally does not define detailed classification criteria. Those belong to the Assessment Standard.

## 4. Selection principles

An Assessment Item is admitted to the Framework only when it passes all of the following tests.

### 4.1 Design-relevance test

The item must expose a distinction that can materially change which design concerns Stage 3 must consider.

This does not require Stage 2 to know the Design Rule that will eventually apply.

### 4.2 Evidence-observability test

The distinction must be establishable, at least in principle, from governed requirement evidence or explicitly representable as unknown.

Items that require knowledge of the chosen solution do not belong in Stage 2.

### 4.3 Non-design test

The item must characterize the requirement rather than prescribe a solution.

For example:

```text
"Does the requirement involve persistent business state?"
→ valid Assessment question

"Should the solution use a workflow engine?"
→ Design Governance / Planning question
```

### 4.4 Distinctiveness test

The item must capture information not already represented adequately by another Assessment Item.

Overlapping dimensions increase ambiguity and reduce repeatability.

### 4.5 Actionable-downstream test

A qualified SA must be able to explain why knowing the result is useful before design decisions are made.

If no downstream design concern changes when the result changes, the item should be challenged or removed.

### 4.6 Assessability test

The item must be definable clearly enough that an Assessment Standard can later specify valid classifications, evidence expectations and uncertainty conditions.

A concept that cannot be operationalized even for qualified human assessors is not ready for automation and may not be ready for the Framework.

## 5. Sufficiency model

Framework quality is not measured by the number of dimensions.

The target is **minimum sufficient coverage** for the intended Basic Design scope.

```text
Too little
→ materially different requirements collapse into the same assessment

Sufficient
→ important pre-design distinctions are visible downstream

Too much
→ taxonomy and assessment cost grow without additional design value
```

Framework sufficiency must be evaluated on representative project requirements rather than only by expert opinion.

### 5.1 Missing-distinction test

Take two real requirement situations that experienced architects would treat differently during design.

If the Framework cannot express the relevant difference without making a design decision, a dimension may be missing.

### 5.2 Irrelevant-distinction test

Take an existing Assessment Item and imagine removing it.

If Stage 3 would lose no meaningful design-relevant distinction across the target requirement set, the item may not justify its cost.

### 5.3 Coverage test

Apply the Framework to a representative requirement sample and record cases where assessors repeatedly need to describe an important characteristic outside the governed items.

Repeated out-of-framework observations are candidates for Framework evolution, not permission for ad-hoc taxonomy creation during execution.

## 6. Proposed core Assessment Items

The following items form the initial working hypothesis for the RD → BD use case. They are **candidates to be validated**, not universal truths and not claims of an IPA-defined taxonomy.

### 6.1 Functional Intent

**Question:** What business or system behavior is the requirement asking to occur?

**Why it matters:** Design Governance needs to distinguish materially different kinds of behavior before determining applicable design concerns.

**Characteristic family:** behavior / functional intent.

**Boundary:** does not decide the implementing component, interface or technology.

### 6.2 Interaction

**Question:** Does the requirement involve interaction between an actor and the system, or among identifiable participants?

**Why it matters:** Different interaction structures create different concerns around input, response, authorization, presentation and coordination.

**Characteristic family:** interaction pattern and participant structure.

**Boundary:** does not decide that a Screen, API or other interface artifact must exist.

### 6.3 Process and State

**Question:** Does the requirement describe progression, sequencing, lifecycle or persistent business state?

**Why it matters:** Stateful, sequential, conditional and stateless behavior create materially different design concerns.

**Characteristic family:** process/state characteristics.

**Boundary:** does not select workflow engines, state machines, persistence structures or orchestration patterns.

### 6.4 Information

**Question:** What business information is created, consumed, changed, referenced or constrained by the requirement?

**Why it matters:** Information behavior affects downstream concerns such as ownership, integrity, validation, lifecycle and consistency.

**Characteristic family:** information usage and information behavior.

**Boundary:** does not define database tables, schemas, storage technology or physical data models.

### 6.5 Integration and Boundary

**Question:** Does the requirement cross a system, organizational or externally governed boundary?

**Why it matters:** Boundary crossing creates distinct concerns around contracts, failure, trust, ownership and coordination.

**Characteristic family:** integration and boundary characteristics.

**Boundary:** does not choose REST, messaging, file transfer, middleware or any integration technology.

### 6.6 Control and Policy

**Question:** Is behavior constrained by authorization, approval authority, business policy, segregation, auditability or another explicit control concern?

**Why it matters:** Controlled behavior requires downstream governance to consider enforcement, accountability and traceability differently from unconstrained behavior.

**Characteristic family:** control / policy characteristics.

**Boundary:** does not prescribe authorization mechanisms, audit implementation or security products.

### 6.7 Quality and Constraint

**Question:** Does the requirement state a quality expectation or constraint that affects acceptable solution behavior?

**Why it matters:** Performance, availability, security, usability, regulatory or operational constraints can materially alter which design concerns must be addressed even when functional intent is unchanged.

**Characteristic family:** quality and constraint characteristics.

**Boundary:** does not select architecture tactics, products or implementation patterns.

## 7. Debate: BPR / McKinsey view vs AI Engineering view

The candidate Framework must survive both perspectives before it is stabilized.

### 7.1 BPR / management-consulting challenge

The BPR perspective asks whether the Framework captures the minimum set of distinctions needed to support the design objective.

It challenges each item with questions such as:

- Why does this item exist?
- What downstream distinction is lost without it?
- Is this actually one dimension or several different business concerns grouped together?
- Are we describing the requirement, or importing solution thinking?
- Is there a major requirement situation that the current items cannot represent?
- Can two items be merged without losing decision value?

From this perspective, the principal risk is **framework bureaucracy**: a large, sophisticated taxonomy that produces assessment work but little additional design value.

### 7.2 AI Engineering challenge

The AI Engineering perspective asks whether the same Framework can later become an explicit, testable semantic contract.

It challenges each item with questions such as:

- Can the item be expressed as a bounded assessment question?
- Can its classification family be made mutually understandable and sufficiently distinguishable?
- Can evidence requirements be defined?
- Can unknown, ambiguous and conflicting outcomes be represented?
- Can two independent assessors be evaluated for semantic agreement?
- Can the item be versioned without destabilizing unrelated classifications?

From this perspective, the principal risk is **semantic vagueness**: a Framework that sounds sensible to experts but leaves so much interpretation implicit that prompts or human judgment become the real undocumented standard.

### 7.3 SA reconciliation

The SA view reconciles the two by requiring each Assessment Item to be both:

1. meaningful enough to affect downstream design consideration; and
2. explicit enough to become a governed semantic contract without embedding the design response.

An item that passes only one side is not ready.

## 8. Open challenge on the proposed core items

The seven candidate items above should not yet be treated as final.

Several areas require deliberate validation on real RD samples:

- whether `Functional Intent` is genuinely useful as an Assessment dimension or is already sufficiently represented by Stage 1 ontology;
- whether `Interaction` and `Control and Policy` overlap for approval-oriented requirements;
- whether `Process` and `State` should remain one item or become separate dimensions;
- whether `Information` describes requirement characteristics or duplicates ReqKB entity extraction;
- whether `Integration` and `Boundary` should be separated because not every meaningful boundary crossing is system integration;
- whether `Quality and Constraint` is too broad to produce a stable characteristic family;
- whether additional dimensions are needed for exception/error behavior, temporal behavior, volume, lifecycle or organizational responsibility.

These are Framework questions and must be settled through sample-based sufficiency analysis before detailed taxonomy design.

## 9. Framework applicability

Not every Assessment Item must produce a characteristic for every Requirement Evidence Set.

The Framework distinguishes:

- **applicable and classified** — the item applies and evidence supports a governed characteristic;
- **applicable but unknown** — the item matters but evidence is insufficient;
- **applicable but conflicting** — evidence supports incompatible conclusions;
- **not applicable** — the item does not apply to the assessment subject.

`Not applicable` and `Unknown` are semantically different and must not be collapsed.

The Framework itself defines applicability logic at a conceptual level; detailed operational criteria belong to the Assessment Standard.

## 10. Framework evolution

The Framework is a governed project asset.

New dimensions must not be created ad hoc by an LLM or individual assessor during execution.

A proposed addition, split, merge or removal should be supported by evidence such as:

- repeated missing distinctions in representative requirements;
- downstream Design Governance unable to make a necessary distinction;
- persistent human disagreement caused by overlapping items;
- assessment items that show no meaningful downstream use;
- new project scope introducing genuinely new design-relevant concerns.

Framework changes require versioning because they can alter the meaning or completeness of existing Assessment Results.

## 11. Framework validation approach

Before freezing the initial Framework:

```text
1. Select representative RD samples
        ↓
2. Ask qualified SA/BPR reviewers:
   "What must be understood before design?"
        ↓
3. Map observations to candidate Assessment Items
        ↓
4. Record missing, overlapping and irrelevant items
        ↓
5. Refine the Framework
        ↓
6. Re-run on the sample
        ↓
7. Confirm downstream Design Governance can consume the distinctions
```

The objective at this stage is not inter-rater classification accuracy. That comes after the Assessment Standard defines classifications and criteria.

The Framework validation question is narrower:

> Are we asking the right and sufficient questions before design begins?

## 12. Framework acceptance gate

The Assessment Framework is ready for Standard design only when:

- every Assessment Item has a clear WHY;
- every item stays on the requirement-characterization side of the Stage 2 / Stage 3 boundary;
- representative requirements do not expose recurring material distinctions outside the Framework;
- overlapping items have been reduced to an acceptable level;
- each item can plausibly support a bounded characteristic family;
- downstream SA reviewers confirm that the resulting distinctions are useful inputs to Design Governance;
- AI Engineering confirms that each item is explicit enough to be operationalized later without inventing hidden semantics in prompts.

Only after this gate should the project define detailed characteristic taxonomy and classification criteria in the Assessment Standard.