"""Các trang theo cấu trúc chức năng: Kê khai – Đơn vị – Ứng dụng."""
from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import QSettings, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QTextBrowser,
    QToolButton, QVBoxLayout, QWidget,
)

from ..core.calc import fmt, s
from ..core.checks import ERROR, INFO, WARNING, run_checks
from ..core.db import app_data_dir
from ..core.forms import FORMS
from ..core.guide import STEPS
from ..core.package import export_subunits, issue_key, make_package, send_readiness, summarize_file
from . import theme
from .form_editor import FormEditor
from .pages import CheckPage, InfoPage, LegalPage
from .widgets import KpiCard, PageHeader, badge_color

FORM_TABS = ("A1", "A2", "B1", "B2", "B2TH", "C1", "C2", "C3", "D1", "DB", "D2", "DM")
STEP_OF = {f: st for st in STEPS for f in st.forms}


class BasePage(QWidget):
    def __init__(self, crumb, title, sub=""):
        super().__init__()
        self.setObjectName("Page")
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(28, 20, 28, 16)
        self.lay.setSpacing(12)
        self.header = PageHeader(crumb, title, sub)
        self.lay.addWidget(self.header)

    def on_show(self):
        pass


def table(headers, stretch=(), min_h=260):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setAlternatingRowColors(True)
    t.setWordWrap(True)
    for c in stretch:
        t.horizontalHeader().setSectionResizeMode(c, QHeaderView.Stretch)
    t.setMinimumHeight(min_h)
    return t


def item(text, color=None, bold=False, editable=False):
    it = QTableWidgetItem("" if text is None else str(text))
    if color:
        it.setForeground(QBrush(QColor(color)))
    if bold:
        f = it.font()
        f.setBold(True)
        it.setFont(f)
    if not editable:
        it.setFlags(it.flags() & ~Qt.ItemIsEditable)
    return it


def set_link(tbl, row, col, text, slot):
    """Ô liên kết bấm được (dạng chữ) – tránh dùng widget trong ô với bảng dài."""
    it = item(f"{text}  ›", theme.PRIMARY, bold=True)
    tbl.setItem(row, col, it)
    if not hasattr(tbl, "_acts"):
        tbl._acts = {}
        tbl.cellClicked.connect(lambda r, c, t=tbl: t._acts.get((r, c), lambda: None)())
    tbl._acts[(row, col)] = slot


def link_button(text, slot):
    b = QPushButton(text)
    b.setObjectName("Link")
    b.setCursor(Qt.PointingHandCursor)
    b.clicked.connect(slot)
    return b


LEVEL_COLORS = lambda lvl: {ERROR: theme.ERR, WARNING: theme.WARN, INFO: theme.INFO_C}.get(lvl, theme.MUTED)  # noqa


