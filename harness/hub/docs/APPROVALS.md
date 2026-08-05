# Danh sách chờ duyệt — Harness Hub

Ngày: 2026-07-29 · Trạng thái: **ĐÃ DUYỆT TOÀN BỘ 2026-07-29** — duyệt hết theo đề xuất; `OD-05` chốt riêng: log giữ **7 ngày**, chỉnh được trong Settings.

Gồm 2 nguồn:
- **OD/RD** — quyết định treo sẵn trong `harness_hub_backend_docs_v0_1/02_REQUIREMENTS_BASELINE.md` §12 (13 mục)
- **P** — phát sinh trong đợt build 2026-07-28/29 (5 mục)

Cột "Chặn gì" cho biết duyệt xong thì mở khoá được việc gì. Cột "Đề xuất" là khuyến nghị của tôi kèm lý do — duyệt nghĩa là đồng ý với nó, không đồng ý thì ghi khác.

---

## Nhóm 1 — Chặn việc làm được ngay

| # | Quyết định | Đề xuất | Vì sao |
|---|---|---|---|
| **P1** | Hook có được chạy shell không? Bạn đã đồng ý 2026-07-28 nhưng tôi gate sau R9 Phase 1 — nay R9 P1 xong. | **Bật, nhưng bắt buộc qua đường gitjobs** (worktree riêng + `shell=False` + lệnh cố định + cổng diff) | Spawn thẳng từ hook là bề mặt thực thi mới không có lớp cách ly nào. Đi qua gitjobs thì dùng lại toàn bộ containment đã có |
| **P2** | `accept_candidate` tự điền reviewer/rationale mặc định khi caller không gửi | **Bắt buộc reviewer thật**, bỏ giá trị mặc định | Hiện đúng hình thức `REQ-OPS-02` nhưng sai tinh thần: provenance tự bịa thì không phải provenance |
| **RD-01** | Journal bất biến + projection làm nguồn phục hồi (`REQ-RUN-04/05`) | **Duyệt** | Lớp Runtime state là lớp mỏng nhất còn lại. Không có journal thì crash giữa chừng để lại trạng thái không xác định |
| **RD-07** | Vòng đời tin cậy / lưu giữ / thu hồi cho skill và memory | **Duyệt** | `REQ-WF-06` vừa làm nửa đầu (ghim hash skill). Nửa sau là memory — hiện accept xong là vĩnh viễn |
| **OD-02** | Version lạc quan để trong `run.json` hay ledger riêng | **`run.json`** | Hub là file-backed 1 process; ledger riêng thêm file cần đồng bộ mà chưa có nhu cầu |

## Nhóm 2 — Chặn việc sau, quyết sớm thì đỡ phải sửa lại

| # | Quyết định | Đề xuất | Vì sao |
|---|---|---|---|
| **OD-01 / REQ-API-05** | Giữ `/api` hay đổi `/api/v1` | **Giữ `/api`**, version nằm ở header `X-Schema-Version` đã có | Đổi prefix bắt sửa toàn bộ `web-v3` mà không thêm khả năng nào; header đã giải quyết đúng vấn đề |
| **OD-04 / REQ-ART-04** | Artifact: manifest theo run hay index nội dung tập trung | **Giữ theo run** | Chưa có nhu cầu dedupe. Index tập trung kéo theo retention + backup + migration |
| **OD-05 / REQ-OPS-05** | Chính sách lưu giữ/xoá runtime, event, artifact, log | **Cần bạn quyết, tôi không đề xuất được** | Phụ thuộc bạn muốn giữ lịch sử bao lâu và có dữ liệu nhạy cảm nào trong đó không |
| **RD-02 / REQ-DATA-04** | Cam kết độ bền / RPO / RTO | **Không cam kết gì**, ghi rõ là best-effort | `REQ-RUN-06` đang cấm tuyên bố zero-loss. Cam kết mà không đo được là nói quá |
| **RD-08** | Chỉ số kỹ thuật là mục tiêu release hay chỉ tham khảo | **Tham khảo** | Chưa có baseline đo đạc nào |

## Nhóm 3 — Hạng mục lớn, duyệt là cam kết nhiều tuần

