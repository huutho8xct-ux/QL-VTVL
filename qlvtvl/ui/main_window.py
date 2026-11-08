"""Cửa sổ chính: thanh trên cùng + thanh bên chia nhóm Kê khai – Đơn vị – Ứng dụng."""
from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime

from PySide6.QtCore import QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from .. import __version__
from ..core.checks import ERROR, WARNING, run_checks
from ..core.db import Project, app_data_dir
from ..core.guide import STEPS
from ..core.seed import ensure_defaults, load_sample
from . import theme
from .import_page import ImportPage
from .pages import DashboardPage, HelpPage
from .pages2 import (
    FormsPage, HistoryPage, IssuesPage, ProfilesPage, SendPage, SettingsPage, SubunitsPage, SyncPage, UnitPage,
)
from .widgets import chip, icon_button

APP_NAME = "Hệ thống nhập liệu vị trí việc làm"
ORG = "Thư viện thành phố Cần Thơ"
FILE_FILTER = "Hồ sơ vị trí việc làm (*.vtvl);;Tất cả tệp (*.*)"
ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

NAV = (
    ("KÊ KHAI", (
        ("dashboard", "⌂", "Trang làm việc"),
        ("unit", "🏛", "Hồ sơ của đơn vị"),
        ("profiles", "🗀", "Hồ sơ"),
        ("forms", "▦", "Nhập 09 biểu"),
        ("issues", "⚠", "Lỗi và giải trình"),
        ("import", "⭱", "Nhập từ Excel"),
        ("send", "➤", "Kiểm tra và gửi"),
        ("history", "⟲", "Lịch sử hồ sơ"),
    )),
    ("ĐƠN VỊ", (("sub", "👥", "Hồ sơ cấp dưới"),)),
    ("ỨNG DỤNG", (
        ("sync", "⟳", "Đồng bộ dữ liệu"),
        ("settings", "⚙", "Cài đặt ứng dụng"),
        ("help", "?", "Hướng dẫn sử dụng"),
    )),
)


