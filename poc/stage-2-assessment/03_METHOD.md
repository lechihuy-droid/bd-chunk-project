# Assessment Method

## 1. Purpose

The Assessment Method defines how evidence is transformed into characteristics while remaining bounded by the Assessment Standard.

Three execution modes are allowed:

- deterministic rule-based assessment;
- LLM-assisted assessment;
- hybrid assessment.

The method is replaceable. The framework and output semantics are the stable contract.

## 2. Deterministic rule-based assessment

Use deterministic methods when evidence can be recognized through stable, explicit conditions.

Suitable cases include:

- explicit requirement identifiers and references;
- known verbs or phrases with low ambiguity;
- directly stated quality attributes;
- clear event, actor or state-transition language;
- approved terminology mappings.

Rule results must record the rule version and exact supporting evidence.

Rules should prefer precision over coverage. A rule should abstain when context makes the result ambiguous.

## 3. LLM-assisted assessment

Use an LLM when characterization requires contextual language interpretation that is difficult to capture reliably with deterministic rules.

The LLM must:

- receive only the bounded evidence package and applicable taxonomy;
- use structured output;
- return evidence references for every proposed characteristic;
- distinguish explicit evidence from interpretation;
- return `unknown` instead of inventing missing information;
- avoid any design recommendation.

The model is an assessor operating under the standard, not the owner of the standard.

## 4. Hybrid assessment

Hybrid is the default target state.

```text
Deterministic extraction
→ candidate characteristics
→ LLM assessment for unresolved context
→ consolidation
→ validation
→ review policy
```

Rules establish high-confidence findings and constraints. The LLM fills unresolved areas and may challenge rule output when it presents contrary evidence, but cannot silently override deterministic results.

## 5. Recognition and classification

Recognition and classification are separate operations.

- Recognition identifies a candidate concept in evidence.
- Classification maps that concept to the Assessment Standard.

For example:

```text
Evidence: “The manager approves or rejects the request.”
Recognition: approval/rejection interaction
Classification: Interaction characteristic = approval-oriented
```

This separation allows terminology and recognition logic to evolve without changing the downstream characteristic vocabulary.

## 6. Consolidation policy

Assessment may produce several findings from several SourceUnits.

Consolidation must:

- retain all contributing evidence;
- merge equivalent findings;
- preserve distinct characteristics when they can coexist;
- detect incompatible findings;
- avoid selecting one source version silently;
- mark unresolved conflict explicitly.

Confidence alone must not be used to erase contradictory evidence.

## 7. Decision policy

The method produces one of these outcomes for each applicable concern:

- accepted automatically;
- accepted after deterministic agreement;
- proposed for review;
- conflicting;
- unknown;
- not applicable.

Automatic acceptance requires both taxonomy validity and evidence support.

Human review is required when:

- rule and LLM results materially conflict;
- multiple classifications are plausible but mutually exclusive;
- evidence is distributed or incomplete;
- the finding would activate high-impact downstream governance;
- the model introduces a concept not explicitly grounded in the evidence package.

## 8. Method versioning

Every assessment run records:

- Assessment Framework version;
- taxonomy and standard version;
- rule-set version;
- prompt/schema version;
- model identifier when used;
- consolidation policy version;
- reviewer policy version.

A method change may trigger reassessment even when ReqKB evidence is unchanged.

## 9. Evaluation

Evaluate methods against a reviewed golden set using:

- characteristic precision and recall;
- evidence-grounding accuracy;
- conflict-detection rate;
- unknown/abstention quality;
- reviewer correction rate;
- inter-reviewer agreement;
- downstream Design Governance rule-match stability.

The goal is not maximum automatic coverage. The goal is consistent, evidence-backed characterization.