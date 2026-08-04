# Assessment Framework

## 1. Purpose

The Assessment Framework defines the stable viewpoints used to characterize requirement evidence before Design Governance is applied.

The framework answers:

> From which design-relevant perspectives must a requirement be examined?

It does not define detailed detection rules or design solutions.

## 2. Framework structure

The framework is organized as:

```text
Assessment Framework
├── viewpoint
├── assessment concern
├── characteristic category
└── allowed outcome state
```

A viewpoint is a lens. A characteristic is an assessment result produced through that lens.

## 3. Core viewpoints

### Business viewpoint

Examines the business intent expressed by the requirement.

Typical concerns:

- business capability involved;
- business event or trigger;
- participating roles;
- business object affected;
- governing condition or exception.

### Interaction viewpoint

Examines how actors or systems interact.

Typical concerns:

- initiating actor;
- receiving actor or system;
- request, response, notification or approval interaction;
- human versus machine interaction;
- single-party or multi-party coordination.

### Information viewpoint

Examines the information involved without designing storage.

Typical concerns:

- information read, created, changed or referenced;
- master, transaction or reference information;
- lifecycle or state-bearing information;
- sensitivity or retention concern stated in the requirement.

### Process viewpoint

Examines behavior over time.

Typical concerns:

- one-step or multi-step process;
- state transition;
- long-running activity;
- dependency on prior or subsequent actions;
- exception, cancellation or recovery path.

### Integration viewpoint

Examines boundaries between parties or systems.

Typical concerns:

- external or internal integration;
- inbound or outbound exchange;
- synchronous, asynchronous or scheduled interaction when evidenced;
- dependency on another system or organization.

### Quality viewpoint

Examines explicitly stated quality concerns.

Typical concerns:

- security;
- performance;
- availability;
- auditability;
- compliance;
- usability;
- reliability.

### Change and impact viewpoint

Examines the breadth and coupling implied by the requirement without deciding the design.

Typical concerns:

- isolated versus cross-domain change;
- dependency on shared business objects;
- impact on multiple actors or business processes;
- reference to existing behavior that must remain compatible.

## 4. Framework boundaries

The framework may classify:

- approval-oriented interaction;
- stateful process;
- externally integrated behavior;
- read/write information behavior;
- explicitly stated audit concern.

The framework must not produce:

- use Kafka;
- create API X;
- add table Y;
- apply Saga;
- generate screen Z.

Those are downstream governance or design outcomes.

## 5. Extensibility

Viewpoints are versioned and changed conservatively.

A new viewpoint should be added only when:

- an important design-relevant concern cannot be represented by existing viewpoints;
- the concern appears across multiple requirements or projects;
- downstream governance needs it as a stable input;
- reviewers can distinguish it consistently.

Project-specific vocabularies should extend characteristic categories before introducing entirely new viewpoints.

## 6. Unknown and conflict states

Every viewpoint must support:

- `identified` — supported characteristic exists;
- `not_applicable` — viewpoint does not apply;
- `unknown` — evidence is insufficient;
- `conflicting` — evidence supports incompatible findings;
- `review_required` — automated methods cannot decide safely.

Absence of evidence must not be converted into a negative claim.

## 7. Framework governance

The framework is owned jointly by:

- requirement engineering representatives;
- software architects;
- design governance owners;
- assessment reviewers.

Changes require examples from the golden dataset and an impact review on existing Assessment Results and Design Governance rules.
