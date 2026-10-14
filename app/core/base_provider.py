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
    id: str  # videoId or trackId
    title: str
    artists: List[str]
    album: Optional[str] = None
    duration_seconds: int = 0
    match_score: float = 0.0  # 0 to 100
    thumbnail: Optional[str] = None
    is_explicit: bool = False

class BaseMusicProvider(ABC):
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if provider has valid credentials."""
        pass

    @abstractmethod
    def get_playlist(self, playlist_id: str) -> Playlist:
        """Fetch metadata for a given playlist."""
        pass

    @abstractmethod
    def get_playlist_tracks(self, playlist_id: str) -> List[Track]:
        """Fetch all tracks for a playlist, handling pagination automatically."""
        pass

    @abstractmethod
    def search_track(self, track: Track, tolerance_seconds: int = 7) -> Optional[SearchResult]:
        """Search and pick best matching track on this platform."""
        pass

    @abstractmethod
    def create_playlist(self, title: str, description: str = "", is_private: bool = True) -> str:
        """Create a new playlist and return its ID."""
        pass

    @abstractmethod
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> Dict[str, Any]:
        """Add list of track IDs to a playlist (in batches)."""
        pass
