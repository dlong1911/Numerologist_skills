"""Reference ("golden") set for the web app's JS engines, produced by the Python engines.

Usage (Python >= 3.12, lunar_python, kerykeion 6.1.0):
    python audit/make_golden.py <astrology_skills dir> <numerology_skills dir> <out.json>

Cases (~300, seeded): random 1940-2025 births in Hà Nội / TP.HCM, births within minutes of a
节 (solar-term boundary), giờ Tý (23:xx / 00:xx), dates where the Vietnamese and Chinese lunar
calendars disagree, 1955-1975 births where North and South legal time differ, and births near
the odd-hour boundaries. Each case stores the user input exactly as the web form sends it and
the Python results in a normalised shape (branch indexes, Vietnamese star names).
"""
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AS, NU, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path[:0] = [str(ROOT / "bazi" / "scripts"), str(ROOT / "ziwei-doushu" / "scripts"),
                str(AS / "natal-astrology" / "scripts"), str(NU / "pythagorean-numerology" / "scripts")]

import bazi_cli as B          # noqa: E402
import ziwei_cli as Z         # noqa: E402
import astro_cli as A         # noqa: E402
import numerology_cli as N    # noqa: E402
import vn_calendar as V       # noqa: E402
from lunar_python import Solar  # noqa: E402

rng = random.Random(20261121)
PLACES = {"north": ("hanoi", 21.0285, 105.8542), "south": ("hcm", 10.7769, 106.7009)}
NAMES = ["Lê Duy Long", "Nguyễn Thị Thủy", "Trần Quốc Huy", "Phạm Ngọc Ánh", "Đặng Văn Đức", "Lý Mỹ Vy",
         "Hoàng Minh Tuấn", "Vũ Thị Hồng Nhung", "Bùi Quang Khải", "Đỗ Thanh Yến", "Ngô Gia Bảo", "Dương Thùy Linh"]
STAR_VI = {"紫微": "Tử Vi", "天机": "Thiên Cơ", "太阳": "Thái Dương", "武曲": "Vũ Khúc", "天同": "Thiên Đồng",
           "廉贞": "Liêm Trinh", "天府": "Thiên Phủ", "太阴": "Thái Âm", "贪狼": "Tham Lang", "巨门": "Cự Môn",
           "天相": "Thiên Tướng", "天梁": "Thiên Lương", "七杀": "Thất Sát", "破军": "Phá Quân"}
HOA_VI = {"化禄": "Lộc", "化权": "Quyền", "化科": "Khoa", "化忌": "Kỵ"}
BR = B.BRANCHES


def case(tag, local: datetime, region, gender=None):
    place, lat, lon = PLACES[region]
    return {"tag": tag, "input": {"name": rng.choice(NAMES), "gender": gender or rng.choice(["nam", "nu"]),
                                  "birthDate": local.strftime("%Y-%m-%d"), "birthTime": local.strftime("%H:%M"),
                                  "placeId": place, "latitude": lat, "longitude": lon, "region": region}}


