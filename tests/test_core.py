import os
import unicodedata

import pytest
from openpyxl import load_workbook

from qlvtvl.core.calc import DAT, Calculator, fmt, num
from qlvtvl.core.checks import ERROR, WARNING, run_checks
from qlvtvl.core.db import Project
from qlvtvl.core.exporter import (
    bundled_template, export_official, export_word, import_official, repair_template, shift_formula,
)
from qlvtvl.core.forms import FORMS, INPUT_FORMS
from qlvtvl.core.seed import ensure_defaults, load_sample

KY = "01/10/2025 - 30/9/2026"


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
    assert fmt(1904) == "1.904"
    assert fmt(1.366, 3) == "1,366"


def _base(project, with_b2=True, co_so="Trước thay đổi, có điều chỉnh"):
    """Ví dụ PP2 tại Hướng dẫn 7-HD/BTCTW: 6.000 SP × 30 phút; số hóa −500, thuê dịch vụ −100, việc mới +200."""
    project.add_row("A1", dict(ma="NV01", ten="x", co_quan="TV", can_cu="QĐ", ky=KY, trang_thai="Tiếp tục thực hiện",
                               nguon="n"))
    project.add_row("A2", dict(ma="CV01", ma_nv="NV01", ma_vt="VT01", ten="y", san_pham="sp", dvt="hs", can_cu="c"))
    project.add_row("B1", dict(ma_cv="CV01", so_sp=6000, phut_do=30, nguon_sl="BC", nguon_tg="khảo sát",
                               tt_tg="Kiểm đếm, ước lượng thực tế", ky=KY))
    project.add_row("C1", dict(ma="VT01", ten="z", loai_nl="Viên chức", che_do="Phổ biến (40 giờ/tuần)",
                               trang_thai="Tiếp tục sử dụng"))
    if with_b2:
        common = dict(ma_cv="CV01", nguon="bc", ky=KY, co_so=co_so, trang_thai="Đã kiểm chứng",
                      doi_chieu="Đã đối chiếu")
        project.add_row("B2", dict(common, loai="Số hóa", cong_doan="a", sp_ap_dung=1000, phut_truoc=30, phut_sau=0))
        project.add_row("B2", dict(common, loai="Thuê dịch vụ/đặt hàng", cong_doan="b", sp_ap_dung=200,
                                   phut_truoc=30, phut_sau=0))
        project.add_row("B2", dict(common, loai="Công việc mới phát sinh", cong_doan="c", gio_moi=200))
    project.add_row("C3", dict(ma_vt="VT01", pp="PP2", nguoi_can=1.5, giai_trinh="g", trang_thai="Đã kiểm chứng"))


def test_pp2_example_from_guidance(project):
    _base(project)
    c = Calculator(project)
    b1 = project.rows("B1")[0]
    assert c.value("B1", b1, "canh_bao") == DAT
    assert c.value("B1", b1, "gio_tong") == 3000
    t = {x["ma_cv"]: x for x in c.b2th}["CV01"]
    assert (t["giam_so_hoa"], t["giam_khac"], t["gio_moi"], t["rong"]) == (500, 100, 200, -400)
    o = c.v[project.rows("C3")[0]["_id"]]
    assert o["gio_rong"] == 2600
    assert round(o["nguoi_qd"], 3) == 1.366   # không tự làm tròn thành 02 biên chế
    assert o["canh_bao"] == DAT


def test_b2_after_change_not_deducted(project):
    _base(project, co_so="Đã đo sau thay đổi (không trừ)")
    c = Calculator(project)
    assert c.v[project.rows("C3")[0]["_id"]]["gio_rong"] == 3200  # chỉ cộng việc mới


def test_b1_status_rules(project):
    _base(project, with_b2=False)
    r = project.rows("B1")[0]
    project.update_row(r["_id"], {"nguon_sl": ""})
    assert Calculator(project).value("B1", project.rows("B1")[0], "canh_bao") == "THIẾU NGUỒN SẢN LƯỢNG/CÔNG VIỆC"
    project.update_row(r["_id"], {"nguon_sl": "x", "tt_tg": "Có định mức", "nguon_tg": ""})
    assert Calculator(project).value("B1", project.rows("B1")[0], "canh_bao") == "THIẾU NGUỒN THỜI GIAN"
    # phút chuẩn đã xác nhận trong danh mục được ưu tiên
    project.add_row("DM", dict(ma="SP01", ten="hs", phut_chuan=20, trang_thai="Đã xác nhận", van_ban="QĐ 1"))
    project.update_row(r["_id"], {"nguon_tg": "TT", "ma_sp": "SP01"})
    c = Calculator(project)
    rr = project.rows("B1")[0]
    assert c.value("B1", rr, "phut_tinh") == 20 and c.value("B1", rr, "gio_tong") == 2000


