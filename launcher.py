import sys
import os
import threading
import webbrowser
import time


def _app_path():
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(__file__)
    return os.path.join(base, "app.py")


def _set_bundled_ffmpeg():
    """Point yt-dlp to the ffmpeg bundled inside the executable."""
    if not getattr(sys, "frozen", False):
        return
    bin_dir = os.path.join(sys._MEIPASS, "bin")
    # Prepend to PATH so yt-dlp and ffmpeg both find it
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    os.environ["FFMPEG_LOCATION"] = bin_dir


def _open_browser():
    time.sleep(3)
    webbrowser.open("http://localhost:8501")


def main():
    _set_bundled_ffmpeg()

    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    threading.Thread(target=_open_browser, daemon=True).start()

    from streamlit.web.bootstrap import run
    run(_app_path(), command_line="", args=[], flag_options={})


if __name__ == "__main__":
    main()
