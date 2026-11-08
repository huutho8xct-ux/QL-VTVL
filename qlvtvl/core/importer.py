"""Kiểm soát lỗi khi nhập (upload) tệp Bộ biểu Excel.

Tệp được đọc vào VÙNG KIỂM TRA RIÊNG (đối tượng ``ImportReport`` trong bộ nhớ); số liệu chính thức của hồ sơ chỉ
thay đổi khi người dùng bấm KẾT CHUYỂN (``apply``). Kiểm tra 3 lớp: tệp – ô – liên kết (kể cả trùng với hồ sơ).
"""
from __future__ import annotations

import os
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

from .calc import isnum, num, s
from .forms import FORMS, INPUT_FORMS, YEARS

FATAL, ERROR, WARNING, INFO = "Không nhập được", "Lỗi", "Cần xem lại", "Lưu ý"
LEVEL_ORDER = {FATAL: 0, ERROR: 1, WARNING: 2, INFO: 3}
FIRST_ROW = 3
MAX_TEXT = 2000
EXCEL_ERRORS = ("#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#NUM!", "#NULL!", "#SPILL!", "#CALC!")
NEGATIVE_OK = {"de_nghi", "bien_dong"}
MERGE_KEYS = {"B1": ("ma_cv", "ma_sp"), "B2": ("ma_cv", "cong_doan", "ky"), "DB": ("ma_vt", "nam"),
              "D2": ("ma_vt", "nam")}
REF_TARGET_KEY = {"A1": "ma", "A2": "ma", "C1": "ma", "DM": "ma"}


def nfc(v):
    return unicodedata.normalize("NFC", v) if isinstance(v, str) else v


def form_key(code):
    f = FORMS[code]
    return (f.key_col,) if f.key_col else MERGE_KEYS.get(code, ())


@dataclass
class ImportIssue:
    level: str
    sheet: str
    cell: str
    column: str          # ký hiệu cột (A, B…) hoặc ''
    value: str
    message: str         # nội dung
    fix: str = ""        # cách xử lý
    code: str = ""       # mã biểu
    row: int = 0         # dòng Excel
    label: str = ""      # tên cột
    key: str = ""        # mã bản ghi để “Mở trong biểu”


@dataclass
class SheetResult:
    code: str
    sheet: str
    found: bool = False
    structure_ok: bool = True
    rows: list = field(default_factory=list)       # [(excel_row, data)]
    bad_rows: set = field(default_factory=set)
    review_rows: set = field(default_factory=set)

    @property
    def n_rows(self):
        return len(self.rows)

    @property
    def n_ok(self):
        return sum(1 for r, _ in self.rows if r not in self.bad_rows)

    def badge(self):
        if not self.found:
            return "Không có"
        if not self.structure_ok:
            return "Sai cấu trúc"
        if self.bad_rows:
            return f"{len(self.bad_rows)} lỗi"
        if self.review_rows:
            return "Xem lại"
        return "Đạt" if self.rows else "Trống"


@dataclass
class ImportReport:
    path: str
    issues: list = field(default_factory=list)
    sheets: dict = field(default_factory=dict)
    fatal: bool = False
    version: str = ""
    checked_at: str = ""

    def add(self, level, sheet, cell, column, value, message, fix="", code="", row=0, label="", key=""):
        v = "" if value is None else str(value)
        self.issues.append(ImportIssue(level, sheet, cell, column, v[:120], message, fix, code, row, label, key))

    def count(self, level, code=None):
        return sum(1 for i in self.issues if i.level == level and (code is None or i.code == code))

    @property
    def total_rows(self):
        return sum(r.n_rows for r in self.sheets.values() if r.found and r.structure_ok)

    @property
    def error_rows(self):
        return sum(len(r.bad_rows) for r in self.sheets.values() if r.found and r.structure_ok)

    @property
    def valid_rows(self):
        return self.total_rows - self.error_rows

    def importable(self, codes=None, skip_errors=True):
        if self.fatal:
            return False
        codes = codes or [c for c, r in self.sheets.items() if r.found and r.structure_ok]
        if not codes:
            return False
        for c in codes:
            r = self.sheets.get(c)
            if not r or not r.found or not r.structure_ok:
                return False
            if not skip_errors and r.bad_rows:
                return False
        return True