# ================================================================ NHẬP 09 BIỂU
class FormsPage(BasePage):
    def __init__(self, project):
        ky = project.meta().get("ky_thong_ke", "")
        super().__init__(f"Trang làm việc / Hồ sơ Kỳ {ky} / Nhập 09 biểu", "Nhập 09 biểu",
                         "Nhập trực tiếp từng biểu theo đúng cột của Bộ biểu 19-10-2026. Ô xanh là cột công thức tự "
                         "tính; nhãn trên mỗi tab cho biết biểu đã <b>Đạt</b> hay còn lỗi.")
        self.project = project
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.editors = {}
        self.guides = {}
        for code in FORM_TABS:
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(0, 8, 0, 0)
            st = STEP_OF.get(code)
            if st:
                tb = QToolButton()
                tb.setText(f"▸  Bước {st.no}. {st.title} – xem hướng dẫn nghiệp vụ")
                tb.setCheckable(True)
                tb.setStyleSheet(f"QToolButton {{ border:none; color:{theme.PRIMARY}; font-weight:600; }}")
                guide = QTextBrowser()
                guide.setObjectName("Guide")
                guide.setHtml(st.guide)
                guide.setMaximumHeight(190)
                guide.hide()
                tb.toggled.connect(lambda on, g=guide, b=tb, t=st: (g.setVisible(on), b.setText(
                    f"{'▾' if on else '▸'}  Bước {t.no}. {t.title} – {'ẩn' if on else 'xem'} hướng dẫn nghiệp vụ")))
                v.addWidget(tb)
                v.addWidget(guide)
            ed = FormEditor(project, code)
            ed.changed.connect(self._schedule)
            self.editors[code] = ed
            v.addWidget(ed, 1)
            self.tabs.addTab(w, FORMS[code].sheet)
        self.lay.addWidget(self.tabs, 1)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.update_badges)

    def _schedule(self):
        self._timer.start(400)

    def update_badges(self):
        issues = run_checks(self.project)
        for i, code in enumerate(FORM_TABS):
            n = sum(1 for x in issues if x.form == code and x.level in (ERROR, WARNING))
            cnt = self.project.count(code) if not FORMS[code].virtual else len(self.editors[code].model.rows)
            badge = "Trống" if cnt == 0 and code not in ("B2", "B2TH", "DM") else (f"{n} lỗi" if n else "Đạt")
            if cnt == 0 and code in ("B2", "B2TH", "DM"):
                badge = "Không bắt buộc"
            self.tabs.setTabText(i, f"{FORMS[code].sheet}   {badge}")
            self.tabs.tabBar().setTabTextColor(i, QColor(badge_color(badge)))

    def open(self, code, row_id=None, key=None):
        if code not in self.editors:
            return
        self.tabs.setCurrentIndex(FORM_TABS.index(code))
        ed = self.editors[code]
        ed.refresh()
        if row_id:
            ed.select_row_id(row_id)
        elif key:
            ed.select_key(key)

    def on_show(self):
        self.editors[FORM_TABS[self.tabs.currentIndex()]].refresh()
        self.update_badges()


# ================================================================ LỖI VÀ GIẢI TRÌNH
class IssuesPage(BasePage):
    open_form = Signal(str, object, str)

    def __init__(self, project):
        super().__init__("Trang làm việc / Lỗi và giải trình", "Lỗi và giải trình",
                         "Toàn bộ lỗi, cảnh báo của hồ sơ theo cột cảnh báo của Bộ biểu và Phụ lục VI. Ghi giải trình "
                         "trực tiếp vào cột <b>Giải trình</b>; giải trình được đưa vào báo cáo và gói hồ sơ gửi đi.")
        self.project = project
        grid = QGridLayout()
        grid.setSpacing(14)
        self.k_err = KpiCard("Lỗi phải sửa", theme.ERR)
        self.k_warn = KpiCard("Cảnh báo chưa giải trình", theme.WARN)
        self.k_done = KpiCard("Đã giải trình", theme.OK)
        for i, k in enumerate((self.k_err, self.k_warn, self.k_done)):
            grid.addWidget(k, 0, i)
        self.lay.addLayout(grid)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Hiển thị:"))
        self.flt = QComboBox()
        self.flt.addItems(["Lỗi và cảnh báo", "Chỉ lỗi", "Chưa giải trình", "Tất cả (kể cả lưu ý)"])
        self.flt.currentIndexChanged.connect(self.on_show)
        bar.addWidget(self.flt)
        bar.addStretch(1)
        refresh = QPushButton("⟳  Kiểm tra lại")
        refresh.clicked.connect(self.on_show)
        bar.addWidget(refresh)
        self.lay.addLayout(bar)
        self.tbl = table(["Mức", "Biểu", "Mã", "Nội dung", "Giải trình (nhấp đúp để ghi)", "Người, thời điểm", ""],
                         stretch=(3, 4))
        for c, w in ((0, 100), (1, 60), (2, 110), (5, 150), (6, 120)):
            self.tbl.setColumnWidth(c, w)
        self.tbl.verticalHeader().setDefaultSectionSize(40)
        self.tbl.itemChanged.connect(self._edited)
        self.tbl.cellClicked.connect(self._clicked)
        self.lay.addWidget(self.tbl, 1)
        self.items = []

    def on_show(self):
        all_issues = run_checks(self.project)
        gt = self.project.explanations()
        rows = []
        for i in all_issues:
            e = gt.get(issue_key(i), {})
            rows.append((i, s(e.get("giai_trinh")), f"{s(e.get('nguoi'))} {s(e.get('ngay'))}".strip()))
        errs = [r for r in rows if r[0].level == ERROR]
        warns = [r for r in rows if r[0].level == WARNING]
        self.k_err.value.setText(str(len(errs)))
        self.k_warn.value.setText(str(sum(1 for r in warns if not r[1])))
        self.k_done.value.setText(str(sum(1 for r in rows if r[1])))
        f = self.flt.currentIndex()
        if f == 0:
            rows = errs + warns
        elif f == 1:
            rows = errs
        elif f == 2:
            rows = [r for r in errs + warns if not r[1]]
        self.items = rows
        self.tbl.blockSignals(True)
        self.tbl.setRowCount(0)
        if hasattr(self.tbl, "_acts"):
            self.tbl._acts.clear()
        self.tbl.setRowCount(len(rows))
        for n, (i, g, who) in enumerate(rows):
            icon = {"Lỗi": "⛔", "Cảnh báo": "⚠", "Lưu ý": "ⓘ"}.get(i.level, "")
            self.tbl.setItem(n, 0, item(f"{icon} {i.level}", LEVEL_COLORS(i.level)))
            self.tbl.setItem(n, 1, item(i.form))
            self.tbl.setItem(n, 2, item(i.ref))
            self.tbl.setItem(n, 3, item(i.message))
            self.tbl.setItem(n, 4, item(g, theme.OK if g else None, editable=True))
            self.tbl.setItem(n, 5, item(who, theme.MUTED))
            if i.form in FORMS or i.form == "TT":
                link = item("Mở trong biểu  ›", theme.PRIMARY, bold=True)
                link.setData(Qt.UserRole, n)
                self.tbl.setItem(n, 6, link)
        if not rows:
            self.tbl.setRowCount(1)
            self.tbl.setItem(0, 3, item("✔ Hồ sơ không còn lỗi hoặc cảnh báo theo bộ lọc đang chọn.", theme.OK, True))
        self.tbl.blockSignals(False)

    def _clicked(self, r, c):
        if c == 6 and r < len(self.items):
            x = self.items[r][0]
            self.open_form.emit(x.form, x.row_id, x.ref)

    def _edited(self, it):
        if it.column() != 4 or it.row() >= len(self.items):
            return
        i = self.items[it.row()][0]
        self.project.set_explanation(issue_key(i), it.text().strip())
        QTimer.singleShot(0, self.on_show)


