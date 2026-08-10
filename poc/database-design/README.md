# ReqKB Database Design Package

**Status:** POC database-design handoff  
**Audience:** Coding agent, backend developer, architect, reviewer

This folder is the database architecture + implementation contract for ReqKB ingestion.

---

## 1. Read in this order

```text
00_database_review_methodology.md
  ↓ how to review
01_design_methodology.md
  ↓ lifecycle/versioning principles
02_storage_boundary.md
  ↓ canonical owner / System of Record
03_logical_data_model.md
  ↓ entities, relationships, invariants, ERD
04_physical_schema.md
  ↓ SQLite tables, PK/FK/CHECK/UNIQUE/index/transactions
06_data_flow.md
  ↓ how data moves end-to-end
07_data_mutation_spec.md
  ↓ exact action → read/write fields → transaction → failure
08_data_dictionary.md
  ↓ field meaning / source / mutability
05_implementation_guide.md
  ↓ application/repository/runtime boundaries and coding order
schema/sqlite/001_init.sql
  ↓ executable initial SQLite schema
```

For a fast overview first open:

```text
database_design_summary.html
```

---

## 2. What each document answers

| File | Main question |
|---|---|
| `00_database_review_methodology.md` | Review database design in what order? |
| `01_design_methodology.md` | How do identity/version/baseline/publication lifecycles work? |
| `02_storage_boundary.md` | Which store owns which state? |
| `03_logical_data_model.md` | What entities exist and how are they related? |
| `04_physical_schema.md` | What tables/columns/constraints/indexes exist? |
| `05_implementation_guide.md` | How should Web App/services/repositories/runtime adapters be separated? |
| `06_data_flow.md` | Where does data move for each workflow flow? |
| `07_data_mutation_spec.md` | When action X happens, exactly what is read/written and in what transaction? |
| `08_data_dictionary.md` | What does each field mean, who supplies it and may it mutate? |
| `001_init.sql` | What SQL actually creates the current SQLite schema? |
| `database_design_summary.html` | What should a reviewer understand in 3–5 minutes? |

---

## 3. Source-of-truth precedence

Different files own different concerns. Do not choose whichever file is convenient.

```text
Architecture decision / rationale
→ ADR + 02/03

Logical identity / cardinality / invariant
→ 03_logical_data_model.md

Physical type / nullability / PK/FK/CHECK/UNIQUE/index
→ 04_physical_schema.md

Action mutation behavior / transaction / failure
→ 07_data_mutation_spec.md

Field semantics / value source / mutability
→ 08_data_dictionary.md

Executable SQLite DDL
→ schema/sqlite/001_init.sql
```

`001_init.sql` must implement `04`; it does not redefine architecture.

If executable SQL and `04` differ, treat it as **schema drift/defect** and reconcile before coding continues.

---

## 4. Core architecture in one screen

```text
Object Store
= canonical immutable payload bytes

Catalog DB
= business identity + execution correlation + exact lineage
  + candidate registry + baseline + publication governance

Neo4j / ReqKB
= published semantic knowledge

LangGraph / Prefect
= execution runtime only

MLflow
= optional trace/evaluation/experiment layer
```

Non-negotiable:

```text
latest != baseline
successful execution != accepted artifact
accepted artifact != published knowledge
runtime checkpoint != governance System of Record
```

---

## 5. Current POC domain tables

```text
workspace
source_asset
source_revision
processing_run
stage_execution
stage_input
output_slot
output_slot_scope_member
output_set
stored_object
baseline_selection
baseline_head
knowledge_space
publication_scope
publication
publication_head
```

Conditional/deferred capabilities are documented in `03/04` and must not be added just for completeness.

---

## 6. Migration/version rule

`schema/sqlite/001_init.sql` is schema version 001.

After a migration has been applied to a shared environment:

```text
DO NOT edit historical migration
```

Future schema changes use:

```text
002_<change>.sql
003_<change>.sql
...
```

Every schema change must identify:

```text
why the change is needed
which logical invariant/requirement it supports
backfill/migration impact
rollback/backward-compatibility impact
whether an ADR is required
```

Migration runner may keep applied-version bookkeeping as infrastructure metadata; it is not one of the domain tables above.

---

## 7. ADRs

Current accepted decisions:

```text
ADR-001
Stable PublicationScope across SourceRevision changes

ADR-002
StageInput physical reference = controlled dual FK + XOR CHECK

ADR-003
Minimal WorkflowRuntimePort; LangGraph current, Prefect replaceable
```

Create a new ADR when a change affects System of Record, publication/consistency semantics, security isolation, runtime guarantees, or another hard-to-reverse cross-module contract.

---

## 8. Coding-agent entry point

Before writing repository/service code:

1. Read `06` to understand the end-to-end flow.
2. Read the relevant command section in `07`.
3. Check field meaning in `08`.
4. Verify constraints in `04` / `001_init.sql`.
5. Implement through application command/repository boundary from `05`.
6. Test invariants; do not weaken the schema because runtime code is inconvenient.

When unsure where state belongs:

```text
Payload bytes?          → Object Store
Business identity?      → Catalog DB
Lineage/governance?     → Catalog DB
Runtime checkpoint?     → LangGraph / Prefect
Published semantics?    → Neo4j
Trace/evaluation?       → MLflow later
```
