from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.routes import router as api_router

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="MusiConnect",
    description="Cross-platform playlist synchronization tool (Spotify to YouTube Music)",
    version="1.0.0"
)

# Enable CORS for future website integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def read_root():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/callback")
def spotify_oauth_callback(code: str):
    from app.api.routes import spotify_provider
    from fastapi.responses import HTMLResponse
    success = spotify_provider.handle_callback(code)
    msg = "🎉 Spotify Hesabınız Başarıyla Bağlandı!" if success else "❌ Giriş yapılırken bir sorun oluştu."
    return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <meta http-equiv="refresh" content="2;url=/" />
                <title>Spotify Bağlantısı</title>
                <style>
                    body {{ background: #090d16; color: #fff; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                    .box {{ text-align: center; background: rgba(255,255,255,0.05); padding: 2rem 3rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); }}
                    h2 {{ color: #1db954; margin-bottom: 0.5rem; }}
                </style>
            </head>
            <body>
                <div class="box">
                    <h2>{msg}</h2>
                    <p>MusiConnect uygulamasına yönlendiriliyorsunuz...</p>
                </div>
            </body>
        </html>
    """)

@app.get("/health")
def health():
    return {"status": "ok", "app": "MusiConnect"}
