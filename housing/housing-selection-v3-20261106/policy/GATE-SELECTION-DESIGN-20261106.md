# Thiết kế chọn nhà: sàng lọc, ưu tiên nghiên cứu và shortlist có bằng chứng

Ngày: 06/11/2026. Thiết kế bởi Astra để Terra triển khai theo yêu cầu của Huy. Policy đề xuất: `HOUSING-SELECTION-3.0`. Đây là chính sách phân bổ công sức nghiên cứu, không phải mô hình dự báo lợi nhuận, định giá hay kết luận pháp lý. Không sửa ý nghĩa hoặc ghi đè run 1.0/2.0.

## 1. Quyết định thiết kế

**Không tiếp tục trình bày năm bộ đếm gần như giống nhau dưới tên “qua 5 gate”.** Dùng hai bước sàng lọc có ý nghĩa, tiếp theo là các nhóm ưu tiên nghiên cứu, shortlist có luận điểm đã kiểm chứng và thẩm định trước cam kết. G3/G4 cũ không còn được trình bày như những gate PASS nối tiếp.

Luồng chính:

`Toàn bộ tin → Đúng phạm vi → Tách trở ngại cần làm rõ → Ưu tiên nghiên cứu P1/P2/P3/U → Shortlist luận điểm → Thẩm định theo mốc`

- **Phạm vi:** căn/tin đơn lẻ ở Osaka-shi, loại nhà/căn hộ mới/cũ, giá exact 4.000–5.000万円, gồm hai đầu.
- **Sàng lọc trở ngại:** mâu thuẫn trọng yếu, quảng cáo cho thuê/owner-change, không thể xây lại, hoặc không đáp ứng nhu cầu bắt buộc đã xác nhận. Phần chưa kiểm và cờ thông thường vẫn ghi riêng.
- **P1/P2/P3/U:** quyết định nên đọc/kiểm tra tin nào trước bằng một preset công khai, có lý do cho từng URL. Không đồng nghĩa căn tốt/xấu hoặc tăng giá.
- **Shortlist luận điểm:** chỉ khi có hồ sơ riêng cho căn, biết cần kiểm giả thuyết nào, bằng chứng hỗ trợ/phản bác và các vấn đề còn mở. Không tự động gọi toàn bộ P1 là shortlist đầu tư.
- **Thẩm định:** tài chính, quyền, kỹ thuật và điều khoản theo mốc; không chặn nghiên cứu công khai từ đầu.

Tất cả URL vẫn tìm kiếm được. Không đặt chỉ tiêu “G3 phải còn 300, G4 phải còn 50”, không lấy top-N hoặc phần trăm cố định làm gate.

## 2. Vì sao bản hiện tại không giúp chọn

Run `evaluation-20261106-practical-r3` có 11.463 URL duy nhất. G1 research PASS 1.753; G2 PASS 1.752; G3 READY 1.752; map eligible 1.749. G4 chưa đánh giá tất cả; G5 REVIEW tất cả. Giá preferred 1.754 ở catalog là baseline thô, không phải 1.754 căn đã xác minh.

Trong code hiện tại, G2 cho tiếp tục nếu không thấy một số cờ/mâu thuẫn; G3 chỉ cần diện tích **hoặc** `station_raw` **hoặc** sao. Vì mọi tin trong phạm vi đều có `station_raw`, G3 hầu như lặp lại G2. Đổi tên READY thành PASS hoặc bổ sung nhãn “ưu tiên” chung cho 1.700 tin không giải quyết vấn đề.

Giữ kết quả sàng lọc có ít loại bỏ là đúng nếu đó là điều dữ liệu nói. Việc giảm khối lượng cần đọc phải đến từ một chính sách ưu tiên minh bạch, không bóp gate để có hình phễu đẹp.

## 3. Các phương án và lựa chọn

| Phương án | Được | Mất / rủi ro |
|---|---|---|
| Năm hard gate, thêm tuổi/diện tích/phút đi bộ tối đa | Số lượng giảm nhanh | Tự đặt nhu cầu Huy chưa chốt; thiếu dữ liệu dễ bị loại; tạo cảm giác chắc chắn giả. Không chọn. |
| Chỉ scope + cờ, cho người dùng tự sort 1.700 tin | Đơn giản, trung thực | Giữ nguyên gánh nặng chọn nhà; không đáp ứng phàn nàn. Không chọn làm mặc định. |
| **Hai sàng lọc + preset ưu tiên + shortlist có bằng chứng** | Có danh sách đọc trước ngay, giữ cơ hội chưa rõ, có đường tiến tới luận điểm 10–20 năm | Phải hiển thị giới hạn so sánh và thu thập thêm cho luận điểm tăng giá. **Chọn.** |

