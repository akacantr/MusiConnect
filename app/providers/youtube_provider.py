import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from ytmusicapi import YTMusic, setup
from app.core.base_provider import BaseMusicProvider, Track, Playlist, SearchResult
from app.core.matcher import SmartMatcher
from app.config import settings, YTMUSIC_AUTH_FILE

class YouTubeProvider(BaseMusicProvider):
    def __init__(self):
        self._yt: Optional[YTMusic] = None
        self._search_yt: YTMusic = YTMusic()  # Unauthenticated instance for public search fallback
        self._init_client()

    def _init_client(self):
        if YTMUSIC_AUTH_FILE.exists():
            try:
                self._yt = YTMusic(auth=str(YTMUSIC_AUTH_FILE))
            except Exception as e:
                print(f"[YouTubeProvider] Auth init error: {e}")
                self._yt = None
        else:
            self._yt = None

    def refresh_client(self):
        self._init_client()

    def is_authenticated(self) -> bool:
        if not self._yt:
            self._init_client()
        if not self._yt:
            return False
        try:
            info = self._yt.get_account_info()
            return bool(info and info.get("accountName"))
        except Exception:
            return False

    def get_account_details(self) -> Optional[Dict[str, Any]]:
        if not self._yt:
            self._init_client()
        if not self._yt:
            return None
        try:
            return self._yt.get_account_info()
        except Exception as e:
            return None

    @staticmethod
    def _clean_and_parse_input(raw_text: str) -> str:
        import re
        text = raw_text.strip()
        # If user copied as cURL (bash or cmd)
        if text.startswith("curl") or "-H" in text or "-b" in text:
            headers = []
            # 1. Match all -H 'Key: Value'
            for match in re.finditer(r"-H\s+['\"\^](.+?):\s*(.+?)['\"\^](?:\s|$|\\|\^)", text):
                headers.append(f"{match.group(1).strip()}: {match.group(2).strip()}")
            
            # 2. Match -b 'cookies' or --cookie 'cookies'
            cookie_match = re.search(r"(?:-b|--cookie)\s+['\"\^](.+?)['\"\^]", text)
            if cookie_match:
                headers.append(f"cookie: {cookie_match.group(1).strip()}")

            if headers:
                return "\n".join(headers)
        return text

    def save_browser_headers(self, headers_raw: str) -> Dict[str, Any]:
        try:
            cleaned_headers = self._clean_and_parse_input(headers_raw)
            setup(filepath=str(YTMUSIC_AUTH_FILE), headers_raw=cleaned_headers)
            self._init_client()
            if self.is_authenticated():
                account = self.get_account_details()
                return {"success": True, "account": account}
            else:
                if YTMUSIC_AUTH_FILE.exists():
                    YTMUSIC_AUTH_FILE.unlink()
                return {"success": False, "error": "Kimlik doğrulama başarısız oldu. Lütfen başlıkları (headers) kontrol edip tekrar deneyin."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_track(self, track: Track, tolerance_seconds: int = 7) -> Optional[SearchResult]:
        yt_client = self._yt if self._yt else self._search_yt
        
        # 1. Search queries in order of precision
        queries = [
            f"{track.artist_str} - {track.title}",
            f"{track.title} {track.artists[0] if track.artists else ''}",
        ]

        best_result: Optional[SearchResult] = None
        highest_score = 0.0

        for query in queries:
            try:
                # First attempt: search in 'songs' filter (official releases)
                results = yt_client.search(query, filter="songs", limit=10)
                
                # If no songs found, fallback to general search
                if not results:
                    results = yt_client.search(query, limit=10)

                for item in results:
                    video_id = item.get("videoId")
                    if not video_id:
                        continue

                    title = item.get("title", "")
                    artists = [a.get("name", "") for a in item.get("artists", []) if a.get("name")]
                    duration_sec = item.get("duration_seconds", 0)
                    if not duration_sec and "duration" in item:
                        # parse MM:SS string if needed
                        parts = str(item["duration"]).split(":")
                        if len(parts) == 2:
                            duration_sec = int(parts[0]) * 60 + int(parts[1])
                        elif len(parts) == 3:
                            duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

                    category = item.get("category", "")
                    is_song = (category == "Songs" or item.get("resultType") == "song")

                    score = SmartMatcher.score_match(
                        target_track=track,
                        candidate_title=title,
                        candidate_artists=artists,
                        candidate_duration=duration_sec,
                        is_song_category=is_song,
                        tolerance_seconds=tolerance_seconds
                    )

                    if score > highest_score:
                        highest_score = score
                        thumbnails = item.get("thumbnails", [])
                        thumb_url = thumbnails[-1]["url"] if thumbnails else None
                        
                        best_result = SearchResult(
                            id=video_id,
                            title=title,
                            artists=artists,
                            album=item.get("album", {}).get("name") if isinstance(item.get("album"), dict) else None,
                            duration_seconds=duration_sec,
                            match_score=round(score, 1),
                            thumbnail=thumb_url,
                            is_explicit=item.get("isExplicit", False)
                        )

                # If we found a high quality match (> 75 score), stop searching further queries
                if highest_score >= 75.0:
                    break

            except Exception as e:
                print(f"[YouTubeProvider] Search error on query '{query}': {e}")
                continue

        # If score is below acceptable threshold, reject match
        if best_result and best_result.match_score >= 40.0:
            return best_result
        return None

    def create_playlist(self, title: str, description: str = "", is_private: bool = True) -> str:
        if not self._yt:
            self._init_client()
        if not self._yt:
            raise ValueError("YouTube Music hesabı bağlı değil. Lütfen Ayarlar sayfasından giriş yapın.")

        privacy = "PRIVATE" if is_private else "PUBLIC"
        desc = description or "Transferred via MusiConnect"
        playlist_id = self._yt.create_playlist(title=title, description=desc, privacy_status=privacy)
        
        # When created, ytmusicapi might return a string or dict
        if isinstance(playlist_id, dict):
            return playlist_id.get("id", str(playlist_id))
        return str(playlist_id)

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> Dict[str, Any]:
        if not self._yt:
            self._init_client()
        if not self._yt:
            raise ValueError("YouTube Music hesabı bağlı değil.")

        if not track_ids:
            return {"status": "SUCCESS", "added": 0}

        res = self._yt.add_playlist_items(playlistId=playlist_id, videoIds=track_ids, duplicates=False)
        return {"status": "SUCCESS", "response": res, "added": len(track_ids)}

    def get_playlist(self, playlist_id: str) -> Playlist:
        if not self._yt:
            self._init_client()
        yt_client = self._yt if self._yt else self._search_yt
        data = yt_client.get_playlist(playlist_id)
        return Playlist(
            id=playlist_id,
            name=data.get("title", ""),
            description=data.get("description", ""),
            track_count=data.get("trackCount", 0),
            image_url=data.get("thumbnails", [{}])[-1].get("url") if data.get("thumbnails") else None,
            url=f"https://music.youtube.com/playlist?list={playlist_id}"
        )

    def get_playlist_tracks(self, playlist_id: str) -> List[Track]:
        if not self._yt:
            self._init_client()
        yt_client = self._yt if self._yt else self._search_yt
        data = yt_client.get_playlist(playlist_id, limit=None)
        tracks = []
        for item in data.get("tracks", []):
            tracks.append(Track(
                id=item.get("videoId", ""),
                title=item.get("title", ""),
                artists=[a.get("name", "") for a in item.get("artists", [])],
                duration_seconds=item.get("duration_seconds", 0),
                image_url=item.get("thumbnails", [{}])[-1].get("url") if item.get("thumbnails") else None
            ))
        return tracks
