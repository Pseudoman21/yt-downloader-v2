import yt_dlp
import os
import shutil


def _ffmpeg_location():
    for candidate in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"):
        if os.path.isfile(candidate):
            return os.path.dirname(candidate)
    found = shutil.which("ffmpeg")
    return os.path.dirname(found) if found else None


_FFMPEG = _ffmpeg_location()


def _common(cookiefile=None):
    opts = {"quiet": True, "no_warnings": True}
    if _FFMPEG:
        opts["ffmpeg_location"] = _FFMPEG
    if cookiefile and os.path.isfile(cookiefile):
        opts["cookiefile"] = cookiefile
    return opts


def _info_opts(cookiefile=None):
    """For fetching metadata: web client with cookies unlocks full DASH format list."""
    has_cookies = bool(cookiefile and os.path.isfile(cookiefile))
    return {
        **_common(cookiefile),
        "skip_download": True,
        "extractor_args": {
            "youtube": {"player_client": ["web"] if has_cookies else ["android_vr"]}
        },
    }


def _download_opts(cookiefile=None):
    has_cookies = bool(cookiefile and os.path.isfile(cookiefile))
    return {
        **_common(cookiefile),
        # Let yt-dlp pick the best working client; cookies help authenticate
        "extractor_args": {
            "youtube": {"player_client": ["web", "android_vr"] if has_cookies else ["android_vr"]}
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.youtube.com/",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "geo_bypass": True,
    }


def get_video_info(url: str, cookiefile=None) -> dict:
    with yt_dlp.YoutubeDL(_info_opts(cookiefile)) as ydl:
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
    by_height = {}
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


def download_video(url: str, format_id: str, output_dir: str, cookiefile=None, progress_hook=None) -> str:
    is_audio = format_id == "bestaudio/best"

    opts = {
        **_download_opts(cookiefile),
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
