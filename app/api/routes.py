import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings, YTMUSIC_AUTH_FILE
from app.providers.spotify_provider import SpotifyProvider
from app.providers.youtube_provider import YouTubeProvider
from app.core.transfer import TransferManager

router = APIRouter(prefix="/api")

spotify_provider = SpotifyProvider()
youtube_provider = YouTubeProvider()
transfer_manager = TransferManager(spotify_provider, youtube_provider)

class SettingsUpdateModel(BaseModel):
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    transfer_delay: Optional[float] = None
    duration_tolerance: Optional[int] = None
    batch_size: Optional[int] = None

class YouTubeHeadersModel(BaseModel):
    headers_raw: str

class PlaylistPreviewModel(BaseModel):
    url: str

class TransferStartModel(BaseModel):
    url: str
    custom_name: Optional[str] = None
    is_private: bool = True

@router.get("/status")
def get_status() -> Dict[str, Any]:
    spotify_auth = spotify_provider.is_authenticated()
    user_logged_in = spotify_provider.is_user_authenticated()
    user_name = spotify_provider.get_user_display_name()
    yt_auth = youtube_provider.is_authenticated()
    yt_account = youtube_provider.get_account_details() if yt_auth else None

    return {
        "spotify": {
            "connected": spotify_auth,
            "user_logged_in": user_logged_in,
            "user_name": user_name,
            "client_id": settings.spotify_client_id,
            "has_secret": bool(settings.spotify_client_secret)
        },
        "youtube": {
            "connected": yt_auth,
            "account": yt_account
        },
        "settings": {
            "transfer_delay": settings.transfer_delay,
            "duration_tolerance": settings.duration_tolerance,
            "batch_size": settings.batch_size
        }
    }

@router.get("/spotify/login")
def get_spotify_login_url() -> Dict[str, Any]:
    auth_url = spotify_provider.get_auth_url()
    if not auth_url:
        raise HTTPException(status_code=400, detail="Spotify Client ID and Secret are not set.")
    return {"url": auth_url}

@router.post("/settings")
def update_settings(data: SettingsUpdateModel) -> Dict[str, Any]:
    if data.spotify_client_id is not None:
        settings.spotify_client_id = data.spotify_client_id.strip()
    if data.spotify_client_secret is not None:
        settings.spotify_client_secret = data.spotify_client_secret.strip()
    if data.transfer_delay is not None:
        settings.transfer_delay = max(0.1, min(5.0, data.transfer_delay))
    if data.duration_tolerance is not None:
        settings.duration_tolerance = max(1, min(30, data.duration_tolerance))
    if data.batch_size is not None:
        settings.batch_size = max(5, min(100, data.batch_size))

    settings.save()
    spotify_provider.refresh_client()
    return {"success": True, "status": get_status()}

@router.post("/youtube/connect")
def connect_youtube(data: YouTubeHeadersModel) -> Dict[str, Any]:
    if not data.headers_raw.strip():
        raise HTTPException(status_code=400, detail="Please paste request headers.")

    res = youtube_provider.save_browser_headers(data.headers_raw)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Authentication failed."))
    
    return {"success": True, "account": res.get("account")}

@router.post("/youtube/disconnect")
def disconnect_youtube() -> Dict[str, Any]:
    if YTMUSIC_AUTH_FILE.exists():
        YTMUSIC_AUTH_FILE.unlink()
    youtube_provider.refresh_client()
    return {"success": True}

@router.post("/spotify/preview")
def preview_spotify_playlist(data: PlaylistPreviewModel) -> Dict[str, Any]:
    try:
        playlist = spotify_provider.get_playlist(data.url)
        tracks = spotify_provider.get_playlist_tracks(data.url)
        preview_tracks = [t.dict() for t in tracks[:15]]
        
        return {
            "success": True,
            "playlist": playlist.dict(),
            "preview_tracks": preview_tracks,
            "total_tracks": len(tracks)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfer/start")
async def start_transfer(data: TransferStartModel) -> Dict[str, Any]:
    if not youtube_provider.is_authenticated():
        raise HTTPException(status_code=400, detail="YouTube Music account is not connected. Please connect from Settings.")

    try:
        job_id = await transfer_manager.start_transfer(
            source_playlist_url=data.url,
            custom_target_name=data.custom_name,
            is_private=data.is_private
        )
        return {"success": True, "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/transfer/stream/{job_id}")
async def stream_transfer(job_id: str):
    job = transfer_manager.active_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Transfer job not found.")

    queue: asyncio.Queue = job["event_queue"]

    async def event_generator():
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=25.0)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") in ["finished", "error"]:
                    break
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
            except Exception:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/transfer/cancel/{job_id}")
def cancel_transfer(job_id: str) -> Dict[str, Any]:
    transfer_manager.cancel_job(job_id)
    return {"success": True}

@router.get("/history")
def get_history():
    return {"history": transfer_manager.get_history()}
