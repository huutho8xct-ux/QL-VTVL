"""Bảng nhập liệu dùng chung cho các biểu."""
from __future__ import annotations

import re

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QStyledItemDelegate, QTableView,
    QVBoxLayout, QWidget,
)

from ..core.calc import Calculator, fmt, isnum, num, s
from ..core.forms import ALL_FORMS, YEARS
from . import theme

KEY_PREFIX = {"A1": "NV", "A2": "CV", "C1": "VT", "D1": "NL", "DM": "SP"}
# Khi đổi mã ở biểu X thì cập nhật cột tham chiếu ở các biểu phụ thuộc
DEPENDENTS = {
    "A1": [("A2", "ma_nv")],
    "A2": [("B1", "ma_cv"), ("B2", "ma_cv")],
    "C1": [("A2", "ma_vt"), ("C2", "ma_vt"), ("C3", "ma_vt"), ("D1", "ma_vt"), ("DB", "ma_vt"), ("D2", "ma_vt")],
    "DM": [("B1", "ma_sp")],
}
OK_VALUES = {"ĐẠT", "Đạt", "ĐÃ THẨM ĐỊNH", "ĐÃ QUYẾT ĐỊNH", "ĐỐI CHIẾU XONG", "Đã kiểm chứng"}
NEUTRAL_VALUES = {"ĐANG XÂY DỰNG", "SẴN SÀNG THẨM ĐỊNH", "THAM KHẢO – KHÔNG TÍNH", "THAY ĐỔI SO VỚI NĂM CƠ SỞ – CÓ DỰ BÁO",
                  "Kiểm chứng một phần"}
STATUS_KEYS = {"canh_bao", "kiem_tra", "kt_quy_gio", "kiem_soat", "trang_thai"}
BOLD_KEYS = {"gio_tong", "nguoi_qd", "gio_rong", "nguoi_can", "nguoi_nam", "nguoi_can_nam", "rong"}
DECIMALS3 = {"nguoi_qd", "nguoi_can", "nguoi_pp1", "nguoi_pp3", "nguoi_c3", "nguoi_nam", "nguoi_can_nam", "pp2_qd",
             "c3_co_so", "co_the_bt", "de_nghi", "bien_dong"}


def next_code(prefix: str, existing) -> str:
    n, width = 0, 2 if prefix != "NL" else 3
    for e in existing:
        m = re.match(rf"^{prefix}(\d+)$", str(e or ""))
        if m:
            n = max(n, int(m.group(1)))
    return f"{prefix}{n + 1:0{width}d}"


def ref_items(calc: Calculator, ref: str):
    src = {"A1": calc.a1, "A2": calc.a2, "C1": calc.c1, "DM": calc.dm}.get(ref, {})
    return [(k, s(v.get("ten"))) for k, v in src.items() if k]


def status_color(v):
    v = s(v)
    if not v:
        return None
    if v in OK_VALUES:
        return theme.OK
    if v in NEUTRAL_VALUES:
        return theme.PRIMARY
    return theme.WARN if not v.startswith("TRÙNG") else theme.ERR


