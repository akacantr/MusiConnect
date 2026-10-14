import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.core.base_provider import Track, Playlist, SearchResult
from app.providers.spotify_provider import SpotifyProvider
from app.providers.youtube_provider import YouTubeProvider
from app.config import settings, HISTORY_FILE

class TransferItem(BaseModel):
    index: int
    source_track: Track
    matched_result: Optional[SearchResult] = None
    status: str = "pending"
    error: Optional[str] = None

class TransferJobState(BaseModel):
    job_id: str
    source_playlist_name: str
    source_playlist_id: str
    target_playlist_id: Optional[str] = None
    target_playlist_url: Optional[str] = None
    total_tracks: int = 0
    processed_count: int = 0
    added_count: int = 0
    failed_count: int = 0
    status: str = "idle"
    created_at: str = ""
    duration_seconds: float = 0.0

class TransferManager:
    def __init__(self, spotify_provider: SpotifyProvider, youtube_provider: YouTubeProvider):
        self.spotify = spotify_provider
        self.youtube = youtube_provider
        self.active_jobs: Dict[str, Dict[str, Any]] = {}

    def get_history(self) -> List[Dict[str, Any]]:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_to_history(self, record: Dict[str, Any]):
        history = self.get_history()
        history.insert(0, record)
        history = history[:50]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    async def start_transfer(
        self,
        source_playlist_url: str,
        custom_target_name: Optional[str] = None,
        is_private: bool = True
    ) -> str:
        job_id = str(uuid.uuid4())[:8]

        source_playlist = self.spotify.get_playlist(source_playlist_url)
        tracks = self.spotify.get_playlist_tracks(source_playlist_url)

        if not tracks:
            raise ValueError("No tracks found in the selected playlist.")

        target_name = custom_target_name.strip() if custom_target_name else source_playlist.name
        
        target_playlist_id = self.youtube.create_playlist(
            title=target_name,
            description=f"Transferred: {source_playlist.name} (MusiConnect)",
            is_private=is_private
        )
        target_playlist_url = f"https://music.youtube.com/playlist?list={target_playlist_id}"

        event_queue = asyncio.Queue()
        job_data = {
            "job_id": job_id,
            "source_playlist": source_playlist,
            "target_playlist_id": target_playlist_id,
            "target_playlist_url": target_playlist_url,
            "tracks": tracks,
            "items": [TransferItem(index=i+1, source_track=t) for i, t in enumerate(tracks)],
            "event_queue": event_queue,
            "cancel_requested": False,
            "status": "running",
            "start_time": time.time(),
            "processed": 0,
            "added": 0,
            "failed": 0,
        }
        self.active_jobs[job_id] = job_data

        asyncio.create_task(self._run_transfer_worker(job_id))
        return job_id

    async def _run_transfer_worker(self, job_id: str):
        job = self.active_jobs.get(job_id)
        if not job:
            return

        items: List[TransferItem] = job["items"]
        queue: asyncio.Queue = job["event_queue"]
        target_playlist_id: str = job["target_playlist_id"]
        delay: float = settings.transfer_delay
        tolerance: int = settings.duration_tolerance
        batch_size: int = settings.batch_size

        batch_video_ids: List[str] = []
        batch_items: List[TransferItem] = []

        await queue.put({
            "type": "start",
            "job_id": job_id,
            "total": len(items),
            "target_playlist_url": job["target_playlist_url"]
        })

        try:
            for item in items:
                if job.get("cancel_requested"):
                    item.status = "cancelled"
                    break

                search_res = self.youtube.search_track(item.source_track, tolerance_seconds=tolerance)
                job["processed"] += 1

                if search_res:
                    item.matched_result = search_res
                    item.status = "matched"
                    batch_video_ids.append(search_res.id)
                    batch_items.append(item)
                else:
                    item.status = "not_found"
                    item.error = "No suitable match found"
                    job["failed"] += 1

                await queue.put({
                    "type": "item_updated",
                    "item": item.dict(),
                    "processed": job["processed"],
                    "total": len(items),
                    "added": job["added"],
                    "failed": job["failed"]
                })

                if len(batch_video_ids) >= batch_size:
                    try:
                        self.youtube.add_tracks_to_playlist(target_playlist_id, batch_video_ids)
                        for bi in batch_items:
                            bi.status = "added"
                        job["added"] += len(batch_video_ids)
                        await queue.put({
                            "type": "batch_added",
                            "added_count": len(batch_video_ids),
                            "total_added": job["added"]
                        })
                    except Exception as e:
                        for bi in batch_items:
                            bi.status = "error"
                            bi.error = str(e)
                        job["failed"] += len(batch_video_ids)
                    
                    batch_video_ids = []
                    batch_items = []

                await asyncio.sleep(delay)

            if batch_video_ids and not job.get("cancel_requested"):
                try:
                    self.youtube.add_tracks_to_playlist(target_playlist_id, batch_video_ids)
                    for bi in batch_items:
                        bi.status = "added"
                    job["added"] += len(batch_video_ids)
                except Exception as e:
                    for bi in batch_items:
                        bi.status = "error"
                        bi.error = str(e)
                    job["failed"] += len(batch_video_ids)

            duration = round(time.time() - job["start_time"], 1)
            final_status = "cancelled" if job.get("cancel_requested") else "completed"
            job["status"] = final_status

            summary = {
                "job_id": job_id,
                "source_playlist_name": job["source_playlist"].name,
                "source_playlist_id": job["source_playlist"].id,
                "target_playlist_id": target_playlist_id,
                "target_playlist_url": job["target_playlist_url"],
                "total_tracks": len(items),
                "processed_count": job["processed"],
                "added_count": job["added"],
                "failed_count": job["failed"],
                "status": final_status,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": duration
            }

            self.save_to_history(summary)

            await queue.put({
                "type": "finished",
                "summary": summary
            })

        except Exception as e:
            job["status"] = "failed"
            await queue.put({
                "type": "error",
                "error": str(e)
            })

    def cancel_job(self, job_id: str):
        job = self.active_jobs.get(job_id)
        if job:
            job["cancel_requested"] = True
            job["status"] = "cancelling"
