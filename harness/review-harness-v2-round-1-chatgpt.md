# Harness Hub V2 — UI/UX Review Round 1

**Reviewer:** ChatGPT  
**Date:** 2026-07-22  
**Scope:** Multi-LLM chat workspace, Skill/Workflow activation, context management, cost/performance prioritization

---

## 1. Executive summary

Harness Hub hiện đã có nền tảng navigation tốt với các khu vực Chat, Sessions, Workflows, Runs, Agents, Skills, Approvals, Usage và Settings. Tuy nhiên, phần trung tâm vẫn đang hoạt động gần với một giao diện “mở nhiều cửa sổ chat” hơn là một **multi-LLM orchestration workbench**.

Mục tiêu thiết kế cho V2 nên là:

> Người dùng có thể chọn model, kích hoạt Skill/Workflow, quản lý context, theo dõi run, xử lý approval và kiểm soát cost mà không phải rời khỏi màn hình chat.

Ba vấn đề cần giải quyết trước:

1. Chưa phân biệt rõ **Provider – Model – Agent – Profile**.
2. Chat chưa thực sự là control plane để điều phối Skill, Workflow và nhiều model.
3. Context management chưa đủ minh bạch để bảo đảm chất lượng, tiết kiệm token và debug lỗi.

Tổ hợp có tỷ lệ **utility/cost/performance tốt nhất** cho vòng phát triển tiếp theo là:

> Global composer + Skill activation + Shared/local context + Token meter + Structured compression + Workflow card.

---

## 2. Đánh giá UI hiện tại

### Điểm tốt

- Sidebar đã phản ánh đúng các domain chính của một Harness: Chat, Workflow, Run, Agent, Skill, Approval và Usage.
- Multi-pane layout phù hợp với mục tiêu multi-model.
- Provider status đã bắt đầu được hiển thị trên header.
- Màu nền tối phù hợp với developer tool và tác vụ dài.
- Có định hướng quản trị, không chỉ là chat UI thông thường.

### Điểm cần cải thiện

- `Claude`, `Codex`, `NVIDIA free` đang được đặt gần như cùng cấp dù có thể là provider, model, runtime hoặc profile khác nhau.
- `Claude` và `mặc định` bị lặp ở nhiều tầng header nhưng không cung cấp thêm thông tin thực tế.
- `Gửi tất cả` nằm xa composer, chưa cho biết prompt sẽ đi tới model nào và dùng context nào.
- Trạng thái như `NVIDIA không khả dụng` chưa giải thích nguyên nhân hoặc action tiếp theo.
- Empty state quá trống, không hướng dẫn người dùng bắt đầu.
- Màu cam được dùng cho quá nhiều thành phần nên hierarchy chưa rõ.
- Chưa có indication rõ ràng về token, latency, cost, active skill và context scope.
- `READ-ONLY` chưa rõ đang áp dụng cho conversation, tool permission hay artifact.
- Action nguy hiểm như `Xoá` đang nằm quá trực tiếp.

---

## 3. Nguyên tắc kiến trúc UI

UI nên phân tách rõ ba lớp điều khiển.

### 3.1. Conversation level

Điều khiển toàn phiên:

- Mode: Single, Compare, Relay, Auto-route.
- Shared context hoặc Isolated context.
- Danh sách model đích.
- Auto-compress.
- Tổng token, cost và latency.
- Stop all.

### 3.2. Pane level

Điều khiển từng model:

- Provider.
- Model.
- Agent.
- Profile.
- Active Skills.
- Local context.
- Tool permission.
- Retry, reset, maximize, duplicate và close.

### 3.3. Message/Run level

Điều khiển từng response hoặc workflow run:

- Copy, retry, continue, edit/resend.
- Retry bằng model khác.
- Pin, branch, export.
- Tool trace.
- Approval.
- Artifact.
- Token, cost, latency và finish reason.

---

## 4. Ma trận ưu tiên theo utility, cost và performance

Thang điểm:

- **Utility:** tác động đến khả năng sử dụng thực tế.
- **Implementation cost:** độ phức tạp frontend, backend và state management.
- **Runtime cost:** token, API calls và latency.
- **ROI:** giá trị nhận được so với tổng chi phí.

