# ReqKB Ingestion Database Design Methodology

**Status:** POC architecture baseline  
**Scope:** Persistence and version governance for ReqKB ingestion  
**Audience:** System Architect, Database Engineer, AI Engineer, Backend Engineer, Coding Agent  
**Goal:** Define a workflow-agnostic data architecture that remains stable when ingestion steps, tools, or orchestration change.

---

## 1. Purpose and scope

This document defines the **database and persistence methodology**, not the detailed ingestion workflow.

The current ReqKB workflow may contain classification, conversion, parsing, validation, ontology enrichment, review, and publication steps. Those steps may change without forcing a redesign of the persistence model.

The database architecture therefore models stable concepts:

```text
Source Asset
    ↓
Source Revision
    ↓
Processing Run / Stage Execution
    ↓
Immutable Output Revision
    ↓
Baseline Selection
    ↓
Publication
```

Stage 2 Assessment, retrieval, BD generation, MLflow experiment tracking, and BD artifact governance are outside this document.

---

## 2. Design principles

### 2.1 Data-lifecycle first, workflow second

Design order:

```text
Data lifecycle
  → Business identity
    → Version semantics
      → Ownership / System of Record
        → Governance transitions
          → Logical model
            → Physical schema
```

Do not create tables directly from today's G0/G1/G2 node list.

### 2.2 Execution, artifact, baseline, and publication are different concepts

```text
Execution
    ↓ creates
Output Revision
    ↓ may become
Baseline
    ↓ may be
Published
```

A successful execution does not imply its output is trusted. A baseline does not imply it has been published into ReqKB.

### 2.3 Immutable targets, explicit mutable decisions

Historical evidence is append-only:

- Source Revision;
- completed execution facts;
- OutputSet and StoredObject;
- hashes and resolved configuration;
- review/selection decisions;
- publication history.

Mutable state is represented by explicit pointers or current-state records, never by overwriting the historical artifact.

Do not use `latest`, `/final`, or `current.json` as governance semantics.

### 2.4 One state has one primary owner

A value may have references or projections in multiple systems, but its canonical owner must be explicit.

---

## 3. Canonical data lifecycle

```text
SourceAsset
   └── SourceRevision
           │
           ├── ProcessingRun
           │      └── StageExecution
           │             ├── StageInput [0..N]
           │             └── OutputSet
           │                    └── StoredObject [1..N]
           │
           └── OutputSlot / ArtifactSeries
                    ├── OutputSet revision A
                    ├── OutputSet revision B
                    └── OutputSet revision C
                              ↑
                         BaselineHistory
                              │
                        Review / Policy
                              │
                         Publication
```

The model supports linear pipelines, DAGs, fan-in/fan-out, retries, and future stage changes without adding stage-specific foreign keys.

---

## 4. Core domain identities

### 4.1 SourceAsset

Stable business identity of an input document or source.

Example:

```text
SOURCE-001 = Customer Management Requirement Definition
```

### 4.2 SourceRevision

Immutable content revision of a SourceAsset.

```text
SOURCE-001
  ├── REV-001 hash=A
  ├── REV-002 hash=B
  └── REV-003 hash=C
```

Raw bytes are stored in Object Storage; the Catalog DB owns identity, hash, URI, type, timestamps, and source metadata.

### 4.3 ProcessingRun

Correlation container for one processing attempt or workflow invocation.

It is **not** the owner of the final/baseline state.

### 4.4 StageExecution

One execution of one processing capability.

Generic fields include:

```text
stage_execution_id
processing_run_id
stage_type
component_ref
configuration_hash
status
started_at
completed_at
runtime_ref
```

`stage_type` is configuration/data such as `CONVERT`, `PARSE`, or `ONTOLOGY`; it is not a reason to create new tables.

### 4.5 StageInput

A StageExecution may consume zero, one, or many exact inputs.

```text
stage_execution_input
---------------------
stage_execution_id
input_role
input_ref_type
input_ref_id
input_hash
```

This replaces a workflow-coupled `input_output_set_id` column and supports DAG/fan-in processing.

### 4.6 OutputSet

Immutable coherent result produced by a StageExecution.

A stage may produce multiple files that must be selected/versioned together:

