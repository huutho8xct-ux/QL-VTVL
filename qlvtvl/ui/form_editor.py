"""Bảng nhập liệu dùng chung cho các biểu."""
from __future__ import annotations

import re

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QScrollArea, QStyledItemDelegate, QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..core.calc import Calculator, fmt, format_cv_list, has_num, num, parse_cv_list
from ..core.forms import ALL_FORMS, DEFAULT_QUY_GIO
from . import theme

KEY_PREFIX = {"A1": "NV", "A2": "CV", "C1": "VT"}
# Khi đổi mã ở biểu X thì cập nhật cột tham chiếu ở các biểu phụ thuộc
DEPENDENTS = {
    "A1": [("A2", "ma_nv")],
    "A2": [("B1", "ma_cv"), ("B2", "ma_cv")],
    "C1": [("C2", "ma_vt"), ("C3", "ma_vt"), ("D1", "ma_vt"), ("D2", "ma_vt")],
}
NUMERIC_CALC = {"tong_gio", "gio_b1", "gio_b2", "gio_can", "nguoi_quy_doi", "nguoi_can", "hien_co",
                "chenh_lech"}


def next_code(prefix: str, existing) -> str:
    n = 0
    for e in existing:
        m = re.match(rf"^{prefix}(\d+)$", str(e or ""))
        if m:
            n = max(n, int(m.group(1)))
    return f"{prefix}{n + 1:02d}"


def ref_items(calc: Calculator, ref: str):
    src = {"A1": calc.a1, "A2": calc.a2, "C1": calc.c1}.get(ref, {})
    return [(k, v.get("ten", "")) for k, v in src.items()]


