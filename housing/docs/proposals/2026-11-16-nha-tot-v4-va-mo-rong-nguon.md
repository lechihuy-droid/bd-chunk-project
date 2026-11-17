# Đề xuất: định nghĩa "nhà tốt" v4, mở rộng nguồn tin và cách crawl

Ngày: 16/11/2026. Trạng thái: **đề xuất để Huy duyệt, chưa triển khai**. Không sửa hay ghi đè các run/policy đã công bố.

Phạm vi kiểm chứng: số liệu trong Phần A được tính lại từ `housing-selection-v3-20261115-walk-filter/listing-data.json`. Thông tin về nguồn bên ngoài (Phần B, C) được kiểm qua tìm kiếm web; môi trường làm việc không mở được trực tiếp trang Nhật, nên **robots.txt và điều khoản sử dụng của từng trang chưa được đọc nguyên văn** — phải kiểm lại ngay trước khi chạy crawler. Các ngưỡng số trong Phần A là mặc định tôi đề xuất, không phải luật hay nhu cầu Huy đã xác nhận.

---

## Phần A — Review quan điểm "nhà tốt" hiện tại

### A1. Hiện tại "nhà tốt" đang được định nghĩa thế nào

Trên giấy có ba lớp: tám nhóm A–H (`CRITERIA.md`), thang 100 điểm 14 mục (`HOUSING-GATES-v1.0`), và checklist J01–J16. Trên dữ liệu thực, chỉ có một định nghĩa đang chạy (`HOUSING-SELECTION-3.0`):

> P1 = trong dải 4.000–5.000万 **và** giá rao ≤ trung vị các tin rao cùng ga **và** đi bộ tới ga ≤ 10 phút.

Mọi thứ còn lại (giao dịch thật, hazard, quỹ sửa chữa, dự án, dân cư) được thiết kế kỹ nhưng chưa có dữ liệu nuôi.

### A2. Điểm nên giữ

- Thiếu dữ liệu ghi "chưa biết", không tự cho 0 điểm và không tự loại.
- Tách tin rao, căn, dự án; tách giá rao với giá giao dịch.
- Không cộng lặp một nguyên nhân (cùng một ga mới không được tính ba lần).
- Checklist G5 theo mốc (trước đề nghị, trước ký/cọc, trước bàn giao).
- Giữ nguyên dữ liệu gốc, có manifest và hash.

### A3. Vấn đề cần sửa

| # | Vấn đề | Bằng chứng trong repo | Hệ quả |
|---|---|---|---|
| 1 | "Nhà tốt" chỉ còn hai tín hiệu | P1 chỉ dùng `asking_signal` và `access_signal` | Không phân biệt được căn tốt với căn rẻ vì có khuyết điểm |
| 2 | So giá rao với giá rao | Peers là tin đang rao, quyền đất của peers phần lớn chưa rõ | Chọn ngược: căn rẻ hơn trung vị thường là tầng thấp, hướng xấu, quỹ yếu. Một nửa P1 xây trước năm 2000 |
| 3 | Đếm tin, không đếm căn | 1.743 tin trong phạm vi gom thô còn khoảng 1.046 nhóm; 353 tin P1 còn khoảng 165 nhóm | Danh sách đọc dài gấp đôi cần thiết; trung vị bị lệch về căn nhiều môi giới đăng |
| 4 | Nhà riêng gần như không được xếp | Nhà cũ: 0 P1, 315/328 ở nhóm U. Nhà mới: 218/258 ở U | Phương pháp so tin cùng ga không hợp với nhà riêng (mỗi lô đất một khác) |
| 5 | Ga chỉ là "≤10 phút hay không" | Không có tuyến, lượng khách, thời gian tới Umeda/Namba | Ga nhỏ một tuyến được coi ngang ga lớn nhiều tuyến |
| 6 | Dữ liệu chi tiết đã thu nhưng không dùng | Phí quản lý/sửa chữa có ở 1.158/1.162 chung cư cũ, không vào ưu tiên | Bỏ phí tín hiệu chất lượng sẵn có |
| 7 | Thiếu trường quan trọng | Không có 取引態様, 総戸数, tầng, hướng trong bất kỳ file nào | Không lọc được tin không mất phí môi giới; không so đúng căn tương đồng |
| 8 | Hazard chưa áp dụng | `hazard_status` chưa xác minh cấp căn | Osaka có chênh lệch lớn giữa vùng vịnh thấp và vùng cao; đây là rủi ro giữ giá 10–20 năm |
| 9 | Nhu cầu cá nhân chưa chốt | `CRITERIA.md` mục 1: chưa chốt diện tích, phòng, nơi làm, trẻ em, xe, mới/cũ | Hệ thống phải giữ 1.753 tin vì không có căn cứ loại |
| 10 | Quy trình nặng hơn kết quả | 5 bản publish, G4 chưa chạy lần nào, `selection_research_stages.json` rỗng | Chưa có căn nào được nghiên cứu sâu |

