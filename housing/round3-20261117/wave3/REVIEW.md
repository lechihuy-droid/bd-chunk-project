# REVIEW wave3 — details-suumo.csv / details-yahoo.csv

**Kết luận: PASS** — không có sai lệch field nào trong mẫu, không có dữ liệu bịa, không vi phạm robots.txt, không có request lỗi hoặc quá nhanh.

Người review độc lập, không fetch mạng, không sửa file nào khác ngoài file này.

## Bảng kết quả

| # | Kiểm tra | Phạm vi | Kết quả |
|---|---|---|---|
| 1 | Độ chính xác field (random.seed(17)) | 10 condo + 15 nhà mới SUUMO + 5 Yahoo = 30 dòng x 12 field | 0 sai lệch, 0 bịa (fabrication), 0 bỏ sót (miss) |
| 2 | Parse giá | 408 dòng SUUMO + 18 dòng Yahoo | 0 lỗi |
| 3 | robots.txt (`User-agent: *`, longest-match, `*` và `$`) | 472 URL SUUMO + 18 URL Yahoo | 0 URL bị chặn |
| 4 | Kỷ luật request | 2 log | 0 status khác 200; 0 cặp liên tiếp < 3.0 s |
| 5 | Vệ sinh repo | `housing/round3-20261117` | 0 file .html được track; 0 file .html trên đĩa |
| 6 | Phân loại 64 URL new_condo_project | 64 dòng | 15 dòng là căn lẻ do môi giới bán (khớp báo cáo của lane) |

## Chi tiết

**1. Độ chính xác field.** Với mỗi field khác rỗng trong CSV, giá trị đã chuẩn hóa (NFKC, bỏ khoảng trắng, `~`/`～`, `<>`/`＜＞`) được tìm trong văn bản HTML đã cache. Với các trang condo của chủ đầu tư, văn bản còn gộp thêm trang phụ `/property/`, vì scraper lấy completion/quản lý phí/tích lập sửa chữa/diện tích đất từ trang đó. Trang phụ này có trong cache và có trong log. Với nhà mới có trang `/bukkengaiyo/` thì làm tương tự. Toàn bộ giá trị trong CSV đều có trên trang. 15 dòng nhà mới còn được đối chiếu thủ công theo cặp nhãn/giá trị: giá, địa chỉ, completion, handover, diện tích đất/nhà, 取引態様 đều khớp.

Với các ô rỗng, tôi đã đối chiếu với nhãn trên trang để tìm giá trị bị bỏ sót, và không thấy trường hợp nào:
- Trang chỉ hiển thị `-` hoặc không có nhãn (đất/総戸数 trên trang môi giới; quản lý phí/tích lập trên nhà mới; 取引態様 trên trang condo của chủ đầu tư).
- 3 nhà mới không có nhãn 取引態様 trên trang (hirano nc_21917632, hirano nc_78147972, ino nc_78354482).
- Yahoo mansion 00156718 (giá chưa định) không có completion/tổng căn/đất trên trang.

Số sai lệch theo field (SUUMO 25 dòng + Yahoo 5 dòng): price_raw 0, price_min/max 0, address 0, completion_raw 0, handover_raw 0, management_fee_raw 0, repair_reserve_raw 0, units_total 0, land_area_raw 0, unit_or_building_area_raw 0, transaction_type_raw 0.

**Danh sách sai lệch / bịa:** không có.

**2. Parse giá.** Tất cả dòng có số trong price_raw đều có price_min_man và price_max_man, đều khớp với price_raw (gồm dạng 億 như `1億880万円` = 10880 và `3360万円~1億8880万円` = 3360..18880, dạng `3900万円台~7300万円台`, `3990万円・4190万円`), và min ≤ max. 17 dòng SUUMO và 2 dòng Yahoo có price_raw là `未定` hoặc `第二期 未定`, đúng là không có số nên min/max rỗng. Không có dòng nào có số nhưng min rỗng.

**3. robots.txt.** Bản copy `wave1/robots/suumo.jp.txt` và `wave1/robots/realestate.yahoo.co.jp.txt` được áp dụng cho nhóm `*`. Tất cả URL (cả `/property/`, `/bukkengaiyo/` và URL Yahoo) đều được phép.

**4. Kỷ luật request.** SUUMO: gap nhỏ nhất 4 s (294 gap 5 s, 172 gap 4 s), không trùng URL. Yahoo: gap nhỏ nhất 4 s. Timestamp trong log chỉ có độ phân giải 1 giây nên gap thực có thể lệch tối đa 1 s, nhưng vẫn không thể < 3.0 s. Log SUUMO có 472 dòng: 408 URL trong CSV + 64 trang phụ `/property/`. Log Yahoo có 18 dòng, khớp 18 URL.

**5. Repo.** `git ls-files | grep -i '\.html$'` trong thư mục round3 trả 0. `find` cũng không thấy .html.

**6. Phân loại.** Quy tắc: 取引態様 = `<仲介>` (kiểm tra độc lập trên HTML gốc và trên CSV, hai cách khớp nhau trên cả 64 dòng) → 15 dòng. Cả 15 dòng đều có 販売戸数 = 1戸. Hai dòng condo khác cũng có 販売戸数 = 1戸 (マリモ, nc_67736723 và nc_67736092, tổng 42 căn) nhưng là dự án của chủ đầu tư, không phải môi giới, nên không tính vào 15. Hai dòng `parse_partial` (nc_21246968, nc_20537901) là dòng môi giới, thiếu units_total vì trang ghi `-`.

## Khuyến nghị
Không có sửa đổi nào cần thiết dựa trên bằng chứng. Ghi chú để người dùng dữ liệu biết: trong 64 dòng new_condo_project có 15 dòng môi giới căn lẻ, và 2 dòng chủ đầu tư chỉ còn 1 căn đang bán. Cột `transaction_type_raw` rỗng đối với trang chủ đầu tư là do trang không có nhãn đó.
