# AUDIT phần tính toán: Bát tự, chiêm tinh, thần số học

1. **Tin được:**
   - Vị trí thiên thể của chiêm tinh lệch ≤ 1″ so với JPL DE421; Mặt Trăng, cung mọc, thiên đỉnh, các cung nhà Placidus và nút thật lệch ≤ 0,4″.
   - Bát tự: tiết khí lệch ≤ 0,3 phút, tứ trụ, tàng can, thập thần và đại vận đều đúng.
   - Thần số học khớp tính tay ở mọi chỉ số, theo đúng quy tắc mà code tự công bố.
2. **Sai ở phần lịch và múi giờ dùng chung:**
   - Âm lịch Việt Nam bị đổi theo lịch Trung Quốc (F1). Lỗi này ảnh hưởng cả Bát tự lẫn Tử Vi.
   - Người sinh ở miền Bắc 1960–1975 bị tính UTC+8 (F2, A1). Ở chiêm tinh, lỗi này làm cung mọc lệch khoảng 15° và đổi luôn cung (ví dụ Xử Nữ thay vì Thiên Bình).
3. **Sai ở chiêm tinh:**
   - Sinh ở vĩ độ trên 66,56° thì engine báo lỗi, với mọi hệ nhà (A2).
   - Lá số ngày/đêm (sect) sai khi dùng hệ nhà whole sign (A3).
   - Thiếu giờ sinh thì lấy 00:00 mà không cảnh báo rằng Mặt Trăng có thể đổi cung trong ngày (A4).
4. **Không căn cứ:**
   - Bát tự: điểm vượng/nhược bỏ qua địa chi, nên Nhâm thân nhược ra −0,2 (F3). Nhãn "cân bằng" và dụng/hỷ/kỵ do code nằm ngoài các repo này sinh ra (F5).
   - Thần số học mặc định dùng cách tính Decoz, nên số chủ đạo ca chuẩn ra **6**. Cách cộng mọi chữ số (chính tài liệu của repo gọi là phổ biến ở Việt Nam) ra **33** (N1).
5. **Chưa kiểm được:** code chọn dụng thần; quy tắc chữ Y trong tên tiếng Việt (Duy, Thủy, Nguyễn) làm chỉ số Linh hồn đổi từ 5 thành 3.

---

## Phạm vi thực tế và bản đồ code

Repo kiểm (Bát tự, Tử Vi): `dlong1911/Numerologist_skills` @ `43618f8` (fork của FANzR-arch). Chiêm tinh và thần số học nằm ở hai repo riêng, xem hai phần cuối báo cáo. Repo chứa:

| Phần | File | Thư viện ngoài | Ghi chú |
|---|---|---|---|
| Bát tự (mới, chưa kiểm) | `bazi/scripts/bazi_cli.py` | `lunar_python` 1.4.9, `zoneinfo`/`tzdata` | Do model khác viết thêm (commit 43618f8) |
| Tử Vi (đã đối chiếu) | `ziwei-doushu/scripts/ziwei_cli.py` | `lunar_python` | Dùng chung **lịch âm** của `lunar_python` với Bát tự |
| Kỳ Môn | `qimen-dunjia/` | | Ngoài phạm vi |
| Chiêm tinh, thần số học | repo riêng `astrology_skills`, `numerology_skills` | | Xem phần "Chiêm tinh" và "Thần số học" |

Hàm trong `bazi_cli.py`:
- `normalize_input`: múi giờ, đổi âm sang dương, kinh độ, quy ước giờ Tý.
- `compute_times`: đổi sang giờ Bắc Kinh, tính giờ mặt trời thực.
- `build_chart`: tứ trụ. Năm và tháng lấy từ `EightChar` theo giờ Bắc Kinh; ngày và giờ lấy theo giờ địa phương hoặc giờ mặt trời thực.
- `pillar_detail`: tàng can, thập thần, nạp âm, trường sinh.
- `element_counts`: chấm điểm ngũ hành.
- `strength_factors`: điểm vượng/nhược.
- `detect_interactions`: quan hệ can chi.
- `getYun`/`getDaYun` của `lunar_python`: đại vận.

**Ghi chú về ca chuẩn.** Engine khớp các số anh/chị đưa (Mộc 3, Hỏa 1,1, Thổ 1,6, Kim 0,3, Thủy 2; −0,2). Đó là `element_counts.weighted` và `strength_factors.heuristic_score`. Tuy vậy repo **không có** chữ "cân bằng" và **không có** phép chọn dụng/hỷ/kỵ (grep `喜|用神|忌` chỉ thấy trong prompt). Engine **có** xuất `丁壬合（化木）` và ba cặp `卯戌合`. Nếu bài luận không nhắc tới chúng thì chúng bị bỏ ở tầng sau, không phải ở engine.

## Phương pháp và nguồn tham chiếu

- **[EPH]** PyEphem 4.2.1, dùng VSOP87 cho Mặt Trời. Kinh độ hoàng đạo biểu kiến được giải nghiệm bằng chia đôi. Đã kiểm lại với `ephem.next_equinox(2000)`: lệch 3 giây.
- **[JDN]** Chỉ số ngày trong chu kỳ 60 = (JDN + 49) mod 60, mốc 1/1/2000 = Mậu Ngọ.
- **[TZ]** File `asia` của IANA tzdata, mục Vietnam. Mục này trích Trần Tiến Bình, *Lịch Việt Nam thế kỷ XX–XXI*, 2005, và Công báo VNCH 1955, 1959.
- **[VNL]** Lịch âm Việt Nam là lịch Trung Quốc tính theo kinh tuyến UTC+7 (thuật toán Hồ Ngọc Đức). Tôi viết lại bằng PyEphem. Chạy ở UTC+8, bản này **khớp lunar_python 100%** (0 ngày lệch, 1950–2030), nên cách cài đặt đáng tin. Chạy ở UTC+7, kết quả khớp các mốc Tết đã công bố rộng rãi: 21/1/1985, 29/1/1968 (miền Bắc) và 17/2/2007.
- **[HAND]** Tính tay, có trình bày từng bước bên dưới.

