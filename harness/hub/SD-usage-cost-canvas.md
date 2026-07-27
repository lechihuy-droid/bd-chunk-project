# SD — Usage/Cost tracking + Workflow Canvas
**Date:** 2026-07-22 · **Status:** ✅ APPROVED (user, 2026-07-22) · **Author:** Claude (Opus 4.8)
**Upstream:** UI v3 xong 9/9 trang (`ffe3d17`), Phase D xong (`c03c8c7`), perf fix (`b70ce08`).
**Yêu cầu user:** (1) đem chức năng tracking log / usage token / chi phí của hub cũ vào v3, thiết kế UI cho hợp;
(2) chưa có canvas kéo-thả agent.

---

## 1. Audit — hub cũ có gì, v3 đang bỏ gì

Backend **đã có sẵn** gần hết dữ liệu (không cần build mới):

| Endpoint | Trả về | v3 đang dùng? |
|---|---|---|
| `GET /api/usage?source&model&since` | **event thô**: ts, source, model, total_tokens, calls, session, command | ❌ không dùng |
| `GET /api/usage/rollup?source&model&since` | `by_model`, **`by_day`**, `by_source`, `totals{calls, input_tokens, output_tokens, total_tokens, cache_tokens, non_cache_tokens}` | ⚠️ chỉ dùng by_source + by_model |
| `GET /api/usage/cockpit` | today / week7d theo provider + `quota_warn_per_day` | ✅ dùng (quota card) |
| `GET /api/tools` | rollup tool events | ⚠️ nhét trong `<details>` |

**v3 UsagePage bỏ mất 4 thứ hub cũ có:**
1. **Bộ lọc** source / model / since — backend hỗ trợ, UI không gửi.
2. **`by_day`** — biểu đồ xu hướng theo ngày (hub cũ: bar chart 30 ngày + xem tất cả).
3. **Tách cache / input / output** — `cache_tokens`, `non_cache_tokens` không hiển thị.
4. **Bảng log event thô** — chính là "log" user muốn (hub cũ: 200 dòng gần nhất, có session + command).

## 2. Chi phí — sự thật cần chốt trước khi build

**Không có pricing ở bất kỳ đâu trong repo.** Quan trọng hơn: kiến trúc harness này cố tình chạy
**claude/codex qua CLI subscription** + **NVIDIA free tier** + gemini CLI → **không có hoá đơn theo token**.
Hiển thị một con số "$" sẽ là **do ta tự tính**, không phải đọc từ bill.

Ba cách mô hình hoá, đã chốt ở §5:
- **A. Shadow cost** — bảng giá list API × token đã dùng, nhãn *"ước tính — không thực trả"*.
- **B. Chỉ quota burn** — % hạn mức ngày/tuần theo provider (`quota_warn_per_day` có sẵn).
- **C. Cả hai** — quota burn là số chính, shadow cost là số phụ có nhãn ước tính.

Dù chọn gì: **không được** trình bày như tiền thật đã tiêu.

## 3. Thiết kế UI — trang "Usage & chi phí"

Giữ ngôn ngữ v3: nền panel, màu theo provider, số mono, nhãn 10px uppercase. Trang hiện tại là một đống phẳng;
tái cấu trúc thành 5 tầng, đọc từ tổng quan → chi tiết:

