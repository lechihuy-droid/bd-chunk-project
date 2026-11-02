# ver2.0-20261102

Audit scope: preferred. All 1754 fresh preferred candidate URLs have checks. The 2179 original historical CSV rows are retained in old-listings-audit.csv; other fresh and historical rows are marked not_checked, with no claim of a complete historical link audit.

[Mở danh sách nhà](index.html) · [CSV gốc mới](all-listings.csv) · [CSV trong dải giá, link còn mở được](preferred-exact.csv) · [SQLite](suumo-v2.sqlite.gz)

11463 URL mới quan sát; 1751 tin trong dải giá đã nhận dạng trang chi tiết còn hoạt động. Thời gian thu danh sách: 02/11/2026; xem timestamp từng hàng và ngày kiểm link riêng. Phiên bản mang ngày bắt đầu, không giả mọi kiểm tra diễn ra cùng ngày.

[Kiểm link cũ](old-listings-audit.csv) · [Tin hết đăng/không tìm thấy](expired-listings.csv) · [Tin ưu tiên chưa xác minh](preferred-unverified.csv) · [Dự án](projects.csv) · [Phạm vi và kết quả](summary.json).

CSV gốc giữ mọi tin mới quan sát kèm trạng thái; giao diện chỉ dùng tin trong dải giá có bằng chứng trang chi tiết còn hoạt động. Không suy ra đã bán từ hết đăng. Thiếu route hoặc chạm trần phân trang được ghi trong summary; không coi là toàn bộ thị trường. Giá là giá quảng cáo lúc lấy trang danh sách, có thể khác thời điểm kiểm link. Sao lưu theo URL trong trình duyệt.

SQLite download is gzip-compressed; decompress it to obtain suumo-v2.sqlite.