| # | Quyết định | Đề xuất | Vì sao |
|---|---|---|---|
| **RD-04 / OD-03 / REQ-SEC-06** | Đầu tư controlled Windows executor (Gate D) hay giữ read-only ít bảo đảm | **Giữ read-only** | Đây là hạng mục lớn nhất trong bộ. Baseline tự nói không được tuyên bố sandbox production. Chạy local 1 người dùng thì lợi ích chưa tương xứng |
| **RD-05** | Cơ chế kiểm soát egress (WFP / broker / worker cách ly) | **Hoãn** | Chỉ cần khi có tuyên bố egress/isolation. Hiện không có |
| **RD-06 / REQ-GOV-07** | Đưa MCP vào lộ trình gần | **Hoãn** | Cần tool kernel có kiểu + registry + admission + test SSRF trước. R9 Phase 2 mới là mầm đầu tiên của tool kernel |
| **RD-03 / REQ-CHAT-06** | Chốt bộ provider cho Gate C + smoke test thật | **Hoãn** | Cần credential và chính sách dữ liệu; test hiện toàn bộ là mock, cố ý |
| **REQ-GIT-04** | Git job giữ riêng hay gộp vào Executor Port | **Giữ riêng** | BD04 cố ý tách. Gộp vào lúc này là kéo containment của gitjobs vào một lớp chưa đủ chín |
| **REQ-RUN-09** | Session xuyên provider + memory chia sẻ | **Hoãn** | Chưa có nhu cầu thực tế |

## Nhóm 4 — Quản trị tài liệu

| # | Quyết định | Đề xuất | Vì sao |
|---|---|---|---|
| **P3** | Duyệt `02_REQUIREMENTS_BASELINE.md` từ `In Review` → `Approved` | **Duyệt** | Theo luật §5 của chính nó, `In Review` chỉ được prototype. Ta đã code theo nó rồi, nên hoặc duyệt, hoặc thừa nhận đang vi phạm quy trình của chính mình |
| **P4** | 6 doc rời trong `harness/hub/docs/` chưa gắn trạng thái. `workspace.md` tả route `#/workspace` **đã không còn tồn tại** | **Đánh dấu `workspace.md` là Superseded**, 5 cái còn lại gắn trạng thái | Doc mô tả thứ không tồn tại thì tệ hơn không có doc |
| **P5** | Đang có 2 quy trình: `SDD-toolkit/` (CLAUDE.md tuyên bố chính thức) và bộ baseline | **Chọn baseline, hạ SDD-toolkit xuống template dùng cho project khác** | Giữ 2 quy trình cho cùng 1 repo là nguồn mâu thuẫn thường trực |

---

## Kết quả — đã thi công

| # | Trạng thái |
|---|---|
| P1 hook chạy shell | **XONG** — đi qua `gitjobs.create_hook_job` + `approve`; `services/hooks.py` không import `subprocess` |
| P2 reviewer thật | **XONG** — `accept_candidate` từ chối khi thiếu `accepted_by`/`reason` |
| RD-01 + OD-02 | **XONG** — `state_version` trong `run.json`, lock theo run, bản ghi idempotency, `transactions.jsonl` có checksum, tail hỏng bị cách ly |
| RD-07 | **XONG** — memory revoked/expired bị loại khỏi `list_memory()` nên ngừng được dùng thật, không chỉ gắn cờ |
| OD-05 | **XONG** — mặc định 7 ngày trong `config.py`, sửa được ở Settings; quét bỏ qua run đang chạy, **không đụng** audit evidence và artifact |
| Nhóm 2 (OD-01, OD-04, RD-02, RD-08) | Quyết định là **giữ nguyên** — không sinh việc, ghi lại để lần sau không bàn lại |
| Nhóm 3 (RD-03/04/05/06, OD-03, REQ-GIT-04, REQ-RUN-09) | **Hoãn** theo đề xuất |
| P3 | Baseline coi như **Approved** kể từ 2026-07-29. Không sửa file trong `harness_hub_backend_docs_v0_1/` — đó là bản drop ngoài; việc duyệt ghi ở đây |
| P4 | `workspace.md` gắn nhãn Superseded |
| P5 | `SDD-toolkit/` hạ xuống template dùng cho project khác; repo này theo bộ baseline |

## Giới hạn còn lại, nói rõ để không ai hiểu nhầm

`REQ-RUN-06` vẫn nguyên hiệu lực. Việc có journal **không** đồng nghĩa:
- **không** đảm bảo zero-loss khi mất điện
- lock là **in-process**, không điều phối được 2 server
- recovery **không** replay side effect ra bên ngoài

`REQ-SEC-08` cũng vẫn nguyên: không được tuyên bố hành vi CLI cùng user, provider adapter, child scope, memory, skill, tool là production-safe.