### A4. Đề xuất v4: năm trụ độc lập, không cộng điểm

> Cập nhật 17/11/2026: phần xếp hạng bằng năm trụ ở mục này đã được thay bằng một tiêu chí duy nhất, xem [HOUSING-SELECTION-4.0](../standards/HOUSING-SELECTION-4.0.md). Bước 0–2 và bước 5 vẫn dùng.

Nguyên tắc: giữ kỷ luật "chưa biết khác với xấu", nhưng hệ thống phải dẫn tới 20–30 **căn** (không phải tin) để đi xem 5–10 căn.

**Bước 0 — Khử trùng về cấp căn trước mọi phép đếm.** Khóa gom ở mục C3.

**Bước 1 — Nhu cầu cứng do Huy chốt (6 câu).** Diện tích tối thiểu; số phòng; ga/khu làm việc và thời gian đi làm tối đa; có cần chỗ xe; chấp nhận nhà cũ đến năm nào; có chấp nhận tự sửa. Câu nào chưa chốt thì không lọc theo câu đó.

**Bước 2 — Loại khách quan (đề xuất mặc định, bật/tắt được).**

| Điều kiện | Lý do | Xử lý |
|---|---|---|
| 再建築不可 | Khó vay, khó bán lại | Loại khỏi danh sách thường |
| Đất thuê (借地権) | Thời hạn và phí ảnh hưởng giá bán sau 10–20 năm | Hàng chờ riêng |
| Đang cho thuê (オーナーチェンジ) | Không vào ở được | Loại |
| Xây trước 1982 (khả năng chuẩn kháng chấn cũ) | Khó vay, khó bán; năm xây chỉ là dấu hiệu, cần hồ sơ xác nhận | Hàng chờ riêng, không trộn với nhà chuẩn mới |

**Bước 3 — Chấm năm trụ, mỗi trụ một trong bốn trạng thái: tốt / trung bình / xấu / chưa biết.** Không cộng thành tổng điểm.

| Trụ | Câu hỏi | Dữ liệu | Có sẵn chưa |
|---|---|---|---|
| V — Giá | Giá rao so với **giao dịch thật** cùng khu, cùng loại, diện tích ±20%, tuổi ±10 năm, trong 2 năm | API reinfolib của MLIT (giá giao dịch và giá thành ước); tin rao đã khử trùng chỉ là phụ | Chưa — việc số 1 |
| L — Vị trí/thanh khoản | Ga mạnh cỡ nào, đi bộ bao lâu, tới Umeda/Namba/Honmachi mất bao lâu | Phút đi bộ (đã có); số tuyến và lượng khách theo ga (reinfolib có lớp dữ liệu ga); bảng thời gian tới trung tâm lập một lần cho khoảng 120 ga | Có một phần |
| Q — Tài sản | Chung cư: tổng số căn, tầng, hướng, phí quản lý + quỹ sửa chữa trên m² so với mức khuyến nghị của MLIT, hình thức quản lý. Nhà riêng: diện tích đất, đường tiếp giáp ≥4m, kết cấu, giá trị đất làm sàn (路線価 × diện tích) | Trang chi tiết SUUMO; 路線価 của cơ quan thuế | Phí đã có; còn lại phải thu thêm |
| R — Rủi ro vị trí | Ngập sông, triều cường, sóng thần, hóa lỏng theo địa chỉ cấp chome | reinfolib (đã cấp các lớp ngập, sạt lở, sóng thần, triều cường qua API); bản đồ Osaka | Chưa |
| C — Chi phí và lối ra | Phí hằng tháng, có mất phí môi giới không (取引態様), tuổi nhà ở năm thứ 10 và 20 | Trang chi tiết SUUMO | Một phần |

