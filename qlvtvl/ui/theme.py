"""Giao diện: bảng màu sáng/tối, màu nhấn và stylesheet."""

ACCENTS = {
    "Đỏ": ("#B3261E", "#8C1D17", "#FCE8E6"),
    "Xanh dương": ("#0B5394", "#083C6B", "#E3EDF8"),
    "Xanh lục": ("#1E7A46", "#155C34", "#E3F3EA"),
}

PRIMARY = PRIMARY_DARK = ACCENT_SOFT = ""
ACCENT = "#C9A227"
BG = CARD = TEXT = MUTED = BORDER = CALC_BG = SIDEBAR = HOVER = ""
OK, WARN, ERR, INFO_C = "#1E7E34", "#B26A00", "#C62828", "#1565C0"
DARK = False
STYLE = ""


def apply_theme(dark: bool = False, accent: str = "Đỏ") -> str:
    """Đặt bảng màu toàn cục và trả về stylesheet."""
    global PRIMARY, PRIMARY_DARK, ACCENT_SOFT, BG, CARD, TEXT, MUTED, BORDER, CALC_BG, SIDEBAR, HOVER
    global OK, WARN, ERR, INFO_C, DARK, STYLE
    DARK = dark
    PRIMARY, PRIMARY_DARK, ACCENT_SOFT = ACCENTS.get(accent, ACCENTS["Đỏ"])
    if dark:
        BG, CARD, TEXT, MUTED, BORDER = "#16181D", "#22252C", "#E8EAED", "#9AA0A6", "#363A43"
        CALC_BG, SIDEBAR, HOVER = "#2A2F38", "#1C1F25", "#2C3038"
        ACCENT_SOFT = "#3A2526" if accent == "Đỏ" else ("#1F2E40" if accent == "Xanh dương" else "#1E3328")
        OK, WARN, ERR, INFO_C = "#5BC27A", "#E0A030", "#F07067", "#7FB2F0"
    else:
        BG, CARD, TEXT, MUTED, BORDER = "#F4F5F9", "#FFFFFF", "#1F2329", "#5F6670", "#E1E4EA"
        CALC_BG, SIDEBAR, HOVER = "#EEF2F8", "#FFFFFF", "#F2F3F6"
        OK, WARN, ERR, INFO_C = "#1E7E34", "#B26A00", "#C62828", "#1565C0"
    head_bg = "#2A2F38" if dark else "#F1F3F7"
    sel_bg = "#3B4250" if dark else "#DCE8FA"
    STYLE = f"""
* {{ font-family: "Segoe UI", "Arial", sans-serif; font-size: 10pt; color: {TEXT}; }}
QMainWindow, QWidget#Page, QStackedWidget {{ background: {BG}; }}
QDialog {{ background: {BG}; }}
QWidget#TopBar {{ background: {CARD}; border-bottom: 1px solid {BORDER}; }}
QLabel#AppTitle {{ font-size: 12.5pt; font-weight: 700; }}
QLabel#AppSub {{ color: {MUTED}; font-size: 9pt; }}
QPushButton#Chip {{ background: {HOVER}; border: 1px solid {BORDER}; border-radius: 15px; padding: 5px 14px;
                    color: {TEXT}; }}
QPushButton#Chip:hover {{ border-color: {PRIMARY}; }}
QPushButton#IconBtn {{ background: transparent; border: none; font-size: 14pt; padding: 4px 8px; border-radius: 8px; }}
QPushButton#IconBtn:hover {{ background: {HOVER}; }}
QLabel#Avatar {{ background: {ACCENT_SOFT}; color: {PRIMARY}; border-radius: 17px; font-weight: 700;
                 min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; }}
QLabel#Badge {{ background: {ERR}; color: white; border-radius: 8px; font-size: 7.5pt; font-weight: 700;
                padding: 0 4px; }}
QWidget#Sidebar {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}
QListWidget#Nav {{ background: transparent; border: none; outline: none; }}
QListWidget#Nav::item {{ padding: 9px 12px; border-radius: 8px; margin: 1px 8px; color: {TEXT}; }}
QListWidget#Nav::item:hover {{ background: {HOVER}; }}
QListWidget#Nav::item:selected {{ background: {ACCENT_SOFT}; color: {PRIMARY}; font-weight: 600; }}
QLabel#Crumb {{ color: {MUTED}; font-size: 9pt; }}
QLabel#PageTitle {{ font-size: 19pt; font-weight: 700; color: {TEXT}; }}
QLabel#PageSub {{ color: {MUTED}; font-size: 10.5pt; }}
QLabel#StepBadge {{ background: {PRIMARY}; color: white; border-radius: 15px; font-weight: 700; font-size: 12pt;
                    min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; }}
QFrame#Card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}
QLabel#CardValue {{ font-size: 22pt; font-weight: 700; color: {TEXT}; }}
QLabel#CardLabel {{ color: {MUTED}; font-size: 9.5pt; }}
QLabel#Note {{ background: {"#2B2A1E" if dark else "#FFF8E1"}; border: 1px solid {"#5A5230" if dark else "#F3DFA2"};
               border-radius: 8px; padding: 8px 12px; color: {TEXT}; }}
QLabel#InfoBanner {{ background: {"#1E2A3A" if dark else "#EAF2FD"}; border: 1px solid {"#2F4A6E" if dark else "#C7DCF7"};
                     border-radius: 10px; padding: 12px 16px; color: {TEXT}; }}
QTextBrowser#Guide {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px 10px; }}
QPushButton {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 14px; }}
QPushButton:hover {{ border-color: {PRIMARY}; color: {PRIMARY}; }}
QPushButton:disabled {{ color: {MUTED}; background: {HOVER}; }}
QPushButton#Primary {{ background: {PRIMARY}; color: white; border: 1px solid {PRIMARY}; font-weight: 600; }}
QPushButton#Primary:hover {{ background: {PRIMARY_DARK}; color: white; }}
QPushButton#Primary:disabled {{ background: {BORDER}; border-color: {BORDER}; color: {MUTED}; }}
QPushButton#Danger:hover {{ border-color: {ERR}; color: {ERR}; }}
QPushButton#Link {{ border: none; background: transparent; color: {PRIMARY}; text-align: left; padding: 2px;
                    font-weight: 600; }}
QPushButton#Link:hover {{ text-decoration: underline; }}
QTableView, QTableWidget {{ background: {CARD}; gridline-color: {BORDER}; border: 1px solid {BORDER};
                            border-radius: 8px; selection-background-color: {sel_bg}; selection-color: {TEXT};
                            alternate-background-color: {"#262A31" if dark else "#FAFBFC"}; }}
QHeaderView::section {{ background: {head_bg}; color: {TEXT}; font-weight: 600; padding: 7px 5px; border: none;
                        border-right: 1px solid {BORDER}; border-bottom: 1px solid {BORDER}; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: {HOVER}; padding: 8px 16px; margin: 0 4px 4px 0; border: 1px solid {BORDER};
                border-radius: 10px; color: {MUTED}; }}
QTabBar::tab:selected {{ background: {CARD}; color: {TEXT}; font-weight: 600; border: 2px solid {PRIMARY}; }}
QLineEdit, QComboBox, QPlainTextEdit, QDoubleSpinBox, QSpinBox, QTextEdit {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 6px; padding: 5px 7px; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{ border-color: {PRIMARY}; }}
QComboBox QAbstractItemView {{ background: {CARD}; }}
QStatusBar {{ background: {CARD}; border-top: 1px solid {BORDER}; }}
QMenuBar {{ background: {CARD}; }}
QMenu {{ background: {CARD}; border: 1px solid {BORDER}; }}
QMenu::item:selected {{ background: {ACCENT_SOFT}; color: {PRIMARY}; }}
QToolTip {{ background: {CARD}; color: {TEXT}; border: 1px solid {BORDER}; }}
QScrollArea {{ border: none; background: transparent; }}
QWidget#ScrollBody {{ background: {BG}; }}
QCheckBox, QRadioButton {{ spacing: 6px; }}
QFrame#DropZone {{ background: {CARD}; border: 2px dashed {BORDER}; border-radius: 14px; }}
QFrame#DropZone[hover="true"] {{ border-color: {PRIMARY}; background: {ACCENT_SOFT}; }}
"""
    return STYLE


apply_theme(False, "Đỏ")
