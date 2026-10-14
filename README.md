# 🎵 MusiConnect

A modern web application to synchronize and transfer your Spotify playlists to YouTube Music with zero track limits and accurate track matching.

---

## ✨ Features

- **Unlimited Transfers (Quota Friendly):** Bypasses the strict 66-tracks/day quota limit of the official YouTube Data API by leveraging `ytmusicapi` to transfer playlists of 100, 500, or 1,000+ tracks seamlessly.
- **Smart Track Matching:**
  - Automatically cleans unnecessary video noise (e.g., `Official Video`, `Remastered`, `Lyrics`, `Visualizer`).
  - Strict duration validation (default ±7s tolerance) to eliminate 1-hour loops, interviews, podcasts, and extended live cuts.
  - Prioritizes official label uploads in the YouTube Music "Songs" category.
- **Batch Processing & Rate-Limit Safeguards:** Adds songs to YouTube playlists in batches of 25 with polite delay intervals to prevent server throttling.
- **Live Real-time Progress Bar:** Watch the live transfer status, matching scores, added tracks, and skipped items in real-time.
- **Extensible Architecture:** Designed with `BaseMusicProvider` abstraction to support other platforms (such as Apple Music or Deezer) in the future.

---

## 🚀 Quick Start

### 1. Launching the App
Double-click `start.bat` or run from your terminal:

```powershell
py run.py
```

Your browser will automatically open at `http://127.0.0.1:8000`.

---

## 🔑 Authentication Setup

### 1. Spotify Connection
1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and sign in.
2. Click **Create app** (you can name it `MusiConnect`).
3. Set Redirect URI to `http://127.0.0.1:8000/callback` and select **Web API**.
4. In your app's **Settings**, copy your **Client ID** and **Client Secret**.
5. Paste them into the **Connections & Settings** tab in MusiConnect, then click **Log in with Spotify (Authorize)**.

### 2. YouTube Music Connection
1. Open [music.youtube.com](https://music.youtube.com) and ensure you are logged in to your Google/YouTube account.
2. Press **F12** to open Developer Tools and go to the **Network** tab (filter by `Fetch/XHR`).
3. Click on **Library** or refresh the page. Right-click the `browse` request.
4. Select **Copy ➔ Copy as cURL (bash)**.
5. Paste it into the YouTube Music box in MusiConnect and click **Connect & Verify**.

---

## 📁 Project Architecture

```text
MusiConnect/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   ├── base_provider.py
│   │   ├── matcher.py
│   │   └── transfer.py
│   ├── providers/
│   │   ├── spotify_provider.py
│   │   └── youtube_provider.py
│   └── static/
│       ├── index.html
│       ├── css/style.css
│       └── js/app.js
├── data/
├── requirements.txt
├── run.py
└── start.bat
```
