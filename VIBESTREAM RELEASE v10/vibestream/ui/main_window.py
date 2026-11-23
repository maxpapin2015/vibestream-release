import random
import threading
import requests
from typing import List, Dict, Any, Optional

from PyQt6.QtCore import Qt, QTimer, QUrl, QSize, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QImage, QIcon, QAction, QColor, QKeySequence, QShortcut
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QInputDialog,
    QFileDialog,
    QMessageBox,
    QSystemTrayIcon,
    QMenu,
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
)

from vibestream.core.storage import StorageManager
from vibestream.core.music_provider import MusicProvider
from vibestream.ui.styles import get_spotify_stylesheet
from vibestream.ui.visualizer import SpectrumVisualizer
from vibestream.ui.mini_player import FloatingMiniPlayer, fmt_time
from vibestream.ui.icons import make_icon
from vibestream.ui.star_rating import StarRatingWidget
from vibestream.ui.playing_indicator import MiniBarsIndicator


class WorkerSignals(QObject):
    tracks_loaded = pyqtSignal(list, str, str)
    stream_resolved = pyqtSignal(dict, str)
    cover_loaded = pyqtSignal(str, QPixmap)
    lyrics_loaded = pyqtSignal(str, dict)
    download_finished = pyqtSignal(str, bool)


