import re
from typing import List, Optional, Dict, Any
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from app.core.base_provider import BaseMusicProvider, Track, Playlist, SearchResult
from app.config import settings, DATA_DIR

SPOTIFY_CACHE_FILE = DATA_DIR / ".spotify_cache"

class SpotifyProvider(BaseMusicProvider):
    def __init__(self):
        self._sp: Optional[spotipy.Spotify] = None
        self._oauth: Optional[SpotifyOAuth] = None
        self._init_client()

    def _init_client(self):
        client_id = settings.spotify_client_id.strip()
        client_secret = settings.spotify_client_secret.strip()
        if client_id and client_secret:
            try:
                self._oauth = SpotifyOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=settings.spotify_redirect_uri,
                    scope="playlist-read-private playlist-read-collaborative user-library-read",
                    cache_path=str(SPOTIFY_CACHE_FILE),
                    open_browser=False
                )
                
                # If user already logged in via OAuth, use OAuth session
                if self._oauth.get_cached_token():
                    self._sp = spotipy.Spotify(auth_manager=self._oauth, requests_timeout=15)
                else:
                    # Otherwise use ClientCredentials until user logs in
                    cc = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
                    self._sp = spotipy.Spotify(auth_manager=cc, requests_timeout=15)
            except Exception as e:
                print(f"[SpotifyProvider] Init error: {e}")
                self._sp = None
        else:
            self._sp = None

    def refresh_client(self):
        self._init_client()

    def get_auth_url(self) -> Optional[str]:
        if not self._oauth:
            self._init_client()
        if self._oauth:
            return self._oauth.get_authorize_url()
        return None

    def handle_callback(self, code: str) -> bool:
        if not self._oauth:
            self._init_client()
        if not self._oauth:
            return False
        try:
            token_info = self._oauth.get_access_token(code)
            if token_info:
                self._sp = spotipy.Spotify(auth_manager=self._oauth, requests_timeout=15)
                return True
        except Exception as e:
            print(f"[SpotifyProvider] Callback error: {e}")
        return False

    def is_user_authenticated(self) -> bool:
        if not self._oauth:
            self._init_client()
        return bool(self._oauth and self._oauth.get_cached_token())

    def get_user_display_name(self) -> Optional[str]:
        if self.is_user_authenticated() and self._sp:
            try:
                me = self._sp.current_user()
                return me.get("display_name") or me.get("id")
            except Exception:
                return None
        return None

    def is_authenticated(self) -> bool:
        if not self._sp:
            self._init_client()
        if not self._sp:
            return False
        try:
            self._sp.search(q="test", limit=1, type="track")
            return True
        except Exception:
            return False

    @staticmethod
    def extract_playlist_id(url_or_id: str) -> str:
        text = url_or_id.strip()
        match = re.search(r"playlist[/:]([a-zA-Z0-9]+)", text)
        if match:
            return match.group(1)
        cleaned = re.sub(r"[^a-zA-Z0-9]", "", text)
        return cleaned

    def get_playlist(self, playlist_id_or_url: str) -> Playlist:
        if not self._sp:
            self._init_client()
        if not self._sp:
            raise ValueError("Spotify API anahtarları tanımlanmamış. Lütfen Ayarlar sayfasından Client ID ve Secret girin.")

        p_id = self.extract_playlist_id(playlist_id_or_url)
        try:
            data = self._sp.playlist(p_id)
        except spotipy.SpotifyException as se:
            if se.http_status == 401 or "Valid user authentication required" in str(se):
                raise ValueError("Bu çalma listesine erişebilmek için lütfen 'Spotify ile Giriş Yap' butonuna tıklayarak hesabınızı yetkilendirin.")
            raise se
        
        image_url = None
        if data.get("images") and len(data["images"]) > 0:
            image_url = data["images"][0].get("url")

        track_count = 0
        if isinstance(data.get("tracks"), dict):
            track_count = data.get("tracks", {}).get("total", 0)
        elif isinstance(data.get("items"), dict):
            track_count = data.get("items", {}).get("total", 0)

        return Playlist(
            id=data["id"],
            name=data.get("name", "İsimsiz Liste"),
            description=data.get("description", ""),
            track_count=track_count,
            image_url=image_url,
            owner=data.get("owner", {}).get("display_name", ""),
            url=data.get("external_urls", {}).get("spotify", f"https://open.spotify.com/playlist/{p_id}")
        )

    def get_playlist_tracks(self, playlist_id_or_url: str) -> List[Track]:
        if not self._sp:
            self._init_client()
        if not self._sp:
            raise ValueError("Spotify API anahtarları tanımlanmamış. Lütfen Ayarlar sayfasından Client ID ve Secret girin.")

        p_id = self.extract_playlist_id(playlist_id_or_url)
        tracks: List[Track] = []
        offset = 0
        limit = 100

        while True:
            try:
                response = self._sp.playlist_items(
                    p_id,
                    offset=offset,
                    limit=limit,
                    additional_types=('track',)
                )
            except spotipy.SpotifyException as se:
                if se.http_status == 401 or "Valid user authentication required" in str(se):
                    raise ValueError("Bu çalma listesine erişebilmek için lütfen 'Spotify ile Giriş Yap' butonuna tıklayarak hesabınızı yetkilendirin.")
                raise se

            items = response.get("items", [])
            if not items:
                break

            for item in items:
                t = item.get("item") or item.get("track")
                if not t or not t.get("name"):
                    continue

                artists = [a.get("name", "") for a in t.get("artists", []) if a.get("name")]
                album_name = t.get("album", {}).get("name") if isinstance(t.get("album"), dict) else None
                images = t.get("album", {}).get("images", []) if isinstance(t.get("album"), dict) else []
                image_url = images[0].get("url") if images else None
                isrc = t.get("external_ids", {}).get("isrc") if isinstance(t.get("external_ids"), dict) else None
                duration_sec = int(t.get("duration_ms", 0)) // 1000

                track_obj = Track(
                    id=t.get("id", f"sp_{len(tracks)}"),
                    title=t.get("name"),
                    artists=artists,
                    album=album_name,
                    duration_seconds=duration_sec,
                    isrc=isrc,
                    image_url=image_url,
                    uri=t.get("uri")
                )
                tracks.append(track_obj)

            offset += len(items)
            total = response.get("total", 0)
            if offset >= total:
                break

        return tracks

    def search_track(self, track: Track, tolerance_seconds: int = 7) -> Optional[SearchResult]:
        raise NotImplementedError("Spotify arama henüz hedeflenmedi.")

    def create_playlist(self, title: str, description: str = "", is_private: bool = True) -> str:
        raise NotImplementedError("Spotify'a aktarım için Spotify OAuth gerekir.")

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> Dict[str, Any]:
        raise NotImplementedError("Spotify'a aktarım için Spotify OAuth gerekir.")