```text
OUTSET-221
  ├── parsed-document.json
  ├── chunks.json
  └── diagnostics.json
```

### 4.7 StoredObject

Physical payload belonging to an OutputSet.

```text
stored_object_id
output_set_id
object_role
object_uri
content_hash
schema_version
media_type
```

### 4.8 OutputSlot / ArtifactSeries

Stable identity of **what is being versioned**.

Example:

```text
SLOT-17
source_revision = REV-003
logical_role = CHUNK_SET
```

It may have hundreds of candidate revisions:

```text
SLOT-17
  ├── OUTSET-187
  ├── OUTSET-221  ← baseline
  └── OUTSET-240
```

Without OutputSlot/ArtifactSeries, a baseline answers "which output" but not "baseline of what".

### 4.9 BaselineHistory

Append-only governance record selecting one OutputSet revision for one OutputSlot.

```text
baseline_id
output_slot_id
output_set_id
effective_from
effective_to
selection_mode
review_decision_id
created_at
```

`latest output != baseline`.

### 4.10 ReviewDecision

Records human, policy, or AI-assisted selection evidence.

AI may recommend; authority is determined by policy.

### 4.11 Publication

Boundary that materializes an accepted baseline into the downstream canonical knowledge store.

Publication is distinct from stage execution and baseline selection.

---

## 5. Version and baseline semantics

### 5.1 Different objects have different version semantics

Do not use one generic `version` field for everything.

- SourceRevision: source content changed.
- OutputSet revision: a new execution produced a new candidate.
- Schema version: contract shape changed.
- Component/config version: producer behavior changed.
- Baseline revision: governance selection changed.
- Publication revision: canonical published state changed.

### 5.2 Downstream processing pins exact inputs

A StageExecution never means "use the latest previous output".

It records exact StageInput references and hashes. This makes lineage reproducible even after the baseline changes later.

### 5.3 Baseline changes are append-only

Example:

```text
BASE-008 → OUTSET-187   effective T1..T2
BASE-009 → OUTSET-221   effective T2..∞
```

Do not mutate one row forever.

### 5.4 Baseline concurrency must be explicit

Two users/processes may try to change the same baseline.

Use optimistic concurrency or an equivalent DB constraint:

```text
expected_baseline_version = 8
approve OUTSET-230
→ baseline version 9
```

A second write expecting version 8 must fail with a conflict instead of silently becoming last-write-wins.

### 5.5 Selection and publication are separate transitions

Intermediate artifacts use **Baseline Selection**.

The ReqKB boundary uses **Publication/Promotion**.

This terminology prevents every internal selection from being treated as a publication event.

---

## 6. Storage ownership

### 6.1 Object Store — canonical immutable payload

Primary owner for:

- original DOCX/PDF/XLSX bytes;
- normalized/converted files;
- full parser output;
- chunk bundles;
- enrichment bundles;
- diagnostics and large evaluation evidence;
- publication manifests.

Object keys are locations, not current/final state.

Recommended generic layout:

```text
reqkb/
└── projects/{project_id}/
    └── sources/{source_asset_id}/
        ├── revisions/{source_revision_id}/raw/...
        └── runs/{processing_run_id}/
            └── stages/{stage_execution_id}/...
```

### 6.2 Ingestion Catalog DB — identity, governance, lineage, queryable projections

Primary owner for:

- source/revision identity;
- ProcessingRun and StageExecution facts;
- StageInput lineage;
- OutputSlot, OutputSet, StoredObject registry;
- baseline history;
- review/selection decisions;
- publication lifecycle;
- resolved component/config/schema references;
- queryable projections required for operations and review.

### 6.3 Queryable projections

Some large artifacts need relational projections for efficient diff/review/query.

For example, chunk/SourceUnit rows may be projected into the Catalog DB while the full immutable `chunks.json` remains canonical in Object Storage.

Rule:

> **Object artifact is the source of truth; relational projection is rebuildable.**

Projection rows must contain source artifact/output IDs and content hashes so divergence can be detected and rebuilt.

### 6.4 Knowledge Store / Neo4j

Primary owner only for semantic knowledge that has crossed the Publication boundary.

Neo4j is not the scratch/staging store for processing executions.

---

## 7. Lineage and reproducibility

