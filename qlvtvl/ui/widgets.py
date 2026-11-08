"""Thành phần giao diện dùng chung."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from . import theme


class PageHeader(QWidget):
    """Đường dẫn (breadcrumb) + tiêu đề lớn + mô tả + vùng nút bên phải."""

    def __init__(self, crumb: str, title: str, sub: str = "", parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        v = QVBoxLayout()
        v.setSpacing(4)
        self.crumb = QLabel(crumb)
        self.crumb.setObjectName("Crumb")
        self.title = QLabel(title)
        self.title.setObjectName("PageTitle")
        self.sub = QLabel(sub)
        self.sub.setObjectName("PageSub")
        self.sub.setWordWrap(True)
        self.sub.setTextFormat(Qt.RichText)
        v.addWidget(self.crumb)
        v.addWidget(self.title)
        if sub:
            v.addWidget(self.sub)
        h.addLayout(v, 1)
        self.right = QHBoxLayout()
        h.addLayout(self.right)

    def add_button(self, btn):
        self.right.addWidget(btn, 0, Qt.AlignBottom)
        return btn


class Stepper(QFrame):
    """Thanh tiến trình nhiều bước: ✓ (xong), số (đang làm / chưa làm); bước hiện tại gạch chân màu nhấn."""
    clicked = Signal(int)

    def __init__(self, steps, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.steps = steps  # [(tiêu đề, mô tả)]
        self.current = 0
        self.done = set()
        self.setMinimumHeight(78)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_state(self, current: int, done=None):
        self.current = current
        self.done = set(done or range(current))
        self.update()

    def mousePressEvent(self, e):
        w = self.width() / len(self.steps)
        i = int(e.position().x() // w)
        if 0 <= i < len(self.steps):
            self.clicked.emit(i)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        n = len(self.steps)
        w = self.width() / n
        h = self.height()
        for i, (title, desc) in enumerate(self.steps):
            x0 = i * w
            if i:
                p.setPen(QPen(QColor(theme.BORDER), 1))
                p.drawLine(int(x0), 10, int(x0), h - 10)
            cx, cy, r = x0 + 34, h / 2, 15
            if i in self.done:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(theme.OK))
                p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))
                p.setPen(QPen(QColor("white"), 2.4))
                p.drawPolyline([QPointF(cx - 6, cy), QPointF(cx - 1.5, cy + 5), QPointF(cx + 7, cy - 5)])
            else:
                active = i == self.current
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(theme.PRIMARY if active else theme.HOVER))
                p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))
                f = QFont(self.font())
                f.setBold(True)
                p.setFont(f)
                p.setPen(QColor("white" if active else theme.MUTED))
                p.drawText(QRectF(cx - r, cy - r, 2 * r, 2 * r), Qt.AlignCenter, str(i + 1))
            f = QFont(self.font())
            f.setBold(i == self.current)
            f.setPointSizeF(10.5)
            p.setFont(f)
            p.setPen(QColor(theme.TEXT))
            p.drawText(QRectF(cx + 26, cy - 20, w - 70, 20), Qt.AlignLeft | Qt.AlignVCenter, title)
            f.setBold(False)
            f.setPointSizeF(9)
            p.setFont(f)
            p.setPen(QColor(theme.MUTED))
            p.drawText(QRectF(cx + 26, cy + 1, w - 70, 20), Qt.AlignLeft | Qt.AlignVCenter, desc)
            if i == self.current:
                p.fillRect(QRectF(x0 + 2, h - 4, w - 4, 4), QColor(theme.PRIMARY))


class KpiCard(QFrame):
    """Thẻ số liệu lớn có viền màu phía trên."""

    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        self.color = color
        self.setObjectName("Card")
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 18, 16, 16)
        self.value = QLabel("0")
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setStyleSheet(f"font-size: 26pt; font-weight: 700; color: {color};")
        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 11pt;")
        v.addWidget(self.value)
        v.addWidget(self.label)
        self.setMinimumHeight(118)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(self.color))
        p.drawRoundedRect(QRectF(0, 0, self.width(), 7), 4, 4)


def chip(text: str, slot=None, tip: str = "") -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("Chip")
    b.setCursor(Qt.PointingHandCursor)
    if tip:
        b.setToolTip(tip)
    if slot:
        b.clicked.connect(slot)
    return b


def icon_button(text: str, tip: str, slot=None) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("IconBtn")
    b.setToolTip(tip)
    b.setCursor(Qt.PointingHandCursor)
    if slot:
        b.clicked.connect(slot)
    return b


def badge_color(text: str) -> str:
    if text in ("Đạt", "Hợp lệ"):
        return theme.OK
    if "lỗi" in text or "Sai" in text:
        return theme.ERR
    if text in ("Xem lại",):
        return theme.WARN
    return theme.MUTED