```
GIÁM SÁT
Usage & chi phí                 [Hôm nay][7 ngày][30 ngày][Tất cả]
                                [source ▾] [model ▾]
─────────────────────────────────────────────────────────────
┌ Tokens ────┐ ┌ Calls ───┐ ┌ Cache ────┐ ┌ Ước tính ──┐
│ 1.24M      │ │ 342      │ │ 68%       │ │ ~$4.10     │
│ 890k in ·  │ │ 12 hôm   │ │ tiết kiệm │ │ ước tính   │
│ 350k out   │ │ nay      │ │ nhờ cache │ │ (không trả)│
└────────────┘ └──────────┘ └───────────┘ └────────────┘
─────────────────────────────────────────────────────────────
Xu hướng theo ngày            ← SVG tự vẽ, MỘT chuỗi (by_day không tách provider)
  ▁▂▃▅▂▇▃▁▂▅▃▁▂▇▅▃
─────────────────────────────────────────────────────────────
Theo model              │ Theo provider
 table + cột chi phí    │ table + quota burn %
─────────────────────────────────────────────────────────────
▸ Nhật ký (log)   ← bảng event thô, áp bộ lọc, lazy-load khi mở
   Thời gian │ Source │ Model │ Tokens │ Calls │ Session │ Command
```

**Quyết định thiết kế:**
- **Bộ lọc ở đỉnh điều khiển toàn trang** — một state, mọi tầng dùng chung, đẩy thẳng vào query param backend
  đã hỗ trợ. Đây là thứ biến trang từ "báo cáo tĩnh" thành "công cụ điều tra".
- **Xu hướng theo ngày là nhân vật chính** — trang tracking mà không có trục thời gian thì vô dụng. Đây cũng
  chính là thứ hub cũ có mà v3 đánh rơi.
- **Cache là KPI riêng** — dữ liệu thật cho thấy cache chiếm ~57% token; với kiến trúc CLI subscription đây là
  đòn bẩy tiết kiệm lớn nhất, hub cũ chỉ ghi một dòng phụ.
- **Độ phủ giá phải đi kèm số tiền** — dữ liệu thật: 91% token CHƯA CÓ GIÁ. Hiện `$317` trần trụi là gây hiểu
  nhầm; phải kèm "chỉ 9% token có giá". Model chưa có giá hiện chữ "chưa có giá", KHÔNG hiện `$0.00`
  (đọc thành "miễn phí").
- **Log nằm trong `<details>` đóng sẵn + lazy fetch** — dataset thật 28k+ event, không kéo khi chỉ liếc tổng quan.
- **Không thêm npm dep cho chart**: tự vẽ SVG (~80-120 dòng), đúng luật self-contained.

## 4. Thiết kế UI — Canvas kéo-thả

> **⚠️ SỬA ĐỔI 2026-07-22 — §4 bên dưới ĐÃ LỖI THỜI, đọc §4-bis.**
> Đọc lại `services/workflow.py` phát hiện schema **cấm** graph tự do. Xem §4-bis.

### 4-bis. Bản sửa — canvas là trình biên tập CHUỖI, không phải graph

**Sự thật quyết định (`services/workflow.py:181`):**
`"Edges must form exactly one linear chain covering every node once"` — `_walk_chain` bắt buộc
in_degree ≤ 1, out_degree ≤ 1, đúng MỘT node đầu và MỘT node cuối. Không nhánh, không merge, không rẽ nhánh.

Hệ quả trực tiếp:
1. **Canvas graph tự do sinh workflow invalid 100%.** Cho người dùng nối cạnh tuỳ ý = mời họ tạo thứ
   không chạy được. Ràng buộc phải nằm trong UI, không nằm ở thông báo lỗi sau khi bấm Lưu.
2. **React Flow bị huỷ (ghi đè §5.2).** Giá trị của nó là zoom/pan/minimap/nối cạnh tự do — đúng những
   thứ phải khoá. 3-5 node thì minimap vô nghĩa. Quay lại luật "không thêm dep" của SD-ui-v3 §6.
   *(user duyệt 2026-07-22)*
3. **Không cần `.layout.json`.** Thứ tự chuỗi ĐÃ quyết định vị trí — toạ độ x/y là dữ liệu thừa,
   thừa thì lệch. Bỏ luôn. (Ghi đè §4 gạch đầu dòng cuối và §6 cột E4.)

**Thiết kế đúng:**

