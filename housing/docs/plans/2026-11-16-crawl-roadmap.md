# Lộ trình crawl cho subagent — đợt 3

Ngày: 16/11/2026. Trạng thái: **chờ Huy duyệt, chưa chạy**. Kế thừa [đề xuất v4](../proposals/2026-11-16-nha-tot-v4-va-mo-rong-nguon.md) và các ràng buộc trong [kế hoạch 03/11](2026-11-03-v2-gate-execution-plan.md) (phân vai Terra/Luna, tối đa 3 subagent cùng lúc, không sửa dữ liệu lịch sử).

Môi trường viết tài liệu này không mở được trang Nhật. Các điểm đánh dấu **[kiểm khi chạy]** là giả định phải xác nhận ở bước đầu của lane tương ứng; sai thì lane dừng và báo, không tự tìm đường vòng.

## 1. Đầu vào đã có (không hỏi lại Huy)

| Đầu vào | Giá trị | Nguồn |
|---|---|---|
| Khu vực | Osaka-shi, 24 quận | `CRITERIA.md` mục 1 |
| Loại | Nhà riêng và chung cư, mới và cũ | `CRITERIA.md` mục 1 |
| Giá | 4.000–5.000万, gồm hai đầu, giá chính xác của một căn | `HOUSING-GATES-v1.0` G1-03 |
| Mục đích | Để ở, giữ 10–20 năm, ưu tiên giữ giá và bán lại | Bộ tiêu chuẩn Osaka |
| Quyền đất | Ưu tiên sở hữu đất; đất thuê và nhà liền kề xem riêng | Bộ tiêu chuẩn Osaka |
| Loại trừ | Không xây lại được; đang cho thuê không bàn giao trống | Bộ tiêu chuẩn Osaka, `CRITERIA.md` mục 6 |
| Phụ | Trường học, đi làm, tiện ích chỉ để phân định khi ngang nhau | Bộ tiêu chuẩn Osaka |
| Đi bộ tới ga, khoảng giá hẹp hơn | Bộ lọc Huy tự chỉnh trên giao diện, không cố định | Bản 15/11 |
| Diện tích, số phòng, tuổi nhà, chỗ xe | **Chưa có** → không lọc, chỉ thu và hiển thị | — |

## 2. Nguyên tắc chia việc

- **Một máy chủ nguồn chỉ một subagent, một luồng.** Song song là giữa các nguồn khác nhau, không phải nhiều agent cùng đánh SUUMO.
- Mỗi lane bắt đầu bằng việc đọc và lưu robots.txt cùng điều khoản của nguồn. Nguồn cấm thì lane dừng.
- Cách nhau ít nhất 3 giây. Gặp 401/403/429 hoặc trang thử thách thì dừng cả lane. Không đăng nhập, không proxy, không gọi API nội bộ.
- HTML gốc lưu bất biến kèm hash và thời điểm tải, **nằm ngoài thư mục công khai**.
- Mỗi lane có trần số request. Hết trần thì dừng và báo phần còn thiếu, không tự nới.
- Người viết không tự review. Agent chính kiểm đối soát trước khi chuyển đợt.

## 3. Các đợt

### Đợt 0 — Không gọi mạng

| Lane | Ai | Việc | Đầu ra | Điều kiện xong |
|---|---|---|---|---|
| 0A Đọc lại cache | Luna-Data | Parse lại trang chi tiết đã lưu của khoảng 1.750 tin trong phạm vi để lấy thêm: 取引態様, tên công ty đăng, 総戸数, tầng/tổng tầng, hướng, hình thức quản lý, ngày cập nhật tin | `detail-fields.csv` kèm lý do thiếu theo từng trường | Báo tỷ lệ có dữ liệu theo trường × loại nhà; đối chiếu tay 10 tin |
| 0B Gom về căn | Terra thiết kế, Luna chạy | Gom tin thành căn theo khóa ở mục C3 của đề xuất v4 (không dùng giá) | `properties.csv`, `listing-property-links.csv` | Thêm tin trùng không làm đổi số căn; tin nghi trùng giữ tách có nhãn |

Lý do có đợt này: trang chi tiết của tin trong phạm vi đã được tải ở lần kiểm link 02–03/11, nên các trường còn thiếu lấy được ngay mà không tốn request nào.

### Đợt 1 — Ba lane song song, ba nguồn khác nhau

| Lane | Ai | Nguồn | Việc | Trần request | Đầu ra |
|---|---|---|---|---|---|
| 1S Làm mới SUUMO | Luna-Data | SUUMO | (a) Trang danh sách 4 loại × 24 quận, dùng bộ lọc giá 4.000–5.000万 của chính trang **[kiểm khi chạy]**, sắp theo tin mới. (b) Trang chi tiết chỉ cho tin mới hoặc đổi giá so với 02/11. (c) Thử lại 6 tuyến chung cư mới còn thiếu | 600 | Snapshot mới; bảng `first_seen`, `last_seen`, lịch sử giá; danh sách tin đã biến mất |
| 1M Dữ liệu MLIT | Luna-Data (instance khác) | 不動産情報ライブラリ, 国土数値情報 | (a) Tải CSV giá giao dịch của Osaka-fu, 8 quý gần nhất, từ trang tải về công khai **[kiểm khi chạy: không cần khóa API]**. (b) Tải lớp ngập sông, triều cường, sóng thần của Osaka-fu | 40 | `transactions.csv` lọc Osaka-shi; các file lớp hazard gốc kèm ngày phát hành |
| 1C Đo độ phủ | Terra-Research | ニフティ不動産 | Lấy mẫu 3 quận × 2 loại (chung cư cũ, nhà cũ), chỉ trang danh sách, ghi nguồn đăng của từng căn rồi khớp với bảng căn ở 0B | 40 | `coverage-sample.csv`; tỷ lệ căn không có trên SUUMO, tách theo nguồn |