# ================================================================ KIỂM TRA VÀ GỬI
class SendPage(CheckPage):
    sent = Signal()

    def __init__(self, project, step):
        super().__init__(project, step)
        old = self.lay.itemAt(0).widget()
        old.hide()
        self.lay.insertWidget(0, PageHeader("Trang làm việc / Kiểm tra và gửi", "Kiểm tra và gửi",
                                            "Kiểm tra toàn hồ sơ theo Phụ lục VI, xuất Bộ biểu Excel chính thức, báo "
                                            "cáo Word và đóng gói hồ sơ gửi cơ quan quản lý."))
        card = QFrame()
        card.setObjectName("Card")
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 12, 16, 12)
        self.ready_lbl = QLabel()
        self.ready_lbl.setTextFormat(Qt.RichText)
        self.ready_lbl.setWordWrap(True)
        h.addWidget(self.ready_lbl, 1)
        self.btn_send = QPushButton("📦  Đóng gói và gửi hồ sơ")
        self.btn_send.setObjectName("Primary")
        self.btn_send.setToolTip("Tạo gói .zip: Bộ biểu Excel chính thức, báo cáo Word, danh sách giải trình, tệp hồ sơ")
        self.btn_send.clicked.connect(self.send)
        h.addWidget(self.btn_send)
        self.lay.insertWidget(2, card)

    def on_show(self):
        super().on_show()
        r = send_readiness(self.project)
        meta = self.project.meta()
        status = meta.get("trang_thai_ho_so") or "Đang kê khai"
        ver = meta.get("phien_ban") or "0"
        st = f"Trạng thái hồ sơ: <b>{status}</b>" + (f" (phiên bản {ver}, {meta.get('ngay_gui', '')})" if ver != "0" else "")
        if r["ready"]:
            msg = f"<span style='color:{theme.OK}'><b>✔ Đủ điều kiện gửi.</b></span>"
        else:
            parts = []
            if r["errors"]:
                parts.append(f"{r['errors']} lỗi phải sửa")
            if r["unexplained"]:
                parts.append(f"{r['unexplained']} cảnh báo chưa giải trình")
            msg = f"<span style='color:{theme.WARN}'><b>Chưa đủ điều kiện gửi:</b></span> " + ", ".join(parts) + \
                  " (xem mục Lỗi và giải trình)."
        self.ready_lbl.setText(f"{st}<br>{msg}")

    def send(self):
        r = send_readiness(self.project)
        if not r["ready"]:
            if QMessageBox.question(
                    self, "Chưa đủ điều kiện",
                    f"Hồ sơ còn {r['errors']} lỗi và {r['unexplained']} cảnh báo chưa giải trình.\n"
                    "Theo Hướng dẫn, phần chưa đủ căn cứ phải được nêu rõ khi gửi. Vẫn đóng gói (bản kèm danh sách "
                    "nội dung chưa đủ căn cứ)?") != QMessageBox.Yes:
                return
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu gói hồ sơ",
                                                  os.path.expanduser("~/Documents"))
        if not folder:
            return
        try:
            path = make_package(self.project, folder)
        except PermissionError:
            QMessageBox.critical(self, "Lỗi", "Không ghi được tệp – kiểm tra quyền thư mục hoặc đóng tệp đang mở.")
            return
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không đóng gói được: {e}")
            return
        self.on_show()
        self.sent.emit()
        QMessageBox.information(self, "Đã đóng gói hồ sơ",
                                f"Đã tạo gói hồ sơ:\n{path}\n\nGửi tệp .zip này cho cơ quan quản lý theo kênh quy định "
                                "(thư điện tử công vụ, phần mềm quản lý văn bản…). Phiên bản đã được lưu trong Lịch sử hồ sơ.")


