# Crawl lần 2 — toàn Osaka-shi, nhà mới và cũ

Ngày 13/10/2026. Trạng thái: người mua đã duyệt phạm vi và thiết kế chi tiết qua câu trả lời “Duyệt, triển khai và cho Luna chạy”. Người chạy: GPT-6 Luna.

## Quyết định từ hai bộ tiêu chuẩn

Không biến checklist mua nhà thành bộ lọc quảng cáo quá chặt. Thu thập dữ liệu thị trường trước, chuẩn hóa có nguồn, rồi gắn việc cần xác minh. Chưa chấm căn nào “đủ điều kiện mua”, chưa kết luận khả năng vay hoặc tăng giá.

Ba cách đã cân nhắc:

- Lặp pilot năm quận: nhanh, so sánh tốt với lần trước, nhưng giữ thiên lệch phạm vi và thiếu nhà mới.
- **Khuyến nghị/đã chọn về phạm vi:** cả Osaka-shi và bốn loại nhà, phân tầng quận × loại, lưu SQLite rồi query; không lọc cứng tuổi nhà/ga.
- Crawl không giới hạn toàn bộ website: không chọn; chi phí/tải truy cập cao, nhiều dữ liệu ngoài mục tiêu và không giải quyết được pháp lý/tài chính còn thiếu.

## Phạm vi và ngân sách lượt chạy

- Bốn nhóm: nhà riêng cũ, căn hộ cũ, nhà riêng mới, căn hộ mới. Dùng URL thật phát hiện trên website; không đoán mã quận hoặc endpoint API.
- Khám phá đường dẫn cho mọi quận Osaka-shi; ghi rõ nhóm/quận không có URL, không có tin hoặc không hỗ trợ parser. Không báo “0 căn” nếu lỗi truy cập/parser.
- Một lượt thăm trang đầu của mọi nhóm/quận có URL hợp lệ trước. Sau đó ưu tiên thu chi tiết tin giá chính xác 4.000–5.000万円, phân bố giữa nhóm/quận. Giá thấp hơn vẫn giữ để query; giá dự án theo khoảng được đưa vào nhóm riêng.
- Giới hạn triển khai đề xuất: tối đa 180 HTTP requests gồm robots/khám phá/danh sách/chi tiết; ít nhất 3 giây giữa requests; không song song HTTP. Dành tối đa 40 trang chi tiết. Phần ngân sách còn lại mới đọc trang kế tiếp thật, tối đa hai trang danh sách mỗi nhóm/quận.
- Đây là **đợt khảo sát có giới hạn trên phạm vi toàn thành phố**, không cam kết lấy toàn bộ tin. Manifest phải công khai coverage, lý do thiếu và số trang còn biết chưa tải. Không tăng ngân sách để che việc thiếu phủ.
- HTTP công khai qua CLI; không cần Chrome/Edge MCP hoặc extension nếu HTML đủ. Thiếu dữ liệu render động thì ghi hạn chế, không vượt chặn/login/challenge.
- Tôn trọng robots cả wildcard/query. Dừng toàn lượt khi 401/403/429/challenge. Không retry dồn dập, proxy, đổi danh tính, bypass redirect hay endpoint bị cấm. Robots không thay thế điều khoản sử dụng.

## Ba lớp dữ liệu

### 1. Bằng chứng bất biến

Thư mục riêng theo run_id. Lưu HTML thành công, URL yêu cầu, thời gian lấy UTC, HTTP status, hash và phiên bản parser. Không ghi đè output/cache/SQLite/report của lần trước. Replay giữ thời điểm lấy gốc và được đánh dấu riêng, không tính là quan sát mới.

### 2. Dữ liệu quảng cáo chuẩn hóa

Khóa quan sát là run_id + canonical listing URL; không gọi là unique property. Giữ source_id và nguyên văn:

- loại, title, địa chỉ/quận, giá exact hoặc range/undisclosed, diện tích đất/xây dựng/căn hộ, layout, ngày/năm xây hoặc dự kiến hoàn thành, ga và mô tả đi bộ;
- khi trang chi tiết có: quyền đất người bán công bố, management/repair fees, lease fee, quỹ đóng ban đầu/chi phí khác, kết cấu/tầng, đường/private-road/setback, zoning/coverage/FAR, hiện trạng/thời điểm bàn giao, energy/renovation mentions;
- mỗi trường giữ raw label/value, source URL và trạng thái `advertised`, không gắn `verified` vì đã parse được;
- missing_reason phân biệt `not_collected`, `not_disclosed`, `not_applicable`, `parse_failed`, `ambiguous`;
- trường không có không được đổi thành 0, false hoặc “đạt”.

