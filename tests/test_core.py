import os

import pytest

from qlvtvl.core.calc import Calculator, fmt, num, parse_cv_list
from qlvtvl.core.checks import ERROR, WARNING, run_checks
from qlvtvl.core.db import Project
from qlvtvl.core.exporter import export_excel, export_word, import_excel
from qlvtvl.core.seed import ensure_defaults, load_sample


@pytest.fixture
def project(tmp_path):
    p = Project(str(tmp_path / "t.vtvl"))
    ensure_defaults(p)
    yield p
    p.close()


def test_num_and_fmt():
    assert num("1.904") == 1904
    assert num("1,5") == 1.5
    assert num("2.5") == 2.5
    assert num("1.904,25") == 1904.25
    assert num("") == 0
    assert fmt(1904) == "1.904"
    assert fmt(1.366, 3) == "1,366"


def test_parse_cv_list():
    assert parse_cv_list("CV01, CV02*0.5; CV03 (30%)") == [("CV01", 1.0), ("CV02", 0.5), ("CV03", 0.3)]
    assert parse_cv_list("CV04*50%") == [("CV04", 0.5)]


def test_pp2_formula(project):
    project.add_row("A1", {"ma": "NV01", "ten": "x"})
    project.add_row("A2", {"ma": "CV01", "ma_nv": "NV01", "ten": "y"})
    project.add_row("B1", {"ma_cv": "CV01", "so_luong": 2600, "gio_sp": 1})
    project.add_row("C1", {"ma": "VT01", "ten": "z"})
    project.add_row("C3", {"ma_vt": "VT01", "phuong_phap": "PP2 - Khối lượng, thời gian", "ds_cv": "CV01"})
    c = Calculator(project)
    r = project.rows("C3")[0]
    v = c.c3_values(r)
    assert v["gio_can"] == 2600
    assert round(v["nguoi_quy_doi"], 3) == 1.366  # ví dụ trong Hướng dẫn 07: không làm tròn thành 2
    assert round(c.need("VT01"), 3) == 1.366


def test_b2_adjustment_and_share(project):
    project.add_row("B1", {"ma_cv": "CV01", "so_luong": 1000, "gio_sp": 2})
    project.add_row("B2", {"ma_cv": "CV01", "gio_thay_doi": -400})
    project.add_row("C3", {"ma_vt": "VT01", "phuong_phap": "PP2", "ds_cv": "CV01*0.5"})
    c = Calculator(project)
    v = c.c3_values(project.rows("C3")[0])
    assert v["gio_b1"] == 1000 and v["gio_b2"] == -200 and v["gio_can"] == 800


def test_sample_is_consistent(project):
    load_sample(project)
    issues = run_checks(project)
    assert not [i for i in issues if i.level in (ERROR, WARNING)], issues


def test_checks_detect_problems(project):
    project.add_row("A2", {"ma": "CV01", "ma_nv": "NV99", "ten": "x"})
    project.add_row("C3", {"ma_vt": "VT01", "phuong_phap": "PP2 - Khối lượng, thời gian", "ds_cv": "CV01*0.7, CVX"})
    project.add_row("C3", {"ma_vt": "VT02", "phuong_phap": "PP2 - Khối lượng, thời gian", "ds_cv": "CV01*0.6"})
    msgs = [i.message for i in run_checks(project) if i.level == ERROR]
    assert any("NV99" in m for m in msgs)
    assert any("> 100%" in m for m in msgs)
    assert any("CVX" in m for m in msgs)


def test_export_import_roundtrip(project, tmp_path):
    load_sample(project)
    x = str(tmp_path / "o.xlsx")
    export_excel(project, x)
    export_word(project, str(tmp_path / "o.docx"))
    assert os.path.getsize(x) > 0
    p2 = Project(str(tmp_path / "t2.vtvl"))
    res = import_excel(p2, x)
    assert res["C3"] == project.count("C3")
    for code in ("A1", "A2", "B1", "B2", "C1", "C3", "D1", "D2"):
        a = [{k: v for k, v in r.items() if k != "_id" and v not in (None, "")} for r in project.rows(code)]
        b = [{k: v for k, v in r.items() if k != "_id"} for r in p2.rows(code)]
        assert a == b, code
    p2.close()


def test_rename_key_propagates(project):
    project.add_row("C1", {"ma": "VT01"})
    project.add_row("D1", {"ma_vt": "VT01"})
    project.rename_key([("D1", "ma_vt")], "VT01", "VT10")
    assert project.rows("D1")[0]["ma_vt"] == "VT10"