class FormModel(QAbstractTableModel):
    def __init__(self, project, code: str, parent=None):
        super().__init__(parent)
        self.project = project
        self.code = code
        self.form = ALL_FORMS[code]
        self.cols = list(self.form.columns)
        self.calc = Calculator(project)
        self.rows = project.rows(code)
        self._silent = False

    # ----------------------------------------------------------- structure
    def reload(self):
        self.beginResetModel()
        self.calc.refresh()
        self.rows = self.project.rows(self.code)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.cols) + 1

    def col_at(self, column: int):
        return None if column == 0 else self.cols[column - 1]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return "STT" if section == 0 else self.cols[section - 1].label
            if role == Qt.ToolTipRole and section > 0:
                c = self.cols[section - 1]
                t = c.label
                if c.tip:
                    t += "\n" + c.tip
                if c.kind == "calc":
                    t += "\n(Tự động tính)"
                if c.required:
                    t += "\n(Bắt buộc)"
                return t
            if role == Qt.ForegroundRole and section > 0 and self.cols[section - 1].kind == "calc":
                return QBrush(QColor(theme.MUTED))
        return None

    def flags(self, index):
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        c = self.col_at(index.column())
        if c and c.kind != "calc":
            f |= Qt.ItemIsEditable
        return f

    # ---------------------------------------------------------------- data
    def raw(self, row: int, key: str):
        return self.calc.value(self.code, self.rows[row], key)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        r = self.rows[index.row()]
        c = self.col_at(index.column())
        if c is None:
            if role == Qt.DisplayRole:
                return index.row() + 1
            if role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            if role == Qt.ForegroundRole:
                return QBrush(QColor(theme.MUTED))
            return None
        v = self.calc.value(self.code, r, c.key)
        numeric = c.kind in ("int", "float") or c.key in NUMERIC_CALC
        if role == Qt.DisplayRole:
            if numeric:
                if v is None or v == "":
                    return ""
                if c.key == "nguoi_can" and self.code == "C3" and not has_num(v):
                    return ""
                return fmt(v, 3 if c.key in ("nguoi_quy_doi", "nguoi_can", "chenh_lech") else 2)
            if c.kind == "ref":
                return v or ""
            return "" if v is None else str(v)
        if role == Qt.EditRole:
            return "" if v is None else v
        if role == Qt.ToolTipRole:
            if c.kind == "ref" and v:
                name = dict(ref_items(self.calc, c.ref)).get(v)
                return f"{v}: {name}" if name else f"{v}: (không tồn tại trong biểu {c.ref})"
            if c.kind == "multiref":
                lines = []
                for code, share in parse_cv_list(v):
                    lines.append(f"{code} ({fmt(share * 100)}%): {self.calc.a2.get(code, {}).get('ten', '?')}")
                return "\n".join(lines) or c.tip
            if v not in (None, "") and not numeric:
                return str(v)
            return c.tip or None
        if role == Qt.TextAlignmentRole:
            return (Qt.AlignRight | Qt.AlignVCenter) if numeric else (Qt.AlignLeft | Qt.AlignVCenter)
        if role == Qt.BackgroundRole:
            if c.kind == "calc":
                return QBrush(QColor(theme.CALC_BG))
            if c.required and str(r.get(c.key, "")).strip() == "":
                return QBrush(QColor("#FDECEA"))
            if c.kind == "ref" and v and v not in dict(ref_items(self.calc, c.ref)):
                return QBrush(QColor("#FFE0B2"))
        if role == Qt.ForegroundRole:
            if c.key == "chenh_lech" and has_num(v):
                f = num(v)
                if f <= -0.5:
                    return QBrush(QColor(theme.ERR))
                if f >= 0.5:
                    return QBrush(QColor(theme.WARN))
            if c.kind == "calc":
                return QBrush(QColor("#34495E"))
        if role == Qt.FontRole and c.key in ("nguoi_can", "nguoi_quy_doi", "tong_gio", "gio_can"):
            from PySide6.QtGui import QFont
            fnt = QFont()
            fnt.setBold(True)
            return fnt
        return None

    def convert(self, c, value):
        if c.kind in ("float", "int"):
            if value is None or str(value).strip() == "":
                return None
            v = num(value, None)
            if v is None:
                raise ValueError(f"'{value}' không phải là số hợp lệ.")
            return int(round(v)) if c.kind == "int" else v
        return "" if value is None else str(value).strip()

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        c = self.col_at(index.column())
        if c is None or c.kind == "calc":
            return False
        try:
            v = self.convert(c, value)
        except ValueError as e:
            QMessageBox.warning(None, "Dữ liệu không hợp lệ", str(e))
            return False
        return self.set_values(index.row(), {c.key: v})

    def set_values(self, row: int, values: dict) -> bool:
        r = self.rows[row]
        old_key = r.get(self.form.key_col) if self.form.key_col else None
        if all(r.get(k) == v for k, v in values.items()):
            return False
        self.project.update_row(r["_id"], values, notify=False)
        r.update(values)
        new_key = r.get(self.form.key_col) if self.form.key_col else None
        if old_key and new_key != old_key and self.code in DEPENDENTS:
            self.project.rename_key(DEPENDENTS[self.code], old_key, new_key)
            if self.code == "A2":
                for cr in self.project.rows("C3"):
                    items = parse_cv_list(cr.get("ds_cv"))
                    if any(code == old_key for code, _ in items):
                        items = [(new_key if code == old_key else code, s) for code, s in items]
                        self.project.update_row(cr["_id"], {"ds_cv": format_cv_list(items)}, notify=False)
        self.calc.refresh()
        self.dataChanged.emit(self.index(0, 0), self.index(len(self.rows) - 1, len(self.cols)))
        self._silent = True
        try:
            self.project._notify(self.code)
        finally:
            self._silent = False
        return True


