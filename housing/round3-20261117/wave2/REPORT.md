# Kết quả đợt 2 — crawl 6 trang ngoài SUUMO

Chạy ngày 17/11/2026 từ máy chủ đám mây. 296 request tới 6 trang, mỗi trang một luồng, cách nhau hơn 3 giây; không trang nào chặn. Nhật ký: [requests.log](requests.log). Số liệu tổng hợp: [summary.json](summary.json).

**Dữ liệu từng tin của 6 trang này không nằm trong repo.** Điều khoản của các trang cấm đăng lại nội dung, và repo đang công khai. File dữ liệu được gửi riêng cho Huy; repo chỉ giữ code, nhật ký URL và số tổng hợp.

## Điều khoản và robots.txt

| Trang | robots.txt | Điều khoản |
|---|---|---|
| Yahoo!不動産 | Cho phép đường dẫn tìm kiếm có `?page=`; đã tuân theo | **Chưa đọc được** (nằm ở tên miền khác, môi trường chặn) |
| 住友不動産ステップ | Cho phép đường dẫn đã dùng | Đã mở trang "ご利用について", không thấy điều khoản về truy cập tự động hay sao chép |
| 三井のリハウス | Cho phép | **Chưa tìm được trang điều khoản** |
| 野村の仲介+ | Cho phép | Cấm sao chép, đăng lại nội dung khi chưa được phép; cấm gây tải quá mức cho máy chủ |
| 東急リバブル | Cho phép | Cấm dùng lại, sao chép dữ liệu trên trang khi chưa được phép |
| 大京穴吹不動産 | Cho phép | Cấm dùng, đăng lại, sao chép khi chưa được phép |

Không trang nào trong số đã đọc nêu riêng việc cấm truy cập tự động. Cả ba trang đọc được đều cấm sao chép và đăng lại, nên dữ liệu chỉ nên dùng nội bộ cho việc tìm nhà. Đây không phải tư vấn pháp lý.

## Số tin thu được (trong dải 4.000–5.000万, Osaka-shi)

| Trang | Request | Chung cư cũ | Nhà cũ | Nhà mới | Tổng | Độ đầy đủ |
|---|---:|---:|---:|---:|---:|---|
| Yahoo!不動産 | 17 | 193 | 86 | 122 | 401 | Trang báo 194 / 88 / 134 |
| 三井のリハウス | 81 | 140 | 16 | 0 | 156 | Đọc được 1.271/1.318 thẻ chung cư mọi giá (96%); nhà riêng chỉ lấy loại 戸建 |
| 野村の仲介+ | 5 | 117 | 15 | 0 | 132 | Khớp đúng số trang báo (117 và 15) |
| 東急リバブル | 93 | 103 | 23 | 3 | 129 | Đọc hết 1.008 thẻ mọi giá rồi lọc |
| 住友不動産ステップ | 48 | 42 | 17 | — | 59 | Khớp đúng số trang báo ở cả 29 trang có kết quả |
| 大京穴吹不動産 | 52 | 25 | 2 | 0 | 27 | Đọc được 230/269 thẻ mọi giá (86%) |
| **Tổng** | **296** | **620** | **159** | **125** | **904** | |

Chưa lấy: chung cư mới ở mọi trang; nhà mới ở ステップ; nhà liền kề (テラスハウス) ở リハウス.

## So với SUUMO

904 tin gom lại thành **594 căn**. Khớp với SUUMO theo địa chỉ cấp chome + diện tích (và quận + diện tích + năm xây khi địa chỉ ghi khác độ chi tiết).

| Kết quả so với snapshot SUUMO 02/11 | Chung cư cũ | Nhà cũ | Nhà mới | Tổng |
|---|---:|---:|---:|---:|
| Có trên SUUMO, trong dải giá | 300 | 89 | 37 | 426 |
| Có trên SUUMO nhưng ở giá khác (ngoài dải) | 19 | 5 | 3 | 27 |
| **Không có trên SUUMO** | **49** | **36** | **56** | **141** |
| Tổng | 368 | 130 | 96 | 594 |

Theo nguồn (đếm theo tin): Yahoo! có 108 tin không có trên SUUMO, リハウス 16, 野村 12, リバブル 10, ステップ 10, 大京 4. Chỉ 8 trong 141 căn mới xuất hiện ở từ hai trang trở lên.

### Cách đọc con số 141

Con số này là **trần trên**, không phải số căn SUUMO thật sự bỏ sót:

1. **Snapshot SUUMO đã 15 ngày tuổi.** Tin đăng sau 02/11 đều bị tính là không có.
2. **Nhà mới (56 căn) bị thổi phồng.** SUUMO đăng nhiều khu nhà xây sẵn dưới dạng tin dự án có giá khoảng; 309 tin như vậy đang nằm ở hàng chờ riêng và không tham gia phép khớp. Nhiều căn trong 56 căn này có thể là lô trong các dự án đó.
3. **Chung cư cũ (49) và nhà cũ (36) đáng tin hơn**, nhưng vẫn chịu ảnh hưởng của điểm 1.
4. Phép khớp dựa vào diện tích ghi giống hệt nhau. Nếu hai trang ghi diện tích lệch nhau vài phần trăm mét vuông thì căn bị tính là mới.

27 căn "có trên SUUMO ở giá khác" là nhóm đáng xem: cùng khu, cùng diện tích, nhưng SUUMO ghi giá cao hơn dải (ví dụ 4.980万 ở trang môi giới, 5.380万 trên SUUMO). Có thể là căn đã giảm giá, hoặc căn khác tầng cùng tòa.

## Việc tiếp theo

1. Làm mới SUUMO (trang danh sách trong dải giá và 309 tin dự án) rồi chạy lại `tools/merge_sources.py` để có con số lọt thật.
2. Chạy bốn trang bị chặn từ máy của Huy theo [brief](../../docs/plans/2026-11-17-brief-local-crawl.md).
3. Đọc điều khoản Yahoo! và リハウス.
4. Với các căn không có trên SUUMO còn đáng quan tâm: tải trang chi tiết để lấy loại người bán, phí quản lý, quyền đất.
