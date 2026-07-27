# SD — Chat thành control plane (phản hồi review ChatGPT round 1)

**Date:** 2026-07-22 · **Status:** chờ user duyệt · **Author:** Claude (Opus 4.8)
**Nguồn:** `harness/review-harness-v2-round-1-chatgpt.md` (ChatGPT, 2026-07-22, 569 dòng)
**Upstream:** `bf31eb2` review doc · `ebf4a2a` fix onClear · `2f39fed` E5 artifact · `8629828` E3 canvas

---

## 1. Nhận định chung về review

Luận điểm trung tâm **đúng**: ChatPage hiện là 4 ô chat song song, không phải bàn điều khiển.
Ma trận utility/cost/ROI của review cũng lành mạnh — nó xếp đúng thứ rẻ mà có giá trị lên trước.

Nhưng review là **thuần UI, viết từ ảnh chụp màn hình**. Nó không biết backend có gì, nên có chỗ nó
đòi thứ đã có sẵn, có chỗ nó coi nhẹ thứ thực ra phải sửa backend. Mục 2 là kết quả đối chiếu với code.

Một điểm nữa: review **không biết ràng buộc của workflow engine**. Nó đề xuất "Workflow card trong chat"
mà không biết workflow bị ép là **chuỗi thẳng** (`services/workflow.py:181`) và có **gate dừng chờ duyệt**
(`workflow_exec.py:250`). Bất kỳ thiết kế nào cho workflow vào chat đều phải tôn trọng hai thứ đó.

## 2. Đối chiếu với code — cái gì rẻ, cái gì không

| Review đòi | Sự thật trong code | Chi phí thật |
|---|---|---|
| Token meter trong chat | Sự kiện `done` của SSE **đã mang `usage`**; ChatPage đã lưu vào `message.usage` | **Frontend, rất rẻ** |
| Error card có nguyên nhân + action | `/api/providers` **đã trả** `detail` (`"NVIDIA_API_KEY not set in environment"`, `"not_installed"`, `"ok"`) + `capabilities{stream,resume,models}` | **Frontend, rất rẻ** |
| Global composer, target selector | thuần state frontend | **Frontend, vừa** |
| Shared context / pane-local | thuần state frontend, ghép trước khi POST | **Frontend, vừa** |
| Provider–Model–**Agent**–Profile | `/api/chat` **CHỐI role `system`** (`server.py:112`: "message role must be user or assistant") | **Cần sửa backend** |
| Kích hoạt Skill từ chat | cùng lý do trên — skill nhét vào đâu nếu không có system message | **Cần sửa backend** |
| Auto-compress theo ngưỡng 60/75/85/95% | không đo được context window của claude/codex — chúng chạy qua CLI, giữ context riêng bên trong | **Không làm được đúng lúc này** |

### 2.1. Phát hiện thêm — review không có, quan trọng hơn nửa danh sách của nó

**`available: true` NÓI DỐI.** `/api/providers` báo claude `available:true`, `version:"2.1.207"`,
`detail:"ok"`. Gọi thật thì trả về:
```
Failed to authenticate: OAuth session expired and could not be refreshed
```
Nguyên nhân: kiểm tra sức khoẻ provider chỉ dò **có cài đặt hay không**, không dò **có đăng nhập được không**.
Người dùng thấy chấm xanh rồi gõ prompt, đợi, rồi mới biết hỏng. Đây chính là lý do bảng phân loại trạng thái
mà review đòi là cần thiết — nhưng phải sửa cả chỗ **đo**, không chỉ chỗ **hiện**.