def rand_dt(y0=1940, y1=2025):
    a, b = datetime(y0, 1, 1), datetime(y1, 12, 31, 23, 59)
    return a + timedelta(minutes=rng.randrange(int((b - a).total_seconds() // 60)))


cases = []
for _ in range(170):
    cases.append(case("random", rand_dt(), rng.choice(["north", "south"])))
# solar-term boundaries (± 2-20 min, in local legal time)
for _ in range(40):
    y = rng.randrange(1941, 2025)
    tbl = Solar.fromYmd(y, 6, 1).getLunar().getJieQiTable()
    name = rng.choice(["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"])
    s = tbl[name]
    bj = datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute())
    region = rng.choice(["north", "south"])
    try:
        off = V.vn_offset(bj, region)["hours"]
    except ValueError:
        continue
    local = bj + timedelta(hours=off - 8) + timedelta(minutes=rng.choice([-1, 1]) * rng.randrange(2, 21))
    cases.append(case(f"jie:{name}", local, region))
# giờ Tý
for _ in range(30):
    d = rand_dt()
    hm = rng.choice([(23, rng.randrange(0, 60)), (0, rng.randrange(0, 60))])
    cases.append(case("zi_hour", d.replace(hour=hm[0], minute=hm[1]), rng.choice(["north", "south"])))
# Vietnamese vs Chinese lunar calendar disagree
diff_days = []
d = date(1968, 1, 1)
while d < date(2025, 12, 31) and len(diff_days) < 400:
    for region in ("north", "south"):
        try:
            vn = V.vn_solar_to_lunar(d, region)
        except ValueError:
            continue
        lu = Solar.fromYmd(d.year, d.month, d.day).getLunar()
        if vn != (lu.getYear(), abs(lu.getMonth()), lu.getDay(), lu.getMonth() < 0):
            diff_days.append((d, region))
    d += timedelta(days=3)
for d, region in rng.sample(diff_days, min(30, len(diff_days))):
    cases.append(case("calendar_diff", datetime(d.year, d.month, d.day, rng.randrange(1, 23), rng.randrange(60)), region))
# Tết 1968 and the 1967-08-08 switch
for d in (date(1968, 1, 29), date(1968, 1, 30), date(1967, 8, 7), date(1967, 8, 9)):
    for region in ("north", "south"):
        cases.append(case("vn_1967_1968", datetime(d.year, d.month, d.day, 10, 30), region))
# 1955-1975 region-dependent legal time, same wall clock in both regions
for _ in range(10):
    t = rand_dt(1956, 1974)
    for region in ("north", "south"):
        cases.append(case("region_window", t, region, gender="nam"))
# near odd-hour boundaries
for _ in range(12):
    t = rand_dt()
    h = rng.choice(range(1, 23, 2))
    cases.append(case("hour_boundary", t.replace(hour=h, minute=rng.choice([0, 1, 2, 58, 59]) if h else 0), rng.choice(["north", "south"])))


def gz_list(x):
    return [x[k] for k in B.PILLAR_KEYS]


def run_case(c):
    i = c["input"]
    g_cn = "男" if i["gender"] == "nam" else "女"
    bt = f'{i["birthDate"]} {i["birthTime"]}'
    out = {}
    try:
        bz = B.build_output({"calendar_type": "solar", "birth_time": bt, "gender": g_cn, "timezone": "Asia/Ho_Chi_Minh",
                             "latitude": i["latitude"], "longitude": i["longitude"], "use_true_solar_time": True,
                             "query_years": [2026]})
        ch = bz["chart"]
        out["bazi"] = {
            "utc_offset_hours": ch["times"]["utc_offset_hours"],
            "pillars": [ch["pillars"][k]["ganzhi"] for k in B.PILLAR_KEYS],
            "ten_gods": [ch["pillars"][k]["stem_ten_god"] for k in B.PILLAR_KEYS],
            "element_weighted": ch["element_counts"]["weighted"],
            "dayun_direction": ch["dayun"]["direction"],
            "dayun_start": [ch["dayun"]["start"]["years"], ch["dayun"]["start"]["months"], ch["dayun"]["start"]["days"]],
            "dayun": [p["ganzhi"] for p in ch["dayun"]["pillars"][:8]],
            "dayun_start_year": ch["dayun"]["pillars"][0]["start_year"],
            "interactions": sorted(x["detail"] for x in ch["natal_interactions"]),
            "late_zi_flag": ch["late_zi"] is not None,
        }
    except Exception as e:  # noqa: BLE001
        out["bazi"] = {"error": str(e)}
    try:
        zw = Z.build_output({"calendar_type": "solar", "birth_time": bt, "gender": g_cn, "latitude": i["latitude"],
                             "query_year": 2026})
        cal, chz = zw["calendar"], zw["chart"]
        major = {}
        for p in chz["palaces"]:
            for s in p["major_stars"]:
                major[STAR_VI[s["name"]]] = BR.index(p["branch"])
        out["tuvi"] = {
            "late_zi_rule": "next_day",
            "late_zi_flag": zw["calendar"]["late_zi"] is not None,
            "lunar": [cal["lunar_year"], cal["lunar_month"], cal["lunar_day"], cal["is_leap_month"]],
            "year_ganzhi": cal["year_ganzhi"],
            "menh": BR.index(chz["ming_gong"]["branch"]),
            "than": next(BR.index(p["branch"]) for p in chz["palaces"] if p["is_shen_gong"]),
            "cuc": chz["wuxing_ju"]["number"],
            "major": major,
            "sihua": {STAR_VI.get(x["star"], x["star"]): HOA_VI[x["type"]] for x in chz["year_sihua"]},
            "tuan": [BR.index(b) for b in chz["xunkong"]],
            "triet": [BR.index(b) for b in chz["jielu"]],
            "no_major": sorted(BR.index(p["branch"]) for p in chz["palaces"] if p["no_major_star"]),
            "xiaoxian_2026": BR.index(zw["horoscope"]["xiaoxian"]["branch"]),
            "decadal_direction": chz["decadal_direction"],
        }
    except Exception as e:  # noqa: BLE001
        out["tuvi"] = {"error": str(e)}
    try:
        nu = N.build_output({"full_name": i["name"], "birth_date": i["birthDate"], "query_date": "2026-11-20"})
        cc = nu["core"]
        out["numerology"] = {k: cc[k]["value"] for k in ("life_path", "expression", "soul_urge", "personality",
                                                          "birthday", "maturity", "attitude")}
        out["numerology"]["life_path_note_33"] = "note" in cc["life_path"]
        out["numerology"]["personal_year"] = nu["cycles"]["personal_year"]["value"]
    except Exception as e:  # noqa: BLE001
        out["numerology"] = {"error": str(e)}
    try:
        ao = A.build_output({"birth_datetime": bt, "timezone": "Asia/Ho_Chi_Minh", "latitude": i["latitude"],
                             "longitude": i["longitude"], "time_uncertainty_minutes": 0, "return_bodies": []})
        pts = ao["chart"]["points"]
        out["astro"] = {
            "birth_utc": ao["normalized_input"]["birth_utc"],
            "lon": {k: pts[k]["longitude"] for k in A.PLANETS + ["Ascendant", "Medium_Coeli", "Mean_North_Lunar_Node"]},
            "retro": sorted(ao["chart"]["retrogrades"]),
            "cusps": [h["cusp_longitude"] for h in ao["chart"]["houses"]],
            "sect": ao["chart"]["sect"],
        }
    except Exception as e:  # noqa: BLE001
        out["astro"] = {"error": str(e)}
    return out


for c in cases:
    c["python"] = run_case(c)
meta = {"generator": "Numerologist_skills/audit/make_golden.py", "count": len(cases),
        "notes": ["bazi: Asia/Ho_Chi_Minh + vn_calendar North/South table, true solar time on, late_zi next_day (default)",
                  "tuvi: lunar_calendar vn, civil time, late_zi next_day (Python default)",
                  "numerology: phillips life path, y_rule vowel, query 2026-11-20",
                  "astro: kerykeion 6.1.0, Placidus, tropical; mean node listed for comparison with JS"]}
OUT.write_text(json.dumps({"meta": meta, "cases": cases}, ensure_ascii=False, indent=1), encoding="utf-8")
print("cases", len(cases), {t: sum(c["tag"].split(":")[0] == t for c in cases) for t in
                            ("random", "jie", "zi_hour", "calendar_diff", "vn_1967_1968", "region_window", "hour_boundary")})
print("errors", {k: sum("error" in c["python"][k] for c in cases) for k in ("bazi", "tuvi", "numerology", "astro")})