| Hạng mục | Utility | Implementation cost | Runtime cost | ROI | Priority |
|---|---:|---:|---:|---:|---|
| Chuẩn hóa Provider–Model–Agent–Profile | 5/5 | 2/5 | 1/5 | Rất cao | P0 |
| Global composer và target selector | 5/5 | 2/5 | 1/5 | Rất cao | P0 |
| Shared context / pane-local context | 5/5 | 3/5 | 1/5 | Rất cao | P0 |
| Kích hoạt Skill từ chat | 5/5 | 2/5 | 1/5 | Rất cao | P0 |
| Token meter và context usage | 5/5 | 2/5 | 1/5 | Rất cao | P0 |
| Pin context và structured summary | 5/5 | 3/5 | 2/5 | Rất cao | P0 |
| Stop, retry, fallback và error details | 5/5 | 2/5 | 1/5 | Rất cao | P0 |
| Session persistence | 5/5 | 3/5 | 1/5 | Rất cao | P0 |
| Workflow card trong chat | 5/5 | 3/5 | 1/5 | Cao | P1 |
| Context Inspector | 5/5 | 3/5 | 1/5 | Cao | P1 |
| Tool trace và inline approval | 5/5 | 4/5 | 1/5 | Cao | P1 |
| Artifact panel | 4/5 | 3/5 | 1/5 | Cao | P1 |
| Compare mode | 4/5 | 3/5 | 4/5 | Trung bình–cao | P1 |
| Semantic retrieval từ history | 4/5 | 4/5 | 2/5 | Trung bình | P2 |
| Judge và merge answer | 3/5 | 3/5 | 5/5 | Trung bình | P2 |
| Auto-routing model | 4/5 | 5/5 | 2/5 | Trung bình | P2 |
| Hierarchical context checkpoint | 4/5 | 5/5 | 2/5 | Trung bình | P2 |
| RBAC, audit và budget policy | 4/5 | 5/5 | 1/5 | Cao với enterprise | P2 |

---

## 5. P0 — giá trị cao, cost thấp hoặc trung bình

### 5.1. Chuẩn hóa Provider–Model–Agent–Profile

Cần thống nhất hierarchy:

```text
Provider
  └ Model
      └ Agent
          └ Profile
```

Header từng pane nên có dạng:

```text
Anthropic / Claude Sonnet
Agent: Reviewer · Profile: Default
Tools: Read-only
```

Không nên chỉ hiển thị `Claude · mặc định`, vì không đủ để xác định endpoint, model thực tế hoặc permission.

### 5.2. Global composer

Composer phải trở thành control center của chat:

```text
[+ File] [@ Agent] [# Skill] [/ Workflow]
[Context: Shared ▼] [Targets: Claude, Codex ▼]
```

Người dùng phải thấy rõ:

- Prompt gửi cho model nào.
- Dùng shared context hay local context.
- Skill/Workflow nào đang active.
- Chạy một model hay nhiều model.
- Có chia sẻ lịch sử giữa các pane hay không.

`Gửi tất cả` nên được đưa sát composer và đổi thành target selector rõ ràng.

### 5.3. Kích hoạt Skill trực tiếp từ chat

Hỗ trợ ba cơ chế:

```text
/skill code-review
#code-review
@codex #code-review kiểm tra file này
```

Sau khi chọn, hiển thị dưới dạng chip:

```text
[# Code Review ×]
[Scope: Current message ▼]
[Target: Codex ▼]
```

Scope tối thiểu:

- Current message.
- Current pane.
- Current session.
- All panes.
- Workflow step.

Header pane hoặc conversation bar phải luôn hiển thị Skill đang active để tránh việc người dùng quên Skill vẫn đang áp dụng.

### 5.4. Shared context và pane-local context

Cần tách hai lớp context.

**Shared context:**

- Objective.
- Requirement.
- File đầu vào.
- Quyết định đã duyệt.
- Project memory.
- Pinned information.

**Pane-local context:**

- Lịch sử riêng của từng model.
- Tool results riêng.
- Branch thử nghiệm.
- Scratch state.

UI đề xuất:

```text
Context
Shared: 28k
Claude local: 12k
Codex local: 9k
```

