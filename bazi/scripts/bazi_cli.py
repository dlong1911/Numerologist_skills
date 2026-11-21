#!/usr/bin/env python3
"""四柱八字确定性排盘脚本。

四柱、藏干、十神、纳音、十二长生、旺相休囚死、五行计数、大运、起运、流年、
干支刑冲合害破等固定计算全部由本脚本完成；模型只读脚本输出做解读，不手排。

口径要点（详见 bazi/SKILL.md「脚本排盘口径」）：
- 年柱以立春为界、月柱以十二节为界，均按「出生瞬间」判断。lunar_python 的节气
  时刻是北京时间（UTC+8），所以先把出生时刻换算成北京时间（固定 UTC+8）再定年、月柱与起运，
  这样非中国时区（如越南 UTC+7）出生也能正确判断节气边界。
- 日柱、时柱按出生地的民用时间（或开启 use_true_solar_time 时的真太阳时）判断。
- 子时默认「夜子时」口径（late_zi_rule=same_day）：23:00-24:00 日柱仍取当日，
  时柱为子时（时干按次日五鼠遁，即 lunar_python sect=2）；next_day 则 23:00 起日柱换次日。
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lunar_python import Lunar, LunarYear, Solar
from lunar_python.util import LunarUtil

import vn_calendar as VN

DEFAULT_RULESET = "bazi-ziping-v1"
DEFAULT_TIMEZONE = "Asia/Shanghai"
JIEQI_TIMEZONE = "UTC+08:00"  # lunar_python 节气时刻所用的北京时间（固定 UTC+8，不含 1986-1991 夏令时）
JIEQI_TZ = timezone(timedelta(hours=8))

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
JIAZI = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]

STEM_ELEMENT = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
BRANCH_ELEMENT = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
ELEMENTS = ["木", "火", "土", "金", "水"]
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 地支藏干（本气、中气、余气），与 references/tiangan-dizhi.md 一致
HIDDEN_STEMS = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"], "卯": ["乙"],
    "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"], "午": ["丁", "己"], "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"], "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"],
}
HIDDEN_LABELS = ["本气", "中气", "余气"]
# 五行计数中藏干权重（简化口径，见 SKILL.md）
HIDDEN_WEIGHTS = {1: [1.0], 2: [0.7, 0.3], 3: [0.6, 0.3, 0.1]}

TWELVE_STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
CHANGSHENG_START = {"甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申", "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯"}

# 月令五行（四季月取土）
SEASON_ELEMENT = {"寅": "木", "卯": "木", "巳": "火", "午": "火", "申": "金", "酉": "金", "亥": "水", "子": "水", "辰": "土", "戌": "土", "丑": "土", "未": "土"}

STEM_COMBOS = {frozenset("甲己"): "土", frozenset("乙庚"): "金", frozenset("丙辛"): "水", frozenset("丁壬"): "木", frozenset("戊癸"): "火"}
STEM_CLASHES = [frozenset(p) for p in ("甲庚", "乙辛", "丙壬", "丁癸")]
LIU_CHONG = [frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")]
LIU_HE = {frozenset("子丑"): "土", frozenset("寅亥"): "木", frozenset("卯戌"): "火", frozenset("辰酉"): "金", frozenset("巳申"): "水", frozenset("午未"): "火土"}
SAN_HE = {"申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"}
SAN_HUI = {"寅卯辰": "木", "巳午未": "火", "申酉戌": "金", "亥子丑": "水"}
LIU_HAI = [frozenset(p) for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")]
LIU_PO = [frozenset(p) for p in ("子酉", "午卯", "申巳", "寅亥", "辰丑", "戌未")]
SELF_XING = {"辰", "午", "酉", "亥"}
XING_GROUPS = {"寅巳申": "无恩之刑", "丑戌未": "恃势之刑"}

GENDER_ALIASES = {"男": "男", "male": "男", "m": "男", "乾": "男", "女": "女", "female": "女", "f": "女", "坤": "女"}
LATE_ZI_RULES = {
    "same_day": "夜子时：23:00-24:00 日柱仍取当日，时柱取子时（时干按次日起）",
    "next_day": "23:00 起即换日：日柱取次日，时柱为次日子时",
}
YUN_SECTS = {
    2: "精确到分钟：出生至节令的时间差，4320 分钟（3 天）折 1 年，按比例折算月日时",
    1: "传统口径：按天数和时辰折算，3 天折 1 年、1 天折 4 个月、1 时辰折 10 天",
}
PILLAR_KEYS = ["year", "month", "day", "hour"]
PILLAR_NAMES = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}


# ---------------------------------------------------------------- 基础工具

def get_timezone(name: str):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == DEFAULT_TIMEZONE:
            return timezone(timedelta(hours=8), name=DEFAULT_TIMEZONE)
        if name.upper() == "UTC":
            return timezone.utc
        raise


def parse_datetime_string(value: str) -> dict[str, int]:
    normalized = value.strip().replace("T", " ").replace("/", "-").replace("年", "-").replace("月", "-").replace("日", " ")
    normalized = normalized.replace("时", ":").replace("點", ":").replace("点", ":").replace("分", "").replace("秒", "")
    parts = normalized.split()
    if not parts:
        raise ValueError("birth_time 不能为空")
    date_bits = [int(bit) for bit in parts[0].split("-") if bit]
    if len(date_bits) != 3:
        raise ValueError("日期格式需为 YYYY-MM-DD")
    if len(parts) < 2:
        raise ValueError("缺少出生时间：八字排盘需要出生时辰，请先向用户确认")
    time_bits = [int(bit) for bit in parts[1].split(":") if bit]
    if not time_bits:
        raise ValueError("出生时间格式需为 HH:MM")
    return {
        "year": date_bits[0], "month": date_bits[1], "day": date_bits[2],
        "hour": time_bits[0], "minute": time_bits[1] if len(time_bits) > 1 else 0,
    }


def ten_god(day_stem: str, other_stem: str) -> str:
    """十神：以日干为我，看他干。"""
    me, other = STEM_ELEMENT[day_stem], STEM_ELEMENT[other_stem]
    same_polarity = (STEMS.index(day_stem) % 2) == (STEMS.index(other_stem) % 2)
    if me == other:
        return "比肩" if same_polarity else "劫财"
    if GENERATES[me] == other:
        return "食神" if same_polarity else "伤官"
    if CONTROLS[me] == other:
        return "偏财" if same_polarity else "正财"
    if CONTROLS[other] == me:
        return "七杀" if same_polarity else "正官"
    if GENERATES[other] == me:
        return "偏印" if same_polarity else "正印"
    raise ValueError(f"无法计算十神 {day_stem}->{other_stem}")


def twelve_stage(stem: str, branch: str) -> str:
    """十二长生：阳干顺行、阴干逆行。"""
    start = BRANCHES.index(CHANGSHENG_START[stem])
    idx = BRANCHES.index(branch)
    step = (idx - start) % 12 if STEMS.index(stem) % 2 == 0 else (start - idx) % 12
    return TWELVE_STAGES[step]


def wangxiang(month_branch: str) -> dict[str, str]:
    """旺相休囚死：当令者旺，令生者相，生令者休，克令者囚，令克者死。"""
    season = SEASON_ELEMENT[month_branch]
    result = {}
    for el in ELEMENTS:
        if el == season:
            result[el] = "旺"
        elif GENERATES[season] == el:
            result[el] = "相"
        elif GENERATES[el] == season:
            result[el] = "休"
        elif CONTROLS[el] == season:
            result[el] = "囚"
        else:
            result[el] = "死"
    return result


def year_ganzhi(year: int) -> str:
    return JIAZI[(year - 4) % 60]


def equation_of_time_minutes(d: date) -> float:
    """均时差（分钟），NOAA 近似公式，误差约 ±0.5 分钟。"""
    gamma = 2 * math.pi / 365 * (d.timetuple().tm_yday - 1)
    return 229.18 * (
        0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma)
    )


# ---------------------------------------------------------------- 输入规整

@dataclass
class BirthInfo:
    calendar_type: str
    local_dt: datetime  # 出生地民用时间（带时区）
    gender: str
    timezone: str
    longitude: float | None
    use_true_solar_time: bool
    late_zi_rule: str
    yun_sect: int
    query_years: list[int]
    original_input: Any
    warnings: list[str]
    lunar_calendar: str = "cn"
    birth_region: str | None = None
    utc_offset_source: dict | None = None


def normalize_input(payload: dict[str, Any]) -> BirthInfo:
    warnings: list[str] = []
    location = payload.get("location") or {}
    tz_name = str(payload.get("timezone") or location.get("timezone") or DEFAULT_TIMEZONE).strip()
    try:
        tz = get_timezone(tz_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"无法识别时区 {tz_name}: {exc}") from exc
    if not (payload.get("timezone") or location.get("timezone")):
        warnings.append(f"未提供时区，按默认 {DEFAULT_TIMEZONE} 计算；海外出生请补充 timezone。")

    calendar_type = str(payload.get("calendar_type") or "solar").strip().lower()
    raw_input = payload.get("birth_time")
    if raw_input in (None, ""):
        raise ValueError("缺少 birth_time")
    if isinstance(raw_input, dict):
        if "hour" not in raw_input:
            raise ValueError("缺少出生时间：八字排盘需要出生时辰，请先向用户确认")
        raw = {k: int(raw_input.get(k, 0)) for k in ("year", "month", "day", "hour", "minute")}
    else:
        raw = parse_datetime_string(str(raw_input))
    if not (0 <= raw["hour"] <= 23 and 0 <= raw["minute"] <= 59):
        raise ValueError("出生时间超出范围")

    is_vn = tz_name in VN.VN_ZONES
    region = VN.resolve_region(payload.get("birth_region"), payload.get("latitude", location.get("latitude")))
    lunar_calendar = str(payload.get("lunar_calendar") or ("vn" if is_vn else "cn")).strip().lower()
    if lunar_calendar not in ("vn", "cn"):
        raise ValueError("lunar_calendar 只支持 vn / cn")
    if calendar_type == "solar":
        local_date = date(raw["year"], raw["month"], raw["day"])
    elif calendar_type == "lunar":
        is_leap = bool(payload.get("is_leap_month", False))
        if lunar_calendar == "vn":
            local_date = VN.vn_lunar_to_solar(raw["year"], raw["month"], raw["day"], is_leap, region)
        else:
            if is_leap and LunarYear.fromYear(raw["year"]).getLeapMonth() != raw["month"]:
                raise ValueError(f"农历 {raw['year']} 年没有闰{raw['month']}月")
            solar = Lunar.fromYmd(raw["year"], -raw["month"] if is_leap else raw["month"], raw["day"]).getSolar()
            local_date = date(solar.getYear(), solar.getMonth(), solar.getDay())
    else:
        raise ValueError(f"不支持的 calendar_type: {calendar_type}（只支持 solar / lunar）")
    naive = datetime(local_date.year, local_date.month, local_date.day, raw["hour"], raw["minute"])
    offset_source = None
    if is_vn:
        # tzdata's Asia/Ho_Chi_Minh is South Vietnam only; use the regional table (vn_calendar.py)
        tz, offset_source = VN.vn_tzinfo(naive, region)
        if offset_source["uncertain"]:
            warnings.append(f"Múi giờ {naive:%d/%m/%Y} chưa chắc chắn (UTC+{offset_source['hours']:g}): {offset_source['note']}")
    local_dt = naive.replace(tzinfo=tz)

    gender = GENDER_ALIASES.get(str(payload.get("gender") or "").strip().lower())
    if gender is None:
        raise ValueError("缺少或无法识别 gender（男/女）：性别决定大运顺逆，请先向用户确认")

    longitude = payload.get("longitude", location.get("longitude"))
    longitude = float(longitude) if longitude not in (None, "") else None
    use_tst = bool(payload.get("use_true_solar_time", longitude is not None))
    if use_tst and longitude is None:
        raise ValueError("use_true_solar_time=true 时必须提供 longitude（出生地经度，东经为正）")
    if longitude is not None and not -180 <= longitude <= 180:
        raise ValueError("longitude 超出范围")

    late_zi_rule = str(payload.get("late_zi_rule") or "same_day").strip()
    if late_zi_rule not in LATE_ZI_RULES:
        raise ValueError(f"late_zi_rule 只支持 {list(LATE_ZI_RULES)}")
    yun_sect = int(payload.get("yun_sect") or 2)
    if yun_sect not in YUN_SECTS:
        raise ValueError("yun_sect 只支持 1 或 2")

    query_years = payload.get("query_years")
    if query_years is None and payload.get("query_year") is not None:
        query_years = [payload["query_year"]]
    query_years = [int(y) for y in (query_years or [])]

    return BirthInfo(
        calendar_type=calendar_type, local_dt=local_dt, gender=gender, timezone=tz_name,
        longitude=longitude, use_true_solar_time=use_tst, late_zi_rule=late_zi_rule,
        yun_sect=yun_sect, query_years=query_years, original_input=raw_input, warnings=warnings,
        lunar_calendar=lunar_calendar, birth_region=region, utc_offset_source=offset_source,
    )


# ---------------------------------------------------------------- 排盘

def solar_from_naive(dt: datetime) -> Solar:
    return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def compute_times(info: BirthInfo) -> dict[str, Any]:
    beijing_dt = info.local_dt.astimezone(JIEQI_TZ)
    offset_hours = info.local_dt.utcoffset().total_seconds() / 3600
    result: dict[str, Any] = {
        "local_civil_time": info.local_dt.strftime("%Y-%m-%d %H:%M"),
        "utc_offset_hours": offset_hours,
        "beijing_time": beijing_dt.strftime("%Y-%m-%d %H:%M"),
        "beijing_dt": beijing_dt.replace(tzinfo=None),
    }
    chart_dt = info.local_dt.replace(tzinfo=None)
    if info.use_true_solar_time:
        meridian = offset_hours * 15
        lon_corr = (info.longitude - meridian) * 4
        eot = equation_of_time_minutes(info.local_dt.date())
        # 夏令时也包含在 utcoffset 中，经度校正以「时区子午线」为基准即可抵消
        chart_dt = chart_dt + timedelta(minutes=lon_corr + eot)
        result["true_solar_time"] = {
            "longitude": info.longitude,
            "zone_meridian": meridian,
            "longitude_correction_minutes": round(lon_corr, 2),
            "equation_of_time_minutes": round(eot, 2),
            "total_correction_minutes": round(lon_corr + eot, 2),
            "value": chart_dt.strftime("%Y-%m-%d %H:%M:%S"),
        }
    result["chart_time"] = chart_dt.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    result["chart_dt"] = chart_dt.replace(microsecond=0)
    return result


def find_jie_bounds(beijing_dt: datetime) -> dict[str, Any]:
    """出生瞬间（北京时间）前后最近的「节」。"""
    lunar = solar_from_naive(beijing_dt).getLunar()
    prev_jie = lunar.getPrevJie(False)
    next_jie = lunar.getNextJie(False)

    def to_dt(s: Solar) -> datetime:
        return datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute(), s.getSecond())

    prev_dt, next_dt = to_dt(prev_jie.getSolar()), to_dt(next_jie.getSolar())
    return {
        "prev": {"name": prev_jie.getName(), "beijing_time": prev_dt.strftime("%Y-%m-%d %H:%M:%S"),
                 "hours_since": round((beijing_dt - prev_dt).total_seconds() / 3600, 2)},
        "next": {"name": next_jie.getName(), "beijing_time": next_dt.strftime("%Y-%m-%d %H:%M:%S"),
                 "hours_until": round((next_dt - beijing_dt).total_seconds() / 3600, 2)},
    }


def pillar_detail(key: str, ganzhi: str, day_stem: str) -> dict[str, Any]:
    stem, branch = ganzhi[0], ganzhi[1]
    hidden = HIDDEN_STEMS[branch]
    return {
        "name": PILLAR_NAMES.get(key, key),
        "ganzhi": ganzhi,
        "stem": stem,
        "branch": branch,
        "stem_element": STEM_ELEMENT[stem],
        "branch_element": BRANCH_ELEMENT[branch],
        "stem_ten_god": "日主" if key == "day" else ten_god(day_stem, stem),
        "hidden_stems": [
            {"stem": h, "type": HIDDEN_LABELS[i], "element": STEM_ELEMENT[h], "ten_god": ten_god(day_stem, h)}
            for i, h in enumerate(hidden)
        ],
        "nayin": LunarUtil.NAYIN[ganzhi],
        "day_master_stage": twelve_stage(day_stem, branch),
        "self_stage": twelve_stage(stem, branch),
    }


def element_counts(pillars: dict[str, dict[str, Any]]) -> dict[str, Any]:
    visible = {el: 0 for el in ELEMENTS}
    weighted = {el: 0.0 for el in ELEMENTS}
    for p in pillars.values():
        visible[p["stem_element"]] += 1
        visible[p["branch_element"]] += 1
        weighted[p["stem_element"]] += 1.0
        hidden = HIDDEN_STEMS[p["branch"]]
        for h, w in zip(hidden, HIDDEN_WEIGHTS[len(hidden)]):
            weighted[STEM_ELEMENT[h]] += w
    return {
        "visible": visible,
        "weighted": {k: round(v, 2) for k, v in weighted.items()},
        "method": "visible：4 天干 + 4 地支本气五行各计 1；weighted：天干各计 1，每个地支总计 1 分摊给藏干"
                  "（单藏 1.0；两藏 0.7/0.3；三藏 0.6/0.3/0.1）。仅为统计口径，不等于旺衰结论。",
    }


def strength_factors(pillars: dict[str, dict[str, Any]], day_stem: str, wx: dict[str, str]) -> dict[str, Any]:
    dm_el = STEM_ELEMENT[day_stem]
    support_gods = {"比肩", "劫财", "正印", "偏印"}
    month_branch = pillars["month"]["branch"]
    roots = []
    for key, p in pillars.items():
        for h in p["hidden_stems"]:
            if STEM_ELEMENT[h["stem"]] == dm_el:
                roots.append({"pillar": PILLAR_NAMES[key], "branch": p["branch"], "stem": h["stem"], "type": h["type"]})
    visible_support = [PILLAR_NAMES[k] for k, p in pillars.items() if k != "day" and p["stem_ten_god"] in support_gods]
    # 启发式分数：仅供参考，不是旺衰判词
    score = 0.0
    score += {"旺": 2.0, "相": 1.5, "休": 0.0, "囚": -1.0, "死": -1.5}[wx[dm_el]]
    score += sum({"本气": 1.0, "中气": 0.5, "余气": 0.3}[r["type"]] for r in roots)
    score += 0.8 * len(visible_support)
    score -= 0.5 * sum(1 for k, p in pillars.items() if k != "day" and p["stem_ten_god"] not in support_gods)
    return {
        "day_master": day_stem,
        "day_master_element": dm_el,
        "month_command": {"month_branch": month_branch, "season_element": SEASON_ELEMENT[month_branch],
                          "day_master_state": wx[dm_el],
                          "day_master_stage_in_month": pillars["month"]["day_master_stage"]},
        "roots": roots,
        "visible_support_stems": visible_support,
        "heuristic_score": round(score, 2),
        "heuristic_note": "启发式分数（得令 + 通根 + 透出比印 − 透出克泄耗），>0 偏强、<0 偏弱，仅作参考；"
                          "身强身弱、格局与喜用必须结合原局由解读者判断。",
    }


# ---------------------------------------------------------------- 干支关系

def detect_interactions(items: list[dict[str, str]], require_any: set[str] | None = None) -> list[dict[str, Any]]:
    """items: [{"label": "年柱", "ganzhi": "己卯"}, ...]；require_any 非空时只返回涉及这些 label 的关系。"""
    found: list[dict[str, Any]] = []

    def add(kind: str, labels: list[str], detail: str, extra: dict[str, Any] | None = None):
        if require_any and not (set(labels) & require_any):
            return
        entry = {"type": kind, "between": labels, "detail": detail}
        if extra:
            entry.update(extra)
        found.append(entry)

    for a, b in combinations(items, 2):
        sa, sb, ba, bb = a["ganzhi"][0], b["ganzhi"][0], a["ganzhi"][1], b["ganzhi"][1]
        labels = [a["label"], b["label"]]
        pair_s, pair_b = frozenset((sa, sb)), frozenset((ba, bb))
        if pair_s in STEM_COMBOS and sa != sb:
            add("天干五合", labels, f"{sa}{sb}合（化{STEM_COMBOS[pair_s]}）")
        if pair_s in STEM_CLASHES:
            add("天干相冲", labels, f"{sa}{sb}冲")
        if pair_b in LIU_CHONG:
            add("六冲", labels, f"{ba}{bb}冲")
        if pair_b in LIU_HE and ba != bb:
            add("六合", labels, f"{ba}{bb}合（{LIU_HE[pair_b]}）")
        if pair_b in LIU_HAI:
            add("六害", labels, f"{ba}{bb}害")
        if pair_b in LIU_PO:
            add("六破", labels, f"{ba}{bb}破")
        if pair_b == frozenset("子卯"):
            add("相刑", labels, "子卯刑（无礼之刑）")
        for group, name in XING_GROUPS.items():
            if ba != bb and ba in group and bb in group:
                add("相刑", labels, f"{ba}{bb}刑（{group}{name}，两字）")
        if ba == bb and ba in SELF_XING:
            add("自刑", labels, f"{ba}{bb}自刑")
        for group, el in SAN_HE.items():
            if ba != bb and ba in group and bb in group:
                kind = "半合" if group[1] in (ba, bb) else "拱合"
                add(kind, labels, f"{ba}{bb}{kind}（{group}{el}局缺{(set(group) - {ba, bb}).pop()}）")
        if a["ganzhi"] == b["ganzhi"]:
            add("伏吟", labels, f"{a['ganzhi']}与{b['ganzhi']}干支相同")
        elif pair_s in STEM_CLASHES and pair_b in LIU_CHONG:
            add("反吟", labels, f"{a['ganzhi']}与{b['ganzhi']}天克地冲")
        elif pair_b in LIU_CHONG and CONTROLS.get(STEM_ELEMENT[sa]) == STEM_ELEMENT[sb] or \
                pair_b in LIU_CHONG and CONTROLS.get(STEM_ELEMENT[sb]) == STEM_ELEMENT[sa]:
            add("天克地冲", labels, f"{a['ganzhi']}与{b['ganzhi']}天干相克、地支相冲")

    for group_map, kind in ((SAN_HE, "三合"), (SAN_HUI, "三会")):
        for group, el in group_map.items():
            members = {ch: [it["label"] for it in items if it["ganzhi"][1] == ch] for ch in group}
            if all(members.values()):
                labels = sorted({l for ls in members.values() for l in ls}, key=lambda l: [it["label"] for it in items].index(l))
                add(kind, labels, f"{group}{kind}{el}局" if kind == "三合" else f"{group}三会{el}方")
    for group, name in XING_GROUPS.items():
        members = {ch: [it["label"] for it in items if it["ganzhi"][1] == ch] for ch in group}
        if all(members.values()):
            labels = sorted({l for ls in members.values() for l in ls}, key=lambda l: [it["label"] for it in items].index(l))
            add("三刑", labels, f"{group}三刑（{name}）")
    return found


# ---------------------------------------------------------------- 主流程

def build_chart(info: BirthInfo) -> dict[str, Any]:
    warnings = list(info.warnings)
    times = compute_times(info)
    sect = 2 if info.late_zi_rule == "same_day" else 1

    # 年、月柱：按北京时间判断节气边界
    bj_ec = solar_from_naive(times["beijing_dt"]).getLunar().getEightChar()
    bj_ec.setSect(sect)
    # 日、时柱：按出生地（真太阳）时间
    local_ec = solar_from_naive(times["chart_dt"]).getLunar().getEightChar()
    local_ec.setSect(sect)

    gz = {"year": bj_ec.getYear(), "month": bj_ec.getMonth(), "day": local_ec.getDay(), "hour": local_ec.getTime()}
    day_stem = gz["day"][0]
    pillars = {k: pillar_detail(k, gz[k], day_stem) for k in PILLAR_KEYS}
    wx = wangxiang(gz["month"][1])

    # 大运 / 起运（以北京时间瞬间相对节气计算）
    yun = bj_ec.getYun(1 if info.gender == "男" else 0, info.yun_sect)
    start_solar = yun.getStartSolar()
    start_dt = datetime(start_solar.getYear(), start_solar.getMonth(), start_solar.getDay(),
                        start_solar.getHour(), start_solar.getMinute())
    birth_year = info.local_dt.year
    dayun_list = []
    for dy in yun.getDaYun(10)[1:]:
        g = dy.getGanZhi()
        idx = dy.getIndex()
        approx_start = start_dt.replace(year=start_dt.year + 10 * (idx - 1)) if not (start_dt.month == 2 and start_dt.day == 29) \
            else start_dt + timedelta(days=round(365.2425 * 10 * (idx - 1)))
        dayun_list.append({
            "index": idx,
            "ganzhi": g,
            "stem_ten_god": ten_god(day_stem, g[0]),
            "branch_main_ten_god": ten_god(day_stem, HIDDEN_STEMS[g[1]][0]),
            "nayin": LunarUtil.NAYIN[g],
            "day_master_stage": twelve_stage(day_stem, g[1]),
            "start_year": dy.getStartYear(),
            "end_year": dy.getEndYear(),
            "start_age_xu": dy.getStartAge(),
            "end_age_xu": dy.getEndAge(),
            "start_date_approx": approx_start.strftime("%Y-%m-%d"),
        })

    year_stem_yang = STEMS.index(gz["year"][0]) % 2 == 0
    forward_expected = (year_stem_yang and info.gender == "男") or (not year_stem_yang and info.gender == "女")

    natal_items = [{"label": PILLAR_NAMES[k], "ganzhi": gz[k]} for k in PILLAR_KEYS]

    liunian = []
    for y in info.query_years:
        ln = year_ganzhi(y)
        current = None
        for d in dayun_list:
            if d["start_year"] <= y <= d["end_year"]:
                current = d
        items = list(natal_items)
        dynamic = {"流年"}
        if current:
            items.append({"label": "大运", "ganzhi": current["ganzhi"]})
            dynamic.add("大运")
        items.append({"label": "流年", "ganzhi": ln})
        inter = detect_interactions(items, require_any=dynamic)
        if current and current["ganzhi"] == ln:
            inter.append({"type": "岁运并临", "between": ["大运", "流年"], "detail": f"大运与流年同为{ln}"})
        liunian.append({
            "year": y,
            "ganzhi": ln,
            "age_xu": y - birth_year + 1,
            "stem_ten_god": ten_god(day_stem, ln[0]),
            "branch_hidden_ten_gods": [{"stem": h, "ten_god": ten_god(day_stem, h)} for h in HIDDEN_STEMS[ln[1]]],
            "nayin": LunarUtil.NAYIN[ln],
            "day_master_stage": twelve_stage(day_stem, ln[1]),
            "dayun": current["ganzhi"] if current else "童限（未起运）",
            "interactions": inter,
        })

    # 自检
    month_start_stem = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚", "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
    hour_start_stem = {"甲": "甲", "己": "甲", "乙": "丙", "庚": "丙", "丙": "戊", "辛": "戊", "丁": "庚", "壬": "庚", "戊": "壬", "癸": "壬"}
    exp_month_stem = STEMS[(STEMS.index(month_start_stem[gz["year"][0]]) + (BRANCHES.index(gz["month"][1]) - 2) % 12) % 10]
    hour_base_day = day_stem
    chart_dt = times["chart_dt"]
    if chart_dt.hour == 23 and info.late_zi_rule == "same_day":
        hour_base_day = STEMS[(STEMS.index(day_stem) + 1) % 10]  # 夜子时按次日起时干
    exp_hour_stem = STEMS[(STEMS.index(hour_start_stem[hour_base_day]) + BRANCHES.index(gz["hour"][1])) % 10]
    exp_hour_branch = BRANCHES[((chart_dt.hour + 1) // 2) % 12]
    self_check = {
        "pillars_valid_jiazi": all(g in JIAZI for g in gz.values()),
        "month_stem_by_wuhu_dun": exp_month_stem == gz["month"][0],
        "hour_stem_by_wushu_dun": exp_hour_stem == gz["hour"][0],
        "hour_branch_matches_chart_time": exp_hour_branch == gz["hour"][1],
        "dayun_direction_matches_rule": forward_expected == yun.isForward(),
    }
    if not all(self_check.values()):
        warnings.append(f"自检未通过：{[k for k, v in self_check.items() if not v]}，请勿使用本盘并反馈问题。")

    # 边界提醒
    jie = find_jie_bounds(times["beijing_dt"])
    if jie["prev"]["hours_since"] < 24 or jie["next"]["hours_until"] < 24:
        warnings.append(f"出生时刻距离节令（{jie['prev']['name']}/{jie['next']['name']}）不足 24 小时，"
                        "月柱（立春时还有年柱）对出生时间很敏感，请确认时间与时区。")
    minutes_in_day = chart_dt.hour * 60 + chart_dt.minute + chart_dt.second / 60
    nearest_boundary = min(abs(minutes_in_day - (h * 60)) for h in range(-1, 26, 2))
    if nearest_boundary <= 15:
        warnings.append(f"排盘时间 {chart_dt.strftime('%H:%M')} 距时辰交界不足 15 分钟，建议同时排相邻时辰对比。")
    if chart_dt.hour == 23 or chart_dt.hour == 0:
        warnings.append(f"出生在子时，采用口径：{LATE_ZI_RULES[info.late_zi_rule]}。")
    if info.local_dt.dst():
        warnings.append(f"出生时刻处于夏令时（{info.timezone}），已按实际 UTC 偏移换算节气时刻与真太阳时。")
    if times["utc_offset_hours"] != 8:
        warnings.append("出生地非 UTC+8：年、月柱与起运已换算为北京时间判断节气，日、时柱按出生地时间。")
    if not info.use_true_solar_time:
        warnings.append("未启用真太阳时；如需校正请传 longitude（出生地经度）。")

    return {
        "times": {k: v for k, v in times.items() if not k.endswith("_dt")},
        "jie_bounds": jie,
        "pillars": pillars,
        "bazi": " ".join(gz[k] for k in PILLAR_KEYS),
        "day_master": {"stem": day_stem, "element": STEM_ELEMENT[day_stem],
                       "polarity": "阳" if STEMS.index(day_stem) % 2 == 0 else "阴"},
        "xun_kong": {"day": local_ec.getDayXunKong(),
                     "year": bj_ec.getYearXunKong()},
        "wangxiang_xiuqiu": {"month_branch": gz["month"][1], "states": wx},
        "element_counts": element_counts(pillars),
        "strength_factors": strength_factors(pillars, day_stem, wx),
        "natal_interactions": detect_interactions(natal_items),
        "dayun": {
            "direction": "顺排" if yun.isForward() else "逆排",
            "start": {"years": yun.getStartYear(), "months": yun.getStartMonth(), "days": yun.getStartDay(),
                      "hours": yun.getStartHour() if info.yun_sect == 2 else 0,
                      "start_date": start_dt.strftime("%Y-%m-%d %H:%M"),
                      "method": YUN_SECTS[info.yun_sect]},
            "pillars": dayun_list,
        },
        "liunian": liunian,
        "self_check": self_check,
        "warnings": warnings,
    }


def build_output(payload: dict[str, Any]) -> dict[str, Any]:
    info = normalize_input(payload)
    chart = build_chart(info)
    warnings = chart.pop("warnings")
    return {
        "normalized_input": {
            "calendar_type": info.calendar_type,
            "birth_time_input": info.original_input,
            "local_solar_time": info.local_dt.strftime("%Y-%m-%d %H:%M"),
            "timezone": info.timezone,
            "gender": info.gender,
            "longitude": info.longitude,
            "use_true_solar_time": info.use_true_solar_time,
            "late_zi_rule": info.late_zi_rule,
            "lunar_calendar": info.lunar_calendar,
            "birth_region": info.birth_region,
            "utc_offset_source": info.utc_offset_source,
            "yun_sect": info.yun_sect,
            "query_years": info.query_years,
        },
        "ruleset": {
            "id": DEFAULT_RULESET,
            "year_boundary": "立春（精确到时刻）",
            "month_boundary": "十二节（精确到时刻）",
            "jieqi_timezone": JIEQI_TIMEZONE,
            "late_zi_rule": LATE_ZI_RULES[info.late_zi_rule],
            "yun_method": YUN_SECTS[info.yun_sect],
            "true_solar_time": "经度差×4 分钟 + 均时差（NOAA 近似）" if info.use_true_solar_time else "未启用",
            "age": "虚岁（出生年记 1 岁）",
            "engine": "lunar_python",
        },
        "chart": chart,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a structured bazi (four pillars) chart payload.")
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    args = parser.parse_args()
    output_path = Path(args.output)
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
        output = build_output(payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    except Exception as exc:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
