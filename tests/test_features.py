import os
import zipfile

import pytest
from openpyxl import load_workbook

from qlvtvl.core.checks import WARNING as CW
from qlvtvl.core.checks import run_checks
from qlvtvl.core.db import Project
from qlvtvl.core.exporter import export_official
from qlvtvl.core.importer import WARNING, analyze, export_annotated, save_blank_template
from qlvtvl.core.package import issue_key, make_package, send_readiness, summarize_file
from qlvtvl.core.seed import ensure_defaults, load_sample


@pytest.fixture
def sample(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    p = Project(str(tmp_path / "s.vtvl"))
    ensure_defaults(p)
    load_sample(p)
    yield p, tmp_path
    p.close()


def test_duplicate_with_project_and_annotated_file(sample):
    p, tmp = sample
    f = tmp / "f.xlsx"
    export_official(p, str(f))
    wb = load_workbook(f)
    wb["1. A1_NhiemVu"]["B3"] = "Tên đã sửa"
    wb["3. B1_KhoiLuong"]["C5"] = "khoảng 2500"
    wb.save(f)
    rep = analyze(str(f), p)
    dup = [i for i in rep.issues if i.level == WARNING and "Trùng với dòng đã có trong hồ sơ" in i.message]
    assert dup and dup[0].cell == "A3" and dup[0].key == "NV01" and dup[0].fix
    assert rep.sheets["A1"].badge() == "Xem lại" and rep.sheets["B1"].badge() == "1 lỗi"
    assert rep.total_rows == rep.valid_rows + rep.error_rows
    out = tmp / "kq.xlsx"
    n = export_annotated(rep, str(out))
    assert n >= 2
    ws = load_workbook(out)["3. B1_KhoiLuong"]
    col = next(c for c in range(1, ws.max_column + 1) if ws.cell(2, c).value == "KẾT QUẢ KIỂM TRA")
    assert "Phải là số" in ws.cell(5, col).value and ws["C5"].comment is not None


def test_blank_template_is_repaired(sample, tmp_path):
    p, _ = sample
    out = tmp_path / "mau.xlsx"
    save_blank_template(p, str(out))
    wb = load_workbook(out)
    assert "[" not in wb["8. C3_NhuCau"]["M50"].value and wb["1. A1_NhiemVu"]["A3"].value is None


def test_explanations_and_package(sample, tmp_path):
    p, _ = sample
    r = p.rows("C3")[4]
    p.update_row(r["_id"], {"giai_trinh": ""})        # tạo cảnh báo: thiếu giải trình
    warns = [i for i in run_checks(p) if i.level == CW]
    assert warns and not send_readiness(p)["ready"]
    for i in warns:
        p.set_explanation(issue_key(i), "Đang bổ sung hồ sơ khảo sát, hoàn thành trước 15/11/2026.")
    assert send_readiness(p)["ready"]
    z = make_package(p, str(tmp_path))
    names = zipfile.ZipFile(z).namelist()
    assert any(n.endswith(".xlsx") and n.startswith("BoBieu") for n in names)
    assert any(n.endswith(".docx") for n in names) and any(n.endswith(".vtvl") for n in names)
    assert p.get_meta("phien_ban") == "1" and p.get_meta("trang_thai_ho_so") == "Đã gửi"
    assert p.history()[0]["event"].startswith("Đóng gói và gửi hồ sơ")


def test_history_restore_keeps_log(sample):
    p, _ = sample
    snap = p.snapshot("Test")
    p.log("Mốc A", "", backup=snap)
    p.delete_rows("A1", [r["_id"] for r in p.rows("A1")])
    assert p.count("A1") == 0
    p.restore_from(snap)
    assert p.count("A1") == 11
    assert any(h["event"] == "Mốc A" for h in p.history())


def test_subunit_summary(sample, tmp_path):
    p, _ = sample
    f = tmp_path / "cap_duoi.xlsx"
    export_official(p, str(f))
    a = summarize_file(str(f))
    b = summarize_file(p.path)
    assert not a["error"] and a["vt"] == 13 and a["unit"]
    assert b["need"] == a["need"] == 29


def test_gui_pages_and_links(sample, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6.QtWidgets")
    from PySide6.QtWidgets import QApplication, QMessageBox
    from qlvtvl.ui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    p, tmp = sample
    path = p.path
    p.close()
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    w = MainWindow()
    w.load(path)
    for key in w.pages:
        w.go(key)
        app.processEvents()
    hp = w.pages["history"]
    hp.save_version()
    w.go("history")
    assert hp.tbl.item(0, 5).text().startswith("Khôi phục")
    hp.tbl.cellClicked.emit(0, 5)          # bấm liên kết “Khôi phục”
    app.processEvents()
    assert any("Khôi phục phiên bản" in h["event"] for h in w.project.history())
    w.open_form("C3", key="VT05")
    assert w.current_key() == "forms"
    w.project.close()
    w.project = None
