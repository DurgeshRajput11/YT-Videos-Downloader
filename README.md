# YouTube Playlist Downloader

Flask web app with playlist preview, single-video and playlist modes, range/resume/selected-item downloads, quality selection, progress polling, and ZIP or individual downloads.

## Local development

Requirements: Python 3.10+, FFmpeg, and Deno (for yt-dlp JavaScript challenge support).

```bash
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Render deployment (Docker)

This repository uses Docker so FFmpeg and Deno are installed in the same runtime as the Flask app.

1. Push the repository to GitHub.
2. In Render, create a **Docker** web service for the repository (or create/sync a Blueprint from `render.yaml`).
3. Ensure the Dockerfile path is `./Dockerfile`.
4. Leave the Render Start Command empty so the Dockerfile `CMD` runs.
5. Deploy.

## Important limitations

- This is a single-instance starter app. Job state is kept in process memory; do not add multiple instances/workers without moving job state to shared storage.
- Render filesystems may be ephemeral. Files can disappear after restart/redeploy, and large downloads can exhaust disk space.
- Before opening this to the public, add rate limits, authentication or quotas, file-size/job limits, and automatic cleanup.
- Deno and FFmpeg improve compatibility but do not guarantee that every source is downloadable. Hosting providers' IPs may be restricted by source platforms; the app must not attempt to bypass access controls or verification.
- Use this app only for content you own or have permission to download, and follow the source platform's terms and applicable copyright law.
