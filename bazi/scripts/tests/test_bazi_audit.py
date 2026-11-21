"""Audit tests for bazi_cli.py (see AUDIT.md at the repo root).

Every expected value cites an independent source:
  [EPH]  PyEphem 4.2 (VSOP87 Sun) for 节气 instants and true solar time.
  [JDN]  Julian Day Number: day index = (JDN + 49) mod 60, anchored at 2000-01-01 = 戊午.
  [TZ]   IANA tzdata 'asia' file (Vietnam section, citing Trần Tiến Bình 2005).
  [VNL]  Vietnamese lunisolar calendar = Chinese rules computed at UTC+7 (Hồ Ngọc Đức);
         re-implemented with PyEphem, which reproduces lunar_python exactly at UTC+8 for 1950-2030.
         Tết 1985 = 21/1/1985 and Tết 2007 = 17/2/2007 are also widely published.
  [HAND] Hand calculation, steps shown in AUDIT.md.

Tests marked xfail(strict=True) are known defects; the reason names the finding ID.
When a defect is fixed, the test starts passing (XPASS) and strict mode fails it,
so remove the marker then.
"""

import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "bazi" / "scripts"))
sys.path.insert(0, str(ROOT / "ziwei-doushu" / "scripts"))

import pytest
from lunar_python import Solar
from lunar_python.util import LunarUtil

import bazi_cli as B

STEMS, BRANCHES = B.STEMS, B.BRANCHES
JIAZI = B.JIAZI


def run(**kw):
    p = {"calendar_type": "solar", "gender": "男", "timezone": "Asia/Ho_Chi_Minh"}
    p.update(kw)
    return B.build_output(p)


# ------------------------------------------------------------ canonical case (confirmed by the user)

CANON = dict(birth_time="1999-03-11 05:15")


def test_canonical_pillars():
    c = run(**CANON)["chart"]
    assert c["bazi"] == "己卯 丁卯 壬戌 癸卯"


def test_canonical_dayun_backward_jiazi_from_2020():
    c = run(**CANON)["chart"]
    assert c["dayun"]["direction"] == "逆排"
    jz = [d for d in c["dayun"]["pillars"] if d["ganzhi"] == "甲子"][0]
    assert jz["start_year"] == 2020


def test_canonical_dayun_start_matches_ephemeris():
    # [EPH] 惊蛰 1999 = 1999-03-06 08:57:39 BJT; birth = 1999-03-11 06:15 BJT
    # [HAND] 7037.4 min / 4320 min-per-year = 1.629 y (1 y 7 m 16 d in the 3-day=1-year convention)
    s = run(**CANON)["chart"]["dayun"]["start"]
    assert (s["years"], s["months"], s["days"]) == (1, 7, 16)


def test_canonical_element_weighted_formula():
    # [HAND] stems 己土 丁火 壬水 癸水 = 1 each; 卯×3 = 木 3.0; 戌(戊.6 辛.3 丁.1)
    w = run(**CANON)["chart"]["element_counts"]["weighted"]
    assert w == {"木": 3.0, "火": 1.1, "土": 1.6, "金": 0.3, "水": 2.0}


def test_canonical_heuristic_score_formula():
    # [HAND] 休 0 + roots 0 + 0.8×1 (癸劫财) − 0.5×2 (己官, 丁财) = −0.2
    assert run(**CANON)["chart"]["strength_factors"]["heuristic_score"] == -0.2


def test_canonical_combinations_are_reported_by_engine():
    inter = run(**CANON)["chart"]["natal_interactions"]
    details = {i["detail"] for i in inter}
    assert "丁壬合（化木）" in details
    assert any("卯戌合" in d or "戌卯合" in d for d in details)


# ------------------------------------------------------------ jieqi / year / month boundaries

def _sun_lon(d):
    import ephem
    s = ephem.Sun(d)
    return math.degrees(ephem.Ecliptic(ephem.Equatorial(s.g_ra, s.g_dec, epoch=d), epoch=d).lon)


def _term_utc(deg, near):
    import ephem
    f = lambda t: ((_sun_lon(ephem.Date(t)) - deg + 180) % 360) - 180
    a, b = float(ephem.Date(near)) - 20, float(ephem.Date(near)) + 20
    for _ in range(50):
        m = (a + b) / 2
        a, b = (a, m) if f(a) * f(m) <= 0 else (m, b)
    return ephem.Date((a + b) / 2).datetime().replace(tzinfo=timezone.utc)


