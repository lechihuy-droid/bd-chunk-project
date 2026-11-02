# Phản hồi review và trạng thái bàn giao

Ngày 03/11/2026. Agent chính chịu trách nhiệm chuẩn và kế hoạch; Terra 6.1 high review độc lập, Luna 6 medium kiểm kê dữ liệu đọc local.

| Finding Terra | Xử lý trong chuẩn |
|---|---|
| G5 trộn ký và bàn giao | Thêm G5_stage, due_checks, stage_state và ai xác nhận từng mốc |
| Chưa đánh giá khác thiếu hồ sơ | Thêm NOT_EVALUATED, quy tắc gộp và highest_passed_gate liên tiếp |
| G4 không có điều kiện PASS | score_state tách biệt; G4 PASS cần G1–G3 PASS, active, COMPLETE và double-count clear |
| Trùng rows và cân bằng số lượng | Giữ source_row_id/raw; mapping canonical; disposition cộng theo unique URL |
| Mapping CSV/availability thiếu | Ghi field, đơn vị, cache replay, join checks/timestamps, missing reasons |
| ranked_ready chưa rõ | Tách gate_qualified/ranking_eligible; thiếu score còn review_required |
| Rubric/evidence chưa đủ để tự chấm | Cấp evidence theo score item, cohort, comparison memo và khóa rubric_revision trước chấm |
| Cộng trùng | Ledger evidence→claim→effect→score owner; cùng effect chỉ một owner |
| Privacy trong free text | Public allowlist và template reasons; không xuất private DB hoặc chỉ dựa redaction |
| Các chi tiết còn mỏng | Bổ sung NA mua không vay, giảm giá/bán chậm, hiệu suất/quyền cải tạo, bảo hành/thuế/đứng tên, người phụ trách và hạn thông báo lỗi |

Các sửa đổi trên là tài liệu thiết kế, chưa phải code triển khai. Tài liệu cũ và dữ liệu v2 giữ nguyên. Chưa có bất kỳ kết quả gate hay xếp hạng mới nào được công bố.

Tái review Terra phát hiện thêm ba câu; parent đã sửa: G4/ranking đòi availability active dù availability là field riêng; observed_at là thời điểm crawler quan sát, source_updated_at là ngày do nguồn công bố; G1-04 chỉ khử bản sao ở view unique và giữ raw rows. Đây là phản hồi sửa của parent, không gán nhãn Terra đã review lại lần thứ ba.

Khi triển khai, các mục cần người mua/chuyên gia xác nhận vẫn có thể REVIEW. Hoàn thành engine hoặc làm giàu dữ liệu không tự làm các mục đó PASS.