# ================================================================ HỒ SƠ
class ProfilesPage(BasePage):
    request_new = Signal()
    request_open = Signal(str)
    request_sample = Signal()
    request_save_as = Signal()

    def __init__(self, project):
        super().__init__("Trang làm việc / Hồ sơ", "Hồ sơ",
                         "Mỗi hồ sơ là một tệp .vtvl lưu toàn bộ dữ liệu của một đợt rà soát. Dữ liệu tự lưu khi nhập.")
        self.project = project
        card = QFrame()
        card.setObjectName("Card")
        g = QGridLayout(card)
        g.setContentsMargins(18, 16, 18, 16)
        self.info = QLabel()
        self.info.setTextFormat(Qt.RichText)
        self.info.setWordWrap(True)
        g.addWidget(self.info, 0, 0, 1, 5)
        for col, (text, sig, prim) in enumerate((("＋ Tạo hồ sơ mới", self.request_new, True),
                                                 ("📂 Mở hồ sơ…", None, False),
                                                 ("💾 Lưu bản sao…", self.request_save_as, False),
                                                 ("Mở hồ sơ dữ liệu minh họa", self.request_sample, False),
                                                 ("Mở thư mục chứa", None, False))):
            b = QPushButton(text)
            if prim:
                b.setObjectName("Primary")
            if sig is not None:
                b.clicked.connect(sig.emit)
            elif col == 1:
                b.clicked.connect(self._open)
            else:
                b.clicked.connect(lambda: _open_path(os.path.dirname(self.project.path)))
            g.addWidget(b, 1, col)
        self.lay.addWidget(card)
        t = QLabel("Hồ sơ gần đây")
        t.setStyleSheet("font-size: 13pt; font-weight: 700;")
        self.lay.addWidget(t)
        self.tbl = table(["Tệp hồ sơ", "Thư mục", "Sửa lần cuối", ""], stretch=(1,))
        self.tbl.setColumnWidth(0, 300)
        self.tbl.setColumnWidth(2, 150)
        self.tbl.setColumnWidth(3, 110)
        self.lay.addWidget(self.tbl, 1)

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Mở hồ sơ", "", "Hồ sơ vị trí việc làm (*.vtvl)")
        if path:
            self.request_open.emit(path)

    def on_show(self):
        m = self.project.meta()
        self.info.setText(
            f"<span style='font-size:13pt'><b>Hồ sơ đang mở: {m.get('ten_don_vi', '')}</b></span><br>"
            f"Tệp: {self.project.path}<br>Kỳ thống kê: {m.get('ky_thong_ke', '')} · Ngày chốt nhân lực: "
            f"{m.get('ngay_chot', '')}<br>Trạng thái: <b>{m.get('trang_thai_ho_so') or 'Đang kê khai'}</b> · Phiên bản "
            f"đã gửi: {m.get('phien_ban') or '0'} · Lần kết chuyển gần nhất: {m.get('last_import') or '—'}"
            + (" · <span style='color:%s'>Dữ liệu minh họa</span>" % theme.WARN if m.get("du_lieu_mau") == "1" else ""))
        recent = [p for p in (QSettings("ThuVienCanTho", "QL-VTVL").value("recent", []) or []) if os.path.exists(p)]
        self.tbl.setRowCount(0)
        if hasattr(self.tbl, "_acts"):
            self.tbl._acts.clear()
        self.tbl.setRowCount(len(recent))
        for n, p in enumerate(recent):
            cur = os.path.abspath(p) == os.path.abspath(self.project.path)
            self.tbl.setItem(n, 0, item(os.path.basename(p) + ("  (đang mở)" if cur else ""), bold=cur))
            self.tbl.setItem(n, 1, item(os.path.dirname(p), theme.MUTED))
            self.tbl.setItem(n, 2, item(datetime.fromtimestamp(os.path.getmtime(p)).strftime("%d/%m/%Y %H:%M")))
            if not cur:
                set_link(self.tbl, n, 3, "Mở", lambda x=p: self.request_open.emit(x))


