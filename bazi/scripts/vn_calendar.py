"""Vietnamese calendar helpers shared by the bazi and ziwei scripts.

Identical copies live in bazi/scripts/ and ziwei-doushu/scripts/ so each skill stays
self-contained; tests/test_vn_calendar.py checks the two files are byte-identical.

1. Vietnamese lunisolar calendar (âm lịch Việt Nam): the Chinese rules evaluated at the
   meridian of the region's legal time. North Vietnam moved from UTC+8 to UTC+7 on 1967-08-08
   (source [WIKI-VC]: en.wikipedia.org/wiki/Vietnamese_calendar, citing H. Aslaksen,
   "The Mathematics of the Chinese Calendar", pp 29-30), hence Tết 1968 fell on different days
   in North and South. South Vietnam stayed on UTC+8 until 1975-06-13 [TZ].

2. Civil UTC offset in Vietnam by region before reunification. Sources:
   [TZ]  IANA tzdata 'asia', Vietnam section (Paul Eggert 2024-01-14), quoting
         Trần Tiến Bình, "Lịch Việt Nam: thế kỷ XX-XXI (1901-2100)", NXB VHTT 2005, pp 49-50.
   [CB55] Ngô Đình Diệm, Dụ số 46 (1955-06-25), Công Báo VN No. 92, 1955-07-02, pp 1780-1781.
   [CB59] Sắc lệnh 362-TTP (1959-12-30), Công Báo VNCH 1960 part 1, p 62.
   [VNDQ] Võ Nguyên Giáp, Việt Nam Dân Quốc Công Báo No. 1 (1945-09-29), p 13.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta


VN_TZ = 7.0

# ---------------------------------------------------------------- lunisolar calendar
# Same rules as the Chinese calendar (month starts on the civil day of the new moon; month 11
# contains the winter solstice; in a 13-month year the first month without a principal term is
# leap), evaluated at a chosen meridian. New moons and solar terms come from lunar_python's
# 寿星 high-precision routines (ShouXingUtil.shuoHigh / qiHigh, Beijing time, ΔT applied).

J2000 = 2451545


def _S():
    from lunar_python.util.ShouXingUtil import ShouXingUtil  # lazy: offsets work without lunar_python
    return ShouXingUtil


def _shuo_day(k: int, tz: float) -> int:
    """Civil JDN (at UTC+tz) of the k-th new moon counted from 2000-01-06."""
    return math.floor(_S().shuoHigh(k * 2 * math.pi) + (tz - 8) / 24 + 0.5) + J2000


def _qi_day(n: int, tz: float) -> int:
    """Civil JDN of solar term n (15° steps, n = 0 at the 1999 vernal equinox)."""
    return math.floor(_S().qiHigh(n * math.pi / 12) + (tz - 8) / 24 + 0.5) + J2000


def _k_before(day: int, tz: float) -> int:
    k = math.floor((day - 2451551) / 29.5306)
    while _shuo_day(k + 1, tz) <= day:
        k += 1
    while _shuo_day(k, tz) > day:
        k -= 1
    return k


def _month11_k(year: int, tz: float) -> int:
    """New-moon index of lunar month 11 that contains the winter solstice of `year`."""
    return _k_before(_qi_day(18 + 24 * (year - 1999), tz), tz)


def _year_months(lunar_year: int, tz: float) -> list[tuple[int, int, bool]]:
    """[(start JDN, month, leap)] from month 11 of lunar_year-1 up to month 11 of lunar_year (excl.)."""
    ka, kb = _month11_k(lunar_year - 1, tz), _month11_k(lunar_year, tz)
    starts = [_shuo_day(k, tz) for k in range(ka, kb + 1)]
    leap_i = None
    if kb - ka == 13:
        zq = [_qi_day(n, tz) for n in range(18 + 24 * (lunar_year - 2000), 18 + 24 * (lunar_year - 1999) + 1, 2)]
        for i in range(1, 13):
            if not any(starts[i] <= d < starts[i + 1] for d in zq):
                leap_i = i
                break
    out, month = [], 11
    for i in range(kb - ka):
        if i == leap_i:
            out.append((starts[i], month, True))
            continue
        if i:
            month = month % 12 + 1
        out.append((starts[i], month, False))
    return out


def solar_to_lunar(d: date, tz: float = VN_TZ) -> tuple[int, int, int, bool]:
    """Returns (lunar_year, lunar_month, lunar_day, is_leap). tz=8 delegates to lunar_python
    (which also carries China's published pre-1960 corrections)."""
    if tz == 8:
        from lunar_python import Solar
        lu = Solar.fromYmd(d.year, d.month, d.day).getLunar()
        return lu.getYear(), abs(lu.getMonth()), lu.getDay(), lu.getMonth() < 0
    jdn = d.toordinal() + 1721425
    for ly in (d.year + 1, d.year):
        months = _year_months(ly, tz)
        if months[0][0] <= jdn:
            idx = max(i for i, m in enumerate(months) if m[0] <= jdn)
            first = next(i for i, m in enumerate(months) if m[1] == 1 and not m[2])
            start, month, leap = months[idx]
            return (ly if idx >= first else ly - 1), month, jdn - start + 1, leap
    raise AssertionError(d)


def leap_month_of(lunar_year: int, tz: float = VN_TZ) -> int:
    for start, month, leap in _year_months(lunar_year, tz) + _year_months(lunar_year + 1, tz)[:2]:
        if leap and solar_to_lunar(jd_to_date(start), tz)[0] == lunar_year:
            return month
    return 0


def jd_to_date(jd: int) -> date:
    return date.fromordinal(jd - 1721425)


def lunar_to_solar(lunar_year: int, lunar_month: int, lunar_day: int, is_leap: bool = False,
                   tz: float = VN_TZ) -> date:
    if tz == 8:
        from lunar_python import Lunar, LunarYear
        if is_leap and LunarYear.fromYear(lunar_year).getLeapMonth() != lunar_month:
            raise ValueError(f"âm lịch {lunar_year} không có tháng nhuận {lunar_month}")
        so = Lunar.fromYmd(lunar_year, -lunar_month if is_leap else lunar_month, lunar_day).getSolar()
        return date(so.getYear(), so.getMonth(), so.getDay())
    cands = _year_months(lunar_year, tz) + _year_months(lunar_year + 1, tz)
    for start, month, leap in cands:
        if month == lunar_month and leap == is_leap and solar_to_lunar(jd_to_date(start), tz)[0] == lunar_year:
            out = jd_to_date(start + lunar_day - 1)
            if solar_to_lunar(out, tz)[1:] != (lunar_month, lunar_day, is_leap):
                raise ValueError(f"ngày âm lịch không tồn tại: {lunar_day}/{lunar_month}/{lunar_year}")
            return out
    raise ValueError(f"âm lịch {lunar_year} không có tháng {'nhuận ' if is_leap else ''}{lunar_month}")


# ---------------------------------------------------------------- civil time by region

VN_ZONES = {"Asia/Ho_Chi_Minh", "Asia/Saigon"}
REGION_ALIASES = {"north": "north", "bac": "north", "bắc": "north", "mien bac": "north", "miền bắc": "north",
                  "south": "south", "nam": "south", "mien nam": "south", "miền nam": "south"}
PARTITION_LAT = 17.0  # vĩ tuyến 17 (sông Bến Hải), Hiệp định Genève 1954

NORTH_1967 = datetime(1967, 8, 8)
# (start of local wall time, UTC offset hours, sources, note); a row applies until the next one.
_COMMON = [
    (datetime(1906, 7, 1), 7 + 6.5 / 60 + 0.13 / 3600, "TZ", "PLMT (Phù Liễn)"),
    (datetime(1911, 5, 1), 7.0, "TZ", ""),
    (datetime(1942, 12, 31, 23), 8.0, "TZ", ""),
    (datetime(1945, 3, 14, 23), 9.0, "TZ", ""),
    (datetime(1945, 9, 2), 7.0, "TZ;VNDQ", ""),
    (datetime(1947, 4, 1), 8.0, "TZ", ""),
]
VN_OFFSETS = {
    "north": _COMMON + [
        (datetime(1954, 10, 10), 7.0, "TZ;GABRIEL",
         "UNCERTAIN: nguồn mâu thuẫn, mặc định UTC+7. [WIKI-VC] và [TZLIST11] cho rằng miền Bắc ở +8 tới 8/8/1967; "
         "sách Gabriel (Traité de l'heure dans le monde, 1991) ghi +7 từ 15/4/1955 tới 1/1/1960; "
         "tzdata gán miền Bắc vào Asia/Bangkok (+7) nhưng chỉ cam kết số liệu từ 1970. Giờ sinh có thể lệch 1 tiếng."),
        (NORTH_1967, 7.0, "WIKI-VC;TZLIST11", ""),
    ],
    "south": _COMMON + [
        (datetime(1955, 7, 1, 1), 7.0, "TZ;CB55", ""),
        (datetime(1959, 12, 31, 23), 8.0, "TZ;CB59", ""),
        (datetime(1975, 6, 13), 7.0, "TZ", ""),
    ],
}
SOURCES = {
    "TZ": "IANA tzdata 'asia', mục Vietnam (Eggert 2024), dẫn Trần Tiến Bình, Lịch Việt Nam thế kỷ XX-XXI, 2005, tr. 49-50",
    "CB55": "Dụ số 46 ngày 25/6/1955, Công Báo VN số 92 (2/7/1955), tr. 1780-1781",
    "CB59": "Sắc lệnh 362-TTP ngày 30/12/1959, Công Báo VNCH 1960 phần 1, tr. 62",
    "VNDQ": "Việt Nam Dân Quốc Công Báo số 1 (29/9/1945), tr. 13",
    "WIKI-VC": "en.wikipedia.org/wiki/Vietnamese_calendar, dẫn Aslaksen, The Mathematics of the Chinese Calendar, tr. 29-30",
    "TZLIST11": "Alois Treindl, tz mailing list 19/5/2011 (mm.icann.org/pipermail/tz/2011-May/008539.html)",
    "GABRIEL": "Gabriel, Traité de l'heure dans le monde (1991), theo Treindl, tz mailing list 18/5/2011 (008537)",
}


def resolve_region(region: str | None, latitude: float | None = None) -> str | None:
    if region not in (None, ""):
        key = str(region).strip().lower()
        if key not in REGION_ALIASES:
            raise ValueError("birth_region chỉ nhận 'north' (miền Bắc) hoặc 'south' (miền Nam)")
        return REGION_ALIASES[key]
    if latitude is not None:
        return "north" if float(latitude) > PARTITION_LAT else "south"
    return None


def _row(naive: datetime, region: str):
    return [r for r in VN_OFFSETS[region] if r[0] <= naive][-1]


def vn_offset(local: datetime, region: str | None) -> dict:
    """UTC offset of a Vietnamese wall-clock time. Raises when the regions differ and region is unknown."""
    naive = local.replace(tzinfo=None)
    if naive < _COMMON[0][0]:
        raise ValueError("trước 1/7/1906 Việt Nam dùng giờ địa phương (LMT): hãy truyền longitude và dùng giờ mặt trời thực")
    if region is None:
        n, s = _row(naive, "north"), _row(naive, "south")
        if n[1] != s[1]:
            raise ValueError(f"ngày {naive:%d/%m/%Y}: miền Bắc UTC+{n[1]:g}, miền Nam UTC+{s[1]:g}. "
                             "Cần birth_region='north' hoặc 'south' (hoặc latitude nơi sinh).")
        region = "south"
    row = _row(naive, region)
    return {"hours": row[1], "sources": [SOURCES[k] for k in row[2].split(";")], "note": row[3],
            "region": region, "uncertain": row[3].startswith("UNCERTAIN")}


def lunar_meridian(d: date, region: str) -> float:
    """UTC offset whose meridian defines the Vietnamese lunar calendar on date d in `region`."""
    naive = datetime(d.year, d.month, d.day, 12)
    return 8.0 if naive < NORTH_1967 else vn_offset(naive, region)["hours"]


def vn_solar_to_lunar(d: date, region: str | None) -> tuple[int, int, int, bool]:
    """Vietnamese lunar date. region is only required when North and South calendars disagree."""
    if region:
        return solar_to_lunar(d, lunar_meridian(d, region))
    n, s = (solar_to_lunar(d, lunar_meridian(d, r)) for r in ("north", "south"))
    if n != s:
        raise ValueError(f"ngày {d:%d/%m/%Y}: âm lịch miền Bắc {n[2]}/{n[1]}/{n[0]}, miền Nam {s[2]}/{s[1]}/{s[0]}. "
                         "Cần birth_region='north' hoặc 'south' (hoặc latitude nơi sinh).")
    return n


def vn_lunar_to_solar(y: int, m: int, day: int, leap: bool, region: str | None) -> date:
    found = set()
    for r in ([region] if region else ["north", "south"]):
        for tz in (7.0, 8.0):
            try:
                out = lunar_to_solar(y, m, day, leap, tz)
            except ValueError:
                continue
            if lunar_meridian(out, r) == tz:
                found.add(out)
    if not found:
        raise ValueError(f"ngày âm lịch Việt Nam không tồn tại: {day}/{m}/{y}{' (nhuận)' if leap else ''}")
    if len(found) > 1:
        raise ValueError(f"âm lịch {day}/{m}/{y} ứng với {sorted(found)} tùy miền. Cần birth_region='north' hoặc 'south'.")
    return found.pop()


def vn_tzinfo(local: datetime, region: str | None):
    """(fixed-offset tzinfo, offset record) for a Vietnamese wall-clock time."""
    from datetime import timezone
    off = vn_offset(local, region)
    return timezone(timedelta(hours=off["hours"])), off
