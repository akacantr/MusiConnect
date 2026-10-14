import os
import sys
import time
import webbrowser
import threading
import uvicorn

def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"\n[MusiConnect] Tarayıcı açılıyor: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    print("=" * 60)
    print("🎵 MusiConnect - Spotify to YouTube Music Converter")
    print("=" * 60)
    print("Web sunucusu başlatılıyor: http://127.0.0.1:8000")
    print("Durdurmak için Ctrl+C tuşlarına basabilirsiniz.\n")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