# ------------------------------------------------------------------ chuẩn hóa
def _convert(col, raw, rep, sheet, rr, code, key):
    cell = f"{col.letter}{rr}"

    def add(level, msg, fix, value=raw):
        rep.add(level, sheet, cell, col.letter, value, msg, fix, code, rr, col.label, key)

    v = nfc(raw)
    if isinstance(v, str):
        v = v.strip()
        if v.upper() in EXCEL_ERRORS:
            add(ERROR, "Ô chứa giá trị lỗi của Excel.", "Kiểm tra công thức/giá trị nguồn, nhập lại giá trị đúng.")
            return None, True
    if v is None or v == "":
        return None, False
    if col.kind in ("int", "float"):
        if isinstance(v, bool) or not isnum(v):
            add(ERROR, f"“{col.label}” phải là số – Phải là số (ví dụ 1904 hoặc 2,5).",
                "Chỉ ghi chữ số; bỏ chữ, đơn vị tính, ký hiệu (ví dụ “khoảng”, “giờ”).")
            return None, True
        f = num(v)
        if f < 0 and col.key not in NEGATIVE_OK:
            add(ERROR, "Không được là số âm.", "Nhập số lớn hơn hoặc bằng 0; giờ giảm ghi tại Biểu B2.")
            return None, True
        return (int(round(f)) if col.kind == "int" else f), False
    if col.key == "nam":
        if not isnum(v) or num(v) != int(num(v)) or int(num(v)) not in YEARS:
            add(ERROR, "Năm phải là 2027, 2028, 2029, 2030 hoặc 2031.", "Chọn năm trong giai đoạn 2027 – 2031.")
            return None, True
        return str(int(num(v))), False
    if isinstance(v, (datetime, date)):
        txt = v.strftime("%d/%m/%Y")
        add(INFO, "Ô kiểu ngày tháng – đã chuyển thành văn bản dd/mm/yyyy.", "Không cần xử lý.", txt)
        return txt, False
    if isinstance(v, float):
        v = str(int(v)) if v.is_integer() else str(v)
    elif not isinstance(v, str):
        v = str(v)
    if col.kind == "choice" and v not in col.options:
        match = [o for o in col.options if " ".join(o.split()).casefold() == " ".join(v.split()).casefold()]
        if match:
            add(INFO, f"Đã chuẩn hóa thành “{match[0]}”.", "Không cần xử lý.")
            return match[0], False
        add(WARNING, "Không thuộc danh sách lựa chọn của bộ biểu.",
            "Chọn một giá trị: " + "; ".join(col.options) + ".")
    if len(v) > MAX_TEXT:
        add(WARNING, f"Nội dung dài {len(v)} ký tự.", f"Rút gọn còn ≤ {MAX_TEXT} ký tự; chi tiết để ở hồ sơ minh chứng.",
            v[:60] + "…")
    return v, False


def _same(form, a: dict, b: dict) -> bool:
    for c in form.columns:
        if c.kind == "calc" or not c.letter:
            continue
        x, y = a.get(c.key), b.get(c.key)
        if c.kind in ("int", "float"):
            if isnum(x) != isnum(y) or (isnum(x) and abs(num(x) - num(y)) > 1e-9):
                return False
        elif s(x) != s(y):
            return False
    return True


