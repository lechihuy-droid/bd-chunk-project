# Kết quả đợt 0 và đợt 1 — bảng căn gốc và khảo sát nguồn

Chạy ngày 17/11/2026 (UTC 00:10–00:19) từ máy chủ đám mây của phiên làm việc, không phải từ máy ở Nhật. Tổng 54 request tới 12 trang (12 robots.txt + 42 trang), cách nhau 3–4 giây, một luồng. Nhật ký: [requests.log](requests.log). HTML gốc không đưa vào repo.

**Chưa làm:** chưa đọc điều khoản sử dụng của trang nào (mới đọc robots.txt). Việc này phải xong trước khi crawl ở đợt 2.

## Đợt 0 — Bảng căn gốc

| Loại | Tin SUUMO trong dải giá | Căn sau khi gom |
|---|---:|---:|
| Chung cư cũ | 1.162 | 635 |
| Nhà riêng cũ | 329 | 254 |
| Nhà riêng mới | 262 | 219 |
| **Tổng** | **1.753** | **1.108** |

- 44 nhóm có các tin lệch giá nhau (trung vị lệch 4,6%); 20 tin thiếu trường nên không gộp.
- Giới hạn: SUUMO không cho tên tòa và tầng, nên hai căn cùng tòa cùng diện tích khác tầng đang bị gộp.
- File: [properties.csv](../wave0/properties.csv), [listing-property-links.csv](../wave0/listing-property-links.csv), [lược đồ chung](../wave0/SCHEMA.md).

## Đợt 1 — Từng trang

| Trang | Truy cập từ đám mây | robots.txt với trang danh sách/chi tiết | Lọc Osaka-shi + giá | Dữ liệu | Số tin |
|---|---|---|---|---|---|
| Yahoo!不動産 | Được | Cho phép đường dẫn có `?page=`; cấm `start=` và tham số dạng `[x]=` | Được: `/search/06/27/271/?p_from=40000000&p_to=50000000` (đơn vị yên) | HTML tĩnh; có tên tòa, tổng số căn, tầng, hướng, công ty đăng | Trong dải: 194 chung cư cũ, 88 nhà cũ, 134 nhà mới |
| 住友不動産ステップ | Được | Cho phép; cấm `/search/list/` và `/mapsearch/` | Được theo quận: `/mansion/area_27/list_27_1xx/?hanbaiKakakuMin=4000&hanbaiKakakuMax=5000` | HTML tĩnh (mã cp932); có tên tòa, tầng, hướng | 555 chung cư cũ toàn Osaka-shi, mọi giá |
| 三井のリハウス | Được | Cho phép | Theo quận: `/buy/mansion/prefecture/27/city/271xx/`; tham số giá chưa tìm | HTML tĩnh, 30 tin/trang; có tên tòa | 北区 309, 中央区 206, 西区 154 (mọi giá) |
| 野村の仲介+ | Được | Cho phép; cấm `eki_Search` | Osaka-shi: `/mansion/area_osaka/271/`; tham số giá chưa tìm | HTML tĩnh, 40 tin/trang; có tên tòa, tầng, hướng, tổng số căn | 1.003 chung cư cũ toàn Osaka-shi, mọi giá |
| 東急リバブル | Được | Cho phép (cấm `/kounyu/kw/*?*`) | Theo quận: `/kounyu/chuko-mansion/osaka/a271xx/` (URL đoán, tải được); tham số giá chưa tìm | HTML có nội dung; có tên tòa, tầng, hướng | 中央区 158 (mọi giá) |
| 大京穴吹不動産 | Được | Cho phép | Theo quận: `/buy/mansion/p27/c271xx/`; tham số giá chưa tìm | HTML tĩnh, 20 tin/trang; có tên tòa, tầng, hướng, tổng số căn | 373 chung cư cũ toàn Osaka-fu; 北区 59, 中央区 40, 西区 28 |
| 福屋不動産販売 | Được | Cho phép | Chưa tìm được URL Osaka-shi; bộ lọc gửi bằng form `ds[..]` | Chưa xem trang danh sách | 1.814 chung cư toàn Osaka-fu |
| athome | **Bị chặn sau 5 request**: trang "認証中" (yêu cầu xác thực) | Không có nhóm `User-agent: *`; chỉ cấm một số bot có tên | Osaka-shi: `/mansion/chuko/osaka/osaka-locate/list/`; tham số giá trên URL không có tác dụng | HTML tĩnh, 30 tin/trang; có tên tòa, tầng | 7.321 chung cư cũ toàn Osaka-shi, mọi giá |
| LIFULL HOME'S | **Bị chặn ngay**: HTTP 202, thân rỗng | Cho phép; liệt kê sitemap trang chi tiết theo từng loại nhà | Chưa xem được | — | — |
| 不動産ジャパン | **Bị chặn ngay**: 403 kể cả robots.txt | Không đọc được | — | — | — |
| 近鉄不動産 | **Bị chặn ngay**: 403 kể cả robots.txt | Không đọc được | — | — | — |
| 阪急阪神不動産 | Lỗi kết nối TLS tới `www.8111.com`; tên miền tôi dùng có thể sai | — | — | — | — |

