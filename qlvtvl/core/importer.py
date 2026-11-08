"""Kiểm soát lỗi khi nhập (upload) tệp Bộ biểu Excel.

Quy trình: ``analyze()`` đọc tệp, kiểm tra 3 lớp (tệp – ô – liên kết) và trả về báo cáo kèm dữ liệu đã chuẩn hóa;
người dùng xem trước; ``apply()`` sao lưu hồ sơ rồi mới ghi dữ liệu (thay thế hoặc bổ sung/cập nhật theo mã).
"""
from __future__ import annotations

import os
import shutil
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

from .calc import isnum, num, s
from .forms import FORMS, INPUT_FORMS, YEARS

FATAL, ERROR, WARNING, INFO = "Không nhập được", "Lỗi", "Cảnh báo", "Lưu ý"
LEVEL_ORDER = {FATAL: 0, ERROR: 1, WARNING: 2, INFO: 3}
FIRST_ROW = 3
MAX_TEXT = 2000
EXCEL_ERRORS = ("#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#NUM!", "#NULL!", "#SPILL!", "#CALC!")
# các cột số được phép âm
NEGATIVE_OK = {"de_nghi", "bien_dong"}
# khóa ghép để bổ sung/cập nhật theo mã với các biểu không có mã riêng
MERGE_KEYS = {
    "B1": ("ma_cv", "ma_sp"),
    "B2": ("ma_cv", "cong_doan", "ky"),
    "DB": ("ma_vt", "nam"),
    "D2": ("ma_vt", "nam"),
}
REF_TARGET_KEY = {"A1": "ma", "A2": "ma", "C1": "ma", "DM": "ma"}


def nfc(v):
    return unicodedata.normalize("NFC", v) if isinstance(v, str) else v


@dataclass
class ImportIssue:
    level: str
    sheet: str
    cell: str
    column: str
    value: str
    message: str
    code: str = ""


@dataclass
class SheetResult:
    code: str
    sheet: str
    found: bool = False
    structure_ok: bool = True
    rows: list = field(default_factory=list)       # [(excel_row, data)]
    bad_rows: set = field(default_factory=set)     # excel_row có lỗi

    @property
    def n_rows(self):
        return len(self.rows)

    @property
    def n_ok(self):
        return sum(1 for r, _ in self.rows if r not in self.bad_rows)


@dataclass
class ImportReport:
    path: str
    issues: list = field(default_factory=list)
    sheets: dict = field(default_factory=dict)
    fatal: bool = False
    version: str = ""

    def add(self, level, sheet, cell, column, value, message, code=""):
        v = "" if value is None else str(value)
        self.issues.append(ImportIssue(level, sheet, cell, column, v[:120], message, code))

    def count(self, level, code=None):
        return sum(1 for i in self.issues if i.level == level and (code is None or i.code == code))

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
def _convert(col, raw, rep, sheet, cell, code):
    """Trả về (giá trị chuẩn hóa, có_lỗi)."""
    v = nfc(raw)
    if isinstance(v, str):
        v = v.strip()
        if v.upper() in EXCEL_ERRORS:
            rep.add(ERROR, sheet, cell, col.label, raw, "Ô chứa giá trị lỗi của Excel.", code)
            return None, True
    if v is None or v == "":
        return None, False
    if col.kind in ("int", "float"):
        if isinstance(v, bool) or not isnum(v):
            rep.add(ERROR, sheet, cell, col.label, raw, "Phải là số (ví dụ 1904 hoặc 2,5).", code)
            return None, True
        f = num(v)
        if f < 0 and col.key not in NEGATIVE_OK:
            rep.add(ERROR, sheet, cell, col.label, raw, "Không được là số âm.", code)
            return None, True
        return (int(round(f)) if col.kind == "int" else f), False
    if col.key == "nam":
        if not isnum(v) or num(v) != int(num(v)) or int(num(v)) not in YEARS:
            rep.add(ERROR, sheet, cell, col.label, raw, "Năm phải là 2027, 2028, 2029, 2030 hoặc 2031.", code)
            return None, True
        return str(int(num(v))), False
    if isinstance(v, (datetime, date)):
        txt = v.strftime("%d/%m/%Y")
        rep.add(INFO, sheet, cell, col.label, txt, "Ô kiểu ngày tháng – đã chuyển thành văn bản dd/mm/yyyy.", code)
        return txt, False
    if isinstance(v, float):
        v = str(int(v)) if v.is_integer() else str(v)
    elif not isinstance(v, str):
        v = str(v)
    if col.kind == "choice":
        if v not in col.options:
            match = [o for o in col.options if o.casefold() == v.casefold() or
                     " ".join(o.split()).casefold() == " ".join(v.split()).casefold()]
            if match:
                rep.add(INFO, sheet, cell, col.label, raw, f"Đã chuẩn hóa thành “{match[0]}”.", code)
                return match[0], False
            rep.add(WARNING, sheet, cell, col.label, raw,
                    "Không thuộc danh sách lựa chọn của bộ biểu (" + "; ".join(col.options[:6]) +
                    ("…" if len(col.options) > 6 else "") + "). Vẫn nhập, cột cảnh báo của biểu sẽ báo.", code)
    if len(v) > MAX_TEXT:
        rep.add(WARNING, sheet, cell, col.label, v[:60] + "…", f"Nội dung dài {len(v)} ký tự (nên ≤ {MAX_TEXT}).", code)
    return v, False


