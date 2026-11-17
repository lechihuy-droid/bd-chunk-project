# Brief cho Codex/Luna chạy trên máy Windows của Huy — đợt 2L

Ngày: 17/11/2026. Người viết: Claude (phiên đám mây). Người chạy: Luna-Data, một instance cho mỗi trang. Reviewer: Terra (instance khác).

## Vì sao phải chạy ở máy này

Bốn trang dưới đây chặn máy chủ đám mây (xem [khảo sát nguồn](../../round3-20261117/wave1/SOURCE-SURVEY.md)). Chưa biết chúng có cho máy ở Nhật vào hay không; bước 1 của mỗi trang là kiểm điều đó.

| Trang | Kết quả từ đám mây ngày 17/11 |
|---|---|
| athome (`www.athome.co.jp`) | 5 request đầu tải được; request thứ 6 trả trang "認証中" (yêu cầu xác thực) |
| LIFULL HOME'S (`www.homes.co.jp`) | HTTP 202, thân rỗng ngay request đầu |
| 不動産ジャパン (`www.fudousan.or.jp`) | HTTP 403 kể cả robots.txt |
| 近鉄不動産 (`www.kintetsu-re.co.jp`) | HTTP 403 kể cả robots.txt |

Thêm một việc cùng đợt: **làm mới SUUMO** trong dải giá, vì snapshot hiện có là ngày 02/11.

## Phạm vi dữ liệu

Osaka-shi 24 quận; chung cư cũ, nhà riêng cũ, nhà riêng mới, chung cư mới; giá chính xác 4.000–5.000万 gồm hai đầu. Chỉ trang danh sách; trang chi tiết để đợt sau.

## Quy tắc bắt buộc

1. Một trang nguồn một luồng. Các trang khác nhau được chạy song song, tối đa 3 instance.
2. Đọc và lưu robots.txt cùng trang điều khoản sử dụng **trước** request dữ liệu đầu tiên. Nếu cấm truy cập tự động hoặc cấm đường dẫn cần dùng thì dừng trang đó và báo.
3. Khoảng cách tối thiểu giữa hai request: 8 giây cho athome và HOME'S, 5 giây cho các trang còn lại.
4. Gặp 401/403/429, trang xác thực hoặc thân rỗng: **dừng ngay trang đó**. Không đổi IP, không proxy, không giả danh, không tự giải xác thực bằng máy, không gọi API nội bộ. Ghi lại request thứ mấy thì bị chặn.
5. Nếu Huy tự bấm qua bước xác thực trong trình duyệt đang mở thì được chạy tiếp, với khoảng cách gấp đôi. Bị chặn lần hai thì dừng hẳn.
6. Dùng trình duyệt thật (Playwright có hiển thị) cho athome và HOME'S; các trang khác thử HTTP thường trước.
7. Trần request: athome 400, HOME'S 400, 不動産ジャパン 200, 近鉄 100, SUUMO 300. Hết trần thì dừng và báo phần thiếu.
8. HTML gốc lưu ngoài thư mục `housing/` của repo, kèm URL, thời điểm tải và hash. **Không commit dữ liệu thu được của các trang này lên GitHub** cho đến khi Huy quyết định về việc công khai.
9. Chỉ lưu dữ kiện (giá, diện tích, địa chỉ, năm xây…). Không lưu ảnh và đoạn mô tả quảng cáo.

## Điều đã biết, dùng để khỏi dò lại

**athome**

- Danh sách chung cư cũ toàn Osaka-shi: `/mansion/chuko/osaka/osaka-locate/list/`, phân trang `/list/page2/`. 30 tin/trang, 7.321 tin mọi giá.
- Nhà riêng: thay bằng `/kodate/chuko/…` và `/kodate/shinchiku/…`. Đường dẫn `/mansion/shinchiku/osaka/osaka-locate/list/` trả 404; phải dò đường dẫn chung cư mới.
- Thêm `?PRICEFROM=kp009&PRICETO=kp110` vào URL **không** lọc được ở HTML máy chủ trả về (vẫn ra 7.321). Cần chọn giá trên giao diện rồi lấy URL kết quả, hoặc sắp theo giá (`SORT=7`) và chỉ đọc các trang rơi vào dải giá.
- Thẻ tin có tên tòa, tầng, bố trí phòng, năm/tháng xây, kết cấu, diện tích, địa chỉ, ga.

**LIFULL HOME'S**

- robots.txt cho phép và liệt kê sitemap trang chi tiết theo loại, ví dụ `sitemap-bukken-detail-mansion-chuko.xml`, `sitemap-bukken-detail-kodate-chuko.xml`. Nếu trang danh sách khó lọc, sitemap là đường thay thế hợp lệ.

**SUUMO**

- Dùng crawler và cache sẵn có của đợt `ver2.0-20261102`. Chỉ tải trang danh sách đã lọc giá 4.000–5.000万, 4 loại × 24 quận; nếu trang không lọc được giá thì báo lại, không tải cả kho.
- Thử lại 6 tuyến chung cư mới còn thiếu.

## Đầu ra của mỗi trang

1. `listings-<source>.csv` theo đúng [lược đồ chung](../../round3-20261117/wave0/SCHEMA.md).
2. `requests-<source>.log`: thời điểm, mã HTTP, URL.
3. `pages-<source>.json`: mỗi trang danh sách ghi số thẻ nhìn thấy, số dòng trích được, tổng số trang báo.
4. Bản lưu robots.txt và điều khoản, kèm một dòng kết luận.

## Điều kiện xong

- Số dòng trích được khớp tổng số trang báo, hoặc ghi rõ thiếu bao nhiêu và vì sao.
- Đối chiếu tay 10 tin mỗi trang: giá, diện tích, năm xây, địa chỉ, ga đúng với trang gốc.
- Không có dòng nào ngoài dải giá hoặc ngoài Osaka-shi.
- Terra kiểm lại 10 tin khác, không phải người viết parser.
- Chạy `round3-20261117/tools/merge_sources.py` (xem repo) để khớp với bảng căn và báo số căn mới theo loại.

## Báo lại cho Huy

Mỗi trang một dòng: tải được hay bị chặn (ở request thứ mấy), số tin trong dải, số căn mới so với bảng căn, phần còn thiếu.
