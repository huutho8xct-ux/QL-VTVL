"""Trang “Nhập từ Excel”: Chọn tệp → Kiểm tra tệp → Xem kết quả → Kết chuyển."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QRadioButton, QScrollArea, QStackedWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..core.forms import FORMS, INPUT_FORMS
from ..core.importer import (
    ERROR, FATAL, INFO, WARNING, analyze, apply, export_annotated, export_issues, save_blank_template,
    undo_last_import,
)
from . import theme
from .widgets import KpiCard, PageHeader, Stepper, badge_color

STEPS = [("Chọn tệp", "Một biểu hoặc cả bộ biểu"), ("Kiểm tra tệp", "Mẫu, sheet, tiêu đề, công thức"),
         ("Xem kết quả", "Lỗi đến từng ô"), ("Kết chuyển", "Ghi vào hồ sơ, tính lại")]
ICON = {FATAL: "⛔", ERROR: "⛔", WARNING: "⚠", INFO: "ⓘ"}


def level_color(level):
    return {FATAL: theme.ERR, ERROR: theme.ERR, WARNING: theme.WARN, INFO: theme.INFO_C}[level]


class DropZone(QFrame):
    dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(220)
        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignCenter)
        ic = QLabel("⭱")
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"font-size: 34pt; color: {theme.PRIMARY};")
        t = QLabel("Kéo và thả tệp Excel (.xlsx) vào đây")
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-size: 13pt; font-weight: 600;")
        sub = QLabel("hoặc")
        sub.setAlignment(Qt.AlignCenter)
        sub.setObjectName("PageSub")
        self.btn = QPushButton("Chọn tệp từ máy tính…")
        self.btn.setObjectName("Primary")
        self.btn.setCursor(Qt.PointingHandCursor)
        for w in (ic, t, sub):
            v.addWidget(w)
        v.addWidget(self.btn, 0, Qt.AlignCenter)
        hint = QLabel("Dùng Bộ biểu VTVL kèm Hướng dẫn 7-HD/BTCTW. Tệp được kiểm tra ngay trên máy, chưa ghi vào hồ sơ.")
        hint.setObjectName("PageSub")
        hint.setAlignment(Qt.AlignCenter)
        v.addWidget(hint)

    def _set_hover(self, on):
        self.setProperty("hover", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, e):
        urls = e.mimeData().urls()
        if urls and urls[0].toLocalFile().lower().endswith((".xlsx", ".xls", ".xlsm", ".csv")):
            e.acceptProposedAction()
            self._set_hover(True)

    def dragLeaveEvent(self, e):
        self._set_hover(False)

    def dropEvent(self, e):
        self._set_hover(False)
        urls = e.mimeData().urls()
        if urls:
            self.dropped.emit(urls[0].toLocalFile())


class SheetTabs(QWidget):
    """Hàng tab theo sheet (tự xuống dòng), mỗi tab có nhãn trạng thái màu: Đạt / n lỗi / Xem lại."""
    currentChanged = Signal(int)

    def __init__(self, per_row=6, parent=None):
        super().__init__(parent)
        self.per_row = per_row
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 4, 0, 4)
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(6)
        self.buttons = []
        self._current = -1

    def set_tabs(self, tabs):
        for b in self.buttons:
            b.deleteLater()
        self.buttons = []
        for i, (name, badge, color) in enumerate(tabs):
            b = QPushButton()
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            lbl = QLabel(f"{name} &nbsp;&nbsp;<b><span style='color:{color};'>{badge}</span></b>")
            lbl.setTextFormat(Qt.RichText)
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            hl = QHBoxLayout(b)
            hl.setContentsMargins(10, 4, 10, 4)
            hl.addWidget(lbl)
            b.setMinimumHeight(38)
            b.clicked.connect(lambda _=False, k=i: self.setCurrentIndex(k))
            self.grid.addWidget(b, i // self.per_row, i % self.per_row)
            self.buttons.append(b)
        self._current = -1
        self.setCurrentIndex(0 if tabs else -1)

    def setCurrentIndex(self, i):
        for k, b in enumerate(self.buttons):
            b.setChecked(k == i)
            b.setStyleSheet(f"QPushButton {{ border: 2px solid {theme.PRIMARY}; border-radius: 10px; }}" if k == i
                            else "QPushButton { border-radius: 10px; }")
        if i != self._current:
            self._current = i
            self.currentChanged.emit(i)

    def currentIndex(self):
        return self._current


class ImportPage(QWidget):
    open_form = Signal(str, str)     # mã biểu, mã bản ghi
    imported = Signal()

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.setObjectName("Page")
        self.project = project
        self.rep = None
        self.stats = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        body = QWidget()
        body.setObjectName("ScrollBody")
        sc.setWidget(body)
        outer.addWidget(sc)
        lay = QVBoxLayout(body)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(14)
        ky = project.meta().get("ky_thong_ke", "")
        self.header = PageHeader(f"Trang làm việc / Hồ sơ Kỳ {ky} / Nhập từ Excel", "Nhập dữ liệu từ tệp Excel",
                                 "Phần mềm đọc tệp vào vùng kiểm tra riêng, báo kết quả đến từng ô; số liệu chính thức "
                                 "của hồ sơ chỉ thay đổi khi bấm <b>Kết chuyển</b>.")
        tpl = QPushButton("⭳  Tải biểu mẫu chuẩn")
        tpl.setToolTip("Lưu Bộ biểu Excel chuẩn (đã sửa các công thức lỗi của bản phát hành) để phát cho người điền")
        tpl.clicked.connect(self.download_template)
        self.header.add_button(tpl)
        lay.addWidget(self.header)
        self.stepper = Stepper(STEPS)
        self.stepper.clicked.connect(self._step_clicked)
        lay.addWidget(self.stepper)
        banner = QLabel("ⓘ   Tệp được kiểm tra ngay trên máy này, không cần mạng. Sau khi kết chuyển, vào "
                        "<b>Kiểm tra và gửi</b> để đóng gói hồ sơ gửi cơ quan quản lý.")
        banner.setObjectName("InfoBanner")
        banner.setWordWrap(True)
        lay.addWidget(banner)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self._build_choose()
        self._build_checking()
        self._build_result()
        self._build_commit()
        self.go(0)

    # ------------------------------------------------------------- bước 1
    def _build_choose(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        self.drop = DropZone()
        self.drop.btn.clicked.connect(self.pick_file)
        self.drop.dropped.connect(self.load_file)
        v.addWidget(self.drop)
        scope = QFrame()
        scope.setObjectName("Card")
        h = QHBoxLayout(scope)
        h.addWidget(QLabel("<b>Phạm vi kiểm tra:</b>"))
        self.rb_all = QRadioButton("Cả bộ biểu")
        self.rb_one = QRadioButton("Một biểu:")
        self.rb_all.setChecked(True)
        g = QButtonGroup(self)
        g.addButton(self.rb_all)
        g.addButton(self.rb_one)
        self.cb_form = QComboBox()
        for c in INPUT_FORMS:
            self.cb_form.addItem(f"{FORMS[c].sheet} – {FORMS[c].title}", c)
        self.cb_form.currentIndexChanged.connect(lambda _: self.rb_one.setChecked(True))
        h.addWidget(self.rb_all)
        h.addWidget(self.rb_one)
        h.addWidget(self.cb_form)
        h.addStretch(1)
        v.addWidget(scope)
        v.addStretch(1)
        self.stack.addWidget(w)

    def set_scope(self, code=None):
        if code and code in INPUT_FORMS:
            self.rb_one.setChecked(True)
            self.cb_form.setCurrentIndex(INPUT_FORMS.index(code))
        else:
            self.rb_all.setChecked(True)

    # ------------------------------------------------------------- bước 2
    def _build_checking(self):
        w = QFrame()
        w.setObjectName("Card")
        v = QVBoxLayout(w)
        self.check_lbl = QLabel("Đang kiểm tra tệp…")
        self.check_lbl.setAlignment(Qt.AlignCenter)
        self.check_lbl.setStyleSheet("font-size: 13pt; padding: 40px;")
        self.check_lbl.setWordWrap(True)
        v.addWidget(self.check_lbl)
        row = QHBoxLayout()
        row.addStretch(1)
        b = QPushButton("Chọn tệp khác")
        b.clicked.connect(lambda: self.go(0))
        row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)
        self.stack.addWidget(w)

    # ------------------------------------------------------------- bước 3
    def _build_result(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(14)
        self.file_lbl = QLabel()
        self.file_lbl.setTextFormat(Qt.RichText)
        self.file_lbl.setWordWrap(True)
        v.addWidget(self.file_lbl)
        grid = QGridLayout()
        grid.setSpacing(16)
        self.k_total = KpiCard("Tổng số dòng kiểm tra", theme.INFO_C)
        self.k_err = KpiCard("Số dòng có lỗi, cần sửa", theme.ERR)
        self.k_ok = KpiCard("Số dòng hợp lệ", theme.OK)
        for i, k in enumerate((self.k_total, self.k_err, self.k_ok)):
            grid.addWidget(k, 0, i)
        v.addLayout(grid)
        card = QFrame()
        card.setObjectName("Card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(16, 14, 16, 14)
        top = QHBoxLayout()
        t = QLabel("Chi tiết theo sheet")
        t.setStyleSheet("font-size: 13.5pt; font-weight: 700;")
        top.addWidget(t)
        top.addStretch(1)
        top.addWidget(QLabel("Mức:"))
        self.lvl = QComboBox()
        self.lvl.addItems(["Tất cả", "Lỗi", "Cần xem lại", "Lưu ý"])
        self.lvl.currentIndexChanged.connect(self._fill_table)
        top.addWidget(self.lvl)
        b1 = QPushButton("⭳  Tải về tệp kết quả có cột báo lỗi")
        b1.setToolTip("Bản sao tệp đã chọn: thêm cột KẾT QUẢ KIỂM TRA ở mỗi sheet, tô màu và ghi chú tại ô lỗi")
        b1.clicked.connect(self.download_annotated)
        b2 = QPushButton("Danh sách lỗi")
        b2.setToolTip("Xuất danh sách lỗi ra một bảng Excel")
        b2.clicked.connect(self.download_list)
        top.addWidget(b1)
        top.addWidget(b2)
        cv.addLayout(top)
        self.tabs = SheetTabs()
        self.tabs.currentChanged.connect(self._fill_table)
        cv.addWidget(self.tabs)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Ô", "Cột", "Mức", "Nội dung", "Cách xử lý", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setWordWrap(True)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        for j, wd in ((0, 70), (1, 60), (2, 130), (5, 130)):
            self.table.setColumnWidth(j, wd)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setMinimumHeight(360)
        self.table.cellClicked.connect(self._cell_clicked)
        cv.addWidget(self.table)
        v.addWidget(card)
        nav = QHBoxLayout()
        b = QPushButton("◀  Chọn tệp khác")
        b.clicked.connect(lambda: self.go(0))
        nav.addWidget(b)
        nav.addStretch(1)
        self.to_commit = QPushButton("Tiếp tục: Kết chuyển  ▶")
        self.to_commit.setObjectName("Primary")
        self.to_commit.clicked.connect(lambda: self.go(3))
        nav.addWidget(self.to_commit)
        v.addLayout(nav)
        self.stack.addWidget(w)

    # ------------------------------------------------------------- bước 4
    def _build_commit(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)
        card = QFrame()
        card.setObjectName("Card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(16, 14, 16, 14)
        t = QLabel("Kết chuyển vào hồ sơ")
        t.setStyleSheet("font-size: 13.5pt; font-weight: 700;")
        cv.addWidget(t)
        cv.addWidget(QLabel("Chọn biểu cần kết chuyển (chỉ biểu có sheet đúng cấu trúc và có dữ liệu):"))
        self.sel = QTableWidget(0, 6)
        self.sel.setHorizontalHeaderLabels(["Kết chuyển", "Biểu", "Sheet", "Dòng hợp lệ", "Dòng lỗi", "Tình trạng"])
        self.sel.verticalHeader().setVisible(False)
        self.sel.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sel.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.sel.setMinimumHeight(300)
        cv.addWidget(self.sel)
        opt = QHBoxLayout()
        opt.addWidget(QLabel("<b>Cách ghi:</b>"))
        self.rb_replace = QRadioButton("Thay thế toàn bộ dữ liệu của biểu đã chọn")
        self.rb_merge = QRadioButton("Bổ sung / cập nhật theo mã (giữ dòng không có trong tệp)")
        self.rb_merge.setChecked(True)
        g = QButtonGroup(self)
        g.addButton(self.rb_replace)
        g.addButton(self.rb_merge)
        opt.addWidget(self.rb_merge)
        opt.addWidget(self.rb_replace)
        opt.addStretch(1)
        self.skip = QCheckBox("Bỏ qua các dòng có lỗi")
        self.skip.setChecked(True)
        self.skip.stateChanged.connect(self._update_commit)
        opt.addWidget(self.skip)
        cv.addLayout(opt)
        self.commit_note = QLabel()
        self.commit_note.setObjectName("Note")
        self.commit_note.setWordWrap(True)
        cv.addWidget(self.commit_note)
        v.addWidget(card)
        nav = QHBoxLayout()
        b = QPushButton("◀  Xem lại kết quả kiểm tra")
        b.clicked.connect(lambda: self.go(2))
        nav.addWidget(b)
        nav.addStretch(1)
        self.btn_commit = QPushButton("✔  Kết chuyển")
        self.btn_commit.setObjectName("Primary")
        self.btn_commit.clicked.connect(self.commit)
        nav.addWidget(self.btn_commit)
        v.addLayout(nav)
        self.done_card = QFrame()
        self.done_card.setObjectName("Card")
        dv = QVBoxLayout(self.done_card)
        self.done_lbl = QLabel()
        self.done_lbl.setTextFormat(Qt.RichText)
        self.done_lbl.setWordWrap(True)
        dv.addWidget(self.done_lbl)
        row = QHBoxLayout()
        b_undo = QPushButton("↶  Hoàn tác lần kết chuyển này")
        b_undo.clicked.connect(self.undo)
        b_new = QPushButton("Nhập tệp khác")
        b_new.clicked.connect(self.reset)
        b_open = QPushButton("Mở Nhập 09 biểu")
        b_open.setObjectName("Primary")
        b_open.clicked.connect(lambda: self.open_form.emit(self._first_code(), ""))
        row.addWidget(b_undo)
        row.addStretch(1)
        row.addWidget(b_new)
        row.addWidget(b_open)
        dv.addLayout(row)
        self.done_card.hide()
        v.addWidget(self.done_card)
        v.addStretch(1)
        self.stack.addWidget(w)

    # ------------------------------------------------------------- điều hướng
    def go(self, i):
        if i >= 2 and self.rep is None:
            i = 0
        if i == 3 and self.rep is not None and self.rep.fatal:
            i = 2
        self.stack.setCurrentIndex(i)
        done = set(range(i))
        if self.stats is not None:
            done = {0, 1, 2, 3}
        self.stepper.set_state(i, done)
        if i == 3:
            self._fill_commit()

    def _step_clicked(self, i):
        if i == 0 or self.rep is not None:
            self.go(i if i != 1 else 2)

    def reset(self):
        self.rep = None
        self.stats = None
        self.done_card.hide()
        self.btn_commit.setEnabled(True)
        self.go(0)

    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn tệp Bộ biểu Excel", "", "Excel (*.xlsx);;Tất cả tệp (*.*)")
        if path:
            self.load_file(path)

    def load_file(self, path):
        self.stats = None
        self.done_card.hide()
        self.btn_commit.setEnabled(True)
        self.go(1)
        self.check_lbl.setText(f"Đang kiểm tra tệp <b>{os.path.basename(path)}</b>: mẫu, sheet, tiêu đề, công thức…")
        QApplication.processEvents()
        codes = [self.cb_form.currentData()] if self.rb_one.isChecked() else None
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.rep = analyze(path, self.project, codes)
        finally:
            QApplication.restoreOverrideCursor()
        self._show_result()
        self.go(2)

    # ------------------------------------------------------------- hiển thị kết quả
    def _show_result(self):
        rep = self.rep
        n_e = rep.count(ERROR) + rep.count(FATAL)
        n_w, n_i = rep.count(WARNING), rep.count(INFO)
        if rep.fatal:
            verdict = f"<span style='color:{theme.ERR}'><b>⛔ Không nhập được tệp này.</b></span>"
        elif rep.error_rows or n_e:
            verdict = f"<span style='color:{theme.WARN}'><b>Có lỗi cần sửa</b></span> (có thể bỏ qua dòng lỗi khi kết chuyển)"
        else:
            verdict = f"<span style='color:{theme.OK}'><b>✔ Tệp hợp lệ, sẵn sàng kết chuyển.</b></span>"
        self.file_lbl.setText(f"📄 <b>{os.path.basename(rep.path)}</b> &nbsp;·&nbsp; {rep.version or 'Chưa nhận dạng được'}"
                              f" &nbsp;·&nbsp; kiểm tra lúc {rep.checked_at} &nbsp;·&nbsp; {verdict} &nbsp;·&nbsp; "
                              f"{n_e} lỗi · {n_w} cần xem lại · {n_i} lưu ý")
        self.k_total.value.setText(f"{rep.total_rows:,}".replace(",", "."))
        self.k_err.value.setText(f"{rep.error_rows:,}".replace(",", "."))
        self.k_ok.value.setText(f"{rep.valid_rows:,}".replace(",", "."))
        tabs = []
        self.tab_keys = []
        general = [i for i in rep.issues if not i.code]
        if general or rep.fatal:
            tabs.append(("Toàn tệp", "Không nhập được" if rep.fatal else f"{len(general)} thông báo",
                         theme.ERR if rep.fatal else theme.WARN))
            self.tab_keys.append(None)
        order = sorted((r for r in rep.sheets.values() if r.found),
                       key=lambda r: (0 if (r.bad_rows or not r.structure_ok) else 1 if r.review_rows else 2, r.sheet))
        for r in order:
            tabs.append((r.sheet, r.badge(), badge_color(r.badge())))
            self.tab_keys.append(r.code)
        self.tabs.set_tabs(tabs)
        self.to_commit.setEnabled(not rep.fatal)
        self._fill_table()

    def _fill_table(self):
        if self.rep is None or self.tabs.currentIndex() < 0:
            self.table.setRowCount(0)
            return
        code = self.tab_keys[self.tabs.currentIndex()]
        want = {0: None, 1: {ERROR, FATAL}, 2: {WARNING}, 3: {INFO}}[self.lvl.currentIndex()]
        items = [i for i in self.rep.issues if (i.code or None) == code and (want is None or i.level in want)]
        self.table.setRowCount(0)
        self.table.setRowCount(len(items))
        for r, i in enumerate(items):
            vals = (i.cell, i.column, f"{ICON[i.level]} {i.level}", i.message + (f"  [{i.value}]" if i.value and
                                                                              i.value not in i.message else ""),
                    i.fix)
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 2:
                    it.setForeground(QBrush(QColor(level_color(i.level))))
                if c == 1 and i.label:
                    it.setToolTip(i.label)
                if c in (3, 4):
                    it.setToolTip(v)
                self.table.setItem(r, c, it)
            if i.code and i.key:
                link = QTableWidgetItem("Mở trong biểu  ›")
                link.setForeground(QBrush(QColor(theme.PRIMARY)))
                f = link.font()
                f.setBold(True)
                link.setFont(f)
                link.setData(Qt.UserRole, (i.code, i.key))
                link.setToolTip(f"Mở Biểu {i.code} tại bản ghi {i.key}")
                self.table.setItem(r, 5, link)
        if not items:
            self.table.setRowCount(1)
            msg = "✔ Không có lỗi trong sheet này." if code else "Không có thông báo."
            it = QTableWidgetItem(msg)
            it.setForeground(QBrush(QColor(theme.OK)))
            self.table.setItem(0, 3, it)

    def _cell_clicked(self, r, c):
        it = self.table.item(r, c)
        data = it.data(Qt.UserRole) if it is not None and c == 5 else None
        if data:
            self.open_form.emit(*data)

    # ------------------------------------------------------------- kết chuyển
    def _fill_commit(self):
        rep = self.rep
        self.sel.setRowCount(0)
        self.checks = {}
        for code, r in rep.sheets.items():
            row = self.sel.rowCount()
            self.sel.insertRow(row)
            chk = QCheckBox()
            enabled = r.found and r.structure_ok and r.n_rows > 0 and not rep.fatal and self.stats is None
            chk.setChecked(enabled)
            chk.setEnabled(enabled)
            chk.stateChanged.connect(self._update_commit)
            holder = QWidget()
            hl = QHBoxLayout(holder)
            hl.setContentsMargins(14, 0, 0, 0)
            hl.addWidget(chk)
            self.sel.setCellWidget(row, 0, holder)
            self.checks[code] = chk
            status = r.badge()
            vals = [f"{code} – {FORMS[code].title}", r.sheet, str(r.n_ok) if r.found else "–",
                    str(len(r.bad_rows)) if r.found else "–",
                    {"Không có": "Không có sheet – giữ nguyên dữ liệu hiện có",
                     "Trống": "Sheet trống – giữ nguyên dữ liệu hiện có",
                     "Sai cấu trúc": "Sai cấu trúc cột – không kết chuyển"}.get(status, status)]
            for j, v in enumerate(vals, 1):
                it = QTableWidgetItem(v)
                if j == 5:
                    it.setForeground(QBrush(QColor(badge_color(status))))
                self.sel.setItem(row, j, it)
        self.sel.resizeColumnsToContents()
        self.sel.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self._update_commit()

    def selected(self):
        return [c for c, chk in getattr(self, "checks", {}).items() if chk.isChecked() and chk.isEnabled()]

    def _update_commit(self):
        if self.rep is None:
            return
        codes = self.selected()
        ok = bool(codes) and self.rep.importable(codes, self.skip.isChecked()) and self.stats is None
        self.btn_commit.setEnabled(ok)
        bad = sum(len(self.rep.sheets[c].bad_rows) for c in codes)
        txt = "Trước khi kết chuyển, phần mềm tự sao lưu hồ sơ; có thể hoàn tác. Ô công thức trong tệp không được " \
              "nhập – phần mềm tự tính lại theo công thức của bộ biểu."
        if bad and not self.skip.isChecked():
            txt = f"⚠ Biểu đã chọn còn {bad} dòng lỗi: chọn “Bỏ qua các dòng có lỗi” hoặc sửa tệp rồi kiểm tra lại. " + txt
        elif bad:
            txt = f"{bad} dòng lỗi sẽ được bỏ qua. " + txt
        self.commit_note.setText(txt)

    def commit(self):
        codes = self.selected()
        mode = "merge" if self.rb_merge.isChecked() else "replace"
        lost = [c for c in codes if mode == "replace" and self.project.count(c)]
        if lost and QMessageBox.question(
                self, "Xác nhận thay thế",
                f"Dữ liệu hiện có của {', '.join(lost)} sẽ được thay bằng dữ liệu trong tệp. Tiếp tục?") != QMessageBox.Yes:
            return
        try:
            self.stats = apply(self.project, self.rep, codes, mode=mode, skip_errors=self.skip.isChecked())
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không kết chuyển được: {e}")
            return
        lines = []
        for c, v in self.stats.items():
            t = f"<li><b>{c}</b>: thêm {v['added']}"
            if v["updated"]:
                t += f", cập nhật {v['updated']}"
            if v["skipped"]:
                t += f", bỏ qua {v['skipped']} dòng lỗi"
            lines.append(t + "</li>")
        self.done_lbl.setText(f"<span style='color:{theme.OK}; font-size:13pt'><b>✔ Đã kết chuyển vào hồ sơ và tính "
                              f"lại toàn bộ.</b></span><ul>{''.join(lines)}</ul>Vào <b>Lỗi và giải trình</b> hoặc "
                              "<b>Kiểm tra và gửi</b> để rà soát toàn hồ sơ.")
        self.done_card.show()
        self.btn_commit.setEnabled(False)
        self.go(3)
        self.imported.emit()

    def undo(self):
        if QMessageBox.question(self, "Hoàn tác", "Khôi phục hồ sơ về trạng thái trước lần kết chuyển này?") \
                != QMessageBox.Yes:
            return
        if undo_last_import(self.project):
            QMessageBox.information(self, "Hoàn tác", "Đã khôi phục hồ sơ.")
            self.reset()
            self.imported.emit()
        else:
            QMessageBox.warning(self, "Hoàn tác", "Không tìm thấy bản sao lưu của lần kết chuyển.")

    def _first_code(self):
        return next(iter(self.stats), "A1") if self.stats else "A1"

    # ------------------------------------------------------------- tải tệp
    def _save_path(self, title, name):
        path, _ = QFileDialog.getSaveFileName(self, title, name, "Excel (*.xlsx)")
        if path and not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        return path

    def download_template(self):
        path = self._save_path("Lưu biểu mẫu chuẩn", "BoBieu_VTVL_19-10-2026_mau_chuan.xlsx")
        if not path:
            return
        try:
            save_blank_template(self.project, path)
        except PermissionError:
            QMessageBox.critical(self, "Lỗi", "Không ghi được tệp – hãy đóng tệp nếu đang mở.")
            return
        QMessageBox.information(self, "Đã lưu", f"Đã lưu biểu mẫu chuẩn:\n{path}")

    def download_annotated(self):
        if self.rep is None or self.rep.fatal:
            return
        base = os.path.splitext(os.path.basename(self.rep.path))[0]
        path = self._save_path("Lưu tệp kết quả có cột báo lỗi", f"{base}_KetQuaKiemTra.xlsx")
        if not path:
            return
        try:
            n = export_annotated(self.rep, path)
        except PermissionError:
            QMessageBox.critical(self, "Lỗi", "Không ghi được tệp – hãy đóng tệp nếu đang mở.")
            return
        QMessageBox.information(self, "Đã lưu", f"Đã lưu tệp kết quả ({n} ô được tô màu, ghi chú):\n{path}\n\n"
                                "Gửi tệp này cho người điền để sửa đúng ô bị báo lỗi.")

    def download_list(self):
        if self.rep is None:
            return
        base = os.path.splitext(os.path.basename(self.rep.path))[0]
        path = self._save_path("Lưu danh sách lỗi", f"DanhSachLoi_{base}.xlsx")
        if path:
            export_issues(self.rep, path)
            QMessageBox.information(self, "Đã lưu", f"Đã lưu:\n{path}")