# --------------------------------------------------------------------- phân tích
def analyze(path: str, project=None, codes=None) -> ImportReport:
    rep = ImportReport(path)
    codes = list(codes or INPUT_FORMS)
    name = os.path.basename(path)
    # ---- lớp 1: tệp
    if not os.path.exists(path):
        rep.add(FATAL, "", "", "", name, "Không tìm thấy tệp.")
        rep.fatal = True
        return rep
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xls", ".xlsb", ".ods", ".csv"):
        rep.add(FATAL, "", "", "", name, f"Định dạng {ext} không được hỗ trợ. Mở tệp bằng Excel và “Lưu thành” "
                                          "Excel Workbook (*.xlsx).")
        rep.fatal = True
        return rep
    if os.path.getsize(path) == 0:
        rep.add(FATAL, "", "", "", name, "Tệp rỗng (0 byte).")
        rep.fatal = True
        return rep
    if not zipfile.is_zipfile(path):
        rep.add(FATAL, "", "", "", name, "Tệp không phải Excel .xlsx hợp lệ: có thể bị hỏng, được đặt mật khẩu mở tệp, "
                                          "hoặc là tệp khác đổi đuôi. Mở bằng Excel, bỏ mật khẩu và lưu lại dạng .xlsx.")
        rep.fatal = True
        return rep
    try:
        wb_v = load_workbook(path, data_only=True)
        wb_f = load_workbook(path, data_only=False)
    except Exception as e:  # noqa: BLE001
        rep.add(FATAL, "", "", "", name, f"Không đọc được tệp Excel: {e}. Hãy đóng tệp nếu đang mở và thử lại.")
        rep.fatal = True
        return rep
    names = set(wb_v.sheetnames)
    known = [c for c in codes if FORMS[c].sheet in names]
    if not known:
        rep.add(FATAL, "", "", "", name, "Tệp không chứa trang tính nào của Bộ biểu VTVL (ví dụ “1. A1_NhiemVu”, "
                                          "“6. C1_VTVL”). Hãy dùng đúng tệp Bộ biểu kèm Hướng dẫn 7-HD/BTCTW.")
        rep.fatal = True
        return rep
    official = {"HD_DIEN_BIEU", "DM_THAM_SO"} <= names
    rep.version = "Bộ biểu VTVL kèm Hướng dẫn 7-HD/BTCTW" + (" (đủ trang tham số)" if official else "")
    if not official:
        rep.add(WARNING, "", "", "", name, "Không thấy trang HD_DIEN_BIEU/DM_THAM_SO: tệp có thể không phải bản phát "
                                            "hành chính thức hoặc đã bị xóa bớt trang.")
    if "DM_THAM_SO" in names and project is not None:
        q = wb_v["DM_THAM_SO"]["B3"].value
        if isnum(q) and abs(num(q) - project.quy_gio()) > 0.01:
            rep.add(WARNING, "DM_THAM_SO", "B3", "Quỹ giờ PP2", q,
                    f"Quỹ giờ trong tệp ({q}) khác quỹ giờ của hồ sơ ({project.quy_gio():g}).")
    for c in codes:
        if FORMS[c].sheet not in names:
            rep.sheets[c] = SheetResult(c, FORMS[c].sheet, found=False)

    # ---- lớp 2: từng trang, từng ô
    for code in known:
        form = FORMS[code]
        sh = form.sheet
        res = SheetResult(code, sh, found=True)
        rep.sheets[code] = res
        ws_v, ws_f = wb_v[sh], wb_f[sh]
        # cấu trúc: dòng tiêu đề 2
        wrong = []
        for col in form.columns:
            if not col.letter:
                continue
            h = nfc(s(ws_v[f"{col.letter}2"].value))
            if h != col.label:
                wrong.append(f"cột {col.letter} là “{h or '(trống)'}” – cần “{col.label}”")
        if wrong:
            res.structure_ok = False
            rep.add(ERROR, sh, "dòng 2", "", "", "Cấu trúc trang khác bộ biểu (không nhập trang này): "
                    + "; ".join(wrong[:4]) + ("…" if len(wrong) > 4 else "") +
                    ". Không chèn/xóa/đổi tên cột của bộ biểu.", code)
            continue
        inputs = [c for c in form.columns if c.letter and c.kind != "calc"]
        calcs = [c for c in form.columns if c.letter and c.kind == "calc"]
        key = form.columns[0]
        empty_run = 0
        max_row = ws_v.max_row
        overwritten = 0
        for rr in range(FIRST_ROW, max_row + 1):
            raw = {c.key: ws_v.cell(rr, column_index_from_string(c.letter)).value for c in inputs}
            if all(v is None or (isinstance(v, str) and not v.strip()) for v in raw.values()):
                empty_run += 1
                if empty_run > 50:
                    break
                continue
            empty_run = 0
            data, bad = {}, False
            for c in inputs:
                v, err = _convert(c, raw[c.key], rep, sh, f"{c.letter}{rr}", code)
                bad |= err
                if v is not None:
                    data[c.key] = v
            # ô công thức bị nhập đè
            for c in calcs:
                fv = ws_f.cell(rr, column_index_from_string(c.letter)).value
                tpl_formula = isinstance(ws_f.cell(FIRST_ROW, column_index_from_string(c.letter)).value, str) and \
                    str(ws_f.cell(FIRST_ROW, column_index_from_string(c.letter)).value).startswith("=")
                if fv not in (None, "") and not (isinstance(fv, str) and fv.startswith("=")) and tpl_formula:
                    overwritten += 1
                    if overwritten <= 20:
                        rep.add(WARNING, sh, f"{c.letter}{rr}", c.label, fv,
                                "Ô công thức (ô xám) bị nhập đè bằng giá trị – phần mềm bỏ qua và tự tính lại.", code)
            if not s(data.get(key.key)):
                rep.add(ERROR, sh, f"{key.letter}{rr}", key.label, "",
                        f"Dòng có dữ liệu nhưng thiếu “{key.label}” – không xác định được bản ghi.", code)
                bad = True
            missing = [c.label for c in inputs if c.required and c.key != key.key and c.key not in data]
            if missing and not bad:
                rep.add(INFO, sh, f"dòng {rr}", "", "", "Chưa nhập: " + "; ".join(missing[:5]) +
                        ("…" if len(missing) > 5 else "") + " (sẽ báo ở Bước 8).", code)
            res.rows.append((rr, data))
            if bad:
                res.bad_rows.add(rr)
        if overwritten > 20:
            rep.add(WARNING, sh, "", "", "", f"Còn {overwritten - 20} ô công thức khác bị nhập đè.", code)
        if res.n_rows > form.capacity:
            rep.add(WARNING, sh, "", "", res.n_rows,
                    f"Có {res.n_rows} dòng, vượt sức chứa {form.capacity} dòng của bộ biểu.", code)
        if res.n_rows == 0:
            rep.add(INFO, sh, "", "", "", "Trang không có dữ liệu.", code)
        # trùng mã / trùng khóa
        kc = (form.key_col,) if form.key_col else MERGE_KEYS.get(code)
        uniq = form.key_col or code in ("DB", "D2")
        if kc and uniq:
            cnt = Counter(tuple(s(d.get(k)) for k in kc) for rr, d in res.rows if s(d.get(kc[0])))
            for rr, d in res.rows:
                k = tuple(s(d.get(x)) for x in kc)
                if k[0] and cnt[k] > 1:
                    letters = "/".join(form.col(x).letter for x in kc)
                    rep.add(ERROR, sh, f"{letters}{rr}", "", " – ".join(k),
                            f"Trùng {'mã' if form.key_col else 'cặp mã – năm'} trong trang ({cnt[k]} lần).", code)
                    res.bad_rows.add(rr)

    # ---- lớp 3: liên kết mã
    def keys_of(target):
        r = rep.sheets.get(target)
        if r and r.found and r.structure_ok and r.rows:
            return {s(d.get("ma")) for rr, d in r.rows if rr not in r.bad_rows}
        if project is not None:
            return {s(x.get("ma")) for x in project.rows(target)}
        return set()

    target_keys = {t: keys_of(t) for t in REF_TARGET_KEY}
    for code, res in rep.sheets.items():
        if not res.found or not res.structure_ok:
            continue
        form = FORMS[code]
        for col in form.columns:
            if col.kind != "ref" or col.ref not in target_keys:
                continue
            missing = Counter()
            first = {}
            for rr, d in res.rows:
                v = s(d.get(col.key))
                if v and v not in target_keys[col.ref]:
                    missing[v] += 1
                    first.setdefault(v, rr)
            for v, n in missing.items():
                rep.add(WARNING, res.sheet, f"{col.letter}{first[v]}", col.label, v,
                        f"Mã chưa có ở biểu {col.ref}" + (f" ({n} dòng)" if n > 1 else "") +
                        " – vẫn nhập, cần bổ sung biểu gốc.", code)
    rep.issues.sort(key=lambda i: (LEVEL_ORDER[i.level], INPUT_FORMS.index(i.code) if i.code in INPUT_FORMS else -1))
    return rep