Script kiểm chứng nằm trong `audit/`: `ref.py` (tham chiếu), `check1.py` (tiết khí, trụ ngày, khởi vận, giờ mặt trời thực), `check2.py` (lịch âm VN và TQ), `check3.py` (ca biên). Chạy với `python audit/checkN.py audit <đường dẫn tới bazi/scripts> [ziwei-doushu/scripts]`. Phần tái hiện được đã chuyển thành test trong `bazi/scripts/tests/test_bazi_audit.py`.

## Đã kiểm chứng là đúng

| Mục | Cách kiểm | Kết quả |
|---|---|---|
| Thời điểm 12 tiết (1950–2030) | 810 tiết so với [EPH] | Sai lớn nhất 0,3 phút, trung bình 0,1 phút |
| Ranh giới năm (Lập Xuân) | 2024: Lập Xuân 15:26:56 UTC+7 [EPH]; sinh 15:20 và 15:35 | Lần lượt Quý Mão/Ất Sửu và Giáp Thìn/Bính Dần ✓ |
| Ranh giới tháng | Kinh Trập 2024 lúc 09:22:38 UTC+7; sinh 09:15 và 09:30 | Bính Dần, rồi Đinh Mão ✓ |
| Đổi sang giờ Bắc Kinh để so tiết | Bảng tiết của lunar_python là UTC+8; code đổi khoảnh khắc sinh sang UTC+8 | Đúng về nguyên tắc ✓ |
| Trụ ngày | 3000 ngày ngẫu nhiên 1900–2100 so với [JDN] | 0 lệch ✓ |
| Trụ giờ, giờ Tý | Sinh 23:30 ngày 10/3/1999. `same_day`: Tân Dậu / Canh Tý (dạ tý, can giờ khởi theo ngày Nhâm hôm sau). `next_day`: Nhâm Tuất / Canh Tý | Cả hai là quy ước có tên trong sách ✓ |
| Giờ mặt trời thực | 400 thời điểm 1950–2030, kinh độ 102–110°E, so với góc giờ Mặt Trời [EPH] | Sai ≤ 0,83 phút ✓ (NOAA, chấp nhận được) |
| Tàng can | So với `LunarUtil.ZHI_HIDE_GAN` và bảng tử bình thông dụng | Khớp ✓ (xem chú thích về Tỵ ở mục chưa kiểm) |
| Thập thần | 100 cặp can so với `LunarUtil.SHI_SHEN` | Khớp ✓ |
| Trường sinh | Hỏa Thổ đồng cung, can âm đi nghịch; so với `EightChar.getDayDiShi` | Khớp ✓ |
| Vượng tướng hưu tù tử | Xuân: Mộc vượng, Hỏa tướng, Thủy hưu, Kim tù, Thổ tử. Tháng tứ quý tính là Thổ | Đúng quy ước ✓ |
| Chiều đại vận | Năm can dương với nam, hoặc can âm với nữ, thì thuận | ✓ |
| Tuổi khởi vận, ca chuẩn | [EPH] Kinh Trập 1999 lúc 06/3 08:57:39 BJT; sinh 11/3 06:15 BJT; cách 7037,4 phút. Tính 7037,4 / 4320 = 1,629 năm, tức 1 năm 7 tháng 16 ngày (quy ước 3 ngày = 1 năm) | Engine ra 1n 7th 16ng; vận Giáp Tý từ 2020 ✓ |

Tứ trụ ca chuẩn tính tay:
- Năm: 1999 sau Lập Xuân (4/2), nên Kỷ Mão.
- Tháng: sau Kinh Trập (6/3) và trước Thanh Minh, nên tháng Mão. Năm Kỷ khởi tháng Dần là Bính Dần, vậy tháng Mão là Đinh Mão.
- Ngày: JDN 2451249, (2451249 + 49) mod 60 = 58, tức Nhâm Tuất.
- Giờ: 05:15 thuộc giờ Mão. Ngày Nhâm khởi giờ Tý là Canh Tý, vậy giờ Mão là Quý Mão.

---

## Phát hiện (nặng nhất trước)

### F1 — SAI: lịch âm dùng lịch Trung Quốc, không phải lịch Việt Nam