Không cần năm “gate thật” nếu dữ liệu chỉ đủ hai sàng lọc. UI có thể thể hiện năm công đoạn nhưng không dùng chuỗi PASS hoặc gọi các nhóm P là đã qua thẩm định.

## 4. Dữ liệu thực đang có

Phân tích read-only từ facts đã sửa giá; đây là mức có trường, chưa phải độ đúng của claim:

| Trường | Chung cư cũ (1.162) | Nhà cũ (329) | Nhà mới (262) |
|---|---:|---:|---:|
| Giá / quận / station_raw | 1.162 | 329 | 262 |
| Diện tích căn hộ | 1.162 | NA | NA |
| Đất / nhà | NA | 329 / 326 | 262 / 245 |
| Năm xây | 1.162 | 329 | 0 |
| Parse sơ bộ `徒歩 N分` | 1.162 | 326 | 255 |
| Quyền đất có claim | 1.161 | 329 | 260 |
| Phí quản lý / sửa chữa có claim | 1.159 / 1.158 | NA | NA |
| Đường có claim | NA | 327 | 255 |

Không có căn hộ mới trong G1 in-scope ở snapshot này; không xóa hỗ trợ loại đó. Dự án/giá khoảng 309 URL giữ queue riêng; coverage crawl căn hộ mới còn thiếu sáu route. Nhà mới không có `built_year` là không có dữ liệu, không tự gán tuổi 0 hoặc FAIL.

Có 4 claim thuê đất ở chung cư cũ; 2 claim thuê đất nhà mới nằm trong `rights` nhưng chưa xuất hiện trong flag sẵn có. Vì vậy không thể chỉ đọc mảng `advertised_risk_flags`. Nhà có cờ đường riêng/setback; chúng không tự đồng nghĩa không xây lại được. Phí đang là claim có cấu trúc, phải đọc đơn vị/tần suất; không dùng số đầu tiên trong chuỗi làm chi phí tháng.

Nguồn ngoài `research-context-20261104` chỉ có dân số cấp quận và sự kiện dự án theo giai đoạn. `station_route_status`, `hazard_status`, `project_link_status` chưa xác minh cấp căn. Không dùng sidecar này để gắn “gần dự án”, “an toàn ngập” hay “được hưởng tăng giá”. Join URL, kiểm hash/phạm vi, không nhận nguyên quyết định giá từ baseline cũ của sidecar.

### Thử nghiệm read-only để kiểm thiết kế

Terra đã chạy prototype trên facts, chỉ để kiểm heuristic có phân biệt được dữ liệu hiện tại. Với ga đầu tiên trong chuỗi, matching đúng loại/quận/diện tích/tuổi và peer rights chưa rõ được giữ có điều kiện, nhóm target có đủ đầu vào cho prototype cho kết quả:

| Loại | Target đủ đầu vào | P1 | P2 | P3 | U vì thiếu peers |
|---|---:|---:|---:|---:|---:|
| Chung cư cũ | 1.161 | 493 | 402 | 26 | 240 |
| Nhà cũ | 322 | 49 | 23 | 8 | 242 |
| Nhà mới | 236 | 18 | 44 | 10 | 164 |
| Tổng tập prototype | 1.719 | **560** | 469 | 44 | 646 |

Trong 1.749 target active được nghiên cứu theo r3, 30 tin còn lại thiếu đầu vào prototype (5 nhà cũ, 25 nhà mới) phải vào U hoặc specialist theo lý do; không biến mất. Nếu chỉ gộp missing vào U ở prototype thì U=676 và tổng P1/P2/P3/U=1.749. **560 không phải count nghiệm thu hoặc chỉ tiêu cần đạt.** Prototype còn dùng tên ga đầu tiên chưa chuẩn hóa tuyến, peer availability lịch sử và fingerprint chưa hoàn thiện; implementation phải tính lại sau các guardrail bên dưới, có thể ra ít hoặc nhiều P1 hơn.