**Bước 4 — Quy tắc vào danh sách xem nhà.**

- Vào danh sách: qua bước 1–2, không có trụ nào "xấu" ở Q và R, có "tốt" ở V hoặc L, và tối đa hai trụ "chưa biết".
- Trụ "chưa biết" tạo việc cụ thể (thu trường nào, hỏi ai), không phải lý do xếp thấp.
- Nhà riêng và chung cư xếp riêng, không so chéo.
- Nhà riêng dùng trụ V khác: so với giá trị đất cộng nhà đã khấu hao, không so tin cùng ga.

**Bước 5 — G5 giữ nguyên**, chỉ mở cho căn đã đi xem.

**Nên dừng:** thang 100 điểm G4 (chưa bao giờ có dữ liệu để chạy); việc publish thêm bản mới khi số liệu không đổi; bộ đếm theo URL.

---

## Phần B — Nguồn tin để tăng độ phủ

### B1. Nguồn tin rao

| Nhóm | Nguồn | Giá trị bổ sung so với SUUMO | Đề xuất |
|---|---|---|---|
| Cổng lớn | athome, LIFULL HOME'S, Yahoo!不動産 | Môi giới nhỏ không trả phí SUUMO thường chỉ đăng ở đây | Đo độ trùng trước (mục B3), rồi chọn **một** cổng để crawl |
| Cổng của hiệp hội | 不動産ジャパン; ハトマークサイト (全宅連); ラビーネット (全日) | Tin của môi giới địa phương; hội viên 全日 được tự động đẩy tin sang 不動産ジャパン và ラビーネット | Dùng tay để đối chiếu |
| Trang gộp | ニフティ不動産 | Gộp SUUMO, HOME'S, athome, Yahoo!不動産, アドパーク, ピタットハウス, メジャーセブン, 住まい探しの窓口 | Công cụ nhanh nhất để đo SUUMO thiếu bao nhiêu |
| Môi giới lớn | 三井のリハウス, 住友不動産ステップ, 東急リバブル, 野村の仲介+, 近鉄不動産, 阪急阪神不動産, 大京穴吹不動産, 福屋不動産販売, 長谷工の仲介 | Tin đăng trên trang riêng trước khi lên cổng; tin "chỉ dành cho hội viên" | Đăng ký hội viên và bật email báo tin mới; không crawl |
| Người bán là công ty (không mất phí môi giới) | Chủ đầu tư chung cư mới (メジャーセブン và trang từng dự án); nhà xây sẵn (nhóm 飯田, オープンハウス, フジ住宅); mua lại–bán lại (レジデンシャル不動産, リプライス, インテリックス, スター・マイカ, 大京穴吹) | Chính là hướng "không qua trung gian" | Lập danh sách theo dõi bằng tay; đồng thời lọc 取引態様 = 売主/代理 trong dữ liệu SUUMO |
| Ngách | Đấu giá tòa án (BIT), 家いちば, 空き家バンク | Giá thấp nhưng khó vay, rủi ro cao | Ngoài phạm vi giai đoạn này |

Ghi chú: カチタス đứng đầu thị trường mua lại–bán lại (khoảng 5.600 căn/năm) nhưng chủ yếu là nhà riêng vùng ven, ít liên quan Osaka-shi dải 4.000–5.000万.

### B2. Nguồn bằng chứng (không phải tin rao)

| Nguồn | Dùng cho | Cách lấy |
|---|---|---|
| 不動産情報ライブラリ (reinfolib, MLIT) | Giá giao dịch thật, giá thành ước từ REINS (đã làm mờ để không lộ từng căn), lớp hazard, quy hoạch, dữ liệu ga | API chính thức, phải đăng ký lấy khóa |
| 近畿レインズ | Báo cáo tháng/quý về số giao dịch và đơn giá theo khu | Tải PDF |
| マンションレビュー | Lịch sử giá rao theo từng tòa, giá ước tính | Xem tay, đăng ký miễn phí để bỏ giới hạn |
| 路線価 (cơ quan thuế), 地価公示 | Giá trị đất làm sàn cho nhà riêng | Tra theo địa chỉ; 地価公示 có trong reinfolib |
| Bản đồ thiên tai Osaka | Đối chiếu trụ R | Tra tay cho các căn vào danh sách |