class FormModel(QAbstractTableModel):
    def __init__(self, project, code: str, parent=None):
        super().__init__(parent)
        self.project = project
        self.code = code
        self.form = ALL_FORMS[code]
        self.cols = list(self.form.columns)
        self.calc = Calculator(project)
        self.rows = self._load_rows()
        self._silent = False

    def _load_rows(self):
        return self.calc.virtual_rows(self.code) if self.form.virtual else self.project.rows(self.code)

    def reload(self):
        self.beginResetModel()
        self.calc.refresh()
        self.rows = self._load_rows()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.cols) + 1

    def col_at(self, column: int):
        return None if column == 0 else self.cols[column - 1]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None
        if role == Qt.DisplayRole:
            if section == 0:
                return "STT"
            c = self.cols[section - 1]
            return f"{c.label}" + (f"\n({c.letter})" if c.letter else "")
        if role == Qt.ToolTipRole and section > 0:
            c = self.cols[section - 1]
            t = c.label + (f" – cột {c.letter} trong bộ biểu" if c.letter else "")
            if c.tip:
                t += "\n" + c.tip
            if c.kind == "calc":
                t += "\n(Tự động – không nhập)"
            if c.required:
                t += "\n(Bắt buộc)"
            return t
        if role == Qt.ForegroundRole and section > 0 and self.cols[section - 1].kind == "calc":
            return QBrush(QColor(theme.MUTED))
        return None

    def flags(self, index):
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        c = self.col_at(index.column())
        if c and c.kind != "calc" and not self.form.virtual:
            f |= Qt.ItemIsEditable
        return f

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
        numeric = c.kind in ("int", "float") or (c.kind == "calc" and isinstance(v, (int, float)))
        if role == Qt.DisplayRole:
            if v is None or v == "":
                return ""
            if numeric:
                return fmt(num(v), 3 if c.key in DECIMALS3 else 2)
            return str(v)
        if role == Qt.EditRole:
            return "" if v is None else v
        if role == Qt.ToolTipRole:
            if c.kind == "ref" and v:
                name = dict(ref_items(self.calc, c.ref)).get(s(v))
                return f"{v}: {name}" if name is not None else f"{v}: (chưa có ở biểu {c.ref})"
            if v not in (None, "") and not numeric:
                return str(v)
            return c.tip or None
        if role == Qt.TextAlignmentRole:
            return (Qt.AlignRight | Qt.AlignVCenter) if numeric else (Qt.AlignLeft | Qt.AlignVCenter)
        if role == Qt.BackgroundRole:
            if c.kind == "calc":
                return QBrush(QColor(theme.CALC_BG))
            if c.required and (r.get(c.key) is None or s(r.get(c.key)) == ""):
                return QBrush(QColor("#FDECEA"))
            if c.kind == "ref" and s(v) and s(v) not in dict(ref_items(self.calc, c.ref)):
                return QBrush(QColor("#FFE0B2"))
        if role == Qt.ForegroundRole:
            if c.key in STATUS_KEYS and c.kind == "calc":
                col = status_color(v)
                if col:
                    return QBrush(QColor(col))
            if c.kind == "calc":
                return QBrush(QColor("#34495E"))
        if role == Qt.FontRole and (c.key in BOLD_KEYS or (c.key in STATUS_KEYS and c.kind == "calc")):
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
        if role != Qt.EditRole or not index.isValid() or self.form.virtual:
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
        old_key = s(r.get(self.form.key_col)) if self.form.key_col else None
        if all(r.get(k) == v for k, v in values.items()):
            return False
        self.project.update_row(r["_id"], values, notify=False)
        r.update(values)
        new_key = s(r.get(self.form.key_col)) if self.form.key_col else None
        if old_key and new_key and new_key != old_key and self.code in DEPENDENTS:
            self.project.rename_key(DEPENDENTS[self.code], old_key, new_key)
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
        if c is None or c.kind == "calc":
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
            cb.view().setMinimumWidth(440)
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
                i = editor.findData(s(v))
                editor.setCurrentIndex(i) if i >= 0 else editor.setEditText(s(v))
            else:
                editor.setCurrentIndex(max(0, editor.findText(s(v))))
            QTimer.singleShot(0, editor.showPopup)
        else:
            if isinstance(v, float):
                v = fmt(v, 4).replace(".", "")
            editor.setText("" if v is None else str(v))

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            c = self.m.col_at(self._src(index).column())
            if c.kind == "ref":
                data, text = editor.currentData(), editor.currentText()
                value = data if data and text.startswith(str(data)) else text.split(" — ")[0].strip()
            else:
                value = editor.currentText()
            model.setData(index, value, Qt.EditRole)
        else:
            model.setData(index, editor.text(), Qt.EditRole)


