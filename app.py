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
                info = get_video_info(url)
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
            st.image(info["thumbnail"], use_container_width=True)
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
        status_text = st.empty()

        progress_data = {"value": 0, "status": ""}

        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    pct = downloaded / total
                    progress_data["value"] = pct
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