def unidecode_vn(text: str) -> str:
    text = text.replace("Đ", "D").replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return "TV"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bắt đầu")
        self.choice = None
        self.resize(580, 360)
        v = QVBoxLayout(self)
        v.setContentsMargins(26, 22, 26, 22)
        t = QLabel("Hệ thống nhập liệu vị trí việc làm")
        t.setObjectName("PageTitle")
        v.addWidget(t)
        s = QLabel("Rà soát vị trí việc làm, nhu cầu nhân lực và phương án biên chế 2027–2031 theo Hướng dẫn số "
                   "7-HD/BTCTW ngày 19/10/2026 và Bộ biểu Excel kèm theo. Chọn cách bắt đầu:")
        s.setWordWrap(True)
        s.setObjectName("PageSub")
        v.addWidget(s)
        v.addSpacing(8)
        for key, title, desc, primary in (
            ("blank", "Tạo hồ sơ mới (trống)", "Bắt đầu kê khai số liệu thực tế của đơn vị.", True),
            ("import", "Tạo hồ sơ mới từ Bộ biểu Excel đã điền", "Kế thừa dữ liệu đã kê khai; kiểm tra lỗi trước khi "
                                                                 "kết chuyển.", False),
            ("sample", "Mở hồ sơ có dữ liệu minh họa", "Số liệu mẫu của Thư viện TP Cần Thơ để làm quen.", False),
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
        self.pages = {}
        self.setWindowTitle(APP_NAME)
        self.resize(1440, 900)
        self.setMinimumSize(1150, 700)
        ico = os.path.join(ASSETS, "app.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))
        self.apply_settings(rebuild=False)
        self.status_lbl = QLabel()
        self.statusBar().addPermanentWidget(self.status_lbl)
        for seq, slot in (("Ctrl+N", self.new_project), ("Ctrl+O", self.open_project),
                          ("Ctrl+I", lambda: self.go("import")), ("Ctrl+E", self.export_excel),
                          ("Ctrl+Shift+S", self.save_as), ("F1", lambda: self.go("help")),
                          ("Ctrl+Q", self.close)):
            QShortcut(QKeySequence(seq), self, slot)
        self._bell_timer = QTimer(self)
        self._bell_timer.setSingleShot(True)
        self._bell_timer.timeout.connect(self.refresh_topbar)

    # ------------------------------------------------------------ giao diện
    def apply_settings(self, rebuild=True):
        dark = self.settings.value("dark", "false") in ("true", True)
        style = theme.apply_theme(dark, self.settings.value("accent", "Đỏ"))
        app = QApplication.instance()
        if app:
            f = QFont("Segoe UI", int(self.settings.value("font", 10)))
            app.setFont(f)
            app.setStyleSheet(style.replace("font-size: 10pt;", f"font-size: {int(self.settings.value('font', 10))}pt;", 1))
        if rebuild and self.project:
            cur = self.current_key()
            self.build_ui()
            self.go(cur or "dashboard")

    def toggle_dark(self):
        self.settings.setValue("dark", "false" if theme.DARK else "true")
        self.apply_settings()

    def _top_bar(self):
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(64)
        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 6, 16, 6)
        h.setSpacing(10)
        h.addWidget(icon_button("☰", "Thu gọn / mở rộng thanh bên", self.toggle_sidebar))
        logo = QLabel()
        pm = QPixmap(os.path.join(ASSETS, "app.png"))
        if not pm.isNull():
            logo.setPixmap(pm.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        h.addWidget(logo)
        tv = QVBoxLayout()
        tv.setSpacing(0)
        t = QLabel("HỆ THỐNG NHẬP LIỆU VỊ TRÍ VIỆC LÀM")
        t.setObjectName("AppTitle")
        sub = QLabel(f"{self.project.meta().get('ten_don_vi', ORG)} · Hướng dẫn 7-HD/BTCTW")
        sub.setObjectName("AppSub")
        tv.addWidget(t)
        tv.addWidget(sub)
        h.addLayout(tv)
        h.addSpacing(18)
        m = self.project.meta()
        self.chip_unit = chip(m.get("ten_don_vi", ORG), lambda: self.go("unit"), "Đơn vị kê khai")
        self.chip_ky = chip(f"Kỳ {m.get('ky_thong_ke', '')}", lambda: self.go("unit"), "Kỳ thống kê khối lượng")
        self.chip_status = chip("", lambda: self.go("send"), "Trạng thái hồ sơ")
        for c in (self.chip_unit, self.chip_ky, self.chip_status):
            h.addWidget(c)
        h.addStretch(1)
        bell_box = QWidget()
        bl = QHBoxLayout(bell_box)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)
        self.bell = icon_button("🔔", "Lỗi và cảnh báo của hồ sơ", lambda: self.go("issues"))
        self.bell_badge = QLabel("0")
        self.bell_badge.setObjectName("Badge")
        bl.addWidget(self.bell)
        bl.addWidget(self.bell_badge, 0, Qt.AlignTop)
        h.addWidget(bell_box)
        h.addWidget(icon_button("☾" if not theme.DARK else "☀", "Chuyển giao diện sáng/tối", self.toggle_dark))
        h.addWidget(icon_button("?", "Hướng dẫn sử dụng (F1)", lambda: self.go("help")))
        h.addSpacing(6)
        self.avatar = QLabel()
        self.avatar.setObjectName("Avatar")
        self.avatar.setAlignment(Qt.AlignCenter)
        h.addWidget(self.avatar)
        uv = QVBoxLayout()
        uv.setSpacing(0)
        self.user_lbl = QLabel()
        self.user_lbl.setStyleSheet("font-weight:600;")
        self.role_lbl = QLabel()
        self.role_lbl.setObjectName("AppSub")
        uv.addWidget(self.user_lbl)
        uv.addWidget(self.role_lbl)
        h.addLayout(uv)
        return bar

    def _sidebar(self):
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(270)
        v = QVBoxLayout(side)
        v.setContentsMargins(4, 12, 4, 10)
        self.nav = QListWidget()
        self.nav.setObjectName("Nav")
        self.nav_keys = []
        for section, items in NAV:
            head = QListWidgetItem(section)
            head.setFlags(Qt.NoItemFlags)
            f = head.font()
            f.setPointSizeF(8.5)
            f.setLetterSpacing(QFont.PercentageSpacing, 110)
            head.setFont(f)
            head.setForeground(Qt.gray)
            head.setSizeHint(QSize(200, 34))
            self.nav.addItem(head)
            self.nav_keys.append(None)
            for key, icon, label in items:
                it = QListWidgetItem(f"{icon}   {label}")
                it.setData(Qt.UserRole, label)
                self.nav.addItem(it)
                self.nav_keys.append(key)
        self.nav.currentRowChanged.connect(self._on_nav)
        v.addWidget(self.nav, 1)
        foot = QLabel(f"Phiên bản {__version__}\nDữ liệu lưu trên máy, không cần mạng")
        foot.setObjectName("AppSub")
        foot.setContentsMargins(12, 0, 0, 0)
        v.addWidget(foot)
        self.sidebar = side
        return side

    def toggle_sidebar(self):
        collapsed = self.sidebar.width() > 100
        self.sidebar.setFixedWidth(64 if collapsed else 270)
        for i, key in enumerate(self.nav_keys):
            it = self.nav.item(i)
            if key is None:
                it.setHidden(collapsed)
            else:
                label = it.data(Qt.UserRole)
                icon = it.text().split("   ")[0]
                it.setText(icon if collapsed else f"{icon}   {label}")
                it.setToolTip(label)

    def build_ui(self):
        self.project._listeners.clear()
        old = self.centralWidget()
        root = QWidget()
        rv = QVBoxLayout(root)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)
        rv.addWidget(self._top_bar())
        body = QHBoxLayout()
        body.setSpacing(0)
        body.addWidget(self._sidebar())
        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)
        rv.addLayout(body, 1)
        p = self.project
        send_step = next(st for st in STEPS if not st.forms)
        self.pages = {
            "dashboard": DashboardPage(p), "unit": UnitPage(p), "profiles": ProfilesPage(p), "forms": FormsPage(p),
            "issues": IssuesPage(p), "import": ImportPage(p), "send": SendPage(p, send_step),
            "history": HistoryPage(p), "sub": SubunitsPage(p), "sync": SyncPage(p), "settings": SettingsPage(p),
            "help": HelpPage(),
        }
        for w in self.pages.values():
            self.stack.addWidget(w)
        pg = self.pages
        pg["dashboard"].go_step.connect(self.go_step)
        pg["issues"].open_form.connect(self.goto_issue)
        pg["send"].goto.connect(self.goto_issue)
        pg["send"].export_excel.connect(self.export_excel)
        pg["send"].export_word.connect(self.export_word)
        pg["send"].sent.connect(self.refresh_topbar)
        pg["import"].open_form.connect(lambda c, k: self.open_form(c, key=k))
        pg["import"].imported.connect(self._after_data_change)
        pg["history"].restored.connect(self._after_restore)
        pg["sync"].restored.connect(self._after_restore)
        pg["profiles"].request_new.connect(self.new_project)
        pg["profiles"].request_open.connect(self.load)
        pg["profiles"].request_sample.connect(self.open_sample)
        pg["profiles"].request_save_as.connect(self.save_as)
        pg["settings"].changed.connect(self.apply_settings)
        p.subscribe(lambda form: self._bell_timer.start(500))
        self.setCentralWidget(root)
        if old:
            old.deleteLater()
        self.go("dashboard")
        self.refresh_topbar()

    # ------------------------------------------------------------- điều hướng
    def current_key(self):
        row = self.nav.currentRow() if hasattr(self, "nav") else -1
        return self.nav_keys[row] if 0 <= row < len(getattr(self, "nav_keys", [])) else None

    def go(self, key):
        if key in self.nav_keys:
            self.nav.setCurrentRow(self.nav_keys.index(key))

    def _on_nav(self, row):
        key = self.nav_keys[row] if 0 <= row < len(self.nav_keys) else None
        if not key:
            return
        page = self.pages[key]
        self.stack.setCurrentWidget(page)
        if hasattr(page, "on_show"):
            page.on_show()

    def go_step(self, n):
        st = next((x for x in STEPS if x.no == n), None)
        if st and st.forms:
            self.open_form(st.forms[0])
        else:
            self.go("send")

    def open_form(self, code, row_id=None, key=None):
        self.go("forms")
        self.pages["forms"].open(code, row_id=row_id, key=key)

    def goto_issue(self, form, row_id, ref):
        if form == "TT":
            self.go("unit")
            return
        self.open_form(form, row_id=row_id, key=None if row_id else ref)

    def refresh_topbar(self):
        if not self.project or not hasattr(self, "bell_badge"):
            return
        m = self.project.meta()
        issues = run_checks(self.project)
        n = sum(1 for i in issues if i.level in (ERROR, WARNING))
        self.bell_badge.setText(str(n) if n < 100 else "99+")
        self.bell_badge.setVisible(n > 0)
        self.chip_unit.setText(m.get("ten_don_vi", ORG)[:34])
        self.chip_ky.setText(f"Kỳ {m.get('ky_thong_ke', '')}")
        ver = m.get("phien_ban") or "0"
        status = m.get("trang_thai_ho_so") or "Đang kê khai"
        self.chip_status.setText(f"{'✔ ' if status == 'Đã gửi' else '✎ '}{status}" + (f" · v{ver}" if ver != "0" else ""))
        name = m.get("nguoi_lap", "") or "Chưa đặt tên người dùng"
        self.avatar.setText(initials(m.get("nguoi_lap", "") or m.get("ten_don_vi", "TV")))
        self.user_lbl.setText(name)
        self.role_lbl.setText(self.settings.value("role", "Cán bộ kê khai"))
        self.status_lbl.setText(f"💾 Tự lưu {datetime.now():%H:%M:%S}   |   Hồ sơ: {self.project.path}")

    def _after_data_change(self):
        self.refresh_topbar()

    def _after_restore(self):
        cur = self.current_key()
        self.build_ui()
        self.go(cur or "dashboard")
        QMessageBox.information(self, "Khôi phục", "Đã khôi phục dữ liệu hồ sơ.")

    # --------------------------------------------------------------- hồ sơ
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
        if dlg.choice == "import":
            ok = self.new_project(first=True)
            if ok:
                self.go("import")
            return ok
        if dlg.choice == "sample":
            return self.open_sample()
        return self.open_project() or self.new_project(first=True)

    def load(self, path):
        if self.project:
            self.project.close()
        self.project = Project(path)
        ensure_defaults(self.project)
        self.settings.setValue("last_project", path)
        recent = [p for p in (self.settings.value("recent", []) or []) if p != path]
        self.settings.setValue("recent", ([path] + recent)[:10])
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
            if self.project and os.path.abspath(self.project.path) == os.path.abspath(path):
                self.project.close()
                self.project = None
            os.remove(path)
        self.load(path)
        self.project.log("Tạo hồ sơ mới", os.path.basename(path))
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
        if self.project and os.path.abspath(self.project.path) == os.path.abspath(path):
            self.project.close()
            self.project = None
        if os.path.exists(path):
            os.remove(path)
        pr = Project(path)
        ensure_defaults(pr)
        load_sample(pr)
        pr.log("Tạo hồ sơ dữ liệu minh họa", "Số liệu mẫu, không phải số liệu chính thức")
        pr.close()
        self.load(path)
        QMessageBox.information(self, "Dữ liệu minh họa",
                                "Đã mở hồ sơ dữ liệu MINH HỌA của Thư viện thành phố Cần Thơ.\n\nSố liệu chỉ để làm quen. "
                                "Khi rà soát chính thức, hãy tạo hồ sơ mới (mục Hồ sơ).")
        return True

    def save_as(self):
        path = self._ask_path("Lưu bản sao hồ sơ", f"SaoLuu_VTVL_{datetime.now():%Y%m%d_%H%M}.vtvl")
        if not path:
            return
        self.project.backup(path)
        self.project.log("Lưu bản sao hồ sơ", path)
        if QMessageBox.question(self, "Đã lưu", f"Đã lưu bản sao:\n{path}\n\nChuyển sang làm việc với bản sao này?"
                                ) == QMessageBox.Yes:
            self.load(path)

    # ---------------------------------------------------------------- xuất
    def _export_path(self, title, name, flt):
        d = self.settings.value("export_dir", os.path.expanduser("~/Documents"))
        path, _ = QFileDialog.getSaveFileName(self, title, os.path.join(d, name), flt)
        if path:
            self.settings.setValue("export_dir", os.path.dirname(path))
        return path

    def export_excel(self):
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
        self.project.log("Xuất Bộ biểu Excel", os.path.basename(path))
        extra = ""
        if info.get("fixed"):
            extra += f"\n\nĐã tự sửa {info['fixed']} ô công thức lỗi của bản phát hành."
        if info.get("overflow"):
            extra += "\n\nVượt sức chứa bộ biểu: " + ", ".join(f"{k}: {v} dòng" for k, v in info["overflow"].items())
        self._done(path, extra)

    def export_word(self):
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
        self.project.log("Xuất báo cáo Word", os.path.basename(path))
        self._done(path)

    def _done(self, path, extra=""):
        box = QMessageBox(self)
        box.setWindowTitle("Hoàn tất")
        box.setText(f"Đã xuất tệp:\n{path}{extra}")
        open_btn = box.addButton("Mở tệp", QMessageBox.AcceptRole)
        box.addButton("Đóng", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def import_all(self):
        self.go("import")

    def open_import(self, code=None):
        self.go("import")
        self.pages["import"].reset()
        self.pages["import"].set_scope(code)

    def closeEvent(self, e):
        if self.project:
            if self.settings.value("autobackup", "true") in ("true", True):
                try:
                    self.project.snapshot("KhiDong")
                    d = os.path.join(app_data_dir(), "SaoLuu")
                    keep = int(self.settings.value("keep", 20))
                    files = sorted(f for f in os.listdir(d) if f.startswith("KhiDong_"))
                    for f in files[:-keep]:
                        os.remove(os.path.join(d, f))
                except OSError:
                    pass
            self.project.close()
        super().closeEvent(e)
