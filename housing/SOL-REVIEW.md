# Review tiêu chí — GPT-6.1 Sol high

Ngày: 2026-10-12. Reviewer: /root/review_osaka_criteria, GPT-6.1 Sol, reasoning high.
Đối tượng: CRITERIA.md v0.1 và ASTRA-RESEARCH.md.
Nội dung nhận xét được agent chính biên tập và ghi phản hồi; có review vòng2 cho v0.2 ở cuối file.

## Kết luận reviewer trên v0.1

Đủ để làm pilot thu thập thủ công30–50 tin; cần chỉnh trước khi triển khai crawler và xếp hạng tự động. Chưa đủ để kết luận khu/căn có lợi suất tốt. Các điểm chống cộng lặp, giá rao khác giao dịch, tin dự án khác căn, unknown khác0 và tuổi nhà lúc bán đã xử lý tốt.

## Phát hiện và xử lý

| Mức | Phát hiện của Sol | Xử lý trong v0.2 |
|---|---|---|
| Cao | Ưu tiên40–45M dễ bị hiểu là sở thích user, trong khi user thích40–50M | Giữ40–50M trong shortlist;35–40M khám phá. Ghi40–45M chỉ là tư vấn tài chính sơ bộ của agent, không hạ hạng tự động |
| Cao | Tăng giá danh nghĩa chưa bằng hiệu quả tài chính | Thêm mục13: phí, sửa, giá trị bán ròng, vay, lợi ích ở và lạm phát tách riêng; chưa dự báo khi thiếu dữ liệu |
| Vừa | Tám nhóm dễ bị gọi là tám động lực tăng giá | Mục10 phân biệt nhu cầu/cung/giữ giá/rủi ro/định giá |
| Vừa | Tên nguồn chưa chứng minh trường có thể lấy được | Mục11 ma trận nguồn, mức chi tiết, cách lấy và fallback; pilot không giả vờ đã ghép nguồn ngoài |
| Vừa | Mẫu nhiều khu vẫn có thể lệch về Naniwa | Mục12 inventory mới/cũ, loại nhà, các vùng; báo parser chưa hỗ trợ và coverage |
| Vừa | NULL chưa phân biệt nguyên nhân | Mục12 missing_reason và acquisition_status riêng; không chấm xấu vì thiếu hồ sơ |
| Vừa | Điều kiện pass pilot chưa đo được | Mục12 kiểm10 tin+ca đặc biệt, chạy lại, fixtures riêng, lỗi trọng yếu bằng0; incomplete không báo pass |
| Thấp | Cờ thiếu trạng thái; tuổi cố định theo2036/2046 | Mục12 ba trạng thái, mục13 mốc tính từ ngày mua; thời hạn thuê đất và tiếp cận lúc lớn tuổi |

## Quyết định agent chính

Tiếp thu toàn bộ vấn đề, làm rõ điểm ngân sách thay vì bỏ phân tích tài chính trước đây. Bản0.2 được dùng để viết pilot thu thập có giới hạn và kiểm tra chất lượng; KHÔNG triển khai xếp hạng/khuyến nghị đầu tư tự động. Việc đạt điều kiện kỹ thuật sẽ do kết quả chạy và đối chiếu mẫu quyết định.

## Review vòng2 — v0.2 và CRAWL-SCENARIO.md

Sol6.1 high đã đọc lại và trả: **GO cho pilot kỹ thuật giới hạn; không GO cho ranking đầu tư hoặc quyết định mua.**

- Tám findings đã được xử lý đủ trong thiết kế.
- Scenario5khu x2loại nhà cũ, nhà mới deferred, tối đa35requests, đối chiếu HTML và replay cache phù hợp.
- Không còn blocker thiết kế pilot.
- Phải giữ verification_incomplete nếu chưa kiểm đủ10tin và ca đặc biệt. Verdict không xác nhận code/dữ liệu thực thi đã đạt.
