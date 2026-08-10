# Database Architecture Review Methodology

**Status:** POC review baseline  
**Scope:** Database architecture, version governance, physical schema, and migration safety  
**Purpose:** Provide a repeatable review method that remains valid even when the ReqKB workflow changes.

---

## 1. Review philosophy

Database review must not start from SQL syntax or from the current workflow nodes.

Review in this order:

```text
Business identity
  ↓
Data lifecycle & version semantics
  ↓
System of Record / ownership
  ↓
Logical relationships & constraints
  ↓
Concurrency / consistency
  ↓
Physical schema
  ↓
Indexes / performance / security
  ↓
Migration & drift safety
```

A schema that is fast but models the wrong lifecycle is still a bad schema.

---

## 2. Research basis

This methodology combines lessons from several independent sources. The sources are used for different review layers rather than treated as one universal checklist.

### 2.1 Supabase Agent Skills — PostgreSQL implementation review

Source:

- https://github.com/supabase/agent-skills
- `supabase-postgres-best-practices`

The skill explicitly covers schema design, query performance, connection management, concurrency/locking, RLS/security, access patterns, and monitoring.

Use it primarily for **physical PostgreSQL review**, after the domain model is already sound.

### 2.2 GitHub Awesome Copilot — independent PostgreSQL code review

Source:

- https://github.com/github/awesome-copilot
- `postgresql-code-review`

The skill focuses on PostgreSQL-specific schema quality, JSONB, custom types, constraints, indexes, functions, RLS, privileges, and PostgreSQL anti-patterns.

Use it as an **independent second reviewer** to challenge the physical design and catch engine-specific issues.

### 2.3 wshobson/agents — logical database and architecture review

Source:

- https://github.com/wshobson/agents
- `postgresql-table-design`
- `architecture-patterns`
- `event-store-design`
- `projection-patterns`

The repository separates focused architecture/database skills and emphasizes composability and clear responsibility boundaries.

Use it mainly for **logical modeling, identity, projection, architecture boundaries, and system-of-record reasoning**.

### 2.4 Atlas — schema-as-code and migration verification

Source:

- https://github.com/ariga/atlas

Atlas supports declarative and versioned schema workflows, schema diff, migration planning/linting, testing, and drift detection across PostgreSQL and SQLite among other databases.

Use it for **machine-verifiable schema change review** after the physical schema exists.

### 2.5 Bytebase — database change governance reference

Source:

- https://github.com/bytebase/bytebase

Bytebase provides database CI/CD, schema change review, GitOps integration, migration management, SQL Review, approval workflows, and audit-oriented database lifecycle management.

Use it as a **reference architecture for database version/change governance**, not as the ReqKB persistence model itself.

---

## 3. Five review gates

Every meaningful database design change should pass five gates.

### Gate A — Domain & identity

Question: **Are we versioning the correct business objects?**

Check:

- stable business identity vs revision identity;
- execution identity vs artifact identity;
- what event creates a new revision;
- whether the design depends on current workflow node names;
- whether one generic `version` field is hiding several version semantics;
- whether a candidate revision belongs to a stable ArtifactSeries/OutputSlot.

Typical P0 findings:

```text
Run ID used as artifact identity
Latest row treated as current truth
Stage-specific tables created for every workflow node
No stable identity for the object being baselined
```

Primary review lens: logical modeling / architecture skills.

---

### Gate B — Ownership, lineage & version governance

Question: **Can the system prove what is canonical and why?**

Check:

- System of Record for every representation;
- immutable target vs mutable/current pointer;
- baseline selection history;
- publication/promotion separated from execution;
- provenance from input revision to output revision;
- review/approval evidence;
- exact upstream input pinning;
- stale/downstream dependency handling;
- concurrent baseline update semantics.

Required rule:

```text
latest != baseline
success != approval
baseline != publication
```

Typical P0 findings:

```text
/final folder determines truth
baseline row overwritten without history
AI recommendation implicitly equals approval
relational projection and object artifact both claim to be canonical
last-write-wins on baseline change
```

Primary review lens: version governance; Bytebase is a useful change-governance reference.

---

### Gate C — Logical relational model

Question: **Can the model enforce valid states without depending on application convention?**

Review:

- PK/FK boundaries;
- cardinality;
- optional vs mandatory relationships;
- normalization vs intentional projection/denormalization;
- uniqueness constraints;
- state transition invariants;
- many-input / DAG support where required;
- delete/retention semantics;
- queryable projection rebuildability.

Important principle:

> Prefer database constraints for invariants that must never be violated; do not rely only on application code.

Examples:

```text
one OutputSet belongs to exactly one StageExecution
one StoredObject belongs to exactly one OutputSet
one baseline revision selects one OutputSet for one OutputSlot
only one current baseline is allowed per baseline scope
```

Primary review lens: table-design and architecture modeling.

---

### Gate D — Physical DB quality

Question: **Is the chosen engine used safely and efficiently?**

For PostgreSQL review:

