"""Xuất dữ liệu vào Bộ biểu Excel chính thức (Bộ biểu VTVL 19-10-2026), nhập ngược lại; xuất báo cáo Word."""
from __future__ import annotations

import os
import re
import sys
from datetime import date

from openpyxl import load_workbook

from .calc import Calculator, fmt, isnum, num, s
from .checks import ERROR, WARNING, run_checks
from .forms import FORMS, INPUT_FORMS, NINE, YEARS

TEMPLATE_NAME = "BoBieu_VTVL_19-10-2026.xlsx"
FIRST_ROW = 3
# các trang dữ liệu có công thức theo dòng: chuẩn hóa mọi dòng theo công thức dòng 3
DATA_SHEETS = ("2. A2_CongViec", "3. B1_KhoiLuong", "4. B2_CT_TacDong", "5. B2_ThayDoi", "6. C1_VTVL",
               "8. C3_NhuCau", "9. D1_NhanLuc", "10. D2_PhuongAn", "DU_BAO_5_NAM")


def bundled_template() -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = os.path.join(base, "qlvtvl", "assets", TEMPLATE_NAME)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", TEMPLATE_NAME)


def template_path(project=None) -> str:
    custom = project.get_meta("template_path", "") if project else ""
    if custom and os.path.exists(custom):
        return custom
    return bundled_template()


# ------------------------------------------------------------ công thức
_REF = re.compile(r"(?<![A-Za-z0-9_$.])(\$?)([A-Z]{1,3})(\$?)(\d+)(?![\d(A-Za-z_])")


def shift_formula(formula: str, delta: int) -> str:
    """Dịch các tham chiếu dòng tương đối của công thức đi ``delta`` dòng (bỏ qua chuỗi và tên trang tính)."""
    out, i, n = [], 0, len(formula)
    while i < n:
        ch = formula[i]
        if ch in "'\"":
            j = i + 1
            while j < n:
                if formula[j] == ch:
                    if j + 1 < n and formula[j + 1] == ch:
                        j += 2
                        continue
                    break
                j += 1
            out.append(formula[i:j + 1])
            i = j + 1
            continue
        j = i
        while j < n and formula[j] not in "'\"":
            j += 1
        seg = formula[i:j]

        def rep(m):
            if m.group(3):
                return m.group(0)
            return f"{m.group(1)}{m.group(2)}{int(m.group(4)) + delta}"

        out.append(_REF.sub(rep, seg))
        i = j
    return "".join(out)


def repair_template(wb) -> int:
    """Chuẩn hóa công thức của bản phát hành: mọi dòng dữ liệu dùng đúng công thức dòng 3.

    Bản 19-10-2026 có các lỗi: C3!M4:M202, D2!J4:J202, DU_BAO!G4:G1002 trỏ tới tệp ngoài ([1], [399]...);
    DU_BAO!I và D2!J có chuỗi thông báo bị đánh số theo dòng ("C4 CHƯA ĐƯỢC XÁC NHẬN"...);
    C1!E35:E202 gọi tên QUY_GIO_PP34... thay cho QUY_GIO_PP2. Trả về số ô đã sửa.
    """
    fixed = 0
    for sheet in DATA_SHEETS:
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        for col in range(1, ws.max_column + 1):
            base = ws.cell(FIRST_ROW, col).value
            if not (isinstance(base, str) and base.startswith("=")):
                continue
            for row in range(FIRST_ROW + 1, ws.max_row + 1):
                cell = ws.cell(row, col)
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    expected = shift_formula(base, row - FIRST_ROW)
                    if cell.value != expected:
                        cell.value = expected
                        fixed += 1
    if hasattr(wb, "_external_links"):
        wb._external_links = []
    return fixed