Trong Compare mode, tất cả model phải nhận cùng một shared-context snapshot để kết quả so sánh công bằng.

### 5.5. Context compression cơ bản

Không cần triển khai vector database ngay. Phiên bản đầu nên có:

1. Immutable raw transcript.
2. Recent messages giữ nguyên văn.
3. Structured summary cho phần lịch sử cũ.
4. Pinned context không bị compress.
5. Artifact lớn chỉ đưa reference vào prompt.
6. Token meter riêng cho từng model.

Structured summary nên dùng schema:

```yaml
objective:
confirmed_decisions:
constraints:
active_tasks:
open_questions:
artifacts:
```

Policy đề xuất:

- Dưới 60% context: giữ nguyên.
- 60–75%: loại log và dữ liệu lặp.
- 75–85%: compress history cũ.
- Trên 85%: tạo checkpoint.
- Trên 95%: cảnh báo nếu phải loại context quan trọng.

Sau khi compress, cần thông báo:

```text
Context đã tối ưu
48,200 → 13,600 tokens

Giữ lại:
- 8 message gần nhất
- 6 pinned decisions
- 3 artifact references

[Xem chi tiết] [Khôi phục]
```

Compression không nên hoàn toàn vô hình.

### 5.6. Trạng thái, lỗi và message actions

Provider status cần phân biệt:

- Online.
- Chưa cấu hình.
- Authentication error.
- Rate limited.
- Quota exhausted.
- Endpoint unavailable.
- Reconnecting.

Ví dụ error card:

```text
NVIDIA không khả dụng
Nguyên nhân: quota exhausted

[Retry] [Đổi model] [Mở Settings]
```

Message actions tối thiểu:

- Copy.
- Regenerate.
- Continue.
- Edit and resend.
- Retry bằng model khác.
- Pin.
- Branch.
- Export.
- Xem token, latency, cost và finish reason.

---

## 6. P1 — tính năng tạo khác biệt cho Harness Hub

### 6.1. Workflow chạy trực tiếp trong chat

Người dùng có thể gọi:

```text
/workflow basic-design-generation
```

Chat hiển thị run card:

```text
Basic Design Generation

✓ Read requirements
✓ Extract screens and APIs
● Generate design
○ Cross-model review
○ Human approval
○ Export Excel

[Xem log] [Tạm dừng] [Huỷ]
```

Màn hình Runs vẫn tồn tại để xem lịch sử và debug chi tiết, nhưng thao tác chính nên diễn ra ngay trong chat.

### 6.2. Context Inspector

Panel bên phải:

```text
Context | Skills | Tools | Trace | Artifacts
```

Tab Context nên hiển thị:

```text
Token budget                 74%
System & policies            4.2k
Pinned context               8.5k
Recent conversation         12.3k
Compressed history           6.8k
Retrieved knowledge          3.1k
Artifacts                   18.6k
Reserved output             16.0k
```

Các action quan trọng:

- Pin/unpin.
- Exclude khỏi prompt.
- Compress now.
- Reset pane context.
- Restore checkpoint.
- Xem actual payload gửi cho provider.

`View actual payload` có giá trị cao cho việc debug sự khác nhau giữa các model.

### 6.3. Tool trace và inline approval

Trace rút gọn trong chat:

```text
Prompt
→ Router
→ Claude
→ Read file
→ Generate patch
→ Waiting for approval
```

Approval card:

```text
Agent muốn chạy: git push

[Approve once]
[Approve for this run]
[Reject]
```

Mục Approvals trong sidebar chỉ là nơi tổng hợp toàn bộ request đang chờ.

### 6.4. Artifact panel

Workflow output nên tách thành:

```yaml
display_output:
context_output:
artifact_output:
```

Ví dụ khi đọc Excel:

- `display_output`: Đã đọc 14 sheet.
- `context_output`: tên sheet và phát hiện chính.
- `artifact_output`: JSON đầy đủ lưu ngoài context.

Artifact panel nên hỗ trợ:

- Markdown.
- Code.
- Diff.
- Excel.
- JSON.
- HTML preview.
- Diagram.
- Report.

Việc này cải thiện cả UX và token performance.

### 6.5. Compare mode

Mode selector:

