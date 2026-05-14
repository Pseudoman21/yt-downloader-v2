import streamlit as st
import os
import tempfile
import threading
from downloader import get_video_info, download_video, format_duration, format_views

st.set_page_config(
    page_title="YT Downloader",
    page_icon="▶",
    layout="centered",
)


@st.cache_resource
def _cookies_from_secrets():
    """Write cookies from Streamlit secrets to a temp file once per deployment."""
    cookies = st.secrets.get("YOUTUBE_COOKIES", "")
    if not cookies:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w")
    tmp.write(cookies)
    tmp.flush()
    return tmp.name


# --- Sidebar: manual cookie upload (overrides secrets if provided) ---
with st.sidebar:
    st.header("YouTube Cookies")
    st.markdown(
        "Cookies are required when running on a cloud server. "
        "Follow these steps to export and upload them:"
    )
    with st.expander("How to get cookies.txt", expanded=True):
        st.markdown(
            """
**Step 1 — Install the extension**
Install [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) on Chrome.

**Step 2 — Log in to YouTube**
Open [youtube.com](https://youtube.com) and make sure you are signed in to your Google account.

**Step 3 — Export the cookies**
Click the extension icon in the toolbar, then click **Export** (or "Export as .txt"). Save the file — it will be named something like `youtube.com_cookies.txt`.

**Step 4 — Upload below**
Click **Browse files** and select the file you just saved.
            """
        )
    cookie_file = st.file_uploader("Upload cookies.txt", type=["txt"])
    if cookie_file:
        st.success("Cookies loaded successfully.")

if "cookie_path" not in st.session_state:
    st.session_state.cookie_path = None

if cookie_file:
    if st.session_state.cookie_path is None or not os.path.exists(st.session_state.cookie_path):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="wb")
        tmp.write(cookie_file.read())
        tmp.flush()
        st.session_state.cookie_path = tmp.name

# Uploaded file takes priority; fall back to secrets
cookiefile = st.session_state.cookie_path or _cookies_from_secrets()

# --- Main UI ---
st.title("▶ YouTube Downloader")
st.caption("Paste a YouTube URL to download video or audio for free.")

url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "url" not in st.session_state:
    st.session_state.url = ""

if url:
    if st.button("Fetch Video Info", type="primary"):
        with st.spinner("Fetching video info..."):
            try:
                info = get_video_info(url, cookiefile=cookiefile)
                st.session_state.video_info = info
                st.session_state.url = url
            except Exception as e:
                st.error(f"Failed to fetch video info: {e}")
                st.session_state.video_info = None

info = st.session_state.get("video_info")

if info:
    col1, col2 = st.columns([1, 2])
    with col1:
        if info["thumbnail"]:
            st.image(info["thumbnail"], width=200)
    with col2:
        st.subheader(info["title"])
        st.write(f"**Channel:** {info['uploader']}")
        st.write(f"**Duration:** {format_duration(info['duration'])}")
        st.write(f"**Views:** {format_views(info['view_count'])}")

    st.divider()

    formats = info["formats"]
    format_labels = [f["label"] for f in formats]
    selected_label = st.selectbox("Select format", format_labels)
    selected_format = next(f for f in formats if f["label"] == selected_label)

    if st.button("Download", type="primary"):
        progress_bar = st.progress(0, text="Starting download...")

        progress_data = {"value": 0, "status": ""}

        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    progress_data["value"] = downloaded / total
                    speed = d.get("_speed_str", "")
                    eta = d.get("_eta_str", "")
                    progress_data["status"] = f"Downloading... {speed} | ETA: {eta}"
            elif d["status"] == "finished":
                progress_data["value"] = 1.0
                progress_data["status"] = "Processing..."

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = {"filepath": None, "error": None}

            def run_download():
                try:
                    result["filepath"] = download_video(
                        url or st.session_state.url,
                        selected_format["format_id"],
                        tmp_dir,
                        cookiefile=cookiefile,
                        progress_hook=progress_hook,
                    )
                except Exception as e:
                    result["error"] = str(e)

            thread = threading.Thread(target=run_download)
            thread.start()

            while thread.is_alive():
                progress_bar.progress(
                    min(progress_data["value"], 0.99),
                    text=progress_data["status"] or "Downloading...",
                )
                thread.join(timeout=0.5)

            thread.join()

            if result["error"]:
                st.error(f"Download failed: {result['error']}")
            elif result["filepath"] and os.path.exists(result["filepath"]):
                progress_bar.progress(1.0, text="Done!")
                filepath = result["filepath"]
                filename = os.path.basename(filepath)
                mime = "audio/mpeg" if filename.endswith(".mp3") else "video/mp4"

                with open(filepath, "rb") as f:
                    file_bytes = f.read()

                st.success("Download ready!")
                st.download_button(
                    label=f"Save {filename}",
                    data=file_bytes,
                    file_name=filename,
                    mime=mime,
                    type="primary",
                )
            else:
                st.error("Download completed but file not found.")

st.divider()
st.caption("Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) · Built with Streamlit")
