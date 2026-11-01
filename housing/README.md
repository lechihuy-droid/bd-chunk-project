# Housing — nghiên cứu mua nhà Osaka-shi

Bản chia sẻ kết quả, upload ngày 02/11/2026. **Dữ liệu crawl gần nhất trong gói này được thu ngày 23/10/2026**, không phải danh sách đang bán được xác nhận hôm nay.

## Đọc báo cáo

- [Báo cáo kết quả crawl lần 2](report/round2-20261023/report.html): bảng theo quận/loại nhà, 295 tin trong dải giá, ánh xạ hai bộ tiêu chuẩn và giới hạn dữ liệu.
- [Bộ tiêu chuẩn mua nhà Osaka](report/bo-tieu-chuan-mua-nha.html).
- [Tiêu chuẩn mua nhà Nhật và đối chiếu Osaka](report/tieu-chuan-mua-nha-nhat-va-review-osaka.html).
- [Tiêu chí A–H](CRITERIA.md), [nghiên cứu Astra](ASTRA-RESEARCH.md), [review Sol](SOL-REVIEW.md), [thiết kế crawl](CRAWL-ROUND2-DESIGN.md).

GitHub hiển thị mã nguồn HTML. Tải thư mục/repository về và mở file HTML bằng trình duyệt để xem báo cáo; giữ cấu trúc thư mục để các liên kết tương đối hoạt động.

## Dữ liệu

- [SQLite](output/round2-20261023-luna/suumo-round2.sqlite): 2.179 URL tin và dữ liệu chi tiết, truy vấn offline.
- [Toàn bộ tin CSV](output/round2-20261023-luna/all-listings.csv).
- [295 tin giá chính xác 4.000–5.000 man](output/round2-20261023-luna/preferred-exact.csv).
- [Tin cấp dự án](output/round2-20261023-luna/projects.csv).
- [Độ phủ](output/round2-20261023-luna/coverage.json), [tổng kết lượt](output/round2-20261023-luna/summary.json), [40 trang chi tiết đã trích xuất](output/round2-20261023-luna/detail-summary.json).

Đơn vị đếm là URL tin, chưa khử trùng nhiều môi giới cùng rao một căn. Lượt crawl dùng 180 requests, thu được dữ liệu ở 90/96 ô quận–loại nhà; không phải toàn bộ thị trường.

## Căn hộ mới và tiến độ xây dựng

Có 208 URL căn hộ mới; 198 là tin cấp dự án. Trong dữ liệu thô có ngày bàn giao `引渡時期`, gồm các dự án dự kiến bàn giao 2027–2028. Chưa chuẩn hóa trạng thái chưa khởi công / đang xây / đã hoàn thành. Ngày bàn giao tương lai không tự chứng minh đang xây. Số căn hộ mới bằng không trong danh sách 295 không có nghĩa không có lựa chọn trong ngân sách; giá dự án/kiểu căn chưa được xác minh tới từng căn.

## Kiểm chứng và phạm vi chia sẻ

- [Báo cáo Luna replay](output/round2-20261023-luna/LUNA-ROUND2-REPORT.md): replay không gọi mạng, khớp 2.179 tin, 40 chi tiết và timestamps; 180 tệp HTML nguồn khớp hash lúc kiểm tra.
- [Kiểm tra nguồn chọn mẫu](report/round2-20261023/SOURCE-AUDIT.md).
- [Chi tiết kiểm tra replay](output/round2-20261023-luna-replay/LUNA-ROUND2-AUDIT.json).
- [Danh sách và SHA-256 của gói công khai](MANIFEST.json).

Bản công khai đã ẩn số dư tiền mặt, tên cá nhân, tình trạng cư trú và đường dẫn máy. Dải giá là tham số khảo sát, không phải kết luận khả năng chi trả. SQLite giữ dữ liệu tin và timestamps; đường dẫn cache nội bộ được chuẩn hóa. Hash gói công khai khác bản nội bộ khi có chỉnh sửa này.

Không upload HTML nguồn của các trang bất động sản, ảnh QA có thông tin riêng, dữ liệu tài chính gốc, báo cáo pilot cá nhân hoặc cache replay trùng lặp. Các tham chiếu đến những tệp đó trong tài liệu kiểm chứng là bằng chứng của lần kiểm tra nội bộ; gói công khai này không đủ để replay từ HTML gốc. Không có kết luận thẩm định pháp lý, khả năng vay hay bảo đảm tăng giá.
