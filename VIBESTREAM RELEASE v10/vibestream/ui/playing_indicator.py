import math
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QWidget


class MiniBarsIndicator(QWidget):
    """Compact 3-bar animated equalizer badge for active track state."""

    def __init__(self, accent: str = "#1DB954", parent=None):
        super().__init__(parent)
        self.accent = QColor(accent)
        self.active = False
        self.phase = 0.0
        self.setFixedSize(22, 16)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(55)

    def set_accent(self, hex_color: str):
        self.accent = QColor(hex_color)
        self.update()

    def set_active(self, active: bool):
        self.active = active
        self.update()

    def _tick(self):
        if self.active:
            self.phase += 0.32
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self.accent))

        w = self.width()
        h = self.height()
        bar_w = 4.0
        gap = 3.0
        start_x = (w - (3 * bar_w + 2 * gap)) / 2.0

        for i in range(3):
            if self.active:
                norm = 0.35 + 0.65 * abs(math.sin(self.phase + i * 1.15))
            else:
                norm = 0.25
            bh = max(3.0, norm * (h - 2))
            x = start_x + i * (bar_w + gap)
            y = h - bh
            p.drawRoundedRect(QRectF(x, y, bar_w, bh), 1.5, 1.5)
