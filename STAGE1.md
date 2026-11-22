# Giai đoạn 1: sửa engine (chưa commit)

Nhánh `fix/audit-stage1` ở cả ba repo (Numerologist_skills, astrology_skills, numerology_skills). Chưa commit, chưa push.

| Repo | Lệnh test | Kết quả |
|---|---|---|
| Numerologist_skills (Bát tự, Tử Vi, Kỳ Môn) | `pytest bazi ziwei-doushu qimen-dunjia` | **489 passed, 1 xfailed** (F4) |
| astrology_skills (Python 3.12) | `pytest natal-astrology/scripts/tests` | **45 passed, 3 xfailed** (A2 ×2, A5: chưa được yêu cầu sửa) |
| numerology_skills | `pytest pythagorean-numerology/scripts/tests` | **46 passed** |

## Đính chính báo cáo audit (do nguồn mới tìm được ở bước này)

- **F1:** lịch âm Việt Nam chỉ tính theo UTC+7 từ **8/8/1967**, và chỉ ở miền Bắc. Trước đó Việt Nam dùng lịch tính theo UTC+8, trùng lịch Trung Quốc. Miền Nam giữ UTC+8 tới 13/6/1975.
  - Nguồn: [Vietnamese calendar (Wikipedia)](https://en.wikipedia.org/wiki/Vietnamese_calendar), dẫn Aslaksen, *The Mathematics of the Chinese Calendar*, tr. 29–30. Trang này cũng ghi Tết 1968 hai miền khác ngày.
  - Vì vậy các ngày lệch giai đoạn 1950–1967 mà báo cáo audit đếm **không phải lỗi**. Lỗi F1 chỉ đúng từ 1967.
- **F2:** múi giờ miền Bắc giai đoạn 1955–1967 có **nguồn mâu thuẫn**.
  - [Wikipedia](https://en.wikipedia.org/wiki/Vietnamese_calendar) và [tz mailing list 2011](https://mm.icann.org/pipermail/tz/2011-May/008539.html) cho rằng miền Bắc ở +8 tới 8/8/1967.
  - Sách Gabriel, *Traité de l'heure dans le monde* (1991), theo [tz mailing list 2011](https://mm.icann.org/pipermail/tz/2011-May/008537.html), ghi +7 trong 1955–1960.
  - tzdata gán miền Bắc vào Asia/Bangkok (+7), nhưng tzdata chỉ cam kết số liệu từ 1970.
  - Ca Hà Nội 1970 trong F2/A1 vẫn đúng: mọi nguồn đều cho miền Bắc ở +7 từ 1967.

## 1. Lịch và múi giờ dùng chung (F1, F2, A1): đã sửa

Module mới `vn_calendar.py`, giống hệt nhau ở `bazi/scripts`, `ziwei-doushu/scripts` và `natal-astrology/scripts`. Có test kiểm hai bản trong cùng repo là một.

**Bảng múi giờ theo miền** (`VN_OFFSETS`; mỗi mốc ghi mã nguồn, danh sách đầy đủ trong `SOURCES`):

| Từ (giờ địa phương) | Miền Bắc | Miền Nam | Nguồn |
|---|---|---|---|
| 1/7/1906 | +7:06:30 (PLMT) | như Bắc | tzdata (Trần Tiến Bình 2005) |
| 1/5/1911 | +7 | như Bắc | tzdata |
| 31/12/1942 23:00 | +8 | như Bắc | tzdata |
| 14/3/1945 23:00 | +9 | như Bắc | tzdata |
| 2/9/1945 | +7 | như Bắc | tzdata; Việt Nam Dân Quốc Công Báo số 1 (29/9/1945) |
| 1/4/1947 | +8 | +8 | tzdata (vùng Pháp kiểm soát) |
| 1/7/1955 01:00 | +8 (**chưa chắc**, có cảnh báo) | +7 | tzdata; Dụ 46 (25/6/1955), Công Báo VN số 92 |
| 31/12/1959 23:00 | +8 (chưa chắc) | +8 | tzdata; Sắc lệnh 362-TTP (30/12/1959) |
| 8/8/1967 | +7 | +8 | Wikipedia (dẫn Aslaksen); tz list 2011 |
| 13/6/1975 | +7 | +7 | tzdata |

**Tham số mới:**
- `birth_region`: `north` hoặc `south` (nhận cả "Miền Bắc", "bac"…), hoặc suy từ `latitude` (trên 17°N là miền Bắc).
- Chỉ bắt buộc khi hai miền khác nhau tại thời điểm đó. Thiếu thì engine báo lỗi kèm câu cần hỏi người dùng, không tự đoán.
- Chiêm tinh luôn có vĩ độ, nên tự suy ra miền. Bảng thành phố (Hà Nội, Hải Phòng, Vinh) giờ ra đúng mà không cần sửa bảng.

**Lịch âm Việt Nam:**
- Dùng quy tắc của lịch Trung Quốc, tính tại kinh tuyến của giờ pháp định. Thời điểm sóc và trung khí lấy từ hàm chính xác cao (寿星) của lunar_python.
- Ngày nào áp UTC+8 thì giao hẳn cho lunar_python, để giữ cả các hiệu chỉnh lịch đã công bố trước 1960.
- Kiểm chứng (`audit/check2.py`, `audit/ref.py`):
  - Đầu tháng âm 1901–2100 tại UTC+7 khớp bản PyEphem độc lập, trừ 2 tháng (12/2072, 11/2077): sóc rơi cách nửa đêm vài giây, DE421 không phủ tới nên chưa phân xử được.
  - Đổi âm sang dương rồi ngược lại cho 2.473 đầu tháng: 0 lỗi.
- **Tôi đã bỏ thuật toán Hồ Ngọc Đức** vì nó lệch 92 ngày (1900–2100) so với tính chính xác. Trang nguồn của tác giả cũng không còn truy cập được (lỗi 404).

**Đã nối vào:**
- **Bát tự:** đổi âm sang dương (`lunar_calendar`, mặc định `vn` khi timezone là Việt Nam) và giờ sinh theo miền.
- **Tử Vi:** `lunar_calendar` mặc định `vn`; test so với iztro truyền `cn`, vì iztro dùng lịch Trung Quốc.
- **Chiêm tinh:** thời điểm sinh dùng `Etc/GMT-N` theo bảng; các transit vẫn dùng timezone gốc.

**Ca kiểm:**
- Tết Mậu Thân: miền Bắc 29/1/1968, miền Nam 30/1/1968.
- Âm lịch 1/1/2007 là 17/2/2007; 1/1/1985 là 21/1/1985.
- Tử Vi người sinh 1/2/1985 ra Ất Sửu tháng Giêng ngày 12.
- Hà Nội 15/6/1970 13:20 ra trụ giờ Mùi; chiêm tinh ra UTC 06:20, cung mọc Thiên Bình.

## 2. Bát tự: thân vượng/nhược và dụng/hỷ/kỵ — ĐÃ LÀM theo phương án "chỉ phán khi chắc"

**Đã làm (sau khi anh/chị duyệt):**
- Thêm trường mới `chart.strength_assessment` trong `bazi_cli.py`. `heuristic_score` vẫn giữ nhưng ghi DEPRECATED, và SKILL.md cấm LLM dùng nó.
- `level` nhận một trong các giá trị:
  - `weak`: tỷ lệ hỗ trợ dưới 0,25 và 0/3 điều kiện;
  - `strong`: tỷ lệ trên 0,65 và 3/3 điều kiện;
  - `possible_follow`: tỷ lệ dưới 0,15 và không có gốc ở bản khí/trung khí;
  - `possible_dominant`: tỷ lệ trên 0,85;
  - `undetermined`: mọi trường hợp còn lại.
- `useful_gods` chỉ có khi `weak`/`strong`. Code kiểm cứng hỷ không khắc dụng, kỵ là hành khắc dụng.
- Ngưỡng 0,15 cho tòng cách tôi đặt **sau khi** xem #8 và #19. Đó là điều chỉnh theo bộ chuẩn, cần thêm lá số để kiểm.
- Kết quả trên bộ chuẩn:
  - #8: nhược rõ, dụng Mộc, đúng sách.
  - #19: có thể tòng cách, đúng sách.
  - Ca chuẩn: có thể tòng cách, cần luận, không có dụng/hỷ/kỵ.
  - 18 lá số còn lại: cần luận. **Không lá số nào bị phán ngược sách.**
- Test: `test_never_contradicts_book` (20 lá số) và kiểm "hỷ không khắc dụng" trên 3.000 tứ trụ ngẫu nhiên.

**Phần dưới là đề xuất ban đầu và số liệu đã dùng để quyết định.**

**Công thức hiện tại:** xem F3 (điểm) và F5 (dụng/hỷ/kỵ nằm ngoài các repo này).
- Ca chuẩn ra −0,2 vì:
  - nguyệt lệnh "hưu" được 0 điểm;
  - không có gốc;
  - Quý (kiếp tài) cộng 0,8; Kỷ (quan) và Đinh (tài) trừ 0,5 mỗi chữ;
  - còn ba chữ Mão (thương quan) nằm ở địa chi nên **không bị trừ gì**.
- Dụng Kim / hỷ Hỏa / kỵ Mộc khớp đúng phép "hành yếu nhất / yếu nhì / mạnh nhất" theo `element_counts.weighted` (Kim 0,3; Hỏa 1,1; Mộc 3,0). Phép này không xét sinh khắc, nên mới ra hỷ Hỏa khắc dụng Kim.

**Công thức thử** (`audit/strength_proposal.py`; trọng số chọn trước khi chạy bộ chuẩn):
- Lực của mỗi chữ chia theo vai trò so với nhật chủ (tỷ kiếp, ấn, thực thương, tài, quan sát):
  - can năm, tháng, giờ: 1,0; can lộ mà không thông căn chỉ tính 60%;
  - chi năm 1,0; **chi tháng 3,0 (nguyệt lệnh)**; chi ngày 1,5; chi giờ 1,0;
  - mỗi chi chia cho các tàng can theo tỷ lệ 0,6/0,3/0,1.
- Tỷ lệ hỗ trợ = (tỷ kiếp + ấn) / tổng. Từ 0,55 trở lên là vượng, dưới 0,45 là nhược, ở giữa là trung hòa.
- Dụng/hỷ/kỵ theo phù ức:
  - Nhược: tài nặng nhất thì dụng tỷ kiếp, hỷ ấn; ngược lại dụng ấn, hỷ tỷ kiếp.
  - Vượng: ấn nặng hơn tỷ kiếp thì dụng tài, hỷ thực thương; ngược lại dụng quan sát (hỷ tài), hoặc thực thương nếu không có quan sát.
  - Kỵ thần là hành khắc dụng thần. Code **kiểm cứng** rằng hỷ thần không khắc dụng thần.

**Bộ chuẩn:** 20 lá số trong 《滴天髓闡微》 (Nhậm Thiết Tiều chú), bản [zh.wikisource](https://zh.wikisource.org/wiki/%E6%BB%B4%E5%A4%A9%E9%AB%93%E9%97%A1%E5%BE%AE). Gồm 18 lá số thường và 2 tòng cách; mỗi lá có lời phán thân vượng/nhược và dụng thần ghi rõ trong sách (cột cuối của `BENCH` ghi mục). Lưu ý bản wikisource có lỗi chép; nên đối chiếu tứ trụ với bản in.

Bảng so sánh. "Cũ: dụng/hỷ/kỵ" là giả thuyết công thức tầng ngoài (F5). Cột "Cũ: nhãn" là cân bằng khi |điểm| ≤ 0,5.

| # | Tứ trụ | Sách: thân | Sách: dụng | Cũ: điểm → nhãn | Cũ: dụng/hỷ/kỵ | Thử: tỷ lệ → mức | Thử: dụng/hỷ/kỵ | Thân đúng cũ/thử | Dụng đúng cũ/thử |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 癸卯 丙辰 甲辰 丙寅 | vượng | Thổ | +1.8 → vượng | Kim/Thủy/Mộc | 0.46 → trung hòa | —/—/— | ✓/✗ | ✗/✗ |
| 2 | 己卯 庚午 甲寅 丁卯 | vượng | Hỏa | +1.5 → vượng | Thủy/Kim/Mộc | 0.32 → nhược | Thủy/Mộc/Thổ | ✓/✗ | ✗/✗ |
| 3 | 癸巳 壬戌 乙卯 戊寅 | vượng | Hỏa | +2.1 → vượng | Kim/Hỏa/Mộc | 0.38 → nhược | Mộc/Thủy/Kim | ✓/✗ | ✗/✗ |
| 4 | 丙子 己亥 乙酉 壬午 | nhược | Hỏa | +1.8 → vượng | Kim/Mộc/Thủy | 0.53 → trung hòa | —/—/— | ✗/✗ | ✗/✗ |
| 5 | 丁卯 辛亥 丙寅 丙申 | vượng | Thủy | +0.1 → cân bằng | Thổ/Thủy/Hỏa | 0.55 → vượng | Kim/Thổ/Hỏa | ✗/✓ | ✗/✗ |
| 6 | 乙亥 辛巳 丙辰 癸巳 | nhược | Hỏa | +3.8 → vượng | Thổ/Mộc/Hỏa | 0.44 → nhược | Hỏa/Mộc/Thủy | ✗/✓ | ✗/✓ |
| 7 | 丙申 戊戌 丁卯 乙巳 | vượng | Kim | +2.4 → vượng | Thủy/Kim/Hỏa | 0.46 → trung hòa | —/—/— | ✓/✗ | ✗/✗ |
| 8 | 癸亥 甲子 丁酉 癸卯 | nhược | Mộc | −1.7 → nhược | Thổ/Hỏa/Thủy | 0.24 → nhược | Mộc/Hỏa/Kim | ✓/✓ | ✗/✓ |
| 9 | 庚申 庚辰 戊辰 戊午 | nhược | Hỏa | +4.6 → vượng | Thủy/Mộc/Thổ | 0.51 → trung hòa | —/—/— | ✗/✗ | ✗/✗ |
| 10 | 己丑 庚午 戊申 癸亥 | nhược | Hỏa | +3.1 → vượng | Mộc/Hỏa/Thổ | 0.50 → trung hòa | —/—/— | ✗/✗ | ✗/✗ |
| 11 | 辛酉 辛丑 己酉 丙寅 | nhược | Hỏa | +3.1 → vượng | Thủy/Mộc/Kim | 0.34 → nhược | Hỏa/Thổ/Thủy | ✗/✓ | ✗/✓ |
| 12 | 丁未 庚戌 庚辰 丙子 | vượng | Hỏa | +1.8 → vượng | Mộc/Thủy/Hỏa | 0.55 → trung hòa | —/—/— | ✓/✗ | ✗/✗ |
| 13 | 己酉 丙寅 庚申 庚辰 | vượng | Mộc | +2.1 → vượng | Thủy/Mộc/Kim | 0.52 → trung hòa | —/—/— | ✓/✗ | ✗/✗ |
| 14 | 甲午 丙寅 辛酉 己丑 | nhược | Thổ | +0.1 → cân bằng | Thủy/Mộc/Kim | 0.40 → nhược | Kim/Thổ/Hỏa | ✗/✓ | ✗/✗ |
| 15 | 己丑 丙子 辛酉 壬辰 | vượng | Thủy | +1.1 → vượng | Mộc/Hỏa/Thủy | 0.42 → nhược | Thổ/Kim/Mộc | ✓/✗ | ✗/✗ |
| 16 | 癸亥 乙卯 壬申 乙巳 | vượng | Hỏa | +1.3 → vượng | Thổ/Hỏa/Mộc | 0.35 → nhược | Kim/Thủy/Hỏa | ✓/✗ | ✗/✗ |
| 17 | 庚午 己卯 壬申 己酉 | vượng | Thổ | +0.3 → cân bằng | Hỏa/Mộc/Kim | 0.35 → nhược | Kim/Thủy/Hỏa | ✗/✗ | ✗/✗ |
| 18 | 戊午 乙卯 癸卯 癸亥 | nhược | Thủy | +0.8 → vượng | Kim/Hỏa/Mộc | 0.18 → nhược | Kim/Thủy/Hỏa | ✗/✓ | ✗/✗ |
| 19 | 丁卯 壬寅 癸卯 丙辰 | tòng nhi | Hỏa | +0.1 → cân bằng | Kim/Thổ/Mộc | 0.12 → nhược | Kim/Thủy/Hỏa | –/– | ✗/✗ |
| 20 | 庚辰 己丑 己亥 壬申 | giả tòng tài | Thủy | +4.1 → vượng | Hỏa/Mộc/Thổ | 0.37 → nhược | Thổ/Hỏa/Mộc | –/– | ✗/✗ |
| 0 | 己卯 丁卯 壬戌 癸卯 (ca chuẩn) | nhược (tính tay, F3) | Kim | −0.2 → cân bằng | Kim/Hỏa/Mộc | 0.12 → nhược | Kim/Thủy/Hỏa | –/– | ✓/✓ |

Trên 18 lá số thường: thân đúng **cũ 9/18, thử 6/18**; dụng đúng **cũ 0/18, thử 3/18**. Thêm quy tắc ba điều kiện cổ điển (đắc lệnh / đắc địa / đắc thế, vượng nếu đạt ít nhất 2): thân đúng **8/18**.

**Kết luận và đề xuất (cần anh/chị quyết):**
1. Không công thức cộng điểm nào tái hiện được lời phán của Nhậm Thiết Tiều; cả ba đều quanh mức may rủi.
   - Lời phán trong sách dựa vào hợp hóa, xung, lưu thông sinh hóa và điều hậu (ví dụ #4, #9, #13: "nhược mà thành vượng"), không dựa vào tổng lực.
   - Tôi **không** khuyên thay công thức cũ bằng công thức thử rồi coi như đã sửa.
2. Đề xuất thay thế: engine **chỉ phán khi chắc chắn**.
   - Xuất đủ các yếu tố: lực theo vai trò, đắc lệnh, đắc địa, đắc thế, gốc, hợp xung.
   - Chỉ ghi "thân nhược rõ" / "thân vượng rõ" khi tỷ lệ hỗ trợ dưới 0,25 hoặc trên 0,65 **và** ba điều kiện cùng chiều (0/3 hoặc 3/3).
   - Còn lại ghi "cần luận", và **không xuất dụng/hỷ/kỵ**, để LLM không biến một con số yếu thành lời khuyên chắc chắn.
   - Khi phán rõ: dụng/hỷ/kỵ theo phù ức như trên (hỷ không khắc dụng), ghi rõ "trường phái phù ức, chưa xét điều hậu".
   - Trên bộ chuẩn, ngưỡng "rõ" chỉ bắt được 3 lá số: #8 (đúng là nhược), **#19** và ca chuẩn. Tất cả lá số khác ra "cần luận".
   - **#19 là vấn đề:** sách phán #19 là **tòng nhi cách** (dụng Hỏa, kỵ Thủy). Nhưng các con số của #19 giống hệt ca chuẩn: tỷ lệ 0,12, ba điều kiện 0/3, nhật chủ Quý/Nhâm sinh tháng Dần/Mão, Thủy Mộc nhiều.
   - Vì vậy cần thêm quy tắc: tỷ lệ dưới khoảng 0,15 và không có gốc thì ghi "**có thể tòng cách — cần luận**", không xuất dụng/hỷ/kỵ.
3. **Ca chuẩn rơi đúng vào vùng này.**
   - Theo phù ức, nó là thân nhược: dụng Kim, hỷ Thủy, kỵ Hỏa.
   - Theo quy tắc tòng/hóa cách, nó có thể là tòng nhi cách, hoặc hóa Mộc cách (Đinh Nhâm hợp, sinh tháng Mão, là một điều kiện của hóa Mộc). Khi đó dụng thần là Mộc/Hỏa, **ngược hẳn**.
   - Engine không có căn cứ để tự chọn giữa hai cách đọc. Tôi đề nghị anh/chị (hoặc người luận số anh/chị tin) xác định cách cục cho ca chuẩn, rồi tôi dùng nó làm ca kiểm.
4. F5: phép chọn "yếu nhất / yếu nhì / mạnh nhất" ở tầng ngoài phải bỏ, dù chọn phương án nào.

## 3. Tử Vi: đã bổ sung

- `chart.xunkong` (Tuần), `chart.jielu` (Triệt), và cờ cho từng cung. Ca chuẩn Kỷ Mão: **Tuần ở Thân–Dậu, Triệt ở Thân–Dậu**.
- `palaces[].no_major_star` và `borrowed_major_stars` (chính tinh mượn từ cung đối, kèm miếu hãm tại cung gốc). Ca chuẩn có 4 cung vô chính diệu: Tuất mượn Cơ Lương, Thân mượn Nhật Cự, Mùi mượn Vũ Tham, Ngọ mượn Đồng Âm.
- Lưu niên cung và lưu Tứ Hóa đã có sẵn (`horoscope.yearly`). Mới thêm `horoscope.xiaoxian` (tiểu hạn).
- Ca chuẩn năm 2026 (Bính Ngọ):
  - Tiểu hạn ở Thìn (cung Nô): tuổi Mão khởi tiểu hạn từ Sửu, nam đi thuận, tuổi mụ 28, nên Sửu + 27 = Thìn.
  - Lưu niên ở Ngọ. **Liêm Trinh hóa Kỵ tại Dậu.**
- Test: `ziwei-doushu/scripts/tests/test_ziwei_additions.py`, mọi giá trị đều tính tay theo quy tắc ghi ở đầu file:
  - Tuần/Triệt: 6 lá số; vô chính diệu: 6 vị trí Tử Vi; tiểu hạn, lưu niên, lưu Tứ Hóa: 7 lá số (cả nam và nữ).
  - Lúc tính tay, tôi xếp nhầm Bính Ngọ vào tuần Giáp Thân. Engine đúng (tuần Giáp Thìn, Tuần ở Dần–Mão), và test đã sửa theo.

## 4. Chiêm tinh và thần số học: đã sửa

- **A3:** sect xác định bằng vị trí Mặt Trời so với đường chân trời (cung hoàng đạo từ cung mọc qua thiên đỉnh), không qua số nhà.
- **A4:** không có giờ sinh thì:
  - lập lá số lúc 12:00 trưa;
  - bỏ cung mọc, thiên đỉnh, các nhà, chủ tinh lá số, sect, độ nhạy giờ sinh, cùng góc chiếu và transit tới các góc;
  - thêm `chart.moon_range`, và cảnh báo khi Mặt Trăng đổi cung trong ngày (ví dụ 11/3/1999: Nhân Mã sang Ma Kết).
- **Python ≥ 3.12:** ghi trong requirements.txt, SKILL.md, README; `astro_cli.py` dừng kèm thông báo rõ nếu chạy bằng phiên bản thấp hơn.
- **N1:** mặc định `life_path_method="phillips"`: cộng mọi chữ số; giữ 10, 11, 22 (hiện 22/4) và **33 (hiện 33/6, luận riêng)**, theo quyết định của anh/chị.
  - Ca chuẩn 11/3/1999 giờ ra **33**; cách Decoz ra 6.
  - Trong 1900–2030 có **11.946/47.847 ngày (25,0%)** hai cách khác nhau:

| Decoz | Phillips | số ngày | ví dụ |
|---|---|---|---|
| 1 | 10 | 5315 | 08/01/1900 |
| 6 | 33/6 | 1694 | 29/09/1903, 11/03/1999 |
| 2 | 11 | 1597 | 29/08/1900 |
| 4 | 22/4 | 1378 | 29/01/1900 |
| 22 | 4 | 985 | 29/08/1902 |
| 11 | 2 | 889 | 09/01/1900 |
| 33 | 6 | 88 | 11/11/1901 (tổng các chữ số là 15) |

  - Chưa đối chiếu được với sách gốc của Phillips (archive.org từ chối kết nối). Tài liệu thực hành "Power of Numbers" cũng ghi các số chủ đạo là 2–11, 22/4 và 33/6, khớp với lựa chọn giữ 33.
- **Chữ Y:** mặc định `y_rule="vowel"` (luôn là nguyên âm), đã ghi trong methods.md và SKILL.md. Ca chuẩn đổi thành Linh hồn 3, Nhân cách 4 (nợ 13/4).

## Còn mở

- Cách cục của ca chuẩn (thân nhược hay tòng/hóa cách): engine ghi "cần luận". Khi anh/chị có lời phán, tôi thêm nó làm ca kiểm.
- Giai đoạn 2 cần code của ứng dụng gọi LLM (chart.json, prompt từng chủ đề, `max_tokens`). Code này không có trong ba repo.