class RowDialog(QDialog):
    """Nhập/sửa chi tiết một dòng."""

    def __init__(self, model: FormModel, row: int, parent=None):
        super().__init__(parent)
        self.m, self.row = model, row
        r = model.rows[row]
        self.setWindowTitle(f"Biểu {model.code} – {model.form.title} – dòng {row + 1}")
        self.resize(780, 660)
        outer = QVBoxLayout(self)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        body = QWidget()
        fl = QFormLayout(body)
        fl.setLabelAlignment(Qt.AlignRight)
        self.widgets = {}
        readonly = model.form.virtual
        for c in model.cols:
            label = (f"[{c.letter}] " if c.letter else "") + c.label + (" *" if c.required else "")
            v = model.calc.value(model.code, r, c.key)
            if c.kind == "calc" or readonly:
                txt = fmt(v, 3) if isinstance(v, (int, float)) and not isinstance(v, bool) else s(v)
                w = QLabel(txt)
                col = status_color(v) if c.key in STATUS_KEYS else None
                w.setStyleSheet(f"color:{col or theme.MUTED}; background:{theme.CALC_BG}; padding:4px;"
                                "border-radius:4px;" + ("font-weight:600;" if col else ""))
                w.setWordWrap(True)
            elif c.kind == "choice":
                w = QComboBox()
                w.addItem("")
                w.addItems(list(c.options))
                w.setCurrentIndex(max(0, w.findText(s(v))))
            elif c.kind == "ref":
                w = QComboBox()
                w.addItem("", "")
                for k, name in ref_items(model.calc, c.ref):
                    w.addItem(f"{k} — {name}", k)
                w.setCurrentIndex(max(0, w.findData(s(v))))
            elif c.kind == "memo":
                w = QPlainTextEdit(s(v))
                w.setFixedHeight(64)
            else:
                w = QLineEdit("" if v in (None, "") else (fmt(v, 4).replace(".", "") if isinstance(v, float)
                                                          else str(v)))
                if c.tip:
                    w.setPlaceholderText(c.tip)
            if c.tip:
                w.setToolTip(c.tip)
            self.widgets[c.key] = w
            fl.addRow(label, w)
        sc.setWidget(body)
        outer.addWidget(sc)
        bb = QDialogButtonBox(QDialogButtonBox.Close if readonly else QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        if readonly:
            bb.button(QDialogButtonBox.Close).setText("Đóng")
            bb.rejected.connect(self.reject)
        else:
            bb.button(QDialogButtonBox.Save).setText("Lưu")
            bb.button(QDialogButtonBox.Cancel).setText("Hủy")
            bb.accepted.connect(self._save)
            bb.rejected.connect(self.reject)
        outer.addWidget(bb)

    def _save(self):
        values = {}
        try:
            for c in self.m.cols:
                if c.kind == "calc":
                    continue
                w = self.widgets[c.key]
                if c.kind == "choice":
                    raw = w.currentText()
                elif c.kind == "ref":
                    raw = w.currentData() or ""
                elif c.kind == "memo":
                    raw = w.toPlainText()
                else:
                    raw = w.text()
                values[c.key] = self.m.convert(c, raw)
        except ValueError as e:
            QMessageBox.warning(self, "Dữ liệu không hợp lệ", str(e))
            return
        self.m.set_values(self.row, values)
        self.accept()


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
        self._dirty = False
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
        ro = self.form.virtual
        if not ro:
            bar.addWidget(self._btn("＋ Thêm dòng", self.add_row, "Primary", "Thêm dòng mới (Ctrl+N)"))
        bar.addWidget(self._btn("✎ Chi tiết", self.edit_detail, tip="Xem/sửa dòng đang chọn trong cửa sổ chi tiết"))
        if not ro:
            bar.addWidget(self._btn("⧉ Nhân bản", self.duplicate, tip="Sao chép dòng đang chọn"))
            bar.addWidget(self._btn("▲", lambda: self.move(-1), tip="Chuyển dòng lên"))
            bar.addWidget(self._btn("▼", lambda: self.move(1), tip="Chuyển dòng xuống"))
            bar.addWidget(self._btn("🗑 Xóa", self.delete_rows, "Danger", "Xóa các dòng đang chọn (Delete)"))
        if code in ("C2", "C3"):
            bar.addWidget(self._btn("⟳ Đồng bộ từ C1", self.sync_from_c1,
                                    tip="Tạo dòng cho mọi VTVL ở Biểu C1 chưa có trong biểu này"))
        if code == "C3":
            bar.addWidget(self._btn("∑ Điền theo kết quả tính", self.fill_need,
                                    tip="Gợi ý 'Người cần bố trí' cho các dòng còn trống (PP2 + PP1 + PP3)"))
        if code == "DB":
            bar.addWidget(self._btn("⟳ Tạo dự báo 2027–2031", self.make_forecast,
                                    tip="Tạo dòng cho mọi VTVL × 5 năm, biến động 0 (không đổi)"))
        if code == "D2":
            bar.addWidget(self._btn("⟳ Tạo phương án 2027–2031", self.make_plan,
                                    tip="Tạo dòng mọi VTVL × 5 năm; số người có thể bố trí lấy từ D1"))
        if code == "D1":
            bar.addWidget(self._btn("⟳ Gợi ý nhân lực từ C1", self.make_people,
                                    tip="Tạo nhanh các dòng nguồn lực (NL...) cho từng VTVL"))
        bar.addStretch(1)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Tìm trong biểu...")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(190)
        self.search.textChanged.connect(self.proxy.setFilterFixedString)
        bar.addWidget(self.search)
        if self.form.sheet and not ro:
            bar.addWidget(self._btn("⭳ Nhập từ bộ biểu", self.import_excel,
                                    tip="Nhập biểu này từ Bộ biểu Excel chính thức đã điền"))
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
        self.view.horizontalHeader().setMinimumHeight(64)
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

        if not ro:
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

    # ------------------------------------------------------------- refresh
    def _on_project_change(self, form):
        if self.model._silent:
            return
        if self.isVisible():
            self.refresh()
        else:
            self._dirty = True

    def showEvent(self, e):
        if self._dirty:
            self.refresh()
        super().showEvent(e)

    def refresh(self):
        self._dirty = False
        self.model.reload()
        self._update_footer()

    def _update_footer(self):
        calc, rows = self.model.calc, self.model.rows
        txt = f"Tổng số: {len(rows)} dòng"
        if self.form.sheet:
            txt += f" (sức chứa bộ biểu: {self.form.capacity})"
        txt += "."
        if self.code == "B1":
            dat = [r for r in rows if calc.value("B1", r, "canh_bao") == "ĐẠT"]
            txt += (f"  Dòng ĐẠT: {len(dat)}/{len(rows)}.  Tổng giờ (dòng ĐẠT): "
                    f"{fmt(sum(num(calc.value('B1', r, 'gio_tong')) for r in dat))} giờ.")
        elif self.code in ("B2", "B2TH"):
            txt += f"  Giờ tác động ròng (hợp lệ): {fmt(sum(t['rong'] for t in calc.b2th))} giờ."
        elif self.code == "C3":
            sm = calc.summary()
            txt += (f"  Quỹ giờ PP2: {fmt(calc.quy)} giờ.  Tổng người quy đổi PP2: {fmt(sm['qd'], 3)}.  "
                    f"Tổng người cần bố trí: {fmt(sm['need'], 3)}.  VTVL đủ căn cứ: {sm['ok_vt']}/{sm['vt']}.")
        elif self.code == "D1":
            sm = calc.summary()
            txt += f"  Số người thực tế: {sm['existing']}; người quy đổi: {fmt(sm['existing_qd'], 3)}."
        elif self.code == "D2":
            sm = calc.summary()
            txt += "  Số người cần bố trí theo năm: " + "; ".join(f"{y}: {fmt(sm['plan'][y], 3)}" for y in YEARS) + "."
        if not self.form.virtual:
            txt += "\nÔ nền đỏ: bắt buộc nhập · ô nền xanh: tự động (ô xám trong bộ biểu) · nhấp đúp hoặc gõ để sửa · Enter: chi tiết."
        else:
            txt += "\nBiểu tổng hợp tự động – không nhập."
        self.footer.setText(txt)
        self.changed.emit()

    # ------------------------------------------------------------ selection
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
        kc = self.form.key_col or self.form.columns[0].key
        key = str(key).split(" ")[0]
        for i, r in enumerate(self.model.rows):
            if s(r.get(kc)) == key:
                self.select_row(i)
                return

    # -------------------------------------------------------------- actions
    def _defaults(self):
        m = self.project.meta()
        unit, ky = m.get("ten_don_vi", ""), m.get("ky_thong_ke", "")
        return {
            "A1": dict(co_quan=unit, ky=ky, trang_thai="Tiếp tục thực hiện"),
            "B1": dict(ky=ky),
            "B2": dict(ky=ky, co_so="Trước thay đổi, có điều chỉnh", trang_thai="Chưa kiểm chứng",
                       doi_chieu="Chờ đối chiếu"),
            "C1": dict(loai_nl="Viên chức", trang_thai="Tiếp tục sử dụng", che_do="Phổ biến (40 giờ/tuần)",
                       can_cu_quy_gio="Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc"),
            "C3": dict(trang_thai="Tính thử"),
            "D1": dict(loai_nl="Viên chức", gio_vtvl=self.model.calc.quy, gio_khac=0, noi_bc=unit,
                       trang_thai="Chưa kiểm chứng"),
            "DB": dict(bien_dong=0, trang_thai="Chưa kiểm chứng"),
            "D2": dict(trang_thai="Đang xây dựng"),
        }.get(self.code, {})

    def add_row(self):
        data = dict(self._defaults())
        sel = self.selected_rows()
        if self.code in KEY_PREFIX:
            data[self.form.key_col] = next_code(KEY_PREFIX[self.code],
                                                [r.get(self.form.key_col) for r in self.model.rows])
        if self.code == "A2" and sel:
            data["ma_nv"] = self.model.rows[sel[-1]].get("ma_nv", "")
            data["ma_vt"] = self.model.rows[sel[-1]].get("ma_vt", "")
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
                                                 [r.get(self.form.key_col) for r in self.project.rows(self.code)])
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
            if not self.model.rows and not self.form.virtual:
                self.add_row()
                sel = [len(self.model.rows) - 1]
            else:
                return
        RowDialog(self.model, sel[0], self).exec()

    def _double_clicked(self, index):
        src = self.proxy.mapToSource(index)
        c = self.model.col_at(src.column())
        if self.form.virtual or (c and c.kind == "calc"):
            RowDialog(self.model, src.row(), self).exec()

    def _vt_list(self):
        return [(m, r) for m, r in self.model.calc.c1.items() if m and s(r.get("trang_thai")) != "Đề nghị bãi bỏ"]

    def sync_from_c1(self):
        existing = {s(r.get("ma_vt")) for r in self.model.rows}
        added = 0
        for vt, r in self._vt_list():
            if vt in existing:
                continue
            d = {"ma_vt": vt}
            if self.code == "C3":
                d.update(trang_thai="Tính thử")
            self.project.add_row(self.code, d, notify=False)
            added += 1
        self.project._notify(self.code)
        QMessageBox.information(self, "Đồng bộ", f"Đã thêm {added} vị trí việc làm từ Biểu C1.")

    def fill_need(self):
        calc = self.model.calc
        n = 0
        for r in self.model.rows:
            if not isnum(r.get("nguoi_can")) and s(r.get("pp")):
                self.project.update_row(r["_id"], {"nguoi_can": round(calc.suggested_need(r), 3)}, notify=False)
                n += 1
        self.project._notify(self.code)
        QMessageBox.information(self, "Hoàn tất",
                                f"Đã gợi ý {n} dòng (giữ số lẻ, không làm tròn cơ học). Đơn vị phải xem xét hiện diện, "
                                "kiêm nhiệm, dùng chung, loại trùng phần việc giữa các phương pháp rồi kết luận.")

    def make_forecast(self):
        have = {(s(r.get("ma_vt")), s(r.get("nam"))) for r in self.model.rows}
        n = 0
        for vt, _ in self._vt_list():
            for y in YEARS:
                if (vt, str(y)) in have:
                    continue
                self.project.add_row("DB", dict(ma_vt=vt, nam=str(y), bien_dong=0,
                                                noi_dung="Không đổi so với năm cơ sở", trang_thai="Chưa kiểm chứng"),
                                     notify=False)
                n += 1
        self.project._notify("DB")
        QMessageBox.information(self, "Hoàn tất", f"Đã tạo {n} dòng dự báo. Bổ sung căn cứ và xác nhận từng dòng.")

    def make_plan(self):
        calc = self.model.calc
        have = {(s(r.get("ma_vt")), s(r.get("nam"))) for r in self.model.rows}
        n = 0
        for vt, _ in self._vt_list():
            avail = calc.existing(vt)[0]
            for y in YEARS:
                if (vt, str(y)) in have:
                    continue
                need = calc.forecast(vt, str(y))
                d = dict(ma_vt=vt, nam=str(y), co_the_bt=avail, trang_thai="Đang xây dựng")
                if need != "":
                    d["de_nghi"] = round(need - avail, 3)
                self.project.add_row("D2", d, notify=False)
                n += 1
        self.project._notify("D2")
        QMessageBox.information(self, "Hoàn tất", f"Đã tạo {n} dòng phương án. Bổ sung điều chuyển, giải trình.")

    def make_people(self):
        from PySide6.QtWidgets import QInputDialog
        vts = [m for m, _ in self._vt_list()]
        if not vts:
            QMessageBox.information(self, "Chưa có VTVL", "Hãy lập Biểu C1 trước.")
            return
        vt, ok = QInputDialog.getItem(self, "Thêm nguồn lực", "Vị trí việc làm:", vts, 0, False)
        if not ok:
            return
        cnt, ok = QInputDialog.getInt(self, "Thêm nguồn lực", f"Số người hiện có tại {vt}:", 1, 1, 200)
        if not ok:
            return
        loai = s(self.model.calc.c1.get(vt, {}).get("loai_nl")) or "Viên chức"
        codes = [r.get("ma_nl") for r in self.project.rows("D1")]
        base = dict(self._defaults())
        for _ in range(cnt):
            code = next_code("NL", codes)
            codes.append(code)
            self.project.add_row("D1", dict(base, ma_nl=code, ma_vt=vt, loai_nl=loai), notify=False)
        self.project._notify("D1")

    def import_excel(self):
        win = self.window()
        if hasattr(win, "open_import"):
            win.open_import(self.code)