def _open_path(path):
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))


# ================================================================ HỒ SƠ CỦA ĐƠN VỊ
class UnitPage(BasePage):
    def __init__(self, project):
        super().__init__("Trang làm việc / Hồ sơ của đơn vị", "Hồ sơ của đơn vị",
                         "Thông tin đơn vị dùng cho phần đầu biểu, chữ ký, báo cáo; danh mục căn cứ pháp lý.")
        self.tabs = QTabWidget()
        self.info = InfoPage(project)
        self.legal = LegalPage(project)
        for p in (self.info, self.legal):
            p.lay.setContentsMargins(0, 8, 0, 0)
            p.lay.itemAt(0).widget().hide()   # ẩn tiêu đề trùng
        self.tabs.addTab(self.info, "Thông tin đơn vị")
        self.tabs.addTab(self.legal, "Căn cứ pháp lý")
        self.tabs.currentChanged.connect(lambda _: self.on_show())
        self.lay.addWidget(self.tabs, 1)

    def on_show(self):
        self.tabs.currentWidget().on_show()


# ================================================================ LỊCH SỬ HỒ SƠ
class HistoryPage(BasePage):
    restored = Signal()

    def __init__(self, project):
        super().__init__("Trang làm việc / Lịch sử hồ sơ", "Lịch sử hồ sơ",
                         "Nhật ký kết chuyển, gửi hồ sơ, khôi phục; mỗi mốc quan trọng có bản lưu để khôi phục khi cần.")
        self.project = project
        b = QPushButton("💾  Lưu phiên bản hiện tại")
        b.clicked.connect(self.save_version)
        self.header.add_button(b)
        self.tbl = table(["Thời gian", "Sự kiện", "Chi tiết", "Người thực hiện", "Phiên bản gửi", ""], stretch=(2,))
        for c, w in ((0, 150), (1, 260), (3, 150), (4, 100), (5, 120)):
            self.tbl.setColumnWidth(c, w)
        self.lay.addWidget(self.tbl, 1)

    def on_show(self):
        h = self.project.history()
        self.tbl.setRowCount(0)
        if hasattr(self.tbl, "_acts"):
            self.tbl._acts.clear()
        self.tbl.setRowCount(len(h))
        for n, r in enumerate(h):
            self.tbl.setItem(n, 0, item(r.get("time")))
            self.tbl.setItem(n, 1, item(r.get("event"), bold=True))
            self.tbl.setItem(n, 2, item(r.get("detail"), theme.MUTED))
            self.tbl.setItem(n, 3, item(r.get("user")))
            self.tbl.setItem(n, 4, item(r.get("version")))
            bk = r.get("backup")
            if bk and os.path.exists(bk):
                set_link(self.tbl, n, 5, "Khôi phục", lambda x=bk, e=r.get("event"): self.restore(x, e))
        self.tbl.resizeRowsToContents()

    def save_version(self):
        path = self.project.snapshot("ThuCong")
        self.project.log("Lưu phiên bản thủ công", os.path.basename(path), backup=path)
        self.on_show()

    def restore(self, path, event):
        if QMessageBox.question(self, "Khôi phục phiên bản",
                                f"Khôi phục hồ sơ về bản lưu của mốc “{event}”?\nTrạng thái hiện tại được lưu lại trước "
                                "khi khôi phục.") != QMessageBox.Yes:
            return
        cur = self.project.snapshot("TruocKhoiPhuc")
        self.project.restore_from(path)
        self.project.log("Khôi phục phiên bản", f"Về mốc: {event}", backup=cur)
        self.restored.emit()