# ------------------------------------------------------------------------ ghi
def backup_before_import(project) -> str:
    from .db import app_data_dir
    d = os.path.join(app_data_dir(), "SaoLuu")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"TruocKhiNhap_{datetime.now():%Y%m%d_%H%M%S}.vtvl")
    project.backup(path)
    # giữ 20 bản gần nhất
    files = sorted(f for f in os.listdir(d) if f.startswith("TruocKhiNhap_"))
    for f in files[:-20]:
        try:
            os.remove(os.path.join(d, f))
        except OSError:
            pass
    return path


def apply(project, rep: ImportReport, codes, mode="replace", skip_errors=True) -> dict:
    """Ghi dữ liệu đã kiểm tra vào hồ sơ. mode: 'replace' | 'merge'. Trả về thống kê từng biểu."""
    if not rep.importable(codes, skip_errors):
        raise ValueError("Tệp còn lỗi không cho phép nhập.")
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
        kc = (form.key_col,) if form.key_col else MERGE_KEYS.get(code, ())
        existing = {}
        for r in project.rows(code):
            existing.setdefault(tuple(s(r.get(k)) for k in kc), r)
        added = updated = 0
        for d in rows:
            k = tuple(s(d.get(x)) for x in kc)
            if kc and k in existing:
                cur = existing[k]
                new = {c.key: d.get(c.key) for c in form.columns if c.kind != "calc" and c.letter}
                project.update_row(cur["_id"], new, notify=False)
                updated += 1
            else:
                project.add_row(code, d, notify=False)
                added += 1
        project._notify(code)
        stats[code] = {"added": added, "updated": updated, "skipped": skipped}
    return stats


