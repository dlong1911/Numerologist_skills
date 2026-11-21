import sys, json
from datetime import timezone, timedelta, date
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2]); sys.path.insert(0, sys.argv[3])
import ref
import bazi_cli as B
import ziwei_cli as Z

def run(**kw):
    p = {"calendar_type": "solar", "gender": "男", "timezone": "Asia/Ho_Chi_Minh"}; p.update(kw)
    return B.build_output(p)

BJ = timezone(timedelta(hours=8)); VN = timezone(timedelta(hours=7))
lc = ref.jie_times(2024)["立春"]
print("2024 立春 ephem VN", lc.astimezone(VN))
for t in ["2024-02-04 15:20", "2024-02-04 15:35"]:
    print(t, run(birth_time=t)["chart"]["bazi"])
for t in ["2024-03-05 10:15", "2024-03-05 10:30"]:
    print(t, run(birth_time=t)["chart"]["bazi"], ref.jie_times(2024)["惊蛰"].astimezone(VN))

print("--- 23h")
for rule in ["same_day", "next_day"]:
    o = run(birth_time="1999-03-10 23:30", late_zi_rule=rule)
    print(rule, o["chart"]["bazi"], o["chart"]["self_check"])
print("JDN day 1999-03-10", ref.day_ganzhi_index(date(1999, 3, 10)), "1999-03-11", ref.day_ganzhi_index(date(1999, 3, 11)))

print("--- lunar input")
for ly in ["2007-01-01", "1985-01-01", "1999-01-24"]:
    o = run(birth_time=ly + " 12:00", calendar_type="lunar")
    print(ly, "->", o["normalized_input"]["local_solar_time"], o["chart"]["bazi"])
months_vn = ref.lunisolar_months(1984, 2008, 7)
for d in [date(2007, 2, 17), date(1985, 1, 21), date(1999, 3, 11)]:
    print("VN lunar of", d, ref.solar_to_lunar(d, months_vn))
zi = Z.build_output({"calendar_type": "solar", "birth_time": "2007-02-17 12:00", "gender": "男"}) if hasattr(Z, "build_output") else None
if zi: print("ziwei 2007-02-17 lunar:", json.dumps(zi.get("normalized_input", zi), ensure_ascii=False)[:400])

print("--- Hanoi 1970")
for tz in ["Asia/Ho_Chi_Minh", "Asia/Bangkok"]:
    o = run(birth_time="1970-06-15 12:30", timezone=tz, longitude=105.85)
    print(tz, o["chart"]["bazi"], o["chart"]["times"]["true_solar_time"]["value"])
from datetime import datetime
utc = datetime(1970, 6, 15, 5, 30, tzinfo=timezone.utc)
print("ephem TST Hanoi for 12:30 at +07:", ref.true_solar_time(utc, 105.85))

print("--- no timezone")
o = B.build_output({"calendar_type": "solar", "gender": "男", "birth_time": "1999-03-11 05:15"})
print(o["chart"]["bazi"], o["warnings"][:1])