Trong các target có đủ peers, ít nhất một peer chưa rõ rights xuất hiện ở 888/921 chung cư, 63/80 nhà cũ và 57/72 nhà mới. Nếu bắt rights phải đầy đủ, pool toàn catalog chỉ còn khoảng 1.720 tin, gần như chính tập preferred; bỏ rào này có điều kiện mới mở pool đủ đầu vào lên 10.977 tin (7.733 chung cư cũ, 2.648 nhà cũ, 596 nhà mới). Đây là lý do cần nhãn BASIC_MATCHED và số missing của peers, không phải lý do giả rằng quyền đất đã giống nhau.

Khử trùng sơ bộ giảm số cặp target–peer ở matching cùng ga từ 26.239 xuống 21.454 ở chung cư, 1.110 xuống 984 nhà cũ, 946 xuống 872 nhà mới. Đây là số **cặp so sánh**, không phải số căn độc lập. Không được lấy các tổng này làm độ phủ thị trường hoặc chứng cứ đã khử hết trùng.

## 5. Sàng lọc phạm vi và trở ngại

### S1 — Phạm vi

Giữ semantics G1 practical: `IN_SCOPE`, `OUT_OF_SCOPE`, `PROJECT_QUEUE`, `SCOPE_REVIEW`. Giá khoảng, giá dự án, xung đột danh tính/giá/địa chỉ hoặc thiếu evidence không được biến thành exact hợp lệ. `availability` là chiều riêng với timestamp gốc. `not_found/expired` giữ lịch sử, không vào view hiện hành; `unverified/not_checked` vào queue kiểm link, không giả active.

### S2 — Trở ngại và phạm vi đã đọc

Máy phải xuất riêng:

- `material_review`: giá/danh tính/địa chỉ/hiện trạng mâu thuẫn; claim owner-change/đang cho thuê cần làm rõ khả năng sử dụng để ở; claim không thể xây lại; vi phạm nhu cầu bắt buộc thật sự đã cấu hình. Claim không xây lại được đưa review về quyền/tài sản, không đợi Huy khai rằng chắc chắn sẽ xây lại.
- `conditional_flags`: thuê đất, terrace/liền kề, đường riêng, setback và các nghĩa vụ quảng cáo khác. Không tự HOLD mọi đường riêng/setback. Thuê đất/terrace cần nhóm nghiên cứu riêng, không trộn như sở hữu đất/nhà độc lập.
- `screening_coverage`: `detail_scanned`, `catalog_only`, `scan_failed`; phạm vi field đã kiểm và nguồn. Không có keyword không đồng nghĩa không có rủi ro; không tạo badge “an toàn”.
- `data_review`: sai kiểu/đơn vị, diện tích không dương, parse mâu thuẫn; thiếu diện tích/năm/ga dẫn đến so sánh chưa đủ, không phải nhà xấu. Giá trị hiếm (ví dụ năm 1900 hoặc nhà 9,58 m²) phải giữ nguyên để kiểm nguồn; không tự sửa, không loại bằng ngưỡng sở thích giả định.

Quét claim trong field tài sản hoặc trích đoạn đúng ngữ cảnh; không bắt keyword từ menu, disclaimer, tin gợi ý. Có phủ định/không xác định ngữ cảnh → `claim_needs_review`, không kết luận pháp lý. Mỗi flag phải có evidence và raw excerpt tương ứng.

`material_review` tạm rời danh sách nghiên cứu thông thường sang queue làm rõ. Các dimension còn lại có thể tính để trợ giúp reviewer nhưng không xuất P1 như đã sạch rủi ro. Thiếu hồ sơ pháp lý/kỹ thuật riêng không tự chặn P1 nghiên cứu.

## 6. Preset mặc định: “Giá rao tương đồng + tiếp cận ga”

Đây là **heuristic do hệ thống đề xuất để chọn thứ tự kiểm chứng**, không phải giới hạn đi bộ Huy đã đồng ý, thang điểm đầu tư hay tiêu chuẩn thị trường. Tên/version/giá trị preset phải hiện trong UI và manifest. Người dùng có thể chuyển về “Tất cả trong phạm vi” hoặc đổi preset; không được âm thầm điều chỉnh sau khi thấy số lượng.

