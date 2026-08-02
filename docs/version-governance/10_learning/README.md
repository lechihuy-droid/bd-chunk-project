# Version Governance — Fast Learning Package

## Trạng thái

**Hoàn thành.** Bộ Learning Package đã đủ đầu vào để chuyển sang SDD.

## Mục tiêu

Bộ tài liệu này giúp người đọc nắm đủ khái niệm và quyết định nền tảng để chuyển nhanh sang SDD, không nhằm trở thành một bộ nghiên cứu dài hạn.

Thời lượng mục tiêu: khoảng 3 giờ.

## Thứ tự đọc

1. `01_core_concepts.md` — hiểu domain và các khái niệm cốt lõi.
2. `02_reference_implementations.md` — hiểu LangGraph, MLflow, Git, object storage và Harness Hub sở hữu phần nào.
3. `03_build_decisions.md` — chốt phần nào Adopt, Extend hoặc Build; xác định system of record, invariants, risks và input trực tiếp cho SDD.
4. `04_poc_boundary.md` — khóa vertical slice, Definition of Done, quality guardrails và các capability không làm trong POC.

## Learning exit criteria

Có thể chuyển sang `docs/50_sdd/version-governance/` khi người đọc trả lời được:

- Vì sao Git không đủ để quản lý provenance của AI workflow?
- Khác biệt giữa Workflow Release, Run và Frozen Run Manifest là gì?
- Khác biệt giữa Artifact, Artifact Revision và Approved Baseline là gì?
- LangGraph, MLflow, Git và Harness Hub sở hữu loại trạng thái nào?
- Thành phần nào được Adopt, thành phần nào được Extend và thành phần nào Harness Hub phải Build?
- Vì sao dependency phải được tích hợp qua adapter?
- Vertical slice POC tối thiểu gồm những gì?
- POC được coi là hoàn thành theo các tiêu chí nào?
- Những capability nào bị loại khỏi POC và cần ADR để bổ sung?

## Quan hệ với tài liệu khác

```text
Engineering Philosophy
    ↓
Fast Learning Package
    ↓
POC Boundary
    ↓
Canonical Architecture
    ↓
SDD
    ↓
Implementation
```

Learning package không thay thế tài liệu kiến trúc canonical tại `docs/40_architecture/` và không được lặp lại chi tiết implementation.

## Bước tiếp theo

Tạo tài liệu:

```text
docs/50_sdd/version-governance/01_requirements.md
```

Requirement phải bám theo phạm vi đã khóa trong `04_poc_boundary.md` và không tự thêm capability ngoài scope.