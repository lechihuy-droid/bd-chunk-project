# Nhà mới và chung cư mới theo chuẩn 4.0 — kết quả chạy 18/11/2026

Dữ liệu: trang chi tiết SUUMO đợt 3 (344 tin nhà riêng mới trong dải giá, 64 trang chung cư mới), giá đất và giá chung cư so sánh lấy từ snapshot 02/11. Giá là **giá rao**, chưa phải giá giao dịch. Cách tính: [chuẩn 4.0 mục 10](../../docs/standards/HOUSING-SELECTION-4.0.md).

## Nhà riêng mới

344 tin gom lại còn **289 căn**.

| Nhóm | Số căn |
|---|---:|
| A (25% chi phí ở thực/m² thấp nhất) | 50 |
| B | 46 |
| C | 48 |
| D | 48 |
| U — tin gộp nhiều lô | 92 |
| U — ước tính đất vượt giá rao | 3 |
| S — đất thuê | 2 |

| | Khoảng giữa |
|---|---|
| Chi phí ở thực/tháng | 10,8–14,3 vạn yên |
| Trên m² nhà/tháng | 998–1.420 yên |
| Tỷ lệ giữ giá (giá trị đất / giá mua) | 0,45–0,62 |

Các số này gần như trùng với lần chạy trên snapshot 02/11 (998–1.430 yên/m²), nên cách tính ổn định giữa hai lần thu.

- **Tình trạng xây** của 289 căn: 100 đã xong, 35 xong trong tháng 11, 105 xong sau đó, 49 chỉ ghi "xây sau khi ký hợp đồng". Nhóm A có đủ cả bốn loại.
- **Ước tính đất cấp quận (thô) dồn vào nhóm A:** 19/50 căn A, so với 8–12 căn ở mỗi nhóm khác. Căn A dựa trên ước tính cấp quận cần kiểm lại giá đất trước khi tin.
- **A tập trung ở** 西淀川区, 平野区, 東住吉区; **D nhiều ở** 港区, 住吉区.

### Không mất phí môi giới

62 căn: 46 căn người bán trực tiếp hoặc đại lý, 16 căn trang ghi rõ miễn phí môi giới. Phân bố: A 10, B 14, C 17, D 10, U 11. File: [new-house-no-brokerage.csv](new-house-no-brokerage.csv).

## Chung cư mới

64 trang gồm 49 dự án và 15 căn lẻ do môi giới bán lại.

| Tình trạng của 49 dự án | Số |
|---|---:|
| Khoảng giá chạm 4.000–5.000万 | 29 |
| Chưa công bố giá | 17 |
| Có giá nhưng chưa công bố phí | 2 |
| Ngoài dải | 1 |

- **Tỷ lệ giữ giá 20 năm của khu** tính được cho 26/49 dự án; khoảng giữa 0,58–0,75. 23 dự án còn lại không đủ chung cư gần mới cùng khu để so.
- **Phí quản lý + quỹ sửa chữa** khoảng giữa 260–395 yên/m²/tháng. Căn nhỏ ở trung tâm (北区, 都島区) lên tới khoảng 580 yên/m².
- 14/15 căn lẻ môi giới bán lại đều trên 5.000万 (phần lớn ở リバーガーデン四天王寺), nên không liên quan dải giá.

**Danh sách theo dõi:** [watchlist-new-condo.csv](watchlist-new-condo.csv), 25 dự án (19 từ SUUMO, 6 chỉ có trên Yahoo!) chưa công bố giá hoặc phí. Cần kiểm lại khi dự án công bố.

## File

- [net-cost-new-house.csv](net-cost-new-house.csv): 289 căn nhà riêng mới, xếp nhóm.
- [new-condo-projects.csv](new-condo-projects.csv): 64 dòng chung cư mới với các chỉ số trên.
- [summary-new-builds.json](summary-new-builds.json): số tổng hợp.

## Giới hạn

1. 92 tin gộp nhiều lô chưa xếp hạng. Muốn xếp được cần tải bảng giá từng lô (trang chi tiết lô).
2. Giá đất vẫn dựa trên giá rao nhà cũ, chưa phải giá giao dịch hay 路線価.
3. Chung cư mới chưa có chi phí ở thực; cần bảng giá theo từng căn.
4. Phí mua khi không qua môi giới là giả định.
