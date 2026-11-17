# Chuẩn chọn nhà 4.0 — xếp hạng theo chi phí ở thực

Ngày: 17/11/2026. `policy_version = HOUSING-SELECTION-4.0`. Trạng thái: **đã chạy thử trên snapshot SUUMO 02/11; các giả định ở mục 5 chờ Huy xác nhận**.

Chuẩn này thay phần "năm trụ" trong [đề xuất v4](../proposals/2026-11-16-nha-tot-v4-va-mo-rong-nguon.md) và thay nhóm ưu tiên P1/P2/P3 của `HOUSING-SELECTION-3.0`. Các tài liệu cũ giữ nguyên để đối chiếu. Checklist thẩm định trước khi ký (G5) không đổi.

Đây là công cụ xếp thứ tự xem nhà. Nó không phải định giá, dự báo tăng giá, hay xác nhận được mua.

## 1. Tiêu chí

> Trong các căn bán lại được cho người mua vay ngân hàng bình thường, ưu tiên căn có **chi phí ở thực mỗi tháng trên mỗi m²** thấp nhất.

**Chi phí ở thực/tháng = (giá mua × (1 + phí mua) − giá trị còn lại × (1 − phí bán)) ÷ số tháng giữ + chi phí định kỳ**

Lý do chọn: mọi bộ tiêu chí trước đều nêu nguyên tắc "căn đáng mua phải đứng vững khi giá không tăng và bán lại được sau 10–20 năm", nhưng chưa bộ nào đo nguyên tắc đó. Con số này đo trực tiếp, và so được chung cư với nhà riêng, mới với cũ.

## 2. Điều kiện xem riêng (không xếp hạng chung)

| Điều kiện | Nguồn trong dữ liệu |
|---|---|
| Không phải sở hữu đất, hoặc có ghi đất thuê | `advertised_rights`, cờ `leasehold` |
| Xây từ 1981 trở về trước | `built_year` |
| Nhà liền kề, ghi không xây lại được | cờ `terrace`, `rebuild` |
| Đang ở hàng chờ làm rõ của bản 3.0 (cho thuê, mâu thuẫn dữ liệu, link hỏng) | `selection_queue` khác `ORDINARY` |

Các căn này nhận nhóm **S**. Chúng không bị xóa và không bị coi là xấu; chỉ không so chung với nhà thông thường.

## 3. Giá trị còn lại

Không dùng dự báo tăng giá. Giá trị còn lại không bao giờ vượt giá mua.

**Chung cư:** giá mua × tỷ lệ giữ giá của khu.

- Tỷ lệ giữ giá = trung vị giá/m² của chung cư **già hơn 20 năm** ÷ trung vị giá/m² của chung cư **cùng tuổi** với căn đang xét, trong cùng khu, diện tích trong khoảng 0,7–1,3 lần.
- Ưu tiên tính theo ga; không đủ 8 nhóm căn ở mỗi vế thì tính theo quận; vẫn không đủ thì **chưa biết**.
- Áp tỷ lệ vào giá của chính căn đó, nên căn giữ nguyên mức đắt/rẻ so với hàng xóm.

**Nhà riêng:** diện tích đất × giá đất ước tính. Phần nhà coi như không còn giá trị khi bán.

- Giá đất ước tính = trung vị giá rao/m² đất của nhà cũ từ 30 năm tuổi trong cùng khu.
- Ưu tiên theo ga (từ 5 nhóm), không đủ thì theo quận (từ 8 nhóm) và gắn nhãn "thô".
- Nếu ước tính đất bằng hoặc vượt giá rao thì không xếp hạng, ghi `land_estimate_exceeds_price`.

## 4. Chi phí định kỳ

- Chung cư: phí quản lý + quỹ sửa chữa hằng tháng theo tin rao. Thiếu thì chưa biết.
- Nhà riêng: khoản dự phòng bảo trì giả định theo diện tích nhà (mục 5), vì nhà riêng không có quỹ sửa chữa và nếu bỏ qua thì luôn trông rẻ hơn chung cư.

## 5. Tham số và giả định

File: [`policy.json`](../../round3-20261117/selection4/policy.json).

| Tham số | Giá trị | Tình trạng |
|---|---|---|
| Thời gian giữ | 20 năm | **Tôi giả định**, trong khoảng 10–20 năm Huy đã nêu |
| Phí mua | 7% giá mua | **Tôi giả định** |
| Phí bán | 4% giá bán | **Tôi giả định** |
| Dự phòng bảo trì nhà riêng | 200 yên/m² nhà/tháng | **Tôi giả định**, chưa có nguồn |
| Kịch bản xấu | Giá trị còn lại giảm thêm 20% | Để hiển thị khoảng, không phải dự báo |
| Cửa sổ năm xây khi so sánh | ±5 năm | |
| Số nhóm so sánh tối thiểu | 8 (đất theo ga: 5) | |