# --------------------------------------------------------------------- phân tích
def analyze(path: str, project=None, codes=None) -> ImportReport:
    rep = ImportReport(path, checked_at=f"{datetime.now():%d/%m/%Y %H:%M}")
    codes = list(codes or INPUT_FORMS)
    name = os.path.basename(path)

    def fatal(msg, fix):
        rep.add(FATAL, "", "", "", name, msg, fix)
        rep.fatal = True
        return rep

    if not os.path.exists(path):
        return fatal("Không tìm thấy tệp.", "Chọn lại tệp.")
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xls", ".xlsb", ".ods", ".csv"):
        return fatal(f"Định dạng {ext} không được hỗ trợ.", "Mở bằng Excel → Lưu thành → Excel Workbook (*.xlsx).")
    if os.path.getsize(path) == 0:
        return fatal("Tệp rỗng (0 byte).", "Chọn đúng tệp đã điền.")
    if not zipfile.is_zipfile(path):
        return fatal("Tệp không phải Excel .xlsx hợp lệ (hỏng, có mật khẩu mở tệp hoặc tệp khác đổi đuôi).",
                     "Mở bằng Excel, bỏ mật khẩu và lưu lại dạng .xlsx.")
    try:
        wb_v = load_workbook(path, data_only=True)
        wb_f = load_workbook(path, data_only=False)
    except Exception as e:  # noqa: BLE001
        return fatal(f"Không đọc được tệp Excel: {e}.", "Đóng tệp nếu đang mở trong Excel và thử lại.")
    names = set(wb_v.sheetnames)
    known = [c for c in codes if FORMS[c].sheet in names]
    if not known:
        return fatal("Tệp không chứa trang tính nào của Bộ biểu VTVL.",
                     "Dùng đúng tệp Bộ biểu kèm Hướng dẫn 7-HD/BTCTW (nút “Tải biểu mẫu chuẩn”).")
    official = {"HD_DIEN_BIEU", "DM_THAM_SO"} <= names
    rep.version = "Bộ biểu VTVL kèm Hướng dẫn 7-HD/BTCTW" + (" (đủ trang tham số)" if official else "")
    if not official:
        rep.add(WARNING, "", "", "", name, "Thiếu trang HD_DIEN_BIEU/DM_THAM_SO.",
                "Dùng bản Bộ biểu phát hành chính thức; không xóa trang của bộ biểu.")
    if "DM_THAM_SO" in names and project is not None:
        q = wb_v["DM_THAM_SO"]["B3"].value
        if isnum(q) and abs(num(q) - project.quy_gio()) > 0.01:
            rep.add(WARNING, "DM_THAM_SO", "B3", "B", q, f"Quỹ giờ trong tệp khác hồ sơ ({project.quy_gio():g}).",
                    "Thống nhất quỹ giờ PP2 với cơ quan chủ trì.")
    for c in codes:
        if FORMS[c].sheet not in names:
            rep.sheets[c] = SheetResult(c, FORMS[c].sheet, found=False)

    for code in known:
        form = FORMS[code]
        sh = form.sheet
        res = SheetResult(code, sh, found=True)
        rep.sheets[code] = res
        ws_v, ws_f = wb_v[sh], wb_f[sh]
        wrong = []
        for col in form.columns:
            if col.letter:
                h = nfc(s(ws_v[f"{col.letter}2"].value))
                if h != col.label:
                    wrong.append(f"cột {col.letter} là “{h or '(trống)'}” – cần “{col.label}”")
        if wrong:
            res.structure_ok = False
            rep.add(ERROR, sh, "dòng 2", "", "", "Cấu trúc trang khác bộ biểu (không nhập trang này): "
                    + "; ".join(wrong[:3]) + ("…" if len(wrong) > 3 else ""),
                    "Dùng biểu mẫu chuẩn; không chèn, xóa, đổi tên cột.", code, 2)
            continue
        inputs = [c for c in form.columns if c.letter and c.kind != "calc"]
        calcs = [c for c in form.columns if c.letter and c.kind == "calc"]
        tpl_formula = {c.key: str(ws_f[f"{c.letter}{FIRST_ROW}"].value or "").startswith("=") for c in calcs}
        keycol = form.columns[0]
        empty_run = overwritten = 0
        for rr in range(FIRST_ROW, ws_v.max_row + 1):
            raw = {c.key: ws_v.cell(rr, column_index_from_string(c.letter)).value for c in inputs}
            if all(v is None or (isinstance(v, str) and not v.strip()) for v in raw.values()):
                empty_run += 1
                if empty_run > 50:
                    break
                continue
            empty_run = 0
            key = s(nfc(raw.get(keycol.key)))
            data, bad = {}, False
            for c in inputs:
                v, err = _convert(c, raw[c.key], rep, sh, rr, code, key)
                bad |= err
                if v is not None:
                    data[c.key] = v
            for c in calcs:
                fv = ws_f.cell(rr, column_index_from_string(c.letter)).value
                if fv not in (None, "") and not (isinstance(fv, str) and fv.startswith("=")) and tpl_formula[c.key]:
                    overwritten += 1
                    if overwritten <= 20:
                        rep.add(WARNING, sh, f"{c.letter}{rr}", c.letter, fv,
                                "Ô công thức (ô xám) bị nhập đè bằng giá trị.",
                                "Không nhập vào ô xám; phần mềm bỏ qua giá trị này và tự tính lại.", code, rr, c.label,
                                key)
            if not s(data.get(keycol.key)):
                rep.add(ERROR, sh, f"{keycol.letter}{rr}", keycol.letter, "",
                        f"Dòng có dữ liệu nhưng thiếu “{keycol.label}”.",
                        "Ghi mã cho dòng này hoặc xóa dòng thừa.", code, rr, keycol.label)
                bad = True
            missing = [c.label for c in inputs if c.required and c.key != keycol.key and c.key not in data]
            if missing and not bad:
                rep.add(INFO, sh, f"dòng {rr}", "", "", "Chưa nhập: " + "; ".join(missing[:5]) +
                        ("…" if len(missing) > 5 else "") + ".", "Bổ sung trước khi gửi (Bước 8 sẽ nhắc lại).",
                        code, rr, "", key)
            res.rows.append((rr, data))
            if bad:
                res.bad_rows.add(rr)
        if overwritten > 20:
            rep.add(WARNING, sh, "", "", "", f"Còn {overwritten - 20} ô công thức khác bị nhập đè.",
                    "Khôi phục công thức từ biểu mẫu chuẩn.", code)
        if res.n_rows > form.capacity:
            rep.add(WARNING, sh, "", "", res.n_rows, f"Có {res.n_rows} dòng, vượt sức chứa {form.capacity} dòng.",
                    "Báo đầu mối hỗ trợ kỹ thuật để mở rộng có kiểm soát.", code)
        kc = form_key(code)
        if kc and (form.key_col or code in ("DB", "D2")):
            cnt = Counter(tuple(s(d.get(k)) for k in kc) for _, d in res.rows if s(d.get(kc[0])))
            for rr, d in res.rows:
                k = tuple(s(d.get(x)) for x in kc)
                if k[0] and cnt[k] > 1:
                    letters = "/".join(form.col(x).letter for x in kc)
                    rep.add(ERROR, sh, f"{letters}{rr}", letters, " – ".join(k),
                            f"Trùng {'mã' if form.key_col else 'cặp mã – năm'} trong trang ({cnt[k]} lần).",
                            "Giữ một dòng; đổi mã hoặc xóa dòng trùng.", code, rr, "", k[0])
                    res.bad_rows.add(rr)
        # trùng với dòng đã có trong hồ sơ
        if project is not None and kc:
            existing = {}
            for r in project.rows(code):
                existing.setdefault(tuple(s(r.get(k)) for k in kc), r)
            same = []
            for rr, d in res.rows:
                if rr in res.bad_rows:
                    continue
                k = tuple(s(d.get(x)) for x in kc)
                if k[0] and k in existing:
                    letters = "/".join(form.col(x).letter for x in kc)
                    if _same(form, d, existing[k]):
                        same.append(rr)
                    else:
                        rep.add(WARNING, sh, f"{letters}{rr}", letters, " – ".join(k),
                                "Trùng với dòng đã có trong hồ sơ.",
                                "Kết chuyển sẽ cập nhật dòng đã có; đổi mã hoặc xóa dòng đã có nếu muốn lưu thành "
                                "dòng mới.", code, rr, "", k[0])
                        res.review_rows.add(rr)
            if same:
                rep.add(INFO, sh, f"{len(same)} dòng", "", "",
                        f"{len(same)} dòng đã có trong hồ sơ với nội dung giống hệt (kết chuyển không làm thay đổi).",
                        "Không cần xử lý.", code)

    def keys_of(target):
        r = rep.sheets.get(target)
        if r and r.found and r.structure_ok and r.rows:
            return {s(d.get("ma")) for rr, d in r.rows if rr not in r.bad_rows}
        return {s(x.get("ma")) for x in project.rows(target)} if project is not None else set()

    target_keys = {t: keys_of(t) for t in REF_TARGET_KEY}
    for code, res in rep.sheets.items():
        if not res.found or not res.structure_ok:
            continue
        for col in FORMS[code].columns:
            if col.kind != "ref" or col.ref not in target_keys:
                continue
            missing, first = Counter(), {}
            for rr, d in res.rows:
                v = s(d.get(col.key))
                if v and v not in target_keys[col.ref]:
                    missing[v] += 1
                    first.setdefault(v, rr)
            for v, n in missing.items():
                rep.add(WARNING, res.sheet, f"{col.letter}{first[v]}", col.letter, v,
                        f"Mã chưa có ở biểu {col.ref}" + (f" ({n} dòng)" if n > 1 else "") + ".",
                        f"Bổ sung mã {v} vào Biểu {col.ref} hoặc sửa lại mã cho đúng.", code, first[v], col.label, v)
                res.review_rows.add(first[v])
    rep.issues.sort(key=lambda i: (LEVEL_ORDER[i.level], i.sheet, i.row))
    return rep


