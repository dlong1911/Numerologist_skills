import sys, random
from datetime import datetime, timedelta, timezone, date
sys.path.insert(0, sys.argv[1])
import ref, ephem
from lunar_python import Solar, Lunar
from lunar_python.util import LunarUtil

BJ = timezone(timedelta(hours=8))

# sanity: equinox 2000 vs ephem.next_equinox
print("equinox check", ref.term_time(0, ephem.Date("2000/3/20")), ephem.next_equinox("2000/1/1").datetime())

# 1) jie times: lunar_python vs ephem, 1950-2030
worst = (0, None)
diffs = []
for y in range(1950, 2031):
    jt = ref.jie_times(y)
    tbl = Solar.fromYmd(y, 6, 1).getLunar().getJieQiTable()
    for name, utc in jt.items():
        key = {"小寒": "XIAO_HAN", "大雪": "DA_XUE", "惊蛰": "惊蛰"}.get(name, name)
        s = None
        for k, v in tbl.items():
            if k == key and v.getYear() == y:
                s = v
        if s is None:
            continue
        lp = datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute(), s.getSecond(), tzinfo=BJ)
        d = (lp - utc).total_seconds() / 60
        diffs.append(d)
        if abs(d) > abs(worst[0]): worst = (d, (y, name, lp, utc.astimezone(BJ)))
print("jie count", len(diffs), "max |diff| min", round(worst[0], 2), worst[1])
print("mean abs", round(sum(abs(d) for d in diffs) / len(diffs), 2))

# 2) day pillar vs JDN formula
JIAZI = [LunarUtil.GAN[i % 10 + 1] + LunarUtil.ZHI[i % 12 + 1] for i in range(60)]
bad = 0
for _ in range(3000):
    d = date(1900, 1, 1) + timedelta(days=random.randint(0, 200 * 365))
    lp = Solar.fromYmdHms(d.year, d.month, d.day, 12, 0, 0).getLunar().getEightChar().getDay()
    if lp != JIAZI[ref.day_ganzhi_index(d)]: bad += 1
print("day pillar mismatches /3000:", bad, "canonical 1999-03-11 ->", JIAZI[ref.day_ganzhi_index(date(1999, 3, 11))])

# 3) canonical jie and dayun start
jt = ref.jie_times(1999)
print("1999 惊蛰 ephem BJT", jt["惊蛰"].astimezone(BJ), "清明", jt["清明"].astimezone(BJ))
birth = datetime(1999, 3, 11, 5, 15, tzinfo=timezone(timedelta(hours=7)))
mins = (birth - jt["惊蛰"]).total_seconds() / 60
yrs = mins / 4320
print("minutes since 惊蛰", round(mins, 1), "years", round(yrs, 4), "start date", birth + timedelta(days=yrs * 365.2422))

# 4) true solar time: NOAA EoT in code vs ephem
sys.path.insert(0, sys.argv[2])
import bazi_cli as B
worst = 0
for _ in range(400):
    d = datetime(1950, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=random.randint(0, 80 * 525600))
    lon = random.uniform(102, 110)
    ref_tst = ref.true_solar_time(d, lon)
    code_tst = (d + timedelta(hours=7)).replace(tzinfo=None) + timedelta(minutes=(lon - 105) * 4 + B.equation_of_time_minutes((d + timedelta(hours=7)).date()))
    worst = max(worst, abs((code_tst - ref_tst).total_seconds() / 60))
print("TST max err min", round(worst, 2))
