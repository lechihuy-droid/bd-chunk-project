# Database Architecture Review Methodology

**Status:** POC review baseline  
**Scope:** Database architecture, version governance, physical schema và migration safety  
**Purpose:** Tạo một review method lặp lại được, vẫn dùng được khi ReqKB workflow thay đổi.

---

## 1. Review philosophy

Database review không bắt đầu từ SQL syntax hoặc danh sách workflow node hiện tại.

Review theo thứ tự:

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

Một schema nhanh nhưng model sai lifecycle vẫn là schema sai.

---

## 2. Research basis

Methodology này tổng hợp các góc review từ nhiều nguồn độc lập. Mỗi nguồn dùng cho một layer khác nhau, không coi bất kỳ repo/skill nào là universal checklist.

### 2.1 Supabase Agent Skills — PostgreSQL implementation review

Nguồn:

- https://github.com/supabase/agent-skills
- skill `supabase-postgres-best-practices`

Skill cover schema design, query performance, connection management, concurrency/locking, RLS/security, access patterns và monitoring.

Dùng chủ yếu cho **physical PostgreSQL review**, sau khi domain model đã đúng.

### 2.2 GitHub Awesome Copilot — independent PostgreSQL review

Nguồn:

- https://github.com/github/awesome-copilot
- skill `postgresql-code-review`

Skill tập trung PostgreSQL-specific schema quality, JSONB, custom types, constraints, indexes, functions, RLS, privileges và anti-patterns.

Dùng như **independent second reviewer** để challenge physical design.

### 2.3 wshobson/agents — logical database và architecture review

Nguồn:

- https://github.com/wshobson/agents
- `postgresql-table-design`
- `architecture-patterns`
- `event-store-design`
- `projection-patterns`

Repo tách các skill architecture/database theo single responsibility và composable boundaries.

Dùng chủ yếu cho **logical modeling, identity, projection, architecture boundary và System-of-Record reasoning**.

### 2.4 Atlas — schema-as-code và migration verification

Nguồn:

- https://github.com/ariga/atlas

Atlas hỗ trợ declarative/versioned schema workflow, inspect/diff, migration planning/linting, testing và drift detection trên PostgreSQL, SQLite và nhiều engine khác.

Dùng cho **machine-verifiable schema change review** khi physical schema đã tồn tại.

### 2.5 Bytebase — database change governance reference

Nguồn:

- https://github.com/bytebase/bytebase

Bytebase cung cấp database CI/CD, schema change review, GitOps integration, migration management, SQL Review, approval workflow và audit-oriented database lifecycle.

Dùng như **reference architecture cho database change/version governance**, không copy làm ReqKB persistence model.

---

## 3. Five review gates

Mọi database design change quan trọng phải đi qua 5 gate.

### Gate A — Domain & identity

Câu hỏi: **Ta có đang version đúng business object không?**

Review:

- stable business identity vs revision identity;
- execution identity vs artifact identity;
- event nào tạo revision mới;
- schema có phụ thuộc workflow node name không;
- một generic `version` có đang che nhiều version semantics không;
- candidate revision có thuộc stable ArtifactSeries/OutputSlot không.

P0 điển hình:

```text
Run ID dùng làm artifact identity
Latest row bị coi là current truth
Mỗi workflow node tạo một table riêng
Không có stable identity cho object được baseline
```

Primary lens: logical modeling / architecture.

---

### Gate B — Ownership, lineage & version governance

Câu hỏi: **Hệ thống có chứng minh được cái gì là canonical và tại sao không?**

Review:

- System of Record của từng representation;
- immutable target vs mutable/current pointer;
- baseline selection history;
- publication tách khỏi execution;
- provenance từ input revision đến output revision;
- review/approval evidence;
- exact upstream input pinning;
- stale/downstream dependency handling;
- concurrent baseline update semantics.

Rule bắt buộc:

```text
latest != baseline
success != approval
baseline != publication
```

P0 điển hình:

```text
/final folder quyết định truth
baseline bị overwrite không có history
AI recommendation mặc định bằng approval
Object artifact và DB projection đều claim canonical
baseline dùng last-write-wins
```

Primary lens: version governance; Bytebase dùng làm change-governance reference.

---

### Gate C — Logical relational model

Câu hỏi: **Model có enforce valid state mà không chỉ dựa vào application convention không?**

Review:

- PK/FK boundaries;
- cardinality;
- optional/mandatory relationship;
- normalization vs intentional projection/denormalization;
- UNIQUE/CHECK constraints;
- state transition invariants;
- multi-input/DAG support khi cần;
- delete/retention semantics;
- queryable projection rebuildability.

Principle:

> Invariant nào tuyệt đối không được vi phạm thì ưu tiên enforce bằng database constraint, không chỉ bằng application code.

Ví dụ:

```text
một OutputSet thuộc đúng một StageExecution
một StoredObject thuộc đúng một OutputSet
một Baseline revision chọn một OutputSet cho một OutputSlot
mỗi baseline scope chỉ có tối đa một current baseline
```

---

### Gate D — Physical DB quality

Câu hỏi: **Chosen engine có được dùng an toàn và hiệu quả không?**

