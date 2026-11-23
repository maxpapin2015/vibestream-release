import math
import random
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush
from PyQt6.QtWidgets import QWidget


class SpectrumVisualizer(QWidget):
    """Smooth 32-bar animated Spotify-green audio spectrum visualizer."""

    def __init__(self, bars: int = 32, accent_color: str = "#1DB954", parent=None):
        super().__init__(parent)
        self.num_bars = bars
        self.accent = QColor(accent_color)
        self.levels = [0.08] * bars
        self.targets = [0.08] * bars
        self.is_playing = False
        self.phase = 0.0

        self.setMinimumHeight(56)
        self.setMaximumHeight(72)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(35)

    def set_accent(self, hex_color: str):
        self.accent = QColor(hex_color)
        self.update()

    def set_playing(self, playing: bool):
        self.is_playing = playing

    def _tick(self):
        self.phase += 0.18
        for i in range(self.num_bars):
            if self.is_playing:
                # Harmonic wave + organic energy distribution (stronger bass on left, mids center, highs right)
                bass_boost = math.exp(-((i - 4) ** 2) / 18.0) * 0.45
                mid_boost = math.exp(-((i - 15) ** 2) / 35.0) * 0.35
                wave = abs(math.sin(self.phase + i * 0.35)) * 0.45
                jitter = random.uniform(0.05, 0.32)
                self.targets[i] = min(1.0, max(0.1, bass_boost + mid_boost + wave * 0.6 + jitter))
            else:
                self.targets[i] = 0.06

            # Smooth interpolation
            self.levels[i] += (self.targets[i] - self.levels[i]) * 0.28

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        gap = 3
        bar_w = max(3.0, (w - (self.num_bars - 1) * gap) / self.num_bars)

        grad = QLinearGradient(0, h, 0, 0)
        c_bottom = QColor(self.accent)
        c_bottom.setAlpha(140)
        c_top = QColor(self.accent).lighter(135)
        grad.setColorAt(0.0, c_bottom)
        grad.setColorAt(1.0, c_top)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)

        for i, val in enumerate(self.levels):
            bh = max(4.0, val * (h - 6))
            x = i * (bar_w + gap)
            y = h - bh
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bh), 2, 2)
