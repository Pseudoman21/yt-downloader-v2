# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform
from PyInstaller.utils.hooks import collect_all

IS_WIN = platform.system() == "Windows"

FFMPEG  = os.path.join("bin", "ffmpeg.exe"  if IS_WIN else "ffmpeg")
FFPROBE = os.path.join("bin", "ffprobe.exe" if IS_WIN else "ffprobe")

binaries = []
if os.path.isfile(FFMPEG):  binaries.append((FFMPEG,  "bin"))
if os.path.isfile(FFPROBE): binaries.append((FFPROBE, "bin"))

ctk_datas,   ctk_bins,   ctk_hidden   = collect_all("customtkinter")
ytdlp_datas, ytdlp_bins, ytdlp_hidden = collect_all("yt_dlp")

# --- Explicitly collect tcl/tk data so _tk_data is populated on Windows ---
tk_datas = []
if IS_WIN:
    python_tcl = os.path.join(os.path.dirname(sys.executable), "tcl")
    if os.path.isdir(python_tcl):
        for item in os.listdir(python_tcl):
            full = os.path.join(python_tcl, item)
            if os.path.isdir(full):
                tk_datas.append((full, os.path.join("_tk_data", item)))

a = Analysis(
    ["gui.py"],
    pathex=["."],
    binaries=binaries + ctk_bins + ytdlp_bins,
    datas=ctk_datas + ytdlp_datas + tk_datas,
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
    runtime_hooks=["rthook_tkinter.py"],
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