Tin dự án/nhiều căn/giá khoảng được tách khỏi căn đơn chưa xác minh. Không dùng cận dưới giá dự án làm giá căn. Khoảng giá giao vùng mong muốn chỉ là `project_range_overlap`, không phải ứng viên exact-price. Không ghép cưỡng bức nhiều môi giới thành một căn; chỉ gắn nghi trùng nếu có cơ sở.

### 3. Checklist xác minh bên ngoài

- J01–J03: nhu cầu, tiền mặt/thu nhập/nghĩa vụ, khoản vay/団信 từ người mua/ngân hàng; không gửi tài chính cá nhân lên website.
- J04/J13–J16: đối tác, hợp đồng/cọc, bảo hành, thuế, bàn giao cần hồ sơ riêng; mặc định chưa xác minh.
- J05/J06: quyền/đường/xây lại trên tin là lời công bố, cần đăng ký/hồ sơ địa phương.
- J07/J10: năm xây, kết cấu, energy/renovation trên tin không thay kiểm định/chứng nhận.
- J08: phí hằng tháng không chứng minh số dư quỹ hay kế hoạch sửa đủ; cần hồ sơ quản lý.
- J09: hazard cần tọa độ chính xác và lớp bản đồ phù hợp; không suy từ tên quận.
- J11: ga/đi bộ quảng cáo không thay thời gian cửa–cửa, trường học hay lộ trình thật.
- J12 và lớp tăng giá Osaka: cần giao dịch so sánh, nguồn dự án/dân cư/hạ tầng chính thức; không dùng giá rao để chứng minh tăng giá.

## SQLite và đầu ra

Giữ cấu trúc nhỏ, kiểm tra được: runs, pages, listings, observations, details; thêm coverage/validation trong JSON nếu chưa cần bảng riêng. Chuẩn hóa nằm trong payload có provenance; tránh migration DB cũ.

- SQLite riêng của lượt mới; CSV toàn tin và CSV exact-price ưu tiên; CSV dự án/khoảng giá riêng nếu có.
- run summary + coverage manifest + quality report, gồm raw cards/parsed/errors theo adapter, missingness theo loại và mẫu đối chiếu nguồn.
- Báo cáo HTML tiếng Việt giải thích cách crawl mới, dữ liệu thực sự lấy được, phạm vi chưa làm và đối chiếu hợp lệ với pilot.
- SQL/Python hoặc notebook tái lập kiểm tra, không chứa dữ liệu tài chính riêng ngoài thông tin người dùng đã đưa vào tiêu chuẩn.

## Kiểm tra trước/sau mạng

- Fixture tests cho bốn loại, số tiền exact/range/undisclosed, diện tích, ngày dự kiến, dự án/nhiều căn, thiếu phí và phí một lần so với tháng.
- Robots wildcard/query tests; không truy cập URL bị cấm để kiểm nghiệm.
- Self-check trước mạng; dừng adapter không nhận dạng thay vì tạo hàng sai.
- Đối chiếu mẫu raw HTML theo label→value, có cả nhà mới/nhà cũ, dự án nếu xuất hiện và trường phí/quyền. Không chỉ so CSV với SQLite cùng parser.
- Replay không mạng tái tạo kết quả, giữ timestamps, không nhân đôi listing URL.
- So với pilot cũ chỉ trong cùng loại/quận/phạm vi có thể so: URL trùng/mới/không thấy, thay đổi giá exact ở URL trùng. Không thấy không nghĩa đã bán; mở rộng phạm vi không phải thị trường tăng nguồn cung.
- Xác nhận hash DB/cache cũ không đổi. Không scheduler, git push hay liên hệ môi giới.

## Điều không thuộc lượt này

Không crawl mọi trang vô hạn; không mua dữ liệu; không geocode/bổ sung hazard hàng loạt; không kết luận pháp lý; không tự chấm đầu tư; không đổi ngưỡng tài chính, tuổi nhà, diện tích hay ga thành điều kiện loại trừ.
