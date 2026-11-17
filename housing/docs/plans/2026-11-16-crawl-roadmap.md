# Lộ trình crawl cho subagent — đợt 3 (bản sửa 17/11)

Trạng thái: **chờ Huy duyệt, chưa chạy**. Kế thừa [đề xuất v4](../proposals/2026-11-16-nha-tot-v4-va-mo-rong-nguon.md) và phân vai Terra/Luna trong [kế hoạch 03/11](2026-11-03-v2-gate-execution-plan.md).

Thay đổi so với bản 16/11 theo yêu cầu của Huy:

- **Các trang ngoài SUUMO đi trước**, mục tiêu là không lọt căn. SUUMO làm mới sau cùng.
- **Chọn trang trước, quy trình crawl sau.**
- Việc dữ liệu công khai trên GitHub Pages **để sau**, không nằm trong lộ trình này. Dữ liệu thô của đợt này chỉ lưu nội bộ.

Môi trường viết tài liệu này không mở được trang Nhật. Danh sách trang ở Phần 2 dựa trên hiểu biết chung về thị trường và kết quả tìm kiếm, **chưa kiểm trực tiếp từng trang**; bước khảo sát ở Phần 3 dùng để xác nhận hoặc loại.

## 1. Đầu vào đã có (không hỏi lại Huy)

| Đầu vào | Giá trị |
|---|---|
| Khu vực | Osaka-shi, 24 quận |
| Loại | Nhà riêng và chung cư, mới và cũ |
| Giá | 4.000–5.000万, gồm hai đầu |
| Mục đích | Để ở, giữ 10–20 năm, ưu tiên giữ giá và bán lại |
| Quyền đất | Ưu tiên sở hữu đất; đất thuê và nhà liền kề xem riêng |
| Loại trừ | Không xây lại được; đang cho thuê không bàn giao trống |
| Diện tích, số phòng, tuổi nhà, chỗ xe | Chưa có → không lọc, chỉ thu và hiển thị |

## 2. Chọn trang

### 2.1 Tiêu chí chọn

1. Có khả năng chứa căn **không có trên SUUMO** (nguồn tin khác với SUUMO).
2. Lọc được theo Osaka-shi, loại nhà và giá ngay trên trang danh sách, để không phải tải cả kho.
3. Robots.txt và điều khoản không cấm việc đọc trang danh sách và chi tiết công khai.
4. Trang chi tiết có các trường cần cho v4: loại người bán (取引態様), tổng số căn, tầng, hướng, phí, quyền đất, đường.

### 2.2 Danh sách đề xuất

**Nhóm A — crawl đầy đủ (3 trang).** Đây là ba nguồn có tập môi giới khác SUUMO rõ nhất.

| Trang | Vì sao chọn | Rủi ro |
|---|---|---|
| athome | Mạng hội viên là môi giới vừa và nhỏ ở địa phương, nhiều công ty không trả phí đăng SUUMO | Trang có thể dựng nội dung bằng JavaScript |
| LIFULL HOME'S | Cổng lớn thứ hai cho nhà cũ; tập công ty đăng khác SUUMO một phần | Điều khoản có thể chặt; cần đọc kỹ |
| 不動産ジャパン | Cổng của các hiệp hội môi giới; hội viên được đẩy tin tự động, kể cả công ty không mua quảng cáo ở cổng thương mại | Dữ liệu ít trường hơn, cập nhật chậm hơn |

**Nhóm B — khảo sát trước, chỉ crawl trang nào có căn riêng (8 trang).** Môi giới lớn thường đăng cả lên SUUMO, nhưng có tin đăng trang riêng trước hoặc chỉ ở trang riêng.

| Trang | Ghi chú |
|---|---|
| 三井のリハウス, 住友不動産ステップ, 東急リバブル, 野村の仲介+ | Bốn môi giới lớn toàn quốc |
| 近鉄不動産, 阪急阪神不動産, 福屋不動産販売, 大京穴吹不動産 | Mạnh ở Kansai; 大京穴吹 có căn cải tạo tự bán |

**Nhóm C — chỉ dùng để đối chiếu, không crawl làm nguồn.**

