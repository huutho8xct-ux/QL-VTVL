"""Xuất Bộ 09 biểu ra Excel, báo cáo thuyết minh ra Word; nhập lại từ Excel."""
from __future__ import annotations

from datetime import date

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .calc import Calculator, fmt, num
from .checks import run_checks
from .forms import FORM_ORDER, FORMS, YEARS

HD_REF = "(Kèm theo Hướng dẫn số 07-HD/BTCTW ngày 19/10/2026 của Ban Tổ chức Trung ương)"
FONT = "Times New Roman"
THIN = Side(style="thin", color="000000")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD_FILL = PatternFill("solid", fgColor="DCE6F1")
TOTAL_FILL = PatternFill("solid", fgColor="F2F2F2")

NUMERIC_KINDS = ("int", "float")
SUM_COLS = {
    "B1": ("tong_gio",),
    "B2": ("gio_thay_doi",),
    "C3": ("gio_b1", "gio_b2", "gio_can", "nguoi_quy_doi", "nguoi_dinh_muc", "nguoi_can"),
    "D1": ("nguoi_can", "vien_chuc", "hop_dong", "hien_co", "chenh_lech", "giao"),
    "D2": ("nguoi_can", "hien_co") + tuple(f"y{y}" for y in YEARS),
}
CALC_NUMERIC = {"tong_gio", "gio_b1", "gio_b2", "gio_can", "nguoi_quy_doi", "nguoi_can", "hien_co",
                "chenh_lech"}


def _font(size=12, bold=False, italic=False):
    return Font(name=FONT, size=size, bold=bold, italic=italic)


