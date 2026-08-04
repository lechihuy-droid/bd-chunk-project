# Assessment Inputs

## 1. Input categories

Assessment requires three governed input categories:

```text
Requirement Evidence
+ Assessment Standard
+ Assessment Knowledge
```

These categories must remain distinguishable because they have different authorities and change cycles.

## 2. Requirement Evidence

Requirement Evidence is read from ReqKB.

Minimum evidence package:

- requirement or evidence-set identifier;
- relevant SourceUnit IDs;
- verbatim source text;
- document, revision, heading and location metadata;
- lightweight ontology annotations from Stage 1;
- literal references to related requirements or business rules;
- validation and review status;
- active/superseded state.

Only accepted and traceable SourceUnits enter the automatic assessment path. Review or rejected units remain visible but cannot silently support accepted findings.

### Evidence selection

Assessment may require more than one SourceUnit when meaning is distributed across:

- a lead-in and dependent list;
- requirement and exception clauses;
- requirement and referenced business rule;
- multiple versions or related sections.

The evidence package must record why each SourceUnit was included.

## 3. Assessment Standard

The Assessment Standard is the semantic contract for the stage.

It contains:

- framework and viewpoint versions;
- characteristic taxonomy;
- definitions and boundaries;
- allowed outcome states;
- evidence requirements;
- acceptance and review policy;
- examples and counterexamples.

The standard is authoritative for classification. Rules and LLM prompts may not invent values outside it.

## 4. Assessment Knowledge

Assessment Knowledge helps methods recognize and classify characteristics.

It may include:

- business and requirement glossary;
- approved aliases;
- characteristic pattern library;
- deterministic assessment rules;
- positive and negative examples;
- known ambiguity cases;
- LLM instructions and structured-output schema;
- reviewer guidance;
- historical reviewed assessments.

Assessment Knowledge supports execution but does not override source evidence or the Assessment Standard.

## 5. Optional contextual input

Limited context may be supplied when required to interpret the requirement:

- project or domain identifier;
- business capability taxonomy;
- trusted document manifest;
- active terminology dictionary;
- explicitly linked neighboring evidence.

Project design conventions and architecture decisions must not be included at this stage. They belong to Design Governance and may bias assessment toward a preferred solution.

## 6. Input authority order

When inputs disagree, apply this authority order:

```text
Verbatim active source evidence
→ accepted source metadata and traceability
→ Assessment Standard
→ approved terminology and pattern knowledge
→ model inference
```

Model inference cannot override explicit source evidence.

## 7. Input readiness gate

An evidence package is ready when:

- all SourceUnits are traceable to active document revisions;
- raw text and metadata are accessible;
- Stage 1 validation permits assessment;
- the applicable Assessment Standard version is known;
- unresolved source conflicts are explicitly represented;
- the package contains sufficient context to avoid detached-pronoun or missing-reference interpretation.

If these conditions fail, Assessment returns `input_not_ready` rather than guessing.