def _excel_value(col, v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    if col.kind in ("int", "float"):
        return num(v) if isnum(v) else None
    if col.key == "nam" and isnum(v):
        return int(num(v))
    return v


def export_official(project, path: str, tpl: str | None = None) -> dict:
    """Ghi dữ liệu vào bản sao Bộ biểu Excel chính thức; giữ nguyên công thức, danh sách chọn, bảo vệ trang."""
    calc = Calculator(project)
    wb = load_workbook(tpl or template_path(project))
    info = {"fixed": repair_template(wb), "rows": {}, "overflow": {}}
    for code in INPUT_FORMS:
        form = FORMS[code]
        if form.sheet not in wb.sheetnames:
            continue
        ws = wb[form.sheet]
        rows = calc.rows[code]
        cap_last = FIRST_ROW + form.capacity - 1
        for idx, r in enumerate(rows):
            rr = FIRST_ROW + idx
            for col in form.columns:
                if not col.letter:
                    continue
                cell = ws[f"{col.letter}{rr}"]
                if col.kind == "calc":
                    if rr > cap_last or not (isinstance(cell.value, str) and str(cell.value).startswith("=")):
                        # ngoài sức chứa của bộ biểu: ghi giá trị đã tính
                        v = calc.value(code, r, col.key)
                        cell.value = None if v == "" else v
                    continue
                cell.value = _excel_value(col, r.get(col.key))
        info["rows"][code] = len(rows)
        if len(rows) > form.capacity:
            info["overflow"][code] = len(rows) - form.capacity
    meta = project.meta()
    if "14. T_TienDo" in wb.sheetnames:
        ws = wb["14. T_TienDo"]
        ws["A3"] = meta.get("ten_don_vi", "")
        ws["B3"] = meta.get("ky_thong_ke", "")
    if "DM_THAM_SO" in wb.sheetnames and abs(calc.quy - 1904) > 0.01:
        wb["DM_THAM_SO"]["B3"] = calc.quy
    try:
        wb.calculation.fullCalcOnLoad = True
    except AttributeError:
        pass
    wb.save(path)
    return info


export_excel = export_official


# ----------------------------------------------------------------- nhập
def import_official(project, path: str, codes=None, mode="replace") -> dict:
    """Nhập từ Bộ biểu Excel chính thức qua bộ kiểm soát lỗi (bỏ qua dòng lỗi, có sao lưu trước khi nhập)."""
    from .importer import analyze, apply
    rep = analyze(path, project, codes)
    if rep.fatal:
        raise ValueError("; ".join(i.message for i in rep.issues if i.level == "Không nhập được"))
    ok = [c for c, r in rep.sheets.items() if r.found and r.structure_ok]
    stats = apply(project, rep, ok, mode=mode, skip_errors=True)
    return {c: v["added"] + v["updated"] for c, v in stats.items()}


import_excel = import_official


# ------------------------------------------------------------------ Word
def export_word(project, path: str):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    calc = Calculator(project)
    meta = project.meta()
    sm = calc.summary()
    issues = run_checks(project, calc)
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(13)
    st.element.rPr.rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia",
                              "Times New Roman")
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(3), Cm(2), Cm(2), Cm(2)

    def para(text="", bold=False, italic=False, align=None, size=None, after=6, indent=False):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold, run.italic = bold, italic
        if size:
            run.font.size = Pt(size)
        p.alignment = {"center": WD_ALIGN_PARAGRAPH.CENTER, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
                       "right": WD_ALIGN_PARAGRAPH.RIGHT}.get(align)
        p.paragraph_format.space_after = Pt(after)
        if indent:
            p.paragraph_format.first_line_indent = Cm(1)
        return p

    def table(headers, data, size=10):
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, h in enumerate(headers):
            c = t.rows[0].cells[j]
            run = c.paragraphs[0].add_run(h)
            run.bold = True
            run.font.size = Pt(size)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for row in data:
            cells = t.add_row().cells
            for j, v in enumerate(row):
                run = cells[j].paragraphs[0].add_run(str(v))
                run.font.size = Pt(size)
        doc.add_paragraph()

    head = doc.add_table(rows=2, cols=2)
    for r_, c_, text, bold in ((0, 0, meta.get("co_quan_chu_quan", "").upper(), False),
                               (1, 0, meta.get("ten_don_vi", "").upper(), True),
                               (0, 1, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", True),
                               (1, 1, "Độc lập - Tự do - Hạnh phúc", True)):
        p = head.cell(r_, c_).paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = bold
        run.font.size = Pt(12)
    today = date.today()
    para(f"Cần Thơ, ngày {today.day:02d} tháng {today.month:02d} năm {today.year}", italic=True, align="right")
    para("BÁO CÁO", bold=True, align="center", size=14, after=0)
    para("Kết quả rà soát, hoàn thiện vị trí việc làm, xác định nhu cầu nhân lực và xây dựng phương án "
         "số lượng người làm việc giai đoạn 2027 - 2031", bold=True, align="center", size=14)

    para("I. CĂN CỨ THỰC HIỆN", bold=True)
    for r in project.rows("CC"):
        if r.get("hieu_luc", "Đang áp dụng") == "Đang áp dụng":
            ngay = f" ngày {r.get('ngay')}" if s(r.get("ngay")) else ""
            para(f"- {r.get('so_hieu', '')}{ngay} của {r.get('co_quan', '')}: {r.get('trich_yeu', '')}",
                 align="justify", indent=True, after=3)
    para(f"Kỳ thống kê khối lượng, thời gian: {meta.get('ky_thong_ke', '')}; nhân lực hiện có chốt tại ngày "
         f"{meta.get('ngay_chot', '')}.", align="justify", indent=True)

    para("II. KẾT QUẢ RÀ SOÁT NHIỆM VỤ, CÔNG VIỆC, KHỐI LƯỢNG (Bước 1 – 4)", bold=True)
    para(f"Rà soát {sm['nv']} nhiệm vụ (Biểu A1), phân rã thành {sm['cv']} công việc gắn sản phẩm và vị trí việc "
         f"làm (Biểu A2). Tổng giờ lao động đủ căn cứ (dòng B1 đạt): {fmt(sm['hours'])} giờ; tác động ròng của "
         f"chuyển đổi số, tự chủ, thuê dịch vụ, xã hội hóa đã kiểm chứng (B2): {fmt(sm['delta'])} giờ; giờ ròng: "
         f"{fmt(sm['net'])} giờ.", align="justify", indent=True)

    para("III. DANH MỤC VỊ TRÍ VIỆC LÀM (Bước 5)", bold=True)
    para(f"Tổng số {sm['vt']} vị trí việc làm, theo loại nhân lực:", indent=True)
    for g, v in sm["by_group"].items():
        para(f"- {g}: {v['vt']} vị trí.", indent=True, after=2)

    para("IV. NHU CẦU NHÂN LỰC THEO VỊ TRÍ VIỆC LÀM (Bước 6)", bold=True)
    para(f"Quỹ thời gian quy đổi PP2: {fmt(calc.quy)} giờ/người/năm. Người quy đổi PP2 = Giờ ròng ÷ Quỹ giờ; "
         "không tự làm tròn thành biên chế; kết quả tính không tự động làm tăng biên chế.", align="justify",
         indent=True)
    data = []
    for i, r in enumerate(calc.rows["C3"], 1):
        o = calc.v[r["_id"]]
        data.append((i, s(r.get("ma_vt")), o["ten_vt"], s(r.get("pp")), fmt(o["gio_rong"]), fmt(o["nguoi_qd"], 3),
                     fmt(r.get("nguoi_can"), 3) if isnum(r.get("nguoi_can")) else "", o["canh_bao"]))
    data.append(("", "", "Tổng cộng", "", fmt(sm["net"]), fmt(sm["qd"], 3), fmt(sm["need"], 3), ""))
    table(("STT", "Mã", "Vị trí việc làm", "PP", "Giờ ròng", "Người quy đổi", "Người cần bố trí", "Cảnh báo"), data)

    para("V. ĐỐI CHIẾU NHÂN LỰC HIỆN CÓ VÀ PHƯƠNG ÁN 2027 - 2031 (Bước 7)", bold=True)
    giao = meta.get("bc_giao", "")
    para(f"Nhu cầu (C3): {fmt(sm['need'], 3)} người; nhân lực hiện có (D1): {sm['existing']} người "
         f"(tương đương {fmt(sm['existing_qd'], 3)} người quy đổi)"
         + (f"; số lượng người làm việc được giao: {giao}" if giao else "") + ".", align="justify", indent=True)
    data = []
    for y in YEARS:
        data.append((y, fmt(sm["plan"][y], 3), fmt(sm["avail"][y], 3), fmt(sm["req"][y], 3)))
    table(("Năm", "Số người cần bố trí", "Số người có thể bố trí", "Đề nghị điều chỉnh"), data, 11)

    para("VI. NỘI DUNG CHƯA ĐỦ CĂN CỨ, CẦN TIẾP TỤC XỬ LÝ", bold=True)
    pending = [i for i in issues if i.level in (ERROR, WARNING)]
    if pending:
        table(("STT", "Biểu", "Mã", "Nội dung", "Đầu mối, thời hạn"),
              [(n, i.form, i.ref, i.message, "") for n, i in enumerate(pending, 1)], 10)
    else:
        para("Không còn lỗi hoặc cảnh báo theo kiểm tra tự động. Kết quả kiểm tra tự động không thay thế việc "
             "xác nhận nghiệp vụ của cơ quan, đơn vị.", align="justify", indent=True)

    para("VII. KIẾN NGHỊ, ĐỀ XUẤT", bold=True)
    kn = s(meta.get("kien_nghi")) or (
        "Đề nghị cơ quan có thẩm quyền xem xét, thẩm định danh mục vị trí việc làm, nhu cầu nhân lực và phương án "
        "số lượng người làm việc giai đoạn 2027 - 2031 của Thư viện theo kết quả rà soát nêu trên.")
    for line in kn.splitlines():
        para(line, align="justify", indent=True)

    sig = doc.add_table(rows=1, cols=2)
    left = sig.cell(0, 0).paragraphs[0]
    left.add_run("Nơi nhận:\n").bold = True
    left.add_run("- " + meta.get("co_quan_chu_quan", "") + ";\n- Lưu: VT.").font.size = Pt(11)
    right = sig.cell(0, 1).paragraphs[0]
    right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    right.add_run((meta.get("chuc_vu_nguoi_dung_dau") or "THỦ TRƯỞNG ĐƠN VỊ").upper() + "\n").bold = True
    right.add_run("(Ký tên, đóng dấu)\n\n\n\n").italic = True
    right.add_run(meta.get("nguoi_dung_dau", "")).bold = True
    doc.save(path)


__all__ = ["export_official", "export_excel", "import_official", "import_excel", "export_word",
           "template_path", "bundled_template", "shift_formula", "repair_template", "NINE"]
