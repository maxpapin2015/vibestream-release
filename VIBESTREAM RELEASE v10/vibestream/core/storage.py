import json
from pathlib import Path
from typing import Dict, List, Any


class StorageManager:
    """Manages local user data: playlists, liked songs, ratings, history, settings, and offline downloads."""

    def __init__(self):
        self.base_dir = Path.home() / ".vibestream"
        self.cache_dir = self.base_dir / "offline_music"
        self.covers_dir = self.base_dir / "covers"
        self.data_file = self.base_dir / "library.json"

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.covers_dir.mkdir(parents=True, exist_ok=True)

        self.data: Dict[str, Any] = self._load()

    def _default_data(self) -> Dict[str, Any]:
        return {
            "liked_songs": [],
            "ratings": {},  # track_id -> int (1..5)
            "history": [],
            "playlists": {
                "Daily Mix": [],
                "Late Night Focus": [],
                "High Energy": [],
            },
            "settings": {
                "volume": 80,
                "shuffle": False,
                "repeat": "off",  # off, all, one
                "playback_rate": 1.0,
                "equalizer_preset": "Flat",
                "eq_gains": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "local_folders": [str(Path.home() / "Music")],
                "mini_player_pos": None,
                "theme_accent": "#1DB954",
            },
            "stats": {
                "total_seconds_listened": 0,
                "tracks_played": 0,
            },
        }

    def _load(self) -> Dict[str, Any]:
        if not self.data_file.exists():
            data = self._default_data()
            self._save(data)
            return data
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            default = self._default_data()
            for k, v in default.items():
                if k not in loaded:
                    loaded[k] = v
            return loaded
        except Exception:
            return self._default_data()

    def save(self):
        self._save(self.data)

    def _save(self, data: Dict[str, Any]):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Storage] Save error: {e}")

    def is_liked(self, track_id: str) -> bool:
        return any(t.get("id") == track_id for t in self.data["liked_songs"])

    def toggle_like(self, track: Dict[str, Any]) -> bool:
        tid = track.get("id")
        if self.is_liked(tid):
            self.data["liked_songs"] = [t for t in self.data["liked_songs"] if t.get("id") != tid]
            self.save()
            return False
        else:
            enriched = dict(track)
            enriched["liked"] = True
            self.data["liked_songs"].insert(0, enriched)
            self.save()
            return True

    def set_rating(self, track_id: str, stars: int):
        stars = max(0, min(5, int(stars)))
        ratings = self.data.setdefault("ratings", {})
        if stars == 0:
            ratings.pop(track_id, None)
        else:
            ratings[track_id] = stars
        self.save()

    def get_rating(self, track_id: str) -> int:
        return int(self.data.get("ratings", {}).get(track_id, 0))

    def add_history(self, track: Dict[str, Any]):
        tid = track.get("id")
        self.data["history"] = [t for t in self.data["history"] if t.get("id") != tid]
        self.data["history"].insert(0, track)
        self.data["history"] = self.data["history"][:120]
        self.data["stats"]["tracks_played"] = self.data["stats"].get("tracks_played", 0) + 1
        self.save()

    def add_listening_seconds(self, seconds: int):
        self.data["stats"]["total_seconds_listened"] = (
            self.data["stats"].get("total_seconds_listened", 0) + seconds
        )
        self.save()

    def create_playlist(self, name: str) -> bool:
        name = name.strip()
        if not name or name in self.data["playlists"]:
            return False
        self.data["playlists"][name] = []
        self.save()
        return True

    def delete_playlist(self, name: str):
        if name in self.data["playlists"]:
            del self.data["playlists"][name]
            self.save()

    def add_to_playlist(self, playlist_name: str, track: Dict[str, Any]):
        if playlist_name in self.data["playlists"]:
            tracks = self.data["playlists"][playlist_name]
            if not any(t.get("id") == track.get("id") for t in tracks):
                tracks.append(track)
                self.save()

    def remove_from_playlist(self, playlist_name: str, track_id: str):
        if playlist_name in self.data["playlists"]:
            self.data["playlists"][playlist_name] = [
                t for t in self.data["playlists"][playlist_name] if t.get("id") != track_id
            ]
            self.save()

    def get_offline_path(self, track_id: str) -> Path:
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(track_id))
        return self.cache_dir / f"{safe_id}.mp3"

    def is_downloaded(self, track_id: str) -> bool:
        p = self.get_offline_path(track_id)
        return p.exists() and p.stat().st_size > 10000
