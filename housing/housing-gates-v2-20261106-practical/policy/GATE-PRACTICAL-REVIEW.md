# Đề xuất rà soát: phễu 5 gate thực dụng cho nghiên cứu nhà Osaka

**Trạng thái: đề xuất để Huy xem xét, chưa triển khai.** Đây là thay đổi ý nghĩa gate so với `HOUSING-GATES-1.0`, cần một phiên bản chính sách mới và chạy lại có đối chiếu; không sửa ngầm kết quả đang công bố. `PASS nghiên cứu` chỉ cho phép tiếp tục tìm hiểu hoặc đưa vào bản đồ, không xác nhận đủ tiền, quyền sở hữu, an toàn hay có thể mua. Thẩm định mua là trạng thái riêng tại G5.

## Vì sao cần đổi

Run offline `evaluation-20261104-pricefix` có 11.463 URL; 1.753 tin `in_scope`. Trong 1.753 tin này: G1 đều REVIEW, G2 đều REVIEW, G3 đều NOT_EVALUATED. G1 hiện yêu cầu làm rõ danh tính căn và khả năng vào ở; G2 yêu cầu tài chính riêng; do đó bản đồ chỉ nhận G1–G3 PASS hiện rỗng dù có ứng viên để nghiên cứu. Đây là tình trạng của snapshot, không phải kết luận thị trường hiện tại.

Trong 1.753 tin `in_scope`: 1.750 link `active`, 2 `not_found`, 1 `unverified` theo lần kiểm cũ. Giá, địa chỉ, quận và `station_raw` có ở cả 1.753; năm xây có 1.491. Có diện tích đất 591, diện tích xây dựng 571, diện tích căn hộ 1.162; các mẫu số này thuộc loại tài sản khác nhau và không được cộng/gộp như cùng một diện tích. Đây là dữ liệu tin rao E1, không mặc nhiên đã được xác minh. Số lượng phải tính lại khi chạy chính sách mới.

## Quy ước dùng chung

- `PASS nghiên cứu`: đã làm đủ công việc của gate để tiếp tục nghiên cứu; mọi claim và phần chưa biết vẫn hiển thị. `HOLD`: có vấn đề hay thiếu dữ liệu trọng yếu cần làm rõ trước khi chuyển bước; giữ tin và lý do. `OUT_OF_SCOPE`: dữ liệu đủ rõ cho thấy ngoài phạm vi đã xác nhận, không hàm ý nhà xấu. `NOT_EVALUATED` giữ nghĩa chưa đánh giá. Các trạng thái này thuộc phễu nghiên cứu mới, không dùng lại PASS cũ như thể tương đương.
- Ngoài phạm vi theo giá chỉ khi giá exact đáng tin cậy cho một tin/căn nằm ngoài **40–50 triệu JPY, gồm hai đầu**; thông tin mâu thuẫn/giá không rõ đưa HOLD, không lấy giá thấp nhất của dự án làm giá căn. Dự án và giá khoảng có hàng chờ riêng, không hòa vào danh sách so sánh căn đơn lẻ.
- Claim quảng cáo không xác nhận pháp lý, kỹ thuật, ngân hàng hay an toàn; không thấy từ khóa rủi ro không đồng nghĩa an toàn. `FLAG` là thông tin quảng cáo cần kiểm nhưng không tự chặn: thuê đất, đường riêng, setback hoặc các điều kiện có thể thông thường. `HOLD` áp dụng cho claim bất lợi trọng yếu có thể ảnh hưởng nhu cầu ở, mâu thuẫn giá/danh tính hoặc mâu thuẫn với nhu cầu bắt buộc đã xác nhận; giữ nguyên văn, nguồn và lý do. Không biến claim E1 thành kết luận pháp lý hoặc tự FAIL.
- Link `active` là kết quả kiểm ở thời điểm lưu, không đảm bảo còn bán hôm nay. `expired/not_found` ra khỏi bản đồ hiện hành; `unverified/not_checked` giữ hàng nghiên cứu với trạng thái cần kiểm, chưa đưa bản đồ chính. Mọi lần kiểm lại giữ timestamp và nguồn riêng. Không coi hồ sơ private vắng mặt là chi phí bằng 0.

## G1 — Đúng phạm vi tìm kiếm

1. Địa chỉ nguồn chỉ ra Osaka-shi; thông tin thiếu hoặc mâu thuẫn → HOLD.
2. Nhận diện loại tin nhà/căn hộ và mới/cũ theo category; subtype khác giữ nhãn, không tự nâng thành nhà độc lập.
3. Giá exact 40–50 triệu JPY cho tin đơn lẻ → PASS phạm vi; giá ngoài dải → OUT_OF_SCOPE; giá thiếu/mâu thuẫn → HOLD.
4. URL và `listing_level` đủ để xem như **tin ứng viên chưa xác minh danh tính căn**; nghi trùng giữ liên kết, không gộp cưỡng bức. Dự án/giá khoảng → project queue riêng.

