from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from vibestream.ui.icons import make_icon


class StarRatingWidget(QWidget):
    rating_changed = pyqtSignal(int)

    def __init__(self, rating: int = 0, accent: str = "#1DB954", star_px: int = 14, parent=None):
        super().__init__(parent)
        self._rating = rating
        self._accent = accent
        self._star_px = star_px
        self._buttons = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        for i in range(1, 6):
            btn = QPushButton()
            btn.setFixedSize(star_px + 4, star_px + 4)
            btn.setIconSize(QSize(star_px, star_px))
            btn.setStyleSheet("background: transparent; border: none; padding: 0px;")
            btn.setToolTip(f"Rate {i} / 5")
            btn.clicked.connect(lambda checked, val=i: self._on_click(val))
            layout.addWidget(btn)
            self._buttons.append(btn)

        self._refresh_icons()

    def _on_click(self, val: int):
        new_val = 0 if val == self._rating else val
        self.set_rating(new_val)
        self.rating_changed.emit(new_val)

    def set_rating(self, rating: int):
        self._rating = max(0, min(5, int(rating)))
        self._refresh_icons()

    def set_accent(self, accent: str):
        self._accent = accent
        self._refresh_icons()

    def _refresh_icons(self):
        for idx, btn in enumerate(self._buttons, start=1):
            if idx <= self._rating:
                btn.setIcon(QIcon(make_icon("star_filled", self._star_px, self._accent)))
            else:
                btn.setIcon(QIcon(make_icon("star_outline", self._star_px, "#52525B")))