### B3. Đo độ trùng trước khi viết crawler thứ hai

1. Chọn 3 quận × 2 loại (chung cư cũ, nhà cũ), dải 4.000–5.000万.
2. Trên ニフティ不動産, lấy 30 căn mỗi ô và ghi nguồn đăng.
3. Đếm bao nhiêu căn **không** có trên SUUMO.
4. Nếu dưới 15% thì không cần crawler thứ hai, chỉ cần email báo tin. Nếu trên 15% thì crawl thêm cổng có nhiều tin riêng nhất.

Lý do: mỗi crawler thêm là thêm parser, thêm khử trùng chéo nguồn và thêm rủi ro điều khoản. Chưa có số đo thì chưa nên xây.

---

## Phần C — Cách crawl

### C1. Thứ tự ưu tiên

1. **API reinfolib** — chính thức, không rủi ro điều khoản, lấp trụ V và R.
2. **Thu thêm trang chi tiết SUUMO cho khoảng 1.750 tin trong phạm vi** — lấp trụ Q, C và 取引態様.
3. **Crawl tăng dần hằng ngày trên SUUMO** — có lịch sử giá và số ngày rao.
4. **Một cổng thứ hai**, chỉ khi B3 cho thấy đáng.

### C2. API reinfolib

Đã xác nhận qua tìm kiếm:

- Phải đăng ký sử dụng; API cũ của 土地総合情報システム đã dừng cuối tháng 3/2024.
- Xác thực bằng header `Ocp-Apim-Subscription-Key`.
- Giá giao dịch: `https://www.reinfolib.mlit.go.jp/ex-api/external/XIT001`, tham số `year` (bắt buộc), `area` (mã tỉnh), `city` (mã quận/thành phố).
- Kết quả gồm loại tài sản, tổng giá, bố trí phòng, diện tích, năm xây, công năng, kỳ giao dịch; **không có tọa độ**, vị trí chỉ tới cấp khu.
- MLIT đã bổ sung các lớp ngập (quy mô tối đa), sạt lở, sóng thần, triều cường vào API; dữ liệu gốc là 国土数値情報 nên có thể khác bản đồ hiển thị.

Chưa xác nhận, phải đọc tài liệu chính thức khi triển khai: tham số tách giá giao dịch với giá thành ước, giới hạn tần suất, câu ghi nguồn bắt buộc, điều kiện phát hành lại dữ liệu. Mã quận Osaka-shi là 27102–27128.

### C3. Kiến trúc dữ liệu (mở rộng cái đã có)

```
nguồn → HTML gốc (bất biến, có hash) → parser theo nguồn → bảng tin chuẩn hóa (thêm cột source)
      → gom về căn (property_id) → ghép reinfolib + hazard → chấm năm trụ
```

Khóa gom căn, **không dùng giá** (cùng một căn các môi giới có thể rao khác giá):

- Chung cư: tên tòa đã chuẩn hóa + diện tích (0,01 m²) + tầng + bố trí phòng. Thiếu tên tòa thì dùng địa chỉ cấp chome + năm/tháng xây + diện tích.
- Nhà riêng: địa chỉ cấp chome + diện tích đất + diện tích nhà + năm/tháng xây.
- Không đủ trường thì giữ tách và gắn nhãn "nghi trùng"; không tự gộp.

Trường cần thu thêm từ trang chi tiết: 取引態様, tên công ty đăng, 総戸数, tầng/tổng tầng, hướng, phí quản lý, quỹ sửa chữa, hình thức quản lý, kết cấu, quyền đất, đường tiếp giáp, 用途地域, hiện trạng, ngày bàn giao, ngày cập nhật tin.

Crawl tăng dần: mỗi ngày chỉ đọc trang danh sách sắp theo tin mới, chỉ tải trang chi tiết của tin mới hoặc đổi giá. Lưu `first_seen`, `last_seen` và lịch sử giá. Từ đó có số ngày rao và số lần giảm giá — tín hiệu đàm phán mà một lần chụp không cho được.

