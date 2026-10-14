from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Track(BaseModel):
    id: str
    title: str
    artists: List[str]
    album: Optional[str] = None
    duration_seconds: int = 0
    isrc: Optional[str] = None
    image_url: Optional[str] = None
    uri: Optional[str] = None

    @property
    def artist_str(self) -> str:
        return ", ".join(self.artists)

class Playlist(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    track_count: int = 0
    image_url: Optional[str] = None
    owner: Optional[str] = None
    url: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    title: str
    artists: List[str]
    album: Optional[str] = None
    duration_seconds: int = 0
    match_score: float = 0.0
    thumbnail: Optional[str] = None
    is_explicit: bool = False

class BaseMusicProvider(ABC):
    @abstractmethod
    def is_authenticated(self) -> bool:
        pass

    @abstractmethod
    def get_playlist(self, playlist_id: str) -> Playlist:
        pass

    @abstractmethod
    def get_playlist_tracks(self, playlist_id: str) -> List[Track]:
        pass

    @abstractmethod
    def search_track(self, track: Track, tolerance_seconds: int = 7) -> Optional[SearchResult]:
        pass

    @abstractmethod
    def create_playlist(self, title: str, description: str = "", is_private: bool = True) -> str:
        pass

    @abstractmethod
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> Dict[str, Any]:
        pass
