"""Cửa sổ chính."""
from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime

from PySide6.QtCore import QSettings, QSize, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from .. import __version__
from ..core.checks import ERROR, run_checks, step_status
from ..core.db import Project, app_data_dir
from ..core.guide import STEPS
from ..core.seed import ensure_defaults, load_sample
from .pages import CheckPage, DashboardPage, HelpPage, InfoPage, LegalPage, StepPage

def unidecode_vn(text: str) -> str:
    text = text.replace("Đ", "D").replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


APP_NAME = "Phần mềm rà soát vị trí việc làm"
ORG = "Thư viện thành phố Cần Thơ"
FILE_FILTER = "Hồ sơ vị trí việc làm (*.vtvl);;Tất cả tệp (*.*)"


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bắt đầu")
        self.choice = None
        self.resize(560, 330)
        v = QVBoxLayout(self)
        v.setContentsMargins(26, 22, 26, 22)
        t = QLabel("Chào mừng đến với phần mềm rà soát vị trí việc làm")
        t.setObjectName("PageTitle")
        t.setWordWrap(True)
        v.addWidget(t)
        s = QLabel("Thực hiện theo 08 bước và Bộ biểu Excel kèm Hướng dẫn số 7-HD/BTCTW ngày 19/10/2026 "
                   "của Ban Tổ chức Trung ương. Chọn cách bắt đầu:")
        s.setWordWrap(True)
        s.setObjectName("PageSub")
        v.addWidget(s)
        v.addSpacing(10)
        for key, title, desc, primary in (
            ("blank", "Tạo hồ sơ mới (trống)", "Bắt đầu nhập số liệu thực tế của đơn vị.", True),
            ("sample", "Mở hồ sơ có dữ liệu minh họa",
             "Dữ liệu mẫu của Thư viện TP Cần Thơ để làm quen phần mềm (không phải số liệu chính thức).", False),
            ("open", "Mở hồ sơ đã có (.vtvl)", "Tiếp tục làm việc với hồ sơ đã lưu.", False),
        ):
            b = QPushButton(f"{title}\n{desc}")
            b.setStyleSheet("text-align:left; padding:10px 14px;")
            if primary:
                b.setObjectName("Primary")
            b.clicked.connect(lambda _=False, k=key: self._pick(k))
            v.addWidget(b)
        v.addStretch(1)

    def _pick(self, k):
        self.choice = k
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("ThuVienCanTho", "QL-VTVL")
        self.project: Project | None = None
        self.setWindowTitle(APP_NAME)
        self.resize(1400, 860)
        self.setMinimumSize(1100, 680)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "app.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self._build_menu()
        self.status_lbl = QLabel()
        self.statusBar().addPermanentWidget(self.status_lbl)

    # ------------------------------------------------------------------ menu
    def _build_menu(self):
        mb = self.menuBar()
        m = mb.addMenu("&Tệp")
        self._act(m, "Hồ sơ mới...", self.new_project, QKeySequence.New)
        self._act(m, "Mở hồ sơ...", self.open_project, QKeySequence.Open)
        self._act(m, "Lưu thành (sao lưu)...", self.save_as, QKeySequence("Ctrl+Shift+S"))
        self._act(m, "Mở hồ sơ dữ liệu minh họa", self.open_sample)
        m.addSeparator()
        self._act(m, "Nhập từ Bộ biểu Excel chính thức (đã điền)...", self.import_all)
        m.addSeparator()
        self._act(m, "Thoát", self.close, QKeySequence("Ctrl+Q"))
        x = mb.addMenu("&Xuất báo cáo")
        self._act(x, "Xuất vào Bộ biểu Excel chính thức...", self.export_excel, QKeySequence("Ctrl+E"))
        self._act(x, "Báo cáo thuyết minh (Word)...", self.export_word, QKeySequence("Ctrl+W"))
        h = mb.addMenu("Trợ &giúp")
        self._act(h, "Hướng dẫn sử dụng", lambda: self.go(len(self.pages) - 1), QKeySequence.HelpContents)
        self._act(h, "Thư mục dữ liệu", lambda: self._open_folder(app_data_dir()))
        self._act(h, "Giới thiệu", self.about)

    def _act(self, menu, text, slot, shortcut=None):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    # ------------------------------------------------------------- building
    def build_ui(self):
        self.project._listeners.clear()
        old = self.centralWidget()
        root = QWidget()
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(300)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(10, 16, 10, 10)
        brand = QLabel("📚  QL-VTVL")
        brand.setObjectName("Brand")
        sub = QLabel(f"Rà soát vị trí việc làm\n{self.project.meta().get('ten_don_vi', ORG)}")
        sub.setObjectName("BrandSub")
        sub.setWordWrap(True)
        sv.addWidget(brand)
        sv.addWidget(sub)
        sv.addSpacing(10)
        self.nav = QListWidget()
        self.nav.setObjectName("Nav")
        self.nav.setIconSize(QSize(18, 18))
        sv.addWidget(self.nav, 1)
        foot = QLabel(f"Theo Hướng dẫn 07-HD/BTCTW\nPhiên bản {__version__}")
        foot.setObjectName("BrandSub")
        sv.addWidget(foot)
        h.addWidget(side)

        self.stack = QStackedWidget()
        h.addWidget(self.stack, 1)
        self.pages = []
        p = self.project
        self.dashboard = DashboardPage(p)
        self.dashboard.go_step.connect(lambda n: self.go(self.step_index[n]))
        self._add("🏠  Tổng quan", self.dashboard)
        self._add("🏛  Thông tin đơn vị", InfoPage(p))
        self.step_index = {}
        self.step_pages = {}
        self.form_step = {}
        for st in STEPS:
            if st.forms:
                page = StepPage(p, st)
                page.next_btn.clicked.connect(lambda _=False, n=st.no: self.go(self.step_index[n + 1]))
                page.prev_btn.clicked.connect(lambda _=False, n=st.no: self.go(self.step_index[n - 1]))
                for ed in page.editors.values():
                    ed.changed.connect(self._update_status)
                for f in st.forms:
                    self.form_step[f] = st.no
            else:
                page = CheckPage(p, st)
                page.goto.connect(self.goto_issue)
                page.export_excel.connect(self.export_excel)
                page.export_word.connect(self.export_word)
            self.step_index[st.no] = len(self.pages)
            self.step_pages[st.no] = page
            self._add(f"Bước {st.no}. {st.short}", page)
        self._add("⚖  Căn cứ pháp lý", LegalPage(p))
        self._add("❔  Hướng dẫn sử dụng", HelpPage())
        self.nav.currentRowChanged.connect(self._on_nav)
        self.setCentralWidget(root)
        if old:
            old.deleteLater()
        self.nav.setCurrentRow(0)
        self._refresh_nav()
        self._update_status()

    def _add(self, label, page):
        self.pages.append(page)
        self.stack.addWidget(page)
        it = QListWidgetItem(label)
        self.nav.addItem(it)

    def _on_nav(self, i):
        if i < 0:
            return
        self.stack.setCurrentIndex(i)
        self.pages[i].on_show()
        self._refresh_nav()

    def go(self, i):
        self.nav.setCurrentRow(i)

    def _refresh_nav(self):
        status = step_status(self.project)
        icon = {"done": "✅", "partial": "🟡", "empty": "⚪"}
        for st in STEPS:
            it = self.nav.item(self.step_index[st.no])
            it.setText(f"{icon[status[st.no]]}  Bước {st.no}. {st.short}")
            it.setToolTip(st.title)

    def goto_issue(self, form, row_id, ref):
        if form == "TT":
            self.go(1)
            return
        n = self.form_step.get(form)
        if not n:
            return
        self.go(self.step_index[n])
        page = self.step_pages[n]
        page.show_form(form, row_id=row_id, key=None if row_id else ref)
        if not row_id and ref and form == "C3":
            # lỗi phân công công việc: mở C3 ở đầu biểu
            pass

    def _update_status(self):
        if not self.project:
            return
        t = datetime.now().strftime("%H:%M:%S")
        self.status_lbl.setText(f"💾 Đã lưu tự động lúc {t}   |   Hồ sơ: {self.project.path}")
        if hasattr(self, "nav"):
            QTimer.singleShot(0, self._refresh_nav)

    # --------------------------------------------------------------- project
    def start(self):
        last = self.settings.value("last_project", "")
        if last and os.path.exists(last):
            self.load(last)
            return True
        dlg = WelcomeDialog(self)
        if not dlg.exec():
            return False
        if dlg.choice == "blank":
            return self.new_project(first=True)
        if dlg.choice == "sample":
            return self.open_sample()
        return self.open_project() or self.new_project(first=True)

    def load(self, path):
        if self.project:
            self.project.close()
        self.project = Project(path)
        ensure_defaults(self.project)
        self.settings.setValue("last_project", path)
        self.setWindowTitle(f"{APP_NAME} – {os.path.basename(path)}")
        self.build_ui()

    def _ask_path(self, title, default_name):
        default = os.path.join(self.settings.value("last_dir", os.path.expanduser("~/Documents")), default_name)
        path, _ = QFileDialog.getSaveFileName(self, title, default, FILE_FILTER)
        if path and not path.lower().endswith(".vtvl"):
            path += ".vtvl"
        if path:
            self.settings.setValue("last_dir", os.path.dirname(path))
        return path

    def new_project(self, first=False):
        name = f"HoSo_VTVL_{datetime.now():%Y}.vtvl"
        path = self._ask_path("Tạo hồ sơ mới", name)
        if not path:
            if first:
                path = os.path.join(app_data_dir(), name)
            else:
                return False
        if os.path.exists(path):
            if QMessageBox.question(self, "Tệp đã tồn tại", "Ghi đè tệp đã có?") != QMessageBox.Yes:
                return False
            os.remove(path)
        self.load(path)
        return True

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Mở hồ sơ", self.settings.value("last_dir", ""), FILE_FILTER)
        if not path:
            return False
        self.settings.setValue("last_dir", os.path.dirname(path))
        self.load(path)
        return True

    def open_sample(self):
        path = os.path.join(app_data_dir(), "DuLieuMinhHoa_ThuVienCanTho.vtvl")
        if os.path.exists(path):
            if self.project and os.path.abspath(self.project.path) == os.path.abspath(path):
                self.project.close()
                self.project = None
            os.remove(path)
        pr = Project(path)
        ensure_defaults(pr)
        load_sample(pr)
        pr.close()
        self.load(path)
        QMessageBox.information(self, "Dữ liệu minh họa",
                                "Đã mở hồ sơ dữ liệu MINH HỌA của Thư viện thành phố Cần Thơ.\n\n"
                                "Số liệu chỉ để làm quen phần mềm. Khi rà soát chính thức, hãy tạo hồ sơ mới "
                                "(Tệp → Hồ sơ mới) hoặc sửa trực tiếp bằng số liệu đã được xác nhận.")
        return True

    def save_as(self):
        path = self._ask_path("Lưu bản sao hồ sơ", f"SaoLuu_VTVL_{datetime.now():%Y%m%d_%H%M}.vtvl")
        if not path:
            return
        self.project.backup(path)
        if QMessageBox.question(self, "Đã lưu", f"Đã lưu bản sao:\n{path}\n\nChuyển sang làm việc với bản sao này?"
                                ) == QMessageBox.Yes:
            self.load(path)

    # ---------------------------------------------------------------- export
    def _export_path(self, title, name, flt):
        meta_dir = self.settings.value("export_dir", os.path.expanduser("~/Documents"))
        path, _ = QFileDialog.getSaveFileName(self, title, os.path.join(meta_dir, name), flt)
        if path:
            self.settings.setValue("export_dir", os.path.dirname(path))
        return path

    def _confirm_errors(self):
        errs = [i for i in run_checks(self.project) if i.level == ERROR]
        if not errs:
            return True
        return QMessageBox.question(
            self, "Còn lỗi dữ liệu",
            f"Dữ liệu còn {len(errs)} lỗi (xem Bước 8). Vẫn xuất báo cáo để xem trước?") == QMessageBox.Yes

    def export_excel(self):
        if not self._confirm_errors():
            return
        unit = re.sub(r"[^A-Za-z0-9]+", "", unidecode_vn(self.project.meta().get("ten_don_vi", ""))) or "DonVi"
        path = self._export_path("Xuất vào Bộ biểu Excel chính thức",
                                 f"BoBieu_VTVL_{unit}_{datetime.now():%Y%m%d}.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        from ..core.exporter import export_official
        try:
            info = export_official(self.project, path)
        except PermissionError:
            QMessageBox.critical(self, "Lỗi", "Không ghi được tệp. Hãy đóng tệp nếu đang mở trong Excel.")
            return
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không xuất được bộ biểu: {e}")
            return
        extra = ""
        if info.get("fixed"):
            extra += (f"\n\nĐã tự sửa {info['fixed']} ô công thức lỗi của bản phát hành (tham chiếu tệp ngoài, "
                      "chuỗi thông báo bị đánh số, tên QUY_GIO_PP2 bị lệch).")
        if info.get("overflow"):
            extra += "\n\nVượt sức chứa bộ biểu: " + ", ".join(f"{k}: {v} dòng" for k, v in info["overflow"].items()) + \
                     " (đã ghi giá trị tính sẵn; báo đầu mối hỗ trợ kỹ thuật)."
        self._done(path, extra)

    def export_word(self):
        if not self._confirm_errors():
            return
        path = self._export_path("Xuất báo cáo thuyết minh", f"BaoCao_RaSoat_VTVL_{datetime.now():%Y%m%d}.docx",
                                 "Word (*.docx)")
        if not path:
            return
        if not path.lower().endswith(".docx"):
            path += ".docx"
        from ..core.exporter import export_word
        try:
            export_word(self.project, path)
        except PermissionError:
            QMessageBox.critical(self, "Lỗi", "Không ghi được tệp. Hãy đóng tệp nếu đang mở trong Word.")
            return
        self._done(path)

    def _done(self, path, extra=""):
        box = QMessageBox(self)
        box.setWindowTitle("Hoàn tất")
        box.setText(f"Đã xuất tệp:\n{path}{extra}")
        open_btn = box.addButton("Mở tệp", QMessageBox.AcceptRole)
        box.addButton("Đóng", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            self._open_folder(path)

    def import_all(self):
        path, _ = QFileDialog.getOpenFileName(self, "Nhập từ Bộ biểu Excel chính thức", "", "Excel (*.xlsx)")
        if not path:
            return
        if QMessageBox.question(self, "Xác nhận", "Dữ liệu các biểu có trong tệp sẽ thay thế dữ liệu hiện tại. "
                                "Nên sao lưu hồ sơ trước. Tiếp tục?") != QMessageBox.Yes:
            return
        from ..core.exporter import import_official
        try:
            res = import_official(self.project, path)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không đọc được tệp: {e}")
            return
        self.build_ui()
        QMessageBox.information(self, "Hoàn tất", "Đã nhập: " + ", ".join(f"{k}: {v} dòng" for k, v in res.items())
                                if res else "Không tìm thấy biểu nào đúng cấu trúc.")

    @staticmethod
    def _open_folder(path):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def about(self):
        QMessageBox.about(
            self, "Giới thiệu",
            f"<h3>{APP_NAME}</h3><p>Phiên bản {__version__}</p>"
            f"<p>Đơn vị sử dụng: <b>{ORG}</b></p>"
            "<p>Hỗ trợ rà soát, hoàn thiện vị trí việc làm, xác định nhu cầu nhân lực và xây dựng phương án "
            "số lượng người làm việc giai đoạn 2027 - 2031 theo <b>Hướng dẫn số 07-HD/BTCTW ngày 19/10/2026</b> "
            "của Ban Tổ chức Trung ương (08 bước, Bộ biểu Excel 19-10-2026: A1, A2, B1, B2, C1, C2, C3, D1, D2), "
            "Kết luận 107-KL/TW, Nghị định 232/2026/NĐ-CP, Luật Viên chức 2025, "
            "Nghị định 106/2020/NĐ-CP và Thông tư 10/2023/TT-BVHTTDL.</p>"
            "<p>Dữ liệu lưu cục bộ trên máy tính, không gửi ra ngoài.</p>")

    def closeEvent(self, e):
        if self.project:
            self.project.close()
        super().closeEvent(e)