- data types;
- PK strategy;
- FK indexes;
- compound/partial indexes;
- JSONB only where query semantics justify it;
- timestamp/time-zone types;
- CHECK/UNIQUE constraints;
- transaction boundaries;
- locking and concurrency;
- role/privilege/RLS requirements;
- connection pooling and scale assumptions.

For SQLite POC review:

- writer concurrency assumptions;
- transaction behavior;
- foreign keys enabled;
- WAL/locking decision;
- indexes based on real query paths;
- features that will require redesign when moving to PostgreSQL.

Use Supabase `supabase-postgres-best-practices` as the primary implementation checklist and GitHub `postgresql-code-review` as an independent second pass for PostgreSQL.

---

### Gate E — Migration, drift & operability

Question: **Can the schema evolve safely after data exists?**

Check:

- schema-as-code source;
- migration history;
- destructive changes;
- NOT NULL/default changes on existing data;
- large-table rewrite/lock risk;
- backward compatibility during deployment;
- rollback/roll-forward strategy;
- drift between expected and actual schema;
- data backfill strategy;
- migration tests.

Recommended machine verification when implementation begins:

```text
schema definition
   ↓
Atlas inspect / diff
   ↓
Atlas migration lint
   ↓
review
   ↓
apply
   ↓
drift detection
```

Bytebase can be studied when a larger approval/change-management layer is needed.

---

## 4. Review severity

Use three severities.

### P0 — architecture blocker

Must fix before physical schema implementation.

Examples:

- incorrect business/version identity;
- ambiguous System of Record;
- no baseline/concurrency semantics;
- workflow-specific schema that cannot support foreseeable changes;
- provenance cannot be reconstructed;
- destructive mutation of immutable history.

### P1 — design risk

Fix before pilot/production or before the affected capability is implemented.

Examples:

- missing constraint/index strategy;
- unclear stale propagation;
- weak migration strategy;
- excessive JSON/denormalization;
- poor transaction boundary.

### P2 — optimization / maintainability

Can be deferred with an explicit backlog item.

Examples:

- naming consistency;
- optional secondary indexes;
- convenience views;
- observability improvements.

---

## 5. Multi-reviewer process

A strong review should use independent passes rather than one agent attempting everything at once.

```text
Pass 1 — Architecture Reviewer
identity / lifecycle / ownership / boundaries

Pass 2 — Version Governance Reviewer
revision / baseline / audit / concurrency / publication

Pass 3 — Database Model Reviewer
ERD / PK-FK / constraints / cardinality / query model

Pass 4 — Engine Reviewer
PostgreSQL or SQLite physical design

Pass 5 — Migration Reviewer
schema diff / migration safety / drift
```

The reviewers may disagree. Resolve disagreements against explicit requirements and invariants, not majority voting.

---

## 6. Required review inputs by maturity

### Methodology stage

Input:

- data lifecycle;
- business identities;
- version rules;
- ownership boundaries;
- expected query/use cases.

Do not review indexes yet.

### Logical model stage

Input:

- entity definitions;
- ERD;
- cardinality;
- lifecycle/state transitions;
- baseline/publication rules.

### Physical schema stage

Input:

- DDL;
- representative queries;
- expected volumes;
- concurrency model;
- selected DB engine.

### Migration stage

Input:

- current schema;
- desired schema;
- existing data characteristics;
- deployment compatibility constraints.

---

## 7. Standard review output

Every review must produce the same structure:

```text
Overall assessment

P0 findings
- finding
- consequence
- recommended correction

P1 findings
...

P2 findings
...

Decisions confirmed
- what is already correct and should not be reopened

Open architecture decisions
- decisions that require explicit choice

Next gate
- what artifact must exist before the next review
```

Avoid reviews that only say "looks good" or produce a long generic best-practices list.

---

## 8. ReqKB-specific architecture invariants

The current ReqKB database design should preserve these invariants even when workflow steps change:

1. A SourceAsset may have many immutable SourceRevisions.
2. Processing execution is separate from output/artifact identity.
3. Every candidate OutputSet belongs to a stable OutputSlot/ArtifactSeries.
4. A StageExecution may consume multiple exact versioned inputs.
5. Object Store owns immutable payload; Catalog DB owns identity/governance/lineage.
6. Relational content projections are explicitly rebuildable from their canonical artifact.
7. Baseline is an explicit append-only governance decision; `latest` is never implicit baseline.
8. Concurrent baseline changes cannot silently become last-write-wins.
9. Publication to ReqKB is separate from intermediate baseline selection.
10. Workflow node changes should not require core schema redesign.

These invariants are the primary review standard for `01_design_methodology.md`, `02_storage_boundary.md`, the logical ERD, and the physical schema.

---

## 9. Recommended tool usage for this project

Current recommendation:

```text
Logical architecture review
→ architecture/table-design skill or database architect reviewer

PostgreSQL physical review
→ supabase-postgres-best-practices
→ github/awesome-copilot postgresql-code-review as second pass

Schema/migration verification
→ Atlas

Database change governance research
→ Bytebase patterns
```

Tools supplement architecture judgment; they do not decide domain identity or System-of-Record boundaries automatically.
