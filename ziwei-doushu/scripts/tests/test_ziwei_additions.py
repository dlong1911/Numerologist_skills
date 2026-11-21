"""Tuần/Triệt, vô chính diệu (+ borrowed stars), tiểu hạn, lưu niên, lưu Tứ Hóa.

Every expected value below is a hand derivation from the rules (shown in comments):
  Triệt (截路空亡) by year stem: 甲己→申酉, 乙庚→午未, 丙辛→辰巳, 丁壬→寅卯, 戊癸→子丑.
  Tuần (旬空) by year ganzhi: the two branches missing from its decade (甲子旬→戌亥, 甲戌旬→申酉,
      甲申旬→午未, 甲午旬→辰巳, 甲辰旬→寅卯, 甲寅旬→子丑).
  14 stars from Tử Vi at branch z: 天机 z−1, 太阳 z−3, 武曲 z−4, 天同 z−5, 廉贞 z−8;
      天府 f = 4−z; 太阴 f+1, 贪狼 f+2, 巨门 f+3, 天相 f+4, 天梁 f+5, 七杀 f+6, 破军 f+10.
      Vô chính diệu = no major star; borrowed = major stars of the opposite palace (+6).
  Tiểu hạn: 寅午戌年起辰, 申子辰年起戌, 巳酉丑年起未, 亥卯未年起丑; nam thuận, nữ nghịch; 1 cung / tuổi mụ.
  Lưu niên cung = chi của năm xem. Lưu Tứ Hóa = Tứ Hóa theo can năm xem, đặt tại vị trí sao gốc.
  文昌 = 戌 − giờ.
Branch numbers: 子0 丑1 寅2 卯3 辰4 巳5 午6 未7 申8 酉9 戌10 亥11.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from ziwei_cli import build_output

CANON = ("1999-03-11 05:15", "男")


def chart(bt, g, **kw):
    return build_output({"calendar_type": "solar", "birth_time": bt, "gender": g, **kw})


def palace_by_branch(out):
    return {p["branch"]: p for p in out["chart"]["palaces"]}


# ------------------------------------------------------------ Tuần / Triệt

@pytest.mark.parametrize("bt,g,year_gz,tuan,triet", [
    ("1999-03-11 05:15", "男", "己卯", ["申", "酉"], ["申", "酉"]),  # 己卯 ∈ 甲戌旬 → 申酉; 己 → 申酉
    ("2000-08-15 12:00", "男", "庚辰", ["申", "酉"], ["午", "未"]),  # 庚辰 ∈ 甲戌旬; 庚 → 午未
    ("1984-06-15 08:00", "女", "甲子", ["戌", "亥"], ["申", "酉"]),  # 甲子旬 → 戌亥; 甲 → 申酉
    ("1966-06-15 20:00", "男", "丙午", ["寅", "卯"], ["辰", "巳"]),  # 甲辰旬 (甲辰 乙巳 丙午 … 癸丑) → 寅卯; 丙 → 辰巳
    ("2017-06-15 02:00", "女", "丁酉", ["辰", "巳"], ["寅", "卯"]),  # 丁酉 ∈ 甲午旬 → 辰巳; 丁 → 寅卯
    ("1983-06-15 10:00", "男", "癸亥", ["子", "丑"], ["子", "丑"]),  # 癸亥 ∈ 甲寅旬 → 子丑; 癸 → 子丑
])
def test_tuan_triet(bt, g, year_gz, tuan, triet):
    o = chart(bt, g)
    assert o["calendar"]["year_ganzhi"] == year_gz
    assert o["chart"]["xunkong"] == tuan and o["chart"]["jielu"] == triet
    pb = palace_by_branch(o)
    assert {b for b, p in pb.items() if p["xunkong"]} == set(tuan)
    assert {b for b, p in pb.items() if p["jielu"]} == set(triet)


# ------------------------------------------------------------ vô chính diệu

@pytest.mark.parametrize("bt,ziwei,empty", [
    # z=5 (巳): 机辰 阳寅 武丑 同子 廉酉; f=亥: 阴子 贪丑 巨寅 相卯 梁辰 杀巳 破酉 → 午未申戌 empty
    ("1999-03-11 05:15", "巳", {"午": ["天同", "太阴"], "未": ["武曲", "贪狼"], "申": ["太阳", "巨门"], "戌": ["天机", "天梁"]}),
    # z=2 (寅): 机丑 阳亥 武戌 同酉 廉午; f=寅: 阴卯 贪辰 巨巳 相午 梁未 杀申 破子 → none empty
    ("1990-01-01 12:00", "寅", {}),
    # z=0 (子): 机亥 阳酉 武申 同未 廉辰; f=辰: 阴巳 贪午 巨未 相申 梁酉 杀戌 破寅 → 丑卯 empty
    ("1990-01-03 12:00", "子", {"丑": ["天同", "巨门"], "卯": ["太阳", "天梁"]}),
    # z=6 (午): 机巳 阳卯 武寅 同丑 廉戌; f=戌: 阴亥 贪子 巨丑 相寅 梁卯 杀辰 破申 → 未酉 empty
    ("1990-01-09 12:00", "午", {"未": ["天同", "巨门"], "酉": ["太阳", "天梁"]}),
    # z=9 (酉): 机申 阳午 武巳 同辰 廉丑; f=未: 阴申 贪酉 巨戌 相亥 梁子 杀丑 破巳 → 寅卯 empty
    ("1990-01-12 12:00", "酉", {"寅": ["天机", "太阴"], "卯": ["紫微", "贪狼"]}),
    # z=11 (亥): 机戌 阳申 武未 同午 廉卯; f=巳: 阴午 贪未 巨申 相酉 梁戌 杀亥 破卯 → 子丑寅辰 empty
    ("1990-01-22 12:00", "亥", {"子": ["天同", "太阴"], "丑": ["武曲", "贪狼"], "寅": ["太阳", "巨门"], "辰": ["天机", "天梁"]}),
])
def test_vo_chinh_dieu_and_borrowed(bt, ziwei, empty):
    o = chart(bt, "男")
    assert o["chart"]["self_check"]["ziwei_branch"] == ziwei
    pb = palace_by_branch(o)
    assert {b for b, p in pb.items() if p["no_major_star"]} == set(empty)
    for b, stars in empty.items():
        borrowed = pb[b]["borrowed_major_stars"]
        assert sorted(s["name"] for s in borrowed) == sorted(stars)
    for b, p in pb.items():
        if not p["no_major_star"]:
            assert p["borrowed_major_stars"] == []


# ------------------------------------------------------------ tiểu hạn, lưu niên, lưu Tứ Hóa

@pytest.mark.parametrize("bt,g,query,age,xiaoxian,liunian,sihua", [
    # 己卯 (亥卯未 → 丑), nam: 丑 + 27 = 辰. 2026 丙午: 同(z−5=子)禄 机(辰)权 昌(戌−卯=未)科 廉(酉)忌
    ("1999-03-11 05:15", "男", 2026, 28, "辰", "午", [("天同", "子"), ("天机", "辰"), ("文昌", "未"), ("廉贞", "酉")]),
    # same chart, nữ: 丑 − 27 = 戌 (stars unchanged)
    ("1999-03-11 05:15", "女", 2026, 28, "戌", "午", [("天同", "子"), ("天机", "辰"), ("文昌", "未"), ("廉贞", "酉")]),
    # 庚辰 (申子辰 → 戌), nam, z=酉: 戌 + 26 = 子. 丙: 同辰 机申 昌(戌−午=辰) 廉丑
    ("2000-08-15 12:00", "男", 2026, 27, "子", "午", [("天同", "辰"), ("天机", "申"), ("文昌", "辰"), ("廉贞", "丑")]),
    # 甲子 (申子辰 → 戌), nữ, z=卯 (f=丑): 戌 − 41 = 巳. 2025 乙巳: 机寅禄 梁(f+5=午)权 紫卯科 阴(f+1=寅)忌
    ("1984-06-15 08:00", "女", 2025, 42, "巳", "巳", [("天机", "寅"), ("天梁", "午"), ("紫微", "卯"), ("太阴", "寅")]),
    # 丙午 (寅午戌 → 辰), nam, z=未 (f=酉): 辰 + 64 = 申. 2030 庚戌: 阳辰禄 武卯权 阴(f+1=戌)科 同寅忌
    ("1966-06-15 20:00", "男", 2030, 65, "申", "戌", [("太阳", "辰"), ("武曲", "卯"), ("太阴", "戌"), ("天同", "寅")]),
    # 丁酉 (巳酉丑 → 未), nữ, z=寅: 未 − 9 = 戌. 丙: 同酉 机丑 昌(戌−丑=酉) 廉午
    ("2017-06-15 02:00", "女", 2026, 10, "戌", "午", [("天同", "酉"), ("天机", "丑"), ("文昌", "酉"), ("廉贞", "午")]),
    # 癸亥 (亥卯未 → 丑), nam, z=子: 丑 + 43 = 申. 丙: 同未 机亥 昌(戌−巳=巳) 廉辰
    ("1983-06-15 10:00", "男", 2026, 44, "申", "午", [("天同", "未"), ("天机", "亥"), ("文昌", "巳"), ("廉贞", "辰")]),
])
def test_yearly_layers(bt, g, query, age, xiaoxian, liunian, sihua):
    h = chart(bt, g, query_year=query)["horoscope"]
    assert h["nominal_age"] == age
    assert h["xiaoxian"]["branch"] == xiaoxian
    assert h["yearly"]["ming_branch"] == liunian
    assert [(x["star"], x["branch"]) for x in h["yearly"]["sihua"]] == sihua


def test_canonical_bingwu_lianzhen_ji_at_you():
    h = chart(*CANON, query_year=2026)["horoscope"]
    ji = [x for x in h["yearly"]["sihua"] if x["type"] == "化忌"][0]
    assert (ji["star"], ji["branch"]) == ("廉贞", "酉")