Với PostgreSQL review:

- data types;
- PK strategy;
- FK indexes;
- compound/partial indexes;
- JSONB chỉ dùng khi query semantics phù hợp;
- timestamp/time-zone types;
- CHECK/UNIQUE constraints;
- transaction boundaries;
- locking/concurrency;
- role/privilege/RLS;
- pooling và scale assumptions.

Với SQLite POC:

- writer concurrency assumption;
- transaction behavior;
- foreign keys enabled;
- WAL/locking decision;
- indexes theo real query path;
- feature nào sẽ cần redesign khi move sang PostgreSQL.

Dùng `supabase-postgres-best-practices` làm primary implementation checklist và GitHub `postgresql-code-review` làm second pass cho PostgreSQL.

---

### Gate E — Migration, drift & operability

Câu hỏi: **Schema có evolve an toàn sau khi đã có data không?**

Review:

- schema-as-code source;
- migration history;
- destructive changes;
- NOT NULL/default changes trên existing data;
- table rewrite/lock risk;
- backward compatibility khi deploy;
- rollback/roll-forward strategy;
- expected vs actual schema drift;
- data backfill strategy;
- migration tests.

Recommended machine verification khi implementation bắt đầu:

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

Bytebase có thể nghiên cứu thêm khi cần approval/change-management layer lớn hơn.

---

## 4. Review severity

### P0 — Architecture blocker

Phải sửa trước physical schema implementation.

Ví dụ:

- sai business/version identity;
- System of Record mơ hồ;
- thiếu baseline/concurrency semantics;
- workflow-specific schema dễ gãy khi flow đổi;
- không reconstruct được provenance;
- mutate immutable history.

### P1 — Design risk

Phải sửa trước pilot/production hoặc trước capability liên quan.

Ví dụ:

- thiếu constraint/index strategy;
- stale propagation chưa rõ;
- migration strategy yếu;
- JSON/denormalization quá mức;
- transaction boundary chưa tốt.

### P2 — Optimization / maintainability

Có thể defer với backlog rõ ràng.

Ví dụ:

- naming consistency;
- secondary indexes;
- convenience views;
- observability improvements.

---

## 5. Multi-reviewer process

Không nên để một reviewer/agent review tất cả trong một pass.

```text
Pass 1 — Architecture Reviewer
identity / lifecycle / ownership / boundaries

Pass 2 — Version Governance Reviewer
revision / baseline / audit / concurrency / publication

Pass 3 — Database Model Reviewer
ERD / PK-FK / constraints / cardinality / query model

Pass 4 — Engine Reviewer
PostgreSQL hoặc SQLite physical design

Pass 5 — Migration Reviewer
schema diff / migration safety / drift
```

Nếu reviewer disagree, resolve theo requirement/invariant rõ ràng, không majority voting.

---

## 6. Required review inputs theo maturity

### Methodology stage

Cần:

- data lifecycle;
- business identities;
- version rules;
- ownership boundaries;
- expected query/use cases.

Chưa review indexes.

### Logical model stage

Cần:

- entity definitions;
- ERD;
- cardinality;
- lifecycle/state transitions;
- baseline/publication rules.

### Physical schema stage

Cần:

- DDL;
- representative queries;
- expected volumes;
- concurrency model;
- selected DB engine.

### Migration stage

Cần:

- current schema;
- desired schema;
- existing data characteristics;
- deployment compatibility constraints.

---

## 7. Standard review output

Mỗi review phải có cùng cấu trúc:

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
- điểm đã đúng, không reopen nếu không có evidence mới

Open architecture decisions
- điểm cần explicit choice

Next gate
- artifact nào phải có trước review tiếp theo
```

Không chấp nhận review chỉ nói “looks good” hoặc list generic best practices không gắn với design hiện tại.

---

## 8. ReqKB-specific architecture invariants

Các invariant này phải giữ dù workflow thay đổi:

1. Một SourceAsset có nhiều immutable SourceRevision.
2. Processing execution tách khỏi output/artifact identity.
3. Mỗi candidate OutputSet thuộc một stable OutputSlot/ArtifactSeries.
4. StageExecution có thể consume nhiều exact versioned inputs.
5. Object Store sở hữu immutable payload; Catalog DB sở hữu identity/governance/lineage.
6. Relational content projection phải explicit là rebuildable từ canonical artifact.
7. Baseline là append-only governance decision; `latest` không bao giờ implicit baseline.
8. Concurrent baseline change không được silent last-write-wins.
9. Publication vào ReqKB tách khỏi intermediate baseline selection.
10. Workflow node thay đổi không được buộc core schema redesign.

Các invariant này là review standard chính cho `01_design_methodology.md`, `02_storage_boundary.md`, logical ERD và physical schema.

---

## 9. Recommended review stack cho project

```text
Logical architecture review
→ database architect / architecture + table-design skill

PostgreSQL physical review
→ supabase-postgres-best-practices
→ github/awesome-copilot postgresql-code-review (second pass)

Schema/migration verification
→ Atlas

Database change governance research
→ Bytebase patterns
```

Tool hỗ trợ architecture judgment; không tự quyết định domain identity hoặc System-of-Record boundary.