Hai tín hiệu:

1. `asking_signal`: mức rao của căn không cao hơn trung vị nhóm tin rao tương đồng, theo công thức dưới đây.
2. `access_signal`: quảng cáo đường đi bộ tới ga đường sắt được parse chắc chắn, tối đa **10 phút**. Đây là ngưỡng ưu tiên nghiên cứu có thể thay, không phải hard filter hay chứng cứ thanh khoản. `station_raw` bus/car/walk không rõ giữ unknown; không tính phút đi bộ tới bến xe buýt như ga.

| Nhóm | Công thức khi cả hai tín hiệu đã biết | Câu chữ UI |
|---|---|---|
| P1 | asking=true AND access=true | Ưu tiên kiểm chứng trước: giá rao và tiếp cận đều có tín hiệu |
| P2 | đúng một tín hiệu true | Cân nhắc tiếp: có đánh đổi giữa giá rao và tiếp cận |
| P3 | cả hai false | Để sau theo preset hiện tại |
| U | một hoặc cả hai unknown | Cần bổ sung để so sánh; không phải ưu tiên thấp |

Không gán unknown thành false/0. Căn có ga 3 phút nhưng không đủ peers vẫn U, đồng thời ghi tín hiệu ga đã biết để mở queue có ích. U có các nhóm lý do `peer_sample_thin`, `area_missing`, `age_missing`, `station_unparsed`, `tenure_specialist`, `claim_conflict`; không để một khối “chưa biết” không có việc tiếp theo.

P1 không cần private finance, hồ sơ E3 hoặc một dự án tăng giá được chứng minh. Nó chỉ là nơi bắt đầu kiểm chứng. Mỗi căn P1 phải ghi hai lý do cụ thể, mẫu peers và các điểm chưa biết; tuyệt đối không ghi “rẻ hơn giá trị”, “tiềm năng tăng X%”, “tốt để mua”.

### 6.1 Tập tham chiếu

- Dùng toàn bộ **catalog exact căn đơn lẻ** hợp lệ trong snapshot làm pool, gồm giá ngoài 4.000–5.000万円. Không chỉ dùng shortlist giá để dựng median rồi gọi là giá thị trường.
- Chỉ dùng cùng category mới/cũ và cùng loại tài sản. Không mix nhà riêng, chung cư, dự án hoặc terrace đã biết. Loại xung đột scope/giá/diện tích và claim materially incompatible đã biết. Peer thiếu hồ sơ vẫn là tin rao chưa kiểm, không phải giao dịch tương đương được xác minh.
- `not_found/expired` peer không dùng trong so sánh hiện hành. `not_checked` có thể dùng như quan sát catalog lịch sử, phải báo số này và ngày snapshot; không gọi toàn bộ mẫu là đang bán. Nếu lọc này làm n giảm dưới ngưỡng thì U.
- Không dùng giá hiện tại mới hơn với peers ở thời kỳ khác mà không hiện kỳ. V1 chỉ so trong cùng snapshot; không suy giảm giá hay thời gian bán từ số URL quan sát một lần.
- **Quan trọng:** detail/rights chủ yếu được thu cho tập preferred. Bắt mọi peer phải có rights sẽ làm pool gần như chỉ còn đúng dải giá preferred, gây thiên lệch. Cho phép rights peer chưa rõ trong `BASIC_MATCHED`, đếm và hiện số thiếu; loại known tenure mismatch. Không gọi đó là đã chứng minh tương đương quyền. Target thuê đất hoặc subtype đặc biệt → queue chuyên biệt cho tới khi có mẫu tương ứng; không so giá với target sở hữu đất thông thường.

### 6.2 Matching và số mẫu

Matching chính mặc định, mọi điều kiện phải đạt:

