import os
import re
import glob
import random
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False


class MusicProvider:
    """
    Aggregates multiple completely free, ad-free, keyless music sources:
    1. YouTube Music / YouTube via yt-dlp (virtually every song on Earth, full length, high bitrate audio)
    2. Audius Decentralized Music Protocol (open API, instant MP3 streaming, trending & underground)
    3. LRCLIB.net (free synchronized timestamped karaoke lyrics)
    4. Local MP3/FLAC/WAV/OGG scanner
    """

    AUDIUS_HOSTS = [
        "https://discoveryprovider.audius.co",
        "https://discoveryprovider2.audius.co",
        "https://discoveryprovider3.audius.co",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "VibeStreamDesktop/2.0"})
        self._audius_host = self.AUDIUS_HOSTS[0]

    def _get_audius_host(self) -> str:
        try:
            r = self.session.get("https://api.audius.co", timeout=3)
            if r.ok:
                hosts = r.json().get("data", [])
                if hosts:
                    self._audius_host = random.choice(hosts)
        except Exception:
            pass
        return self._audius_host

    def get_trending(self, genre: str = "") -> List[Dict[str, Any]]:
        """Fetch trending tracks from Audius (instant load) with fallback curated queries."""
        tracks = self._fetch_audius_trending(genre=genre, limit=24)
        if tracks:
            return tracks
        return self.search_tracks("Top Hits 2026 Music", limit=18)

    def _fetch_audius_trending(self, genre: str = "", limit: int = 24) -> List[Dict[str, Any]]:
        host = self._get_audius_host()
        params = {"limit": limit}
        if genre and genre != "All":
            params["genre"] = genre
        try:
            r = self.session.get(f"{host}/v1/tracks/trending", params=params, timeout=6)
            if not r.ok:
                return []
            items = r.json().get("data", [])
            results = []
            for item in items:
                tid = item.get("id")
                artwork = item.get("artwork") or {}
                cover = artwork.get("480x480") or artwork.get("150x150") or ""
                user = item.get("user") or {}
                results.append({
                    "id": f"audius_{tid}",
                    "raw_id": tid,
                    "source": "audius",
                    "title": item.get("title", "Unknown Track"),
                    "artist": user.get("name") or user.get("handle") or "Unknown Artist",
                    "album": item.get("genre") or "Audius Stream",
                    "duration": int(item.get("duration") or 180),
                    "cover_url": cover,
                    "stream_url": f"{host}/v1/tracks/{tid}/stream",
                })
            return results
        except Exception:
            return []

    def search_tracks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search across YouTube Music (full catalog) and Audius simultaneously."""
        query = query.strip()
        if not query:
            return []

        results: List[Dict[str, Any]] = []

        # 1. Primary: YouTube search via yt-dlp (gives access to 100M+ official songs, remixes, covers)
        if HAS_YTDLP:
            try:
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": True,
                    "skip_download": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch{limit}:{query} audio", download=False)
                    entries = info.get("entries", []) if info else []
                    for entry in entries:
                        if not entry:
                            continue
                        vid = entry.get("id")
                        if not vid:
                            continue
                        dur = int(entry.get("duration") or 0)
                        if dur > 900:  # Skip hour-long mixes in quick search
                            continue
                        raw_title = entry.get("title") or "Unknown"
                        channel = entry.get("uploader") or entry.get("channel") or "YouTube Music"
                        artist, clean_title = self._parse_artist_title(raw_title, channel)
                        thumbs = entry.get("thumbnails") or []
                        cover = thumbs[-1].get("url") if thumbs else f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
                        results.append({
                            "id": f"yt_{vid}",
                            "raw_id": vid,
                            "source": "youtube",
                            "title": clean_title,
                            "artist": artist,
                            "album": "YouTube Music",
                            "duration": dur if dur > 0 else 200,
                            "cover_url": cover,
                            "webpage_url": f"https://www.youtube.com/watch?v={vid}",
                            "stream_url": "",  # Resolved lazily on play for speed
                        })
            except Exception as e:
                print(f"[MusicProvider] yt-dlp search error: {e}")

        # 2. Secondary / Supplement: Audius search
        if len(results) < 6:
            try:
                host = self._get_audius_host()
                r = self.session.get(
                    f"{host}/v1/tracks/search",
                    params={"query": query, "limit": 12},
                    timeout=5,
                )
                if r.ok:
                    for item in r.json().get("data", []):
                        tid = item.get("id")
                        artwork = item.get("artwork") or {}
                        cover = artwork.get("480x480") or artwork.get("150x150") or ""
                        user = item.get("user") or {}
                        results.append({
                            "id": f"audius_{tid}",
                            "raw_id": tid,
                            "source": "audius",
                            "title": item.get("title", "Unknown"),
                            "artist": user.get("name") or "Unknown Artist",
                            "album": item.get("genre") or "Audius",
                            "duration": int(item.get("duration") or 180),
                            "cover_url": cover,
                            "stream_url": f"{host}/v1/tracks/{tid}/stream",
                        })
            except Exception:
                pass

        return results

    def resolve_stream_url(self, track: Dict[str, Any], offline_path: Optional[Path] = None) -> Optional[str]:
        """Resolve direct playable audio URL or local file path."""
        if offline_path and offline_path.exists() and offline_path.stat().st_size > 10000:
            return str(offline_path.resolve())

        source = track.get("source")
        if source == "local":
            p = track.get("stream_url") or track.get("file_path")
            return p if p and os.path.exists(p) else None

        if source == "audius":
            return track.get("stream_url")

        if source == "youtube" and HAS_YTDLP:
            vid = track.get("raw_id")
            url = track.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"
            ydl_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        if info.get("duration"):
                            track["duration"] = int(info["duration"])
                        return info.get("url")
            except Exception as e:
                print(f"[MusicProvider] Stream resolve error: {e}")

        return track.get("stream_url") or None

    def download_track(self, track: Dict[str, Any], dest_path: Path) -> bool:
        """Download track for offline listening."""
        source = track.get("source")
        try:
            if source == "audius":
                url = track.get("stream_url")
                if not url:
                    return False
                with self.session.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(dest_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
                return dest_path.exists() and dest_path.stat().st_size > 10000

            elif source == "youtube" and HAS_YTDLP:
                vid = track.get("raw_id")
                url = track.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"
                out_tmpl = str(dest_path.with_suffix("")) + ".%(ext)s"
                ydl_opts = {
                    "format": "bestaudio[ext=m4a]/bestaudio/best",
                    "outtmpl": out_tmpl,
                    "quiet": True,
                    "no_warnings": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                # Rename whatever extension was downloaded to dest_path
                for candidate in dest_path.parent.glob(f"{dest_path.stem}.*"):
                    if candidate != dest_path:
                        candidate.replace(dest_path)
                        break
                return dest_path.exists() and dest_path.stat().st_size > 10000
        except Exception as e:
            print(f"[MusicProvider] Download error: {e}")
        return False

    def fetch_lyrics(self, title: str, artist: str) -> Dict[str, Any]:
        """Fetch synchronized LRC or plain lyrics from free LRCLIB API."""
        clean_title = re.sub(r"\(.*?\)|\[.*?\]", "", title).strip()
        clean_artist = re.sub(r"\(.*?\)|\[.*?\]|- Topic|VEVO|Official", "", artist, flags=re.I).strip()
        try:
            r = self.session.get(
                "https://lrclib.net/api/search",
                params={"track_name": clean_title, "artist_name": clean_artist},
                timeout=5,
            )
            if r.ok:
                items = r.json()
                if items:
                    best = items[0]
                    synced = best.get("syncedLyrics") or ""
                    plain = best.get("plainLyrics") or ""
                    return {
                        "synced": self._parse_lrc(synced),
                        "plain": plain,
                    }
        except Exception:
            pass
        return {"synced": [], "plain": ""}

    @staticmethod
    def _parse_lrc(lrc_text: str) -> List[tuple]:
        lines = []
        pattern = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\](.*)")
        for raw_line in lrc_text.splitlines():
            m = pattern.match(raw_line.strip())
            if m:
                mins = int(m.group(1))
                secs = float(m.group(2))
                text = m.group(3).strip()
                if text:
                    lines.append((mins * 60.0 + secs, text))
        lines.sort(key=lambda x: x[0])
        return lines

    def scan_local_folders(self, folders: List[str]) -> List[Dict[str, Any]]:
        """Scan local directories for MP3, FLAC, M4A, OGG, WAV files."""
        exts = ("*.mp3", "*.flac", "*.m4a", "*.ogg", "*.wav")
        found = []
        for folder in folders:
            if not folder or not os.path.isdir(folder):
                continue
            for ext in exts:
                for path_str in glob.glob(os.path.join(folder, "**", ext), recursive=True):
                    p = Path(path_str)
                    title = p.stem
                    artist = "Локальный файл"
                    album = p.parent.name
                    duration = 180
                    if HAS_MUTAGEN:
                        try:
                            audio = MutagenFile(path_str, easy=True)
                            if audio:
                                if audio.info and getattr(audio.info, "length", None):
                                    duration = int(audio.info.length)
                                if "title" in audio:
                                    title = str(audio["title"][0])
                                if "artist" in audio:
                                    artist = str(audio["artist"][0])
                                if "album" in audio:
                                    album = str(audio["album"][0])
                        except Exception:
                            pass
                    found.append({
                        "id": f"local_{abs(hash(path_str))}",
                        "raw_id": path_str,
                        "source": "local",
                        "title": title,
                        "artist": artist,
                        "album": album,
                        "duration": duration,
                        "cover_url": "",
                        "stream_url": path_str,
                    })
        return found

    @staticmethod
    def _parse_artist_title(raw_title: str, channel: str) -> tuple:
        cleaned = re.sub(
            r"\((Official\s*(Music\s*)?Video|Audio|Lyrics|Lyric\s*Video|HD|4K|Visualizer)\)|"
            r"\[(Official\s*(Music\s*)?Video|Audio|Lyrics|HD|4K)\]",
            "",
            raw_title,
            flags=re.IGNORECASE,
        ).strip()
        if " - " in cleaned:
            parts = cleaned.split(" - ", 1)
            return parts[0].strip(), parts[1].strip()
        clean_channel = re.sub(r"\s*-\s*Topic$|VEVO$|Official$", "", channel, flags=re.I).strip()
        return clean_channel or "Artist", cleaned
