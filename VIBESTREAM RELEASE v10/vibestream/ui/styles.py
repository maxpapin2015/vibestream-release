def get_spotify_stylesheet(accent: str = "#1DB954", accent_hover: str = "#1ED760") -> str:
    return f"""
    QMainWindow, QWidget#RootContainer {{
        background-color: #070709;
        color: #F4F4F6;
        font-family: "Inter", "Segoe UI", "SF Pro Display", Arial, sans-serif;
        font-size: 13px;
    }}

    QWidget#Sidebar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #131318,
            stop:1 #0E0E12);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
    }}

    QPushButton.NavBtn {{
        background-color: transparent;
        color: #9A9AA6;
        border: 1px solid transparent;
        border-radius: 9px;
        text-align: left;
        padding: 10px 14px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton.NavBtn:hover {{
        color: #FFFFFF;
        background-color: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.06);
    }}
    QPushButton.NavBtn[active="true"] {{
        color: #FFFFFF;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(29, 185, 84, 0.18),
            stop:1 rgba(255, 255, 255, 0.04));
        border: 1px solid rgba(29, 185, 84, 0.35);
        font-weight: 700;
    }}

    QListWidget#PlaylistList {{
        background-color: transparent;
        border: none;
        outline: none;
        color: #9A9AA6;
        font-size: 12px;
    }}
    QListWidget#PlaylistList::item {{
        padding: 8px 11px;
        border-radius: 8px;
        margin-bottom: 2px;
    }}
    QListWidget#PlaylistList::item:hover {{
        background-color: rgba(255, 255, 255, 0.05);
        color: #FFFFFF;
    }}
    QListWidget#PlaylistList::item:selected {{
        background-color: rgba(255, 255, 255, 0.09);
        color: {accent};
        font-weight: 700;
    }}

    QWidget#MainContent {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #14141A,
            stop:1 #0F0F13);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
    }}

    QFrame#HeroBanner {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(29, 185, 84, 0.28),
            stop:0.55 rgba(24, 24, 32, 0.88),
            stop:1 rgba(16, 16, 21, 1.0));
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 14px;
    }}

    QWidget#RightPanel {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #131318,
            stop:1 #0E0E12);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
    }}

    QLineEdit#SearchInput {{
        background-color: #1A1A22;
        color: #FFFFFF;
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        padding: 10px 18px;
        font-size: 13px;
    }}
    QLineEdit#SearchInput:focus {{
        border: 1.5px solid {accent};
        background-color: #21212B;
    }}

    QPushButton.ChipBtn {{
        background-color: #191920;
        color: #C8C8D2;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 15px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton.ChipBtn:hover {{
        background-color: #23232D;
        color: #FFFFFF;
        border-color: rgba(255, 255, 255, 0.18);
    }}
    QPushButton.ChipBtn[active="true"] {{
        background-color: {accent};
        color: #070709;
        border-color: {accent};
        font-weight: 800;
    }}

    QPushButton.PrimaryAccentBtn {{
        background-color: {accent};
        color: #070709;
        border: none;
        border-radius: 19px;
        padding: 9px 20px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.4px;
    }}
    QPushButton.PrimaryAccentBtn:hover {{
        background-color: {accent_hover};
    }}

    QPushButton.SecondaryBtn {{
        background-color: #1A1A22;
        color: #E4E4EA;
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 17px;
        padding: 7px 15px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton.SecondaryBtn:hover {{
        background-color: #242430;
        color: #FFFFFF;
        border-color: rgba(255, 255, 255, 0.22);
    }}

    QTableWidget#TrackTable {{
        background-color: transparent;
        alternate-background-color: rgba(255, 255, 255, 0.015);
        border: none;
        gridline-color: transparent;
        color: #F4F4F6;
        selection-background-color: rgba(255, 255, 255, 0.08);
        selection-color: #FFFFFF;
        outline: none;
    }}
    QTableWidget#TrackTable::item {{
        padding: 5px 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }}
    QTableWidget#TrackTable::item:hover {{
        background-color: rgba(255, 255, 255, 0.05);
    }}
    QHeaderView::section {{
        background-color: #121217;
        color: #787886;
        border: none;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding: 9px 8px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.9px;
    }}

    QWidget#BottomPlayer {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #0C0C10,
            stop:0.5 #111116,
            stop:1 #0C0C10);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 14px;
    }}

    QPushButton.PlayerCtrlBtn {{
        background-color: transparent;
        color: #A1A1AE;
        border: none;
        border-radius: 16px;
    }}
    QPushButton.PlayerCtrlBtn:hover {{
        color: #FFFFFF;
        background-color: rgba(255, 255, 255, 0.08);
    }}
    QPushButton.PlayerCtrlBtn[active="true"] {{
        color: {accent};
        background-color: rgba(29, 185, 84, 0.14);
    }}

    QPushButton#MainPlayBtn {{
        background-color: #FFFFFF;
        color: #070709;
        border: none;
        border-radius: 20px;
    }}
    QPushButton#MainPlayBtn:hover {{
        background-color: {accent_hover};
    }}

    QSlider::groove:horizontal {{
        border: none;
        height: 4px;
        background: rgba(255, 255, 255, 0.14);
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {accent};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: #FFFFFF;
        border: none;
        width: 12px;
        height: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }}

    QSlider::groove:vertical {{
        background: rgba(255, 255, 255, 0.12);
        width: 4px;
        border-radius: 2px;
    }}
    QSlider::add-page:vertical {{
        background: rgba(255, 255, 255, 0.12);
        border-radius: 2px;
    }}
    QSlider::sub-page:vertical {{
        background: {accent};
        border-radius: 2px;
    }}
    QSlider::handle:vertical {{
        background: #FFFFFF;
        height: 12px;
        width: 12px;
        margin: 0 -4px;
        border-radius: 6px;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 7px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.18);
        min-height: 28px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.36);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """
