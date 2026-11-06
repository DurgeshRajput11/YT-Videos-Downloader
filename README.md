# YouTube Playlist Downloader (Flask)

A small Flask web app with playlist preview, single video, full playlist, range,
resume-from-index, selected videos, quality selection, progress polling, and ZIP
or individual file downloads.

## Local run

1. Install Python 3.10+ and FFmpeg.
2. Install Deno (recommended by yt-dlp for YouTube JavaScript challenge support).
3. Run:

   ```bash
   python -m pip install -r requirements.txt
   python app.py
   ```

4. Open http://127.0.0.1:5000

## Deploy on Render

This repo includes `render.yaml`. Push the folder to a GitHub repository and
create a Render Blueprint from that repository, or create a Python web service
manually with:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --workers 1 --threads 4 --timeout 0 app:app`

Install FFmpeg and Deno in the deployment environment as well. The exact method
depends on the host; a Docker deployment is the most reliable way to bundle both.

## Important deployment notes

- This starter uses in-memory job state and is designed for one app instance and
  one Gunicorn worker. Do not scale horizontally without moving job state to
  Redis/a database and downloads to shared object storage.
- Many free hosting plans have ephemeral filesystems, strict CPU/RAM/time limits,
  or disallow long-running downloads. Use a host and plan that permit this workload.
- Downloaded files are stored under `downloads/<job-id>`. Add a cleanup policy
  before making the service public; old downloads consume disk.
- Add authentication, rate limiting, per-user quotas, and automatic cleanup before
  public deployment. An unrestricted public downloader can be abused and generate
  significant bandwidth/storage costs.
- The app only accepts HTTPS YouTube URLs, but you should still deploy behind a
  reputable host and keep dependencies updated.
- The selected 1080p/1440p/2160p option is a minimum resolution. Videos that do
  not offer that resolution are skipped. "Best available" does not enforce a
  minimum.
- YouTube may return HTTP 403 or restrict formats. Deno, FFmpeg, and current
  yt-dlp help with compatibility, but cannot guarantee every video will download.
- Use only for content you own or are authorized to download, and comply with
  applicable platform terms and copyright law.