```
Workflows › <id>            [Kiểm tra] [Lưu] [Chạy]
┌ Palette ──┬─ Chuỗi ──────────────┬─ Inspector ────┐
│ Agent     │   ┌─────────────┐    │ node: implement│
│ · thinker │   │ ① brief     │    │ agent   [▾]    │
│ · coder   │   │   thinker   │    │ prompt  [    ] │
│ · drafter │   └──────┬──────┘    │ gate    [▾]    │
│           │      ▼ thả vào đây   │                │
│ Node      │   ┌─────────────┐    │ tham chiếu:    │
│ · validate│   │ ② implement │◆   │ {{brief_output}}│
│           │   │   coder     │    │ ✓ hợp lệ       │
└───────────┴───┴─────────────┴────┴────────────────┘
```

- **Kéo node = đổi THỨ TỰ trong chuỗi**, không phải đặt toạ độ. `edges` tự sinh từ thứ tự
  (`[[n0,n1],[n1,n2],…]`) → không bao giờ tạo được chuỗi gãy.
- **Kéo agent từ palette thả vào khe giữa hai node = chèn node mới** tại vị trí đó.
- **Cạnh không vẽ tay.** Người dùng không có khái niệm "nối" — bớt một lớp trạng thái sai.
- **Đổi thứ tự có thể làm hỏng prompt.** `{{X_output}}` chỉ hợp lệ khi X đứng TRƯỚC
  (`workflow.py:225-229`); `validate.target` cũng phải là node trước đó. Canvas phải cảnh báo
  ngay tại node bị hỏng, không đợi tới lúc Lưu.
- **Gate = ◆ amber** trên mép node, dùng lại ngôn ngữ spine của RunsPage.

**Emit YAML — làm ở BACKEND, không làm ở TS.**
`PUT /api/workflows/{id}` chỉ nhận `yaml_text` thô. Tự sinh YAML bằng TS phải tự lo block scalar cho
prompt nhiều dòng, escape, quote — dễ sai âm thầm. Thay vào đó thêm endpoint nhận **JSON model**,
dùng `yaml.safe_dump` của Python, rồi dán lại khối comment đầu file. Đường ghi vẫn đi qua
`save_workflow()` nên giữ nguyên validate + backup.

**Comment đầu file phải sống.** 3 template D4 mang cảnh báo ngữ nghĩa gate ngay trên đầu file
(`code-task.workflow.yaml` 4 dòng). Emit ngây thơ sẽ nuốt mất. Bắt buộc tách khối comment dẫn đầu
(mọi dòng `#` / dòng trống trước dòng YAML đầu tiên) và ghi lại nguyên văn.

**Gap phát hiện thêm:** không có endpoint đọc YAML thô. WorkflowsPage hiện bắt người dùng *dán YAML
vào textarea* mới sửa được (`"YAML không có endpoint đọc thô"`). Thêm `GET /api/workflows/{id}/source`
sửa luôn cả hai chỗ.

---

### 4 (bản gốc — giữ để đối chiếu, KHÔNG thi hành)

Hub cũ có `web/canvas.js` (141 dòng) mount trong workflow editor + `emitWorkflowYaml()`, rất tối giản. v3 chưa port.
Thiết kế mới dùng lại ngôn ngữ hình ảnh của **run spine** (node tròn, gate = thoi amber):

```
Workflows › canvas
┌ Palette ──┬─ Canvas ────────────────────┬─ Inspector ──┐
│ Agents    │                             │ node: draft  │
│ · drafter │    ┌───────┐                │ agent  [▾]   │
│ · thinker │    │ draft │───┐            │ prompt [   ] │
│ · coder   │    └───────┘   │            │ gate   [▾]   │
│           │            ┌───▼────┐       │              │
│ Node      │            │ check  │◇ amber│ (validate:   │
│ · validate│            └───┬────┘       │  target/     │
│           │            ┌───▼────┐       │  checks/     │
│           │            │ refine │       │  on_fail)    │
└───────────┴────────────┴────────┴───────┴──────────────┘
        [Kiểm tra] [Lưu] [Chạy]
```