# ================================================================ HỒ SƠ CẤP DƯỚI
class SubunitsPage(BasePage):
    def __init__(self, project):
        super().__init__("Đơn vị / Hồ sơ cấp dưới", "Hồ sơ cấp dưới",
                         "Tổng hợp hồ sơ của các đơn vị trực thuộc (tệp .vtvl hoặc Bộ biểu Excel đã điền). Số người "
                         "chỉ tính một lần ở đầu mối quản lý; số liệu cấp dưới dùng để đối chiếu, không cộng trùng.")
        self.project = project
        bar = QHBoxLayout()
        for text, slot in (("＋ Thêm tệp…", self.add_files), ("＋ Thêm cả thư mục…", self.add_folder),
                           ("⟳ Làm mới", self.on_show), ("Bỏ khỏi danh sách", self.remove),
                           ("⭳ Xuất bảng tổng hợp", self.export)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch(1)
        self.lay.addLayout(bar)
        self.tbl = table(["Đơn vị", "Tệp", "Nhiệm vụ", "VTVL", "Giờ ròng", "Người quy đổi", "Người cần bố trí",
                          "Hiện có", "VTVL đủ căn cứ", "Lỗi", "Cảnh báo", "Tình trạng", "Cập nhật"], stretch=(0,))
        self.lay.addWidget(self.tbl, 1)
        self.rows = []

    def _paths(self):
        return [r.get("path") for r in self.project.rows("SUB")]

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Chọn hồ sơ cấp dưới", "",
                                                "Hồ sơ (*.vtvl *.xlsx);;Tất cả tệp (*.*)")
        self._add(paths)

    def add_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa hồ sơ cấp dưới")
        if d:
            self._add([os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith((".vtvl", ".xlsx"))])

    def _add(self, paths):
        have = set(self._paths())
        for p in paths:
            if p and p not in have and os.path.abspath(p) != os.path.abspath(self.project.path):
                self.project.add_row("SUB", {"path": p}, notify=False)
        self.on_show()

    def remove(self):
        rows = sorted({i.row() for i in self.tbl.selectedIndexes()})
        subs = self.project.rows("SUB")
        ids = [subs[r]["_id"] for r in rows if r < len(subs)]
        if ids:
            self.project.delete_rows("SUB", ids)
            self.on_show()

    def on_show(self):
        self.rows = [summarize_file(p) for p in self._paths()]
        n = len(self.rows)
        self.tbl.setRowCount(0)
        if hasattr(self.tbl, "_acts"):
            self.tbl._acts.clear()
        self.tbl.setRowCount(n + (1 if n else 0))
        tot = dict(nv=0, vt=0, net=0.0, qd=0.0, need=0.0, existing=0, ok_vt=0, errors=0, warnings=0)
        for i, r in enumerate(self.rows):
            if r.get("error"):
                self.tbl.setItem(i, 0, item(r.get("unit") or r["file"]))
                self.tbl.setItem(i, 1, item(r["file"]))
                self.tbl.setItem(i, 11, item("Lỗi: " + r["error"], theme.ERR))
                continue
            vals = [r["unit"], r["file"], r["nv"], r["vt"], fmt(r["net"]), fmt(r["qd"], 3), fmt(r["need"], 3),
                    r["existing"], f"{r['ok_vt']}/{r['vt']}", r["errors"], r["warnings"], r.get("status", ""),
                    r.get("updated", "")]
            for c, v in enumerate(vals):
                color = theme.ERR if c == 9 and r["errors"] else (theme.WARN if c == 10 and r["warnings"] else None)
                self.tbl.setItem(i, c, item(v, color))
            for k in tot:
                tot[k] += r[k]
        if n:
            vals = ["TỔNG CỘNG", f"{n} hồ sơ", tot["nv"], tot["vt"], fmt(tot["net"]), fmt(tot["qd"], 3),
                    fmt(tot["need"], 3), tot["existing"], f"{tot['ok_vt']}/{tot['vt']}", tot["errors"],
                    tot["warnings"], "", ""]
            for c, v in enumerate(vals):
                self.tbl.setItem(n, c, item(v, bold=True))
        self.tbl.resizeColumnsToContents()
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def export(self):
        if not self.rows:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Xuất bảng tổng hợp", "TongHop_HoSoCapDuoi.xlsx", "Excel (*.xlsx)")
        if path:
            export_subunits(self.rows, path)
            QMessageBox.information(self, "Đã lưu", f"Đã lưu:\n{path}")