**Nặng hơn: hub KHÔNG PHÂN BIỆT ĐƯỢC lượt hỏng với lượt thành công.** Đo trên máy thật sau khi F1 lên:
lượt gọi claude thất bại vì hết hạn OAuth được lưu thành
```
{ role: "assistant", content: "Failed to authenticate: OAuth session expired…", usage: {…} }
```
— tức là nó đi qua đường **`delta` + `done`**, y hệt một lượt trả lời bình thường, KHÔNG phải sự kiện
SSE `error`. Ba hệ quả:
1. Error card của F1 **không bao giờ kích hoạt** cho loại lỗi này. Đã kiểm chứng: đổi `role` thành
   `system` thì thẻ hiện đúng ("Provider không khả dụng · Nguyên nhân: … · [Thử lại] [Đổi model]
   [Mở Settings]"). Thẻ đúng, chỉ là không có đường nào tới nó.
2. Lượt hỏng bị **ghi vào thống kê usage như một lượt thành công** — bẩn dữ liệu của trang Usage.
3. Mọi cơ chế retry/fallback sau này đều vô dụng, vì không có tín hiệu nào để bám.
Gốc rễ: adapter provider chuyển stderr/exit code của CLI thành văn bản trả lời thay vì thành lỗi.
**Đây là việc backend đáng giá nhất hiện giờ**, gộp vào F1b.

**Chat provider codex trả lời sai.** Gửi prompt vào pane codex, nó đáp `"Sẵn sàng. Gửi task đầu tiên."`
thay vì nội dung — thiếu preamble kiểu `FRESH START` mà `codex exec` đang dùng. Pane codex hiện vô dụng.

**`Xoá` xoá sạch pane, không hỏi lại.** Review chê đúng. Hôm nay chính nó đẻ ra một lỗi HIGH
(tham chiếu artifact treo, panel tự bật lại) — đã vá ở `ebf4a2a`, nhưng nút vẫn nguy hiểm như cũ.

## 3. Chỗ tôi KHÔNG làm theo review

1. **Auto-compress theo ngưỡng % — hoãn.** Với claude/codex qua CLI, ta không cầm context window nên mọi
   ngưỡng đều là đoán. Nặng hơn: nén tự động là **âm thầm viết lại lịch sử**, mà đây là công cụ điều phối,
   khả năng tái lập quan trọng hơn tiết kiệm token. Làm phần **nhìn thấy được** trước (token meter, pin);
   khi nào có số thật thì mới bàn chính sách nén.
2. **Chat KHÔNG nuốt Workflows/Runs/Approvals.** Review muốn "không phải rời màn hình chat". Làm đúng thế
   nghĩa là dựng lại U2–U4 lần nữa bên trong chat. Rẻ hơn và đủ tốt: chat mang **điểm vào + trạng thái**,
   bấm vào thì sang trang chuyên dụng. 80% giá trị, 20% công.
3. **Compare / Relay / Auto-route — hoãn**, đồng ý với chính review (P1/P2).
4. **Artifact panel — đã làm rồi** (`2f39fed`), review xếp P1. Không phải làm lại.

## 4. Phân pha

Xếp theo rẻ-mà-đau trước. F1+F2 gần như miễn phí và sửa đúng ba thứ tôi va phải hôm nay.

| Phase | Nội dung | Đụng backend? | Size |
|---|---|---|---|
| **F1** | **Sự thật về provider**: bảng trạng thái (online / chưa cấu hình / lỗi xác thực / chưa cài), error card có nguyên nhân + `[Thử lại] [Đổi model] [Mở Settings]`; header pane hiện provider + model thật + ý nghĩa `READ-ONLY`; `Xoá` chuyển vào menu `…` kèm hoàn tác | không | S |
| **F1b** | **Sửa chỗ ĐO**: health check provider phải phát hiện được hết hạn xác thực, không chỉ "đã cài" | có | S |
| **F2** | **Token meter**: cộng dồn `usage` theo pane + theo hội thoại, hiện ở header pane và thanh hội thoại | không | S |
| **F3** | **Global composer**: gộp `Gửi tất cả` thành target selector nằm sát ô nhập, hiện rõ prompt đi tới đâu | không | M |
| **F4** | **Shared context / pane-local**: khối context dùng chung + ghim message, hiện dung lượng từng lớp | không | M |
| **F5** | **Agent binding**: `/api/chat` nhận `agent_id` (hoặc role `system`), pane chọn agent, nạp `system_prompt` + `provider` + `model` + `permission` từ agent yaml | có | M |
| **F6** | **Skill từ chat**: `#skill`, chip hiện skill đang bật + scope | có | M |
| — | E4 canvas kéo-thả (đã có brief) — vẫn làm, nhưng xuống dưới F1–F3 | có | L |

**Sửa vặt kèm F1**: preamble `FRESH START` cho chat provider codex, nếu không pane codex vẫn vô dụng.

## 4-bis. Phase G — hợp nhất design system (review round 2, user chuyển 2026-07-22)

Review thứ hai kết luận: UI hiện giống nhiều nhóm component ghép lại hơn là một sản phẩm chạy trên một
design system. Vấn đề không ở bố cục mà ở **màu, radius, border, typography, trạng thái, hierarchy**
mỗi chỗ một kiểu. Yêu cầu: dừng thêm component mới một vòng, đi hợp nhất lớp nền.

Tách làm hai để chạy song song an toàn với F4–F6 (đang sửa `ChatPage.tsx`):

| | Nội dung | Đụng file đang chạy? |
|---|---|---|
| **G0** | Chốt token (màu, radius 6/8/12/999, spacing lưới 4px, type scale) + dựng primitive `Button/IconButton/Input/Select/Textarea/Chip/Status/ProviderDot/EmptyState` + `DESIGN.md` | **không** — chỉ tạo file mới |
| **G1** | Áp dụng vào từng trang, thay hết giá trị tự phát bằng token | có — làm SAU F6 |

**Quyết định đã chốt theo review:** hướng "dark technical workbench"; một brand accent duy nhất
(violet `#8b7cf6`) dùng cho selection/focus/primary; **màu provider tụt xuống chỉ còn một chấm 6–8px**,
cấm dùng cho button, navigation active hay selection; bốn cấp surface có khoảng cách nhìn thấy được;
mono chỉ dành cho model id, version CLI, số token, command.

⚠️ **Một mâu thuẫn giữa hai review, phải xử khi làm G1:** review round 2 đề xuất pane có
`min-height: 420px`. Nhưng F3-fix-1 vừa ghim trang chat theo chiều cao viewport để composer không bị
đẩy khuất (đo thật: trước khi sửa, 3 pane cho `scrollHeight 1373` trên viewport `720`, composer nằm ở
`1331`). Đặt min-height cứng 420px cho pane sẽ **làm sống lại đúng lỗi đó** khi có 4 pane.
Giữ ưu tiên: composer luôn nhìn thấy > pane cao tối thiểu. Pane co được, và cuộn bên trong.

## 5. Không làm (chốt lại)

- Không nén context tự động khi chưa đo được context window thật.
- Không nhân bản Workflows/Runs/Approvals vào trong chat.
- Không semantic retrieval, judge/merge, auto-routing, RBAC — đồng ý với review, P2.