- **Kéo agent từ palette thả vào canvas** → tạo node gắn agent đó (màu viền = màu provider sau khi resolve
  class cheap/code/smart). Kéo node đổi vị trí. Kéo từ handle mép node sang node khác → tạo edge.
- **Inspector bên phải** sửa prompt/gate; node `validate` sửa target/checks/on_fail (D2).
- **Round-trip**: nạp từ `GET /api/workflows` (đã trả nodes+edges+stop → đủ dựng model, không cần endpoint mới),
  kiểm tra bằng `POST /api/workflows/validate`, lưu bằng `PUT /api/workflows/{id}` (đã có, tự validate).
- **Vị trí node (x,y)** không có trong schema workflow → lưu file phụ `workflows/.layout.json`
  (không đụng schema, không làm hỏng workflow đang chạy).

**⚠️ Rủi ro phải xử lý:** emit YAML từ canvas sẽ **xoá mất comment** trong file — 3 template D4 đang mang comment
quan trọng, gồm cả cảnh báo ngữ nghĩa gate ("đặt gate lên node TIÊU THỤ output"). Bắt buộc: giữ nguyên khối
comment đầu file khi ghi đè, hoặc cảnh báo rõ trước khi lưu. Không được im lặng nuốt mất.

## 5. Quyết định — ĐÃ CHỐT (user, 2026-07-22)

1. **Mô hình chi phí = C — cả hai.** Quota burn là số chính; shadow cost là số phụ, **luôn kèm nhãn "ước tính —
   không thực trả"**. Không bao giờ trình bày như tiền đã tiêu.
2. ~~**Canvas = thêm React Flow.**~~ **HUỶ 2026-07-22** — xem §4-bis. Schema ép chuỗi thẳng nên giá trị của
   React Flow (nối cạnh tự do) là thứ phải khoá. Quay lại luật "không thêm dep".
3. **Canvas = phương án A: tự do vị trí, một luồng chạy** *(user chốt 2026-07-22)*.
   Node đặt được ở toạ độ bất kỳ và toạ độ được lưu; `edges` vẫn phải là một chuỗi thẳng duy nhất.
   Nối thành nhánh bị chặn NGAY lúc nối, không đợi tới lúc bấm Lưu.
