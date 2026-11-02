# Review độc lập chuẩn HOUSING-GATES v1.0

Ngày 03/11/2026. Đối chiếu CRITERIA.md, hai báo cáo tiêu chuẩn Osaka/Nhật và header cùng mẫu CSV v2. Chưa chạy filter hoặc xác minh từng căn. Toán điểm cơ bản nhất quán; cần đóng các điểm sau trước khi triển khai.

1. **G5 nhiều mốc:** PASS cuối yêu cầu cả bàn giao và hậu mua sau ký/cọc. Thêm G5_stage và điều kiện riêng trước đề nghị ràng buộc, trước ký/cọc, trước giải ngân/bàn giao và sau bàn giao; xác định người xác nhận và điều kiện dừng.
2. **Trạng thái chưa đánh giá:** quy tắc gộp thiếu NOT_EVALUATED và chưa định nghĩa G2–G5 sau gate trước REVIEW/FAIL; G4 không có ngưỡng đạt. Thêm NOT_EVALUATED; phân biệt assessment song song với tiến trình tuần tự; quy định gộp FAIL > REVIEW > NOT_EVALUATED > PASS, loại NA khỏi phép gộp. Tách scoring khỏi gate hoặc định nghĩa G4 COMPLETE/INCOMPLETE và highest_passed_gate tương ứng.
3. **Hàng trùng và bảo toàn:** G1-04 nói loại bản ghi trùng URL; nghiệm thu nói không mất URL. Giữ source_row_id, row gốc và mapping canonical URL; chỉ khử bản sao trong view unique. Báo row count, unique URL count, duplicate count và quy định disposition cho row trùng.
4. **Mapping v2:** CSV có url, category, listing_level, price_jpy, price_raw, address, ward, observed_at và một số thuộc tính; thiếu phần lớn hồ sơ G2–G5 và availability. Thêm mapping field, nguồn bổ sung, đơn vị, timestamp, lý do thiếu; không suy unverified_unit thành căn đã xác nhận. Quy định nguồn/join availability, default not_checked; giữ riêng not_collected, not_disclosed, parse_error, source_blocked, unknown, not_applicable.
5. **ranked_ready:** PASS G1–G3 chưa đủ để có thứ hạng số nếu điểm thiếu. Định nghĩa ranked_ready là đủ điều kiện thẩm định; chỉ rank số khi coverage 100%, cùng loại và profile; quy định link not_checked, network_error, expired và điều kiện được phép xếp.
6. **Rubric điểm:** 14 trọng số đúng 100 (P25/Q25/L25/U15/S10), công thức biên đúng. Anchor định tính chưa xác định cohort, nguồn, mức chứng cứ tối thiểu, freshness, xử lý xung đột và điều kiện chấm 1/3. Bổ sung rubric mỗi ID; giữ null khi chưa đủ căn cứ. Coverage 100% không chứng minh độ tin cậy hay hiệu chuẩn.
7. **Đếm trùng:** event_id và bốn cặp là nền tốt nhưng lợi thế ga có thể chảy L2/S1/L3; dự án có thể chảy U1/U2/U3/P1. Thêm ledger evidence–claim–effect, mỗi tác động có một mục sở hữu điểm; mục phụ thuộc để null nếu không tách được. Thử fixture cùng ga/dự án.
8. **Riêng tư:** ẩn private_ref và số tài chính chưa đủ: reason, blockers, next_action, logs, manifest, SQLite và HTML vẫn có thể tiết lộ hồ sơ. Dùng allowlist public, projection tách database private và kiểm tra mọi artifact và lịch sử Git trước push. G2-01–03 công khai chỉ nêu dependency chung.

## Bao phủ và bổ sung

- Ma trận có đủ J01–J16 và A–H. Bổ sung rõ J10 về hiệu suất năng lượng/chứng từ, quyền cải tạo và giới hạn kiểm định; J14 phân biệt bảo hành luật định/hậu mãi/bảo hiểm nhà mới; J15 nguồn tiền góp và tỷ lệ đứng tên; J16 người phụ trách và hạn thông báo lỗi. G3-06 thêm kịch bản giảm giá và bán chậm theo CRITERIA. A so trước/sau cùng điểm đến; B tách giai đoạn dự án; C ghi chuỗi và địa giới; D không coi tin biến mất là giao dịch. Không tạo ngưỡng loại mới.
- G2-03 và G5-04 cần NA có lý do nếu mua không vay được xác nhận; chưa rõ cách tài trợ là REVIEW. G1-05 cần quy tắc khi chưa chốt ngày cần ở; tình trạng chiếm hữu chưa rõ vẫn REVIEW khi trọng yếu.
- Thiếu tài chính giữ G2 REVIEW và không PASS tạm là nhất quán. Nghiên cứu phải ghi chưa đủ điều kiện thẩm định cuối; 1.754 là baseline cũ, không mặc định PASS. Kiểm thử cân bằng disposition, giá khoảng, căn thiếu, nguồn mâu thuẫn, sao và fixture không ghép nhầm.


## Tái kiểm sau chỉnh sửa — 03/11/2026

Đã đọc lại chuẩn và kế hoạch. Đã ghi nhận các sửa cho NOT_EVALUATED, G4/ranking, rubric và ledger, G5 theo mốc, phương án không vay, bảo toàn raw row, availability join, allowlist, J10/J14/J15/J16 và kịch bản giảm giá/bán chậm. Đây là kiểm tra tài liệu, chưa phải kiểm chứng implementation.

Còn hai mâu thuẫn cần sửa trước khi freeze:

1. Kế hoạch T3 dòng oracle nói trạng thái PASS/REVIEW/NA độc lập availability, nhưng chuẩn mục 7 quy định G4 PASS bắt buộc availability=active. Sửa oracle thành G1–G3 và G5 độc lập availability; G4 có dependency active như chuẩn, đồng thời thêm test active/expired/not_checked. Thống nhất thứ tự gộp G4 khi chưa chạy scoring hoặc gate trước FAIL.
2. Mapping mục 10 gọi observed_at là ngày nguồn; CSV v2 là thời điểm quan sát/thu thập, không chứng minh ngày nội dung nguồn cập nhật. Sửa thành thời điểm quan sát, lưu source_updated_at/effective_at riêng nếu có; tuyệt đối không thay timestamp nguồn bằng timestamp crawl.

G1-04 vẫn ghi loại row trùng, trong khi mục 10 đã quy định giữ mọi row và khử trùng chỉ tại view. Sửa câu G1-04 theo mục 10 để tránh triển khai nhầm. Các đề xuất khác đã có hướng xử lý trên giấy; chất lượng rubric, dữ liệu và privacy phải kiểm khi triển khai thực tế.
