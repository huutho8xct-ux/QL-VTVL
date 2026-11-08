"""Hộp thoại kiểm tra và xem trước khi nhập tệp Bộ biểu Excel."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QMessageBox, QPushButton, QRadioButton, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..core.forms import FORMS
from ..core.importer import ERROR, FATAL, INFO, WARNING, analyze, apply, export_issues
from . import theme

COLORS = {FATAL: theme.ERR, ERROR: theme.ERR, WARNING: theme.WARN, INFO: theme.PRIMARY}
ICONS = {FATAL: "⛔", ERROR: "⛔", WARNING: "⚠", INFO: "ⓘ"}


class ImportDialog(QDialog):
    """Kiểm soát lỗi 3 lớp, xem trước, chọn biểu và cách nhập; sao lưu trước khi ghi."""

    def __init__(self, project, path: str, codes=None, parent=None):
        super().__init__(parent)
        self.project = project
        self.path = path
        self.stats = None
        self.setWindowTitle("Kiểm tra tệp trước khi nhập")
        self.resize(1180, 760)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.rep = analyze(path, project, codes)
        finally:
            QApplication.restoreOverrideCursor()
        rep = self.rep

        lay = QVBoxLayout(self)
        title = QLabel(f"📄 {os.path.basename(path)}")
        title.setObjectName("PageTitle")
        lay.addWidget(title)
        n_f, n_e, n_w, n_i = (rep.count(x) for x in (FATAL, ERROR, WARNING, INFO))
        if rep.fatal:
            verdict = f"<span style='color:{theme.ERR}'><b>⛔ Không nhập được tệp này.</b></span>"
        elif n_e:
            verdict = (f"<span style='color:{theme.WARN}'><b>⚠ Có {n_e} lỗi.</b></span> Các dòng lỗi sẽ được bỏ qua "
                       "(hoặc sửa tệp rồi kiểm tra lại).")
        elif n_w:
            verdict = f"<span style='color:{theme.WARN}'><b>Có {n_w} cảnh báo</b></span> – vẫn nhập được."
        else:
            verdict = f"<span style='color:{theme.OK}'><b>✔ Tệp hợp lệ, sẵn sàng nhập.</b></span>"
        sub = QLabel(f"{rep.version or 'Chưa nhận dạng được bộ biểu'} &nbsp;·&nbsp; {verdict} &nbsp;·&nbsp; "
                     f"{n_e + n_f} lỗi · {n_w} cảnh báo · {n_i} lưu ý")
        sub.setTextFormat(Qt.RichText)
        sub.setWordWrap(True)
        lay.addWidget(sub)

        split = QSplitter(Qt.Vertical)
        # ---- bảng tổng hợp theo biểu
        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.addWidget(QLabel("<b>1. Chọn biểu cần nhập</b> (chỉ biểu có trang tính đúng cấu trúc mới chọn được)"))
        self.sheet_tbl = QTableWidget(0, 7)
        self.sheet_tbl.setHorizontalHeaderLabels(["Nhập", "Biểu", "Trang tính", "Dòng đọc được", "Dòng lỗi",
                                                  "Cảnh báo", "Tình trạng"])
        self.sheet_tbl.verticalHeader().setVisible(False)
        self.sheet_tbl.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.sheet_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.checks = {}
        for code, r in rep.sheets.items():
            row = self.sheet_tbl.rowCount()
            self.sheet_tbl.insertRow(row)
            chk = QCheckBox()
            enabled = r.found and r.structure_ok and r.n_rows > 0 and not rep.fatal
            chk.setChecked(enabled)
            chk.setEnabled(enabled)
            chk.stateChanged.connect(self._update_buttons)
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(10, 0, 0, 0)
            hl.addWidget(chk)
            self.sheet_tbl.setCellWidget(row, 0, w)
            self.checks[code] = chk
            if not r.found:
                status, color = "Không có trang này trong tệp – giữ nguyên dữ liệu hiện có", theme.MUTED
            elif not r.structure_ok:
                status, color = "Sai cấu trúc cột – không nhập", theme.ERR
            elif r.n_rows == 0:
                status, color = "Trang trống – giữ nguyên dữ liệu hiện có", theme.MUTED
            elif r.bad_rows:
                status, color = f"Nhập được {r.n_ok}/{r.n_rows} dòng (bỏ qua dòng lỗi)", theme.WARN
            else:
                status, color = "Hợp lệ", theme.OK
            vals = [f"{code if code != 'B2' else 'B2 chi tiết'} – {FORMS[code].title}", r.sheet,
                    str(r.n_rows) if r.found else "–", str(len(r.bad_rows)) if r.found else "–",
                    str(rep.count(WARNING, code)), status]
            for j, v in enumerate(vals, 1):
                it = QTableWidgetItem(v)
                if j == 6:
                    it.setForeground(QBrush(QColor(color)))
                if j in (4, 5) and v not in ("0", "–"):
                    it.setForeground(QBrush(QColor(theme.ERR if j == 4 else theme.WARN)))
                self.sheet_tbl.setItem(row, j, it)
        self.sheet_tbl.resizeColumnsToContents()
        self.sheet_tbl.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        tl.addWidget(self.sheet_tbl)
        split.addWidget(top)

        # ---- danh sách lỗi
        mid = QWidget()
        ml = QVBoxLayout(mid)
        ml.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("<b>2. Kết quả kiểm tra chi tiết</b> (ô cụ thể và hướng xử lý)"))
        bar.addStretch(1)
        bar.addWidget(QLabel("Mức độ:"))
        self.lvl = QComboBox()
        self.lvl.addItems(["Tất cả", f"{ERROR} và {FATAL}", WARNING, INFO])
        self.lvl.currentIndexChanged.connect(self._fill_issues)
        bar.addWidget(self.lvl)
        exp = QPushButton("⭳ Xuất danh sách lỗi (Excel)")
        exp.clicked.connect(self._export)
        bar.addWidget(exp)
        ml.addLayout(bar)
        self.iss = QTableWidget(0, 6)
        self.iss.setHorizontalHeaderLabels(["Mức độ", "Trang tính", "Ô", "Cột", "Giá trị", "Nội dung / hướng xử lý"])
        self.iss.verticalHeader().setVisible(False)
        self.iss.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.iss.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.iss.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        for j, w in enumerate((110, 150, 70, 170, 150)):
            self.iss.setColumnWidth(j, w)
        ml.addWidget(self.iss)
        split.addWidget(mid)
        split.setSizes([260, 360])
        lay.addWidget(split, 1)

        # ---- tùy chọn nhập
        opt = QFrame()
        opt.setObjectName("Card")
        ol = QHBoxLayout(opt)
        ol.addWidget(QLabel("<b>3. Cách nhập:</b>"))
        self.rb_replace = QRadioButton("Thay thế toàn bộ dữ liệu của biểu đã chọn")
        self.rb_merge = QRadioButton("Bổ sung / cập nhật theo mã (giữ dòng không có trong tệp)")
        self.rb_replace.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_replace)
        grp.addButton(self.rb_merge)
        ol.addWidget(self.rb_replace)
        ol.addWidget(self.rb_merge)
        ol.addStretch(1)
        self.skip = QCheckBox("Bỏ qua các dòng có lỗi")
        self.skip.setChecked(True)
        self.skip.stateChanged.connect(self._update_buttons)
        ol.addWidget(self.skip)
        lay.addWidget(opt)
        note = QLabel("ⓘ  Trước khi nhập, phần mềm tự sao lưu hồ sơ; có thể hoàn tác bằng menu Tệp → Hoàn tác lần nhập "
                      "gần nhất. Ô công thức (ô xám) trong tệp không được nhập – phần mềm tự tính lại.")
        note.setObjectName("Note")
        note.setWordWrap(True)
        lay.addWidget(note)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_ok = QPushButton("✔ Nhập dữ liệu")
        self.btn_ok.setObjectName("Primary")
        self.btn_ok.clicked.connect(self._do_import)
        cancel = QPushButton("Hủy")
        cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_ok)
        btns.addWidget(cancel)
        lay.addLayout(btns)
        self._fill_issues()
        self._update_buttons()

    def selected_codes(self):
        return [c for c, chk in self.checks.items() if chk.isChecked() and chk.isEnabled()]

    def _update_buttons(self):
        codes = self.selected_codes()
        ok = bool(codes) and self.rep.importable(codes, self.skip.isChecked())
        self.btn_ok.setEnabled(ok)
        if not codes:
            self.btn_ok.setToolTip("Chưa chọn biểu nào hợp lệ để nhập.")
        elif not ok:
            self.btn_ok.setToolTip("Biểu đã chọn còn dòng lỗi: chọn “Bỏ qua các dòng có lỗi” hoặc sửa tệp.")
        else:
            self.btn_ok.setToolTip("")

    def _fill_issues(self):
        idx = self.lvl.currentIndex()
        want = {0: None, 1: {ERROR, FATAL}, 2: {WARNING}, 3: {INFO}}[idx]
        items = [i for i in self.rep.issues if want is None or i.level in want]
        self.iss.setRowCount(len(items))
        for r, i in enumerate(items):
            for c, v in enumerate((f"{ICONS[i.level]} {i.level}", i.sheet, i.cell, i.column, i.value, i.message)):
                it = QTableWidgetItem(v)
                if c == 0:
                    it.setForeground(QBrush(QColor(COLORS[i.level])))
                if c == 5:
                    it.setToolTip(v)
                self.iss.setItem(r, c, it)

    def _export(self):
        base = os.path.splitext(os.path.basename(self.path))[0]
        path, _ = QFileDialog.getSaveFileName(self, "Lưu danh sách lỗi", f"KiemTra_{base}.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            export_issues(self.rep, path if path.lower().endswith(".xlsx") else path + ".xlsx")
        except PermissionError:
            QMessageBox.critical(self, "Lỗi", "Không ghi được tệp – hãy đóng tệp nếu đang mở.")
            return
        QMessageBox.information(self, "Đã lưu", f"Đã lưu danh sách lỗi:\n{path}")

    def _do_import(self):
        codes = self.selected_codes()
        mode = "merge" if self.rb_merge.isChecked() else "replace"
        skip = self.skip.isChecked()
        lost = [c for c in codes if mode == "replace" and self.project.count(c)]
        msg = (f"Nhập {len(codes)} biểu: {', '.join(codes)}.\n"
               + (f"Chế độ THAY THẾ: dữ liệu hiện có của {', '.join(lost)} sẽ được thay bằng dữ liệu trong tệp.\n"
                  if lost else "")
               + ("Các dòng lỗi sẽ bị bỏ qua.\n" if skip and any(self.rep.sheets[c].bad_rows for c in codes) else "")
               + "\nHồ sơ sẽ được sao lưu tự động trước khi nhập. Tiếp tục?")
        if QMessageBox.question(self, "Xác nhận nhập dữ liệu", msg) != QMessageBox.Yes:
            return
        try:
            self.stats = apply(self.project, self.rep, codes, mode=mode, skip_errors=skip)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không nhập được: {e}")
            return
        self.accept()

    def summary_text(self):
        if not self.stats:
            return ""
        lines = []
        for c, v in self.stats.items():
            t = f"• {c}: thêm {v['added']}"
            if v["updated"]:
                t += f", cập nhật {v['updated']}"
            if v["skipped"]:
                t += f", bỏ qua {v['skipped']} dòng lỗi"
            lines.append(t)
        return "\n".join(lines)


def run_import(parent, project, codes=None) -> bool:
    """Chọn tệp → kiểm tra → xem trước → nhập. Trả về True nếu đã nhập."""
    path, _ = QFileDialog.getOpenFileName(parent, "Chọn tệp Bộ biểu Excel cần nhập", "",
                                          "Excel (*.xlsx);;Tất cả tệp (*.*)")
    if not path:
        return False
    dlg = ImportDialog(project, path, codes, parent)
    if dlg.exec() != QDialog.Accepted:
        return False
    QMessageBox.information(parent, "Đã nhập dữ liệu",
                            "Kết quả nhập:\n" + dlg.summary_text() +
                            "\n\nVào Bước 8 để kiểm tra lại toàn bộ hồ sơ. Nếu cần, dùng Tệp → Hoàn tác lần nhập gần nhất.")
    return True