1. Cùng `category`, cùng ward, cùng ga quảng cáo được normalize chắc chắn. Normalize Unicode NFKC, khoảng trắng; giữ raw và tuyến/ga. Không ghép hai tên giống nhau khi không xác định được ga; không suy ga gần nhất từ vị trí quận. Khi field có nhiều phương án, chỉ lấy rail+walk pair rõ ràng, min phút trong các pair hợp lệ, lưu tất cả pair và cách chọn.
2. Chung cư: diện tích căn hộ peer trong `[0,8; 1,2] × diện tích target`.
3. Nhà riêng: **cả** diện tích đất và diện tích nhà peer trong `[0,8; 1,2] × target`; thiếu một mẫu số thì chưa có so sánh giá đủ cho preset.
4. Loại cũ: chênh năm xây tuyệt đối ≤10 năm, cả hai năm phải hợp lệ và không xung đột. Loại mới: không áp dụng built_year cho matching; không dựng tuổi giả. Nhóm tuổi này là kiểm soát khác biệt giữa peers, không loại nhà cũ khỏi tìm kiếm.
5. Loại target URL và toàn bộ nhóm nghi là cùng căn. Tối thiểu **5 nhóm peer độc lập theo heuristic khử trùng**, không phải 5 URL của cùng căn. Không tuyên bố đã chứng minh có 5 tài sản khác nhau.

Fingerprint phải công khai/versioned, conservative: normalized địa chỉ + tên tòa/dự án nếu có + category + diện tích liên quan + năm + layout + giá; floor/unit identifier nếu có. Không đủ token phân biệt → đánh dấu duplicate uncertainty, gộp thận trọng trong **phép đếm mẫu** hoặc hạ confidence; không tự gộp/xóa URL của catalog. Đồng thời lọc chắc chắn cùng URL/property_id nếu có. Báo `peer_url_count`, `peer_group_count`, `duplicate_heuristic`, sample URLs. Một căn thay giá vẫn có thể cùng tài sản: dùng nhóm identity không chứa giá khi có identifiers đáng tin, và loại toàn bộ cùng nhóm với target; fingerprint có giá chỉ là fallback, không bằng chứng độc lập.

Thử fallback cùng ward nhưng khác ga được phép hiển thị dưới tên “bối cảnh rộng”, kèm mức yếu hơn; **không dùng fallback này để tự sinh P1/P2/P3 mặc định**. Không nới điều kiện trong im lặng chỉ để ít U hơn.

### 6.3 Công thức và confidence

- Chung cư: `asking_ratio = (target_price / target_unit_m2) / median(peer_price / peer_unit_m2)`.
- Nhà riêng: `asking_ratio = target_total_price / median(peer_total_price)`, chỉ sau matching đồng thời đất + nhà. Không coi giá nhà/diện tích đất là đơn giá đất và không dùng một tỷ số m² để định giá nhà riêng.
- `asking_signal = asking_ratio <= 1.0`; giữ số chưa làm tròn khi phân nhóm, chỉ format khi hiển thị. `asking_ratio = null` nếu mẫu không đủ hoặc phép tính không hợp lệ.
- Trung vị là điểm tham chiếu mô tả trung tính của nhóm rao; không phải fair value hoặc một quota 50% P1. Mỗi target có peers khác nhau và pool không bị giới hạn giá preferred; số P1 có thể bằng 0 hoặc tất cả tùy dữ liệu.
- `BASIC_MATCHED`: qua matching công khai nhưng còn rights, tầng/hướng, sửa chữa, chất lượng, phí hoặc identity chưa rõ. Mọi P1 hiện có chỉ được coi là nghiên cứu sơ bộ ở mức này.
- `DOCUMENTED_MATCHED`: chỉ khi review thêm các khác biệt trọng yếu về quyền, subtype, tình trạng, phí/chi phí, tầng/hướng/đường phù hợp loại nhà, danh tính mẫu và kỳ quan sát. Không tự nâng level vì n lớn. Vẫn là giá rao; giao dịch thực là bộ dữ liệu riêng.

Không tính tổng điểm 100 từ hai tín hiệu hoặc lấp missing bằng điểm trung tính. Không thêm trường học/tiện ích vào điểm chính; giữ theo ưu tiên phụ của Huy.

### 6.4 Thứ tự hiển thị, sao và công bằng giữa loại nhà

Mặc định mở P1 còn link active theo lần kiểm lưu. Trong P1 sắp xếp `asking_ratio` tăng, rồi phút đi bộ tăng, rồi URL để stable; ghi “thứ tự kiểm chứng”, không ghi “xếp hạng đầu tư”. Cho phép sort khác, không thay band trong im lặng. Không ưu tiên riêng dải 4.000–4.500万円; mức giá cao hơn có thể P1 nếu so cùng peers thích hợp.

