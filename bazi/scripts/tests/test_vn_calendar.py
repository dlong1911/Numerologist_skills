"""vn_calendar.py: Vietnamese lunar calendar and North/South legal time (AUDIT F1, F2).

References:
  [VNL]  Chinese rules at the UTC+7 meridian, cross-checked against an independent PyEphem
         implementation 1901-2100 (audit/check2.py); disagreements only at 2072-12 and 2077-11
         where a new moon falls within seconds of midnight.
  [WIKI-VC] North Vietnam moved from UTC+8 to UTC+7 on 1967-08-08; Tết 1968 differed N/S.
  [TZ]   IANA tzdata Vietnam section (South: +8 1959-12-31 23:00 → 1975-06-13).
"""
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "bazi" / "scripts"))

import pytest
import vn_calendar as V


def test_copies_identical():
    a = (ROOT / "bazi" / "scripts" / "vn_calendar.py").read_bytes()
    b = (ROOT / "ziwei-doushu" / "scripts" / "vn_calendar.py").read_bytes()
    assert a == b


@pytest.mark.parametrize("lunar,solar", [((2007, 1, 1), date(2007, 2, 17)), ((1985, 1, 1), date(1985, 1, 21)),
                                         ((1999, 1, 24), date(1999, 3, 11))])
def test_post_1975_lunar_dates(lunar, solar):
    assert V.vn_lunar_to_solar(*lunar, False, None) == solar
    assert V.vn_solar_to_lunar(solar, None) == (*lunar, False)


def test_tet_1968_north_south():
    assert V.vn_lunar_to_solar(1968, 1, 1, False, "north") == date(1968, 1, 29)
    assert V.vn_lunar_to_solar(1968, 1, 1, False, "south") == date(1968, 1, 30)
    with pytest.raises(ValueError, match="birth_region"):
        V.vn_solar_to_lunar(date(1968, 1, 29), None)


def test_pre_1967_uses_chinese_calendar():
    from lunar_python import Solar
    d = date(1965, 2, 1)
    lu = Solar.fromYmd(1965, 2, 1).getLunar()
    assert V.vn_solar_to_lunar(d, None) == (lu.getYear(), abs(lu.getMonth()), lu.getDay(), lu.getMonth() < 0)


@pytest.mark.parametrize("when,region,hours", [
    (datetime(1970, 6, 15, 13), "north", 7.0), (datetime(1970, 6, 15, 13), "south", 8.0),
    (datetime(1957, 6, 15, 13), "south", 7.0), (datetime(1980, 1, 1), None, 7.0),
    (datetime(1944, 6, 1), None, 8.0), (datetime(1945, 6, 1), None, 9.0),
])
def test_offsets(when, region, hours):
    assert V.vn_offset(when, region)["hours"] == hours


def test_north_1955_1967_marked_uncertain():
    off = V.vn_offset(datetime(1962, 1, 1), "north")
    assert off["uncertain"] and off["hours"] == 7.0   # sources conflict; default +7 (user decision)


def test_region_from_latitude():
    assert V.resolve_region(None, 21.03) == "north" and V.resolve_region(None, 10.78) == "south"
    assert V.resolve_region("Miền Bắc") == "north"