def _header_block(ws, meta, ncols, code, title):
    last = get_column_letter(ncols)
    half = max(2, ncols // 2)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=half)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=half)
    ws.merge_cells(start_row=1, start_column=half + 1, end_row=1, end_column=ncols)
    ws.merge_cells(start_row=2, start_column=half + 1, end_row=2, end_column=ncols)
    ws.cell(1, 1, meta.get("co_quan_chu_quan", "").upper()).font = _font(11)
    ws.cell(2, 1, meta.get("ten_don_vi", "").upper()).font = _font(11, bold=True)
    ws.cell(1, half + 1, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM").font = _font(11, bold=True)
    ws.cell(2, half + 1, "Độc lập - Tự do - Hạnh phúc").font = _font(12, bold=True)
    for r in (1, 2):
        for c in (1, half + 1):
            ws.cell(r, c).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r, text, f in ((4, f"Biểu {code}", _font(12, bold=True)),
                       (5, title.upper(), _font(14, bold=True)),
                       (6, HD_REF, _font(11, italic=True)),
                       (7, meta.get("ky_ra_soat", ""), _font(11, italic=True))):
        ws.merge_cells(f"A{r}:{last}{r}")
        cell = ws.cell(r, 1, text)
        cell.font = f
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[5].height = 22
    return 9  # dòng tiêu đề bảng


def _signature(ws, row, ncols, meta):
    half = max(2, ncols // 2)
    today = date.today()
    ws.merge_cells(start_row=row, start_column=half + 1, end_row=row, end_column=ncols)
    c = ws.cell(row, half + 1, f"Cần Thơ, ngày {today.day:02d} tháng {today.month:02d} năm {today.year}")
    c.font = _font(12, italic=True)
    c.alignment = Alignment(horizontal="center")
    row += 1
    for col_start, col_end, title, name in (
        (1, half, "NGƯỜI LẬP BIỂU", meta.get("nguoi_lap", "")),
        (half + 1, ncols, (meta.get("chuc_vu_nguoi_dung_dau") or "THỦ TRƯỞNG ĐƠN VỊ").upper(),
         meta.get("nguoi_dung_dau", "")),
    ):
        ws.merge_cells(start_row=row, start_column=col_start, end_row=row, end_column=col_end)
        ws.merge_cells(start_row=row + 1, start_column=col_start, end_row=row + 1, end_column=col_end)
        ws.merge_cells(start_row=row + 5, start_column=col_start, end_row=row + 5, end_column=col_end)
        a = ws.cell(row, col_start, title)
        a.font = _font(12, bold=True)
        b = ws.cell(row + 1, col_start, "(Ký, ghi rõ họ tên)" if col_start == 1 else "(Ký tên, đóng dấu)")
        b.font = _font(11, italic=True)
        n = ws.cell(row + 5, col_start, name)
        n.font = _font(12, bold=True)
        for cc in (a, b, n):
            cc.alignment = Alignment(horizontal="center")


def _cell_value(calc, code, r, col):
    v = calc.value(code, r, col.key)
    if col.kind in NUMERIC_KINDS or col.key in CALC_NUMERIC:
        if v is None or v == "":
            return None
        return round(num(v), 3)
    return v if v is not None else ""


def write_form_sheet(ws, project, calc, code, meta):
    form = FORMS[code]
    cols = form.columns
    ncols = len(cols) + 1
    hr = _header_block(ws, meta, ncols, code, form.title)
    headers = ["STT"] + [c.label for c in cols]
    for j, h in enumerate(headers, 1):
        cell = ws.cell(hr, j, h)
        cell.font = _font(11, bold=True)
        cell.fill = HEAD_FILL
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        nb = ws.cell(hr + 1, j, f"({j})")
        nb.font = _font(10, italic=True)
        nb.border = BORDER
        nb.alignment = Alignment(horizontal="center")
    ws.row_dimensions[hr].height = 48
    ws.column_dimensions["A"].width = 6
    for j, c in enumerate(cols, 2):
        ws.column_dimensions[get_column_letter(j)].width = max(9, min(60, c.width / 6.2))
    row = hr + 2
    rows = project.rows(code)
    for i, r in enumerate(rows, 1):
        ws.cell(row, 1, i)
        for j, c in enumerate(cols, 2):
            ws.cell(row, j, _cell_value(calc, code, r, c))
        for j in range(1, ncols + 1):
            cell = ws.cell(row, j)
            cell.font = _font(11)
            cell.border = BORDER
            numeric = j > 1 and (cols[j - 2].kind in NUMERIC_KINDS or cols[j - 2].key in CALC_NUMERIC)
            cell.alignment = Alignment(vertical="top", wrap_text=True,
                                       horizontal="right" if numeric else ("center" if j == 1 else "left"))
            if numeric:
                cell.number_format = "#,##0.###"
        row += 1
    sums = SUM_COLS.get(code)
    if sums and rows:
        ws.cell(row, 1, "")
        ws.cell(row, 2, "TỔNG CỘNG")
        for j, c in enumerate(cols, 2):
            if c.key in sums:
                ws.cell(row, j, round(sum(num(calc.value(code, r, c.key)) for r in rows), 3))
                ws.cell(row, j).number_format = "#,##0.###"
        for j in range(1, ncols + 1):
            cell = ws.cell(row, j)
            cell.font = _font(11, bold=True)
            cell.border = BORDER
            cell.fill = TOTAL_FILL
        row += 1
    ws.freeze_panes = ws.cell(hr + 2, 3)
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{hr}:{hr + 1}"
    _signature(ws, row + 2, ncols, meta)


def export_excel(project, path: str):
    calc = Calculator(project)
    meta = project.meta()
    wb = Workbook()
    ws = wb.active
    ws.title = "Tổng hợp"
    _summary_sheet(ws, project, calc, meta)
    for code in FORM_ORDER:
        write_form_sheet(wb.create_sheet(code), project, calc, code, meta)
    _checks_sheet(wb.create_sheet("Kiểm tra"), project)
    wb.save(path)


def _summary_sheet(ws, project, calc, meta):
    s = calc.summary()
    ncols = 6
    _header_block(ws, meta, ncols, "TH", "Tổng hợp kết quả rà soát vị trí việc làm")
    ws.cell(4, 1, "")
    data = [
        ("Số nhiệm vụ (A1)", s["nv"]), ("Số công việc (A2)", s["cv"]),
        ("Tổng giờ lao động/năm (B1)", s["hours"]), ("Giờ tăng/giảm do tác động (B2)", s["delta"]),
        ("Số vị trí việc làm (C1)", s["vt"]), ("Quỹ giờ chuẩn/người/năm", calc.default_quy),
        ("Tổng số người cần bố trí (C3)", s["need"]), ("Tổng nhân lực hiện có (D1)", s["existing"]),
        ("Số lượng người làm việc được giao", s["giao"]), ("Chênh lệch hiện có - nhu cầu", s["diff"]),
    ]
    r = 9
    for label, v in data:
        ws.cell(r, 1, label).font = _font(12)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        c = ws.cell(r, 5, round(v, 3))
        c.font = _font(12, bold=True)
        c.number_format = "#,##0.###"
        for j in range(1, 6):
            ws.cell(r, j).border = BORDER
        r += 1
    r += 1
    heads = ["Nhóm vị trí việc làm", "", "", "Số VTVL", "Nhu cầu", "Hiện có"]
    for j, h in enumerate(heads, 1):
        c = ws.cell(r, j, h)
        c.font = _font(11, bold=True)
        c.fill = HEAD_FILL
        c.border = BORDER
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    r += 1
    for g, v in s["by_group"].items():
        ws.cell(r, 1, g)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
        ws.cell(r, 4, v["vt"])
        ws.cell(r, 5, round(v["need"], 3))
        ws.cell(r, 6, round(v["existing"], 3))
        for j in range(1, 7):
            ws.cell(r, j).border = BORDER
            ws.cell(r, j).font = _font(11)
        r += 1
    r += 1
    for j, y in enumerate(YEARS, 2):
        c = ws.cell(r, j, f"Năm {y}")
        c.font = _font(11, bold=True)
        c.fill = HEAD_FILL
        c.border = BORDER
        d = ws.cell(r + 1, j, round(s["plan"][y], 3))
        d.border = BORDER
        d.font = _font(11)
    ws.cell(r, 1, "Phương án").font = _font(11, bold=True)
    ws.cell(r + 1, 1, "Số người làm việc").font = _font(11)
    ws.column_dimensions["A"].width = 24
    for col in "BCDEF":
        ws.column_dimensions[col].width = 14
    _signature(ws, r + 4, 6, meta)


def _checks_sheet(ws, project):
    ws.append(["Mức độ", "Biểu", "Mã", "Nội dung"])
    for c in ws[1]:
        c.font = _font(11, bold=True)
        c.fill = HEAD_FILL
    for i in run_checks(project):
        ws.append([i.level, i.form, i.ref, i.message])
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 8
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 110


# ---------------------------------------------------------------- import
def import_excel(project, path: str, codes=None) -> dict:
    """Nhập dữ liệu từ tệp Excel do phần mềm xuất (hoặc cùng cấu trúc cột)."""
    wb = load_workbook(path, data_only=True)
    result = {}
    for code in codes or FORM_ORDER:
        if code not in wb.sheetnames:
            continue
        ws = wb[code]
        form = FORMS[code]
        label_to_key = {c.label.strip().lower(): c for c in form.columns}
        header_row = None
        for row in ws.iter_rows(min_row=1, max_row=40):
            if row and str(row[0].value or "").strip().upper() == "STT":
                header_row = row[0].row
                break
        if header_row is None:
            continue
        colmap = {}
        for cell in ws[header_row]:
            lab = str(cell.value or "").strip().lower()
            if lab in label_to_key:
                colmap[cell.column] = label_to_key[lab]
        rows = []
        for row in ws.iter_rows(min_row=header_row + 1):
            first = str(row[0].value or "").strip()
            if first.startswith("("):
                continue
            vals = {}
            for cell in row:
                col = colmap.get(cell.column)
                if not col or col.kind == "calc" or cell.value is None:
                    continue
                v = cell.value
                if col.kind in NUMERIC_KINDS:
                    v = num(v, None)
                    if v is None:
                        continue
                    if col.kind == "int":
                        v = int(v)
                else:
                    v = str(v).strip()
                vals[col.key] = v
            label2 = str(row[1].value or "").strip().upper() if len(row) > 1 else ""
            if label2 == "TỔNG CỘNG":
                break
            if not vals:
                if rows:
                    break
                continue
            rows.append(vals)
        project.replace_rows(code, rows)
        result[code] = len(rows)
    return result


# ------------------------------------------------------------------ Word
def export_word(project, path: str):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    calc = Calculator(project)
    meta = project.meta()
    s = calc.summary()
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(13)
    st.element.rPr.rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia", FONT)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)
    sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)

    def para(text="", bold=False, italic=False, align=None, size=None, space_after=6, indent=False):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold, run.italic = bold, italic
        if size:
            run.font.size = Pt(size)
        if align == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "justify":
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(space_after)
        if indent:
            p.paragraph_format.first_line_indent = Cm(1)
        return p

    head = doc.add_table(rows=2, cols=2)
    head.alignment = WD_TABLE_ALIGNMENT.CENTER
    cells = (
        (0, 0, meta.get("co_quan_chu_quan", "").upper(), False),
        (1, 0, meta.get("ten_don_vi", "").upper(), True),
        (0, 1, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", True),
        (1, 1, "Độc lập - Tự do - Hạnh phúc", True),
    )
    for r_, c_, text, bold in cells:
        p = head.cell(r_, c_).paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = bold
        run.font.size = Pt(12)
    today = date.today()
    p = para(f"Cần Thơ, ngày {today.day:02d} tháng {today.month:02d} năm {today.year}", italic=True)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    para("BÁO CÁO", bold=True, align="center", size=14, space_after=0)
    para("Kết quả rà soát, hoàn thiện vị trí việc làm, xác định nhu cầu nhân lực và "
         "xây dựng phương án số lượng người làm việc giai đoạn 2027 - 2031",
         bold=True, align="center", size=14)

    para("I. CĂN CỨ", bold=True)
    for r in project.rows("CC"):
        if r.get("hieu_luc", "Đang áp dụng") == "Đang áp dụng":
            para(f"- {r.get('so_hieu', '')} ({r.get('ngay', '')}) của {r.get('co_quan', '')}: "
                 f"{r.get('trich_yeu', '')}", align="justify", indent=True, space_after=3)

    para("II. KẾT QUẢ RÀ SOÁT NHIỆM VỤ, CÔNG VIỆC", bold=True)
    para(f"Thư viện đã rà soát {s['nv']} nhiệm vụ (Biểu A1), cụ thể hóa thành {s['cv']} công việc gắn với "
         f"sản phẩm đầu ra (Biểu A2). Tổng thời gian lao động trực tiếp xác định được là "
         f"{fmt(s['hours'])} giờ/năm (Biểu B1); tác động của chuyển đổi số, tự chủ, thuê dịch vụ, "
         f"xã hội hóa làm thay đổi {fmt(s['delta'])} giờ/năm (Biểu B2).", align="justify", indent=True)

    para("III. DANH MỤC VỊ TRÍ VIỆC LÀM", bold=True)
    para(f"Tổng số {s['vt']} vị trí việc làm, gồm:", indent=True)
    for g, v in s["by_group"].items():
        para(f"- {g}: {v['vt']} vị trí.", indent=True, space_after=2)

    def table(headers, data, widths=None):
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        for j, h in enumerate(headers):
            cell = t.rows[0].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(h)
            run.bold = True
            run.font.size = Pt(11)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for row in data:
            cells_ = t.add_row().cells
            for j, v in enumerate(row):
                cells_[j].text = ""
                run = cells_[j].paragraphs[0].add_run(str(v))
                run.font.size = Pt(11)
        if widths:
            for row in t.rows:
                for j, w in enumerate(widths):
                    row.cells[j].width = Cm(w)
        doc.add_paragraph()

    para("IV. NHU CẦU NHÂN LỰC THEO VỊ TRÍ VIỆC LÀM", bold=True)
    para(f"Quỹ thời gian làm việc chuẩn: {fmt(calc.default_quy)} giờ/người/năm. Số người quy đổi = "
         "Tổng giờ cần thiết ÷ Quỹ giờ; kết quả không làm tròn cơ học, không tự động trở thành biên chế.",
         align="justify", indent=True)
    data = []
    for i, r in enumerate(project.rows("C3"), 1):
        v = calc.c3_values(r)
        data.append((i, r.get("ma_vt", ""), calc.value("C3", r, "ten_vt"), str(r.get("phuong_phap", ""))[:3],
                     fmt(v["gio_can"]), fmt(v["nguoi_quy_doi"], 3), fmt(calc.need(r.get("ma_vt", "")))))
    table(("STT", "Mã", "Vị trí việc làm", "PP", "Giờ cần", "Quy đổi", "Cần bố trí"), data,
          (1.0, 1.4, 6.0, 1.2, 2.0, 1.8, 2.0))

    para("V. ĐỐI CHIẾU NHÂN LỰC HIỆN CÓ VÀ PHƯƠNG ÁN 2027 - 2031", bold=True)
    para(f"Tổng nhu cầu: {fmt(s['need'])} người; hiện có: {fmt(s['existing'])} người; số lượng người làm "
         f"việc được giao: {fmt(s['giao'])}; chênh lệch (hiện có - nhu cầu): {fmt(s['diff'])}.",
         align="justify", indent=True)
    data = []
    for i, r in enumerate(project.rows("D2"), 1):
        vt = r.get("ma_vt", "")
        data.append([i, vt, fmt(calc.need(vt)), fmt(calc.existing(vt))]
                    + [fmt(r.get(f"y{y}", "")) for y in YEARS])
    tot = ["", "Tổng", fmt(s["need"]), fmt(s["existing"])] + [fmt(s["plan"][y]) for y in YEARS]
    data.append(tot)
    table(["STT", "Mã VTVL", "Nhu cầu", "Hiện có"] + [str(y) for y in YEARS], data)

    para("VI. KIẾN NGHỊ, ĐỀ XUẤT", bold=True)
    kn = meta.get("kien_nghi", "").strip() or (
        "Đề nghị cơ quan có thẩm quyền xem xét, thẩm định danh mục vị trí việc làm và phương án số lượng "
        "người làm việc giai đoạn 2027 - 2031 của Thư viện theo kết quả rà soát nêu trên.")
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