Lane 1S chỉ lấy tin trong dải giá, không lấy lại cả 11.000 tin. Trụ giá của v4 dựa trên giao dịch thật từ lane 1M, nên không cần cả kho tin rao làm mẫu so sánh nữa.

**Cổng quyết định sau đợt 1 (agent chính):**

- 1C cho thấy SUUMO thiếu dưới 15% căn → bỏ lane 2P.
- Thiếu từ 15% trở lên → mở lane 2P cho đúng một cổng có nhiều căn riêng nhất.
- 1M không tải được CSV công khai → lúc đó mới cần Huy đăng ký khóa API.

### Đợt 2 — Tối đa ba lane, tùy kết quả đợt 1

| Lane | Ai | Nguồn | Việc | Trần request | Đầu ra |
|---|---|---|---|---|---|
| 2D Dự án và người bán trực tiếp | Luna-Data | SUUMO | Trang chi tiết của 309 tin dự án trong hàng chờ: bảng giá từng loại căn, 取引態様, ngày bàn giao. Chạy sau khi 1S xong vì cùng nguồn | 350 | `projects-units.csv`; dự án có căn rơi vào 4.000–5.000万 |
| 2P Cổng thứ hai (có điều kiện) | Terra viết parser, Luna chạy | Cổng được chọn ở cổng quyết định | Trang danh sách có lọc giá, 4 loại × 24 quận; trang chi tiết chỉ cho căn không khớp với bảng căn SUUMO | 800 | Bảng tin chuẩn hóa có cột `source`; số căn mới thêm được |
| 2G Ghép vị trí | Terra-Research | Không gọi mạng | Gắn mỗi căn với giao dịch cùng khu/loại/diện tích ±20%/tuổi ±10 năm; gắn lớp hazard theo địa chỉ cấp chome | 0 | Mỗi căn có số mẫu giao dịch, trung vị, và mức hazard, hoặc lý do thiếu |

### Đợt 3 — Tổng hợp và kiểm

| Lane | Ai | Việc | Điều kiện xong |
|---|---|---|---|
| 3A Chấm năm trụ | Terra-Engine | Áp bước 2–4 của v4 trên bảng căn | Mỗi căn có 5 trạng thái kèm bằng chứng; chung cư và nhà riêng xếp riêng |
| 3B Review độc lập | Terra-Reviewer | Kiểm 20 căn mẫu, đặc biệt nhà riêng, đất thuê, căn sát ngưỡng | Không có căn bị loại vì thiếu dữ liệu; không có căn trùng trong danh sách |
| 3C Xuất danh sách | Luna-View | Danh sách xem nhà 20–30 căn; cột riêng cho căn không mất phí môi giới | Bản công khai không chứa dữ liệu thô của nguồn |

### Sau đó — chạy định kỳ

Mỗi ngày một lượt lane 1S rút gọn (chỉ trang danh sách tin mới và trang chi tiết của tin mới/đổi giá), ước khoảng 50–100 request. Mỗi quý tải lại CSV giao dịch. Việc bật lịch chạy cần Huy duyệt riêng.

## 4. Ước lượng

| Đợt | Request | Thời gian chạy ở 3 giây/request |
|---|---:|---|
| 0 | 0 | — |
| 1 | tối đa 680 | khoảng 30 phút cho lane dài nhất |
| 2 | tối đa 1.150 | khoảng 40 phút cho lane dài nhất |
| Hằng ngày | 50–100 | dưới 5 phút |

Đây là trần, không phải dự báo; lần crawl 02/11 dùng 694 request cho toàn bộ catalog.

## 5. Có cần đăng ký API không

**Chưa cần.** API của MLIT chỉ là cách lấy tiện hơn cho cùng dữ liệu; với phạm vi một thành phố, tải file là đủ:

- Giá giao dịch: trang 不動産情報ライブラリ có chức năng tải CSV theo tỉnh và kỳ **[kiểm khi chạy]**.
- Lớp thiên tai: tải từ 国土数値情報, cũng là dữ liệu gốc mà API dùng.

Chỉ nên đăng ký khi lane 1M không tải được file công khai, hoặc khi đã bật chạy định kỳ và muốn tự động hóa việc cập nhật hằng quý.

## 6. Việc cần Huy quyết trước khi chạy

1. Duyệt lộ trình này (hoặc chỉ duyệt đợt 0 và 1 trước).
2. Dữ liệu SUUMO đang công khai trên GitHub Pages: giữ, chuyển riêng tư, hay rút gọn bản công khai. Lane 3C phụ thuộc quyết định này.
