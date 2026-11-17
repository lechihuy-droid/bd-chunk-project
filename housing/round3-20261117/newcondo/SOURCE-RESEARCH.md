# Chung cư mới — nghiên cứu nguồn và độ phủ

Chạy ngày 17/11/2026 từ máy chủ đám mây. 38 request (5 robots.txt + 33 trang), mỗi nguồn một luồng, cách nhau hơn 3 giây. Nhật ký: [requests.log](requests.log). Số tổng hợp: [source-coverage.json](source-coverage.json). Script: [`newcondo_sources.py`](../tools/newcondo_sources.py).

Bảng từng dự án không nằm trong repo (cùng lý do với đợt 2: điều khoản các trang cấm đăng lại, repo đang công khai). File được gửi riêng cho Huy.

Phạm vi: dự án chung cư mới ở Osaka-shi, mọi mức giá, chỉ trang danh sách.

## 1. Nguồn đã xét

| Nguồn | Loại | Truy cập từ đám mây | robots.txt | Dự án Osaka-shi | Thông tin trên trang danh sách |
|---|---|---|---|---:|---|
| Yahoo!不動産 | Cổng quảng cáo | Được | Cho phép danh sách và trang dự án; **cấm** trang 物件概要 (`/summary/`) và bảng căn (`/layoutlist/`) | 72 (trang báo 75 mục) | Tên, địa chỉ, ga, ngày vào ở, số tầng, tổng số căn, chủ đầu tư, đợt bán, khoảng giá, bố trí phòng, diện tích |
| SUUMO | Cổng quảng cáo | Được | Cho phép | 74 dự án (trong 196 tin) + 13 tòa chỉ có tin bán lại căn chưa ở | Tên, địa chỉ tới chome, ga, ngày bàn giao, khoảng giá theo đợt, **giá của tối đa 3 loại căn** |
| 住まいサーフィン | Cơ sở dữ liệu chung cư, không sống bằng quảng cáo dự án | Được | Cho phép đường dẫn đã dùng | 57 | Tên, địa chỉ, tổng số căn, tháng mở bán, khoảng giá thực bán |
| メジャーセブン | Trang chung của 7 chủ đầu tư lớn | Được | Cho phép tất cả | 13 | Tên, địa chỉ, khoảng giá, chủ đầu tư |
| マンションコミュニティ | Diễn đàn theo từng dự án | **Bị chặn** (HTTP 202, thân rỗng) | Không đọc được | — | — |
| ニフティ不動産 | Trang gộp các cổng | **Bị chặn** (403) | Không đọc được | — | — |
| athome, LIFULL HOME'S | Cổng quảng cáo | Bị chặn (đã biết từ đợt 1) | — | — | — |
| Trang riêng của từng chủ đầu tư | Nguồn gốc | Chưa xét | — | — | — |

Chưa đọc điều khoản sử dụng của nguồn nào trong đợt này; mới đọc robots.txt.

## 2. Độ phủ

Gộp bốn nguồn tải được, khớp theo tên dự án và theo địa chỉ + tháng bàn giao, ra **khoảng 85 dự án** đang hoặc sắp mở bán.

| | Số dự án | Tỷ lệ trên 85 |
|---|---:|---:|
| Yahoo!不動産 | 72 | 85% |
| SUUMO | 74 | 87% |
| Yahoo! hoặc SUUMO | 83 | 98% |
| 住まいサーフィン | 57 | 67% |
| メジャーセブン | 13 | 15% |
| Chỉ có ở đúng một nguồn | 11 | (SUUMO 6, Yahoo! 3, メジャーセブン 1, 住まいサーフィン 1) |

Kiểm chéo bằng nguồn độc lập: trong 57 dự án của 住まいサーフィン, 56 dự án có trên Yahoo! hoặc SUUMO; riêng Yahoo! có 52, riêng SUUMO có 50.

**Kết luận về nguồn:**

- Chỉ dùng Yahoo! thì thiếu 13 dự án; chỉ dùng SUUMO thì thiếu 11. Phải dùng cả hai.
- Yahoo! cộng SUUMO phủ gần hết những gì bốn nguồn nhìn thấy (83/85).
- メジャーセブン gần như không thêm gì ngoài một dự án chưa công bố giá.
- Con số 85 là cận dưới. Dự án mới chỉ có landing page của chủ đầu tư, chưa lên cổng nào, sẽ không có trong bảng. Chưa đo được nhóm này vì マンションコミュニティ (nguồn tốt nhất cho dự án sắp bán) chặn máy chủ đám mây.

## 3. Trong dải 4.000–5.000万

| Tình trạng giá | Dự án | Có trên Yahoo! | Có trên SUUMO |
|---|---:|---:|---:|
| Khoảng giá chạm dải 4.000–5.000万 | 37 | 30 | 33 |
| Chưa công bố giá | 18 | 13 | 14 |
| Giá thấp nhất trên 5.000万 | 29 | 28 | 26 |
| Giá cao nhất dưới 4.000万 | 1 | 1 | 1 |

"Chạm dải" nghĩa là khoảng giá công bố giao với 4.000–5.000万; chưa chắc còn căn trong dải để mua.

Ngày vào ở của 85 dự án: 15 dự án đã xong hoặc vào ở ngay, 3 trong 2025–2026, 34 trong 2027, 24 trong 2028, 6 trong 2029–2030, 3 chưa rõ. Tức khoảng 64 dự án đang xây hoặc chưa xây.

18 dự án chưa công bố giá phần lớn bàn giao 2028–2030; đây là nhóm sát nhất với "dự án trên landing page quảng cáo".

## 4. Giới hạn

1. **Khớp dự án bằng tên và địa chỉ có thể sai vài trường hợp.** Đã thấy một dự án mang hai tên ở hai trang (OSAKA MVP Project / プレサンス ロジェ 城北公園) và đã gộp; có thể còn sót, nên 85 có sai số vài dự án.
2. **Khoảng giá là theo đợt bán đang mở**, không phải cả dự án.
3. **Phí quản lý, quỹ sửa chữa, loại người bán, bảng giá đầy đủ từng loại căn chưa có.** Trên Yahoo! các thông tin này nằm ở trang bị robots.txt cấm; trên SUUMO nằm ở trang chi tiết dự án, chưa tải.
4. **Quận còn thiếu ở snapshot 02/11 nay đã có**, vì lần này lấy danh sách toàn Osaka-shi thay vì từng quận.

## 5. Việc tiếp theo đề xuất

1. Tải trang chi tiết SUUMO của 55 dự án chạm dải hoặc chưa công bố giá để lấy bảng giá theo loại căn, phí dự kiến, tổng số căn, chủ đầu tư, tiến độ. SUUMO tải được từ đám mây, nên việc này không cần máy của Huy.
2. Chạy マンションコミュニティ từ máy của Huy để bắt dự án chưa lên cổng.
3. Lập danh sách theo dõi 18 dự án chưa công bố giá; kiểm lại định kỳ.
4. Bổ sung cách tính chi phí ở thực cho chung cư mới vào chuẩn 4.0 khi đã có giá theo loại căn và phí.