> **Đính chính (giai đoạn 1):** lịch âm Việt Nam chỉ tính theo UTC+7 từ 8/8/1967 (miền Bắc) và 13/6/1975 (miền Nam). Trước đó lịch trùng lịch Trung Quốc ([Wikipedia: Vietnamese calendar](https://en.wikipedia.org/wiki/Vietnamese_calendar), dẫn Aslaksen). Vì vậy số ngày lệch đếm cho 1950–1967 dưới đây không phải lỗi. Đã sửa bằng `vn_calendar.py`.
- **Vị trí:**
  - `bazi/scripts/bazi_cli.py:218-223`: `Lunar.fromYmd(...).getSolar()`.
  - `ziwei-doushu/scripts/ziwei_cli.py:180-185` (`lunar_to_solar_date`) và `:268` (`Solar.fromYmd(...).getLunar()`).
  - `lunar_python` tính sóc và trung khí ở UTC+8.
- **Tái hiện:**
  - Bát tự, `calendar_type=lunar`, `birth_time="2007-01-01 12:00"`. Code ra **2007-02-18**. Đúng là **2007-02-17**, Tết Đinh Hợi tại Việt Nam [VNL].
  - Bát tự, âm lịch `1985-01-01`. Code ra **1985-02-20**. Đúng là **1985-01-21** [VNL].
  - Tử Vi, dương lịch `1985-02-01 12:00`. Code ra **Giáp Tý, tháng 12, ngày 12**. Đúng là **Ất Sửu, tháng 1, ngày 12** [VNL]. Can năm sai kéo theo tứ hóa và đại hạn sai, nên lệch cả lá số.
  - Quy mô: 1167 ngày dương lịch trong 1950–2030 có ngày, tháng hoặc năm âm lịch khác giữa hai lịch. Thường là cả một tháng lệch 1 ngày; năm 1984–85 lệch 148 ngày, năm 1987 lệch 59 ngày, do tháng nhuận đặt khác.
  - Danh sách đầy đủ có trong output của `check2.py`.
- **Ảnh hưởng:** người nhập ngày âm lịch Việt Nam có thể nhận Bát tự lệch một ngày, kéo theo trụ ngày và nhật chủ sai. Với Tử Vi, cả lá số có thể sai mà không ai phát hiện.
- **Sửa:** đổi âm/dương theo lịch UTC+7. Có thể tự cài thuật toán Hồ Ngọc Đức, hoặc so sóc/trung khí lại ở UTC+7. Thêm tham số `lunar_calendar: "vn" | "cn"`, mặc định `vn` cho người dùng Việt Nam.
- **Test:** `test_vietnamese_lunar_input` (×2), `test_ziwei_vietnamese_lunar_new_year_1985`.

### F2 — SAI: múi giờ miền Bắc 1960–1975

> **Đính chính (giai đoạn 1):** múi giờ miền Bắc 1955–1967 có nguồn mâu thuẫn (+7 hoặc +8); miền Bắc chắc chắn ở +7 từ 8/8/1967. Ca Hà Nội 1970 vẫn đúng. Đã sửa bằng bảng hai miền trong `vn_calendar.py`.
- **Vị trí:**
  - `bazi_cli.py:192-201` nhận nguyên tên múi giờ.
  - `examples/bazi_input.json` mẫu dùng `Asia/Ho_Chi_Minh`.
  - `bazi_cli.py:275-280`: kinh tuyến chuẩn để tính giờ mặt trời thực lấy từ utcoffset.
- **Tái hiện:** `birth_time="1970-06-15 13:20"`, `timezone="Asia/Ho_Chi_Minh"`, `longitude=105.85` (Hà Nội).
  - Code coi là UTC+8. Giờ mặt trời thực ra 12:23:22, nên trụ giờ **Giáp Ngọ**, và không có cảnh báo.
  - Đúng: miền Bắc vẫn dùng +7 trong giai đoạn này. Theo [TZ], `Asia/Ho_Chi_Minh` chỉ mô tả miền Nam (+8 từ 31/12/1959 đến 13/6/1975); miền Bắc tương ứng `Asia/Bangkok`.
  - Giờ mặt trời thực đúng là 13:23 [EPH], nên trụ giờ đúng là **Ất Mùi**.
  - Khi tắt giờ mặt trời thực, trụ ngày và giờ vẫn đúng (dùng giờ đồng hồ). Nhưng khoảnh khắc so với tiết và tuổi khởi vận vẫn lệch 1 giờ.
- **Ảnh hưởng:** người sinh ở miền Bắc 1960–1975 trong vòng 1 giờ sát ranh giới canh giờ sẽ nhận sai trụ giờ, và phần luận về con cái và tuổi già sai theo.
- **Sửa:** nếu múi giờ là `Asia/Ho_Chi_Minh`, ngày sinh trong 1960–1975 và nơi sinh ở bắc vĩ tuyến 17, thì dùng +7. Nếu không biết nơi sinh, phát cảnh báo bắt buộc.
- **Test:** `test_hanoi_1970_flags_or_corrects_utc8_offset`.

### F3 — KHÔNG CĂN CỨ: điểm vượng/nhược `heuristic_score`
- **Vị trí:** `bazi_cli.py:351-378`.
- **Công thức đúng như code** (tính cho nhật chủ D):

  ```
  score = S(trạng thái mùa của hành D)    # vượng +2 | tướng +1.5 | hưu 0 | tù −1 | tử −1.5
        + Σ gốc                           # mỗi tàng can cùng hành D: bản khí +1, trung khí +0.5, dư khí +0.3
        + 0.8 × (số can lộ là tỷ/kiếp/ấn, không tính can ngày)
        − 0.5 × (số can lộ còn lại)
  ```
- **Tại sao không có căn cứ:**
  - Địa chi chỉ được tính khi là gốc. Ấn trong địa chi không cộng điểm. Thực, thương, tài, quan trong địa chi không trừ điểm.
  - Nguyệt lệnh chỉ được tính qua bậc vượng tướng hưu tù tử, và "hưu" (bị tiết) được 0 điểm, như trung tính.
  - Cách cộng trừ này không trùng với phương pháp đã công bố nào: không trùng ba điều kiện đắc lệnh, đắc địa, đắc thế của tử bình, cũng không trùng phép chấm điểm theo ngày tư lệnh của nhân nguyên.
- **Tái hiện:**
  - Ca chuẩn: 0 + 0 + 0,8 − 1,0 = −0,2 [HAND].
  - Đổi Mão ở trụ năm và trụ giờ thành Dậu (chính ấn): `己酉 丁卯 壬戌 癸酉`. Code vẫn ra **−0,2**, giống hệt ca chuẩn.
  - Theo ba điều kiện của tử bình [HAND]:
    - Đắc lệnh: không, Mão là thương quan, Thủy ở thế hưu.
    - Đắc địa: không, không có Hợi, Tý, Thân, Thìn hay Sửu.
    - Đắc thế: chỉ có Quý trong 3 can.
    - Kết luận là **thân nhược** rõ ràng, chưa kể Đinh Nhâm hợp và ba Mão tiết khí.
  - Ghi chú của chính code nói "<0 偏弱", nên chữ "cân bằng" là do tầng sau đặt ngưỡng (xem F5).
- **Ảnh hưởng:** người thân nhược có thể được luận là "cân bằng", nên lời khuyên về dụng thần và đại vận đi ngược.
- **Sửa:** chọn một phương pháp có tên, ví dụ điểm theo ngày tư lệnh của nhân nguyên, hoặc ba điều kiện đắc lệnh, đắc địa, đắc thế. Cho mọi địa chi góp điểm sinh hoặc khắc nhật chủ, có trọng số nguyệt lệnh. Ghi tên phương pháp vào output.
- **Test:** `test_branch_resource_raises_strength`, `test_canonical_is_clearly_weak`.

### F4 — KHÔNG CĂN CỨ: Bát tự và Tử Vi xử lý thời gian không nhất quán
- **Vị trí:**
  - Bát tự: `bazi_cli.py:240` mặc định `late_zi_rule="same_day"`. Bát tự có xử lý múi giờ, giờ mặt trời thực và đổi sang giờ Bắc Kinh.
  - Tử Vi: `ziwei_cli.py:231` mặc định `"next_day"`. Tử Vi không nhận múi giờ, kinh độ hay giờ mặt trời thực (`ziwei_cli.py:192-252`).
- **Tái hiện:** sinh 23:30 ngày 10/3/1999.
  - Bát tự lấy trụ ngày Tân Dậu, tức ngày 10.
  - Tử Vi lấy `chart_solar_date=1999-03-11`, ngày âm 24.
  - Sinh ở Hà Nội lúc 07:05 ngày 11/2/1999, có bật giờ mặt trời thực: Bát tự tính ra 06:54, giờ **Mão** (Đinh Mão), trong khi Tử Vi dùng 07:05, giờ **Thìn**.
- **Ảnh hưởng:** một bài luận dùng cả hai hệ có thể dựa trên hai ngày hoặc hai giờ sinh khác nhau cho cùng một người.
- **Sửa:** tính ngày và giờ địa phương một lần ở tầng chung (gồm múi giờ, giờ mặt trời thực và quy ước giờ Tý) rồi truyền cho cả hai engine. Thống nhất một mặc định cho giờ Tý.
- **Test:** `test_late_zi_default_consistent_with_ziwei`.

### F5 — KHÔNG CĂN CỨ (nghi vấn, code nằm ngoài repo): nhãn "cân bằng" và dụng/hỷ/kỵ
- **Vị trí:** không có trong repo. Dữ liệu chuẩn bị cho prompt (`SKILL.md`) chỉ có `heuristic_score` và `element_counts`.
- **Đối chiếu giả thuyết của anh/chị trên ca chuẩn:**
  - Hành yếu nhất (theo `weighted`) là Kim 0,3, đúng là dụng.
  - Hành yếu nhì là Hỏa 1,1, đúng là hỷ.
  - Hành mạnh nhất là Mộc 3,0, đúng là kỵ.
  - Theo `visible` cũng ra thứ tự đó (Kim 0, Hỏa 1, Mộc 3).
  - Dữ liệu **phù hợp** với giả thuyết, nhưng tôi **không xác nhận được** vì không có code tầng đó để chạy thêm lá số.
- **Giá trị đúng theo phù ức [HAND]:**
  - Nhâm thân nhược nên lấy ấn (Kim) và tỷ kiếp (Thủy) làm dụng/hỷ; tài (Hỏa), quan sát (Thổ) và thực thương (Mộc) là kỵ.
  - "Hỷ Hỏa" mâu thuẫn trực tiếp: Hỏa là tài, khắc ấn Kim và sinh quan sát Thổ.
  - Theo điều hậu (*Cùng Thông Bảo Giám*) có thể ra kết quả khác. Tôi không có bản gốc để trích, nên phần này chưa kiểm.
- **Ảnh hưởng:** người dùng được khuyên bổ sung hành đang hại mình, ví dụ chọn màu, nghề hay hướng theo Hỏa.
- **Sửa:** chuyển phép chọn dụng thần vào engine. Ghi rõ trường phái (phù ức, điều hậu, thông quan) và lý do, và không bao giờ suy ra từ thứ tự điểm ngũ hành.

### F6 — KHÔNG CĂN CỨ (nhỏ): công thức chấm điểm ngũ hành
- **Vị trí:** `bazi_cli.py:54, 333-348`.
- **Công thức:**
  - `weighted`: mỗi thiên can +1 cho hành của nó. Mỗi địa chi chia đúng 1 điểm cho các tàng can: một tàng can 1,0; hai tàng can 0,7/0,3; ba tàng can 0,6/0,3/0,1.
  - `visible`: 4 can và 4 chi, mỗi chữ được 1 điểm, chi tính theo hành bản khí.
- **Xác nhận:** đây là phép đếm thô. Không có trọng số nguyệt lệnh, thông căn, hợp hóa hay sinh khắc. Bộ trọng số 0,6/0,3/0,1 không theo bảng nào tôi đối chiếu được. Code tự ghi là "不等于旺衰结论" (không phải kết luận vượng suy).
- **Ảnh hưởng:** chỉ là thống kê. Nó chỉ thành sai khi tầng sau dùng để suy vượng suy hoặc dụng thần (F5).
- **Sửa:** đổi tên trong prompt thành "đếm chữ" và cấm suy dụng thần từ nó. Nếu cần điểm sức mạnh thì dùng phương pháp của F3.

### F7 — NHỎ: không truyền múi giờ thì mặc định `Asia/Shanghai`
- **Vị trí:** `bazi_cli.py:32, 195-201`.
- **Tái hiện:** ca chuẩn không truyền `timezone`. Code coi 05:15 là giờ Bắc Kinh, tức sớm hơn giờ thực 1 tiếng, và chỉ có cảnh báo.
- **Ảnh hưởng:** người Việt Nam bị lệch 1 giờ khi tích hợp quên truyền múi giờ.
- **Sửa:** bắt buộc truyền `timezone`, hoặc mặc định `Asia/Ho_Chi_Minh` cho sản phẩm Việt Nam (kèm cảnh báo của F2).

### F8 — NHỎ: gán đại vận cho lưu niên theo năm dương lịch; tuổi mụ tính theo năm dương
- **Vị trí:** `bazi_cli.py:497-500, 513`.
- **Tái hiện:** ca chuẩn hỏi năm 2020. Code gán Giáp Tý cho cả năm, nhưng vận này bắt đầu ngày 27/10/2020; từ tháng 1 đến 10/2020 vẫn là Ất Sửu.
- **Ảnh hưởng:** lời luận cho năm chuyển vận sai trong khoảng 9 tháng.
- **Sửa:** nếu năm lưu niên chứa ngày chuyển vận, ghi cả hai vận kèm ngày chuyển. Tính tuổi mụ theo năm âm.

### F9 — NHỎ: quan hệ can chi không xét vị trí kề nhau; nhãn "hóa" đặt vô điều kiện
- **Vị trí:** `bazi_cli.py:395-428`.
- **Mô tả:**
  - Code có tính đủ ngũ hợp thiên can, lục hợp, tam hợp, bán hợp, củng hợp, tam hội, xung, hình (gồm tự hình và tam hình), hại, phá, phục ngâm và phản ngâm.
  - Nhưng quan hệ được xét giữa mọi cặp trụ, kể cả trụ năm với trụ giờ.
  - Nhãn `丁壬合（化木）` được ghi ra mà không kiểm điều kiện hóa (nguyệt lệnh, can lộ, có bị phá không).
- **Ảnh hưởng:** LLM có thể luận "Nhâm hóa Mộc" như đã xảy ra.
- **Sửa:** ghi thêm hai trụ có kề nhau không, và đổi nhãn thành `合（化木需条件）` (hợp, cần đủ điều kiện mới hóa Mộc). Hoặc kiểm điều kiện hóa thật.

### F10 — NHỎ: giờ mùa hè khi tắt giờ mặt trời thực
- **Vị trí:** `bazi_cli.py:274`.
- **Mô tả:** khi tắt giờ mặt trời thực, trụ ngày và giờ dùng giờ đồng hồ kể cả trong giờ mùa hè. Ví dụ Trung Quốc 1986–1991: giờ đồng hồ sớm hơn giờ chuẩn 1 tiếng.
- **Ảnh hưởng:** không ảnh hưởng người sinh ở Việt Nam, vì Việt Nam không có giờ mùa hè sau 1975.
- **Sửa:** luôn trừ phần `dst()` trước khi tính trụ giờ.

---

# Chiêm tinh phương Tây — `dlong1911/astrology_skills` @ `1a55c26`

## Bản đồ code và quy ước

File: `natal-astrology/scripts/astro_cli.py`.

| Mục | Code dùng | Nhận định |
|---|---|---|
| Vị trí thiên thể | kerykeion 6.1.0, chạy trên **libephemeris 4.0.0** (engine Rust dùng dữ liệu JPL, API tương thích Swiss Ephemeris). Riêng quét transit/return gọi `swe.calc_ut` trực tiếp | Ephemeris thật, không tự viết công thức xấp xỉ |
| Hoàng đạo | Nhiệt đới, địa tâm, vị trí biểu kiến (`:314, 620`) | Quy ước chuẩn của chiêm tinh phương Tây |
| Hệ nhà | Placidus mặc định; có whole sign, Koch, Equal, Porphyry, Regiomontanus, Campanus | Chuẩn |
| Nút Mặt Trăng | Nút thật (dao động tức thời); nút trung bình cũng được liệt kê | Chuẩn |
| Góc chiếu và orb | Natal: hợp/đối 8°, vuông/tam hợp 7°, lục hợp 5°, bất tương hợp 3°. Transit: 3/3/3/3/2/1,5° | Trong khoảng thông dụng |
| Giờ địa phương sang UTC | `zoneinfo` (tzdata) | Xem A1 và A6 |
| Python | kerykeion 6.1.0 cần **Python ≥ 3.12** | requirements.txt không ghi; trên 3.10, pip không cài được |

## Phương pháp và nguồn tham chiếu

- **[DE421]** JPL DE421, đọc qua Skyfield. Vị trí lấy là kinh độ biểu kiến địa tâm, theo hoàng đạo và xuân phân thật của ngày.
  - Cung mọc và thiên đỉnh tính bằng công thức cầu chuẩn, từ giờ sao biểu kiến (GAST) và độ nghiêng hoàng đạo thật.
  - Các cung nhà Placidus tính bằng phép chia ba bán cung, có lặp cho hội tụ; đây là bản tôi tự viết.
  - Nút thật là nút lên của quỹ đạo Mặt Trăng dao động tức thời, tính từ vectơ r × v. Nút trung bình theo công thức Meeus.
  - Coi giờ UTC dân sự là UT1, vì |UT1 − UTC| < 0,9 s. Nếu để Skyfield tự đổi UTC trước 1972, cung mọc lệch tới 4′; đó là mô hình thời gian của tham chiếu, không phải lỗi engine.
- **[HZN]** JPL Horizons API (đại lượng 31) cho Chiron. Dữ liệu thô ở `audit/horizons_chiron.txt`.
- **Script:** `audit/astro_ref.py` (tham chiếu), `audit/check_astro.py` (24 lá số 1950–2030, 10 vĩ độ từ −34° đến 64°), `audit/check_astro2.py` (ca biên).

## Đã kiểm chứng là đúng

| Mục | Cách kiểm | Sai số lớn nhất |
|---|---|---|
| Mặt Trời → Diêm Vương (10 thiên thể) | 24 thời điểm ngẫu nhiên 1950–2030, so với [DE421] | ≤ 0,2″, riêng Sao Thủy 1,1″ trước khi chỉnh UT1 |
| Mặt Trăng | Như trên | 0,4″ |
| Cung mọc, thiên đỉnh | Như trên | 0,2″ |
| 12 cung nhà Placidus | So với bản Placidus tự viết | 0,2″ |
| Nút thật / nút trung bình | Dao động tức thời / Meeus | 0,2″ / 17,8″ |
| Cờ nghịch hành | 240 cặp (thiên thể × thời điểm), so dấu tốc độ với [DE421] | 0 sai |
| Chiron | 7 thời điểm, so với [HZN] | 128″ (khoảng 2′) năm 1950; 20–40″ các năm khác |
| Giờ Việt Nam sang UTC | 05:15 +07 → 22:15 UTC hôm trước | Đúng |
| Mặt Trời sát ranh giới cung | Vào Bạch Dương 20/3/2000 lúc 07:35 UTC: 07:33 cho Song Ngư, 07:37 cho Bạch Dương | Đúng |
| Saturn return ca chuẩn | Engine ra 21/4/2028 08:22 (+7); [DE421] cùng phút | Đúng |
| Thời điểm cung mọc đổi cung | Tìm bằng chia đôi trên `swe.houses` | Dùng chung engine đã kiểm ở trên |

## Phát hiện (nặng nhất trước)

### A1 — SAI: bảng thành phố gán Hà Nội, Hải Phòng, Vinh vào `Asia/Ho_Chi_Minh`
- **Vị trí:** `astro_cli.py:96-97, 102, 108`. Cùng nguyên nhân với F2.
- **Tái hiện:** `birth_datetime="1970-06-15 13:20"`, `city="ha noi"`.
  - Engine ra `birth_utc = 05:20`, cung mọc **29°00′ Xử Nữ**, Mặt Trăng 28°33′ Thiên Bình.
  - Đúng: Hà Nội 1970 dùng +7 [TZ], nên là 06:20 UTC. Theo [DE421], cung mọc **13°02′ Thiên Bình**, Mặt Trăng 29°05′ Thiên Bình.
- **Ảnh hưởng:** người sinh ở miền Bắc 1960–1975 nhận sai cung mọc, sai vị trí nhà của mọi hành tinh và sai chủ tinh lá số.
- **Sửa:** cho các thành phố phía Bắc vĩ tuyến 17 dùng `Asia/Bangkok`, hoặc chọn múi giờ theo vĩ độ khi tz là `Asia/Ho_Chi_Minh` và năm sinh trong 1960–1975.
- **Test:** `test_hanoi_1970_city_table_offset`.

### A2 — SAI (báo lỗi, không ra lá số): sinh ở vĩ độ trên 66,56° với mọi hệ nhà
- **Vị trí:** `astro_cli.py:398-401`. `angles_at` gọi `swe.houses(..., b"P")` cố định Placidus, phục vụ việc tự kiểm và tính khung thời gian cung mọc.
- **Tái hiện:** Tromsø (69,65°N; 18,96°E), 15/12/1990 10:00. Mọi hệ nhà, kể cả `whole_sign` và `porphyry`, đều ném lỗi `PolarCircleError: house system 'P' cannot be calculated at latitude 69.65`.
- **Thêm:** với `placidus` và `koch`, kerykeion **tự chuyển sang Porphyry** và chỉ ghi log. Output vẫn ghi `house_system: placidus`, và cảnh báo của code (`:244`) không nói chuyện đã chuyển.
- **Ảnh hưởng:** người sinh ở Bắc Âu, Alaska hay Siberia không nhận được lá số. Nếu sửa riêng lỗi văng ra, bài luận sẽ gọi nhầm hệ nhà.
- **Sửa:** `angles_at` dùng hệ nhà người dùng chọn (cung mọc và thiên đỉnh không phụ thuộc hệ nhà), hoặc dùng `"O"`. Ghi vào output hệ nhà thực sự được dùng.
- **Test:** `test_high_latitude_non_placidus` (×2).

### A3 — SAI: lá số ngày/đêm (sect) suy từ số nhà
- **Vị trí:** `astro_cli.py:588-589`: `sect = "day" if 7 <= sun_house <= 12`.
- **Tái hiện:** Hà Nội 11/3/1999 06:16 (+7), `house_system="whole_sign"`. Engine ra **night**.
  - Mặt Trời 19°56′ Song Ngư, cung mọc 20°54′ Song Ngư, nên với whole sign Mặt Trời nằm ở nhà 1.
  - [DE421]: Mặt Trời cao **+0,7°** trên chân trời, nên đúng là **day**.
  - Với Placidus, kết quả đúng, vì cung nhà 1 và 7 trùng đường chân trời.
- **Ảnh hưởng:** khi dùng hệ nhà whole sign hoặc equal, bài luận theo trường phái truyền thống (sect, Phần Vận Mệnh, chủ tam phương) có thể đảo ngày thành đêm.
- **Sửa:** xác định sect bằng vị trí Mặt Trời so với đường chân trời, tức nửa vòng hoàng đạo từ DSC qua MC tới ASC, không qua số nhà.
- **Test:** `test_sect_whole_sign_after_sunrise`.

### A4 — THIẾU: không có giờ sinh
- **Vị trí:** `astro_cli.py:248-249`.
- **Tái hiện:** chỉ nhập `"1999-03-11"`.
  - Engine lập lá số lúc 00:00 và vẫn xuất cung mọc, các nhà, góc chiếu tới cung mọc/thiên đỉnh và khung thời gian đổi cung.
  - [DE421]: trong ngày đó Mặt Trăng đi từ 23°30′ Nhân Mã (00:00) tới 5°08′ **Ma Kết** (23:00). Engine chỉ báo "Nhân Mã".
- **Ảnh hưởng:** bài luận có thể khẳng định cung Mặt Trăng sai, và luận cả cung mọc dù cung mọc không xác định được.
- **Sửa:**
  - Theo quy ước thông dụng, lập lá số lúc 12:00 trưa.
  - Bỏ cung mọc, các nhà và góc chiếu tới góc lá số khỏi output.
  - Xuất khoảng vị trí Mặt Trăng trong ngày, kèm cờ nếu Mặt Trăng đổi cung.
- **Test:** `test_no_birth_time_flags_moon_sign_range`.

### A5 — NHỎ: nhãn độ làm tròn thành "30°00′" của cùng cung
- **Vị trí:** `astro_cli.py:135-146`.
- **Tái hiện:** `lon_label(359.995)` cho `30°00' Pisces`. Mặt Trời lúc 07:33 UTC ngày 20/3/2000 cũng hiện `30°00' Pisces`.
- **Ảnh hưởng:** LLM có thể đọc thành "cuối Song Ngư, sát Bạch Dương" hoặc nhầm sang Bạch Dương. Trường `sign` vẫn đúng.
- **Sửa:** cắt bớt phút thay vì làm tròn, hoặc khi làm tròn lên 30° thì hiện 29°59′.
- **Test:** `test_label_never_shows_30_degrees`.

### A6 — NHỎ: giờ sinh rơi vào lúc chuyển giờ mùa hè
- **Vị trí:** `astro_cli.py:165-172, 308-316`.
- **Tái hiện:** New York 07/11/2021 01:30 (giờ lặp lại), hoặc 14/03/2021 02:30 (giờ không tồn tại). kerykeion ném `KerykeionException`, và input không có tham số `is_dst` để người dùng chọn.
- **Ảnh hưởng:** không ảnh hưởng người sinh ở Việt Nam. Người sinh ở nước có giờ mùa hè đúng giờ chuyển sẽ không có lá số.
- **Sửa:** thêm tham số `is_dst` (hoặc `fold`) và truyền nó cho kerykeion.

### A7 — NHỎ: tên pha Mặt Trăng theo cách gọi thiên văn
- **Vị trí:** `astro_cli.py:391-395`.
- **Mô tả:** code chia 8 pha có tâm tại 0°, 45°, …; ví dụ "New Moon" là từ −22,5° tới 22,5°.
  - Chiêm tinh hay dùng 8 pha của Rudhyar, mỗi pha bắt đầu tại 0°, 45°, …; ví dụ góc 30° là pha Trăng Non, còn code gọi là "Waxing Crescent".
  - Cả hai đều có, nhưng output không ghi đang dùng quy ước nào.
- **Sửa:** ghi rõ quy ước trong output, hoặc dùng Rudhyar.

---

# Thần số học — `dlong1911/numerology_skills` @ `1188ab7`

## Bản đồ code và quy ước

File: `pythagorean-numerology/scripts/numerology_cli.py`, chỉ dùng thư viện chuẩn của Python.

- **Bảng chữ:** Pythagoras A–I = 1–9, lặp lại theo chu kỳ (`:25`). Code tự kiểm A = 1, R = 9, Z = 8.
- **Số được giữ nguyên:** 11, 22, 33, kể cả ở bước trung gian (`:69-75`).
- **Tên tiếng Việt:** đ/Đ → D, sau đó NFD và bỏ các dấu kết hợp (Mn), nên bỏ được cả dấu móc của Ư và Ơ (`:108-114`).
- **Mặc định:**
  - Đường đời = `component` (rút gọn tháng, ngày, năm riêng rồi cộng; kiểu Decoz).
  - Chỉ số tên = `per_part` (rút gọn từng từ rồi cộng; Decoz).
  - Chữ Y = `auto` (Y là phụ âm khi đứng cạnh A, E, I, O, U).
  - Năm cá nhân đổi vào ngày 1/1.
- **Biểu đồ ngày sinh và các mũi tên:** theo hệ của David A. Phillips, phổ biến ở Việt Nam (lưới 3-6-9 / 2-5-8 / 1-4-7).

## Ca chuẩn tính tay (khớp engine 100%; đã chuyển thành test)

Người: "Lê Duy Long", sinh 11/3/1999, ngày xem 20/11/2026.

Giá trị từng chữ: L3 E5 | D4 U3 Y7 | L3 O6 N5 G7, nên LE = 8, DUY = 14, LONG = 21.

| Chỉ số | Tính tay | Engine |
|---|---|---|
| Đường đời (component) | 3 + 11 + (1999 → 28 → 10 → 1) = 15 → **6** | 6 |
| Đường đời (all_digits) | 1+1+0+3+1+9+9+9 = **33** | 33 (trong `alternative`) |
| Sứ mệnh | 8 + (14 → 5) + (21 → 3) = 16 → **7**, nợ 16/7 | 7, 16/7 |
| Linh hồn (Y là phụ âm) | 5 + 3 + 6 = 14 → **5**, nợ 14/5 | 5 |
| Linh hồn (Y là nguyên âm) | 5 + (3+7 = 10 → 1) + 6 = 12 → **3** | 3 |
| Nhân cách | 3 + (4+7 = **11**, giữ nguyên) + (15 → 6) = 20 → **2**; cộng tổng: 29 → 11 | 2 / 11 |
| Ngày sinh, Trưởng thành, Thái độ | 11; 6 + 7 = 13 → 4; 3 + 11 = 14 → 5 | 11, 4, 5 |
| Năm, tháng, ngày cá nhân | 3 + 2 + 1 = 6; 6 + 11 = 17 → 8; 8 + 20 = 28 → 1 | 6, 8, 1 |
| Đỉnh cao | 5 (0–30, vì 36 − 6 = 30), 3 (31–39), 8 (40–48), 4 (từ 49) | Khớp |
| Thử thách | \|3−2\| = 1, \|2−1\| = 1, 0, \|3−1\| = 2 | Khớp |
| Biểu đồ ngày sinh | 1×3, 3×1, 9×3; mũi tên trống 4-5-6 và 2-5-8; các số đứng riêng 1, 3, 9 | Khớp |

## Phát hiện

### N1 — KHÔNG CĂN CỨ (trộn trường phái): mặc định số chủ đạo kiểu Decoz đi cùng biểu đồ kiểu Phillips
- **Vị trí:** `numerology_cli.py:204` (`life_path_method` mặc định `"component"`). Tài liệu `references/methods.md` của chính repo ghi `all_digits` "rất phổ biến trong các app/sách thần số học tiếng Việt".
- **Tái hiện:** ca chuẩn.
  - Engine mặc định ra **6**.
  - Cách cộng mọi chữ số (cách được nói là phổ biến ở Việt Nam) ra **33**, tức là số giữ nguyên.
  - Engine có trả cả hai và có cảnh báo. Nhưng trường `value` mà LLM đọc trước là 6.
- **Ảnh hưởng:** người dùng Việt Nam đã quen số chủ đạo 33 (từ app khác hoặc sách) nhận một bài luận về số 6, và hai bên mâu thuẫn ngay ở con số chính.
- **Sửa:** chọn một trường phái cho toàn bộ output và ghi tên trường phái vào `ruleset`. Nếu đối tượng là người Việt và dùng biểu đồ Phillips, mặc định nên là `all_digits`. Tôi chưa có bản sách gốc để khẳng định các quy tắc còn lại của trường phái đó (xem mục chưa kiểm).
- **Test:** `test_default_life_path_matches_vietnamese_convention`.

### N2 — NHỎ: dấu gạch nối nối hai từ thành một
- **Vị trí:** `:113`.
- **Mô tả:** "Hồng-Nhung" thành `HONGNHUNG`. Với cách `per_part`, việc rút gọn theo từng từ đổi khi gộp hai từ, dù ca thử "Phạm Hồng-Nhung" tình cờ ra cùng kết quả.
- **Sửa:** đổi dấu gạch nối thành khoảng trắng trước khi lọc ký tự.

---

## Chưa kiểm chứng được

- **Quy tắc chữ Y trong tên tiếng Việt.**
  - `auto` coi Y là phụ âm trong Duy, Huy, Thủy, Quý, Nguyễn (Y đứng cạnh U hoặc E), và là nguyên âm trong Lý, Mỹ, Vy.
  - Về ngữ âm tiếng Việt, Y trong "uy" và "uyê" là một phần của nguyên âm. Nhưng quy tắc Y kiểu Decoz ("Y là phụ âm khi cùng âm tiết đã có nguyên âm khác") lại cho ra kết quả như code.
  - Tôi không tìm được nguồn tiếng Việt có thẩm quyền.
  - Ảnh hưởng ở ca chuẩn: Linh hồn 5 so với 3, Nhân cách 2 so với 4. Đề nghị anh/chị chọn quy tắc theo sách mà sản phẩm dựa vào.
- **Quy tắc còn lại của trường phái Phillips ở Việt Nam:** có dùng 10 thay cho 1, khoảng số chủ đạo là 2–11, 22 và 33 hay không, và cách tính năm cá nhân. Chưa có bản sách gốc để đối chiếu. Phần này **chưa kiểm**; tôi chỉ kiểm code đúng với quy tắc nó tự công bố.
- **Đỉnh cao với số giữ nguyên:** code giữ 11, 22, 33 ở thành phần tháng, ngày, năm (P1 = 3 + 11). Có sách rút về một chữ số trước khi cộng. Ở ca chuẩn hai cách ra cùng kết quả; chưa có nguồn để chọn.
- **Code chọn dụng/hỷ/kỵ và đặt nhãn "cân bằng":** không có trong repo (F5). Chưa chạy được thêm lá số để xác nhận giả thuyết.
- **Engine không bỏ quan hệ hợp, nhưng bài luận thì không nhắc:** engine có xuất các quan hệ này, nên lỗi nằm ở bước dựng prompt hoặc chính LLM. Không kiểm được vì code đó không có trong repo.
- **Thứ tự tàng can của Tỵ:** code dùng Bính, Canh, Mậu (trung khí là Canh). Một số sách xếp Bính, Mậu, Canh. Cả hai trường phái đều có; tôi không có bản gốc để chọn. Thứ tự này ảnh hưởng điểm 0,3/0,1 và nhãn trung khí/dư khí.
- **Lịch âm miền Nam 1960–1975:** chính quyền miền Nam dùng UTC+8 cho giờ hành chính, nên có thể đã dùng lịch âm theo UTC+8 (trùng lịch Trung Quốc). Tôi không tìm được nguồn xác nhận. Lá số Tử Vi của người sinh ở miền Nam giai đoạn này nên đánh dấu "cần xác nhận".
- **Múi giờ miền Bắc 1945–1955:** tzdata ghi "+8 từ 1/4/1947 ở vùng Pháp kiểm soát", tức có hai chế độ song song. Chưa xác định được múi giờ theo nơi sinh.

## Chạy test

```
pip install "lunar_python>=1.4.8,<2" tzdata ephem "pytest<9"
python -m pytest bazi/scripts/tests ziwei-doushu/scripts/tests -rxX
```

Kết quả hiện tại: **270 passed, 7 xfailed**.

Chiêm tinh (repo `astrology_skills`, cần Python ≥ 3.12):

```
pip install "kerykeion==6.1.0" tzdata "pytest<9"
python -m pytest natal-astrology/scripts/tests -rxX
```

Kết quả: **38 passed, 6 xfailed** (A1–A5). Giá trị DE421 đã ghi sẵn trong test, nên chạy test không cần Skyfield.

Thần số học (repo `numerology_skills`):

```
python -m pytest pythagorean-numerology/scripts/tests -rxX
```

Kết quả: **37 passed, 1 xfailed** (N1).

Các test `xfail(strict=True)` ghi mã phát hiện (F1–F4, A1–A5, N1) trong `reason`. Khi một lỗi được sửa, test của nó chuyển sang XPASS và bị tính là lỗi do chế độ strict; lúc đó gỡ marker. Test so tiết khí với ephemeris tự bỏ qua nếu không cài `ephem`.

pytest 9.2 bị lỗi nội bộ (`INTERNALERROR ... _str_cache`) trên Python 3.10 nên phải dùng pytest 8.