Luôn có tab “Cần bổ sung U” và bộ lọc loại nhà; hiển thị số eligible/matched/P1 theo từng category để không hiểu thiếu peers nhà riêng là nhà riêng kém hơn chung cư. Không quota số nhà theo category. Sao chỉ là lựa chọn cá nhân: giữ URL/storage key cũ, không sửa band, không bypass trở ngại, không tự biến căn U thành P1 hoặc vị trí map chính.

## 7. Từ P1 đến shortlist luận điểm 10–20 năm

Mỗi căn muốn vào `THESIS_SHORTLIST` cần reviewer và ngày, không chỉ `G3_READY`. Hồ sơ có:

1. **Nền tài sản/bán lại (H/E/D):** đặc điểm sở hữu/loại tài sản; tuổi ước tính khi giữ thêm 10 và 20 năm nếu có năm xây; nghĩa vụ/cấu trúc chi phí, khả năng sử dụng và cạnh tranh cùng loại. Không suy tuổi nhà thành đạt chuẩn động đất, không đồng nhất tân trang với kết cấu. Với nhà mới chưa có năm hoàn thành xác nhận, tuổi tương lai ghi unknown/ước tính có nguồn.
2. **Mua vào (G):** mẫu rao đang dùng, khác biệt còn lại, phí/sửa còn thiếu; kế hoạch kiểm giao dịch thực phù hợp. Hạ giá rao tương đối chưa đủ nói rẻ.
3. **Ít nhất một luận điểm cụ thể đáng kiểm tra** về nhu cầu dài hạn/tái phát triển/kết nối/khả năng bán lại, với nguồn phù hợp và liên hệ thực tới tài sản. Có thể là nền nhu cầu hiện hữu, không bắt buộc một dự án tương lai.
4. **Rủi ro và phản biện (F/H/D):** các kịch bản hazard đúng địa điểm khi có, cung cạnh tranh, tiếng ồn, chi phí, tình huống giá không tăng và bán chậm; phần chưa biết hiện rõ. Cờ material unresolved không vào shortlist thông thường.
5. **Hành động tiếp theo:** thông tin có khả năng đổi quyết định nhất, ai kiểm, cần kiểm trước mốc nào. Không đòi hoàn tất cả hồ sơ mua để bắt đầu nghiên cứu.

Trạng thái workstream: `NOT_STARTED`, `IN_RESEARCH`, `THESIS_SHORTLIST`, `COUNTEREVIDENCE`, `MATERIAL_REVIEW`. Không suy THESIS_SHORTLIST từ P1, sao hoặc ward population tăng. Các nhóm này là tiến độ có review, không bắt buộc số giảm theo tỷ lệ.

Giữ đầy đủ tám nhóm A–H/J01–J16 bằng checklist hành động:

| Nhóm | Việc cần bổ sung, tiêu chuẩn liên kết |
|---|---|
| A giao thông | Cửa ga/route thật, trước–sau cùng điểm đến, giai đoạn và thời gian dự kiến; không lấy khoảng cách tới đường hầm. |
| B dự án/việc làm | Event và phase chính thức, địa điểm, cơ chế liên quan đến căn, cạnh tranh/phiền nhiễu; cùng event_id không cộng lặp. |
| C dân cư | Địa giới và kỳ so sánh phù hợp, hộ/nhóm tuổi nếu có; ward tăng chỉ là bối cảnh, không chứng minh cầu mua của căn. |
| D cung | Tin tương đồng đã khử trùng, dự án mới và khác biệt; không gọi tin biến mất là giao dịch hay tự tính months-of-supply. |
| E tiện ích/giao thông | Đi lại hiện hữu kiểm lại; tiện ích/giáo dục là phần phụ, không suy gần trường thành trường tốt. |
| F hazard/môi trường | Độ chính xác tọa độ, kịch bản/bản đồ/ngày, tầng và hạ tầng chung; tâm quận không đủ. |
| G giá | Giá rao và giao dịch tách biệt, phí/sửa và các giả định; chưa đủ giao dịch không kết luận định giá. |
| H tài sản/quyền | Chung cư: quản lý/quỹ/kế hoạch sửa; nhà: đất/đường/quyền/xây sửa/kiểm định; chứng cứ E1/E2/E3 khác nhau. |

## 8. Thẩm định trước cam kết