| Trang | Vai trò |
|---|---|
| ニフティ不動産 | Gộp tin từ 8 trang; dùng lấy mẫu kiểm xem sau nhóm A còn lọt bao nhiêu |
| Yahoo!不動産 | Phần lớn tin lấy từ đối tác; khảo sát độ trùng, chỉ nâng lên nhóm A nếu có căn riêng đáng kể |

**Chưa đưa vào đợt này:** trang của từng chủ đầu tư chung cư mới và từng công ty mua lại–bán lại (xử lý qua trường 取引態様 sau khi có dữ liệu nhóm A), tin chỉ dành cho hội viên (cần đăng nhập), đấu giá, 家いちば, 空き家バンク.

### 2.3 Quy tắc chốt danh sách sau khảo sát

- Trang nhóm A bị loại nếu robots.txt hoặc điều khoản cấm, hoặc không lọc được theo khu vực và giá.
- Trang nhóm B được crawl nếu trong mẫu 30 căn có từ 3 căn trở lên không khớp với bảng căn hiện có (ngưỡng do tôi đề xuất).
- Agent chính chốt danh sách cuối và ghi lý do cho từng trang, kể cả trang bị loại.

## 3. Quy trình crawl

### 3.1 Nguyên tắc

- Một trang nguồn chỉ một subagent, một luồng. Song song là giữa các trang khác nhau, tối đa 3 subagent cùng lúc.
- Cách nhau ít nhất 3 giây. Gặp 401/403/429 hoặc trang thử thách thì dừng cả lane. Không đăng nhập, không proxy, không gọi API nội bộ của trang.
- HTML gốc lưu bất biến kèm hash và thời điểm tải, không đưa lên repo công khai.
- Mỗi lane có trần request; hết trần thì dừng và báo phần thiếu.
- Người viết parser không tự review. Agent chính đối soát trước khi chuyển đợt.

### 3.2 Đợt 0 — Chuẩn bị, không gọi mạng

| Lane | Ai | Việc | Điều kiện xong |
|---|---|---|---|
| 0A Bảng căn gốc | Terra thiết kế, Luna chạy | Gom khoảng 1.750 tin SUUMO trong phạm vi (snapshot 02/11) thành bảng căn, theo khóa ở mục C3 của đề xuất v4 | Thêm tin trùng không đổi số căn; tin nghi trùng giữ tách có nhãn |
| 0B Lược đồ chung | Terra | Định nghĩa bảng tin chuẩn hóa dùng cho mọi nguồn (thêm cột `source`), danh sách trường bắt buộc và lý do thiếu | Luna đọc là viết được parser, không phải hỏi lại |

Bảng căn gốc là thước đo: một căn ở trang khác được tính là "lọt" khi không khớp với bảng này.

### 3.3 Đợt 1 — Khảo sát nguồn

Mỗi subagent nhận một lô trang và trả về một phiếu cho mỗi trang.

| Lane | Ai | Trang | Trần request mỗi trang |
|---|---|---|---:|
| 1A | Terra-Research | athome, LIFULL HOME'S, 不動産ジャパン | 25 |
| 1B | Luna-Data | 4 môi giới toàn quốc | 15 |
| 1C | Luna-Data (instance khác) | 4 môi giới Kansai, Yahoo!不動産 | 15 |

Nội dung phiếu:

1. Robots.txt và điều khoản: bản lưu nguyên văn, kết luận được hay không được đọc trang danh sách và chi tiết.
2. URL tìm kiếm theo Osaka-shi × 4 loại × giá 4.000–5.000万; số kết quả mỗi loại; số tin mỗi trang; cách phân trang.
3. Dạng dữ liệu: HTML tĩnh, JSON nhúng, hay phải dựng bằng trình duyệt.
4. Trường có trên trang danh sách và trang chi tiết so với lược đồ 0B.
5. Mẫu 30 căn đầu (trộn loại) khớp với bảng căn gốc: bao nhiêu căn không có trên SUUMO.

Agent chính chốt danh sách trang theo mục 2.3 rồi mới mở đợt 2.

### 3.4 Đợt 2 — Crawl các trang ngoài SUUMO

