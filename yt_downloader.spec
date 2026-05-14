# -*- mode: python ; coding: utf-8 -*-
import os
import platform
from PyInstaller.utils.hooks import collect_all, collect_data_files

IS_WIN = platform.system() == "Windows"

FFMPEG = os.path.join("bin", "ffmpeg.exe" if IS_WIN else "ffmpeg")
FFPROBE = os.path.join("bin", "ffprobe.exe" if IS_WIN else "ffprobe")

binaries = []
if os.path.isfile(FFMPEG):
    binaries.append((FFMPEG, "bin"))
if os.path.isfile(FFPROBE):
    binaries.append((FFPROBE, "bin"))

# collect_all properly includes data files, binaries, and hidden imports
ctk_datas, ctk_bins, ctk_hidden = collect_all("customtkinter")
ytdlp_datas, ytdlp_bins, ytdlp_hidden = collect_all("yt_dlp")

a = Analysis(
    ["gui.py"],
    pathex=["."],
    binaries=binaries + ctk_bins + ytdlp_bins,
    datas=ctk_datas + ytdlp_datas,
    hiddenimports=ctk_hidden + ytdlp_hidden + [
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "_tkinter",
        "PIL",
        "PIL._tkinter_finder",
        "PIL.Image",
        "PIL.ImageTk",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="YT Downloader",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="YT Downloader",
)

if not IS_WIN:
    app = BUNDLE(
        coll,
        name="YT Downloader.app",
        icon=None,
        bundle_identifier="com.ytdownloader.app",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
        },
    )
