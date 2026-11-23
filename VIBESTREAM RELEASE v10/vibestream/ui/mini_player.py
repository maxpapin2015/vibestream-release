from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QPixmap, QColor, QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QGraphicsDropShadowEffect,
)
from vibestream.ui.icons import make_icon


def fmt_time(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


class FloatingMiniPlayer(QWidget):
    """
    Frameless floating mini-window in the bottom-right corner when closing/minimizing
    the main app. Shows track icon/cover, title, artist, exact timer/seconds,
    seek slider, Prev / Play-Pause / Next, Like heart, Loop-1-track toggle,
    Expand back to main window, and Exit.
    """

    play_pause_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    like_clicked = pyqtSignal()
    loop_one_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int)
    restore_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, accent: str = "#1DB954", parent=None):
        super().__init__(parent)
        self.accent = accent
        self._drag_pos: QPoint | None = None
        self._seeking = False
        self._loop_one = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(412, 126)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        self.card = QWidget(self)
        self.card.setObjectName("MiniCard")
        self.card.setStyleSheet(
            f"""
            QWidget#MiniCard {{
                background-color: rgba(14, 14, 18, 250);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 16px;
            }}
            QLabel {{
                color: #F4F4F6;
                background: transparent;
                font-family: "Inter", "Segoe UI", Arial, sans-serif;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.10);
            }}
            QPushButton#MiniPlayBtn {{
                background-color: {self.accent};
                border-radius: 16px;
            }}
            QPushButton#MiniPlayBtn:hover {{
                background-color: #1ED760;
            }}
            QPushButton#MiniLoopBtn {{
                color: #9A9AA6;
                font-size: 10px;
                font-weight: 800;
                padding: 2px 6px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.10);
            }}
            QPushButton#MiniLoopBtn[active="true"] {{
                color: #070709;
                background-color: {self.accent};
                border-color: {self.accent};
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: #2C2C36;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.accent};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: #FFFFFF;
                width: 10px;
                height: 10px;
                margin: -3px 0;
                border-radius: 5px;
            }}
            """
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 220))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(7)

        top_row = QHBoxLayout()
        top_row.setSpacing(9)

        self.cover_lbl = QLabel()
        self.cover_lbl.setFixedSize(48, 48)
        self.cover_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_lbl.setStyleSheet("background-color: #1C1C24; border-radius: 8px;")
        self.cover_lbl.setPixmap(make_icon("disc", 32, self.accent))
        top_row.addWidget(self.cover_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        self.title_lbl = QLabel("No Track Selected")
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
        self.artist_lbl = QLabel("VIBESTREAM RELEASE")
        self.artist_lbl.setStyleSheet("font-size: 11px; color: #9A9AA6;")
        info_col.addWidget(self.title_lbl)
        info_col.addWidget(self.artist_lbl)
        top_row.addLayout(info_col, 1)

        self.like_btn = QPushButton()
        self.like_btn.setFixedSize(26, 26)
        self.like_btn.setIconSize(QSize(15, 15))
        self.like_btn.setToolTip("Like / Unlike")
        self.like_btn.setIcon(QIcon(make_icon("heart_outline", 15, "#9A9AA6")))
        self.like_btn.clicked.connect(self.like_clicked.emit)
        top_row.addWidget(self.like_btn)

        self.loop_btn = QPushButton("1x LOOP")
        self.loop_btn.setObjectName("MiniLoopBtn")
        self.loop_btn.setProperty("active", "false")
        self.loop_btn.setFixedHeight(24)
        self.loop_btn.setToolTip("Repeat current song continuously")
        self.loop_btn.clicked.connect(self.loop_one_clicked.emit)
        top_row.addWidget(self.loop_btn)

        self.prev_btn = QPushButton()
        self.prev_btn.setFixedSize(26, 26)
        self.prev_btn.setIconSize(QSize(15, 15))
        self.prev_btn.setToolTip("Previous track")
        self.prev_btn.setIcon(QIcon(make_icon("prev", 15, "#E4E4EA")))
        self.prev_btn.clicked.connect(self.prev_clicked.emit)
        top_row.addWidget(self.prev_btn)

        self.play_btn = QPushButton()
        self.play_btn.setObjectName("MiniPlayBtn")
        self.play_btn.setFixedSize(30, 30)
        self.play_btn.setIconSize(QSize(15, 15))
        self.play_btn.setToolTip("Play / Pause")
        self.play_btn.setIcon(QIcon(make_icon("play", 15, "#070709")))
        self.play_btn.clicked.connect(self.play_pause_clicked.emit)
        top_row.addWidget(self.play_btn)

        self.next_btn = QPushButton()
        self.next_btn.setFixedSize(26, 26)
        self.next_btn.setIconSize(QSize(15, 15))
        self.next_btn.setToolTip("Next track")
        self.next_btn.setIcon(QIcon(make_icon("next", 15, "#E4E4EA")))
        self.next_btn.clicked.connect(self.next_clicked.emit)
        top_row.addWidget(self.next_btn)

        self.expand_btn = QPushButton()
        self.expand_btn.setFixedSize(26, 26)
        self.expand_btn.setIconSize(QSize(15, 15))
        self.expand_btn.setToolTip("Open full window")
        self.expand_btn.setIcon(QIcon(make_icon("expand", 15, "#9A9AA6")))
        self.expand_btn.clicked.connect(self.restore_requested.emit)
        top_row.addWidget(self.expand_btn)

        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setToolTip("Exit VIBESTREAM RELEASE")
        self.close_btn.setStyleSheet("color: #787886; font-size: 11px; font-weight: 800;")
        self.close_btn.clicked.connect(self.quit_requested.emit)
        top_row.addWidget(self.close_btn)

        card_layout.addLayout(top_row)

        prog_row = QHBoxLayout()
        prog_row.setSpacing(8)

        self.elapsed_lbl = QLabel("0:00 (0s)")
        self.elapsed_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {self.accent};")
        prog_row.addWidget(self.elapsed_lbl)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self.slider.sliderReleased.connect(self._on_seek_release)
        prog_row.addWidget(self.slider, 1)

        self.total_lbl = QLabel("0:00")
        self.total_lbl.setStyleSheet("font-size: 11px; color: #787886;")
        prog_row.addWidget(self.total_lbl)

        card_layout.addLayout(prog_row)
        root.addWidget(self.card)

    def set_accent(self, accent: str):
        self.accent = accent
        self.elapsed_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {self.accent};")
        self.play_btn.setStyleSheet(
            f"QPushButton#MiniPlayBtn {{ background-color: {self.accent}; border-radius: 16px; }}"
            f"QPushButton#MiniPlayBtn:hover {{ background-color: #1ED760; }}"
        )
        self.set_loop_one(self._loop_one)

    def set_loop_one(self, active: bool):
        self._loop_one = bool(active)
        self.loop_btn.setProperty("active", "true" if active else "false")
        if active:
            self.loop_btn.setStyleSheet(
                f"color: #070709; background-color: {self.accent}; border: 1px solid {self.accent}; "
                "font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 8px;"
            )
        else:
            self.loop_btn.setStyleSheet(
                "color: #9A9AA6; background: transparent; border: 1px solid rgba(255,255,255,0.10); "
                "font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 8px;"
            )

    def _on_seek_release(self):
        self._seeking = False
        self.seek_requested.emit(self.slider.value())

    def snap_to_bottom_right(self):
        screen = self.screen().availableGeometry()
        x = screen.right() - self.width() - 16
        y = screen.bottom() - self.height() - 16
        self.move(x, y)

    def update_track(self, title: str, artist: str, cover_pixmap: QPixmap | None, is_liked: bool):
        short_title = title if len(title) <= 22 else title[:20] + "..."
        short_artist = artist if len(artist) <= 26 else artist[:24] + "..."
        self.title_lbl.setText(short_title)
        self.title_lbl.setToolTip(title)
        self.artist_lbl.setText(short_artist)
        self.set_liked(is_liked)
        if cover_pixmap and not cover_pixmap.isNull():
            scaled = cover_pixmap.scaled(
                48, 48, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
            )
            self.cover_lbl.setPixmap(scaled)
        else:
            self.cover_lbl.setPixmap(make_icon("disc", 32, self.accent))

    def set_liked(self, liked: bool):
        if liked:
            self.like_btn.setIcon(QIcon(make_icon("heart_filled", 15, self.accent)))
        else:
            self.like_btn.setIcon(QIcon(make_icon("heart_outline", 15, "#9A9AA6")))

    def set_playing(self, playing: bool):
        if playing:
            self.play_btn.setIcon(QIcon(make_icon("pause", 15, "#070709")))
        else:
            self.play_btn.setIcon(QIcon(make_icon("play", 15, "#070709")))

    def update_position(self, pos_sec: int, dur_sec: int):
        self.elapsed_lbl.setText(f"{fmt_time(pos_sec)} ({pos_sec}s)")
        self.total_lbl.setText(fmt_time(dur_sec))
        if not self._seeking:
            self.slider.setMaximum(max(1, dur_sec))
            self.slider.setValue(min(pos_sec, max(1, dur_sec)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self.restore_requested.emit()
