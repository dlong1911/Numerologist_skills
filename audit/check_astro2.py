import sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import astro_ref as R
import astro_cli as A

def run(**kw):
    p = {"time_uncertainty_minutes": 0, "return_bodies": []}; p.update(kw)
    return A.build_output(p)

UTC = timezone.utc
print("--- Hanoi 1970 via city table")
o = run(birth_datetime="1970-06-15 13:20", city="ha noi")
print("engine utc", o["normalized_input"]["birth_utc"], "ASC", o["chart"]["angles"]["Ascendant"], "Moon", o["chart"]["points"]["Moon"]["label"])
t = R.t_of(datetime(1970, 6, 15, 6, 20, tzinfo=UTC))
asc, mc, *_ = R.angles(t, 21.0285, 105.8542)
print("correct (+07) ASC", A.lon_label(asc), "Moon", A.lon_label(R.lon("Moon", t)))

print("--- DST edge")
for tz, s in [("America/New_York", "2021-11-07 01:30"), ("America/New_York", "2021-03-14 02:30"), ("Europe/London", "2021-10-31 01:30")]:
    try:
        o = run(birth_datetime=s, timezone=tz, latitude=40.7, longitude=-74.0)
    except Exception as e:
        print(tz, s, "ERROR", type(e).__name__, str(e)[:90]); continue
    sun_ref = R.lon("Sun", R.t_of(datetime.strptime(o["normalized_input"]["birth_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)))
    asc_e = o["chart"]["points"]["Ascendant"]["longitude"]
    t = R.t_of(datetime.strptime(o["normalized_input"]["birth_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC))
    print(tz, s, "engine utc", o["normalized_input"]["birth_utc"], "ASC engine", round(asc_e, 2), "ASC@utc", round(R.angles(t, 40.7, -74.0)[0], 2),
          [c["check"] for c in o["self_check"] if not c["ok"]], o["warnings"])

print("--- cusp label rounding")
print(A.lon_label(359.995), "|", A.lon_label(29.9999), "| sign_of", A.sign_of(359.995))

print("--- Sun ingress Aries 2000 (ephem/USNO 2000-03-20 07:35 UTC)")
for hm in ["07:33", "07:37"]:
    o = run(birth_datetime=f"2000-03-20 {hm}", timezone="UTC", latitude=0, longitude=0)
    print(hm, o["chart"]["points"]["Sun"]["sign"], o["chart"]["points"]["Sun"]["label"])

print("--- high latitude")
for hs in ["placidus", "koch", "whole_sign"]:
    try:
        o = run(birth_datetime="1990-12-15 10:00", timezone="Europe/Oslo", latitude=69.65, longitude=18.96, house_system=hs)
        print(hs, "cusps", [h["label"] for h in o["chart"]["houses"]][:4], "ASC", o["chart"]["angles"]["Ascendant"], o["warnings"], [c["check"] for c in o["chart"] and o["self_check"] if not c["ok"]])
    except Exception as e:
        print(hs, "ERROR", type(e).__name__, str(e)[:200])

print("--- no birth time")
o = run(birth_datetime="1999-03-11", timezone="Asia/Ho_Chi_Minh", latitude=21.03, longitude=105.85)
print("assumed", o["normalized_input"]["birth_local"], "Moon", o["chart"]["points"]["Moon"]["label"], "ASC", o["chart"]["angles"]["Ascendant"], o["warnings"])
for h in (0, 12, 23):
    t = R.t_of(datetime(1999, 3, 11, h, 0, tzinfo=timezone(timedelta(hours=7))))
    print(" Moon at", h, "h:", A.lon_label(R.lon("Moon", t)))

print("--- sect whole_sign vs Sun altitude")
lat, lng = 21.03, 105.85
for m in range(0, 24 * 60, 4):
    loc = datetime(1999, 3, 11, tzinfo=timezone(timedelta(hours=7))) + timedelta(minutes=m)
    o = run(birth_datetime=loc.strftime("%Y-%m-%d %H:%M"), timezone="Asia/Ho_Chi_Minh", latitude=lat, longitude=lng, house_system="whole_sign")
    alt = R.sun_altitude(R.t_of(loc), lat, lng)
    true_sect = "day" if alt > 0 else "night"
    if o["chart"]["sect"] != true_sect:
        print("MISMATCH", loc.strftime("%H:%M"), "engine", o["chart"]["sect"], "Sun alt", round(alt, 2), "Sun", o["chart"]["points"]["Sun"]["label"], "ASC", o["chart"]["angles"]["Ascendant"])
        break
else:
    print("no mismatch")
