import re
from typing import List, Optional
from difflib import SequenceMatcher
from app.core.base_provider import Track, SearchResult

class SmartMatcher:
    # Common video title fluff to strip
    CLEAN_PATTERNS = [
        r"\(official\s*(music\s*)?video\)",
        r"\[official\s*(music\s*)?video\]",
        r"\(official\s*audio\)",
        r"\[official\s*audio\]",
        r"\(lyrics?\)",
        r"\[lyrics?\]",
        r"\(visualizer\)",
        r"\[visualizer\]",
        r"\(audio\)",
        r"\[audio\]",
        r"\(hd\)",
        r"\[hd\]",
        r"\(4k\)",
        r"\[4k\]",
        r"\(remaster(ed)?(\s*\d{4})?\)",
        r"\[remaster(ed)?(\s*\d{4})?\]",
        r"\(bonus track\)",
        r"\[bonus track\]",
        r"\(radio edit\)",
    ]

    @classmethod
    def clean_title(cls, text: str) -> str:
        cleaned = text.lower()
        for pattern in cls.CLEAN_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        # remove punctuation and extra spaces
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        return " ".join(cleaned.split())

    @classmethod
    def string_similarity(cls, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @classmethod
    def score_match(
        cls,
        target_track: Track,
        candidate_title: str,
        candidate_artists: List[str],
        candidate_duration: int,
        is_song_category: bool,
        tolerance_seconds: int = 7
    ) -> float:
        score = 0.0

        clean_target_title = cls.clean_title(target_track.title)
        clean_cand_title = cls.clean_title(candidate_title)

        # 1. Title Similarity (0 to 40 points)
        title_sim = cls.string_similarity(clean_target_title, clean_cand_title)
        score += title_sim * 40.0

        # Check if main title is directly inside candidate title
        if clean_target_title in clean_cand_title or clean_cand_title in clean_target_title:
            score += 5.0

        # 2. Artist Matching (0 to 30 points)
        target_artists = [a.lower().strip() for a in target_track.artists]
        cand_artists = [a.lower().strip() for a in candidate_artists]
        
        artist_matched = False
        for t_art in target_artists:
            for c_art in cand_artists:
                if t_art in c_art or c_art in t_art or cls.string_similarity(t_art, c_art) > 0.8:
                    artist_matched = True
                    break
            # Also check if target artist is mentioned directly in candidate title
            if not artist_matched and t_art in clean_cand_title:
                artist_matched = True

        if artist_matched:
            score += 25.0
            # Extra points if primary artist is exact
            if target_artists and cand_artists and cls.string_similarity(target_artists[0], cand_artists[0]) > 0.85:
                score += 5.0

        # 3. Duration Proximity (0 to 20 points)
        if target_track.duration_seconds > 0 and candidate_duration > 0:
            diff = abs(target_track.duration_seconds - candidate_duration)
            if diff <= 2:
                score += 20.0
            elif diff <= 4:
                score += 15.0
            elif diff <= tolerance_seconds:
                score += 10.0
            elif diff > 15:
                # Heavy penalty for big duration difference (prevents 10-minute cuts, podcasts, 1-hour loops)
                score -= 35.0

        # 4. Category/Type Bonus (0 to 10 points)
        if is_song_category:
            score += 10.0

        return max(0.0, min(100.0, score))