# ------------------------------------------------------------------------ ghi
def backup_before_import(project, prefix="TruocKhiNhap") -> str:
    from .db import app_data_dir
    d = os.path.join(app_data_dir(), "SaoLuu")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{prefix}_{datetime.now():%Y%m%d_%H%M%S_%f}.vtvl")
    project.backup(path)
    files = sorted(f for f in os.listdir(d) if f.startswith(prefix + "_"))
    for f in files[:-20]:
        try:
            os.remove(os.path.join(d, f))
        except OSError:
            pass
    return path


def apply(project, rep: ImportReport, codes, mode="replace", skip_errors=True) -> dict:
    """KẾT CHUYỂN: ghi dữ liệu đã kiểm tra vào hồ sơ (sao lưu trước). mode: 'replace' | 'merge'."""
    if not rep.importable(codes, skip_errors):
        raise ValueError("Tệp còn lỗi không cho phép kết chuyển.")
    bk = backup_before_import(project)
    project.set_meta("last_import_backup", bk, notify=False)
    project.set_meta("last_import", f"{datetime.now():%d/%m/%Y %H:%M} – {os.path.basename(rep.path)}", notify=False)
    stats = {}
    for code in codes:
        res = rep.sheets[code]
        form = FORMS[code]
        rows = [d for rr, d in res.rows if not (skip_errors and rr in res.bad_rows)]
        skipped = res.n_rows - len(rows)
        if mode == "replace":
            project.replace_rows(code, rows)
            stats[code] = {"added": len(rows), "updated": 0, "skipped": skipped}
            continue
        kc = form_key(code)
        existing = {}
        for r in project.rows(code):
            existing.setdefault(tuple(s(r.get(k)) for k in kc), r)
        added = updated = 0
        for d in rows:
            k = tuple(s(d.get(x)) for x in kc)
            if kc and k in existing:
                project.update_row(existing[k]["_id"],
                                   {c.key: d.get(c.key) for c in form.columns if c.kind != "calc" and c.letter},
                                   notify=False)
                updated += 1
            else:
                project.add_row(code, d, notify=False)
                added += 1
        project._notify(code)
        stats[code] = {"added": added, "updated": updated, "skipped": skipped}
    if hasattr(project, "log"):
        detail = "; ".join(f"{c}: +{v['added']}" + (f", cập nhật {v['updated']}" if v["updated"] else "") +
                           (f", bỏ {v['skipped']}" if v["skipped"] else "") for c, v in stats.items())
        project.log("Kết chuyển từ Excel", f"{os.path.basename(rep.path)} ({'thay thế' if mode == 'replace' else 'bổ sung'}"
                    f"): {detail}", backup=bk)
    return stats


