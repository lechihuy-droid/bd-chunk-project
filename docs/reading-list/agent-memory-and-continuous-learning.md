# Reading List — Agent Memory and Continuous Learning

> Mục tiêu: xây nền tảng đọc có hệ thống cho kiến trúc agent có khả năng học từ execution trace và reviewer feedback mà không cần fine-tune LLM nền.
>
> Trọng tâm áp dụng: pipeline RD → BD, Harness đa model, workflow orchestration, execution trace, case-based memory, policy improvement, governance và versioning.

## 1. Core reading

### 1.1 Memento: Fine-tuning LLM Agents without Fine-tuning LLMs

- **Vai trò:** Tài liệu trung tâm.
- **Vấn đề giải quyết:** Làm thế nào để agent thích nghi liên tục mà không cập nhật trọng số của LLM nền.
- **Ý tưởng chính:**
  - Mô hình hóa agent dưới dạng Memory-augmented Markov Decision Process.
  - Lưu kinh nghiệm thực thi trong episodic memory.
  - Cải thiện policy thông qua retrieval tốt hơn thay vì fine-tune model.
  - Cập nhật memory bằng cơ chế rewrite dựa trên feedback môi trường.
  - Hỗ trợ cả parametric và non-parametric case-based retrieval.
- **Điểm cần đọc sâu:**
  - Định nghĩa state, action, reward và memory trong M-MDP.
  - Neural case-selection policy.
  - Memory rewriting mechanism.
  - So sánh parametric và non-parametric CBR.
  - Ablation về tác động của case-based retrieval.
  - Hiệu quả trên GAIA, DeepResearcher, SimpleQA, HLE và các bài toán OOD.
- **Liên hệ với BD Chunk:** Reviewer feedback không chỉ sửa output hiện tại mà phải trở thành reusable experience cho các run sau.
- **ArXiv:** https://arxiv.org/abs/2508.16153
- **PDF:** https://arxiv.org/pdf/2508.16153
- **Code được nêu trong paper:** https://github.com/Agent-on-the-Fly/Memento

## 2. Supporting concepts

### 2.1 Case-Based Reasoning for Agent Memory

- **Mục tiêu đọc:** Hiểu cách biểu diễn, chọn, tái sử dụng, đánh giá và chỉnh sửa một case.
- **Câu hỏi cần trả lời:**
  - Một case trong RD → BD gồm những trường nào?
  - Context similarity được tính thế nào?
  - Khi nào merge, supersede, expire hoặc delete một case?
  - Làm sao tránh một lỗi cục bộ bị khái quát hóa sai thành policy toàn cục?
- **Artifact mong muốn:** `ExperienceCase` schema và lifecycle state machine.

### 2.2 Episodic Memory vs Semantic Memory

- **Episodic memory:** Run cụ thể, input cụ thể, action cụ thể, feedback và outcome cụ thể.
- **Semantic memory:** Quy tắc đã được khái quát hóa, design convention, constraint và reusable pattern.
- **Áp dụng đề xuất:**
  - Execution trace đi vào episodic store.
  - Case consolidation sinh semantic rule candidate.
  - Rule candidate chỉ được publish sau evaluation hoặc human approval.
- **Artifact mong muốn:** Quy tắc chuyển đổi từ execution episode sang approved reusable knowledge.

### 2.3 Reflection and Self-Improvement Workflows

- **Mục tiêu đọc:** Phân biệt reflection tĩnh với learning thực sự.
- **Reflection tĩnh:** Prompt yêu cầu model tự phê bình trong cùng một run.
- **Continual learning:** Feedback được lưu, đánh giá, version và tác động đến decision của các run sau.
- **Rủi ro:** Reflection không có external evidence có thể củng cố hallucination.
- **Artifact mong muốn:** Feedback taxonomy và evidence requirements.

### 2.4 Retrieval as Policy Improvement

- **Luận điểm cần kiểm chứng:** Với agent không fine-tune, chất lượng policy phụ thuộc mạnh vào việc truy xuất đúng kinh nghiệm tại đúng state.
- **Thành phần cần thiết:**
  - Case eligibility filter.
  - Hybrid retrieval.
  - Reranking.
  - Conflict detection.
  - Applicability validation.
  - Outcome-aware scoring.
- **Artifact mong muốn:** Retrieval policy spec cho từng workflow node.

## 3. Architecture reading track for BD Chunk

### 3.1 Execution Trace Architecture

Nghiên cứu cách ghi lại đầy đủ:

```text
Run
└── Workflow version
    └── Node execution
        ├── Input references
        ├── Retrieved context
        ├── Prompt version
        ├── Model/provider/version
        ├── Tool calls
        ├── Output artifact
        ├── Reviewer feedback
        ├── Evaluation result
        └── Final disposition
```

**Yêu cầu kiến trúc:** Trace phải đủ để replay, audit, compare và tạo training/evaluation case.

### 3.2 Memory Rewrite Pipeline

```text
Execution trace
    ↓
Feedback normalization
    ↓
Case extraction
    ↓
Duplicate/conflict detection
    ↓
Generalization candidate
    ↓
Offline evaluation
    ↓
Human approval or policy gate
    ↓
Publish memory version
```

**Điểm cần kiểm chứng:** Không cho phép LLM tự rewrite production memory trực tiếp mà không có validation và rollback path.

### 3.3 Memory Scope Model

Cần phân biệt tối thiểu:

- Platform memory
- Workspace memory
- Project memory
- Workflow memory
- Agent-private memory
- Run-local scratch memory