Chưa tính: lãi vay, thuế tài sản, bảo hiểm, chi phí cải tạo nhà cũ, việc quỹ sửa chữa tăng theo tuổi nhà, phí môi giới thực tế theo loại người bán.

## 6. Nhóm kết quả

Chia theo tứ phân vị **trong từng loại nhà**, chỉ gồm căn qua mục 2 và tính được.

| Nhóm | Ý nghĩa |
|---|---|
| A | 25% chi phí ở thực/m² thấp nhất — xem trước |
| B, C | Hai nhóm giữa |
| D | 25% cao nhất |
| U | Chưa tính được; kèm lý do và việc cần bổ sung |
| S | Xem riêng theo mục 2 |

U không phải xếp hạng thấp. Mỗi căn A phải kèm: số nhóm so sánh, mức so sánh (ga hay quận), và chi phí ở kịch bản xấu.

## 7. Kết quả chạy thử

Dữ liệu: 1.108 căn gom từ 1.753 tin SUUMO trong dải 4.000–5.000万, snapshot 02/11/2026. **Dùng giá rao, chưa phải giá giao dịch.** File: [`net-cost.csv`](../../round3-20261117/selection4/net-cost.csv), [`summary.json`](../../round3-20261117/selection4/summary.json). Script: [`net_cost.py`](../../round3-20261117/tools/net_cost.py).

| Loại | Căn | A | B | C | D | U | S |
|---|---:|---:|---:|---:|---:|---:|---:|
| Chung cư cũ | 635 | 103 | 106 | 102 | 103 | 176 | 45 |
| Nhà riêng cũ | 254 | 52 | 53 | 52 | 52 | 29 | 16 |
| Nhà riêng mới | 219 | 49 | 49 | 49 | 49 | 20 | 3 |

| Loại | Chi phí ở thực/tháng (khoảng giữa) | Trên m²/tháng | Tỷ lệ giữ giá |
|---|---|---|---|
| Chung cư cũ | 9,7–11,8 vạn yên | 1.362–1.865 yên | 0,61–0,70 |
| Nhà riêng cũ | 9,0–13,0 vạn yên | 795–1.322 yên | 0,51–0,76 |
| Nhà riêng mới | 10,9–14,5 vạn yên | 1.000–1.430 yên | 0,45–0,62 |

So với bản 3.0:

- Nhà riêng nay xếp được 405/473 căn; bản 3.0 gần như không xếp được.
- Trong 165 chung cư thuộc P1 cũ, 139 căn tính được và rải gần đều: 32 căn A, 36 B, 33 C, 38 D (còn lại 20 U, 6 S). Hai tiêu chí đo hai thứ khác nhau.
- Chung cư nhóm D tập trung ở 中央区 và 北区; nhóm A nhiều ở 鶴見区, 淀川区, 都島区.

## 8. Giới hạn đã biết

1. **Giá rao thay cho giá giao dịch.** Bản dùng để quyết định phải thay bằng giá giao dịch của MLIT.
2. **So nhà hôm nay với nhà già hơn 20 năm hôm nay là ảnh chụp cắt ngang.** Ở trung tâm, chung cư mới phần lớn là tháp cao tầng còn chung cư cũ thì không, nên tỷ lệ giữ giá của 中央区 và 北区 nhiều khả năng bị tính thấp hơn thực tế.
3. **Giá đất cho nhà riêng còn thô.** 107/405 căn nhà riêng xếp hạng được phải dùng giá đất cấp quận. Cần thay bằng 路線価 hoặc giá giao dịch đất.
4. **176 chung cư chưa tính được**, chủ yếu là tòa xây trước khoảng 1995: không đủ chung cư già hơn 20 năm cùng khu để so.
5. **Mẫu theo ga có khi chỉ 8 nhóm**, nên tỷ lệ giữ giá sát 1,0 ở vài căn đứng đầu cần kiểm lại trước khi tin.
6. **Gom căn còn sót trùng** khi SUUMO ghi địa chỉ ở hai mức chi tiết khác nhau (ví dụ 鶴見1 và 鶴見1-6-109).
7. Nhà cũ từ 25 năm tuổi được gắn `renovation_cost_not_included`.

## 9. Điều kiện nghiệm thu khi triển khai chính thức

- Thay giá rao bằng giá giao dịch; ghi số mẫu và kỳ giao dịch cho từng căn.
- Thêm tin trùng không làm đổi nhóm của căn nào.
- Đổi tham số ở mục 5 thì toàn bộ chạy lại; không sửa riêng một căn.
- Không căn nào vào nhóm D hoặc bị loại chỉ vì thiếu dữ liệu.
- Mỗi căn A có đủ ba thông tin ở mục 6.
- Kiểm tay 10 căn mỗi loại, gồm căn đứng đầu, căn sát ranh A/B và một căn U.
