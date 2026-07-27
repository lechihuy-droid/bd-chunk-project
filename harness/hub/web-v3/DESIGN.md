# DESIGN.md — Harness Hub web-v3

Tài liệu này là **hợp đồng cho coding agent**: đọc xong là làm được migration mà không cần xem lại bản review gốc. Token, tên component, class string đều giữ nguyên tiếng Anh để agent copy-paste chính xác; phần giải thích viết tiếng Việt.

## 1. Định hướng thị giác (3-4 câu)

Hướng thiết kế là **dark technical workbench** — dày đặc thông tin, ít trang trí, trạng thái luôn rõ ràng bằng label (không chỉ màu sắc). Mỗi vùng màn hình (region) chỉ có **một hành động chính** (primary button) — mọi hành động khác là secondary/ghost. Màu tím accent (`--hub-accent`) là màu hành động/chọn lựa duy nhất trong toàn bộ app; màu provider (claude/codex/nvidia/gemini) chỉ còn vai trò **chấm nhận diện 6-8px**, không tô màu nút, điều hướng, selection hay chữ nội dung. Bốn cấp bề mặt (app/sidebar/surface/elevated) tạo phân tầng thị giác rõ, thay cho hai cấp `panel`/`panel2` hiện tại vốn dùng lẫn lộn cho nhiều vai trò khác nhau.

## 2. Bảng token (tokens.css)

File: `src/styles/tokens.css`. Tất cả token có prefix `--hub-` để **không đụng** namespace `--color-*` / `--font-*` hiện có trong `src/index.css`. Đã kiểm tra: không có xung đột tên nào giữa `--hub-*` và các custom property hiện có.

### Surfaces

| Token | Giá trị | Vai trò |
|---|---|---|
| `--hub-bg-app` | `#0d1016` | nền toàn app |
| `--hub-bg-sidebar` | `#141821` | sidebar + topbar |
| `--hub-bg-surface` | `#11151c` | pane / card |
| `--hub-bg-elevated` | `#1a202b` | modal / dropdown / menu / nền input |
| `--hub-bg-hover` | `#202734` | hover row/item/button |
| `--hub-border-subtle` | `#262d39` | border mặc định |
| `--hub-border-strong` | `#343d4c` | border nhấn mạnh (phân tách cột, outline trước focus ring) |

### Text

| Token | Giá trị |
|---|---|
| `--hub-text-primary` | `#eef2f8` |
| `--hub-text-secondary` | `#9ba7b8` |
| `--hub-text-muted` | `#667085` |

### Brand accent (tím, duy nhất)

| Token | Giá trị | Dùng cho |
|---|---|---|
| `--hub-accent` | `#8b7cf6` | selection, focus ring, primary action |
| `--hub-accent-hover` | `#9a8df7` | hover trên primary |
| `--hub-accent-subtle` | `rgba(139,124,246,.12)` | nền nhạt khi cần highlight nhẹ |

### Semantic

| Token | Giá trị |
|---|---|
| `--hub-success` | `#3ecf8e` |
| `--hub-warning` | `#f5b942` |
| `--hub-warning-subtle` | `rgba(245,185,66,.12)` (mới, xem mục 5) |
| `--hub-error` | `#f26d6d` |
| `--hub-error-subtle` | `rgba(242,109,109,.12)` (mới) |
| `--hub-info` | `#63a4ff` |

### Radius — chỉ 4 giá trị

| Token | Giá trị | Dùng cho |
|---|---|---|
| `--hub-radius-sm` | 6px | inline code, checkbox, badge nhỏ |
| `--hub-radius-md` | 8px | input / button / menu item |
| `--hub-radius-lg` | 12px | pane / card / modal |
| `--hub-radius-full` | 999px | status chip, provider chip, pill, dot |

Không còn giá trị 3/4/9/10px tuỳ tiện (xem mục 5).

### Spacing (lưới 4px)

`--hub-space-1..8` = 4 / 8 / 12 / 16 / 24 / 32px.

### Kích thước cố định

`--hub-size-sidebar-item` 40px · `--hub-size-context-strip` 32px · `--hub-size-pane-header` 52px · `--hub-size-toolbar` 48px · `--hub-size-input` 40px · `--hub-size-composer-min` 56px · `--hub-size-drawer` 360px · `--hub-card-padding` 16px · `--hub-pane-gap` 12px.

### Progressive disclosure

