from datetime import datetime

import pytest
from openpyxl import Workbook, load_workbook

from qlvtvl.core.db import Project
from qlvtvl.core.exporter import bundled_template, export_official
from qlvtvl.core.importer import ERROR, FATAL, INFO, WARNING, analyze, apply, export_issues, undo_last_import
from qlvtvl.core.seed import ensure_defaults, load_sample


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    p = Project(str(tmp_path / "t.vtvl"))
    ensure_defaults(p)
    yield p, tmp_path
    p.close()


def msgs(rep, level=None, sheet=None):
    return [i for i in rep.issues if (level is None or i.level == level) and (sheet is None or i.sheet == sheet)]


def test_file_level_errors(env):
    p, tmp = env
    xls = tmp / "a.xls"
    xls.write_bytes(b"abc")
    assert analyze(str(xls), p).fatal
    fake = tmp / "b.xlsx"
    fake.write_text("không phải excel")
    rep = analyze(str(fake), p)
    assert rep.fatal and "không phải Excel" in rep.issues[0].message
    empty = tmp / "c.xlsx"
    empty.write_bytes(b"")
    assert analyze(str(empty), p).fatal
    other = tmp / "d.xlsx"
    Workbook().save(other)
    rep = analyze(str(other), p)
    assert rep.fatal and "không chứa trang tính" in rep.issues[0].message
    assert not rep.importable()


def test_cell_level_errors(env):
    p, tmp = env
    wb = load_workbook(bundled_template())
    a1 = wb["1. A1_NhiemVu"]
    a1["A3"], a1["B3"], a1["F3"] = "NV01", "Nhiệm vụ 1", "tiếp tục THỰC hiện"   # sai hoa/thường -> tự chuẩn hóa
    a1["E6"] = datetime(2026, 9, 30)                                          # ngày -> văn bản
    a1["A4"], a1["B4"], a1["F4"] = "NV01", "Trùng mã", "Tiếp tục thực hiện"    # trùng mã
    a1["B5"] = "Dòng thiếu mã"                                                  # thiếu mã
    a1["A6"], a1["F6"] = "NV03", "Đang làm"                                     # ngoài danh sách
    b1 = wb["3. B1_KhoiLuong"]
    b1["A3"], b1["C3"], b1["D3"] = "CV01", "mười", 5                            # chữ trong cột số
    b1["A4"], b1["C4"], b1["D4"] = "CV02", -10, "#REF!"                         # số âm, ô lỗi
    b1["A5"], b1["C5"], b1["D5"], b1["G5"] = "CV03", 100, 5, 999                # nhập đè ô công thức
    d2 = wb["10. D2_PhuongAn"]
    d2["A3"], d2["B3"] = "VT01", 2035                                           # năm sai
    f = tmp / "dirty.xlsx"
    wb.save(f)
    rep = analyze(str(f), p)
    assert not rep.fatal
    e = " | ".join(i.message for i in msgs(rep, ERROR))
    assert "Trùng mã" in e and "thiếu “Mã nhiệm vụ”" in e
    assert "Phải là số" in e and "số âm" in e and "giá trị lỗi của Excel" in e and "Năm phải là" in e
    w = " | ".join(i.message for i in msgs(rep, WARNING))
    assert "Không thuộc danh sách" in w and "Ô công thức" in w and "Mã chưa có ở biểu A2" in w
    inf = " | ".join(i.message for i in msgs(rep, INFO))
    assert "Đã chuẩn hóa thành “Tiếp tục thực hiện”" in inf and "dd/mm/yyyy" in inf
    a1r = rep.sheets["A1"]
    assert a1r.n_rows == 4 and len(a1r.bad_rows) == 3  # 2 dòng trùng + 1 thiếu mã
    # không bỏ qua dòng lỗi -> không cho nhập
    assert not rep.importable(["A1"], skip_errors=False)
    stats = apply(p, rep, ["A1", "B1"], skip_errors=True)
    assert stats["A1"]["added"] == 1 and stats["A1"]["skipped"] == 3
    r = p.rows("A1")[0]
    assert r["ma"] == "NV03" and r["trang_thai"] == "Đang làm" and r["ky"] == "30/09/2026"
    assert [x["ma_cv"] for x in p.rows("B1")] == ["CV03"]
    out = tmp / "loi.xlsx"
    export_issues(rep, str(out))
    assert load_workbook(out).active.max_row > 10


def test_structure_mismatch_blocks_sheet(env):
    p, tmp = env
    wb = load_workbook(bundled_template())
    ws = wb["2. A2_CongViec"]
    ws["C2"] = "Cột tự thêm"
    ws["A3"] = "CV01"
    f = tmp / "s.xlsx"
    wb.save(f)
    rep = analyze(str(f), p)
    assert not rep.sheets["A2"].structure_ok
    assert any("Cấu trúc trang khác bộ biểu" in i.message for i in msgs(rep, ERROR, "2. A2_CongViec"))
    assert not rep.importable(["A2"])


def test_merge_and_undo(env):
    p, tmp = env
    load_sample(p)
    f = tmp / "full.xlsx"
    export_official(p, str(f))
    wb = load_workbook(f)
    ws = wb["1. A1_NhiemVu"]
    ws["B3"] = "Tên nhiệm vụ đã sửa"
    ws["A20"], ws["B20"], ws["C20"] = "NV99", "Nhiệm vụ mới", "TV"
    wb.save(f)
    before = p.count("A1")
    rep = analyze(str(f), p, ["A1"])
    stats = apply(p, rep, ["A1"], mode="merge")
    assert stats["A1"] == {"added": 1, "updated": before, "skipped": 0}
    assert p.rows("A1")[0]["ten"] == "Tên nhiệm vụ đã sửa" and p.count("A1") == before + 1
    assert undo_last_import(p)
    assert p.count("A1") == before and p.rows("A1")[0]["ten"] != "Tên nhiệm vụ đã sửa"


def test_clean_official_file_has_no_errors(env):
    p, tmp = env
    load_sample(p)
    f = tmp / "ok.xlsx"
    export_official(p, str(f))
    rep = analyze(str(f), p)
    assert not msgs(rep, ERROR) and not msgs(rep, FATAL) and not msgs(rep, WARNING)
    assert rep.importable()