**Câu hỏi thiết kế:** Scope nào được phép kế thừa, override, chia sẻ hoặc cô lập?

### 3.4 Memory Governance

Các thuộc tính bắt buộc cho mỗi memory item:

- Stable ID
- Memory type
- Scope và owner
- Source trace
- Evidence
- Created by
- Approval status
- Valid-from / expiry
- Version
- Supersedes / conflicts-with
- Quality score
- Usage statistics
- Rollback reference

### 3.5 Evaluation Strategy

Không đánh giá memory chỉ bằng retrieval similarity. Cần đo:

- Task success rate
- Design defect rate
- Reviewer correction rate
- Rework effort
- Unsupported-generation rate
- Retrieval precision
- Harmful-memory activation rate
- Cross-project leakage rate
- Regression after memory update

## 4. Reading order

### Phase A — Understand the learning model

1. Đọc abstract, introduction và method của Memento.
2. Vẽ lại M-MDP theo ngôn ngữ của BD Chunk.
3. Xác định state, action, feedback và reward cho một workflow RD → BD.

### Phase B — Understand memory mechanics

1. Đọc phần case selection.
2. Đọc memory rewriting.
3. So sánh parametric với non-parametric CBR.
4. Viết `ExperienceCase` schema bản đầu tiên.

### Phase C — Validate claims

1. Đọc benchmark setup và ablation.
2. Kiểm tra baseline có công bằng hay không.
3. Phân tích mức đóng góp riêng của retrieval, rewrite và model backbone.
4. Xác định kết quả nào có thể chuyển sang enterprise design workflow, kết quả nào không.

### Phase D — Convert into architecture decisions

1. Thiết kế execution trace store.
2. Thiết kế episodic memory store.
3. Thiết kế semantic memory publication flow.
4. Thiết kế evaluation gate và rollback.
5. Chốt ADR về việc không cho online memory update tác động trực tiếp vào production policy.

## 5. Critical review checklist

Khi đọc Memento, cần trả lời rõ:

- “Without fine-tuning LLMs” có bao gồm việc train neural case-selection policy hay không?
- Chi phí train và vận hành retriever là bao nhiêu?
- Reward/feedback trong benchmark đến từ đâu và có sẵn trong enterprise workflow hay không?
- Memory rewrite có tạo ra lỗi tích lũy hoặc catastrophic memory pollution không?
- Kết quả có phụ thuộc vào benchmark có ground-truth rõ ràng hơn tài liệu BD thực tế không?
- Case retrieval có leakage giữa task hoặc benchmark không?
- OOD improvement có ổn định qua nhiều domain hay chỉ trên các tập được báo cáo?
- Có cơ chế rollback, audit, isolation và approval phù hợp môi trường enterprise không?

## 6. Proposed BD Chunk implementation mapping

| Memento concept | BD Chunk component | Trạng thái đề xuất |
|---|---|---|
| Episodic memory | Execution trace + reviewer feedback store | Nên xây sớm |
| Case selection policy | Context/case retriever + reranker | POC sau trace store |
| Memory rewriting | Offline case consolidation job | Human-gated |
| Policy improvement | Versioned retrieval policy | Evaluation-gated |
| Parametric CBR | Learned reranker/retriever | Giai đoạn sau |
| Non-parametric CBR | Vector + metadata + graph retrieval | Phù hợp POC |
| Environmental feedback | Reviewer decision + automated checks | Bắt buộc chuẩn hóa |

## 7. Recommended POC

### POC scope

Chỉ chọn một lỗi lặp lại trong tài liệu BD, ví dụ:

> API design thường thiếu timeout, retry, idempotency hoặc error mapping.

### Flow

```text
Generate API BD
    ↓
Reviewer corrects output
    ↓
Store trace and structured feedback
    ↓
Extract approved experience case
    ↓
Retrieve case in a similar next task
    ↓
Compare output with and without memory
```

### Success criteria

- Giảm reviewer correction rate.
- Không tăng unsupported requirements.
- Case được truy xuất đúng ngữ cảnh.
- Có thể trace ngược từ output đến memory item và source feedback.
- Có thể rollback memory version.

## 8. Repository follow-up artifacts

Các tài liệu nên tạo tiếp sau reading list này:

1. `Experience_Case_Schema.md`
2. `Agent_Memory_Architecture.md`
3. `Memory_Governance_and_Versioning.md`
4. `Feedback_Taxonomy.md`
5. `Memory_Evaluation_Framework.md`
6. `ADR_Online_vs_Offline_Memory_Update.md`
7. `POC_Reviewer_Feedback_Learning.md`

## 9. Current assessment

Memento phù hợp mạnh với định hướng BD Chunk vì nó đưa ra một cơ chế thực tế để agent học từ run trước mà không khóa hệ thống vào một LLM provider cụ thể. Tuy nhiên, paper không tự động giải quyết các yêu cầu production như governance, isolation, provenance, approval, rollback và regression control.

Do đó, hướng áp dụng phù hợp không phải là sao chép nguyên framework, mà là:

```text
Memento learning model
+
Enterprise execution trace
+
Versioned memory governance
+
Human/evaluation gates
+
Workflow-scoped retrieval policy
```

**Kết luận kiến trúc:** Bắt đầu bằng execution trace và structured reviewer feedback. Chưa nên bắt đầu bằng learned retriever hoặc online RL. Khi dữ liệu trace đủ sạch và có evaluation set ổn định, mới nâng cấp từ non-parametric CBR sang parametric case-selection policy.
