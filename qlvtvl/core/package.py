"""Đóng gói hồ sơ gửi đi; giải trình lỗi; tổng hợp hồ sơ cấp dưới."""
from __future__ import annotations

import os
import tempfile
import zipfile
from datetime import datetime

from .calc import Calculator, fmt, s
from .checks import ERROR, INFO, WARNING, run_checks


def issue_key(i) -> str:
    return f"{i.form}|{i.ref}|{i.message}"


def pending_issues(project, calc=None):
    """Lỗi/cảnh báo kèm giải trình đã nhập."""
    gt = project.explanations()
    out = []
    for i in run_checks(project, calc):
        if i.level == INFO:
            continue
        e = gt.get(issue_key(i), {})
        out.append((i, s(e.get("giai_trinh")), s(e.get("nguoi")), s(e.get("ngay"))))
    return out


def send_readiness(project) -> dict:
    items = pending_issues(project)
    errors = [x for x in items if x[0].level == ERROR]
    warns = [x for x in items if x[0].level == WARNING]
    unexplained = [x for x in warns if not x[1]]
    return {"errors": len(errors), "warnings": len(warns), "unexplained": len(unexplained),
            "ready": not errors and not unexplained}


def export_explanations(project, path: str):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "GiaiTrinh"
    ws.append(["STT", "Mức", "Biểu", "Mã", "Nội dung", "Giải trình", "Người giải trình", "Thời điểm"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for n, (i, g, who, when) in enumerate(pending_issues(project), 1):
        ws.append([n, i.level, i.form, i.ref, i.message, g, who, when])
    for col, w in zip("ABCDEFGH", (6, 10, 8, 14, 70, 60, 20, 18)):
        ws.column_dimensions[col].width = w
    wb.save(path)


def make_package(project, folder: str) -> str:
    """Tạo gói hồ sơ .zip: Bộ biểu Excel, báo cáo Word, danh sách giải trình, tệp hồ sơ .vtvl."""
    from .exporter import export_official, export_word
    meta = project.meta()
    ver = int(s(meta.get("phien_ban")) or "0") + 1
    unit = "".join(ch for ch in _ascii(meta.get("ten_don_vi", "DonVi")) if ch.isalnum()) or "DonVi"
    stamp = f"{datetime.now():%Y%m%d_%H%M}"
    zpath = os.path.join(folder, f"HoSo_VTVL_{unit}_v{ver}_{stamp}.zip")
    with tempfile.TemporaryDirectory() as d:
        files = {
            f"BoBieu_VTVL_{unit}_v{ver}.xlsx": lambda p: export_official(project, p),
            f"BaoCao_RaSoat_VTVL_{unit}_v{ver}.docx": lambda p: export_word(project, p),
            f"GiaiTrinh_{unit}_v{ver}.xlsx": lambda p: export_explanations(project, p),
        }
        for name, fn in files.items():
            fn(os.path.join(d, name))
        project.set_meta("phien_ban", str(ver), notify=False)
        project.set_meta("trang_thai_ho_so", "Đã gửi", notify=False)
        project.set_meta("ngay_gui", f"{datetime.now():%d/%m/%Y %H:%M}", notify=False)
        vt = os.path.join(d, f"HoSo_{unit}_v{ver}.vtvl")
        project.backup(vt)
        r = send_readiness(project)
        manifest = (f"Hồ sơ rà soát vị trí việc làm – {meta.get('ten_don_vi', '')}\n"
                    f"Phiên bản: {ver}\nThời điểm đóng gói: {datetime.now():%d/%m/%Y %H:%M}\n"
                    f"Kỳ thống kê: {meta.get('ky_thong_ke', '')}; ngày chốt nhân lực: {meta.get('ngay_chot', '')}\n"
                    f"Người lập: {meta.get('nguoi_lap', '')}; người đứng đầu: {meta.get('nguoi_dung_dau', '')}\n"
                    f"Kiểm tra tự động: {r['errors']} lỗi, {r['warnings']} cảnh báo "
                    f"({r['warnings'] - r['unexplained']} đã giải trình).\n"
                    "Căn cứ: Hướng dẫn số 7-HD/BTCTW ngày 19/10/2026 của Ban Tổ chức Trung ương.\n")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for name in list(files) + [os.path.basename(vt)]:
                z.write(os.path.join(d, name), name)
            z.writestr("DOC_TRUOC.txt", manifest)
    snap = project.snapshot(f"GuiV{ver}")
    project.log(f"Đóng gói và gửi hồ sơ – phiên bản {ver}", os.path.basename(zpath), backup=snap)
    return zpath


def _ascii(text: str) -> str:
    import unicodedata
    text = (text or "").replace("Đ", "D").replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


# ------------------------------------------------------------ hồ sơ cấp dưới
def summarize_file(path: str) -> dict:
    """Đọc một hồ sơ cấp dưới (.vtvl hoặc Bộ biểu .xlsx) và trả về số liệu tổng hợp."""
    from .db import Project
    from .importer import analyze
    from openpyxl import load_workbook
    ext = os.path.splitext(path)[1].lower()
    out = {"path": path, "file": os.path.basename(path), "unit": "", "error": ""}
    try:
        if ext == ".vtvl":
            p = Project(path)
            out["unit"] = p.get_meta("ten_don_vi", "")
            out["status"] = p.get_meta("trang_thai_ho_so", "Đang kê khai")
            out["version"] = p.get_meta("phien_ban", "0")
        else:
            rep = analyze(path, None)
            if rep.fatal:
                out["error"] = rep.issues[0].message
                return out
            p = Project(":memory:")
            for code, r in rep.sheets.items():
                if r.found and r.structure_ok:
                    p.replace_rows(code, [d for rr, d in r.rows if rr not in r.bad_rows])
            try:
                wb = load_workbook(path, read_only=True)
                if "14. T_TienDo" in wb.sheetnames:
                    out["unit"] = s(wb["14. T_TienDo"]["A3"].value)
            except Exception:  # noqa: BLE001
                pass
            out["status"] = "Tệp Bộ biểu"
            out["version"] = ""
        calc = Calculator(p)
        sm = calc.summary()
        issues = run_checks(p, calc)
        out.update(nv=sm["nv"], vt=sm["vt"], net=sm["net"], qd=sm["qd"], need=sm["need"], existing=sm["existing"],
                   ok_vt=sm["ok_vt"], errors=sum(1 for i in issues if i.level == ERROR),
                   warnings=sum(1 for i in issues if i.level == WARNING),
                   updated=datetime.fromtimestamp(os.path.getmtime(path)).strftime("%d/%m/%Y %H:%M"))
        out["unit"] = out["unit"] or os.path.splitext(out["file"])[0]
        p.close()
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out


def export_subunits(rows, path: str):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "TongHop"
    head = ["STT", "Đơn vị", "Tệp", "Nhiệm vụ", "VTVL", "Giờ ròng", "Người quy đổi PP2", "Người cần bố trí",
            "Hiện có", "VTVL đủ căn cứ", "Lỗi", "Cảnh báo", "Tình trạng", "Cập nhật"]
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True)
    tot = {k: 0 for k in ("nv", "vt", "net", "qd", "need", "existing", "ok_vt", "errors", "warnings")}
    for n, r in enumerate(rows, 1):
        if r.get("error"):
            ws.append([n, r.get("unit"), r["file"], "", "", "", "", "", "", "", "", "", "Lỗi: " + r["error"]])
            continue
        ws.append([n, r["unit"], r["file"], r["nv"], r["vt"], round(r["net"], 2), round(r["qd"], 3),
                   round(r["need"], 3), r["existing"], f"{r['ok_vt']}/{r['vt']}", r["errors"], r["warnings"],
                   r.get("status", ""), r.get("updated", "")])
        for k in tot:
            tot[k] += r[k]
    ws.append(["", "TỔNG CỘNG", "", tot["nv"], tot["vt"], round(tot["net"], 2), round(tot["qd"], 3),
               round(tot["need"], 3), tot["existing"], f"{tot['ok_vt']}/{tot['vt']}", tot["errors"], tot["warnings"]])
    for c in ws[ws.max_row]:
        c.font = Font(bold=True)
    for i, w in enumerate((6, 32, 30, 10, 8, 12, 14, 14, 10, 14, 8, 10, 16, 16), 1):
        ws.column_dimensions[chr(64 + i)].width = w
    wb.save(path)


__all__ = ["issue_key", "pending_issues", "send_readiness", "make_package", "summarize_file", "export_subunits",
           "export_explanations", "fmt"]