# ================================================================ ĐỒNG BỘ DỮ LIỆU
class SyncPage(BasePage):
    restored = Signal()

    def __init__(self, project):
        super().__init__("Ứng dụng / Đồng bộ dữ liệu", "Đồng bộ dữ liệu",
                         "Phần mềm chạy độc lập trên máy, không cần mạng. Chuyển dữ liệu giữa các máy bằng <b>gói dữ "
                         "liệu .vtvl</b> (qua USB, thư điện tử công vụ, thư mục dùng chung); mọi lần ghi đè đều có bản "
                         "sao lưu.")
        self.project = project
        bar = QHBoxLayout()
        for text, slot, prim in (("⭱ Xuất gói dữ liệu (.vtvl)…", self.export_pkg, True),
                                 ("⭳ Nhập gói dữ liệu (.vtvl)…", self.import_pkg, False),
                                 ("Mở thư mục sao lưu", lambda: _open_path(os.path.join(app_data_dir(), "SaoLuu")), False)):
            b = QPushButton(text)
            if prim:
                b.setObjectName("Primary")
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch(1)
        self.lay.addLayout(bar)
        t = QLabel("Bản sao lưu trên máy")
        t.setStyleSheet("font-size: 13pt; font-weight: 700;")
        self.lay.addWidget(t)
        self.tbl = table(["Tệp sao lưu", "Thời điểm", "Dung lượng", ""], stretch=(0,))
        self.tbl.setColumnWidth(1, 160)
        self.tbl.setColumnWidth(2, 110)
        self.tbl.setColumnWidth(3, 110)
        self.lay.addWidget(self.tbl, 1)

    def on_show(self):
        d = os.path.join(app_data_dir(), "SaoLuu")
        files = sorted((os.path.join(d, f) for f in os.listdir(d) if f.endswith(".vtvl")), key=os.path.getmtime,
                       reverse=True) if os.path.isdir(d) else []
        self.tbl.setRowCount(0)
        if hasattr(self.tbl, "_acts"):
            self.tbl._acts.clear()
        self.tbl.setRowCount(len(files))
        for n, p in enumerate(files):
            self.tbl.setItem(n, 0, item(os.path.basename(p)))
            self.tbl.setItem(n, 1, item(datetime.fromtimestamp(os.path.getmtime(p)).strftime("%d/%m/%Y %H:%M:%S")))
            self.tbl.setItem(n, 2, item(f"{os.path.getsize(p) / 1024:.0f} KB"))
            set_link(self.tbl, n, 3, "Khôi phục", lambda x=p: self._restore(x))

    def export_pkg(self):
        unit = "".join(ch for ch in self.project.get_meta("ten_don_vi", "HoSo") if ch.isalnum())[:30]
        path, _ = QFileDialog.getSaveFileName(self, "Xuất gói dữ liệu", f"GoiDuLieu_{datetime.now():%Y%m%d_%H%M}.vtvl",
                                              "Hồ sơ (*.vtvl)")
        if path:
            self.project.backup(path if path.endswith(".vtvl") else path + ".vtvl")
            self.project.log("Xuất gói dữ liệu", os.path.basename(path))
            QMessageBox.information(self, "Đã xuất", f"Đã xuất gói dữ liệu {unit}:\n{path}")

    def import_pkg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Nhập gói dữ liệu", "", "Hồ sơ (*.vtvl)")
        if path:
            self._restore(path)

    def _restore(self, path):
        if QMessageBox.question(self, "Ghi đè dữ liệu", f"Thay toàn bộ dữ liệu hồ sơ đang mở bằng:\n{path}?\n"
                                "Trạng thái hiện tại được sao lưu trước.") != QMessageBox.Yes:
            return
        cur = self.project.snapshot("TruocDongBo")
        self.project.restore_from(path)
        self.project.log("Nhập gói dữ liệu / khôi phục", os.path.basename(path), backup=cur)
        self.restored.emit()