The minimum lineage chain is:

```text
SourceRevision
   ↓
StageInput(s)
   ↓
StageExecution
   ↓
OutputSet
   ↓
OutputSlot
   ↓
BaselineDecision
   ↓
Publication
```

Each completed StageExecution should pin enough producer identity to explain/reproduce behavior:

```text
component_ref
code/version ref
configuration_hash
schema_version
ruleset_ref (when applicable)
model_ref / prompt_ref / trace_ref (when AI is used)
```

AI-specific metadata is an extension of the same execution model; it does not change the persistence architecture.

---

## 8. Consistency, failure, and lifecycle rules

### 8.1 No fake distributed transaction

Do not attempt one transaction across Object Store + relational DB + Neo4j.

Use explicit state transitions, idempotent operations, reconciliation, and verification.

Registering output:

```text
1. write immutable payload
2. compute/verify hash
3. register OutputSet + StoredObject rows
4. mark StageExecution SUCCEEDED
```

If DB registration fails, the unregistered object is an orphan candidate for reconciliation/GC.

### 8.2 Failed execution never destroys current baseline

A failed retry or reprocess preserves the previously selected baseline.

### 8.3 Upstream baseline change creates staleness, not silent mutation

When an upstream baseline changes, downstream executions produced from the old input remain historical facts.

The application may mark downstream derived state as stale and schedule/recommend reprocessing, but must not rewrite provenance.

### 8.4 Retry and intentional reprocess are different

Retry avoids duplicate side effects for the same operation.

Intentional reprocess creates a new StageExecution and usually a new OutputSet even when source bytes are unchanged.

---

## 9. Technology portability

The logical model must not require PostgreSQL-specific concepts.

POC may use:

```text
Catalog DB: SQLite
Object Store: local filesystem or S3-compatible adapter
Knowledge Store: Neo4j
Runtime: LangGraph
```

Scale-up may replace SQLite with PostgreSQL.

Portability means **domain/application contracts remain stable**. Physical schema, indexes, locking, isolation, JSON support, connection pooling, HA, and migration strategy may differ by database engine.

Recommended boundaries:

```text
CatalogRepository
ObjectStore
KnowledgePublisher
```

Runtime-specific checkpoints and UI state do not become the Catalog DB domain model.

---

## 10. Current ReqKB workflow mapping

The current workflow is an implementation mapping, not the database architecture itself.

| Generic concept | Current ReqKB example |
|---|---|
| SourceRevision | uploaded Excel/DOCX/PDF revision |
| StageExecution | classify / convert / parse / ontology |
| StageInput | raw source, selected normalized document, selected chunk set |
| OutputSlot | classification, normalized document, chunk set, enriched chunk set |
| OutputSet revision | one candidate produced by one execution |
| BaselineHistory | selected candidate for an OutputSlot |
| ReviewDecision | auto / AI-recommended / human-approved selection |
| Publication | publish selected enriched representation to Neo4j ReqKB |

If tomorrow the workflow removes conversion, adds validation stages, splits ontology into several nodes, or runs stages in parallel, the core persistence model should remain unchanged.

---

## 11. Architecture acceptance checklist

A database design is not ready for physical schema design until it can answer:

- [ ] What is the stable business identity of each versioned object?
- [ ] What creates a new revision?
- [ ] Is execution identity separated from artifact identity?
- [ ] Does every candidate belong to an OutputSlot/ArtifactSeries?
- [ ] Can a StageExecution consume multiple exact inputs?
- [ ] Are historical outputs immutable?
- [ ] Is current baseline an explicit governance state rather than `latest`?
- [ ] Is baseline history auditable and concurrency-safe?
- [ ] Can lineage be reconstructed from source revision to publication?
- [ ] Is the System of Record for every representation explicit?
- [ ] Are relational projections explicitly rebuildable from canonical artifacts?
- [ ] Can failed/retried executions occur without corrupting current baseline?
- [ ] Is publication separated from intermediate selection?
- [ ] Can workflow stages change without schema redesign?
- [ ] Can SQLite/PostgreSQL be swapped behind stable repository contracts while allowing engine-specific physical design?

Only after these decisions are stable should `02_storage_boundary.md`, logical ERD, and physical schema be finalized.
