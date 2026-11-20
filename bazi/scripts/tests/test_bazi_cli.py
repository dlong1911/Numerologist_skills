"""bazi_cli.py 单元测试与端到端断言。

覆盖：
- 十神、十二长生、旺相休囚死基础表
- 端到端样例（越南出生 + 真太阳时）：四柱、大运逆排、起运、流年伏吟
- 立春边界（非 UTC+8 时区换算北京时间判断节气）
- 夜子时 same_day / next_day
- 农历闰月输入与非法闰月
- CLI 读写与 error 字段
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from bazi_cli import build_output, ten_god, twelve_stage, wangxiang, detect_interactions

SCRIPT = Path(__file__).resolve().parent.parent / "bazi_cli.py"
EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "bazi_input.json"


def run(**kw):
    payload = {"calendar_type": "solar", "gender": "男", "timezone": "Asia/Shanghai"}
    payload.update(kw)
    return build_output(payload)


class TestTables:
    def test_ten_god(self):
        assert ten_god("壬", "癸") == "劫财"
        assert ten_god("壬", "乙") == "伤官"
        assert ten_god("壬", "己") == "正官"
        assert ten_god("壬", "戊") == "七杀"
        assert ten_god("壬", "丁") == "正财"
        assert ten_god("壬", "辛") == "正印"
        assert ten_god("甲", "甲") == "比肩"
        assert ten_god("甲", "丙") == "食神"

    def test_twelve_stage(self):
        assert twelve_stage("甲", "亥") == "长生"
        assert twelve_stage("甲", "卯") == "帝旺"
        assert twelve_stage("乙", "午") == "长生"
        assert twelve_stage("乙", "寅") == "帝旺"
        assert twelve_stage("壬", "卯") == "死"
        assert twelve_stage("壬", "戌") == "冠带"

    def test_wangxiang(self):
        assert wangxiang("卯") == {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"}
        assert wangxiang("戌")["土"] == "旺"

    def test_interactions(self):
        items = [{"label": "A", "ganzhi": "甲子"}, {"label": "B", "ganzhi": "庚午"}, {"label": "C", "ganzhi": "乙卯"}]
        types = {(i["type"], tuple(i["between"])) for i in detect_interactions(items)}
        assert ("反吟", ("A", "B")) in types
        assert ("相刑", ("A", "C")) in types  # 子卯刑
        items = [{"label": "A", "ganzhi": "己丑"}, {"label": "B", "ganzhi": "甲戌"}, {"label": "C", "ganzhi": "辛未"}]
        assert any(i["type"] == "三刑" for i in detect_interactions(items))


@pytest.fixture(scope="module")
def out():
    return build_output(json.loads(EXAMPLE.read_text(encoding="utf-8")))


class TestSampleChart:
    def test_pillars(self, out):
        assert out["chart"]["bazi"] == "己卯 丁卯 壬戌 癸卯"
        assert out["chart"]["day_master"]["stem"] == "壬"

    def test_true_solar_time(self, out):
        tst = out["chart"]["times"]["true_solar_time"]
        assert tst["value"].startswith("1999-03-11 05:01")
        assert out["chart"]["times"]["beijing_time"] == "1999-03-11 06:00"

    def test_dayun(self, out):
        dy = out["chart"]["dayun"]
        assert dy["direction"] == "逆排"
        assert (dy["start"]["years"], dy["start"]["months"]) == (1, 7)
        assert dy["start"]["start_date"].startswith("2000-10")
        gz = [(p["ganzhi"], p["start_year"], p["end_year"]) for p in dy["pillars"]]
        assert gz[0] == ("丙寅", 2000, 2009)
        assert ("甲子", 2020, 2029) in gz

    def test_liunian_2023_fuyin(self, out):
        ln = {l["year"]: l for l in out["chart"]["liunian"]}[2023]
        assert ln["ganzhi"] == "癸卯" and ln["stem_ten_god"] == "劫财" and ln["dayun"] == "甲子"
        assert any(i["type"] == "伏吟" and i["between"] == ["时柱", "流年"] for i in ln["interactions"])

    def test_self_check(self, out):
        assert all(out["chart"]["self_check"].values())


class TestEdgeCases:
    def test_lichun_boundary_converted_to_beijing(self):
        # 2024 立春 北京时间 16:27；越南 15:30 = 北京 16:30 → 已过立春
        before = run(birth_time="2024-02-04 15:20", timezone="Asia/Ho_Chi_Minh")
        after = run(birth_time="2024-02-04 15:30", timezone="Asia/Ho_Chi_Minh")
        assert before["chart"]["pillars"]["year"]["ganzhi"] == "癸卯"
        assert before["chart"]["pillars"]["month"]["ganzhi"] == "乙丑"
        assert after["chart"]["pillars"]["year"]["ganzhi"] == "甲辰"
        assert after["chart"]["pillars"]["month"]["ganzhi"] == "丙寅"
        assert any("节令" in w for w in after["warnings"])

    def test_late_zi_same_day(self):
        out = run(birth_time="2024-01-01 23:30")
        assert out["chart"]["bazi"] == "癸卯 甲子 甲子 丙子"

    def test_late_zi_next_day(self):
        out = run(birth_time="2024-01-01 23:30", late_zi_rule="next_day")
        assert out["chart"]["bazi"] == "癸卯 甲子 乙丑 丙子"

    def test_lunar_leap_month(self):
        out = run(calendar_type="lunar", birth_time="2023-02-15 10:00", is_leap_month=True)
        assert out["normalized_input"]["local_solar_time"] == "2023-04-05 10:00"
        assert out["chart"]["bazi"] == "癸卯 丙辰 癸巳 丁巳"

    def test_invalid_leap_month(self):
        with pytest.raises(ValueError):
            run(calendar_type="lunar", birth_time="2023-03-15 10:00", is_leap_month=True)

    def test_female_forward(self):
        out = run(birth_time="1999-03-11 05:00", gender="女", timezone="Asia/Ho_Chi_Minh")
        assert out["chart"]["dayun"]["direction"] == "顺排"

    def test_missing_gender(self):
        with pytest.raises(ValueError):
            build_output({"birth_time": "1999-03-11 05:00"})


class TestCli:
    def test_cli_roundtrip(self, tmp_path):
        out = tmp_path / "out.json"
        rc = subprocess.run([sys.executable, str(SCRIPT), "--input", str(EXAMPLE), "--output", str(out)]).returncode
        assert rc == 0
        assert json.loads(out.read_text(encoding="utf-8"))["chart"]["bazi"] == "己卯 丁卯 壬戌 癸卯"

    def test_cli_error(self, tmp_path):
        inp, out = tmp_path / "in.json", tmp_path / "out.json"
        inp.write_text(json.dumps({"birth_time": "1999-03-11"}), encoding="utf-8")
        rc = subprocess.run([sys.executable, str(SCRIPT), "--input", str(inp), "--output", str(out)]).returncode
        assert rc == 1
        assert "error" in json.loads(out.read_text(encoding="utf-8"))