class FormDelegate(QStyledItemDelegate):
    def __init__(self, model: FormModel, parent=None):
        super().__init__(parent)
        self.m = model

    def _src(self, index):
        proxy = index.model()
        return proxy.mapToSource(index) if isinstance(proxy, QSortFilterProxyModel) else index

    def createEditor(self, parent, option, index):
        c = self.m.col_at(self._src(index).column())
        if c is None or c.kind in ("calc", "multiref"):
            return None
        if c.kind == "choice":
            cb = QComboBox(parent)
            cb.addItem("")
            cb.addItems(list(c.options))
            return cb
        if c.kind == "ref":
            cb = QComboBox(parent)
            cb.setEditable(True)
            cb.addItem("")
            for k, name in ref_items(self.m.calc, c.ref):
                cb.addItem(f"{k} — {name}", k)
            cb.view().setMinimumWidth(420)
            return cb
        ed = QLineEdit(parent)
        if c.tip:
            ed.setPlaceholderText(c.tip)
        return ed

    def setEditorData(self, editor, index):
        v = index.model().data(index, Qt.EditRole)
        if isinstance(editor, QComboBox):
            c = self.m.col_at(self._src(index).column())
            if c.kind == "ref":
                i = editor.findData(v)
                editor.setCurrentIndex(i) if i >= 0 else editor.setEditText(str(v or ""))
            else:
                i = editor.findText(str(v or ""))
                editor.setCurrentIndex(max(0, i))
            QTimer.singleShot(0, editor.showPopup)
        else:
            if isinstance(v, float):
                v = fmt(v, 4).replace(".", "")
            editor.setText("" if v is None else str(v))

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            c = self.m.col_at(self._src(index).column())
            if c.kind == "ref":
                data = editor.currentData()
                text = editor.currentText()
                value = data if data and text.startswith(str(data)) else text.split(" — ")[0].strip()
            else:
                value = editor.currentText()
            model.setData(index, value, Qt.EditRole)
        else:
            model.setData(index, editor.text(), Qt.EditRole)


