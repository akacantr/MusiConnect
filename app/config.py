import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
YTMUSIC_AUTH_FILE = DATA_DIR / "ytmusic_auth.json"
HISTORY_FILE = DATA_DIR / "history.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    def __init__(self):
        self.spotify_client_id: str = ""
        self.spotify_client_secret: str = ""
        self.spotify_redirect_uri: str = "http://127.0.0.1:8000/callback"
        
        self.ytmusic_auth_type: str = "browser"
        self.transfer_delay: float = 0.35
        self.duration_tolerance: int = 7
        self.batch_size: int = 25
        
        self.load()

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.spotify_client_id = data.get("spotify_client_id", "")
                    self.spotify_client_secret = data.get("spotify_client_secret", "")
                    self.spotify_redirect_uri = data.get("spotify_redirect_uri", "http://127.0.0.1:8000/callback")
                    self.ytmusic_auth_type = data.get("ytmusic_auth_type", "browser")
                    self.transfer_delay = float(data.get("transfer_delay", 0.35))
                    self.duration_tolerance = int(data.get("duration_tolerance", 7))
                    self.batch_size = int(data.get("batch_size", 25))
            except Exception as e:
                print(f"[Config] Error loading settings: {e}")

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "spotify_client_id": self.spotify_client_id,
            "spotify_client_secret": self.spotify_client_secret,
            "spotify_redirect_uri": self.spotify_redirect_uri,
            "ytmusic_auth_type": self.ytmusic_auth_type,
            "transfer_delay": self.transfer_delay,
            "duration_tolerance": self.duration_tolerance,
            "batch_size": self.batch_size,
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spotify_client_id": self.spotify_client_id,
            "spotify_client_secret": "***" + self.spotify_client_secret[-4:] if len(self.spotify_client_secret) > 4 else ("***" if self.spotify_client_secret else ""),
            "has_spotify_secret": bool(self.spotify_client_secret),
            "ytmusic_connected": YTMUSIC_AUTH_FILE.exists(),
            "ytmusic_auth_type": self.ytmusic_auth_type,
            "transfer_delay": self.transfer_delay,
            "duration_tolerance": self.duration_tolerance,
            "batch_size": self.batch_size,
        }

settings = Settings()