### C4. Kỹ thuật và giới hạn

- Ưu tiên tải HTML tĩnh; kiểm tra trang có JSON nhúng (JSON-LD) trước khi viết parser theo thẻ HTML. Chỉ dùng trình duyệt tự động khi nội dung bắt buộc phải render.
- Một luồng, cách nhau ít nhất 3 giây, có cache, dừng hẳn khi gặp 403/429 hoặc trang thử thách. Không đăng nhập, không proxy, không giả danh, không gọi API nội bộ của trang.
- Đọc robots.txt và điều khoản của từng trang ngay trước mỗi đợt chạy và lưu lại bản đã đọc.
- Vi phạm điều khoản là rủi ro hợp đồng (bị chặn, bị đòi bồi thường); gây tải lớn có thể thành vấn đề hình sự. Ảnh và đoạn mô tả có bản quyền; dữ kiện như giá, diện tích thì không, nhưng cả bộ dữ liệu vẫn có thể được bảo vệ. Đây không phải tư vấn pháp lý.
- **Không phát hành lại dữ liệu thô ra công khai.** Hiện repo đang đưa hơn 11.000 tin SUUMO lên GitHub Pages. Đề xuất: chuyển repo/Pages sang riêng tư, hoặc bản công khai chỉ còn URL và các trường tự tính.

---

## Phần D — Thứ tự việc đề xuất

| # | Việc | Ai làm | Kiểm tra xong |
|---|---|---|---|
| 1 | Chốt 6 nhu cầu cứng và các điều kiện loại ở bước 2 | Huy | Có file cấu hình được duyệt |
| 2 | Quyết định về việc công khai dữ liệu SUUMO | Huy | Repo/Pages đã đổi hoặc Huy chấp nhận giữ nguyên |
| 3 | Đăng ký khóa API reinfolib | Huy | Có khóa trong `.env` |
| 4 | Khử trùng về cấp căn | Codex | Số căn thay số tin; thêm tin trùng không đổi kết quả |
| 5 | Thu thêm trang chi tiết cho tin trong phạm vi | Codex | Tỷ lệ có 取引態様, 総戸数, tầng, hướng theo từng loại |
| 6 | Ghép giá giao dịch và hazard từ reinfolib | Codex | Mỗi căn có số mẫu giao dịch và lớp hazard, hoặc lý do thiếu |
| 7 | Chấm năm trụ, xuất danh sách xem nhà | Codex viết, Claude review | 20–30 căn, mỗi căn có lý do và việc còn thiếu |
| 8 | Đo độ trùng với cổng khác (B3) | Huy hoặc Claude, làm tay | Có tỷ lệ tin SUUMO thiếu |

Việc 1–3 không phụ thuộc code và mở khóa phần còn lại.

---

## Nguồn tham khảo (qua tìm kiếm, ngày 16/11/2026)

- API reinfolib, tổng quan và XIT001: https://www.issoh.co.jp/md/tech/2385 ; https://qiita.com/AzukiImo/items/da60c0e5872c027829e7
- MLIT, bổ sung lớp phòng chống thiên tai vào API reinfolib: https://www.mlit.go.jp/report/press/content/001969981.pdf
- MLIT, đưa giá thành ước REINS vào thư viện công khai: https://www.mlit.go.jp/tochi_fudousan_kensetsugyo/const/content/001482929.pdf
- ニフティ不動産, danh sách trang được gộp: https://myhome.nifty.com/brand
- 全日, liên kết tự động sang 不動産ジャパン và ラビーネット: https://www.zennichi.or.jp/wp-content/uploads/2024/02/5448acb6013f6978ea1001d89961f8cb.pdf
- 取引態様 và phí môi giới: https://www.ieshil.com/columns/16/
- Xếp hạng mua lại–bán lại 2025: https://e-estate.jp/media/?p=14952 ; quy mô thị trường: https://www.yano.co.jp/press/press.php/003955
- マンションレビュー: https://www.mansion-review.jp/mansion/souba/
- 近畿レインズ, báo cáo thị trường: https://www.kinkireins.or.jp/
- Tính hợp pháp của scraping tại Nhật: https://monolith.law/corporate/scraping-datacollection-law ; https://www.bengo4.com/c_1015/c_17/c_1263/m_1041514/
