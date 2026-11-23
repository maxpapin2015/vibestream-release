# VibeStream RELEASE

Modern, dark-themed desktop music player built with **Python** and **PyQt6** — free, ad-free, and ready to package into a standalone Windows `VibeStream.exe`.

## Highlights

- **Multi-Source Free Streaming & Local Library:** Search catalog tracks via `yt-dlp`, browse genre charts via Audius, or scan local audio folders (`MP3`, `FLAC`, `M4A`, `OGG`, `WAV`).
- **Corner Mini-Player on Minimize:** Minimizing the window (or pressing `Ctrl+M`) docks a sleek always-on-top mini-player in the bottom-right corner with cover art, track title, artist, exact elapsed seconds (`MM:SS (Ns)`), seek slider, `Prev` / `Play-Pause` / `Next`, `Like`, and `Expand`.
- **Likes & 1-5 Star Ratings:** Like tracks anywhere in the app or mini-player, rate tracks from 1 to 5 stars, and browse dedicated **Liked Songs** and **Rated Tracks** views.
- **Dynamic Cover Gradient, Synced Lyrics & 10-Band EQ:** Adapts the hero banner gradient from the active album cover, highlights timestamped lyrics via LRCLIB, renders a 28-bar spectrum visualizer, and saves 10-band equalizer presets.
- **Offline Cache, Playlists, Speed Control & Sleep Timer:** Save tracks locally for offline listening, organize custom playlists, adjust playback speed (`0.75x` to `1.5x`), switch accent themes, and set a sleep timer.

## Quick Start & EXE Build (Windows)

1. Extract the release archive into a folder such as `C:\VibeStream-Release`.
2. Double-click **`BUILD_RELEASE.bat`** to set up `.venv`, generate `vibestream.ico`, and build **`dist\VibeStream.exe`** via PyInstaller.
3. Run **`dist\VibeStream.exe`** directly without a console window.

Alternatively, double-click **`START_HERE.bat`** to launch the interactive PowerShell menu (`1` — run app, `2` — build `VibeStream.exe`, `3` — build and run `VibeStream.exe`).

## Keyboard Shortcuts

- `Space` — Play / Pause
- `Ctrl+Right` — Next Track
- `Ctrl+Left` — Previous Track
- `Ctrl+F` — Focus Search Bar
- `Ctrl+M` — Toggle Corner Mini-Widget

## License

Released under the [MIT License](LICENSE).