@pytest.mark.parametrize("year", range(1950, 2031, 4))
def test_jie_times_within_one_minute_of_ephemeris(year):
    pytest.importorskip("ephem")
    bj = timezone(timedelta(hours=8))
    names = ["小寒", "立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪"]
    table = Solar.fromYmd(year, 6, 1).getLunar().getJieQiTable()
    pinyin = {"小寒": "XIAO_HAN", "立春": "LI_CHUN", "惊蛰": "JING_ZHE", "大雪": "DA_XUE"}
    for i, n in enumerate(names):
        cands = [v for k, v in table.items() if k in (n, pinyin.get(n)) and v.getYear() == year]
        if not cands:
            continue
        s = cands[0]
        lp = datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute(), s.getSecond(), tzinfo=bj)
        ref = _term_utc((285 + 30 * i) % 360, datetime(year, 1, 6) + timedelta(days=30.44 * i))
        assert abs((lp - ref).total_seconds()) < 60, (year, n, lp, ref)


@pytest.mark.parametrize("t,year_gz,month_gz", [
    # [EPH] 立春 2024 = 2024-02-04 15:26:56 UTC+7
    ("2024-02-04 15:20", "癸卯", "乙丑"),
    ("2024-02-04 15:35", "甲辰", "丙寅"),
    # [EPH] 惊蛰 2024 = 2024-03-05 09:22:38 UTC+7
    ("2024-03-05 09:15", "甲辰", "丙寅"),
    ("2024-03-05 09:30", "甲辰", "丁卯"),
])
def test_year_month_boundary_vietnam_time(t, year_gz, month_gz):
    y, m, *_ = run(birth_time=t)["chart"]["bazi"].split()
    assert (y, m) == (year_gz, month_gz)


# ------------------------------------------------------------ day / hour pillars

def _jdn_day(d):
    return JIAZI[(d.toordinal() + 1721425 + 49) % 60]


@pytest.mark.parametrize("d", [date(1900, 1, 31), date(1950, 6, 1), date(1975, 6, 13), date(1999, 3, 11),
                               date(2000, 1, 1), date(2024, 2, 29), date(2030, 12, 31)])
def test_day_pillar_matches_jdn(d):
    c = run(birth_time=f"{d.isoformat()} 12:00", timezone="Asia/Bangkok")["chart"]
    assert c["pillars"]["day"]["ganzhi"] == _jdn_day(d)


def test_late_zi_same_day():
    # [JDN] 1999-03-10 = 辛酉; [HAND] 夜子: hour stem from next day 壬 → 五鼠遁 庚子
    d, h = run(birth_time="1999-03-10 23:30", late_zi_rule="same_day")["chart"]["bazi"].split()[2:]
    assert (d, h) == ("辛酉", "庚子")


def test_late_zi_next_day():
    d, h = run(birth_time="1999-03-10 23:30", late_zi_rule="next_day")["chart"]["bazi"].split()[2:]
    assert (d, h) == ("壬戌", "庚子")


def test_ten_gods_match_lunar_python_table():
    for a in STEMS:
        for b in STEMS:
            assert B.ten_god(a, b) == LunarUtil.SHI_SHEN[a + b]


def test_twelve_stage_matches_lunar_python():
    for i in range(0, 3650, 37):
        s = Solar.fromYmdHms(1990, 1, 1, 12, 0, 0).next(i)
        ec = s.getLunar().getEightChar()
        assert B.twelve_stage(ec.getDayGan(), ec.getDayZhi()) == ec.getDayDiShi()


# ------------------------------------------------------------ true solar time / timezone

def test_true_solar_time_close_to_ephemeris():
    # [EPH] Hanoi 105.85E, 1970-06-15 12:30 at UTC+7 → apparent solar time 12:33:10
    o = run(birth_time="1970-06-15 12:30", timezone="Asia/Bangkok", longitude=105.85)
    tst = datetime.strptime(o["chart"]["times"]["true_solar_time"]["value"], "%Y-%m-%d %H:%M:%S")
    assert abs((tst - datetime(1970, 6, 15, 12, 33, 10)).total_seconds()) < 60


# AUDIT F2 (fixed): regional table in vn_calendar.py
@pytest.mark.parametrize("kw", [{"birth_region": "north"}, {"latitude": 21.03}])
def test_hanoi_1970_uses_utc7(kw):
    # North on +07 from 1967-08-08. 13:20 Hanoi civil → TST ≈ 13:23 → 未时 [EPH]
    o = run(birth_time="1970-06-15 13:20", timezone="Asia/Ho_Chi_Minh", longitude=105.85, **kw)
    assert o["chart"]["times"]["utc_offset_hours"] == 7.0
    assert o["chart"]["pillars"]["hour"]["branch"] == "未"


def test_saigon_1970_uses_utc8():
    o = run(birth_time="1970-06-15 13:20", timezone="Asia/Ho_Chi_Minh", birth_region="south")
    assert o["chart"]["times"]["utc_offset_hours"] == 8.0


def test_vietnam_1970_without_region_is_rejected():
    with pytest.raises(ValueError, match="birth_region"):
        run(birth_time="1970-06-15 13:20", timezone="Asia/Ho_Chi_Minh")


def test_vietnam_1980_needs_no_region():
    assert run(birth_time="1980-06-15 13:20")["chart"]["times"]["utc_offset_hours"] == 7.0


# ------------------------------------------------------------ lunar (âm lịch) input

# AUDIT F1 (fixed): lunar input uses the Vietnamese calendar for Vietnamese time zones
@pytest.mark.parametrize("lunar,solar", [
    ("2007-01-01", "2007-02-17"),  # [VNL] Tết Đinh Hợi in Vietnam; China = 2007-02-18
    ("1985-01-01", "1985-01-21"),  # [VNL] Tết Ất Sửu in Vietnam; China = 1985-02-20
])
def test_vietnamese_lunar_input(lunar, solar):
    o = run(birth_time=f"{lunar} 12:00", calendar_type="lunar")
    assert o["normalized_input"]["local_solar_time"].startswith(solar)


def test_lunar_input_where_calendars_agree():
    o = run(birth_time="1999-01-24 05:15", calendar_type="lunar")
    assert o["normalized_input"]["local_solar_time"] == "1999-03-11 05:15"


# ------------------------------------------------------------ strength heuristic (AUDIT F3: open, see STAGE1.md §2)

def _score(gz4):
    pillars = {k: B.pillar_detail(k, g, gz4[2][0]) for k, g in zip(B.PILLAR_KEYS, gz4)}
    return B.strength_factors(pillars, gz4[2][0], B.wangxiang(gz4[1][1]))["heuristic_score"]


@pytest.mark.xfail(strict=True, reason="AUDIT F3: branches only count as roots; 印 in branches adds nothing, "
                                       "食伤/财/官 in branches subtract nothing")
def test_branch_resource_raises_strength():
    canon = ["己卯", "丁卯", "壬戌", "癸卯"]          # two 卯 (伤官) on year/hour
    with_yin = ["己酉", "丁卯", "壬戌", "癸酉"]       # same stems, 酉 (正印) on year/hour
    assert _score(with_yin) > _score(canon)


@pytest.mark.xfail(strict=True, reason="AUDIT F3: 失令+无根+仅一比劫 should be clearly weak, score is −0.2")
def test_canonical_is_clearly_weak():
    # [HAND] 得令 no (卯 = 伤官, 休), 得地 no (no 亥子申辰丑), 得势 1/3 stems → 身弱 by 子平 three-criteria.
    assert run(**CANON)["chart"]["strength_factors"]["heuristic_score"] <= -1.0


# ------------------------------------------------------------ consistency with ziwei (shared calendar)

@pytest.mark.xfail(strict=True, reason="AUDIT F4: bazi defaults to same_day, ziwei to next_day for 23:00-24:00")
def test_late_zi_default_consistent_with_ziwei():
    import ziwei_cli as Z
    z = Z.build_output({"calendar_type": "solar", "birth_time": "1999-03-10 23:30", "gender": "男"})
    b = run(birth_time="1999-03-10 23:30")
    bazi_date = "1999-03-10" if b["normalized_input"]["late_zi_rule"] == "same_day" else "1999-03-11"
    assert z["calendar"]["chart_solar_date"] == bazi_date


# AUDIT F1 (fixed)
def test_ziwei_vietnamese_lunar_new_year_1985():
    import ziwei_cli as Z
    # [VNL] 1985-02-01 is month 1 day 12 of 乙丑 in Vietnam; in China it is still 甲子 month 12.
    z = Z.build_output({"calendar_type": "solar", "birth_time": "1985-02-01 12:00", "gender": "男"})
    assert (z["calendar"]["year_ganzhi"], z["calendar"]["lunar_month"], z["calendar"]["lunar_day"]) == ("乙丑", 1, 12)