Theo quy tắc của lộ trình, gặp trang xác thực hoặc 403 thì dừng, không tìm đường vòng. Bốn trang bị chặn nhiều khả năng chặn dải IP máy chủ đám mây hoặc IP ngoài Nhật; điều này chưa được kiểm chứng.

## Mẫu so khớp với bảng căn gốc

Lấy các căn trong dải 4.000–5.000万 trên những trang đã tải, khớp theo địa chỉ cấp chome + diện tích + năm xây.

| Trang | Loại | Mẫu | Khớp | Không khớp |
|---|---|---:|---:|---:|
| Yahoo!不動産 | Chung cư cũ | 39 | 36 | 3 |
| Yahoo!不動産 | Nhà riêng cũ | 8 | 5 | 3 |
| Yahoo!不動産 | Nhà riêng mới | 1 | 1 | 0 |
| 住友不動産ステップ | Chung cư cũ | 10 | 6 | 4 |
| 野村の仲介+ | Chung cư cũ | 5 | 4 | 1 |
| 大京穴吹不動産 | Chung cư cũ | 4 | 3 | 1 |
| 三井のリハウス | Chung cư cũ | 2 | 1 | 1 |
| **Tổng** | | **69** | **56** | **13** |

Kiểm lại 12 trong 13 căn không khớp với toàn bộ 11.463 tin SUUMO (mọi giá):

- **4 căn có trên SUUMO nhưng ở giá cao hơn dải** (5.150–6.380万, cùng khu và cùng diện tích). Có hai khả năng chưa phân biệt được: căn đã giảm giá sau 02/11, hoặc là căn khác tầng trong cùng tòa.
- **8 căn hoàn toàn không có trên SUUMO**: 5 chung cư (鶴見区, 西区, 北区, 西淀川区, 此花区) và 3 nhà riêng cũ (福島区, 浪速区, 天王寺区).
- Căn thứ 13 (野村, 北区大深町, xây 2025, 4.280万) nghi do biểu thức trích giá của tôi cắt sai; không tính.

Cách đọc con số này:

- Tỷ lệ không có trên SUUMO vào khoảng 8/68 ≈ 12%, nhưng **mẫu nhỏ và bị nhiễu**: snapshot SUUMO đã 15 ngày tuổi, nên tin mới đăng sau 02/11 cũng bị tính là "lọt".
- Biểu thức trích dữ liệu là bản viết nhanh cho khảo sát, chỉ bắt được một phần số thẻ trên mỗi trang (ví dụ 8/88 nhà cũ của Yahoo!).
- Kết luận chắc chắn được: có căn trong dải giá nằm ngoài SUUMO, và có trường hợp cùng căn nhưng giá ở trang khác thấp hơn. Chưa kết luận được tỷ lệ.

## Danh sách trang chốt cho đợt 2

| Nhóm | Trang | Lý do |
|---|---|---|
| Crawl ngay từ đám mây | Yahoo!不動産 | Dễ nhất: lọc được cả thành phố và giá trong một URL, dữ liệu giàu trường |
| Crawl ngay từ đám mây | 住友不動産ステップ, 三井のリハウス, 野村の仲介+, 東急リバブル, 大京穴吹不動産 | Tải được, HTML tĩnh, có tên tòa và tầng. Mẫu quá nhỏ để áp ngưỡng 3/30, nhưng số tin trong dải của mỗi trang ít nên crawl hết rẻ hơn khảo sát thêm |
| Phải chạy từ máy của Huy ở Nhật | athome, LIFULL HOME'S, 不動産ジャパン, 近鉄不動産 | Bị chặn từ đám mây. athome và HOME'S là hai nguồn lớn nhất ngoài SUUMO nên vẫn là ưu tiên cao nhất về độ phủ |
| Cần khảo sát thêm | 福屋不動産販売, 阪急阪神不動産 | Chưa tìm được URL danh sách / chưa kết nối được |

Việc phải làm trước khi mở đợt 2:

1. Đọc điều khoản sử dụng của sáu trang nhóm "crawl ngay".
2. Tìm tham số lọc giá cho リハウス, 野村, リバブル, 大京 (nếu không có thì lọc sau khi tải theo quận).
3. Làm mới SUUMO sớm hơn dự định, hoặc ít nhất tải lại trang danh sách trong dải giá, để phép đo "lọt" không bị nhiễu bởi snapshot cũ.
4. Thêm tên tòa và tầng vào khóa gom căn khi nguồn có, để tách được căn khác tầng trong cùng tòa.
