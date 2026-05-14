# -*- mode: python ; coding: utf-8 -*-
# Platform-aware spec — used by GitHub Actions on both macOS and Windows runners.
import os
import sys
import platform
import streamlit

STREAMLIT_PATH = os.path.dirname(streamlit.__file__)
IS_WIN = platform.system() == "Windows"

# ffmpeg binaries are downloaded into ./bin/ by the CI build script
FFMPEG = os.path.join("bin", "ffmpeg.exe" if IS_WIN else "ffmpeg")
FFPROBE = os.path.join("bin", "ffprobe.exe" if IS_WIN else "ffprobe")

binaries = []
if os.path.isfile(FFMPEG):
    binaries.append((FFMPEG, "bin"))
if os.path.isfile(FFPROBE):
    binaries.append((FFPROBE, "bin"))

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=binaries,
    datas=[
        (os.path.join(STREAMLIT_PATH, "static"), "streamlit/static"),
        (os.path.join(STREAMLIT_PATH, "runtime"), "streamlit/runtime"),
        (os.path.join(STREAMLIT_PATH, "components"), "streamlit/components"),
        ("app.py", "."),
        ("yt_downloader.py", "."),
        (".streamlit", ".streamlit"),
    ],
    hiddenimports=[
        "streamlit",
        "streamlit.web.bootstrap",
        "streamlit.web.cli",
        "streamlit.runtime.scriptrunner",
        "streamlit.runtime.caching",
        "streamlit.components.v1",
        "yt_dlp",
        "yt_dlp.extractor",
        "yt_dlp.extractor._extractors",
        "yt_dlp.postprocessor",
        "yt_dlp.downloader",
        "yt_dlp.utils",
        "altair",
        "pydeck",
        "pyarrow",
        "click",
        "tornado",
        "packaging",
        "validators",
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

# macOS .app bundle only
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
