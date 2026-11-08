"""Giao diện: màu sắc và stylesheet."""

PRIMARY = "#0B5394"
PRIMARY_DARK = "#083C6B"
ACCENT = "#C9A227"
BG = "#F4F6FA"
CARD = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#6B7280"
BORDER = "#D9DEE7"
OK = "#1E8E3E"
WARN = "#D58512"
ERR = "#C62828"
CALC_BG = "#EEF3FA"

STYLE = f"""
* {{ font-family: "Segoe UI", "Arial", sans-serif; font-size: 10pt; color: {TEXT}; }}
QMainWindow, QWidget#Page {{ background: {BG}; }}
QWidget#Sidebar {{ background: {PRIMARY_DARK}; }}
QLabel#Brand {{ color: white; font-size: 12pt; font-weight: 700; padding: 4px 0; }}
QLabel#BrandSub {{ color: #C9D7EA; font-size: 9pt; }}
QListWidget#Nav {{ background: transparent; border: none; outline: none; }}
QListWidget#Nav::item {{ color: #E3ECF7; padding: 9px 10px; border-radius: 6px; margin: 1px 6px; }}
QListWidget#Nav::item:hover {{ background: rgba(255,255,255,0.10); }}
QListWidget#Nav::item:selected {{ background: white; color: {PRIMARY_DARK}; font-weight: 600; }}
QLabel#PageTitle {{ font-size: 17pt; font-weight: 700; color: {PRIMARY_DARK}; }}
QLabel#PageSub {{ color: {MUTED}; font-size: 10pt; }}
QLabel#StepBadge {{ background: {PRIMARY}; color: white; border-radius: 15px; font-weight: 700;
                    font-size: 12pt; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; }}
QFrame#Card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; }}
QLabel#CardValue {{ font-size: 20pt; font-weight: 700; color: {PRIMARY_DARK}; }}
QLabel#CardLabel {{ color: {MUTED}; font-size: 9pt; }}
QLabel#Note {{ background: #FFF8E1; border: 1px solid #F3DFA2; border-radius: 6px; padding: 7px 10px;
               color: #5D4A00; }}
QTextBrowser#Guide {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px 10px; }}
QPushButton {{ background: white; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 12px; }}
QPushButton:hover {{ border-color: {PRIMARY}; color: {PRIMARY}; }}
QPushButton:pressed {{ background: #E8EEF7; }}
QPushButton#Primary {{ background: {PRIMARY}; color: white; border: 1px solid {PRIMARY}; font-weight: 600; }}
QPushButton#Primary:hover {{ background: {PRIMARY_DARK}; color: white; }}
QPushButton#Danger:hover {{ border-color: {ERR}; color: {ERR}; }}
QPushButton#Link {{ border: none; background: transparent; color: {PRIMARY}; text-align: left; padding: 2px; }}
QPushButton#Link:hover {{ text-decoration: underline; }}
QTableView {{ background: white; gridline-color: #E5E9F0; border: 1px solid {BORDER}; border-radius: 6px;
              selection-background-color: #CFE2FF; selection-color: {TEXT}; alternate-background-color: #FAFBFD; }}
QHeaderView::section {{ background: #E9EFF8; color: {PRIMARY_DARK}; font-weight: 600; padding: 6px 4px;
                        border: none; border-right: 1px solid #D5DEEB; border-bottom: 1px solid #D5DEEB; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: #E3E9F2; padding: 8px 16px; margin-right: 3px; border-top-left-radius: 6px;
                border-top-right-radius: 6px; color: {MUTED}; }}
QTabBar::tab:selected {{ background: white; color: {PRIMARY_DARK}; font-weight: 600; }}
QLineEdit, QComboBox, QPlainTextEdit, QDoubleSpinBox, QSpinBox, QTextEdit {{
    background: white; border: 1px solid {BORDER}; border-radius: 5px; padding: 4px 6px; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{ border-color: {PRIMARY}; }}
QStatusBar {{ background: white; border-top: 1px solid {BORDER}; }}
QToolTip {{ background: #FFFFE8; color: {TEXT}; border: 1px solid {BORDER}; }}
QProgressBar {{ border: 1px solid {BORDER}; border-radius: 5px; background: #EEF1F6; text-align: center;
                height: 14px; }}
QProgressBar::chunk {{ background: {OK}; border-radius: 4px; }}
QScrollArea {{ border: none; background: transparent; }}
"""
