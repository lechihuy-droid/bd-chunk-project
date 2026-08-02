# Harness Hub — Triết lý phát triển kỹ thuật

**Trạng thái:** Canonical  
**Phạm vi:** Toàn bộ Harness Hub  
**Vai trò:** Nguyên tắc định hướng cho Research, ADR, SDD, POC và implementation

---

## 1. Mục đích

Harness Hub không được xây dựng để cạnh tranh với LangGraph, MLflow hay bất kỳ AI framework nào.

Mục tiêu của Harness Hub là:

- Hiểu sâu các AI framework hiện đại.
- Học từ những thiết kế đã được kiểm chứng.
- Tích hợp những thành phần tốt nhất.
- Chỉ tự xây những năng lực tạo ra lợi thế cạnh tranh cho Enterprise AI Delivery Platform.

Dự án đồng thời là:

- Một nền tảng AI-native delivery.
- Một quá trình học tập có chủ đích.
- Một kho tri thức kiến trúc phục vụ lâu dài.

Mỗi module được xây dựng phải tạo ra đồng thời giá trị học tập, giá trị kỹ thuật và giá trị kinh doanh.

---

## 2. Phương châm phát triển

> **Học bằng cách tự xây. Chuẩn hóa bằng cách tích hợp. Chỉ sở hữu phần tạo ra khác biệt.**

> **Learn by Building. Standardize by Integrating. Differentiate by Owning.**

---

## 3. Nguyên tắc cốt lõi

### 3.1 Học bằng cách tự xây

Trước khi quyết định sử dụng một framework hay giải pháp có sẵn, nhóm phát triển có thể chủ động xây một phiên bản tối thiểu để hiểu bản chất vấn đề, trade-off và lý do thiết kế của các implementation trưởng thành.

Ví dụ:

- Prompt Registry tối thiểu.
- Runtime Adapter tối thiểu.
- Version Graph tối thiểu.
- Artifact Lineage tối thiểu.
- Evaluation Pipeline tối thiểu.

Các implementation này là **Learning Artifact**, không mặc định trở thành production implementation.

### 3.2 Benchmark trước khi build

Mỗi capability quan trọng phải được benchmark với các implementation đã trưởng thành trước khi đi vào production design.

Nguồn benchmark ưu tiên:

- LangGraph.
- MLflow.
- LangSmith.
- LiteLLM.
- OpenTelemetry.
- OpenAI Agents SDK.
- Các OSS mature khác.

Benchmark phải trả lời:

- Giải pháp đó xử lý vấn đề gì?
- Vì sao kiến trúc được thiết kế như vậy?
- Điểm mạnh và giới hạn là gì?
- Harness Hub có thực sự cần khác đi không?

### 3.3 Chuẩn hóa thông qua so sánh

Sau Minimal Implementation, phải so sánh với solution bên ngoài và đưa ra một trong ba quyết định:

- **Adopt:** dùng solution hiện có.
- **Extend:** giữ solution hiện có và mở rộng bằng capability của Harness Hub.
- **Replace:** tự xây production implementation khi có gap chiến lược hoặc lợi thế cạnh tranh rõ ràng.

### 3.4 Chỉ sở hữu phần tạo khác biệt

Harness Hub ưu tiên sở hữu:

- AI Delivery Workflow.
- Capability Graph.
- Enterprise Governance.
- Delivery Memory.
- Cross-workflow Knowledge.
- Human–AI Collaboration.
- Artifact Lineage và delivery baseline.

Harness Hub tránh tự xây lại commodity đã trưởng thành như:

- LLM runtime.
- Graph execution engine.
- Object storage.
- Source control.
- Generic observability stack.
- Generic vector database.
- Prompt Registry nếu MLflow đáp ứng đầy đủ.

### 3.5 Mọi dependency phải thay thế được

Harness Hub phụ thuộc vào stable interface thay vì vendor-specific object.

```text
WorkflowRuntimePort
  -> LangGraphRuntimeAdapter
```

Không để domain model phụ thuộc trực tiếp vào LangGraph SDK, MLflow internal schema hoặc một vendor-specific persistence model.

### 3.6 Kiến trúc đi theo business value

Thứ tự quyết định bắt buộc:

```text
Business Capability
  -> Platform Capability
    -> Architecture
      -> Technology
```

Không làm theo chiều ngược lại.

### 3.7 Một UX thống nhất, backend tách rời

Người dùng trải nghiệm một Harness Hub thống nhất. Các thành phần như LangGraph, MLflow, Git và object storage phải được che giấu sau integration boundary phù hợp.

---

## 4. Quy trình quyết định kỹ thuật

Mọi capability quan trọng đi theo vòng đời:

```text
Research
  -> Benchmark
    -> Build Minimal
      -> Compare
        -> ADR
          -> Standardize
            -> Production Implementation
```

Không bỏ qua Benchmark đối với capability mới có impact kiến trúc. Không thay đổi locked decision mà không có ADR.

---

## 5. Research Artifact

Trước Requirement hoặc Design, mỗi module quan trọng nên tạo một Research Artifact gồm:

- Problem Statement.
- Benchmark Targets.
- Key Findings.
- Architectural Observations.
- Gap Analysis.
- Decision.
- Expected Learning.

Research Artifact là tài sản tri thức lâu dài của platform.

---

## 6. Ma trận Build / Borrow / Buy

| Quyết định | Điều kiện |
|---|---|
| Buy | Commodity cần enterprise support hoặc compliance |
| Borrow | OSS mature, kiến trúc đã được kiểm chứng |
| Build Minimal | Mục tiêu học tập và hiểu kiến trúc |
| Build Production | Capability tạo lợi thế chiến lược cho Harness Hub |
| Replace | Solution hiện tại không còn đáp ứng hoặc tạo lock-in không chấp nhận được |

---

## 7. Tiêu chí thành công

Một module được xem là thành công khi tạo ra một hoặc nhiều giá trị sau:

- Hiểu biết mới về AI system architecture.
- Hiểu biết mới về enterprise architecture.
- Tri thức tái sử dụng.
- Capability mới cho Harness Hub.
- Năng suất phát triển cao hơn.
- Giá trị rõ ràng cho enterprise delivery.

Learning được xem là deliverable chính thức, nhưng không được dùng để biện minh cho production design yếu hoặc duplicate commodity vô thời hạn.

---

## 8. Quan hệ với SDD

Harness Hub sử dụng Specification-Driven Development làm phương pháp triển khai chính. Engineering Philosophy mở rộng SDD bằng giai đoạn Research và Benchmark trước Requirement.

```text
Research
  -> Benchmark
    -> ADR
      -> Requirement
        -> Specification
          -> Implementation
            -> Evaluation
              -> Knowledge Capture
```

- SDD quản lý kiến trúc và specification ở cấp platform hoặc subsystem.
- SpecKit-style flow có thể dùng ở cấp module hoặc vertical slice để chuyển specification thành plan, tasks, code và test.
- Git lưu lịch sử version của tài liệu canonical; không tạo nhiều file `final`, `v1.1`, `updated` song song nếu không cần thiết.

---

## 9. Cam kết

Harness Hub không theo đuổi mục tiêu tự xây mọi thứ.

Chúng ta theo đuổi mục tiêu:

- Hiểu sâu.
- Học từ implementation tốt nhất.
- Chuẩn hóa bằng giải pháp đã được chứng minh.
- Giữ quyền thay thế dependency.
- Chỉ sở hữu những năng lực tạo giá trị enterprise lâu dài.