# ================================================================ CÀI ĐẶT
class SettingsPage(BasePage):
    changed = Signal()

    def __init__(self, project):
        super().__init__("Ứng dụng / Cài đặt ứng dụng", "Cài đặt ứng dụng", "Giao diện, người dùng và sao lưu.")
        self.project = project
        self.st = QSettings("ThuVienCanTho", "QL-VTVL")
        card = QFrame()
        card.setObjectName("Card")
        f = QFormLayout(card)
        f.setContentsMargins(20, 16, 20, 16)
        f.setVerticalSpacing(12)
        self.theme = QComboBox()
        self.theme.addItems(["Sáng", "Tối"])
        self.accent = QComboBox()
        self.accent.addItems(list(theme.ACCENTS))
        self.font = QSpinBox()
        self.font.setRange(9, 13)
        self.font.setSuffix(" pt")
        self.user = QLineEdit()
        self.role = QComboBox()
        self.role.addItems(["Cán bộ kê khai", "Lãnh đạo xác nhận", "Đầu mối tổng hợp"])
        self.autobk = QCheckBox("Tự sao lưu hồ sơ khi đóng phần mềm")
        self.keep = QSpinBox()
        self.keep.setRange(5, 200)
        f.addRow("Chế độ hiển thị:", self.theme)
        f.addRow("Màu nhấn:", self.accent)
        f.addRow("Cỡ chữ:", self.font)
        f.addRow("Họ tên người dùng (người lập biểu):", self.user)
        f.addRow("Vai trò:", self.role)
        f.addRow("", self.autobk)
        f.addRow("Số bản sao lưu giữ lại:", self.keep)
        self.lay.addWidget(card)
        save = QPushButton("✔  Lưu cài đặt")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(save)
        self.lay.addLayout(row)
        note = QLabel("ⓘ  Mẫu Bộ biểu Excel và quỹ giờ PP2 đặt tại Hồ sơ của đơn vị → Thông tin đơn vị.")
        note.setObjectName("Note")
        self.lay.addWidget(note)
        self.lay.addStretch(1)

    def on_show(self):
        self.theme.setCurrentIndex(1 if self.st.value("dark", "false") in ("true", True) else 0)
        self.accent.setCurrentText(self.st.value("accent", "Đỏ"))
        self.font.setValue(int(self.st.value("font", 10)))
        self.user.setText(self.project.get_meta("nguoi_lap", ""))
        self.role.setCurrentText(self.st.value("role", "Cán bộ kê khai"))
        self.autobk.setChecked(self.st.value("autobackup", "true") in ("true", True))
        self.keep.setValue(int(self.st.value("keep", 20)))

    def save(self):
        self.st.setValue("dark", "true" if self.theme.currentIndex() == 1 else "false")
        self.st.setValue("accent", self.accent.currentText())
        self.st.setValue("font", self.font.value())
        self.st.setValue("role", self.role.currentText())
        self.st.setValue("autobackup", "true" if self.autobk.isChecked() else "false")
        self.st.setValue("keep", self.keep.value())
        if self.user.text().strip() != self.project.get_meta("nguoi_lap", ""):
            self.project.set_meta("nguoi_lap", self.user.text().strip())
        self.changed.emit()
