"""Điểm khởi chạy phần mềm."""
from __future__ import annotations

import os
import sys
import traceback


def _excepthook(exc_type, exc, tb):
    from PySide6.QtWidgets import QMessageBox

    from .core.db import app_data_dir

    text = "".join(traceback.format_exception(exc_type, exc, tb))
    try:
        with open(os.path.join(app_data_dir(), "loi.log"), "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except OSError:
        pass
    QMessageBox.critical(None, "Lỗi không mong muốn",
                         f"Đã xảy ra lỗi:\n{exc}\n\nChi tiết được ghi vào tệp loi.log trong thư mục dữ liệu.")


def selftest() -> int:
    """Kiểm tra nhanh bản đóng gói: tạo dữ liệu mẫu, dựng giao diện, xuất Excel/Word."""
    import tempfile

    from PySide6.QtWidgets import QApplication

    from .core.db import Project
    from .core.exporter import export_excel, export_word
    from .core.seed import ensure_defaults, load_sample
    from .ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.vtvl")
        pr = Project(path)
        ensure_defaults(pr)
        load_sample(pr)
        export_excel(pr, os.path.join(d, "t.xlsx"))
        export_word(pr, os.path.join(d, "t.docx"))
        pr.close()
        w = MainWindow()
        w.load(path)
        for i in range(len(w.pages)):
            w.go(i)
            app.processEvents()
        w.project.close()
        w.project = None
        w.deleteLater()
        app.processEvents()
    return 0


def main(argv=None):
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from .ui.main_window import MainWindow
    from .ui.theme import STYLE

    if "--selftest" in (argv or sys.argv):
        try:
            return selftest()
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            return 1
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ThuVienCanTho.QLVTVL")
        except Exception:  # noqa: BLE001
            pass
    app = QApplication(argv or sys.argv)
    app.setApplicationName("QL-VTVL")
    app.setOrganizationName("ThuVienCanTho")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(STYLE)
    sys.excepthook = _excepthook
    w = MainWindow()
    args = [a for a in (argv or sys.argv)[1:] if a.lower().endswith(".vtvl") and os.path.exists(a)]
    if args:
        w.load(args[0])
    elif not w.start():
        return 0
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