def undo_last_import(project) -> bool:
    bk = project.get_meta("last_import_backup", "")
    if not bk or not os.path.exists(bk):
        return False
    project.restore_from(bk)
    project.set_meta("last_import_backup", "", notify=False)
    if hasattr(project, "log"):
        project.log("Hoàn tác kết chuyển", os.path.basename(bk))
    return True


# ------------------------------------------------------------------ tệp kết quả
def export_issues(rep: ImportReport, path: str):
    """Danh sách lỗi dạng bảng (một trang)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "KetQuaKiemTra"
    ws.append([f"Kết quả kiểm tra tệp: {os.path.basename(rep.path)} – {rep.checked_at}"])
    ws.append([f"Tổng số dòng: {rep.total_rows}; dòng có lỗi: {rep.error_rows}; dòng hợp lệ: {rep.valid_rows}"])
    ws.append([])
    ws.append(["Mức", "Trang tính", "Ô", "Cột", "Tên cột", "Giá trị", "Nội dung", "Cách xử lý"])
    head = ws.max_row
    for i in rep.issues:
        ws.append([i.level, i.sheet, i.cell, i.column, i.label, i.value, i.message, i.fix])
    for c in ws[head]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DCE6F1")
    for col, w in zip("ABCDEFGH", (14, 20, 10, 6, 24, 24, 60, 60)):
        ws.column_dimensions[col].width = w
    wb.save(path)


def export_annotated(rep: ImportReport, path: str) -> int:
    """Bản sao tệp đã tải lên kèm CỘT BÁO LỖI ở mỗi trang, tô màu ô lỗi và ghi chú tại ô. Trả về số ô được đánh dấu."""
    from openpyxl.comments import Comment
    from openpyxl.styles import Font, PatternFill
    wb = load_workbook(rep.path)
    red, amber = PatternFill("solid", fgColor="F8CBAD"), PatternFill("solid", fgColor="FFE699")
    by_sheet = {}
    for i in rep.issues:
        if i.sheet and i.sheet in wb.sheetnames:
            by_sheet.setdefault(i.sheet, []).append(i)
    marked = 0
    for sheet, items in by_sheet.items():
        ws = wb[sheet]
        last = ws.max_column + 1
        if ws.cell(2, last - 1).value == "KẾT QUẢ KIỂM TRA":
            last -= 1
        letter = get_column_letter(last)
        ws.cell(2, last, "KẾT QUẢ KIỂM TRA").font = Font(bold=True, color="C00000")
        ws.column_dimensions[letter].width = 70
        per_row = {}
        for i in items:
            if i.row >= FIRST_ROW:
                per_row.setdefault(i.row, []).append(i)
            if i.level in (ERROR, WARNING) and i.cell and i.column and i.row >= FIRST_ROW and "/" not in i.column:
                c = ws[f"{i.column}{i.row}"]
                c.fill = red if i.level == ERROR else amber
                c.comment = Comment(f"{i.level}: {i.message}\nCách xử lý: {i.fix}", "QL-VTVL")
                marked += 1
        for rr, lst in per_row.items():
            lst = [x for x in lst if x.level != INFO] or lst
            txt = " | ".join(f"[{x.level}] {x.cell}: {x.message} → {x.fix}" for x in lst)
            cell = ws.cell(rr, last, txt)
            if any(x.level == ERROR for x in lst):
                cell.font = Font(color="C00000")
                cell.fill = red
            elif any(x.level == WARNING for x in lst):
                cell.fill = amber
    if hasattr(wb, "_external_links"):
        wb._external_links = []
    wb.save(path)
    return marked


def save_blank_template(project, path: str):
    """Biểu mẫu chuẩn (đã sửa các công thức lỗi của bản phát hành), chưa có dữ liệu."""
    from .exporter import repair_template, template_path
    wb = load_workbook(template_path(project))
    repair_template(wb)
    wb.save(path)