G1 PASS nghiên cứu không cần hồ sơ quyền sở hữu hay xác nhận ngày vào ở; những việc đó còn mở. Loại tài sản hoặc nhu cầu chưa chốt không tự thành FAIL.

## G2 — Sàng lọc cờ tin rao và mức phù hợp sơ bộ

1. Đọc claim công khai về quyền, đường, xây lại, người thuê và bàn giao. Đường riêng/setback/thuê đất mặc định là FLAG cần kiểm, không tự HOLD; claim bất lợi trọng yếu có thể ảnh hưởng việc ở → HOLD. Xem cụ thể nội dung, không dùng keyword một mình như kết luận.
2. Kiểm mâu thuẫn quan trọng giữa giá, loại tin, hiện trạng và nội dung chi tiết; chưa giải quyết → HOLD, không chọn giá tiện nhất.
3. So thông số công khai với **nhu cầu đã xác nhận**, nếu có; không tự đặt diện tích, năm xây, phút đi bộ hay nhu cầu mới. Nhu cầu chưa chốt ghi `chưa cấu hình`, không chặn.
4. Khi đã quét nguồn có sẵn và không có cờ trọng yếu hoặc mâu thuẫn chưa giải quyết → PASS nghiên cứu, đồng thời hiển thị `chưa xác minh quyền/kỹ thuật/tài chính`. Không có trang chi tiết không được ghi là đã kiểm sạch; nêu phạm vi quảng cáo thực đã đọc và thiếu gì, chỉ HOLD nếu thiếu làm không xác định được cờ trọng yếu cụ thể, còn lại tiếp tục nghiên cứu có điều kiện.

Không cần private profile hay chấp thuận vay ở G2. FAIL pháp lý/tài chính chỉ phát sinh từ thẩm định phù hợp, không từ keyword E1.

## G3 — So sánh công khai để lập shortlist

1. G1 và G2 nghiên cứu PASS; giữ `availability` riêng và thời điểm quan sát.
2. Hiển thị giá rao exact; tính giá rao/m² **chỉ khi có đúng diện tích mẫu số dương**: căn hộ dùng `unit_m2`, nhà dùng `land_m2` hoặc `building_m2` với hai chỉ số tách riêng. Thiếu hoặc sai mẫu số → null. Đây là giá rao/m², không phải giá giao dịch, định giá hay giá hợp lý.
3. Cho xem quận, loại/mới-cũ, diện tích, ga/thời gian đi bộ đúng nguyên văn nguồn; năm xây và phí nếu có, kèm nguồn/ngày. Thiếu năm/phí/ga hoặc chưa chốt nhu cầu không tự loại.
4. Tập so sánh giá rao phải chỉ rõ cùng loại và mẫu số, khu vực, thời điểm, số tin và khác biệt còn lại; quá ít/khác mẫu hoặc thiếu dữ liệu → ghi `không đủ so sánh`, không suy định giá. So giá nhà với đất và căn hộ phải tách nhóm.
5. `G3_RESEARCH_READY` là đã mở bước so sánh, chưa phải chứng nhận tài sản: G1/G2 nghiên cứu PASS, xác định loại tin và giá exact, và **hoặc** có diện tích phù hợp loại tài sản hay claim ga/đi lại, **hoặc** người dùng chủ động gắn sao/shortlist để tìm hiểu. Thiếu thông số vẫn hiển thị rõ; sao chỉ thể hiện ý định, không chứng minh chất lượng. Chưa có comparables E2 vẫn được nghiên cứu; so sánh đã xác minh là trạng thái riêng. Không đặt top-N hay điểm cắt làm tiêu chí loại; giới hạn kỹ thuật chỉ để xử lý.

## G4 — Ưu tiên tìm hiểu, không giả điểm đầu tư

1. Giữ nguyên cờ G2, thông số so sánh G3 và độ phủ; chưa có bằng chứng → null/chưa rõ, không gán 0 hoặc mặc định trung tính.
2. Gợi ý thứ tự nghiên cứu theo **bộ lọc/sắp xếp người dùng chọn** (ví dụ giá rao, diện tích tương ứng, thời gian ga nếu parse chắc chắn), có chiều sắp xếp và số thiếu; ưu tiên người dùng gắn sao được giữ theo URL. Không tự tạo trọng số hay ngưỡng mới.
3. Dự án tương lai, giao thông và tiện ích phải ghi nguồn/ngày, trạng thái và phạm vi tác động; chưa có dữ liệu đủ thì chỉ là ý tưởng, không cộng upside chắc chắn. Không tái dùng cùng tác động để cộng nhiều mục.
4. Chưa có rubric và so sánh thích hợp → không tạo tổng 100 hay thứ hạng đầu tư. `PASS nghiên cứu` chỉ nghĩa là đã tạo hồ sơ ưu tiên công khai tối thiểu từ G3; không được hiểu là tài sản tốt hoặc có lợi nhuận.

