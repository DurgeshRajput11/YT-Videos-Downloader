import os
import re
import uuid
import json
import time
import shutil
import zipfile
import threading
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file, abort

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_ROOT = Path(os.environ.get("DOWNLOAD_DIR", BASE_DIR / "downloads"))
DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)

# This starter app uses in-memory job state. Deploy as one app instance/worker.
JOBS = {}
JOBS_LOCK = threading.Lock()

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtube-nocookie.com",
}


def is_youtube_url(value):
    try:
        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower()
        allowed = host in YOUTUBE_HOSTS or host.endswith(".youtube.com")
        return parsed.scheme == "https" and allowed
    except Exception:
        return False


def set_job(job_id, **kwargs):
    with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(kwargs)


def get_job(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        return dict(job) if job else None


def progress_hook(job_id):
    def hook(data):
        status = data.get("status")
        info = data.get("info_dict") or {}
        if status == "downloading":
            set_job(
                job_id,
                state="downloading",
                title=info.get("title", "Downloading"),
                percent=(data.get("_percent_str") or "").strip(),
                speed=(data.get("_speed_str") or "").strip(),
                eta=(data.get("_eta_str") or "").strip(),
            )
        elif status == "finished":
            set_job(
                job_id,
                state="processing",
                title=info.get("title", "Merging audio and video"),
                percent="100%",
                speed="",
                eta="",
            )
    return hook


def format_selector(quality):
    if quality == "best":
        return "bestvideo+bestaudio/best"
    min_height = int(quality)
    # Do not silently fall back below the selected minimum resolution.
    return (
        f"bestvideo[height>={min_height}]+bestaudio/"
        f"best[height>={min_height}]"
    )


def safe_job_dir(job_id):
    if not re.fullmatch(r"[a-f0-9]{32}", job_id):
        abort(404)
    path = DOWNLOAD_ROOT / job_id
    if not path.exists() or not path.is_dir():
        abort(404)
    return path


def get_video_files(folder):
    extensions = {".mp4", ".mkv", ".webm", ".mov"}
    return sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in extensions],
        key=lambda p: p.name.lower(),
    )


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/preview")
def preview():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not is_youtube_url(url):
        return jsonify(error="Enter a valid HTTPS YouTube video or playlist URL."), 400

    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        entries = info.get("entries")
        if entries is None:
            entries = [info]

        videos = []
        for index, item in enumerate(entries, start=1):
            if not item:
                continue
            videos.append({
                "index": item.get("playlist_index") or index,
                "title": item.get("title") or item.get("id") or "Untitled video",
                "duration": item.get("duration"),
                "url": item.get("url") or item.get("webpage_url"),
            })

        return jsonify({
            "title": info.get("title") or "YouTube videos",
            "uploader": info.get("uploader") or info.get("channel") or "",
            "count": len(videos),
            "videos": videos,
        })
    except Exception as exc:
        return jsonify(error=f"Could not read playlist: {exc}"), 400


def download_worker(job_id, url, mode, selection, quality, package):
    job_dir = DOWNLOAD_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(job_dir / "%(playlist_index)03d - %(title).180B [%(id)s].%(ext)s")
    options = {
        "format": format_selector(quality),
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "noplaylist": mode == "single",
        "ignoreerrors": False,
        "quiet": True,
        "no_warnings": False,
        "retries": 10,
        "fragment_retries": 10,
        "continuedl": True,
        "overwrites": False,
        "progress_hooks": [progress_hook(job_id)],
    }

    if mode in {"range", "resume", "selected"}:
        options["playlist_items"] = selection

    set_job(job_id, state="starting", message="Starting download…")

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        files = get_video_files(job_dir)
        if not files:
            raise RuntimeError(
                "No videos were downloaded. Check whether the selected resolution "
                "exists and whether YouTube allowed the request."
            )

        if package == "zip":
            zip_path = job_dir / "playlist_downloads.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for file_path in files:
                    archive.write(file_path, arcname=file_path.name)

        set_job(
            job_id,
            state="complete",
            message=f"Completed: {len(files)} video(s).",
            file_count=len(files),
            files=[{"name": p.name, "size": p.stat().st_size} for p in files],
        )
    except Exception as exc:
        set_job(job_id, state="error", message=str(exc))


@app.post("/api/download")
def start_download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    mode = data.get("mode", "playlist")
    quality = str(data.get("quality", "1080"))
    package = data.get("package", "zip")
    selection = (data.get("selection") or "").strip()

    if not is_youtube_url(url):
        return jsonify(error="Enter a valid HTTPS YouTube URL."), 400
    if mode not in {"playlist", "single", "range", "resume", "selected"}:
        return jsonify(error="Invalid download mode."), 400
    if quality not in {"1080", "1440", "2160", "best"}:
        return jsonify(error="Invalid quality selection."), 400
    if package not in {"zip", "individual"}:
        return jsonify(error="Invalid output selection."), 400
    if mode in {"range", "resume", "selected"}:
        if not selection or not re.fullmatch(r"[0-9,\-\s]+", selection):
            return jsonify(error="Enter valid playlist item numbers, e.g. 1-5 or 1,3,7."), 400
        selection = re.sub(r"\s+", "", selection)

    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {
            "state": "queued",
            "message": "Queued",
            "percent": "",
            "speed": "",
            "eta": "",
            "title": "",
            "file_count": 0,
            "files": [],
        }

    thread = threading.Thread(
        target=download_worker,
        args=(job_id, url, mode, selection, quality, package),
        daemon=True,
    )
    thread.start()

    return jsonify(job_id=job_id), 202


@app.get("/api/status/<job_id>")
def job_status(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify(error="Job not found. The server may have restarted."), 404
    return jsonify(job)


@app.get("/download/<job_id>/zip")
def download_zip(job_id):
    folder = safe_job_dir(job_id)
    path = folder / "playlist_downloads.zip"
    if not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True, download_name="youtube_playlist.zip")


@app.get("/download/<job_id>/<int:file_index>")
def download_one(job_id, file_index):
    folder = safe_job_dir(job_id)
    files = get_video_files(folder)
    if file_index < 0 or file_index >= len(files):
        abort(404)
    path = files[file_index]
    return send_file(path, as_attachment=True, download_name=path.name)


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    # For local testing only. Use a production WSGI server when deploying.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
