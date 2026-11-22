"""PROPOSAL (not wired into bazi_cli.py): day-master strength with month-command and rooting
weights, plus 扶抑 useful-god selection where the 喜神 never controls the 用神.

Run:  python audit/strength_proposal.py   (prints the comparison table used in AUDIT.md)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bazi" / "scripts"))
import bazi_cli as B  # noqa: E402

E = B.ELEMENTS
GEN, CTL = B.GENERATES, B.CONTROLS
ROLE_OF = {  # element relation to the day master → role
    "same": "比劫", "gen_me": "印", "i_gen": "食伤", "i_ctl": "财", "ctl_me": "官杀"}

# ---- weights (design choices, fixed before looking at the benchmark)
STEM_W = {"year": 1.0, "month": 1.0, "hour": 1.0}
BRANCH_W = {"year": 1.0, "month": 3.0, "day": 1.5, "hour": 1.0}   # 月令 ×3, 日支 ×1.5
UNROOTED_STEM = 0.6                                               # 透干无根 counts 60 %
STRONG, WEAK = 0.55, 0.45


def role(dm_el, el):
    if el == dm_el: return "比劫"
    if GEN[el] == dm_el: return "印"
    if GEN[dm_el] == el: return "食伤"
    if CTL[dm_el] == el: return "财"
    return "官杀"


def element_of_role(dm_el, r):
    return next(el for el in E if role(dm_el, el) == r)


def score(gz4):
    keys = B.PILLAR_KEYS
    dm = gz4[2][0]; dm_el = B.STEM_ELEMENT[dm]
    hidden_els = {B.STEM_ELEMENT[h] for g in gz4 for h in B.HIDDEN_STEMS[g[1]]}
    by_role = {r: 0.0 for r in ROLE_OF.values()}
    for k, g in zip(keys, gz4):
        if k != "day":
            el = B.STEM_ELEMENT[g[0]]
            w = STEM_W[k] * (1.0 if el in hidden_els else UNROOTED_STEM)
            by_role[role(dm_el, el)] += w
        hs = B.HIDDEN_STEMS[g[1]]
        for h, frac in zip(hs, B.HIDDEN_WEIGHTS[len(hs)]):
            by_role[role(dm_el, B.STEM_ELEMENT[h])] += BRANCH_W[k] * frac
    support = by_role["比劫"] + by_role["印"]
    total = sum(by_role.values())
    ratio = support / total
    level = "vượng" if ratio >= STRONG else "nhược" if ratio < WEAK else "trung hòa"
    return ratio, level, by_role, dm_el


def pick_gods(gz4):
    ratio, level, by_role, dm_el = score(gz4)
    if level == "nhược":
        opp = max(("食伤", "财", "官杀"), key=by_role.get)
        dung = "比劫" if opp == "财" else "印"            # 财多用比劫；杀重/伤重用印
        hy = "印" if dung == "比劫" else "比劫"
    elif level == "vượng":
        if by_role["印"] > by_role["比劫"]:
            dung = "财"                                    # 印重用财
        else:
            dung = "官杀" if by_role["官杀"] > 0 else "食伤"   # 比劫重用官杀，无官杀则泄秀
        hy = {"财": "食伤", "官杀": "财", "食伤": "财"}[dung]
    else:
        return ratio, level, None, None, None
    d_el, h_el = element_of_role(dm_el, dung), element_of_role(dm_el, hy)
    assert CTL[h_el] != d_el, "喜神不得克用神"
    ky_el = next(el for el in E if CTL[el] == d_el)       # 忌 = 克用神之神
    return ratio, level, d_el, h_el, ky_el


def old(gz4):
    pillars = {k: B.pillar_detail(k, g, gz4[2][0]) for k, g in zip(B.PILLAR_KEYS, gz4)}
    s = B.strength_factors(pillars, gz4[2][0], B.wangxiang(gz4[1][1]))["heuristic_score"]
    w = B.element_counts(pillars)["weighted"]
    order = sorted(w, key=w.get)
    return s, order[0], order[1], order[-1]   # hypothesis: 用 = weakest, 喜 = 2nd weakest, 忌 = strongest


# 滴天髓闡微 (任铁樵), zh.wikisource.org/wiki/滴天髓闡微 — verdicts quoted in AUDIT.md
BENCH = [
    (1, "癸卯 丙辰 甲辰 丙寅", "vượng", "土", "十一、方局"),
    (2, "己卯 庚午 甲寅 丁卯", "vượng", "火", "二十二、伤官"),
    (3, "癸巳 壬戌 乙卯 戊寅", "vượng", "火", "二十六、出身"),
    (4, "丙子 己亥 乙酉 壬午", "nhược", "火", "九、干支总论 (调候)"),
    (5, "丁卯 辛亥 丙寅 丙申", "vượng", "水", "十一、闲神"),
    (6, "乙亥 辛巳 丙辰 癸巳", "nhược", "火", "三、父母"),
    (7, "丙申 戊戌 丁卯 乙巳", "vượng", "金", "二十二、伤官"),
    (8, "癸亥 甲子 丁酉 癸卯", "nhược", "木", "二、子女"),
    (9, "庚申 庚辰 戊辰 戊午", "nhược", "火", "四、知命"),
    (10, "己丑 庚午 戊申 癸亥", "nhược", "火", "二十六、出身"),
    (11, "辛酉 辛丑 己酉 丙寅", "nhược", "火", "四、知命 (新增; 调候)"),
    (12, "丁未 庚戌 庚辰 丙子", "vượng", "火", "五、何知章"),
    (13, "己酉 丙寅 庚申 庚辰", "vượng", "木", "二十一、官杀 (弱中变旺)"),
    (14, "甲午 丙寅 辛酉 己丑", "nhược", "土", "五、何知章"),
    (15, "己丑 丙子 辛酉 壬辰", "vượng", "水", "二十五、疾病"),
    (16, "癸亥 乙卯 壬申 乙巳", "vượng", "火", "二十二、伤官"),
    (17, "庚午 己卯 壬申 己酉", "vượng", "土", "二十二、伤官"),
    (18, "戊午 乙卯 癸卯 癸亥", "nhược", "水", "九、干支总论 (bán minh thị)"),
    (19, "丁卯 壬寅 癸卯 丙辰", "从儿", "火", "十六、顺局"),
    (20, "庚辰 己丑 己亥 壬申", "假从财", "水", "二十五、疾病"),
    (0, "己卯 丁卯 壬戌 癸卯", "nhược (tính tay, F3)", "金", "ca chuẩn"),
]

VI = {"木": "Mộc", "火": "Hỏa", "土": "Thổ", "金": "Kim", "水": "Thủy", None: "—"}


def old_label(s):
    return "vượng" if s > 0.5 else "nhược" if s < -0.5 else "cân bằng"


if __name__ == "__main__":
    print("| # | Tứ trụ | Sách: thân | Sách: dụng | Cũ: điểm → nhãn | Cũ: dụng/hỷ/kỵ (giả thuyết) | Mới: tỷ lệ → mức | Mới: dụng/hỷ/kỵ | Thân đúng cũ/mới | Dụng đúng cũ/mới |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    tally = {"so": 0, "sn": 0, "do": 0, "dn": 0, "n": 0}
    for n, gz, book_s, book_d, sec in BENCH:
        gz4 = gz.split()
        s, ow, ow2, os_ = old(gz4)
        r, lvl, d, h, k = pick_gods(gz4)
        ol = old_label(s)
        regular = book_s in ("vượng", "nhược")
        so = "✓" if ol == book_s else "✗"
        sn = "✓" if lvl == book_s else "✗"
        do = "✓" if ow == book_d else "✗"
        dn = "✓" if d == book_d else "✗"
        if regular:
            tally["n"] += 1
            tally["so"] += so == "✓"; tally["sn"] += sn == "✓"; tally["do"] += do == "✓"; tally["dn"] += dn == "✓"
        print(f"| {n} | {gz} | {book_s} | {VI[book_d]} | {s:+.1f} → {ol} | {VI[ow]}/{VI[ow2]}/{VI[os_]} | "
              f"{r:.2f} → {lvl} | {VI[d]}/{VI[h]}/{VI[k]} | {so if regular else '–'}/{sn if regular else '–'} | "
              f"{do}/{dn} |")
    t = tally
    print(f"\n18 lá số thường (bỏ #19, #20 tòng cách; ca chuẩn #0 tính riêng): "
          f"thân đúng cũ {t['so']}/{t['n']}, mới {t['sn']}/{t['n']}; dụng đúng cũ {t['do']}/{t['n']}, mới {t['dn']}/{t['n']}")