def undo_last_import(project) -> bool:
    bk = project.get_meta("last_import_backup", "")
    if not bk or not os.path.exists(bk):
        return False
    project.restore_from(bk)
    project.set_meta("last_import_backup", "", notify=False)
    return True


def export_issues(rep: ImportReport, path: str):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "KetQuaKiemTra"
    ws.append([f"Kết quả kiểm tra tệp: {os.path.basename(rep.path)}"])
    ws.append([f"Thời điểm: {datetime.now():%d/%m/%Y %H:%M}"])
    ws.append([])
    ws.append(["Biểu", "Trang tính", "Số dòng", "Dòng lỗi", "Dòng nhập được"])
    for code, r in rep.sheets.items():
        ws.append([code, r.sheet, r.n_rows if r.found else "không có trang",
                   len(r.bad_rows), r.n_ok if r.structure_ok else 0])
    ws.append([])
    ws.append(["Mức độ", "Trang tính", "Ô", "Cột", "Giá trị", "Nội dung lỗi / hướng xử lý"])
    head = ws.max_row
    for i in rep.issues:
        ws.append([i.level, i.sheet, i.cell, i.column, i.value, i.message])
    for row in (4, head):
        for c in ws[row]:
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor="DCE6F1")
    for col, w in zip("ABCDEF", (16, 22, 12, 30, 30, 100)):
        ws.column_dimensions[col].width = w
    wb.save(path)


def copy_file(src, dst):
    shutil.copyfile(src, dst)