Ba trang nhóm A chạy song song, mỗi trang một subagent. Trang nhóm B được chọn chạy ở lượt kế tiếp, cũng tối đa 3 trang một lượt.

Mỗi trang đi qua cùng năm bước:

| Bước | Việc | Điều kiện qua bước |
|---|---|---|
| 1 Parser | Terra viết parser theo lược đồ 0B, thử trên các trang đã lưu ở đợt 1 | Đối chiếu tay 10 tin: giá, diện tích, năm xây, ga, quyền đất đúng |
| 2 Danh sách | Luna tải toàn bộ trang danh sách đã lọc khu vực và giá, 4 loại | Số tin thu được khớp số kết quả trang báo, hoặc ghi rõ phần thiếu |
| 3 Khớp căn | Khớp từng tin với bảng căn; tách ba nhóm: đã có, mới, nghi trùng | Tổng ba nhóm bằng số tin |
| 4 Chi tiết | Tải trang chi tiết cho căn **mới** và căn nghi trùng; căn đã có chỉ tải khi SUUMO thiếu trường | Tỷ lệ có dữ liệu theo trường |
| 5 Báo cáo | Số căn mới theo loại và quận; công ty đăng nào chỉ xuất hiện ở trang này | Reviewer độc lập kiểm 10 căn "mới" xem có thật là không có trên SUUMO |

Trần request: 600 cho mỗi trang nhóm A, 250 cho mỗi trang nhóm B.

Sau mỗi trang, bảng căn được cập nhật, nên trang chạy sau chỉ tải chi tiết cho căn chưa ai có.

### 3.5 Đợt 3 — Làm mới SUUMO và kiểm lọt

| Lane | Ai | Việc | Trần request |
|---|---|---|---:|
| 3S | Luna-Data | SUUMO: trang danh sách đã lọc giá, 4 loại × 24 quận; chi tiết cho tin mới hoặc đổi giá so với 02/11; chi tiết 309 tin dự án; thử lại 6 tuyến chung cư mới còn thiếu | 900 |
| 3K | Terra-Research | Kiểm lọt: lấy mẫu trên ニフティ不動産 ở 3 quận × 2 loại, khớp với bảng căn đã gộp mọi nguồn | 40 |
| 3M | Luna-Data (instance khác) | MLIT: tải file giá giao dịch 8 quý gần nhất và lớp ngập, triều cường, sóng thần của Osaka-fu | 40 |

Nếu 3K vẫn thấy căn không có trong bảng, ghi nguồn của các căn đó và quay lại mục 2.3 để xét thêm trang.

### 3.6 Đợt 4 — Tổng hợp

| Lane | Ai | Việc | Điều kiện xong |
|---|---|---|---|
| 4A | Terra-Research | Gắn giao dịch tương đồng và mức thiên tai cho từng căn | Mỗi căn có số mẫu và mức, hoặc lý do thiếu |
| 4B | Terra-Engine | Chấm năm trụ theo v4 | Chung cư và nhà riêng xếp riêng; không căn nào bị loại vì thiếu dữ liệu |
| 4C | Terra-Reviewer | Kiểm 20 căn mẫu | Không có căn trùng trong danh sách |
| 4D | Luna-View | Danh sách xem nhà 20–30 căn, bản nội bộ | Mỗi căn ghi nguồn, lý do, việc còn thiếu |

## 4. Ước lượng

| Đợt | Request tối đa | Ghi chú |
|---|---:|---|
| 0 | 0 | |
| 1 | khoảng 210 | 11 trang khảo sát |
| 2 | 1.800 cho nhóm A; thêm 250 cho mỗi trang nhóm B được chọn | Lane dài nhất khoảng 30 phút ở 3 giây/request |
| 3 | khoảng 980 | |

Đây là trần, không phải dự báo.

## 5. Đăng ký API MLIT

Chưa cần. Lane 3M tải file công khai; chỉ khi không tải được mới cần Huy đăng ký khóa.

## 6. Cần Huy duyệt

1. Danh sách trang ở mục 2.2 (thêm, bớt, hoặc đổi nhóm).
2. Cho chạy đợt 0 và đợt 1; đợt 2 mở sau khi có kết quả khảo sát.
