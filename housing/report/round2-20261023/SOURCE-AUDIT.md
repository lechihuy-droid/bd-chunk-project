# Đối chiếu nguồn — khảo sát Osaka lần 2

Kiểm tra offline ngày 2026-10-24. Nguồn là HTML lưu từ lượt 2026-10-23; không xác nhận tin còn đang bán vào ngày đọc báo cáo.

## Mẫu trang danh sách

Đã đọc nội dung card HTML gốc và đối chiếu dữ liệu trích xuất cho 12 URL, mỗi loại 3 URL. Đây là kiểm tra chọn mẫu, không phải xác minh thủ công toàn bộ 2.179 tin.

| Loại | SUUMO nc ID | Kết quả đối chiếu |
|---|---|---|
| Nhà riêng cũ | 21541699 | 4.680 man; đất 63,92 m²; nhà 123,08 m²; 4LDK; 1989; ga 1 phút |
| Nhà riêng cũ | 20441229 | 4.680 man; đất 66 m²; nhà 104,05 m²; 3LDK; 2018; ga 5 phút |
| Nhà riêng cũ | 21243545 | 4.480 man; đất 78,33 m²; nhà 150,7 m²; 5LDK; 1993; ga 7 phút |
| Căn hộ cũ | 21004966 | 4.990 man; 68,21 m²; 3LDK; 1999 |
| Căn hộ cũ | 21236614 | 4.680 man; 65,95 m²; 2LDK; 2004 |
| Căn hộ cũ | 21327662 | 4.590 man; 66,11 m²; 3LDK; 2007 |
| Nhà riêng mới | 21581554 | 4.880 man; đất 58,2 m²; nhà 73,41 m²; 3LDK |
| Nhà riêng mới | 21994131 | 4.580 man; đất 61,81 m²; nhà 86,1 m²; 3LDK |
| Nhà riêng mới | 78596639 | 4.680 man; đất 52,58 m²; 3LDK. Diện tích nhà còn thiếu trong dữ liệu chuẩn hóa; xem ghi chú dưới |
| Dự án căn hộ mới | 67734373 | Giá chưa công bố; dải 1LDK–3LDK, 30,78–60,42 m²; giữ cấp dự án |
| Dự án căn hộ mới | 67734593 | 3.480–5.980 man; 1LDK–3LDK, 35,1–60,15 m²; giữ cấp dự án |
| Dự án căn hộ mới | 67736464 | 3.360–18.880 man; 1LDK–4LDK, 31,95–115,43 m²; giữ cấp dự án |

**Giới hạn parser đã thấy:** card `78596639` ghi `93.58m2、うち１階車庫9.77m2`. Parser thận trọng để diện tích nhà null khi gặp ghi chú này. Không dùng null để loại nhà; phải đọc nguồn khi so sánh diện tích. Chưa sửa/reparse toàn bộ lượt vì cần kiểm tra thêm các dạng diện tích có chú thích.

**Căn hộ mới:** card `67734593` còn quảng cáo kiểu căn 2LDK, 45 m², 4.490 man. Giá ở cấp kiểu căn chưa được nâng thành căn đơn đã xác minh. Vì vậy số căn hộ mới trong bảng 295 bằng không không chứng minh thiếu lựa chọn trong ngân sách.

## Mẫu trang chi tiết

Đã đọc ngữ cảnh HTML quanh nhãn và đối chiếu 10 trường của 4 trang; ngữ cảnh lưu ở `detail-source-check.json`. Trình kiểm tra ô liền kề không nhận được ô vì cấu trúc HTML có phần gợi ý; kết luận dưới dựa trên đọc ngữ cảnh nguồn, không dựa vào trường `source_cells` trống.

- Nhà cũ `21819579`: quyền ghi 所有権; nhãn 私道負担・道路 ghi 無. Không suy ra pháp lý đường đi từ một chữ 無.
- Nhà cũ `21571442`: quyền ghi 所有権; đường ghi 無、南5ｍ幅.
- Căn hộ `21698599`: quyền ghi 所有権; quản lý 8.140 yên/tháng; quỹ sửa 1万2430円 = 12.430 yên/tháng, chuyển đơn vị đúng.
- Căn hộ `21218341`: quyền ghi 所有権; quản lý 6.430 yên/tháng; quỹ sửa 4.500 yên/tháng.

Đây đều là thông tin quảng cáo, chưa xác minh bằng đăng ký đất, hợp đồng hay hồ sơ ban quản lý. Không sử dụng ví dụ lãi vay trên trang rao làm báo giá cho người mua.

## Tính nhất quán và trình bày

- SQLite kiểm tra integrity; số URL, loại nhà và dải giá khớp manifest.
- Luna replay offline tái tạo 2.179 tin và 40 chi tiết cùng timestamps; 180 tệp nguồn khớp SHA-256. Xem `../../output/round2-20261023-luna/LUNA-ROUND2-REPORT.md`.
- 24 kiểm thử crawler/analysis đã đạt; kết quả QA trình duyệt tại `qa.json` và ảnh `qa-*.png`.
- Phạm vi 90/96 ô quận–loại; không coi 6 ô thiếu hoặc trang tiếp chưa tải là không có nhà.
- Hai bộ tiêu chuẩn cũ được giữ nguyên. Báo cáo mới chỉ ánh xạ dữ liệu đã thu vào tiêu chuẩn, chưa hoàn tất thẩm định hay dự báo tăng giá theo từng căn.