4. **Phương án B (DAG có nhánh + chạy song song) = hoãn, không huỷ** *(user 2026-07-22: "B lưu lại để sau
   này cần triển khai")*. Hồ sơ điều tra ở §8 — đọc trước khi khởi động lại, đừng điều tra lại từ đầu.

## 6. Phân pha (đã sắp lại theo quyết định §5)

Đảo E1/E2: chi phí cần backend trước, làm backend xong thì **tái cấu trúc frontend MỘT lần** đã gồm luôn cột/KPI
chi phí — thay vì sửa UsagePage hai lượt.

| Phase | Nội dung | Executor | Size | Trạng thái |
|---|---|---|---|---|
| **E1** | **Backend cost/quota**: `config.PRICING_USD_PER_MTOK` + `services/pricing.py` + cache_read/creation tách riêng + `estimated_cost_usd`/`unpriced_tokens` additive + `quota_pct` | [CODEX] | S | ✅ xong, 205 test xanh |
| **E2** | **Usage page tái cấu trúc (một lượt)**: bộ lọc → 4 KPI → xu hướng `by_day` → breakdown kèm chi phí & quota burn → bảng log lazy | [CODEX] | M | ⏭ tiếp theo |
| **E3** | **Canvas đọc-hiển thị (§4-bis)**: `GET /api/workflows/{id}/source` + chuỗi node dọc, gate ◆ amber, inspector chỉ-đọc. KHÔNG dep. | [CODEX] | M | ⏭ |
| E4 | Canvas kéo-thả: đổi thứ tự + chèn/xoá node + sửa inspector + `PUT .../model` (JSON→YAML **giữ comment đầu file**) + cảnh báo `{{X_output}}` gãy khi đổi thứ tự | [CODEX] | L | |
| E5 | Chat: panel artifact bên phải — tách output dài/code block khỏi bong bóng, render markdown + mục lục + copy + xuất .md (nội dung THẬT từ stream, khác mockup `workspace.js`) | [CODEX] | M | |

Mỗi phase: Codex code → Sonnet test/review → Claude build dist + browser-verify → commit.

## 8. Phương án B — DAG có nhánh & chạy song song (HOÃN, hồ sơ giữ lại)

Ghi ngày 2026-07-22 sau khi đọc engine. Khi nào cần B thì bắt đầu từ đây.

**Phát hiện quan trọng nhất: fan-out ĐÃ CÓ SẴN, chưa ai dùng.**
`workflow_exec.py:290` — mỗi node đã có thể `spawn` nhiều agent con, mỗi con mang agent/objective/budget/
skills riêng, chạy qua `runtime_children.create_child_run` với sandbox là **tập con** của cha
(`_ensure_subset` chặn con mở rộng quyền hơn cha). Governance chặn theo `risk_tier`. Output con đổ vào
`{{<node>_claims}}`. **Không workflow YAML nào đang dùng `spawn`.**
→ Lý do phổ biến nhất người ta muốn DAG ("một node gọi nhiều agent") **không cần DAG**. Trước khi mổ
engine, hãy dùng thử `spawn` đã.
→ Nhưng `spawn` hiện chạy **tuần tự** (`_run_child_provider` đồng bộ) và có lỗi: nhiều spawn thì
`node_outputs[f"{node_id}_claims"]` bị ghi đè, **chỉ con cuối sống sót**. Sửa cái này rẻ hơn làm DAG rất nhiều.

**Nếu vẫn làm B, đây là danh sách chỗ phải sửa (đã truy vết, không phải phỏng đoán):**

| Chỗ | Hiện tại | B đòi hỏi |
|---|---|---|
| `workflow.py:34 _walk_chain` | ép in/out-degree ≤ 1, 1 start 1 end | sắp xếp tô-pô, phát hiện chu trình |
| `workflow.py:181` | lỗi "must form exactly one linear chain" | bỏ, thay bằng luật DAG |
| `workflow.py:225-229` | `{{X_output}}` hợp lệ nếu X đứng trước trong walk | X phải là **tổ tiên** trong đồ thị |
| `workflow.py:207` | `validate.target` đứng trước trong walk | target phải là tổ tiên |
| `workflow.py:237 build_ir` | trả danh sách phẳng theo walk | trả đồ thị + tập node sẵn sàng |
| `workflow_exec.py:158` | `while True` + một con trỏ `node_index` | vòng lặp theo **frontier**, nhiều node cùng chạy |
| `workflow_exec.py:322` | checkpoint lưu `node_index` (một số) | lưu **tập** node xong/đang chạy; resume phải dựng lại frontier |
| `workflow_exec.py:250` | gate dừng node hiện tại | nhánh nào dừng? anh em có bị chặn theo không? **quyết định trước khi code** |
| `RunsPage.tsx` spine | danh sách dọc tuyến tính | vẽ đồ thị |
| tests | 206 test dựng trên giả định chuỗi | phần lớn phải viết lại |

**Rủi ro lớn nhất:** gate + checkpoint là hai thứ giữ cho agent `workspace_write` không chạy khi chưa ai
duyệt. B đụng thẳng vào cả hai. Đừng làm B chung phase với việc khác.

## 7. Không làm

- Không hiển thị "$" như tiền thật đã tiêu (xem §2).
- Không đổi schema workflow để nhét toạ độ canvas.
- Không bịa giá cho model không có giá công khai — để **unpriced** và hiện độ phủ.
- Không port lại dashboard cũ 1:1 — gộp vào Usage + Runs theo page map v3.
