# Kết quả đợt 3 — trang chi tiết nhà mới và chung cư mới

Chạy ngày 17/11/2026 bằng ba agent: một agent cho SUUMO, một agent cho Yahoo!不動産, và một agent kiểm độc lập không viết code. Mỗi nguồn một luồng, cách nhau ít nhất 3 giây (khoảng cách thực nhỏ nhất là 4 giây).

| Agent | Request | Kết quả |
|---|---:|---|
| SUUMO | 472 (trần 520) | 408 dòng: 64 trang chung cư + 64 trang 物件概要 đi kèm, 344 nhà riêng mới |
| Yahoo! | 18 (trần 40) | 18 dòng; thêm sửa parser danh sách nhà mới (245 → 263/310 tin) |
| Kiểm độc lập | 0 | **Đạt**, xem [REVIEW.md](REVIEW.md) |

Tất cả 490 request trả HTTP 200; không request nào vào đường dẫn robots.txt cấm. HTML gốc không đưa vào repo.

Dữ liệu: [data/details-suumo.csv](data/details-suumo.csv), [data/details-yahoo.csv](data/details-yahoo.csv). Tổng hợp SUUMO: [details-suumo-summary.json](details-suumo-summary.json). Script: [`details_suumo.py`](../tools/details_suumo.py), [`details_yahoo.py`](../tools/details_yahoo.py).

## Kiểm độc lập

Mẫu ngẫu nhiên cố định: 10 chung cư, 15 nhà riêng (SUUMO), 5 dòng Yahoo!, mỗi dòng 12 trường, so với HTML gốc.

- 0 giá trị sai, 0 giá trị bịa, 0 giá trị bỏ sót.
- Giá: 0 lỗi trên toàn bộ 426 dòng, kể cả dạng 億.
- robots.txt: 0/490 URL bị cấm.

## Chung cư mới (SUUMO)

64 URL thực ra gồm **49 dự án** do chủ đầu tư bán và **15 căn lẻ còn sót** do môi giới bán lại (giá một mức, 1 căn).

Trong 49 dự án:

| | Số |
|---|---:|
| Chưa công bố giá (価格未定) | 17 |
| Có phí quản lý và quỹ sửa chữa bằng số | 36 |
| Phí ghi "chưa quyết" (金額未定) | 13 |
| Đã hoàn thành (trước 11/2026) | 8 |
| Hoàn thành 2026 (từ 11/2026) | 3 |
| Hoàn thành 2027 | 23 |
| Hoàn thành 2028 | 13 |
| Hoàn thành 2029–2030 | 2 |

Tức khoảng **41 dự án đang hoặc sắp xây**. Trang dự án mới của SUUMO không ghi 取引態様; mua từ chủ đầu tư thì thường không mất phí môi giới, nhưng cần xác nhận với từng dự án.

## Nhà riêng mới trong dải 4.000–5.000万 (SUUMO)

344 tin.

| Loại người bán | Số tin |
|---|---:|
| Môi giới (仲介/媒介) — mất phí môi giới | 280 |
| Người bán trực tiếp (売主) — không mất phí môi giới | 54 |
| Đại lý bán (販売提携/代理) — thường không mất phí, cần xác nhận | 7 |
| Không ghi | 3 |

| Tình trạng xây (so với 11/2026) | Số tin |
|---|---:|
| Đã hoàn thành | 130 |
| Hoàn thành trong 11/2026 | 43 |
| Hoàn thành sau đó (đến hết 2027) | 122 |
| Chỉ ghi "N tháng sau hợp đồng" (chưa xây) | 49 |

Nhà riêng không có phí quản lý; chuẩn 4.0 dùng khoản dự phòng bảo trì giả định cho loại này.

## Yahoo! (18 trang không có trên SUUMO)

- 12 nhà riêng: đủ ngày hoàn thành và loại người bán; không có phí.
- 6 dự án chung cư: chỉ 1 dự án (サンメゾン此花) có phí và thông số trên trang chính. Thông số của 5 dự án còn lại nằm ở trang robots.txt cấm, nên không lấy.

## Giới hạn

1. Trang dự án chung cư mới của SUUMO không ghi 取引態様 và tên người bán; trường `seller_raw` chỉ là suy đoán từ phần thông tin công ty.
2. Phí của 13 dự án chưa quyết; 17 dự án chưa có giá. Cần kiểm lại khi dự án công bố.
3. Đây vẫn là thông tin quảng cáo, chưa phải hồ sơ đã xác minh.

## Việc tiếp theo đề xuất

1. Đưa nhà riêng mới và dự án chung cư mới vào cách tính chi phí ở thực của chuẩn 4.0.
2. Lập danh sách theo dõi 17 dự án chưa công bố giá.
3. Lọc riêng 61 nhà riêng mua trực tiếp hoặc qua đại lý (không hoặc có thể không mất phí môi giới).