class VibeStreamWindow(QMainWindow):
    """
    Refined Spotify-grade desktop music player with zero emoji clutter,
    full Like + 1..5 Star Rating system, ambient hero header, synced lyrics,
    10-band equalizer, live spectrum visualizer, and bottom-right mini-player.
    """

    EQ_PRESETS = {
        "Flat (Default)": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "Bass Boost": [8, 7, 5, 2, 0, 0, 1, 2, 3, 4],
        "Electronic / Club": [6, 5, 2, 0, -2, 2, 4, 5, 6, 7],
        "Pop / Hits": [-1, 2, 4, 5, 3, 0, -1, 1, 3, 4],
        "Rock / Metal": [5, 4, 2, -1, -2, 1, 3, 5, 6, 6],
        "Vocal / Studio": [-3, -2, 0, 3, 6, 6, 4, 1, -1, -2],
        "Night Lounge": [3, 2, 0, 0, 0, -1, -2, -3, -4, -5],
    }

    ACCENT_THEMES = {
        "Spotify Green": ("#1DB954", "#1ED760"),
        "Cyber Violet": ("#9B51E0", "#B47AEA"),
        "Electric Cyan": ("#00D2FF", "#4CE0FF"),
        "Sunset Coral": ("#FF5E62", "#FF7B7E"),
        "Gold Luxury": ("#F5A623", "#FFB84D"),
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VIBESTREAM RELEASE")
        self.resize(1380, 860)
        self.setMinimumSize(1060, 700)

        self.storage = StorageManager()
        self.provider = MusicProvider()
        self.signals = WorkerSignals()

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        vol = self.storage.data["settings"].get("volume", 80)
        self.audio_output.setVolume(vol / 100.0)

        self.queue: List[Dict[str, Any]] = []
        self.current_index: int = -1
        self.current_track: Optional[Dict[str, Any]] = None
        self.current_cover: Optional[QPixmap] = None
        self.current_lyrics: Dict[str, Any] = {"synced": [], "plain": ""}
        self._cover_cache: Dict[str, QPixmap] = {}
        self._displayed_tracks: List[Dict[str, Any]] = []
        self._seeking = False
        self._sleep_seconds_left = 0

        accent = self.storage.data["settings"].get("theme_accent", "#1DB954")
        self.accent = accent

        self.mini_player = FloatingMiniPlayer(accent=accent)
        self._connect_mini_player()

        self.setStyleSheet(get_spotify_stylesheet(accent))
        self._build_ui()
        self._setup_tray()
        self._setup_shortcuts()
        self._connect_signals()

        self.sec_timer = QTimer(self)
        self.sec_timer.timeout.connect(self._on_one_second_tick)
        self.sec_timer.start(1000)

        self._sync_loop_ui()
        self.load_trending("All")
        self._sync_loop_ui()

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("RootContainer")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(10, 10, 10, 8)
        outer.setSpacing(8)

        workspace = QHBoxLayout()
        workspace.setSpacing(8)

        workspace.addWidget(self._build_sidebar(), 0)
        workspace.addWidget(self._build_center_panel(), 1)
        workspace.addWidget(self._build_right_panel(), 0)

        outer.addLayout(workspace, 1)
        outer.addWidget(self._build_bottom_player(), 0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(6)

        brand_row = QHBoxLayout()
        brand_dot = QLabel()
        brand_dot.setFixedSize(12, 12)
        brand_dot.setStyleSheet(f"background-color: {self.accent}; border-radius: 6px;")
        brand_lbl = QLabel("VIBESTREAM")
        brand_lbl.setStyleSheet("font-size: 16px; font-weight: 900; letter-spacing: 1.5px; color: #FFFFFF;")
        tier_lbl = QLabel("AD-FREE")
        tier_lbl.setStyleSheet(
            f"background-color: rgba(29, 185, 84, 0.16); color: {self.accent}; "
            "font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 6px; letter-spacing: 0.6px;"
        )
        brand_row.addWidget(brand_dot)
        brand_row.addWidget(brand_lbl)
        brand_row.addStretch()
        brand_row.addWidget(tier_lbl)
        layout.addLayout(brand_row)
        layout.addSpacing(8)

        nav_defs = [
            ("home", "Home & Charts", "home"),
            ("search", "Search Catalog", "search"),
            ("liked", "Liked Songs", "heart_filled"),
            ("rated", "Top Rated (Stars)", "star_filled"),
            ("offline", "Offline Cache", "download"),
            ("local", "Local Files", "disc"),
            ("history", "History & Stats", "repeat"),
        ]
        self.nav_buttons: Dict[str, QPushButton] = {}
        for key, text, icon_name in nav_defs:
            btn = QPushButton(f"  {text}")
            btn.setProperty("class", "NavBtn")
            btn.setIcon(QIcon(make_icon(icon_name, 16, "#A1A1AA")))
            btn.setIconSize(QSize(16, 16))
            if key == "home":
                btn.setProperty("active", "true")
            btn.clicked.connect(lambda checked, k=key: self._switch_view(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn

        divider = QFrame()
        divider.setStyleSheet("background-color: #202028; max-height: 1px; margin: 6px 2px;")
        layout.addWidget(divider)

        pl_head = QHBoxLayout()
        pl_title = QLabel("PLAYLISTS")
        pl_title.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 800; letter-spacing: 0.9px;")
        add_pl_btn = QPushButton()
        add_pl_btn.setFixedSize(26, 26)
        add_pl_btn.setIcon(QIcon(make_icon("plus", 14, "#E4E4E7")))
        add_pl_btn.setIconSize(QSize(14, 14))
        add_pl_btn.setToolTip("Create playlist")
        add_pl_btn.setStyleSheet(
            "background-color: #1C1C24; border: 1px solid #2C2C38; border-radius: 13px;"
        )
        add_pl_btn.clicked.connect(self._create_playlist_dialog)
        pl_head.addWidget(pl_title)
        pl_head.addStretch()
        pl_head.addWidget(add_pl_btn)
        layout.addLayout(pl_head)

        self.playlist_list = QListWidget()
        self.playlist_list.setObjectName("PlaylistList")
        self.playlist_list.itemClicked.connect(self._on_playlist_selected)
        self._refresh_playlist_sidebar()
        layout.addWidget(self.playlist_list, 1)

        mini_btn = QPushButton("  Corner Mini-Widget")
        mini_btn.setProperty("class", "SecondaryBtn")
        mini_btn.setIcon(QIcon(make_icon("mini", 15, "#E4E4E7")))
        mini_btn.setIconSize(QSize(15, 15))
        mini_btn.setToolTip("Minimize to bottom-right corner mini-player (Ctrl+M)")
        mini_btn.clicked.connect(self.activate_mini_mode)
        layout.addWidget(mini_btn)

        theme_row = QHBoxLayout()
        theme_lbl = QLabel("ACCENT")
        theme_lbl.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(self.ACCENT_THEMES.keys()))
        self.theme_combo.setStyleSheet(
            "background-color: #1C1C22; color: #F4F4F5; border: 1px solid #2C2C38; border-radius: 8px; padding: 5px 8px;"
        )
        self.theme_combo.currentTextChanged.connect(self._change_accent_theme)
        theme_row.addWidget(theme_lbl)
        theme_row.addWidget(self.theme_combo, 1)
        layout.addLayout(theme_row)

        return sidebar

    def _build_center_panel(self) -> QWidget:
        center = QWidget()
        center.setObjectName("MainContent")

        layout = QVBoxLayout(center)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)

        # Search & Utility Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search artists, tracks, genres, moods...")
        self.search_input.returnPressed.connect(self._on_search_submitted)
        top_bar.addWidget(self.search_input, 1)

        search_btn = QPushButton("SEARCH")
        search_btn.setProperty("class", "PrimaryAccentBtn")
        search_btn.clicked.connect(self._on_search_submitted)
        top_bar.addWidget(search_btn)

        self.sleep_btn = QPushButton("SLEEP TIMER")
        self.sleep_btn.setProperty("class", "SecondaryBtn")
        self.sleep_btn.clicked.connect(self._configure_sleep_timer)
        top_bar.addWidget(self.sleep_btn)

        layout.addLayout(top_bar)

        # Genre Filter Chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        genres = [
            ("All Charts", "All"),
            ("Electronic", "Electronic"),
            ("Hip-Hop", "Hip-Hop/Rap"),
            ("Rock", "Rock"),
            ("Pop", "Pop"),
            ("Ambient / Chill", "Ambient"),
            ("Russian Hits", "QUERY:Русские хиты 2026"),
            ("Phonk / Drift", "QUERY:Phonk drift"),
        ]
        self.chip_buttons: List[QPushButton] = []
        for idx, (label, code) in enumerate(genres):
            btn = QPushButton(label)
            btn.setProperty("class", "ChipBtn")
            if idx == 0:
                btn.setProperty("active", "true")
            btn.clicked.connect(lambda checked, c=code, b=btn: self._on_chip_clicked(c, b))
            chips_row.addWidget(btn)
            self.chip_buttons.append(btn)
        chips_row.addStretch()
        layout.addLayout(chips_row)

        # Hero Banner Card
        self.hero_banner = QFrame()
        hero = self.hero_banner
        hero.setObjectName("HeroBanner")
        hero_l = QHBoxLayout(hero)
        hero_l.setContentsMargins(20, 16, 20, 16)
        hero_l.setSpacing(16)

        hero_txt = QVBoxLayout()
        hero_txt.setSpacing(4)
        self.hero_kicker = QLabel("CURATED STREAMING CATALOG")
        self.hero_kicker.setStyleSheet(f"color: {self.accent}; font-size: 10px; font-weight: 800; letter-spacing: 1.2px;")
        self.view_title_lbl = QLabel("Trending Now")
        self.view_title_lbl.setStyleSheet("font-size: 24px; font-weight: 900; color: #FFFFFF; letter-spacing: -0.4px;")
        self.view_sub_lbl = QLabel("Unlimited free playback • Zero ads • Like & rate any track")
        self.view_sub_lbl.setStyleSheet("font-size: 12px; color: #A1A1AA;")
        hero_txt.addWidget(self.hero_kicker)
        hero_txt.addWidget(self.view_title_lbl)
        hero_txt.addWidget(self.view_sub_lbl)
        hero_l.addLayout(hero_txt, 1)

        self.scan_folder_btn = QPushButton("ADD FOLDER")
        self.scan_folder_btn.setProperty("class", "SecondaryBtn")
        self.scan_folder_btn.hide()
        self.scan_folder_btn.clicked.connect(self._add_local_folder)
        hero_l.addWidget(self.scan_folder_btn)

        self.play_all_btn = QPushButton("PLAY ALL")
        self.play_all_btn.setProperty("class", "PrimaryAccentBtn")
        self.play_all_btn.clicked.connect(self._play_all_current_table)
        hero_l.addWidget(self.play_all_btn)

        layout.addWidget(hero)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color: {self.accent}; font-size: 12px; font-weight: 700;")
        self.status_lbl.hide()
        layout.addWidget(self.status_lbl)

        # Track Table with Likes + 5-Star Rating + Actions
        self.track_table = QTableWidget(0, 7)
        self.track_table.setObjectName("TrackTable")
        self.track_table.setHorizontalHeaderLabels(
            ["#", "TITLE", "ARTIST", "RATING", "SOURCE", "TIME", "ACTIONS"]
        )
        self.track_table.verticalHeader().setVisible(False)
        self.track_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.track_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.track_table.setShowGrid(False)
        self.track_table.setAlternatingRowColors(True)

        header = self.track_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.track_table.setColumnWidth(0, 40)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.track_table.setColumnWidth(3, 105)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.track_table.setColumnWidth(4, 95)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.track_table.setColumnWidth(5, 58)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.track_table.setColumnWidth(6, 104)

        self.track_table.cellDoubleClicked.connect(self._on_table_double_click)
        layout.addWidget(self.track_table, 1)

        return center

    def _build_right_panel(self) -> QWidget:
        right = QWidget()
        right.setObjectName("RightPanel")
        right.setFixedWidth(316)

        layout = QVBoxLayout(right)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        tab_row = QHBoxLayout()
        tab_row.setSpacing(6)
        self.tab_now_btn = QPushButton("Now Playing")
        self.tab_now_btn.setProperty("active", "true")
        self.tab_lyrics_btn = QPushButton("Lyrics")
        self.tab_eq_btn = QPushButton("Equalizer")

        self.right_tabs = [self.tab_now_btn, self.tab_lyrics_btn, self.tab_eq_btn]
        for idx, btn in enumerate(self.right_tabs):
            btn.setProperty("class", "ChipBtn")
            btn.clicked.connect(lambda checked, i=idx: self._switch_right_tab(i))
            tab_row.addWidget(btn)
        layout.addLayout(tab_row)

        self.right_stack = QStackedWidget()

        # Tab 0: Cover + Title + Like/Stars + Visualizer + Queue
        now_page = QWidget()
        now_l = QVBoxLayout(now_page)
        now_l.setContentsMargins(0, 4, 0, 0)
        now_l.setSpacing(10)

        self.big_cover_lbl = QLabel()
        self.big_cover_lbl.setFixedSize(286, 250)
        self.big_cover_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.big_cover_lbl.setStyleSheet("background-color: #18181F; border-radius: 12px;")
        self.big_cover_lbl.setPixmap(make_icon("disc", 84, self.accent))
        now_l.addWidget(self.big_cover_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        cover_glow = QGraphicsDropShadowEffect(self.big_cover_lbl)
        cover_glow.setBlurRadius(28)
        cover_glow.setOffset(0, 8)
        cover_glow.setColor(QColor(0, 0, 0, 220))
        self.big_cover_lbl.setGraphicsEffect(cover_glow)

        meta_row = QHBoxLayout()
        meta_txt = QVBoxLayout()
        meta_txt.setSpacing(2)
        self.np_title_lbl = QLabel("No Track Selected")
        self.np_title_lbl.setWordWrap(True)
        self.np_title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #FFFFFF;")
        self.np_artist_lbl = QLabel("Double-click any song to start")
        self.np_artist_lbl.setStyleSheet("font-size: 12px; color: #A1A1AA;")
        meta_txt.addWidget(self.np_title_lbl)
        meta_txt.addWidget(self.np_artist_lbl)
        meta_row.addLayout(meta_txt, 1)

        self.np_like_btn = QPushButton()
        self.np_like_btn.setFixedSize(36, 36)
        self.np_like_btn.setIconSize(QSize(20, 20))
        self.np_like_btn.setToolTip("Like track")
        self.np_like_btn.setStyleSheet("background-color: #1C1C24; border-radius: 18px;")
        self.np_like_btn.setIcon(QIcon(make_icon("heart_outline", 20, "#A1A1AA")))
        self.np_like_btn.clicked.connect(self._toggle_like_current)
        meta_row.addWidget(self.np_like_btn)
        now_l.addLayout(meta_row)

        rating_row = QHBoxLayout()
        rating_lbl = QLabel("RATING")
        rating_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #71717A; letter-spacing: 0.8px;")
        self.np_stars = StarRatingWidget(0, self.accent, star_px=16)
        self.np_stars.rating_changed.connect(self._on_current_rating_changed)
        rating_row.addWidget(rating_lbl)
        rating_row.addStretch()
        rating_row.addWidget(self.np_stars)
        now_l.addLayout(rating_row)

        self.visualizer = SpectrumVisualizer(bars=28, accent_color=self.accent)
        now_l.addWidget(self.visualizer)

        tools_row = QHBoxLayout()
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["1.0x", "0.75x", "0.9x", "1.15x", "1.25x", "1.5x"])
        self.speed_combo.setStyleSheet(
            "background-color: #1C1C22; color: #F4F4F5; border: 1px solid #2C2C38; border-radius: 8px; padding: 5px 8px;"
        )
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        tools_row.addWidget(self.speed_combo)

        self.dl_current_btn = QPushButton("SAVE OFFLINE")
        self.dl_current_btn.setProperty("class", "SecondaryBtn")
        self.dl_current_btn.clicked.connect(self._download_current_track)
        tools_row.addWidget(self.dl_current_btn, 1)
        now_l.addLayout(tools_row)

        q_lbl = QLabel("UP NEXT IN QUEUE")
        q_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #71717A; letter-spacing: 0.8px; margin-top: 2px;")
        now_l.addWidget(q_lbl)

        self.queue_list = QListWidget()
        self.queue_list.setObjectName("PlaylistList")
        self.queue_list.itemDoubleClicked.connect(self._on_queue_double_click)
        now_l.addWidget(self.queue_list, 1)

        self.right_stack.addWidget(now_page)

        # Tab 1: Synced Lyrics
        lyrics_page = QWidget()
        lyr_l = QVBoxLayout(lyrics_page)
        lyr_l.setContentsMargins(0, 6, 0, 0)
        lyr_header = QLabel("SYNCHRONIZED LYRICS")
        lyr_header.setStyleSheet("font-size: 11px; font-weight: 800; color: #A1A1AA; letter-spacing: 0.8px;")
        lyr_l.addWidget(lyr_header)

        self.lyrics_view = QTextEdit()
        self.lyrics_view.setReadOnly(True)
        self.lyrics_view.setStyleSheet(
            "background-color: #16161C; color: #E4E4E7; border: 1px solid #24242E; border-radius: 10px; "
            "padding: 12px; font-size: 14px;"
        )
        self.lyrics_view.setPlainText("Play any track to load synchronized lyrics.")
        lyr_l.addWidget(self.lyrics_view, 1)
        self.right_stack.addWidget(lyrics_page)

        # Tab 2: 10-Band Equalizer
        eq_page = QWidget()
        eq_l = QVBoxLayout(eq_page)
        eq_l.setContentsMargins(0, 6, 0, 0)
        eq_l.setSpacing(10)

        eq_title = QLabel("10-BAND EQUALIZER")
        eq_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #A1A1AA; letter-spacing: 0.8px;")
        eq_l.addWidget(eq_title)

        self.eq_preset_combo = QComboBox()
        self.eq_preset_combo.addItems(list(self.EQ_PRESETS.keys()))
        self.eq_preset_combo.setStyleSheet(
            "background-color: #1C1C22; color: #F4F4F5; border: 1px solid #2C2C38; border-radius: 8px; padding: 6px;"
        )
        self.eq_preset_combo.currentTextChanged.connect(self._apply_eq_preset)
        eq_l.addWidget(self.eq_preset_combo)

        bands_row = QHBoxLayout()
        bands_row.setSpacing(4)
        freqs = ["32", "64", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"]
        self.eq_sliders: List[QSlider] = []
        saved_gains = self.storage.data["settings"].get("eq_gains", [0] * 10)
        for i, freq in enumerate(freqs):
            col = QVBoxLayout()
            sl = QSlider(Qt.Orientation.Vertical)
            sl.setRange(-12, 12)
            sl.setValue(saved_gains[i] if i < len(saved_gains) else 0)
            sl.valueChanged.connect(self._save_eq_values)
            lbl = QLabel(freq)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 10px; color: #71717A;")
            col.addWidget(sl, 1, Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(lbl)
            bands_row.addLayout(col)
            self.eq_sliders.append(sl)

        eq_l.addLayout(bands_row, 1)
        self.right_stack.addWidget(eq_page)

        layout.addWidget(self.right_stack, 1)
        return right

    def _switch_right_tab(self, index: int):
        self.right_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.right_tabs):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _build_bottom_player(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("BottomPlayer")
        bar.setFixedHeight(88)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        # Left: Track info + Like button
        left = QHBoxLayout()
        left.setSpacing(12)
        self.bot_cover = QLabel()
        self.bot_cover.setFixedSize(56, 56)
        self.bot_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bot_cover.setStyleSheet("background-color: #1A1A22; border-radius: 8px;")
        self.bot_cover.setPixmap(make_icon("disc", 34, self.accent))
        left.addWidget(self.bot_cover)

        txt_col = QVBoxLayout()
        txt_col.setSpacing(2)
        self.bot_title = QLabel("No Track Selected")
        self.bot_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        self.bot_artist = QLabel("VibeStream")
        self.bot_artist.setStyleSheet("font-size: 12px; color: #A1A1AA;")
        txt_col.addWidget(self.bot_title)
        txt_col.addWidget(self.bot_artist)
        left.addLayout(txt_col)

        self.bot_like_btn = QPushButton()
        self.bot_like_btn.setProperty("class", "PlayerCtrlBtn")
        self.bot_like_btn.setFixedSize(34, 34)
        self.bot_like_btn.setIconSize(QSize(18, 18))
        self.bot_like_btn.setToolTip("Like / Unlike")
        self.bot_like_btn.setIcon(QIcon(make_icon("heart_outline", 18, "#A1A1AA")))
        self.bot_like_btn.clicked.connect(self._toggle_like_current)
        left.addWidget(self.bot_like_btn)

        left_wrap = QWidget()
        left_wrap.setFixedWidth(300)
        left_wrap.setLayout(left)
        layout.addWidget(left_wrap)

        # Center: Transport + Progress
        center = QVBoxLayout()
        center.setSpacing(5)

        btns = QHBoxLayout()
        btns.setSpacing(14)
        btns.addStretch()

        self.shuffle_btn = QPushButton()
        self.shuffle_btn.setProperty("class", "PlayerCtrlBtn")
        self.shuffle_btn.setFixedSize(32, 32)
        self.shuffle_btn.setIconSize(QSize(16, 16))
        self.shuffle_btn.setToolTip("Shuffle")
        self.shuffle_btn.setIcon(QIcon(make_icon("shuffle", 16, "#A1A1AA")))
        self.shuffle_btn.clicked.connect(self._toggle_shuffle)
        btns.addWidget(self.shuffle_btn)

        self.prev_btn = QPushButton()
        self.prev_btn.setProperty("class", "PlayerCtrlBtn")
        self.prev_btn.setFixedSize(34, 34)
        self.prev_btn.setIconSize(QSize(18, 18))
        self.prev_btn.setToolTip("Previous")
        self.prev_btn.setIcon(QIcon(make_icon("prev", 18, "#E4E4E7")))
        self.prev_btn.clicked.connect(self.play_previous)
        btns.addWidget(self.prev_btn)

        self.play_btn = QPushButton()
        self.play_btn.setObjectName("MainPlayBtn")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setIconSize(QSize(18, 18))
        self.play_btn.setToolTip("Play / Pause (Space)")
        self.play_btn.setIcon(QIcon(make_icon("play", 18, "#09090B")))
        self.play_btn.clicked.connect(self.toggle_play_pause)
        btns.addWidget(self.play_btn)

        self.next_btn = QPushButton()
        self.next_btn.setProperty("class", "PlayerCtrlBtn")
        self.next_btn.setFixedSize(34, 34)
        self.next_btn.setIconSize(QSize(18, 18))
        self.next_btn.setToolTip("Next")
        self.next_btn.setIcon(QIcon(make_icon("next", 18, "#E4E4E7")))
        self.next_btn.clicked.connect(self.play_next)
        btns.addWidget(self.next_btn)

        self.repeat_btn = QPushButton()
        self.repeat_btn.setProperty("class", "PlayerCtrlBtn")
        self.repeat_btn.setFixedSize(32, 32)
        self.repeat_btn.setIconSize(QSize(16, 16))
        self.repeat_btn.setToolTip("Repeat")
        self.repeat_btn.setIcon(QIcon(make_icon("repeat", 16, "#A1A1AA")))
        self.repeat_btn.clicked.connect(self._cycle_repeat)
        btns.addWidget(self.repeat_btn)
        self.loop_one_btn = QPushButton("LOOP 1")
        self.loop_one_btn.setProperty("class", "ChipBtn")
        self.loop_one_btn.setFixedHeight(28)
        self.loop_one_btn.setToolTip("Loop current track continuously")
        self.loop_one_btn.clicked.connect(self._toggle_loop_one)
        btns.addWidget(self.loop_one_btn)

        btns.addStretch()
        center.addLayout(btns)

        prog = QHBoxLayout()
        prog.setSpacing(10)
        self.bot_elapsed = QLabel("0:00 (0s)")
        self.bot_elapsed.setStyleSheet("font-size: 11px; color: #A1A1AA;")
        prog.addWidget(self.bot_elapsed)

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self.seek_slider.sliderReleased.connect(self._on_main_seek_release)
        prog.addWidget(self.seek_slider, 1)

        self.bot_total = QLabel("0:00")
        self.bot_total.setStyleSheet("font-size: 11px; color: #71717A;")
        prog.addWidget(self.bot_total)

        center.addLayout(prog)
        layout.addLayout(center, 1)

        # Right: Mini-Player + Volume
        right = QHBoxLayout()
        right.setSpacing(8)
        right.addStretch()

        pop_mini_btn = QPushButton()
        pop_mini_btn.setProperty("class", "PlayerCtrlBtn")
        pop_mini_btn.setFixedSize(34, 34)
        pop_mini_btn.setIconSize(QSize(17, 17))
        pop_mini_btn.setToolTip("Open Corner Mini-Widget (Ctrl+M)")
        pop_mini_btn.setIcon(QIcon(make_icon("mini", 17, "#E4E4E7")))
        pop_mini_btn.clicked.connect(self.activate_mini_mode)
        right.addWidget(pop_mini_btn)

        vol_icon = QLabel()
        vol_icon.setFixedSize(20, 20)
        vol_icon.setPixmap(make_icon("volume", 16, "#A1A1AA"))
        right.addWidget(vol_icon)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.storage.data["settings"].get("volume", 80))
        self.vol_slider.setFixedWidth(105)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)
        right.addWidget(self.vol_slider)

        right_wrap = QWidget()
        right_wrap.setFixedWidth(230)
        right_wrap.setLayout(right)
        layout.addWidget(right_wrap)

        return bar

    # =========================================================================
    # MINI-PLAYER, TRAY, SHORTCUTS
    # =========================================================================

    def _connect_mini_player(self):
        self.mini_player.play_pause_clicked.connect(self.toggle_play_pause)
        self.mini_player.next_clicked.connect(self.play_next)
        self.mini_player.prev_clicked.connect(self.play_previous)
        self.mini_player.like_clicked.connect(self._toggle_like_current)
        self.mini_player.seek_requested.connect(self._seek_to_seconds)
        self.mini_player.restore_requested.connect(self.restore_from_mini_mode)
        self.mini_player.loop_one_clicked.connect(self._toggle_loop_one)
        self.mini_player.quit_requested.connect(self._quit_completely)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                self.mini_player.snap_to_bottom_right()
                self.mini_player.show()
                self.mini_player.raise_()
            elif self.isVisible() and not self.isMinimized():
                self.mini_player.hide()

    def activate_mini_mode(self):
        self.showMinimized()
        self.mini_player.snap_to_bottom_right()
        self.mini_player.show()
        self.mini_player.raise_()

    def restore_from_mini_mode(self):
        self.mini_player.hide()
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon(make_icon("disc", 32, self.accent)))
        self.tray.setToolTip("VIBESTREAM RELEASE")

        menu = QMenu()
        act_show = QAction("Open VibeStream", self)
        act_show.triggered.connect(self.restore_from_mini_mode)
        act_mini = QAction("Corner Mini-Widget", self)
        act_mini.triggered.connect(self.activate_mini_mode)
        act_play = QAction("Play / Pause", self)
        act_play.triggered.connect(self.toggle_play_pause)
        act_next = QAction("Next Track", self)
        act_next.triggered.connect(self.play_next)
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)

        menu.addAction(act_show)
        menu.addAction(act_mini)
        menu.addSeparator()
        menu.addAction(act_play)
        menu.addAction(act_next)
        menu.addSeparator()
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self.restore_from_mini_mode()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )
        self.tray.show()

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self.toggle_play_pause)
        QShortcut(QKeySequence("Ctrl+Right"), self, activated=self.play_next)
        QShortcut(QKeySequence("Ctrl+Left"), self, activated=self.play_previous)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.search_input.setFocus)
        QShortcut(QKeySequence("Ctrl+M"), self, activated=self.activate_mini_mode)

    # =========================================================================
    # SIGNALS & CATALOG LOADING
    # =========================================================================

    def _connect_signals(self):
        self.signals.tracks_loaded.connect(self._on_tracks_loaded)
        self.signals.stream_resolved.connect(self._on_stream_resolved)
        self.signals.cover_loaded.connect(self._on_cover_loaded)
        self.signals.lyrics_loaded.connect(self._on_lyrics_loaded)
        self.signals.download_finished.connect(self._on_download_finished)

        self.player.positionChanged.connect(self._on_player_position_changed)
        self.player.durationChanged.connect(self._on_player_duration_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def _set_loading(self, msg: str):
        if msg:
            self.status_lbl.setText(msg)
            self.status_lbl.show()
        else:
            self.status_lbl.hide()

    def load_trending(self, genre: str = "All"):
        self._set_loading("Loading catalog tracks...")
        threading.Thread(
            target=lambda: self.signals.tracks_loaded.emit(
                self.provider.get_trending(genre=genre),
                "Trending Now" if genre == "All" else f"{genre} Charts",
                "CURATED STREAMING CATALOG",
            ),
            daemon=True,
        ).start()

    def _on_search_submitted(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self._set_loading(f"Searching catalog for '{query}'...")
        threading.Thread(
            target=lambda: self.signals.tracks_loaded.emit(
                self.provider.search_tracks(query, limit=25),
                f"Results for '{query}'",
                "CATALOG SEARCH",
            ),
            daemon=True,
        ).start()

    def _on_chip_clicked(self, code: str, clicked_btn: QPushButton):
        for b in self.chip_buttons:
            b.setProperty("active", "true" if b == clicked_btn else "false")
            b.style().unpolish(b)
            b.style().polish(b)

        if code.startswith("QUERY:"):
            q = code.split(":", 1)[1]
            self.search_input.setText(q)
            self._on_search_submitted()
        else:
            self.load_trending(genre=code)

    def _on_tracks_loaded(self, tracks: List[Dict[str, Any]], header_title: str, kicker: str):
        self._set_loading("")
        self.hero_kicker.setText(kicker)
        self.view_title_lbl.setText(header_title)
        self.view_sub_lbl.setText(f"{len(tracks)} tracks available • Free & ad-free")
        self._populate_track_table(tracks)
        if tracks:
            self.queue = list(tracks)
            self.current_index = 0
            self._refresh_queue_ui()

    def _populate_track_table(self, tracks: List[Dict[str, Any]]):
        self._displayed_tracks = tracks
        self.track_table.setRowCount(0)

        for idx, track in enumerate(tracks):
            row = self.track_table.rowCount()
            self.track_table.insertRow(row)
            self.track_table.setRowHeight(row, 48)

            num_item = QTableWidgetItem(str(idx + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setForeground(QColor("#71717A"))
            self.track_table.setItem(row, 0, num_item)

            title_item = QTableWidgetItem(track.get("title", "Unknown"))
            title_item.setToolTip(track.get("title", ""))
            title_item.setForeground(QColor("#FFFFFF"))
            self.track_table.setItem(row, 1, title_item)

            artist_item = QTableWidgetItem(track.get("artist", "Unknown"))
            artist_item.setForeground(QColor("#A1A1AA"))
            self.track_table.setItem(row, 2, artist_item)

            # Column 3: Interactive 1..5 Star Rating
            tid = track.get("id", "")
            stars_widget = StarRatingWidget(
                self.storage.get_rating(tid), self.accent, star_px=13
            )
            stars_widget.rating_changed.connect(
                lambda r, t_id=tid: self.storage.set_rating(t_id, r)
            )
            self.track_table.setCellWidget(row, 3, stars_widget)

            src_map = {"youtube": "YT Music", "audius": "Audius HQ", "local": "Local"}
            src_label = "Offline" if self.storage.is_downloaded(tid) else src_map.get(track.get("source", ""), "Stream")
            src_item = QTableWidgetItem(src_label)
            src_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            src_item.setForeground(QColor(self.accent if src_label == "Offline" else "#71717A"))
            self.track_table.setItem(row, 4, src_item)

            dur_item = QTableWidgetItem(fmt_time(track.get("duration", 0)))
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dur_item.setForeground(QColor("#A1A1AA"))
            self.track_table.setItem(row, 5, dur_item)

            # Column 6: Like Heart + Add to Playlist + Download
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            liked = self.storage.is_liked(tid)
            like_btn = QPushButton()
            like_btn.setFixedSize(28, 28)
            like_btn.setIconSize(QSize(15, 15))
            like_btn.setToolTip("Like / Unlike")
            like_btn.setStyleSheet("background: transparent; border: none;")
            like_btn.setIcon(
                QIcon(make_icon("heart_filled" if liked else "heart_outline", 15, self.accent if liked else "#A1A1AA"))
            )
            like_btn.clicked.connect(lambda checked, t=track, b=like_btn: self._toggle_row_like(t, b))
            act_layout.addWidget(like_btn)

            pl_btn = QPushButton()
            pl_btn.setFixedSize(28, 28)
            pl_btn.setIconSize(QSize(14, 14))
            pl_btn.setToolTip("Add to playlist")
            pl_btn.setStyleSheet("background: transparent; border: none;")
            pl_btn.setIcon(QIcon(make_icon("plus", 14, "#A1A1AA")))
            pl_btn.clicked.connect(lambda checked, t=track: self._add_track_to_playlist_prompt(t))
            act_layout.addWidget(pl_btn)

            dl_btn = QPushButton()
            dl_btn.setFixedSize(28, 28)
            dl_btn.setIconSize(QSize(14, 14))
            dl_btn.setToolTip("Download for offline")
            dl_btn.setStyleSheet("background: transparent; border: none;")
            dl_btn.setIcon(QIcon(make_icon("download", 14, "#A1A1AA")))
            dl_btn.clicked.connect(lambda checked, t=track: self._start_download(t))
            act_layout.addWidget(dl_btn)

            self.track_table.setCellWidget(row, 6, act_widget)

    # =========================================================================
    # PLAYBACK ENGINE
    # =========================================================================

    def _on_table_double_click(self, row: int, _col: int):
        if row >= len(self._displayed_tracks):
            return
        self.queue = list(self._displayed_tracks)
        self._refresh_queue_ui()
        self.play_at_index(row)

    def _play_all_current_table(self):
        if self._displayed_tracks:
            self.queue = list(self._displayed_tracks)
            self._refresh_queue_ui()
            self.play_at_index(0)

    def _on_queue_double_click(self, item: QListWidgetItem):
        idx = self.queue_list.row(item)
        if 0 <= idx < len(self.queue):
            self.play_at_index(idx)

    def _refresh_queue_ui(self):
        self.queue_list.clear()
        for i, t in enumerate(self.queue):
            prefix = "NOW  " if i == self.current_index else f"{i + 1:02d}   "
            self.queue_list.addItem(f"{prefix}{t.get('title')} — {t.get('artist')}")

    def play_at_index(self, index: int):
        if not self.queue or index < 0 or index >= len(self.queue):
            return
        self.current_index = index
        track = self.queue[index]
        self.current_track = track
        self._refresh_queue_ui()

        tid = track.get("id", "")
        title = track.get("title", "Unknown")
        artist = track.get("artist", "Unknown")
        liked = self.storage.is_liked(tid)
        rating = self.storage.get_rating(tid)

        self.np_title_lbl.setText(title)
        self.np_artist_lbl.setText(artist)
        self.np_stars.set_rating(rating)
        self.bot_title.setText(title if len(title) <= 28 else title[:26] + "...")
        self.bot_artist.setText(artist)
        self._update_like_buttons(liked)

        self.mini_player.update_track(title, artist, None, liked)
        if hasattr(self, "tray"):
            self.tray.setToolTip(f"VibeStream — {title} ({artist})")

        self._set_loading(f"Streaming: {title}...")
        self.storage.add_history(track)

        cover_url = track.get("cover_url", "")
        if cover_url:
            if cover_url in self._cover_cache:
                self._apply_cover_pixmap(self._cover_cache[cover_url])
            else:
                threading.Thread(
                    target=self._fetch_cover_worker, args=(cover_url,), daemon=True
                ).start()
        else:
            self._apply_cover_pixmap(None)

        threading.Thread(
            target=lambda: self.signals.lyrics_loaded.emit(
                tid, self.provider.fetch_lyrics(title, artist)
            ),
            daemon=True,
        ).start()

        offline_path = self.storage.get_offline_path(tid)
        threading.Thread(
            target=lambda: self.signals.stream_resolved.emit(
                track, self.provider.resolve_stream_url(track, offline_path) or ""
            ),
            daemon=True,
        ).start()

    def _on_stream_resolved(self, track: Dict[str, Any], url: str):
        if not self.current_track or track.get("id") != self.current_track.get("id"):
            return
        self._set_loading("")
        if not url:
            self.play_next()
            return

        qurl = QUrl.fromLocalFile(url) if not url.startswith("http") else QUrl(url)
        self.player.setSource(qurl)
        self.player.play()

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            if self.current_track is None and self._displayed_tracks:
                self._play_all_current_table()
            else:
                self.player.play()

    def play_next(self):
        if not self.queue:
            return
        shuffle = self.storage.data["settings"].get("shuffle", False)
        if shuffle and len(self.queue) > 1:
            nxt = random.choice([i for i in range(len(self.queue)) if i != self.current_index])
            self.play_at_index(nxt)
            return

        nxt = self.current_index + 1
        if nxt < len(self.queue):
            self.play_at_index(nxt)
        elif self.storage.data["settings"].get("repeat") == "all":
            self.play_at_index(0)

    def play_previous(self):
        if self.player.position() > 4000:
            self.player.setPosition(0)
            return
        if not self.queue:
            return
        self.play_at_index(max(0, self.current_index - 1))

    def _on_playback_state_changed(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_btn.setIcon(QIcon(make_icon("pause" if playing else "play", 18, "#09090B")))
        self.mini_player.set_playing(playing)
        self.visualizer.set_playing(playing)

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            rep = self.storage.data["settings"].get("repeat", "off")
            if rep == "one":
                self.player.setPosition(0)
                self.player.play()
            else:
                self.play_next()

    def _on_player_position_changed(self, pos_ms: int):
        pos_sec = pos_ms // 1000
        dur_sec = max(1, self.player.duration() // 1000)

        self.bot_elapsed.setText(f"{fmt_time(pos_sec)} ({pos_sec}s)")
        if not self._seeking:
            self.seek_slider.setMaximum(dur_sec)
            self.seek_slider.setValue(min(pos_sec, dur_sec))

        self.mini_player.update_position(pos_sec, dur_sec)
        self._update_synced_lyrics_highlight(pos_ms / 1000.0)

    def _on_player_duration_changed(self, dur_ms: int):
        dur_sec = max(1, dur_ms // 1000)
        self.bot_total.setText(fmt_time(dur_sec))
        self.seek_slider.setMaximum(dur_sec)

    def _on_main_seek_release(self):
        self._seeking = False
        self._seek_to_seconds(self.seek_slider.value())

    def _seek_to_seconds(self, seconds: int):
        self.player.setPosition(int(seconds) * 1000)

    def _on_volume_changed(self, val: int):
        self.audio_output.setVolume(val / 100.0)
        self.storage.data["settings"]["volume"] = val
        self.storage.save()

    def _on_speed_changed(self, text: str):
        try:
            self.player.setPlaybackRate(float(text.replace("x", "")))
        except ValueError:
            pass

    # =========================================================================
    # COVERS & LYRICS
    # =========================================================================

    def _fetch_cover_worker(self, url: str):
        try:
            r = requests.get(url, timeout=6)
            if r.ok:
                img = QImage.fromData(r.content)
                if not img.isNull():
                    self.signals.cover_loaded.emit(url, QPixmap.fromImage(img))
        except Exception:
            pass

    def _on_cover_loaded(self, url: str, pix: QPixmap):
        self._cover_cache[url] = pix
        if self.current_track and self.current_track.get("cover_url") == url:
            self._apply_cover_pixmap(pix)


    def _update_hero_gradient_from_pixmap(self, pix: Optional[QPixmap]):
        if not hasattr(self, "hero_banner"):
            return
        r, g, b = QColor(self.accent).red(), QColor(self.accent).green(), QColor(self.accent).blue()
        if pix and not pix.isNull():
            small = pix.toImage().scaled(24, 24)
            sr = sg = sb = cnt = 0
            for y in range(small.height()):
                for x in range(small.width()):
                    c = QColor(small.pixel(x, y))
                    # Favor vivid non-black/non-white pixels
                    if c.saturation() > 45 and 25 < c.lightness() < 225:
                        sr += c.red()
                        sg += c.green()
                        sb += c.blue()
                        cnt += 1
            if cnt > 0:
                r, g, b = sr // cnt, sg // cnt, sb // cnt

        self.hero_banner.setStyleSheet(
            f"""
            QFrame#HeroBanner {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({r}, {g}, {b}, 0.30),
                    stop:0.55 rgba(24, 24, 32, 0.88),
                    stop:1 rgba(17, 17, 20, 1.0));
                border: 1px solid rgba({r}, {g}, {b}, 0.28);
                border-radius: 12px;
            }}
            """
        )

    def _apply_cover_pixmap(self, pix: Optional[QPixmap]):
        self._update_hero_gradient_from_pixmap(pix)
        self.current_cover = pix
        if pix and not pix.isNull():
            self.big_cover_lbl.setPixmap(
                pix.scaled(
                    286, 250, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                )
            )
            self.bot_cover.setPixmap(
                pix.scaled(
                    56, 56, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            self.big_cover_lbl.setPixmap(make_icon("disc", 84, self.accent))
            self.bot_cover.setPixmap(make_icon("disc", 34, self.accent))

        if self.current_track:
            self.mini_player.update_track(
                self.current_track.get("title", ""),
                self.current_track.get("artist", ""),
                pix,
                self.storage.is_liked(self.current_track.get("id", "")),
            )

    def _on_lyrics_loaded(self, track_id: str, lyrics_data: Dict[str, Any]):
        if not self.current_track or self.current_track.get("id") != track_id:
            return
        self.current_lyrics = lyrics_data
        synced = lyrics_data.get("synced", [])
        plain = lyrics_data.get("plain", "")
        if synced:
            self.lyrics_view.setPlainText("\n".join(line for _, line in synced))
        elif plain:
            self.lyrics_view.setPlainText(plain)
        else:
            self.lyrics_view.setPlainText("No lyrics available for this track.")

    def _update_synced_lyrics_highlight(self, elapsed_sec: float):
        synced = self.current_lyrics.get("synced", [])
        if not synced:
            return
        active_idx = 0
        for i, (ts, _) in enumerate(synced):
            if elapsed_sec >= ts:
                active_idx = i
            else:
                break

        html_lines = []
        for i, (_, text) in enumerate(synced):
            if i == active_idx:
                html_lines.append(
                    f'<p style="color:{self.accent}; font-size:15px; font-weight:800; margin:5px 0;">{text}</p>'
                )
            elif i < active_idx:
                html_lines.append(f'<p style="color:#63636E; margin:3px 0;">{text}</p>')
            else:
                html_lines.append(f'<p style="color:#D4D4D8; margin:3px 0;">{text}</p>')
        self.lyrics_view.setHtml("".join(html_lines))

    # =========================================================================
    # LIKES, RATINGS, LIBRARY, EQUALIZER & SLEEP
    # =========================================================================

    def _switch_view(self, view: str):
        for k, btn in self.nav_buttons.items():
            btn.setProperty("active", "true" if k == view else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.scan_folder_btn.setVisible(view == "local")

        if view == "home":
            self.load_trending("All")
        elif view == "search":
            self.search_input.setFocus()
        elif view == "liked":
            liked = self.storage.data["liked_songs"]
            self.hero_kicker.setText("YOUR FAVORITES")
            self.view_title_lbl.setText("Liked Songs")
            self.view_sub_lbl.setText(f"{len(liked)} liked tracks")
            self._populate_track_table(liked)
        elif view == "rated":
            ratings = self.storage.data.get("ratings", {})
            pool = self.storage.data["liked_songs"] + self.storage.data["history"]
            seen = set()
            rated_tracks = []
            for t in pool:
                tid = t.get("id", "")
                if tid not in seen and ratings.get(tid, 0) >= 1:
                    seen.add(tid)
                    rated_tracks.append(t)
            rated_tracks.sort(key=lambda t: ratings.get(t.get("id", ""), 0), reverse=True)
            self.hero_kicker.setText("STARRED COLLECTION")
            self.view_title_lbl.setText("Rated Tracks")
            self.view_sub_lbl.setText(f"{len(rated_tracks)} rated tracks")
            self._populate_track_table(rated_tracks)
        elif view == "offline":
            pool = self.storage.data["liked_songs"] + self.storage.data["history"]
            seen = set()
            unique = []
            for t in pool:
                tid = t.get("id", "")
                if tid not in seen and self.storage.is_downloaded(tid):
                    seen.add(tid)
                    unique.append(t)
            self.hero_kicker.setText("OFFLINE STORAGE")
            self.view_title_lbl.setText("Downloaded Tracks")
            self.view_sub_lbl.setText(f"{len(unique)} saved for offline listening")
            self._populate_track_table(unique)
        elif view == "local":
            folders = self.storage.data["settings"].get("local_folders", [])
            local_tracks = self.provider.scan_local_folders(folders)
            self.hero_kicker.setText("LOCAL DRIVE")
            self.view_title_lbl.setText("Local Music")
            self.view_sub_lbl.setText(f"{len(local_tracks)} local audio files")
            self._populate_track_table(local_tracks)
        elif view == "history":
            hist = self.storage.data["history"]
            stats = self.storage.data.get("stats", {})
            mins = stats.get("total_seconds_listened", 0) // 60
            played = stats.get("tracks_played", 0)
            self.hero_kicker.setText("LISTENING ACTIVITY")
            self.view_title_lbl.setText("History & Stats")
            self.view_sub_lbl.setText(f"{played} plays • {mins} minutes listened")
            self._populate_track_table(hist)

    def _add_local_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            folders = self.storage.data["settings"].setdefault("local_folders", [])
            if folder not in folders:
                folders.append(folder)
                self.storage.save()
            self._switch_view("local")

    def _refresh_playlist_sidebar(self):
        self.playlist_list.clear()
        for name, items in self.storage.data["playlists"].items():
            self.playlist_list.addItem(f"{name}   ({len(items)})")

    def _create_playlist_dialog(self):
        name, ok = QInputDialog.getText(self, "New Playlist", "Playlist name:")
        if ok and name.strip():
            if self.storage.create_playlist(name.strip()):
                self._refresh_playlist_sidebar()

    def _on_playlist_selected(self, item: QListWidgetItem):
        raw = item.text()
        name = raw.rsplit("   (", 1)[0]
        tracks = self.storage.data["playlists"].get(name, [])
        self.hero_kicker.setText("CUSTOM PLAYLIST")
        self.view_title_lbl.setText(name)
        self.view_sub_lbl.setText(f"{len(tracks)} tracks")
        self._populate_track_table(tracks)
        if tracks:
            self.queue = list(tracks)
            self.current_index = 0
            self._refresh_queue_ui()

    def _add_track_to_playlist_prompt(self, track: Dict[str, Any]):
        names = list(self.storage.data["playlists"].keys())
        if not names:
            return
        choice, ok = QInputDialog.getItem(self, "Add to Playlist", "Select playlist:", names, 0, False)
        if ok and choice:
            self.storage.add_to_playlist(choice, track)
            self._refresh_playlist_sidebar()

    def _toggle_like_current(self):
        if not self.current_track:
            return
        liked = self.storage.toggle_like(self.current_track)
        self._update_like_buttons(liked)

    def _toggle_row_like(self, track: Dict[str, Any], btn: QPushButton):
        liked = self.storage.toggle_like(track)
        btn.setIcon(
            QIcon(make_icon("heart_filled" if liked else "heart_outline", 15, self.accent if liked else "#A1A1AA"))
        )
        if self.current_track and self.current_track.get("id") == track.get("id"):
            self._update_like_buttons(liked)

    def _on_current_rating_changed(self, stars: int):
        if self.current_track:
            self.storage.set_rating(self.current_track.get("id", ""), stars)

    def _update_like_buttons(self, liked: bool):
        icon = QIcon(make_icon("heart_filled" if liked else "heart_outline", 18, self.accent if liked else "#A1A1AA"))
        self.bot_like_btn.setIcon(icon)
        self.bot_like_btn.setProperty("active", "true" if liked else "false")
        self.bot_like_btn.style().unpolish(self.bot_like_btn)
        self.bot_like_btn.style().polish(self.bot_like_btn)

        self.np_like_btn.setIcon(
            QIcon(make_icon("heart_filled" if liked else "heart_outline", 20, self.accent if liked else "#A1A1AA"))
        )
        self.mini_player.set_liked(liked)

    def _toggle_shuffle(self):
        cur = not self.storage.data["settings"].get("shuffle", False)
        self.storage.data["settings"]["shuffle"] = cur
        self.storage.save()
        self.shuffle_btn.setIcon(QIcon(make_icon("shuffle", 16, self.accent if cur else "#A1A1AA")))
        self.shuffle_btn.setProperty("active", "true" if cur else "false")
        self.shuffle_btn.style().unpolish(self.shuffle_btn)
        self.shuffle_btn.style().polish(self.shuffle_btn)


    def _sync_loop_ui(self):
        is_one = self.storage.data["settings"].get("repeat", "off") == "one"
        if hasattr(self, "loop_one_btn"):
            self.loop_one_btn.setProperty("active", "true" if is_one else "false")
            self.loop_one_btn.style().unpolish(self.loop_one_btn)
            self.loop_one_btn.style().polish(self.loop_one_btn)
        if hasattr(self, "mini_player"):
            self.mini_player.set_loop_one(is_one)

    def _toggle_loop_one(self):
        cur = self.storage.data["settings"].get("repeat", "off")
        self.storage.data["settings"]["repeat"] = "off" if cur == "one" else "one"
        self.storage.save()
        self._sync_loop_ui()

    def _quit_completely(self):
        self._really_quit = True
        self.mini_player.close()
        self.close()

    def _cycle_repeat(self):
        order = ["off", "all", "one"]
        cur = self.storage.data["settings"].get("repeat", "off")
        nxt = order[(order.index(cur) + 1) % len(order)]
        self.storage.data["settings"]["repeat"] = nxt
        self.storage.save()
        active = nxt != "off"
        self.repeat_btn.setIcon(QIcon(make_icon("repeat", 16, self.accent if active else "#A1A1AA")))
        self.repeat_btn.setProperty("active", "true" if active else "false")
        self.repeat_btn.style().unpolish(self.repeat_btn)
        self.repeat_btn.style().polish(self.repeat_btn)

    def _download_current_track(self):
        if self.current_track:
            self._start_download(self.current_track)

    def _start_download(self, track: Dict[str, Any]):
        tid = track.get("id", "")
        dest = self.storage.get_offline_path(tid)
        if self.storage.is_downloaded(tid):
            QMessageBox.information(self, "Offline Cache", "Track is already saved offline.")
            return
        self._set_loading(f"Saving offline: {track.get('title')}...")
        threading.Thread(
            target=lambda: self.signals.download_finished.emit(
                track.get("title", "Track"), self.provider.download_track(track, dest)
            ),
            daemon=True,
        ).start()

    def _on_download_finished(self, title: str, success: bool):
        self._set_loading("")
        if success:
            QMessageBox.information(self, "Saved", f"'{title}' is now available offline.")
        else:
            QMessageBox.warning(self, "Download Failed", f"Could not save '{title}'.")

    def _apply_eq_preset(self, preset_name: str):
        gains = self.EQ_PRESETS.get(preset_name, [0] * 10)
        for sl, val in zip(self.eq_sliders, gains):
            sl.setValue(val)
        self._save_eq_values()

    def _save_eq_values(self):
        self.storage.data["settings"]["eq_gains"] = [sl.value() for sl in self.eq_sliders]
        self.storage.save()

    def _change_accent_theme(self, theme_name: str):
        accent, hover = self.ACCENT_THEMES.get(theme_name, ("#1DB954", "#1ED760"))
        self.accent = accent
        self.storage.data["settings"]["theme_accent"] = accent
        self.storage.save()
        self.setStyleSheet(get_spotify_stylesheet(accent, hover))
        self.visualizer.set_accent(accent)
        self.mini_player.set_accent(accent)
        self.np_stars.set_accent(accent)

    def _configure_sleep_timer(self):
        mins, ok = QInputDialog.getInt(
            self, "Sleep Timer", "Stop playback after minutes (0 = off):", 30, 0, 240, 5
        )
        if ok:
            self._sleep_seconds_left = mins * 60
            self.sleep_btn.setText(f"SLEEP {mins}M" if mins > 0 else "SLEEP TIMER")

    def _on_one_second_tick(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.storage.add_listening_seconds(1)
        if self._sleep_seconds_left > 0:
            self._sleep_seconds_left -= 1
            if self._sleep_seconds_left == 0:
                self.player.pause()
                self.sleep_btn.setText("SLEEP TIMER")

    def closeEvent(self, event):
        if getattr(self, "_really_quit", False):
            self.mini_player.close()
            super().closeEvent(event)
            return
        event.ignore()
        self.hide()
        self.mini_player.snap_to_bottom_right()
        self.mini_player.show()
        self.mini_player.raise_()