Giữ checklist chuẩn gốc nhưng nhóm theo mốc `before_binding_offer`, `before_contract_deposit`, `before_settlement_handover`. Tài chính riêng đánh giá một lần cho người mua rồi áp vào căn; public chỉ có dependency tổng quát. Không xuất thu nhập, tài sản, mức vay/giấy tờ riêng, private reference hoặc đường dẫn máy.

Public chưa mở thẩm định thì `NOT_STARTED`, không tạo hàng nghìn “G5 REVIEW” khiến người xem nghĩ từng căn đã được kiểm thiếu hồ sơ. Đã bắt đầu nhưng thiếu chứng cứ → REVIEW; FAIL chỉ khi bằng chứng phù hợp xác nhận vi phạm điều kiện thật. Chỉ người/chủ thể phù hợp xác nhận, không sinh “được mua” từ code ưu tiên.

## 9. Bộ đếm, map và giao diện

Các counter độc lập có mẫu số rõ:

- Catalog raw rows / unique URLs; scope buckets phải cộng đúng 11.463 ở run này.
- Trong scope: active theo lần kiểm / chờ link / unavailable; material-review và screening coverage riêng.
- Trong tập có thể nghiên cứu thông thường: P1/P2/P3/U + specialist queue, cộng theo URL và breakdown category. Không cộng các view giao nhau như sao vào tổng.
- Workstream: đang nghiên cứu / shortlist luận điểm / thẩm định đã mở. `not_started` hiện đúng tên; không gọi count này là số qua gate.

Theo yêu cầu của Huy, map chỉ dành cho các nhóm gần shortlist: mặc định **P1 + active + không material hold**; layer còn lại là **THESIS_SHORTLIST đã có review + active + không material hold**. Không có layer map P2/P3/U/tất cả phạm vi. Các nhóm đó vẫn tìm kiếm/xem đầy đủ ở list. Khi chọn layer và subfilter loại/quận, tập URL marker phải là giao của điều kiện layer với subfilter, không được lẫn URL nhóm khác. Không auto fallback sang toàn bộ 1.749 khi P1 rỗng; giải thích lý do và đưa nút mở queue dạng list. Star view riêng không đổi map selection predicate. Reviewer có thể shortlist một căn từng ở U/P2/P3 nếu đã làm hồ sơ luận điểm; chính review có evidence là đường vào layer THESIS_SHORTLIST, không phải star hoặc nới bộ lọc.

Hiện tại map chỉ là điểm tham chiếu quận; giữ aggregate tại văn phòng quận và nhãn “điểm quận, không phải vị trí nhà”. Mỗi layer phải lọc cả danh sách lẫn tập URL của marker; count trên marker khớp list và eligible counters. `mapped + unmapped = eligible` của layer đang chọn. Không tính hazard/proximity từ những điểm này.

Card căn: nhóm ưu tiên và hai lý do cụ thể; loại/giá/diện tích/ga/tuổi; `asking_ratio`, số peer groups và mức match; phí nếu có; flags/missing; ngày nguồn và ngày kiểm link; next action. Mở được mẫu peers và rule version. Không dùng badge xanh “an toàn”, “tăng giá”, “qua 5 gate”.

## 10. Hợp đồng dữ liệu và kế hoạch Terra

Không sửa facts bất biến. Thêm evaluation mới và policy mới. Mỗi quyết định cần tối thiểu:

`listing_url, policy_version, preset_id, scope_status, availability, availability_checked_at, material_review_reasons, conditional_flags, screening_coverage, priority_band, priority_reasons, asking_ratio, asking_signal, access_signal, walk_minutes, station_key, peer_url_count, peer_group_count, peer_missing_rights_count, peer_unknown_availability_count, peer_match_tier, peer_evidence_refs, unknown_reasons, research_stage, formal_review_stage, next_actions`.

Null giữ null; signals ba giá trị true/false/null. `research_stage` được lưu riêng với nguồn/reviewer, default NOT_STARTED; không tự suy từ priority. All text public dùng allowlist/template; evidence free text chỉ xuất phần listing public đã kiểm.

Trình tự triển khai:

