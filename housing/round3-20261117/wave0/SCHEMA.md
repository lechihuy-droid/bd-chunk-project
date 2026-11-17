# Lược đồ chung cho mọi nguồn (đợt 0B)

Mỗi nguồn xuất một bảng tin `listings-<source>.csv` với đúng các cột dưới đây. Thiếu thì để trống và ghi lý do vào `missing_reason` (`not_disclosed`, `not_collected`, `parse_error`, `not_applicable`); không điền 0.

| Cột | Ý nghĩa |
|---|---|
| `source` | `suumo`, `yahoo`, `stepon`, `rehouse`, `nomu`, `livable`, `daikyo`, `athome`, `homes`, `fudousan` |
| `listing_url` | URL trang chi tiết, đã bỏ tham số theo dõi |
| `observed_at` | Thời điểm tải (UTC) |
| `category` | `used_condo`, `new_condo`, `used_house`, `new_house` |
| `price_jpy`, `price_raw` | Giá chính xác của một căn; giá khoảng để trống `price_jpy` |
| `address`, `ward` | Nguyên văn và tên quận |
| `building_name` | Chung cư: tên tòa (SUUMO trang danh sách không có; các nguồn khác thường có) |
| `floor`, `floors_total`, `direction` | Tầng của căn, tổng tầng, hướng |
| `unit_m2`, `land_m2`, `building_m2` | Diện tích theo loại, không trộn |
| `layout`, `built_year`, `built_month` | |
| `station_raw` | Nguyên văn tuyến/ga/phút đi bộ |
| `units_total` | Tổng số căn của tòa |
| `seller_type` | 取引態様: `売主`, `代理`, `仲介`; trống nếu trang danh sách không ghi |
| `company` | Công ty đăng |
| `missing_reason` | JSON: trường → lý do |

## Khóa gom căn

- Chung cư: `category` + địa chỉ tới chome (chuẩn hóa NFKC, bỏ 「丁目」 và số nhà) + `unit_m2` (2 chữ số) + `built_year` + `layout`. Khi cả hai tin đều có `building_name` và `floor` thì hai trường này phải khớp.
- Nhà riêng: `category` + địa chỉ tới chome + `land_m2` + `building_m2` + `built_year` + `layout`.
- Không dùng giá. Nhóm có giá khác nhau gắn nhãn `price_conflict`.
- Thiếu địa chỉ, bố trí phòng hoặc diện tích thì không gộp (`weak_key_not_merged`).

Giới hạn đã biết: dữ liệu SUUMO công khai không có tên tòa và tầng, nên hai căn cùng tòa, cùng diện tích, cùng bố trí nhưng khác tầng đang bị gộp làm một. 44/1.108 nhóm có giá lệch nhau (trung vị lệch 4,6%) là các ca nghi rơi vào trường hợp này.
