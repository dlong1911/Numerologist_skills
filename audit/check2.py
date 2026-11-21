import sys
from datetime import date, timedelta
sys.path.insert(0, sys.argv[1])
import ref
from lunar_python import Solar

# my lunisolar implementation at UTC+8 must reproduce lunar_python (validates the implementation)
cn = ref.lunisolar_months(1950, 2030, 8)
vn = ref.lunisolar_months(1950, 2030, 7)
d = date(1950, 3, 1); bad8 = 0; diffs = []
while d < date(2030, 12, 1):
    l = Solar.fromYmd(d.year, d.month, d.day).getLunar()
    lp = (l.getYear(), abs(l.getMonth()), l.getDay(), l.getMonth() < 0)
    if ref.solar_to_lunar(d, cn) != lp: bad8 += 1
    v = ref.solar_to_lunar(d, vn)
    if v != lp: diffs.append((d, lp, v))
    d += timedelta(days=1)
print("UTC+8 impl vs lunar_python mismatched days:", bad8)
print("VN(UTC+7) vs lunar_python mismatched days:", len(diffs))
# group into runs
runs = []
for x in diffs:
    if runs and (x[0] - runs[-1][-1][0]).days == 1: runs[-1].append(x)
    else: runs.append([x])
for r in runs:
    print(r[0][0], "->", r[-1][0], f"({len(r)}d)", "CN", r[0][1], "VN", r[0][2])
