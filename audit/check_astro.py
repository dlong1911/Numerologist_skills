import sys, random
from datetime import datetime, timedelta, timezone
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import astro_ref as R
import astro_cli as A

random.seed(1911)
cd = lambda a, b: (a - b + 180) % 360 - 180
LATS = [(21.03, 105.85), (10.78, 106.70), (12.67, 108.05), (-33.87, 151.21), (51.51, -0.13),
        (40.71, -74.01), (60.17, 24.94), (64.15, -21.94), (1.35, 103.82), (35.68, 139.65)]
worst = {}
retro_bad, house_worst, n = [], 0, 0
for i in range(24):
    utc = datetime(1950, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=random.randint(0, 80 * 365 * 86400))
    lat, lng = LATS[i % len(LATS)]
    o = A.build_output({"birth_datetime": utc.strftime("%Y-%m-%d %H:%M"), "timezone": "UTC",
                        "latitude": lat, "longitude": lng, "time_uncertainty_minutes": 0, "return_bodies": []})
    utc = datetime.strptime(o["normalized_input"]["birth_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    t = R.t_of(utc); pts = o["chart"]["points"]; n += 1
    for name in R.BODIES:
        d = abs(cd(pts[name]["longitude"], R.lon(name, t))) * 3600
        worst[name] = max(worst.get(name, (0,))[0], d), utc
        sp = R.speed(name, t)
        if abs(sp) > 1e-3 and (sp < 0) != pts[name]["retrograde"]:
            retro_bad.append((name, utc, sp, pts[name]["retrograde"]))
    asc, mc, _, _ = R.angles(t, lat, lng)
    for k, ref in (("Ascendant", asc), ("Medium_Coeli", mc)):
        d = abs(cd(pts[k]["longitude"], ref)) * 3600
        if d > worst.get(k, (0,))[0]: worst[k] = (d, utc, lat)
    for k, ref in (("Mean_North_Lunar_Node", R.mean_node(t)), ("True_North_Lunar_Node", R.true_node(t))):
        d = abs(cd(pts[k]["longitude"], ref)) * 3600
        if d > worst.get(k, (0,))[0]: worst[k] = (d, utc)
    pc = R.placidus(t, lat, lng)
    for h, c in zip(o["chart"]["houses"], pc):
        house_worst = max(house_worst, abs(cd(h["cusp_longitude"], c)) * 3600)
print("samples", n)
for k, v in worst.items():
    print(f"{k:24s} max err {v[0]:8.1f} arcsec  at {v[1]}")
print("Placidus cusps max err arcsec", round(house_worst, 1))
print("retrograde flag mismatches", retro_bad)
