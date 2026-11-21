"""Independent references: ephem (VSOP87/ELP) for solar terms, new moons, true solar time."""
import math
from datetime import datetime, timedelta, timezone, date
import ephem

def sun_lon(d):
    s = ephem.Sun(d)
    return math.degrees(ephem.Ecliptic(ephem.Equatorial(s.g_ra, s.g_dec, epoch=d), epoch=d).lon)

def term_time(target_deg, near):
    """UTC datetime when apparent geocentric solar longitude == target_deg, searching near `near` (ephem.Date)."""
    lo, hi = ephem.Date(near - 20), ephem.Date(near + 20)
    f = lambda t: ((sun_lon(ephem.Date(t)) - target_deg + 180) % 360) - 180
    a, b = float(lo), float(hi)
    for _ in range(60):
        m = (a + b) / 2
        if f(a) * f(m) <= 0: b = m
        else: a = m
    return ephem.Date((a + b) / 2).datetime().replace(tzinfo=timezone.utc)

def jie_times(year):
    """12 节 for solar year `year` (小寒 .. 大雪), UTC. 节 longitudes: 285(小寒),315(立春),345,15,...,255."""
    out = {}
    names = ["小寒", "立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪"]
    for i, n in enumerate(names):
        deg = (285 + 30 * i) % 360
        approx = ephem.Date(datetime(year, 1, 6) + timedelta(days=30.44 * i))
        out[n] = term_time(deg, approx)
    return out

def true_solar_time(utc_dt, lon_deg):
    """Apparent solar time at longitude = 12h + local apparent hour angle of the Sun."""
    o = ephem.Observer(); o.lon = str(lon_deg); o.lat = "0"; o.date = ephem.Date(utc_dt.replace(tzinfo=None))
    o.pressure = 0
    s = ephem.Sun(o)
    ha = (float(o.sidereal_time()) - float(s.ra)) % (2 * math.pi)
    hours = (math.degrees(ha) / 15 + 12) % 24
    base = (utc_dt + timedelta(hours=lon_deg / 15)).replace(tzinfo=None)
    mean_h = base.hour + base.minute / 60 + base.second / 3600
    diff = ((hours - mean_h + 12) % 24) - 12
    return base + timedelta(hours=diff)

def jdn(d: date):
    return d.toordinal() + 1721425

def day_ganzhi_index(d: date):
    """60-cycle index (0 = 甲子). Anchor: 2000-01-01 = 戊午 (index 54); JDN 2451545."""
    return (jdn(d) + 49) % 60

# ---- lunisolar calendar at a given meridian (Hồ Ngọc Đức rules, used for Vietnam at UTC+7)
def lunisolar_months(y0, y1, tz_hours):
    tz = timezone(timedelta(hours=tz_hours))
    loc = lambda dt: dt.astimezone(tz).date()
    # new moons
    nm = []
    t = ephem.Date(datetime(y0 - 1, 10, 1))
    while t < ephem.Date(datetime(y1 + 1, 3, 1)):
        t = ephem.next_new_moon(t)
        nm.append(loc(t.datetime().replace(tzinfo=timezone.utc)))
        t = ephem.Date(t + 1)
    # zhongqi (multiples of 30 deg) dates
    zq = []
    for y in range(y0 - 1, y1 + 2):
        for k in range(12):
            deg = (270 + 30 * k) % 360  # 冬至 first
            approx = ephem.Date(datetime(y, 12, 21) + timedelta(days=30.44 * k))
            zq.append((deg, loc(term_time(deg, approx))))
    zq.sort(key=lambda x: x[1])
    months = []  # (start_date, lunar_year, month, leap)
    for y in range(y0 - 1, y1 + 1):
        ws1 = [d for deg, d in zq if deg == 270 and d.year == y][0]
        ws2 = [d for deg, d in zq if deg == 270 and d.year == y + 1][0]
        m11a = max(i for i, d in enumerate(nm) if d <= ws1)
        m11b = max(i for i, d in enumerate(nm) if d <= ws2)
        span = nm[m11a:m11b + 1]
        n = m11b - m11a
        leap_idx = None
        if n == 13:
            for i in range(1, 14):
                s, e = nm[m11a + i], nm[m11a + i + 1]
                if not any(s <= d < e for deg, d in zq if deg % 30 == 0 and deg in range(0, 360, 30)):
                    leap_idx = i; break
        mon = 11; ly = y
        for i in range(n):
            start = nm[m11a + i]
            if i == 0:
                months.append((start, y, 11, False)); continue
            if leap_idx is not None and i == leap_idx:
                months.append((start, ly, mon, True)); continue
            mon = mon % 12 + 1
            if mon == 1: ly = y + 1
            months.append((start, ly, mon, False))
    # dedupe and sort
    seen = {}
    for m in months: seen[m[0]] = m
    return [seen[k] for k in sorted(seen)]

def solar_to_lunar(d, months):
    m = max((x for x in months if x[0] <= d), key=lambda x: x[0])
    return (m[1], m[2], (d - m[0]).days + 1, m[3])