def test_special_regime_needs_verified_hours(project):
    _base(project, with_b2=False)
    vt = project.rows("C1")[0]
    project.update_row(vt["_id"], {"che_do": "Đặc thù"})
    c = Calculator(project)
    assert c.value("C1", project.rows("C1")[0], "kt_quy_gio") == "THIẾU GIỜ ĐẶC THÙ"
    assert c.v[project.rows("C3")[0]["_id"]]["canh_bao"] == "PP2: C1 CHƯA ĐỦ CĂN CỨ"
    project.update_row(vt["_id"], {"gio_rieng": 1500, "can_cu_quy_gio": "QĐ ca kíp", "xn_gio_rieng": "Đã kiểm chứng"})
    c = Calculator(project)
    assert c.value("C1", project.rows("C1")[0], "gio_pp2") == 1500
    assert round(c.v[project.rows("C3")[0]["_id"]]["nguoi_qd"], 3) == 2.0


def test_sample_is_consistent(project):
    load_sample(project)
    issues = run_checks(project)
    assert not [i for i in issues if i.level in (ERROR, WARNING)], issues[:5]
    s = Calculator(project).summary()
    assert s["ok_vt"] == s["vt"] == 13


def test_shift_formula_ignores_strings_and_sheets():
    f = '=IF(A3="","",IF(G3="","C3 CHƯA ĐƯỢC XÁC NHẬN",COUNTIF(\'8. C3_NhuCau\'!$A$3:$A$202,A3)+QUY_GIO_PP2))'
    out = shift_formula(f, 5)
    assert 'A8=""' in out and "C3 CHƯA ĐƯỢC XÁC NHẬN" in out and "'8. C3_NhuCau'!$A$3:$A$202,A8" in out
    assert "QUY_GIO_PP2" in out


def test_repair_template_fixes_release_bugs():
    wb = load_workbook(bundled_template())
    n = repair_template(wb)
    assert n > 1000
    assert "[" not in wb["8. C3_NhuCau"]["M50"].value
    assert "C3 CHƯA ĐƯỢC XÁC NHẬN" in wb["DU_BAO_5_NAM"]["I40"].value
    assert "QUY_GIO_PP2)" in wb["6. C1_VTVL"]["E100"].value


def test_export_import_roundtrip(project, tmp_path):
    load_sample(project)
    x = str(tmp_path / "o.xlsx")
    info = export_official(project, x)
    assert info["rows"]["C3"] == 13 and not info["overflow"]
    export_word(project, str(tmp_path / "o.docx"))
    wb = load_workbook(x)
    assert wb["1. A1_NhiemVu"]["A3"].value == "NV01"
    assert wb["3. B1_KhoiLuong"]["F3"].value.startswith("=")   # công thức được giữ nguyên
    p2 = Project(str(tmp_path / "t2.vtvl"))
    import_official(p2, x)
    for code in INPUT_FORMS:
        a = [{k: v for k, v in r.items() if k != "_id" and v not in (None, "")} for r in project.rows(code)]
        b = [{k: v for k, v in r.items() if k != "_id"} for r in p2.rows(code)]
        assert a == b, code
    p2.close()


def test_forms_match_official_headers():
    wb = load_workbook(bundled_template(), read_only=True)
    for code in INPUT_FORMS:
        f = FORMS[code]
        ws = wb[f.sheet]
        header = {c.column_letter: unicodedata.normalize("NFC", c.value)
                  for c in next(ws.iter_rows(min_row=2, max_row=2)) if c.value}
        for col in f.columns:
            if col.letter:
                assert header.get(col.letter) == col.label, (code, col.letter, header.get(col.letter), col.label)


def test_rename_key_propagates(project):
    project.add_row("C1", {"ma": "VT01"})
    project.add_row("D1", {"ma_nl": "NL001", "ma_vt": "VT01"})
    project.rename_key([("D1", "ma_vt")], "VT01", "VT10")
    assert project.rows("D1")[0]["ma_vt"] == "VT10"


def test_checks_detect_problems(project):
    project.add_row("A2", {"ma": "CV01", "ma_nv": "NV99", "ma_vt": "VT9", "ten": "x"})
    project.add_row("D1", {"ma_nl": "NL1", "ma_vt": "VT1"})
    project.add_row("D1", {"ma_nl": "NL1", "ma_vt": "VT1"})
    msgs = [i.message for i in run_checks(project) if i.level == ERROR]
    assert any("NV99" in m for m in msgs)
    assert any("NL1" in m and "trùng" in m for m in msgs)
    assert os.path.exists(bundled_template())
