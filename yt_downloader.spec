# -*- mode: python ; coding: utf-8 -*-
import os
import platform
import customtkinter

CTK_PATH = os.path.dirname(customtkinter.__file__)
IS_WIN = platform.system() == "Windows"

FFMPEG = os.path.join("bin", "ffmpeg.exe" if IS_WIN else "ffmpeg")
FFPROBE = os.path.join("bin", "ffprobe.exe" if IS_WIN else "ffprobe")

binaries = []
if os.path.isfile(FFMPEG):
    binaries.append((FFMPEG, "bin"))
if os.path.isfile(FFPROBE):
    binaries.append((FFPROBE, "bin"))

a = Analysis(
    ["gui.py"],
    pathex=["."],
    binaries=binaries,
    datas=[
        (CTK_PATH, "customtkinter"),
        ("yt_downloader.py", "."),
    ],
    hiddenimports=[
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        "yt_dlp",
        "yt_dlp.extractor",
        "yt_dlp.extractor._extractors",
        "yt_dlp.postprocessor",
        "yt_dlp.downloader",
        "yt_dlp.utils",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["streamlit"],
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
