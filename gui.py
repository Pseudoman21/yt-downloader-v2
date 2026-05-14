import customtkinter as ctk
import threading
import os
import sys
import tempfile
import urllib.request
from io import BytesIO
from PIL import Image, ImageTk

from yt_downloader import get_video_info, download_video, format_duration, format_views

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

RED = "#FF0000"
DARK = "#1a1a1a"
CARD = "#242424"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.geometry("600x680")
        self.resizable(False, False)
        self.configure(fg_color=DARK)

        self._video_info = None
        self._download_thread = None

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(self, text="▶  YouTube Downloader",
                              font=ctk.CTkFont(size=22, weight="bold"),
                              text_color="white")
        header.pack(pady=(24, 4))

        ctk.CTkLabel(self, text="Paste a YouTube URL and download for free",
                     font=ctk.CTkFont(size=12), text_color="#aaaaaa").pack()

        # URL row
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.pack(padx=24, pady=(18, 0), fill="x")

        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://www.youtube.com/watch?v=...",
                                      height=40, font=ctk.CTkFont(size=13))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.fetch_btn = ctk.CTkButton(url_frame, text="Fetch", width=90, height=40,
                                       fg_color=RED, hover_color="#cc0000",
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       command=self._on_fetch)
        self.fetch_btn.pack(side="left")

        # Info card (hidden until fetch)
        self.info_card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)

        # Thumbnail + metadata side by side
        top_row = ctk.CTkFrame(self.info_card, fg_color="transparent")
        top_row.pack(padx=16, pady=(16, 8), fill="x")

        self.thumb_label = ctk.CTkLabel(top_row, text="", width=120, height=68)
        self.thumb_label.pack(side="left", padx=(0, 14))

        meta = ctk.CTkFrame(top_row, fg_color="transparent")
        meta.pack(side="left", fill="both", expand=True)

        self.title_label = ctk.CTkLabel(meta, text="", font=ctk.CTkFont(size=13, weight="bold"),
                                        wraplength=360, justify="left", anchor="w")
        self.title_label.pack(fill="x")

        self.channel_label = ctk.CTkLabel(meta, text="", font=ctk.CTkFont(size=11),
                                          text_color="#aaaaaa", anchor="w")
        self.channel_label.pack(fill="x", pady=(2, 0))

        self.meta_label = ctk.CTkLabel(meta, text="", font=ctk.CTkFont(size=11),
                                       text_color="#aaaaaa", anchor="w")
        self.meta_label.pack(fill="x")

        ctk.CTkFrame(self.info_card, fg_color="#333333", height=1).pack(fill="x", padx=16)

        # Format row
        fmt_row = ctk.CTkFrame(self.info_card, fg_color="transparent")
        fmt_row.pack(padx=16, pady=12, fill="x")

        ctk.CTkLabel(fmt_row, text="Format:", font=ctk.CTkFont(size=13),
                     width=64, anchor="w").pack(side="left")

        self.format_menu = ctk.CTkOptionMenu(fmt_row, values=["—"],
                                              font=ctk.CTkFont(size=13),
                                              dynamic_resizing=False, width=300)
        self.format_menu.pack(side="left", padx=(4, 0))

        # Download button
        self.dl_btn = ctk.CTkButton(self.info_card, text="Download", height=42,
                                    fg_color=RED, hover_color="#cc0000",
                                    font=ctk.CTkFont(size=14, weight="bold"),
                                    command=self._on_download)
        self.dl_btn.pack(padx=16, pady=(0, 8), fill="x")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.info_card, height=8)
        self.progress_bar.set(0)
        self.progress_bar.pack(padx=16, pady=(0, 4), fill="x")

        self.progress_label = ctk.CTkLabel(self.info_card, text="",
                                           font=ctk.CTkFont(size=11),
                                           text_color="#aaaaaa")
        self.progress_label.pack(pady=(0, 14))

        # Status bar at bottom
        self.status = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12),
                                   text_color="#aaaaaa", wraplength=560)
        self.status.pack(pady=(12, 0), padx=24)

    # ------------------------------------------------------------------ #

    def _on_fetch(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self._set_status("Fetching video info...", color="#aaaaaa")
        self.fetch_btn.configure(state="disabled")
        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url):
        try:
            info = get_video_info(url)
            self.after(0, self._on_fetch_done, info)
        except Exception as e:
            self.after(0, self._set_status, f"Error: {e}", "#ff4444")
            self.after(0, lambda: self.fetch_btn.configure(state="normal"))

    def _on_fetch_done(self, info):
        self._video_info = info
        self.fetch_btn.configure(state="normal")

        self.title_label.configure(text=info["title"])
        self.channel_label.configure(text=f"Channel: {info['uploader']}")
        self.meta_label.configure(
            text=f"Duration: {format_duration(info['duration'])}   •   Views: {format_views(info['view_count'])}"
        )

        labels = [f["label"] for f in info["formats"]]
        self.format_menu.configure(values=labels)
        self.format_menu.set(labels[0])

        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self._set_status("", "#aaaaaa")

        self._load_thumbnail(info["thumbnail"])
        self.info_card.pack(padx=24, pady=(14, 0), fill="x")

    def _load_thumbnail(self, url):
        def _worker():
            try:
                with urllib.request.urlopen(url, timeout=5) as r:
                    data = r.read()
                img = Image.open(BytesIO(data)).resize((120, 68), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 68))
                self.after(0, self.thumb_label.configure, {"image": ctk_img})
            except Exception:
                pass
        threading.Thread(target=_worker, daemon=True).start()

    def _on_download(self):
        if not self._video_info:
            return
        selected = self.format_menu.get()
        fmt = next(f for f in self._video_info["formats"] if f["label"] == selected)
        url = self.url_entry.get().strip()

        self.dl_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting...")
        self._set_status("", "#aaaaaa")

        def _worker():
            try:
                out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(out_dir, exist_ok=True)

                prog = {}

                def hook(d):
                    if d["status"] == "downloading":
                        total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                        done = d.get("downloaded_bytes", 0)
                        if total:
                            prog["pct"] = done / total
                        prog["text"] = f"{d.get('_speed_str','').strip()}  ETA {d.get('_eta_str','').strip()}"
                        self.after(0, self._update_progress,
                                   min(prog.get("pct", 0), 0.99), prog.get("text", ""))
                    elif d["status"] == "finished":
                        self.after(0, self._update_progress, 0.99, "Processing…")

                path = download_video(url, fmt["format_id"], out_dir, progress_hook=hook)
                self.after(0, self._on_download_done, path)
            except Exception as e:
                self.after(0, self._on_download_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_progress(self, pct, text):
        self.progress_bar.set(pct)
        self.progress_label.configure(text=text)

    def _on_download_done(self, path):
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Done!")
        self.dl_btn.configure(state="normal")
        self._set_status(f"Saved to: {path}", "#44cc88")

    def _on_download_error(self, msg):
        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.dl_btn.configure(state="normal")
        self._set_status(f"Error: {msg}", "#ff4444")

    def _set_status(self, msg, color="#aaaaaa"):
        self.status.configure(text=msg, text_color=color)


if __name__ == "__main__":
    app = App()
    app.mainloop()
