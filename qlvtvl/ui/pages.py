"""Các trang chức năng."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget,
)

from ..core.calc import Calculator, fmt
from ..core.checks import ERROR, INFO, WARNING, run_checks, step_status
from ..core.forms import FORMS, YEARS
from ..core.guide import DISCLAIMER, STEPS
from . import theme
from .form_editor import FormEditor


def page_header(title: str, sub: str = "", badge: str = "") -> QWidget:
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    if badge:
        b = QLabel(badge)
        b.setObjectName("StepBadge")
        b.setAlignment(Qt.AlignCenter)
        h.addWidget(b)
    v = QVBoxLayout()
    v.setSpacing(0)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    t.setWordWrap(True)
    v.addWidget(t)
    if sub:
        s = QLabel(sub)
        s.setObjectName("PageSub")
        s.setWordWrap(True)
        v.addWidget(s)
    h.addLayout(v, 1)
    return w


def tab_title(code):
    f = FORMS[code]
    if code == "DB":
        return "Dự báo nhu cầu 2027 – 2031"
    if code == "DM":
        return "Danh mục sản phẩm dùng chung"
    return f"Biểu {code if code != 'B2TH' else 'B2'} – {f.title}"


class Page(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Page")
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(22, 18, 22, 14)
        self.lay.setSpacing(10)

    def on_show(self):
        pass


# --------------------------------------------------------------- dashboard
class Card(QFrame):
    def __init__(self, label, color=theme.PRIMARY_DARK):
        super().__init__()
        self.setObjectName("Card")
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        self.value = QLabel("0")
        self.value.setObjectName("CardValue")
        self.value.setStyleSheet(f"color:{color}")
        self.label = QLabel(label)
        self.label.setObjectName("CardLabel")
        self.label.setWordWrap(True)
        v.addWidget(self.value)
        v.addWidget(self.label)
        self.setMinimumHeight(92)


class BarChart(QWidget):
    """Biểu đồ cột đơn giản: nhu cầu và hiện có theo nhóm, phương án theo năm."""

    def __init__(self, title):
        super().__init__()
        self.title = title
        self.series = []  # (label, [(name, value, color)])
        self.setMinimumHeight(240)

    def set_data(self, series):
        self.series = series
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(theme.BORDER)))
        p.setBrush(QBrush(QColor("white")))
        p.drawRoundedRect(r, 10, 10)
        f = QFont(self.font())
        f.setBold(True)
        f.setPointSize(10)
        p.setFont(f)
        p.setPen(QColor(theme.PRIMARY_DARK))
        p.drawText(QRectF(14, 8, r.width() - 28, 22), Qt.AlignLeft | Qt.AlignVCenter, self.title)
        if not self.series:
            p.setPen(QColor(theme.MUTED))
            p.drawText(r, Qt.AlignCenter, "Chưa có dữ liệu")
            return
        legend = []
        for _, bars in self.series:
            for name, _, color in bars:
                if name not in [n for n, _ in legend]:
                    legend.append((name, color))
        f.setBold(False)
        f.setPointSize(8)
        p.setFont(f)
        x = 14
        for name, color in legend:
            p.fillRect(QRectF(x, 34, 11, 11), QColor(color))
            x += 15
            tw = p.fontMetrics().horizontalAdvance(name)
            p.setPen(QColor(theme.TEXT))
            p.drawText(QRectF(x, 31, tw + 4, 18), Qt.AlignVCenter, name)
            x += tw + 18
        top, bottom, left = 66, r.height() - 46, 40
        mx = max([v for _, bars in self.series for _, v, _ in bars] + [1])
        p.setPen(QPen(QColor("#E5E9F0")))
        for i in range(5):
            y = bottom - (bottom - top) * i / 4
            p.drawLine(left, int(y), r.width() - 12, int(y))
            p.setPen(QColor(theme.MUTED))
            p.drawText(QRectF(2, y - 8, left - 6, 16), Qt.AlignRight | Qt.AlignVCenter, fmt(mx * i / 4, 1))
            p.setPen(QPen(QColor("#E5E9F0")))
        n = len(self.series)
        slot = (r.width() - left - 16) / n
        for i, (label, bars) in enumerate(self.series):
            k = len(bars)
            bw = min(34, slot * 0.7 / k)
            x0 = left + i * slot + (slot - bw * k) / 2
            for j, (_, v, color) in enumerate(bars):
                h = (bottom - top) * (v / mx)
                rect = QRectF(x0 + j * bw, bottom - h, bw - 3, h)
                p.fillRect(rect, QColor(color))
                p.setPen(QColor(theme.TEXT))
                p.drawText(QRectF(rect.x() - 10, rect.y() - 15, rect.width() + 20, 14), Qt.AlignCenter, fmt(v, 1))
            p.setPen(QColor(theme.TEXT))
            p.drawText(QRectF(left + i * slot + 2, bottom + 4, slot - 4, 42), Qt.AlignHCenter | Qt.TextWordWrap, label)


class DashboardPage(Page):
    go_step = Signal(int)

    def __init__(self, project):
        super().__init__()
        self.project = project
        self.header = page_header("Tổng quan", " ")
        self.title_lbl, self.sub_lbl = self.header.findChildren(QLabel)[:2]
        self.lay.addWidget(self.header)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.cards = {
            "nv": Card("Nhiệm vụ (A1)"), "cv": Card("Công việc (A2)"),
            "hours": Card("Giờ ròng/năm (B1 đạt + tác động B2)"), "vt": Card("Vị trí việc làm (C1)"),
            "qd": Card("Người quy đổi PP2 (C3) – tham khảo"), "need": Card("Người cần bố trí (C3)", theme.OK),
            "existing": Card("Nhân lực hiện có (D1, người)"), "ok": Card("VTVL đủ căn cứ (C3 ĐẠT + đã kiểm chứng)"),
        }
        for i, c in enumerate(self.cards.values()):
            grid.addWidget(c, i // 4, i % 4)
        self.lay.addLayout(grid)

        mid = QHBoxLayout()
        steps_card = QFrame()
        steps_card.setObjectName("Card")
        sv = QVBoxLayout(steps_card)
        t = QLabel("Tiến độ 08 bước rà soát (Hướng dẫn 07-HD/BTCTW)")
        t.setStyleSheet(f"font-weight:700;color:{theme.PRIMARY_DARK}")
        sv.addWidget(t)
        self.step_btns = []
        for st in STEPS:
            b = QPushButton()
            b.setObjectName("Link")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, n=st.no: self.go_step.emit(n))
            sv.addWidget(b)
            self.step_btns.append((st, b))
        sv.addStretch(1)
        mid.addWidget(steps_card, 2)
        self.chart_group = BarChart("Nhu cầu và hiện có theo loại nhân lực")
        mid.addWidget(self.chart_group, 3)
        self.lay.addLayout(mid, 1)
        self.chart_plan = BarChart("Phương án số người làm việc giai đoạn 2027 - 2031 (Biểu D2)")
        self.lay.addWidget(self.chart_plan, 1)

    def on_show(self):
        calc = Calculator(self.project)
        s = calc.summary()
        meta = self.project.meta()
        sample = " — đang dùng DỮ LIỆU MINH HỌA" if meta.get("du_lieu_mau") == "1" else ""
        self.title_lbl.setText(f"Tổng quan – {meta.get('ten_don_vi', '')}")
        self.sub_lbl.setText(meta.get("ky_ra_soat", "") + sample)
        self.cards["nv"].value.setText(fmt(s["nv"]))
        self.cards["cv"].value.setText(fmt(s["cv"]))
        self.cards["hours"].value.setText(fmt(s["net"], 0))
        self.cards["vt"].value.setText(fmt(s["vt"]))
        self.cards["qd"].value.setText(fmt(s["qd"], 2))
        self.cards["need"].value.setText(fmt(s["need"], 2))
        self.cards["existing"].value.setText(fmt(s["existing"]))
        ok_txt = f"{s['ok_vt']}/{s['vt']}"
        self.cards["ok"].value.setText(ok_txt)
        full = s["vt"] and s["ok_vt"] == s["vt"]
        self.cards["ok"].value.setStyleSheet(f"color:{theme.OK if full else theme.WARN}")
        status = step_status(self.project)
        icon = {"done": "✅", "partial": "🟡", "empty": "⚪"}
        word = {"done": "hoàn thành", "partial": "đang thực hiện", "empty": "chưa bắt đầu"}
        for st, b in self.step_btns:
            stt = status.get(st.no, "empty")
            forms = (" – Biểu " + ", ".join(st.forms)) if st.forms else ""
            b.setText(f"{icon[stt]}  Bước {st.no}. {st.title}{forms}  ({word[stt]})")
        groups = []
        for g, v in s["by_group"].items():
            groups.append((g, [("Người cần bố trí (C3)", v["need"], theme.PRIMARY),
                               ("Hiện có (D1)", v["existing"], theme.ACCENT)]))
        self.chart_group.set_data(groups)
        plan = [(str(y), [("Số người cần bố trí", s["plan"][y], theme.PRIMARY),
                          ("Số người có thể bố trí", s["avail"][y], theme.ACCENT)]) for y in YEARS]
        self.chart_plan.set_data(plan if any(v for _, b in plan for _, v, _ in b) else [])


# --------------------------------------------------------------- step page
class StepPage(Page):
    def __init__(self, project, step, total_steps=8):
        super().__init__()
        self.project = project
        self.step = step
        self.lay.addWidget(page_header(f"{step.title}", f"Bước {step.no}/{total_steps} theo Hướng dẫn 07-HD/BTCTW",
                                       str(step.no)))
        split = QSplitter(Qt.Vertical)
        guide = QTextBrowser()
        guide.setObjectName("Guide")
        guide.setOpenExternalLinks(True)
        guide.setHtml(f"<div style='line-height:140%'>{step.guide}</div>")
        guide.setMinimumHeight(60)
        split.addWidget(guide)
        self.editors = {}
        if len(step.forms) == 1:
            code = step.forms[0]
            ed = FormEditor(project, code)
            self.editors[code] = ed
            wrap = QWidget()
            wl = QVBoxLayout(wrap)
            wl.setContentsMargins(0, 0, 0, 0)
            tl = QLabel(tab_title(code))
            tl.setStyleSheet(f"font-weight:700;font-size:11pt;color:{theme.PRIMARY_DARK}")
            wl.addWidget(tl)
            wl.addWidget(ed)
            split.addWidget(wrap)
        else:
            self.tabs = QTabWidget()
            for code in step.forms:
                ed = FormEditor(project, code)
                self.editors[code] = ed
                self.tabs.addTab(ed, tab_title(code))
            split.addWidget(self.tabs)
        split.setSizes([130, 640])
        split.setStretchFactor(1, 1)
        self.lay.addWidget(split, 1)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Bước trước")
        self.next_btn = QPushButton("Bước tiếp theo ▶")
        self.next_btn.setObjectName("Primary")
        nav.addWidget(self.prev_btn)
        nav.addStretch(1)
        nav.addWidget(self.next_btn)
        self.lay.addLayout(nav)
        self.prev_btn.setEnabled(step.no > 1)

    def show_form(self, code, row_id=None, key=None):
        ed = self.editors.get(code)
        if not ed:
            return
        if hasattr(self, "tabs"):
            self.tabs.setCurrentWidget(ed)
        if row_id:
            ed.select_row_id(row_id)
        elif key:
            ed.select_key(key)

    def on_show(self):
        for ed in self.editors.values():
            ed.refresh()


# ------------------------------------------------------------ check / export
class CheckPage(Page):
    goto = Signal(str, object, str)
    export_excel = Signal()
    export_word = Signal()

    def __init__(self, project, step):
        super().__init__()
        self.project = project
        self.lay.addWidget(page_header(step.title, "Bước 8/8 – kiểm tra tự động và xuất hồ sơ", "8"))
        guide = QTextBrowser()
        guide.setObjectName("Guide")
        guide.setHtml(step.guide)
        guide.setMaximumHeight(150)
        self.lay.addWidget(guide)
        bar = QHBoxLayout()
        run = QPushButton("⟳ Kiểm tra lại")
        run.clicked.connect(self.on_show)
        bar.addWidget(run)
        self.summary = QLabel()
        self.summary.setStyleSheet("font-weight:600")
        bar.addWidget(self.summary, 1)
        self.filter = QComboBox()
        self.filter.addItems(["Tất cả", ERROR, WARNING, INFO])
        self.filter.currentIndexChanged.connect(self._fill)
        bar.addWidget(QLabel("Hiển thị:"))
        bar.addWidget(self.filter)
        bx = QPushButton("📊 Xuất vào Bộ biểu Excel chính thức")
        bx.setObjectName("Primary")
        bx.clicked.connect(self.export_excel.emit)
        bw = QPushButton("📄 Xuất báo cáo thuyết minh (Word)")
        bw.setObjectName("Primary")
        bw.clicked.connect(self.export_word.emit)
        bar.addWidget(bx)
        bar.addWidget(bw)
        self.lay.addLayout(bar)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Mức độ", "Biểu", "Mã", "Nội dung (nhấp đúp để đến vị trí cần sửa)"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 90)
        self.table.cellDoubleClicked.connect(self._go)
        self.lay.addWidget(self.table, 1)
        self.issues = []

    def on_show(self):
        self.issues = run_checks(self.project)
        n_e = sum(1 for i in self.issues if i.level == ERROR)
        n_w = sum(1 for i in self.issues if i.level == WARNING)
        n_i = sum(1 for i in self.issues if i.level == INFO)
        if n_e == 0 and n_w == 0:
            txt = f"<span style='color:{theme.OK}'>✔ Dữ liệu đầy đủ, hợp lệ.</span> {n_i} lưu ý."
        else:
            txt = (f"<span style='color:{theme.ERR}'>{n_e} lỗi</span> · "
                   f"<span style='color:{theme.WARN}'>{n_w} cảnh báo</span> · {n_i} lưu ý")
        self.summary.setText(txt)
        self._fill()

    def _fill(self):
        flt = self.filter.currentText()
        items = [i for i in self.issues if flt == "Tất cả" or i.level == flt]
        self.table.setRowCount(len(items))
        color = {ERROR: theme.ERR, WARNING: theme.WARN, INFO: theme.PRIMARY}
        icon = {ERROR: "⛔", WARNING: "⚠", INFO: "ⓘ"}
        for r, i in enumerate(items):
            vals = [f"{icon[i.level]} {i.level}", i.form, i.ref, i.message]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                if c == 0:
                    it.setForeground(QBrush(QColor(color[i.level])))
                it.setData(Qt.UserRole, i)
                self.table.setItem(r, c, it)
        self.shown = items

    def _go(self, row, _col):
        i = self.shown[row]
        self.goto.emit(i.form, i.row_id, i.ref)


# ------------------------------------------------------------ unit info
class InfoPage(Page):
    FIELDS = (
        ("ten_don_vi", "Tên đơn vị"),
        ("co_quan_chu_quan", "Cơ quan chủ quản"),
        ("dia_chi", "Địa chỉ"),
        ("ky_ra_soat", "Đợt rà soát"),
        ("ky_thong_ke", "Kỳ thống kê khối lượng (12 tháng)"),
        ("ngay_chot", "Ngày chốt nhân lực hiện có"),
        ("bc_giao", "Số lượng người làm việc được giao (tổng)"),
        ("nguoi_dung_dau", "Họ tên người đứng đầu"),
        ("chuc_vu_nguoi_dung_dau", "Chức vụ người đứng đầu"),
        ("nguoi_lap", "Họ tên người lập biểu"),
        ("dien_thoai", "Điện thoại liên hệ"),
        ("quy_gio", "Quỹ giờ quy đổi PP2 (giờ/người/năm)"),
    )

    def __init__(self, project):
        super().__init__()
        self.project = project
        self.lay.addWidget(page_header("Thông tin đơn vị", "Thông tin dùng cho phần đầu biểu, chữ ký và báo cáo"))
        card = QFrame()
        card.setObjectName("Card")
        fl = QFormLayout(card)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setLabelAlignment(Qt.AlignRight)
        fl.setVerticalSpacing(10)
        self.edits = {}
        for key, label in self.FIELDS:
            e = QLineEdit()
            e.setMinimumWidth(460)
            e.editingFinished.connect(lambda k=key, w=e: self._save(k, w.text()))
            if key == "quy_gio":
                e.setToolTip("Mặc định 1.904 giờ (40 giờ/tuần, 5 ngày/tuần, trừ ngày lễ, 12 ngày phép). "
                             "Chỉ thay đổi khi có mức đặc thù đã được xác nhận.")
            self.edits[key] = e
            fl.addRow(label + ":", e)
        self.kn = QPlainTextEdit()
        self.kn.setPlaceholderText("Nội dung kiến nghị, đề xuất đưa vào báo cáo thuyết minh (mục VI)...")
        self.kn.setFixedHeight(110)
        self.kn.textChanged.connect(lambda: self.project.set_meta("kien_nghi", self.kn.toPlainText(), notify=False))
        fl.addRow("Kiến nghị, đề xuất:", self.kn)
        tpl_row = QHBoxLayout()
        self.tpl = QLineEdit()
        self.tpl.setReadOnly(True)
        b1 = QPushButton("Chọn tệp mẫu khác...")
        b1.clicked.connect(self._pick_template)
        b2 = QPushButton("Dùng mẫu kèm phần mềm")
        b2.clicked.connect(lambda: (self.project.set_meta("template_path", ""), self.on_show()))
        tpl_row.addWidget(self.tpl, 1)
        tpl_row.addWidget(b1)
        tpl_row.addWidget(b2)
        fl.addRow("Mẫu Bộ biểu Excel:", tpl_row)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(card)
        self.lay.addWidget(sc, 1)
        note = QLabel("ⓘ  Dữ liệu được lưu tự động ngay khi nhập. Quỹ giờ 1.904 giờ là mức tham chiếu nghiệp vụ PP2 "
                      "(tham số DM_THAM_SO do cơ quan chủ trì quản lý), không phải định mức biên chế. Mẫu Bộ biểu mặc "
                      "định là bản phát hành 19-10-2026; khi Ban Tổ chức Trung ương phát hành phiên bản mới, chọn tệp "
                      "mẫu mới tại đây.")
        note.setObjectName("Note")
        note.setWordWrap(True)
        self.lay.addWidget(note)

    def _pick_template(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Chọn tệp mẫu Bộ biểu Excel", "", "Excel (*.xlsx)")
        if path:
            self.project.set_meta("template_path", path)
            self.on_show()

    def _save(self, key, value):
        if key == "quy_gio":
            from ..core.calc import num
            v = num(value, 0)
            if v <= 0 or v > 3000:
                QMessageBox.warning(self, "Không hợp lệ", "Quỹ giờ phải là số dương (ví dụ 1904).")
                self.edits[key].setText(self.project.get_meta("quy_gio", "1904"))
                return
            value = fmt(v).replace(".", "")
        if self.project.get_meta(key) != value:
            self.project.set_meta(key, value)

    def on_show(self):
        m = self.project.meta()
        for k, e in self.edits.items():
            e.setText(m.get(k, ""))
        self.kn.blockSignals(True)
        self.kn.setPlainText(m.get("kien_nghi", ""))
        self.kn.blockSignals(False)
        from ..core.exporter import template_path
        self.tpl.setText(template_path(self.project))


class LegalPage(Page):
    def __init__(self, project):
        super().__init__()
        self.lay.addWidget(page_header("Căn cứ pháp lý", "Danh mục văn bản về vị trí việc làm và lĩnh vực thư viện"))
        note = QLabel("ⓘ  " + DISCLAIMER)
        note.setObjectName("Note")
        note.setWordWrap(True)
        self.lay.addWidget(note)
        self.editor = FormEditor(project, "CC")
        self.lay.addWidget(self.editor, 1)

    def on_show(self):
        self.editor.refresh()


HELP_HTML = """
<h2 style='color:#083C6B'>Hướng dẫn sử dụng nhanh</h2>
<p>Phần mềm bám sát <b>Hướng dẫn số 7-HD/BTCTW ngày 19/10/2026</b> và <b>Bộ biểu Excel 19-10-2026</b> của Ban Tổ
chức Trung ương: cùng tên cột, cùng danh sách lựa chọn, cùng công thức và cảnh báo (mỗi cột có ký hiệu cột của bộ
biểu, ví dụ “(R)”).</p>
<ol style='line-height:150%'>
<li><b>Thông tin đơn vị:</b> tên đơn vị, kỳ thống kê (01/10/2025 – 30/9/2026), ngày chốt nhân lực (30/9/2026),
người đứng đầu, người lập biểu.</li>
<li>Thực hiện lần lượt <b>Bước 1 → Bước 7</b>. Mỗi bước có hướng dẫn nghiệp vụ ở trên và các biểu ở dưới.</li>
<li>Thao tác: <b>＋ Thêm dòng</b> (Ctrl+N); nhấp đúp hoặc gõ để sửa ô; <b>Enter</b> mở cửa sổ chi tiết;
<b>Delete</b> xóa. Ô nền <span style='background:#FDECEA'>đỏ nhạt</span> là bắt buộc; ô nền
<span style='background:#EEF3FA'>xanh nhạt</span> là cột công thức (ô xám, đã khóa trong bộ biểu).</li>
<li>Cột cảnh báo: <span style='color:#1E8E3E'><b>ĐẠT</b></span> mới được chuyển sang bước sau (B1 → C3, C3 → dự báo → D2).
Xử lý ở cột dữ liệu nguồn, không sửa nội dung cảnh báo.</li>
<li>Mã liên kết: A2 gắn công việc với nhiệm vụ (A1) và VTVL (C1); B1, B2 tự lấy mã VTVL từ A2. Đổi mã ở biểu gốc
thì biểu liên quan tự cập nhật.</li>
<li>Các nút trợ giúp: <i>Đồng bộ từ C1</i> (C2, C3), <i>Điền theo kết quả tính</i> (C3),
<i>Gợi ý nhân lực</i> (D1), <i>Tạo dự báo</i> và <i>Tạo phương án 2027–2031</i>.</li>
<li><b>Bước 8:</b> kiểm tra tự động; nhấp đúp từng dòng để đến đúng chỗ cần sửa. Xuất <b>vào Bộ biểu Excel chính
thức</b> (giữ nguyên công thức – phần mềm tự sửa các công thức lỗi của bản phát hành) và <b>báo cáo Word</b>.</li>
<li><b>Tệp → Nhập từ Bộ biểu Excel</b>: kế thừa dữ liệu đã điền trong bộ biểu chính thức (kể cả do cơ quan đầu mối
chuyển dữ liệu theo Công văn 1972, 2209, 2342-CV/BTCTW).</li>
<li>Dữ liệu tự lưu vào tệp hồ sơ <code>.vtvl</code>; dùng <b>Tệp → Lưu thành (sao lưu)</b> để giữ phiên bản.</li>
</ol>
<h3 style='color:#083C6B'>Nguyên tắc cần nhớ</h3>
<ul style='line-height:150%'>
<li>VTVL xác định từ chức năng, nhiệm vụ; không xuất phát từ người hiện có, ngạch, mức lương hoặc số biên chế đã giao.</li>
<li>Tính giờ lao động thực tế; không cộng tỷ lệ 10–15% hay hệ số cố định cho phần chưa đo; không lấy thời hạn xử lý làm giờ lao động.</li>
<li>Người quy đổi PP2 giữ số thập phân, không tự làm tròn thành biên chế; không làm tròn tăng từng dòng rồi cộng.</li>
<li>Dữ liệu chưa kiểm chứng chỉ để tính thử, không làm căn cứ đề xuất biên chế; kết quả không tự động làm tăng biên chế,
không làm thay đổi lương, phụ cấp.</li>
<li>Đơn vị sự nghiệp: phân biệt viên chức, hợp đồng lao động, nguồn ngân sách và nguồn thu.</li>
</ul>
"""


class HelpPage(Page):
    def __init__(self):
        super().__init__()
        tb = QTextBrowser()
        tb.setObjectName("Guide")
        tb.setHtml(HELP_HTML)
        self.lay.addWidget(tb, 1)