## G5 — Thẩm định trước cam kết và mua

1. Tài chính private: giá, chi phí, vốn theo từng mốc, dự phòng, kịch bản và vay/bảo hiểm khi áp dụng; hồ sơ riêng, không xuất public. Không vay đã xác nhận → phần vay NA, vốn và lịch thanh toán vẫn áp dụng.
2. Người bán/đại diện, hồ sơ quyền, thuê đất, người thuê, giải chấp và bàn giao; người/chuyên gia phù hợp xác minh cho căn cụ thể.
3. Đất, ranh, đường, setback, quyền tiếp cận/xây sửa; kiểm thực trạng/kết cấu, kế hoạch sửa, nghĩa vụ quản lý, rủi ro vị trí bằng nguồn và độ chính xác phù hợp.
4. So giá/cost thực chất với giao dịch có thể so sánh, phí/thuế, sửa và kịch bản giữ/bán; giá rao/m² G3 không thay thế thẩm định.
5. Điều khoản đề nghị, cọc, hủy, bảo hành, thanh toán và bảo hiểm được người mua/chuyên gia hiểu; kiểm theo mốc trước đề nghị ràng buộc, trước ký/cọc, trước tất toán/bàn giao và sau bàn giao.

Mỗi mốc giữ PASS/REVIEW/FAIL, người kiểm, ngày và evidence phù hợp; G5 PASS cuối chỉ sau mọi mục áp dụng và mốc cần thiết hoàn tất. Không đủ hồ sơ → REVIEW/dừng trước nghĩa vụ tương ứng, không suy FAIL. Không tự quyết định mua hoặc ký thay.

## Ánh xạ và chuyển đổi

| Chuẩn 1.0 hiện tại | Đề xuất giữ/di chuyển |
|---|---|
| G1-01–04 | G1 mới: phạm vi, giá, loại và danh tính tin; `unverified_unit` được làm ứng viên nhưng chưa xác minh căn. |
| G1-05/06 | Fit sơ bộ ở G2; quyền sử dụng, người thuê và nhu cầu thực chứng ở G5; preference chưa xác nhận không tự loại. |
| G2-01–03 | G5: vốn, dòng tiền, vay; private, không chặn G1–G4 nghiên cứu. |
| G2-04–08 | G2 nhận cờ quảng cáo để HOLD; hồ sơ quyền/đường/kỹ thuật/hazard/quản lý xác minh chuyển G5. |
| G3-01–06 | G3 dùng so sánh tin rao mô tả; comparables giao dịch, tổng chi phí và kịch bản kiểm chứng chuyển G5. |
| G4 P/Q/L/U/S | G4 dùng để dẫn hướng ưu tiên và ghi missing, chưa tự tính điểm; giá trị điểm cũ chỉ khi đủ rubric/evidence theo chính sách được duyệt. |
| G5-01–08 | G5 mới giữ checklist và các mốc, bổ sung phần private/kiểm chứng chuyển từ G2–G3. |

Giữ ID/policy/run cũ để so sánh; tạo ID và `policy_version` mới cho gate nghiên cứu, bảng mapping và diff URL, không ghi đè v1.0. Chỉ sau khi Huy chấp thuận mới sửa code, chạy lại và công bố; phải kiểm test synthetic thiếu dữ liệu, cờ rủi ro, mâu thuẫn, dự án, giá 2 đầu, private-missing, map và không đánh đồng research PASS với verified purchase.

## Điều kiện bản đồ chính xác

Chỉ hiển thị tin/căn **không phải dự án/giá khoảng**, `G1 nghiên cứu=PASS`, `G2 nghiên cứu=PASS`, `G3_RESEARCH_READY`, không HOLD hoặc OUT_OF_SCOPE, `availability=active` theo lần kiểm gần nhất và còn thuộc bộ lọc đang chọn. Thời điểm link kiểm phải hiện rõ. `active` cũ vẫn là bằng chứng lịch sử, không khẳng định còn bán hôm nay; trước liên hệ/đề nghị phải kiểm lại. Tin `unverified/not_checked` giữ trong danh sách chờ; dự án giữ queue riêng. Có thể mở research list mà không cần đủ điểm G4 hoặc private G5.

Nếu chưa có tọa độ căn đủ tin cậy, gom theo quận tại điểm tham chiếu văn phòng quận, gắn số tin và nhãn rõ `điểm quận, không phải vị trí nhà`; URL thiếu tọa độ/không khớp quận có bộ đếm chưa đặt trên bản đồ và vẫn ở list. Không dùng tâm quận suy hazard hay địa chỉ chính xác. Bản đồ rỗng thì giải thích điều kiện và dữ liệu đang thiếu, không tự nới phạm vi hoặc ngầm hiển thị các gate HOLD.