# ------------------------------------------------------------------ dialogs
class CvPicker(QDialog):
    """Chọn công việc (Biểu A2) mà một vị trí việc làm đảm nhận, kèm tỷ lệ."""

    def __init__(self, calc: Calculator, current: str, vt_label: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chọn công việc đảm nhận – {vt_label}")
        self.resize(900, 560)
        cur = dict(parse_cv_list(current))
        lay = QVBoxLayout(self)
        info = QLabel("Đánh dấu các công việc mà vị trí này đảm nhận. Nếu một công việc do nhiều vị trí "
                      "cùng thực hiện, nhập tỷ lệ (%) phần việc của vị trí này. Tổng tỷ lệ của một công việc "
                      "trên tất cả các vị trí nên bằng 100%.")
        info.setWordWrap(True)
        info.setObjectName("Note")
        lay.addWidget(info)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Tìm công việc...")
        lay.addWidget(self.filter)
        t = QTableWidget(0, 6)
        t.setHorizontalHeaderLabels(["Chọn", "Mã CV", "Tên công việc", "Giờ/năm (B1+B2)",
                                     "Đã giao vị trí khác", "Tỷ lệ (%)"])
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table = t
        self.checks, self.spins, self.codes = [], [], []
        for code, r in calc.a2.items():
            row = t.rowCount()
            t.insertRow(row)
            chk = QCheckBox()
            chk.setChecked(code in cur)
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(8, 0, 0, 0)
            hl.addWidget(chk)
            t.setCellWidget(row, 0, w)
            t.setItem(row, 1, QTableWidgetItem(code))
            t.setItem(row, 2, QTableWidgetItem(r.get("ten", "")))
            hours = calc.b1_hours.get(code, 0) + calc.b2_delta.get(code, 0)
            t.setItem(row, 3, QTableWidgetItem(fmt(hours)))
            other = calc.cv_assign.get(code, 0) - cur.get(code, 0)
            it = QTableWidgetItem(f"{fmt(other * 100)}%")
            if other > 0.999:
                it.setForeground(QBrush(QColor(theme.WARN)))
            t.setItem(row, 4, it)
            sp = QDoubleSpinBox()
            sp.setRange(1, 100)
            sp.setDecimals(1)
            sp.setSuffix(" %")
            sp.setValue(cur.get(code, max(0.0, min(1.0, 1 - other)) or 1.0) * 100)
            t.setCellWidget(row, 5, sp)
            for col in range(1, 5):
                t.item(row, col).setFlags(Qt.ItemIsEnabled)
            self.checks.append(chk)
            self.spins.append(sp)
            self.codes.append(code)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        lay.addWidget(t)
        self.filter.textChanged.connect(self._filter)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Đồng ý")
        bb.button(QDialogButtonBox.Cancel).setText("Hủy")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _filter(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            s = (self.table.item(row, 1).text() + " " + self.table.item(row, 2).text()).lower()
            self.table.setRowHidden(row, bool(text) and text not in s)

    def value(self) -> str:
        items = [(code, sp.value() / 100) for code, chk, sp in zip(self.codes, self.checks, self.spins)
                 if chk.isChecked()]
        return format_cv_list(items)


class RowDialog(QDialog):
    """Nhập/sửa chi tiết một dòng (thân thiện hơn khi nội dung dài)."""

    def __init__(self, model: FormModel, row: int, parent=None):
        super().__init__(parent)
        self.m, self.row = model, row
        r = model.rows[row]
        self.setWindowTitle(f"Biểu {model.code} – {model.form.title} – dòng {row + 1}")
        self.resize(760, 640)
        outer = QVBoxLayout(self)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        body = QWidget()
        fl = QFormLayout(body)
        fl.setLabelAlignment(Qt.AlignRight)
        self.widgets = {}
        for c in model.cols:
            label = c.label + (" *" if c.required else "")
            v = model.calc.value(model.code, r, c.key)
            if c.kind == "calc":
                w = QLabel(fmt(v, 3) if c.key in NUMERIC_CALC else str(v or ""))
                w.setStyleSheet(f"color:{theme.MUTED}; background:{theme.CALC_BG}; padding:4px; border-radius:4px;")
                w.setWordWrap(True)
            elif c.kind == "choice":
                w = QComboBox()
                w.addItem("")
                w.addItems(list(c.options))
                w.setCurrentIndex(max(0, w.findText(str(v or ""))))
            elif c.kind == "ref":
                w = QComboBox()
                w.addItem("", "")
                for k, name in ref_items(model.calc, c.ref):
                    w.addItem(f"{k} — {name}", k)
                i = w.findData(v)
                w.setCurrentIndex(max(0, i))
            elif c.kind == "memo":
                w = QPlainTextEdit(str(v or ""))
                w.setFixedHeight(70)
            elif c.kind == "multiref":
                w = QWidget()
                h = QHBoxLayout(w)
                h.setContentsMargins(0, 0, 0, 0)
                ed = QLineEdit(str(v or ""))
                btn = QPushButton("Chọn...")
                btn.clicked.connect(lambda _=False, e=ed: self._pick(e))
                h.addWidget(ed)
                h.addWidget(btn)
                w.line = ed
            else:
                w = QLineEdit("" if v in (None, "") else (fmt(v, 4).replace(".", "")
                                                          if isinstance(v, float) else str(v)))
                if c.tip:
                    w.setPlaceholderText(c.tip)
            if c.tip:
                w.setToolTip(c.tip)
            self.widgets[c.key] = w
            fl.addRow(label, w)
        sc.setWidget(body)
        outer.addWidget(sc)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText("Lưu")
        bb.button(QDialogButtonBox.Cancel).setText("Hủy")
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)
        outer.addWidget(bb)

    def _pick(self, ed):
        r = self.m.rows[self.row]
        dlg = CvPicker(self.m.calc, ed.text(), r.get("ma_vt", ""), self)
        if dlg.exec():
            ed.setText(dlg.value())

    def _save(self):
        values = {}
        try:
            for c in self.m.cols:
                w = self.widgets[c.key]
                if c.kind == "calc":
                    continue
                if c.kind == "choice":
                    raw = w.currentText()
                elif c.kind == "ref":
                    raw = w.currentData() or ""
                elif c.kind == "memo":
                    raw = w.toPlainText()
                elif c.kind == "multiref":
                    raw = w.line.text()
                else:
                    raw = w.text()
                values[c.key] = self.m.convert(c, raw)
        except ValueError as e:
            QMessageBox.warning(self, "Dữ liệu không hợp lệ", str(e))
            return
        self.m.set_values(self.row, values)
        self.accept()


# ------------------------------------------------------------------ editor
class FormEditor(QWidget):
    changed = Signal()

    def __init__(self, project, code: str, parent=None):
        super().__init__(parent)
        self.project = project
        self.code = code
        self.form = ALL_FORMS[code]
        self.model = FormModel(project, code, self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        project.subscribe(self._on_project_change)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(6)
        if self.form.note:
            note = QLabel("ⓘ  " + self.form.note)
            note.setObjectName("Note")
            note.setWordWrap(True)
            lay.addWidget(note)

        bar = QHBoxLayout()
        self.btn_add = self._btn("＋ Thêm dòng", self.add_row, "Primary", "Thêm dòng mới (Ctrl+N)")
        bar.addWidget(self.btn_add)
        bar.addWidget(self._btn("✎ Chi tiết", self.edit_detail, tip="Sửa dòng đang chọn trong cửa sổ chi tiết (Enter)"))
        bar.addWidget(self._btn("⧉ Nhân bản", self.duplicate, tip="Sao chép dòng đang chọn"))
        bar.addWidget(self._btn("▲", lambda: self.move(-1), tip="Chuyển dòng lên"))
        bar.addWidget(self._btn("▼", lambda: self.move(1), tip="Chuyển dòng xuống"))
        bar.addWidget(self._btn("🗑 Xóa", self.delete_rows, "Danger", "Xóa các dòng đang chọn (Delete)"))
        if self.form.sync_from:
            bar.addWidget(self._btn("⟳ Đồng bộ từ C1", self.sync_from_c1,
                                    tip="Tạo sẵn dòng cho mọi vị trí việc làm ở Biểu C1 chưa có trong biểu này"))
        if code == "C3":
            bar.addWidget(self._btn("∑ Điền theo kết quả tính", self.fill_need,
                                    tip="Điền 'Số người cần bố trí' bằng kết quả tính cho các dòng còn trống"))
        if code == "D2":
            bar.addWidget(self._btn("⇢ Gợi ý lộ trình", self.auto_plan,
                                    tip="Gợi ý lộ trình điều chỉnh dần từ hiện có đến nhu cầu cho các dòng còn trống"))
        bar.addStretch(1)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Tìm trong biểu...")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(190)
        self.search.textChanged.connect(self.proxy.setFilterFixedString)
        bar.addWidget(self.search)
        if code != "CC":
            bar.addWidget(self._btn("⭳ Nhập Excel", self.import_excel, tip="Nhập biểu này từ tệp Excel"))
        lay.addLayout(bar)

        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setItemDelegate(FormDelegate(self.model, self.view))
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.view.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
                                  | QAbstractItemView.AnyKeyPressed)
        self.view.verticalHeader().setVisible(False)
        self.view.verticalHeader().setDefaultSectionSize(30)
        self.view.horizontalHeader().setDefaultAlignment(Qt.AlignCenter | Qt.TextWordWrap)
        self.view.horizontalHeader().setMinimumHeight(46)
        self.view.setWordWrap(False)
        self.view.setColumnWidth(0, 44)
        for i, c in enumerate(self.form.columns, 1):
            self.view.setColumnWidth(i, c.width)
        self.view.doubleClicked.connect(self._double_clicked)
        lay.addWidget(self.view, 1)

        self.footer = QLabel()
        self.footer.setObjectName("PageSub")
        self.footer.setWordWrap(True)
        lay.addWidget(self.footer)
        self._update_footer()

        QShortcut(QKeySequence("Ctrl+N"), self, self.add_row, context=Qt.WidgetWithChildrenShortcut)
        QShortcut(QKeySequence(Qt.Key_Delete), self.view, self.delete_rows, context=Qt.WidgetShortcut)
        QShortcut(QKeySequence(Qt.Key_Return), self.view, self.edit_detail, context=Qt.WidgetShortcut)

    def _btn(self, text, slot, name=None, tip=None):
        b = QPushButton(text)
        if name:
            b.setObjectName(name)
        if tip:
            b.setToolTip(tip)
        b.clicked.connect(slot)
        return b

    # ------------------------------------------------------------- helpers
    def _on_project_change(self, form):
        if self.model._silent:
            return
        self.refresh()

    def refresh(self):
        self.model.reload()
        self._update_footer()

    def _update_footer(self):
        n = len(self.model.rows)
        txt = f"Tổng số: {n} dòng."
        calc = self.model.calc
        if self.code == "B1":
            txt += f"  Tổng giờ lao động: {fmt(sum(calc.b1_hours.values()))} giờ/năm."
        elif self.code == "B2":
            txt += f"  Tổng giờ tăng/giảm: {fmt(sum(calc.b2_delta.values()))} giờ/năm."
        elif self.code == "C3":
            tot_q = sum(calc.c3_values(r)["nguoi_quy_doi"] for r in self.model.rows)
            tot = sum(calc.need(r.get("ma_vt", "")) for r in self.model.rows)
            txt += (f"  Quỹ giờ chuẩn: {fmt(calc.default_quy or DEFAULT_QUY_GIO)} giờ."
                    f"  Tổng quy đổi (PP2): {fmt(tot_q, 3)} người.  Tổng cần bố trí: {fmt(tot, 3)} người.")
        elif self.code == "D1":
            s = calc.summary()
            txt += f"  Nhu cầu: {fmt(s['need'], 3)} – Hiện có: {fmt(s['existing'])} – Chênh lệch: {fmt(s['diff'], 3)}."
        txt += "\nÔ nền đỏ: bắt buộc nhập · ô nền xanh: tự động tính · nhấp đúp hoặc gõ để sửa · Enter: mở chi tiết."
        self.footer.setText(txt)
        self.changed.emit()

    def selected_rows(self):
        rows = {self.proxy.mapToSource(i).row() for i in self.view.selectionModel().selectedIndexes()}
        cur = self.view.currentIndex()
        if not rows and cur.isValid():
            rows = {self.proxy.mapToSource(cur).row()}
        return sorted(rows)

    def select_row(self, row: int, column: int = 1):
        idx = self.proxy.mapFromSource(self.model.index(row, column))
        self.view.setCurrentIndex(idx)
        self.view.scrollTo(idx)
        self.view.setFocus()

    def select_row_id(self, row_id):
        for i, r in enumerate(self.model.rows):
            if r["_id"] == row_id:
                self.select_row(i)
                return

    def select_key(self, key):
        kc = self.form.key_col or "ma"
        for i, r in enumerate(self.model.rows):
            if str(r.get(kc, "")) == str(key):
                self.select_row(i)
                return

    # ------------------------------------------------------------- actions
    def add_row(self):
        data = {}
        sel = self.selected_rows()
        if self.code in KEY_PREFIX:
            data[self.form.key_col] = next_code(KEY_PREFIX[self.code],
                                                [r.get(self.form.key_col) for r in self.model.rows])
        if self.code == "A2" and sel:
            data["ma_nv"] = self.model.rows[sel[-1]].get("ma_nv", "")
        if self.code == "C1":
            data["tinh_trang"] = "Tiếp tục sử dụng"
            data["loai_hinh"] = "Viên chức"
        if self.code == "A1":
            data["tinh_trang"] = "Giữ nguyên"
        self.project.add_row(self.code, data)
        self.search.clear()
        self.select_row(len(self.model.rows) - 1, 2 if self.code in KEY_PREFIX else 1)

    def duplicate(self):
        sel = self.selected_rows()
        if not sel:
            return
        for i in sel:
            d = dict(self.model.rows[i])
            if self.code in KEY_PREFIX:
                d[self.form.key_col] = next_code(KEY_PREFIX[self.code],
                                                 [r.get(self.form.key_col) for r in self.model.rows])
            self.project.add_row(self.code, d, notify=False)
        self.project._notify(self.code)

    def move(self, delta):
        sel = self.selected_rows()
        if len(sel) != 1:
            return
        rid = self.model.rows[sel[0]]["_id"]
        self.project.move_row(self.code, rid, delta)
        self.select_row_id(rid)

    def delete_rows(self):
        sel = self.selected_rows()
        if not sel:
            return
        msg = f"Xóa {len(sel)} dòng đã chọn khỏi Biểu {self.code}?"
        if self.code in DEPENDENTS:
            msg += "\n\nLưu ý: các biểu khác đang tham chiếu mã này sẽ bị báo lỗi khi kiểm tra."
        if QMessageBox.question(self, "Xác nhận xóa", msg) != QMessageBox.Yes:
            return
        self.project.delete_rows(self.code, [self.model.rows[i]["_id"] for i in sel])

    def edit_detail(self):
        sel = self.selected_rows()
        if not sel:
            if not self.model.rows:
                self.add_row()
                sel = [len(self.model.rows) - 1]
            else:
                return
        RowDialog(self.model, sel[0], self).exec()

    def _double_clicked(self, index):
        src = self.proxy.mapToSource(index)
        c = self.model.col_at(src.column())
        if c and c.kind == "multiref":
            r = self.model.rows[src.row()]
            dlg = CvPicker(self.model.calc, r.get(c.key, ""), r.get("ma_vt", ""), self)
            if dlg.exec():
                self.model.set_values(src.row(), {c.key: dlg.value()})
        elif c and c.kind == "calc":
            RowDialog(self.model, src.row(), self).exec()

    def sync_from_c1(self):
        existing = {r.get("ma_vt") for r in self.model.rows}
        added = 0
        for vt, r in self.model.calc.c1.items():
            if vt in existing or r.get("tinh_trang") == "Đề nghị bãi bỏ":
                continue
            d = {"ma_vt": vt}
            if self.code == "C3":
                nhom = r.get("nhom", "")
                d["phuong_phap"] = ("PP1 - Cơ cấu, định mức" if nhom in ("Lãnh đạo, quản lý", "Hỗ trợ, phục vụ")
                                    else "PP2 - Khối lượng, thời gian")
            if self.code == "D1":
                d["kinh_phi"] = "Ngân sách nhà nước"
            self.project.add_row(self.code, d, notify=False)
            added += 1
        self.project._notify(self.code)
        QMessageBox.information(self, "Đồng bộ", f"Đã thêm {added} vị trí việc làm từ Biểu C1.")

    def fill_need(self):
        calc = self.model.calc
        n = 0
        for r in self.model.rows:
            if not has_num(r.get("nguoi_can")):
                v = round(calc.suggested_need(r), 3)
                self.project.update_row(r["_id"], {"nguoi_can": v}, notify=False)
                n += 1
        self.project._notify(self.code)
        QMessageBox.information(self, "Hoàn tất",
                                f"Đã điền {n} dòng theo kết quả tính (giữ nguyên số lẻ, không làm tròn cơ học).\n"
                                "Đơn vị xem xét, điều chỉnh và ghi giải trình nếu cần.")

    def auto_plan(self):
        from ..core.forms import YEARS
        calc = self.model.calc
        n = 0
        for r in self.model.rows:
            if any(has_num(r.get(f"y{y}")) for y in YEARS):
                continue
            vt = r.get("ma_vt", "")
            cur, need = calc.existing(vt), calc.need(vt)
            vals = {f"y{y}": round((cur + (need - cur) * (i + 1) / len(YEARS)) * 2) / 2
                    for i, y in enumerate(YEARS)}
            self.project.update_row(r["_id"], vals, notify=False)
            n += 1
        self.project._notify(self.code)
        QMessageBox.information(self, "Hoàn tất", f"Đã gợi ý lộ trình cho {n} vị trí. Vui lòng rà soát lại.")

    def import_excel(self):
        from ..core.exporter import import_excel
        path, _ = QFileDialog.getOpenFileName(self, f"Nhập Biểu {self.code} từ Excel", "", "Excel (*.xlsx)")
        if not path:
            return
        if QMessageBox.question(self, "Xác nhận",
                                f"Dữ liệu hiện có của Biểu {self.code} sẽ được thay bằng dữ liệu trong tệp. Tiếp tục?"
                                ) != QMessageBox.Yes:
            return
        try:
            res = import_excel(self.project, path, [self.code])
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không đọc được tệp: {e}")
            return
        if not res:
            QMessageBox.warning(self, "Không tìm thấy",
                                f"Tệp không có trang tính '{self.code}' đúng cấu trúc (dòng tiêu đề bắt đầu bằng 'STT').")
        else:
            QMessageBox.information(self, "Hoàn tất", f"Đã nhập {res[self.code]} dòng.")