```text
Single | Compare | Relay | Auto-route
```

Compare mode cần:

- Dùng cùng một context snapshot.
- Hiển thị latency và cost theo model.
- Cho phép chọn output tốt nhất.
- Cho phép gửi output từ model A sang model B để review.

Không nên bật Compare mặc định vì runtime cost tăng gần tuyến tính theo số model.

---

## 7. P2 — chỉ triển khai sau khi core ổn định

### Judge và merge answer

Cần thêm model call nên cost và latency cao. Chỉ nên làm khi Compare mode đã có usage thực tế.

### Semantic retrieval

Có ích cho session dài, nhưng cần chunking, embedding, vector store, ranking, provenance và evaluation. Trong MVP, structured summary + pinned context + recent messages có cost/performance tốt hơn.

### Hierarchical checkpoint

Giải quyết lỗi summary-of-summary, nhưng backend phức tạp. Nên làm khi đã có session dài, workflow dài hoặc nhiều branch.

### Auto-routing

Có thể giảm cost bằng cách chọn model rẻ cho task đơn giản, nhưng cần router, policy, evaluation và fallback. Chỉ nên triển khai sau khi có usage data.

### Enterprise governance

RBAC, audit log, data boundary, quota và budget là bắt buộc cho enterprise rollout, nhưng chưa phải ưu tiên của UI MVP.

---

## 8. Bố cục UI đề xuất

### Conversation bar

```text
Compare | Shared context | Auto-compress ON
3 targets | 74k tokens | ¥0.42 | Stop all
```

### Pane header

```text
Anthropic / Claude Sonnet
Agent: Reviewer · Skill: Code Review
Context: 32k / 128k · 2.1s · ¥0.08
```

### Composer

```text
[+ File] [@ Agent] [# Skill] [/ Workflow]
[Context: Shared ▼] [Targets: All ▼]

Nhập yêu cầu...

[Send] [Stop]
```

### Right panel

```text
Context | Skills | Tools | Trace | Artifacts
```

### Sidebar adjustments

- Cho phép collapse.
- Giảm spacing dọc khoảng 15–20%.
- Dùng màu cam chỉ cho selection và primary action.
- Đưa `Xoá` vào menu `…` và hỗ trợ undo.
- Gom provider status vào một popover.
- Phân biệt rõ Online, Configured và Unavailable.

---

## 9. Roadmap đề xuất

### Phase 1 — Functional Chat Hub

Chiếm khoảng 60% effort:

1. Provider–Model–Agent–Profile.
2. Global composer.
3. Target selector.
4. Shared/local context.
5. Skill activation.
6. Token meter.
7. Pin và structured compression.
8. Stop, retry, fallback.
9. Session persistence.
10. Error details.

Đây là giai đoạn có tỷ lệ cost/performance tốt nhất.

### Phase 2 — Harness Orchestration

Khoảng 30% effort:

1. Workflow card trong chat.
2. Context Inspector.
3. Tool trace.
4. Inline approval.
5. Artifact panel.
6. Compare mode.

Sau giai đoạn này, sản phẩm mới thực sự khác một chat UI thông thường.

### Phase 3 — Optimization và Enterprise

Khoảng 10% effort ban đầu, mở rộng theo nhu cầu:

1. Semantic retrieval.
2. Hierarchical checkpoint.
3. Judge/merge.
4. Auto-routing.
5. RBAC.
6. Audit.
7. Budget policy.
8. Evaluation dashboard.

---

## 10. Kết luận

Ưu tiên cao nhất không phải thêm nhiều model hoặc nhiều menu hơn. Harness Hub cần hoàn thiện ba lớp điều khiển:

1. **Conversation level:** mode, target, shared context và tổng cost.
2. **Pane level:** model, agent, skill, local context và tool permission.
3. **Message/run level:** retry, trace, approval, artifact và workflow state.

Đề xuất cho vòng phát triển tiếp theo:

> Global composer + Skill activation + Shared/local context + Token meter + Structured compression + Workflow card.

Nhóm này tạo ra phần lớn giá trị của Harness Hub nhưng chưa yêu cầu các hệ thống có chi phí cao như vector retrieval, judge model hoặc auto-routing.