1. **Policy + feature extractor:** parse ga/walk/rights/subtype/fees riêng có unit/evidence; đọc cả normalized fields lẫn flags đúng ngữ cảnh. Không viết lại crawler hoặc fetch toàn bộ tin chỉ để chấm.
2. **Peer engine riêng:** dựng reference pool đầy đủ giá exact, indexes theo category/ward/station, kiểm tuổi/diện tích/tenure, dedupe nhóm tham chiếu; tính median và lý do không đủ mẫu. Không nhét matching toàn catalog vào hàm một-căn đang có.
3. **Selection evaluator:** tái sử dụng scope/availability đã kiểm nhưng phát output version mới; tính S2 và P1/P2/P3/U/specialist. Adapter giữ legacy fields chỉ cho đối chiếu, không gán P1 thành PASS G4.
4. **Exporter/runner:** manifest hash facts/catalog/policy/preset/code, peer definition, source dates, counters theo category và disposition, không đè r3. Xuất `selection-decisions`, `peer-comparisons`, `priority-diff`, `quality-report`; SQLite/list/CSV khớp.
5. **View/map:** thay năm PASS counters bằng scope/nhóm nghiên cứu/workstream; default P1, toggles rõ; giữ sao. Chuẩn bị bản local review trước khi publish theo phạm vi parent xử lý.
6. **Dữ liệu nghiên cứu sâu:** checklist và state store cho luận điểm/giấy tờ, default NOT_STARTED; join context cũ chỉ làm bối cảnh. Không cần crawler hazard/giao dịch mới để hoàn tất bản ưu tiên sơ bộ, không giả đã làm các nghiên cứu đó.

Các module hiện hữu cần xem: `gate_practical_engine.py`, `gate_practical_policy.json`, `run_practical_evaluation.py`, `export_practical_results.py`, `build_gate_view.py`, `build_gate_map_data.py`, `gate_map.js`. Có thể thêm `gate_selection_features.py` và `gate_selection_peers.py` để giữ ranh giới, tránh refactor ngoài scope.

## 11. Kiểm thử/điều kiện nghiệm thu

- Price endpoints 40/50 triệu được giữ; projects/ranges không thành unit; không mất URL; old artifacts/hash không thay.
- Cùng nhà nhiều URL không tạo đủ n; self và cả nhóm self bị loại; thêm URL trùng không làm đổi priority. Median tính từ nhóm, không từ số bản đăng.
- Condo dùng unit m²; nhà dùng total price sau matching cả đất và nhà. Chuyển diện tích sai loại, zero/null, conflict → unknown.
- Unknown rights peer báo rõ; known leasehold/freehold mismatch không so. Pool không bị lén giới hạn preferred price. New house không có built_year không bị FAIL.
- Bus/walk, multi-station, range minutes, thiếu ga, Unicode và tên ga mơ hồ; không parse thành thời gian rail chắc chắn sai.
- P1/P2/P3/U đúng truth table; partial unknown không thành P2/P3; threshold dùng số chưa làm tròn. Không quota, không score_total, không tự claim tăng giá.
- Material claim chuyển review, missing legal documents không chặn nghiên cứu; sao không đổi band/risk/map.
- Fallback khác ga không nâng priority mặc định; P1 rỗng không mở map tất cả ngầm.
- Scope + disposition totals, band/category counts, map/list/CSV/SQLite khớp; counters không gọi số URL là số nhà độc lập.
- Nghiên cứu chưa làm ghi NOT_STARTED; context ward không tự tạo property upside/hazard. Không lộ finance/private reference qua CSV/HTML/SQLite/manifest/log/bundle.
- Review thủ công tối thiểu vài ví dụ mỗi loại và band, nhất là P1 nhà riêng, case thuê đất, dữ liệu lạ, n sát 5 và duplicate. Dry-run thống kê chỉ là kiểm thiết kế; kết quả production phải tính lại sau parser/dedupe đã được test.

## 12. Giới hạn cần ghi trên output

Preset này đưa ra **thứ tự nghiên cứu có lý do**, chưa đo trực tiếp xác suất tăng giá hoặc bán lại sau 10–20 năm. Peers là tin rao có mức tương đồng công khai, chất lượng và quyền còn thiếu; đồng thời dữ liệu có thể có bản đăng trùng và coverage chưa toàn thị trường. P1 không thay thế shortlist luận điểm hoặc thẩm định. Việc nhiều căn nằm U là chỉ báo cần thu thập đúng phần thiếu, không phải bằng chứng rằng chúng kém hơn P1.

