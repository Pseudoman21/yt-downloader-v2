import yt_dlp
import os
import shutil


def _ffmpeg_location():
    # Homebrew on Apple Silicon puts ffmpeg in /opt/homebrew/bin
    for candidate in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"):
        if os.path.isfile(candidate):
            return os.path.dirname(candidate)
    return shutil.which("ffmpeg") and os.path.dirname(shutil.which("ffmpeg"))


_FFMPEG = _ffmpeg_location()

_YDL_BASE = {
    "quiet": True,
    "no_warnings": True,
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/112.0.0.0 Mobile Safari/537.36"
        ),
    },
    "extractor_args": {"youtube": {"player_client": ["android_vr"]}},
    **({"ffmpeg_location": _FFMPEG} if _FFMPEG else {}),
}


def get_video_info(url: str) -> dict:
    opts = {**_YDL_BASE, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "uploader": info.get("uploader", "Unknown"),
            "view_count": info.get("view_count", 0),
            "formats": _extract_formats(info.get("formats", [])),
        }


def _extract_formats(formats: list) -> list:
    # Group video-only or combined streams by height; prefer mp4 over webm
    by_height: dict = {}
    for f in formats:
        if f.get("vcodec", "none") == "none":
            continue
        height = f.get("height")
        if not height:
            continue
        ext = f.get("ext", "")
        existing = by_height.get(height)
        if existing is None or (ext == "mp4" and existing.get("ext") != "mp4"):
            by_height[height] = f

    result = []
    for height, f in sorted(by_height.items(), reverse=True):
        ext = f.get("ext", "mp4")
        result.append({
            "label": f"{height}p ({ext})",
            "format_id": f["format_id"],
            "height": height,
            "ext": ext,
            "type": "video",
        })

    result.append({
        "label": "Audio only (mp3)",
        "format_id": "bestaudio/best",
        "ext": "mp3",
        "type": "audio",
    })
    return result


def download_video(url: str, format_id: str, output_dir: str, progress_hook=None) -> str:
    is_audio = format_id == "bestaudio/best"

    opts = {
        **_YDL_BASE,
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
    }

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    if is_audio:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        # Merge specific video stream with best available audio
        opts["format"] = f"{format_id}+bestaudio[ext=m4a]/{format_id}+bestaudio/best"
        opts["merge_output_format"] = "mp4"

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if is_audio:
            filename = os.path.splitext(filename)[0] + ".mp3"
        return filename


def format_duration(seconds: int) -> str:
    if not seconds:
        return "Unknown"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_views(count: int) -> str:
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)