Chức năng phụ **không** được chiếm chỗ cố định trên màn hình chính. Bối cảnh chung, tình
trạng provider, chọn agent/model đều nằm sau một `Popover` hoặc drawer 360px; trên mặt
tiền chỉ còn một dòng tóm tắt.

Mỗi dữ liệu có **một nơi sở hữu duy nhất**: `ProviderDot` giữ provider, nhãn giữ model,
`Status` giữ trạng thái chạy, `Chip` giữ quyền tool. Không lặp cùng một thông tin dưới
hai hình thức khác nhau.

### Quyền sở hữu scroll

Mỗi pane là ba vùng: header, thân hội thoại, composer — và **chỉ thân hội thoại được
cuộn**. Header với composer đứng yên; trang không bao giờ có thanh cuộn riêng.

### AI Workspace — bố cục 3-panel (trang Chat)

Trang Chat theo design "AI Chat Workspace" (import từ claude.ai/design, map sang token
hub — light-theme gốc #3654D6 dịch sang accent violet hub, giữ dark theme-aware). CSS
đặt trong `index.css` dưới tiền tố `.cw-*`.

- **Top bar 56px**: tên workspace + badge Active · `ModelSelector` (thẻ provider, không
  hiện raw model ID) · Export · Cài đặt · avatar.
- **Sidebar 220px**: New chat + tab Chats/Files/Artifacts. Thu về icon-rail rồi ẩn theo
  breakpoint.
- **Center (flex, min 280px)**: context bar (chỉ khi có hội thoại) · vùng tin nhắn (cuộn
  duy nhất) · command chips · composer **luôn hiện** kể cả lúc rỗng.
- **Artifact panel 380px**: header (status/version/type + history/export/copy) + các section
  có menu `⋯` sửa theo từng phần. Trống thì hiện empty state.
- Responsive: `≤1180px` ẩn artifact panel; `≤820px` ẩn sidebar.

`ModelSelector` không bịa speed/cost per-model: mỗi thẻ chỉ nêu vai trò provider + fact thật
(stream/resume/số model/version) và trạng thái khả dụng. Một dữ liệu vẫn một chủ sở hữu.

Chưa có backend (đánh dấu `TODO(backend)` trong `ChatPage.tsx`): Files, versioning artifact,
export PDF/share link. Các phần này để UI thật + thông báo trung thực, không giả lập dữ liệu.

### Typography

| Style | size/line/weight | Token prefix |
|---|---|---|
| display | 20/28/600 | `--hub-display-*` |
| page title | 16/24/600 | `--hub-title-*` |
| section (uppercase, +0.08em) | 12/16/600 | `--hub-section-*` |
| body | 14/20/400 | `--hub-body-*` |
| label | 13/18/500 | `--hub-label-*` |
| caption | 12/16/400 | `--hub-caption-*` |

Font family không đổi — vẫn dùng `--font-sans` / `--font-mono` đã có trong `index.css`. **Mono chỉ dùng cho:** model id, CLI version, token count, command, technical identifier. **Không dùng mono cho** tên provider khi nó đóng vai trò navigation label.

## 3. OLD → NEW token mapping (mọi token đang dùng trong code)

| OLD (index.css `@theme`) | Giá trị cũ | NEW (tokens.css) | Ghi chú |
|---|---|---|---|
| `--color-ink` (`bg-ink`) | `#14161B` | `--hub-bg-app` | `#0d1016`, giá trị đổi (tối hơn) |
| `--color-panel` (`bg-panel`) | `#1B1E25` | `--hub-bg-sidebar` **hoặc** `--hub-bg-surface` | **Không 1:1** — `bg-panel` hiện dùng cho cả topbar/sidebar VÀ card/pane. Phải xét theo vai trò từng chỗ khi migrate. |
| `--color-panel2` (`bg-panel2`) | `#20242D` | `--hub-bg-elevated` **hoặc** `--hub-bg-hover` | **Không 1:1** — `panel2` hiện vừa là nền input, vừa là hover, vừa là surface phụ. Input/dropdown → elevated; hover row/button → hover. |
| `--color-line` (`border-line`) | `#2B303B` | `--hub-border-subtle` **hoặc** `--hub-border-strong` | Đa số → subtle; dùng strong chỉ khi cần tách biệt mạnh hơn. |
| `--color-text` (`text-text`) | `#E8EAF0` | `--hub-text-primary` | `#eef2f8` |
| `--color-dim` (`text-dim`) | `#8B92A3` | `--hub-text-secondary` | `#9ba7b8` |
| `--color-faint` (`text-faint`) | `#5A6172` | `--hub-text-muted` | `#667085` |
| `--color-gate` (`bg-gate`/`text-gate`/`border-gate`) | `#E4B15E` | `--hub-warning` (status/badge) | `#f5b942`. Khi dùng làm **nút hành động chính** (GateCard "Duyệt") — xem mục 5, cần quyết định riêng vì vi phạm luật "1 accent cho primary action". |
| `--color-ok` (`text-ok`) | `#5FBF77` | `--hub-success` | `#3ecf8e` |
| `--color-err` (`text-err`/`border-err`) | `#E06C75` | `--hub-error` | `#f26d6d` |
| `--color-claude/codex/nvidia/gemini` | không đổi | **giữ nguyên tên**, chỉ giới hạn cách dùng | Chỉ còn hợp lệ qua component `ProviderDot`. Mọi chỗ tô màu button/border/selection/text bằng 4 màu này là vi phạm — xem mục 5. |
| *(không có)* | bare `rounded` = 4px | `--hub-radius-sm` (6px) | ví dụ: inline code trong `markdown.tsx`, progress bar trong `UsagePage.tsx` |
| *(không có)* | `rounded-lg` = 8px | `--hub-radius-md` **hoặc** `--hub-radius-lg` | **Không 1:1** — `rounded-lg` hiện dùng chung cho button/input (nên là md=8px, giữ nguyên) VÀ cho pane/card/modal (nên nâng lên lg=12px). Đây là phát hiện chính về "radius không có quan hệ" — cùng 1 class Tailwind đang cõng 2 vai trò khác nhau. |
| *(không có)* | `rounded-[3px]` | `--hub-radius-sm` (6px) | badge hình thoi "gate" xoay 45° trong `RunSpine.tsx:17`, `WorkflowsPage.tsx:56` |
| *(không có)* | `rounded-[9px]` | `--hub-radius-lg` (12px) | logo box trong `Sidebar.tsx:12` |
| *(không có)* | `rounded-[10px]` | `--hub-radius-lg` (12px) | container trong `GateCard.tsx:3`, node card + output box trong `RunSpine.tsx:17`, node button trong `WorkflowsPage.tsx:56` |
| *(không có, raw CSS)* | `.app > aside a { border-radius: 8px }` (`index.css:33`) | `--hub-radius-md` | Đã trùng giá trị với `rounded-lg` hiện tại trên cùng element (Sidebar NavLink) — dư thừa, không phải bug nhưng nên dọn khi sửa `index.css`. |
| *(không có)* | `text-[10px]` + `tracking-[.14em]` (eyebrow/section label, ví dụ "ĐIỀU PHỐI") | `--hub-section-size` (12px) + `--hub-section-tracking` (0.08em) | Kích thước và tracking đều cần chỉnh khi migrate — xem mục 5. |
| *(không có)* | `text-xl font-semibold` (h1 trang, ví dụ `WorkflowsPage.tsx`) | `--hub-title-*` (16/24/600) | h1 hiện tại (20px) thực ra trùng với `--hub-display-*`, không phải `--hub-title-*` — cần **giảm kích thước** khi migrate để đúng vai trò "page title". |
| *(không có)* | `text-xs` (12px, dùng khắp nơi cho meta/badge/button) | `--hub-caption-*` (12/16/400) | Đã khớp sẵn, không cần đổi giá trị. |
| *(không có)* | *(chưa tồn tại — Tailwind không có scale 13px)* | `--hub-label-*` (13/18/500) | Token mới; áp dụng khi dùng `Button`/`Input`/`Chip` từ `ui.tsx`. |

## 4. Component API (`src/lib/ui.tsx`)

Cách style: **Tailwind arbitrary-value class tham chiếu CSS variable** (`bg-[var(--hub-accent)]`), không dùng inline `style`. Giữ nhất quán cách này khi mở rộng thêm component.

| Component | Props chính | Khi dùng |
|---|---|---|
| `Button` | `variant: primary\|secondary\|ghost\|destructive`, `size: sm\|md`, `icon?`, `disabled?` | `primary` — đúng 1 lần mỗi region (xem mục 4b). `secondary` — hành động phụ có khung. `ghost` — hành động rất phụ, không khung. `destructive` — xoá/huỷ/reject. |
| `IconButton` | `icon`, `aria-label` (bắt buộc) | Nút chỉ có icon (đóng pane, menu "…", copy). Hit-area tối thiểu 32×32. |
| `Input` / `Select` / `Textarea` | chuẩn HTML attrs | Mọi ô nhập liệu. Input/Select cao 40px, Textarea tối thiểu 48px. |
| `Chip` | `children`, `onRemove?`, `removeLabel?` | Có `onRemove` → chip xoá được (× ở cuối). Không có → chip tĩnh (hiển thị model/tag). |
| `Status` | `kind` (8 giá trị: ready/running/paused/setup-required/not-installed/rate-limited/error/offline), `label?` | Mọi hiển thị trạng thái provider/pane/run. Label luôn hiện — màu chỉ là tín hiệu phụ. |
| `ProviderDot` | `provider: claude\|codex\|nvidia\|gemini` | Chấm nhận diện 7px. Đây là **CÁCH DUY NHẤT HỢP LỆ** để hiện màu provider. |
| `EmptyState` | `icon?`, `title`, `description?`, `actions?` (tối đa 4, dư bị cắt) | Danh sách rỗng (chưa có workflow, chưa có run, v.v.) |
| `Popover` | `label`, `children` (hoặc `close => children`), `align: start\|end`, `aria-label` | Mọi control phụ: đổi model/agent, tình trạng provider, menu pane. Tự đóng khi click ra ngoài hoặc bấm Escape. Dùng thay cho việc xếp thêm một hàng control cố định. |

### 4b. Luật "1 primary button / region"

Mỗi region (toolbar, card, modal, form) chỉ được có **đúng một** `Button variant="primary"` tại một thời điểm. Các hành động còn lại trong cùng region dùng `secondary` hoặc `ghost`. Ví dụ vi phạm hiện tại cần sửa khi migrate: `AgentsPage.tsx` header có cả nút "Lưu" (`bg-codex`) và tab-bar cũng tô `border-codex` cho tab active trong cùng khung nhìn — sau migrate, chỉ "Lưu" là primary, tab active dùng underline `--hub-accent` nhưng không phải kiểu button.

## 5. Migration checklist — file cụ thể, class string cụ thể

### 5.1 Provider-colour dùng sai vai trò (action/selection/status thay vì chỉ identity dot)

Tổng cộng phát hiện **19 vị trí** trên **6 file**. Quy tắc thay thế chung: đổi `bg-codex`/`border-codex`/... dùng làm accent hành động → `bg-[var(--hub-accent)]` (hoặc tương đương secondary/ghost theo variant); đổi khi dùng làm "loại node"/"trạng thái" → semantic token (`--hub-info`, `--hub-warning`...), không phải màu provider.

| # | File | Class string hiện tại | Vai trò sai | Sửa thành |
|---|---|---|---|---|
| 1 | `src/pages/WorkflowsPage.tsx:56` | `selected?.id === row.id ? 'border-codex bg-panel2' : ...` (workflow list item) | selection | `Button`/hàng chọn dùng `border-[var(--hub-accent)]` |
| 2 | `src/pages/WorkflowsPage.tsx:56` | `className="ml-auto rounded bg-codex px-3 py-1.5 text-xs font-semibold text-ink"` (nút "Chạy") | primary action | `<Button variant="primary">Chạy</Button>` |
| 3 | `src/pages/WorkflowsPage.tsx:56` | `selectedNode === node.id ? 'border-codex ring-1 ring-codex' : ...` (chọn node trên canvas) | selection | `border-[var(--hub-accent)] ring-1 ring-[var(--hub-accent)]` |
| 4 | `src/pages/WorkflowsPage.tsx:56` | `isValidate(node) ? 'border-claude' : 'border-line'` (khung node loại "validate") | node-type indicator, không phải provider | dùng `--hub-info` hoặc `--hub-border-strong`, không phải màu claude |
| 5 | `src/pages/WorkflowsPage.tsx:56` | `<span className="rounded-full border border-claude px-1.5 text-[10px] text-claude">validate</span>` | badge loại node | `border-[var(--hub-info)] text-[var(--hub-info)]` (hoặc `Chip` tĩnh) |
| 6 | `src/pages/WorkflowsPage.tsx:56` | `<div className="flex h-10 flex-col items-center text-codex">` + `<span className="h-6 w-px bg-codex" />` (đường nối giữa node) | trang trí | `text-[var(--hub-border-strong)]` / `bg-[var(--hub-border-strong)]` |
| 7 | `src/pages/RunsPage.tsx:93` | `className="rounded-lg bg-codex px-5 py-2 text-xs font-semibold text-ink disabled:opacity-40"` (nút "Chạy" launch) | primary action | `<Button variant="primary">` |
| 8 | `src/pages/RunsPage.tsx:100` | `hover:border-codex` (card run gần đây) | hover accent | `hover:border-[var(--hub-accent)]` |
| 9 | `src/pages/AgentsPage.tsx:17` | `className="mb-3 w-full rounded bg-codex px-3 py-2 text-xs font-semibold text-ink"` (nút "+ Agent mới") | primary action | `<Button variant="primary">` |
| 10 | `src/pages/AgentsPage.tsx:17` | `agent.id === row.id ? 'border-codex bg-panel2' : ...` (chọn agent trong list) | selection | `border-[var(--hub-accent)]` |
| 11 | `src/pages/AgentsPage.tsx:17` | `tab === name ? 'border-codex text-text' : ...` (tab active) | active state | `border-[var(--hub-accent)]` |
| 12 | `src/pages/AgentsPage.tsx:17` | `className="ml-auto rounded bg-codex px-3 py-1.5 text-xs font-semibold text-ink"` (nút "Lưu") | primary action | `<Button variant="primary">` |
| 13 | `src/pages/SettingsPage.tsx:5` | `<span className="rounded-full border border-codex px-1.5 text-[10px] text-codex">default</span>` (badge model mặc định) | semantic "default", không phải provider | `border-[var(--hub-accent)] text-[var(--hub-accent)]` hoặc `Chip` tĩnh |
| 14 | `src/pages/ApprovalsPage.tsx:17` | `className="rounded bg-codex px-3 py-1.5 text-xs font-semibold text-ink disabled:opacity-40"` (nút duyệt/chấp nhận) | primary action | `<Button variant="primary">` |
| 15 | `src/components/RunSpine.tsx:17` | `node.state === 'running' ? 'border-claude text-claude node-pulse' : ...` (marker trạng thái node) | **status "running" đang tô cứng bằng màu Claude bất kể node chạy bằng provider nào** | `border-[var(--hub-accent)] text-[var(--hub-accent)]` (dùng `Status kind="running"` nếu hợp) |
| 16 | `src/components/RunSpine.tsx:17` | `node.state === 'running' ? 'border-l-2 border-l-claude' : ''` (viền trái box output) | status | `border-l-[var(--hub-accent)]` |
| 17 | `src/components/RunSpine.tsx:17` | `<i className="ml-1 inline-block h-3 w-1.5 animate-pulse bg-claude" />` (con trỏ streaming) | status/decor | `bg-[var(--hub-accent)]` |
| 18 | `src/components/RunSpine.tsx:8` | `providerClass = (agent) => ... `text-${p} border-${p}`` — chip hiện provider bằng text+border màu | **đây chính là identity, nhưng sai hình thức** (tô text/border thay vì chỉ chấm) | Thay chip bằng `<ProviderDot provider={p} />` + text màu `--hub-text-secondary` |
| 19 | `src/components/Sidebar.tsx:12` | `bg-gradient-to-br from-claude to-codex` (logo "H") | dùng 2 màu provider làm gradient trang trí, không liên quan lựa chọn provider nào | Đổi sang gradient/màu dựa trên `--hub-accent` (hoặc màu trung tính), không mượn màu provider |

Các vị trí **ĐÚNG** cần giữ nguyên làm mẫu (không phải lỗi): `ChatPage.tsx` dòng 104/113/126, `AgentsPage.tsx:17`, `SettingsPage.tsx:5` — các `<i className="h-2 w-2 rounded-full ${colors[provider]}" />` chấm nhận diện nhỏ cạnh tên provider. Khi migrate, thay object `colors` cục bộ bằng `<ProviderDot provider={...} />` từ `ui.tsx` để thống nhất kích thước (7px) và tránh định nghĩa lại map màu ở mỗi file.

### 5.2 Hex literal cần thay bằng token

| File | Literal | Thay bằng |
|---|---|---|
| `src/components/ArtifactRail.tsx:10` | `bg-[#181B21]` (nền aside) | `bg-[var(--hub-bg-surface)]` |
| `src/components/GateCard.tsx:3` | `border-[#4A3A20]` | `border-[var(--hub-warning-subtle)]` hoặc token border riêng nếu cần đậm hơn |
| `src/components/GateCard.tsx:3` | `bg-[#221C12]` | `bg-[var(--hub-warning-subtle)]` |
| `src/components/GateCard.tsx:3` | `text-[#1A1508]` (chữ trên nút "Duyệt" nền vàng) | giữ nguyên ý định (chữ tối trên nền warning) nhưng định nghĩa qua token, ví dụ `text-[var(--hub-bg-app)]` nếu độ tương phản đủ, hoặc thêm token `--hub-warning-ink` nếu cần riêng |

### 5.3 Vấn đề cần quyết định thêm (không tự ý sửa)

- **`GateCard.tsx` nút "Duyệt" dùng `bg-gate` (màu warning) làm primary action.** Luật mới nói primary action = `--hub-accent` (tím), nhưng "Duyệt/Từ chối" là hành động gate có ý nghĩa cảnh báo riêng (khác các nút thường). Đề xuất: giữ style riêng cho gate-approve (không phải `Button variant="primary"` chuẩn) nhưng định nghĩa rõ ràng là **variant thứ 5 nằm ngoài `ui.tsx`** hoặc chấp nhận nó là ngoại lệ có chủ đích — cần người review quyết, không migrate máy móc.
- **`bg-panel` / `bg-panel2` không 1:1** (mục 3) — cần xét từng vị trí. Danh sách file dùng nhiều nhất để ưu tiên khi sửa `index.css`/pages sau này: `ChatPage.tsx`, `WorkflowsPage.tsx`, `RunsPage.tsx`, `UsagePage.tsx`, `Sidebar.tsx`, `Topbar.tsx`.
- **`.app > aside a { border-radius: 8px }`** trong `index.css:33` trùng giá trị với `rounded-lg` Tailwind trên cùng phần tử — dư thừa, dọn khi có dịp sửa `index.css`.
- **Eyebrow/section label** (`text-[10px] font-semibold uppercase tracking-[.14em] text-faint`, xuất hiện lặp lại ở `WorkflowsPage.tsx`, `AgentsPage.tsx`, `UsagePage.tsx`, `ApprovalsPage.tsx`, `SkillsPage.tsx`, `SessionsPage.tsx`, `RunsPage.tsx` không có — kiểm tra lại) cần đổi sang `--hub-section-*` (12px, tracking 0.08em thay vì 0.14em).
- **h1 trang** (`text-xl font-semibold`, ví dụ `WorkflowsPage.tsx:56`, `AgentsPage.tsx:17`, `SkillsPage.tsx:14`, `ApprovalsPage.tsx:17`, `SessionsPage.tsx:6`) hiện to bằng scale `display` (20px) — theo quyết định mới nó phải nhỏ lại đúng scale `title` (16px).

## 6. Trạng thái file

- `src/styles/tokens.css` — mới, không import ở đâu (theo constraint không được sửa `main.tsx`/`index.css`). Khi migrate, thêm `import './styles/tokens.css'` sau `import './index.css'` trong entrypoint.
- `src/lib/ui.tsx` — mới, không được page nào import (theo constraint không sửa `src/pages/*`). Khi migrate từng page, import các component cần từ `../lib/ui`.
- Không file nào đang tồn tại bị sửa. Mọi thay đổi mô tả ở mục 5 là việc cần làm **sau** khi constraint tách file được gỡ.
## 7. Quyết định G1

- Nút **Duyệt** = `Button variant="primary"` violet; **Từ chối** = `Button variant="destructive"`.
- Amber chỉ dành cho trạng thái gate (`Status kind="setup-required"`), không dùng cho action.
- Pane có agent hiển thị quyền agent; không hiển thị badge provider `READ-ONLY` song song.

### Workflow Canvas

- Canvas dùng token dark workbench hiện có; node agent dùng `--hub-node-agent`, node validate dùng `--hub-node-validate`, edge dùng `--hub-edge-normal` hoặc `--hub-edge-selected`.
- Canvas dày và vận hành được: lưới chấm, node card gọn, port trái/phải, cạnh cong, inspector bốn tab. Không thêm runtime, role, contract hoặc run-history giả.
- Trạng thái chạy/lỗi lấy từ backend; node đang chạy dùng accent, node hoàn tất dùng success, lỗi validate/run luôn hiện thành banner có nội dung hành động được.
