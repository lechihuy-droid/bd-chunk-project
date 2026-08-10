# ADR-002 — StageInput Physical Reference Strategy

**Status:** Accepted for POC physical schema  
**Scope:** Relational representation của StageExecution input lineage  
**Related:** `../03_logical_data_model.md`, `../04_physical_schema.md`

---

## Context

Logical model yêu cầu một `StageExecution` consume `0..N` exact versioned inputs và POC hiện chỉ cần hai target type:

```text
SourceRevision
OutputSet
```

Schema phải đồng thời:

- support fan-in/DAG;
- giữ real FK integrity;
- pin exact baseline selection khi input được resolve từ baseline;
- tránh generic registry/abstraction không cần thiết cho POC.

Problem:

> Physical schema nên biểu diễn target polymorphism thế nào mà không biến `StageInput` thành free-form pointer hoặc over-engineer POC?

---

## Options considered

### Option A — `ref_type + ref_id`

```text
input_ref_type
input_ref_id
```

**Ưu:** schema rất nhỏ, thêm type mới dễ.

**Nhược:** DB không thể FK trực tiếp tới target table; orphan/cross-workspace reference dễ xảy ra.

**Rejected because:** referential integrity trở thành application convention, trái invariant Gate C.

### Option B — Resource supertype registry

```text
resource
  ├── source_revision
  └── output_set

stage_input.resource_id → resource
```

**Ưu:** một FK duy nhất; mở rộng nhiều resource type tốt.

**Nhược:** thêm identity layer, synchronization và join chỉ để support hai target type hiện tại.

**Rejected for POC because:** complexity chưa có requirement chứng minh; có nguy cơ biến Catalog DB thành generic resource platform.

### Option C — subtype tables

```text
stage_input
source_revision_input
output_set_input
```

**Ưu:** FK integrity rất rõ; type-specific fields sạch.

**Nhược:** nhiều table/join cho một concept nhỏ; write/read path phức tạp hơn POC cần.

**Rejected for POC because:** ceremony cao trong khi target set chỉ có hai type.

### Option D — dual nullable FK columns + XOR CHECK

```text
source_revision_id NULL
output_set_id      NULL

CHECK(exactly one is non-null)
```

**Ưu:** FK thật tới cả hai target, query đơn giản, không cần registry phụ.

**Nhược:** thêm input target type mới sẽ cần schema migration.

---

## Decision

Chọn **Option D — dual nullable FK columns + XOR CHECK** cho POC/main baseline hiện tại.

```text
StageInput
  ├── source_revision_id ?
  └── output_set_id ?

exactly one target required
```

Nếu:

```text
binding_mode = BASELINE
```

thì bắt buộc:

```text
output_set_id IS NOT NULL
source_baseline_selection_id IS NOT NULL
```

và composite FK phải chứng minh baseline selection đó thực sự chọn chính `output_set_id`.

---

## Rationale

Decision này tối ưu cho current requirement:

```text
integrity > theoretical extensibility
```

Nó giữ được:

- exact lineage;
- FK validation;
- simple repository/query code;
- SQLite implementation nhanh;
- PostgreSQL migration trực tiếp.

Không tạo generic abstraction trước khi có target type thứ ba thực sự cần lifecycle tương đương.

---

## Consequences / Trade-offs

### Positive

- orphan StageInput bị DB reject;
- dễ trace execution → source/output;
- baseline-bound input có thể enforce exact output bằng composite FK;
- không cần polymorphic string lookup hoặc resource registry.

### Cost

- mỗi target type mới cần schema migration;
- nhiều nullable FK column nếu target set tăng mạnh.

### Scale trigger

Revisit ADR khi một trong các điều kiện xảy ra:

```text
>= 3-4 durable input resource types
hoặc
plugins cần register arbitrary versioned resources
hoặc
resource identity được reuse rộng ngoài ingestion
```

Khi đó so sánh lại Resource Supertype Registry vs subtype tables dựa trên real query/write patterns.

---

## Migration / rollback implication

SQLite POC tạo strategy này ngay từ initial schema nên không cần data migration.

Nếu main chuyển sang resource supertype sau này:

1. tạo `resource` registry;
2. backfill SourceRevision/OutputSet identities;
3. add `resource_id` vào StageInput;
4. dual-write/verify;
5. migrate reads;
6. drop dual target columns chỉ sau compatibility window.

Do StageInput hiện vẫn pin target identity rõ ràng, backfill là deterministic.
