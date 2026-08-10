# ADR-001 — Stable Publication Scope Across Source Revisions

**Status:** Accepted for logical design  
**Scope:** ReqKB publication identity and active-publication semantics  
**Related:** `../02_storage_boundary.md`, `../03_logical_data_model.md`

---

## Context

`OutputSlot` là artifact-series identity của một **SourceRevision**. Điều này đúng cho intermediate baseline governance: mỗi revision có candidate outputs và baseline riêng.

Nếu publication active state cũng scope theo `(KnowledgeSpace, OutputSlot)`, revision mới tạo OutputSlot mới. Khi đó:

```text
SOURCE-A
 ├── REV-003 → SLOT-003 → PUB-003 ACTIVE
 └── REV-004 → SLOT-004 → PUB-004 ACTIVE
```

Hai publication có thể cùng được coi là active vì chúng thuộc hai OutputSlot khác nhau, dù business intent thường là REV-004 thay thế REV-003 cho cùng stable source trong ReqKB.

Problem cần giải quyết:

> Publication governance phải có stable identity xuyên qua SourceRevision changes, trong khi baseline governance vẫn phải giữ revision-level isolation.

---

## Options considered

### Option A — PublicationHead theo OutputSlot

```text
KnowledgeSpace + OutputSlot → active Publication
```

**Ưu:** đơn giản, reuse trực tiếp artifact identity.

**Nhược:** OutputSlot thay đổi khi SourceRevision thay đổi; không có natural place để enforce revision replacement của cùng SourceAsset.

**Rejected because:** không bảo đảm một stable source chỉ có một current published revision trong cùng publication role.

### Option B — PublicationHead theo SourceRevision

```text
KnowledgeSpace + SourceRevision → active Publication
```

**Ưu:** rõ revision nào đang publish.

**Nhược:** vẫn không giải quyết replacement xuyên revision vì REV-003 và REV-004 là hai scope khác nhau.

**Rejected because:** publication-current semantics vẫn gắn vào revision identity thay vì stable business identity.

### Option C — Stable PublicationScope theo SourceAsset

```text
PublicationScope
= KnowledgeSpace
+ SourceAsset
+ publication_role
```

Publication history của nhiều SourceRevision cùng nằm trong một PublicationScope.

**Ưu:** active publication có stable scope xuyên revision changes; phù hợp source replacement và audit history.

**Nhược:** thêm một entity và cần định nghĩa publication role/scope uniqueness.

---

## Decision

Chọn **Option C — Stable PublicationScope**.

Logical model:

```text
KnowledgeSpace
   ↓
PublicationScope
   ├── SourceAsset
   ├── publication_role
   │
   ├── PUB-003 ← REV-003 output
   └── PUB-004 ← REV-004 output
                     ↑
              PublicationHead
```

`Publication` vẫn pin exact:

```text
OutputSlot
BaselineSelection
OutputSet
```

để giữ provenance về artifact đã publish.

`PublicationHead` trỏ active Publication của **PublicationScope**, không của OutputSlot.

---

## Rationale

Decision này tách hai semantics khác nhau:

```text
Baseline scope
= revision-level artifact selection

Publication scope
= stable business-source publication stream
```

Nhờ vậy:

- rerun cùng SourceRevision chỉ thay baseline candidate khi được chọn;
- SourceRevision mới tạo artifact/baseline history riêng;
- khi revision mới publish, publication cũ của cùng SourceAsset/publication role có thể supersede rõ ràng;
- main không cần redesign publication identity khi ingestion bắt đầu reprocess nhiều document revision.

---

## Consequences / Trade-offs

### Positive

- active publication semantics ổn định khi source revision thay đổi;
- query current published source đơn giản hơn;
- audit được publication history xuyên revision;
- tránh hai revision của cùng source vô tình cùng active trong cùng role.

### Cost

- thêm `PublicationScope` và `PublicationHead` relationship;
- cần uniqueness rule cho `(knowledge_space, source_asset, publication_role)` hoặc scope key tương đương;
- publication activation phải verify Publication thuộc đúng scope/source/workspace.

### Not solved here

ADR này không chọn cách đảm bảo Neo4j candidate invisibility trước activation. Strategy như publication tagging, shadow graph hoặc versioned semantic records cần ADR riêng.

ADR này cũng không định nghĩa whole-ReqKB `KnowledgeRelease`; snapshot toàn KB vẫn là concept khác.

---

## Migration / rollback implication

POC tạo PublicationScope ngay từ schema đầu tiên nên không có legacy migration.

Nếu sau này decision bị đảo ngược, Publication vẫn giữ exact OutputSlot/Baseline/OutputSet provenance, nên có thể derive lại alternative grouping. Tuy nhiên active-publication query semantics và uniqueness constraints sẽ cần migration; vì vậy scope identity được chốt ở logical design trước `04_physical_schema.md`.