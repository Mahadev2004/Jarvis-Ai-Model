# =========================
# FILE: skills/tasks.py
# =========================

from __future__ import annotations

import subprocess
import shutil
import os
import re

try:
    import pyperclip
except ImportError:
    pyperclip = None


# -------------------------
# Helpers
# -------------------------

def _get_clipboard_text() -> str:
    """
    Clipboard se text nikaalta hai (agar pyperclip available ho).
    """
    if pyperclip is None:
        return ""
    try:
        return pyperclip.paste().strip()
    except Exception:
        return ""


def _looks_like_url(text: str) -> bool:
    return bool(re.search(r"https?://", text))


def _ensure_yt_dlp() -> bool:
    """
    Check karta hai yt-dlp available hai ya nahi
    """
    return shutil.which("yt-dlp") is not None


# -------------------------
# Main task handler
# -------------------------

def handle(text: str) -> str:
    """
    Tasks entry point (router yahin call karega)
    """
    t = text.lower()

    if not _ensure_yt_dlp():
        return (
            "yt-dlp install nahi hai. "
            "Pehle install karo: pip install -U yt-dlp"
        )

    # URL detection:
    url = ""

    # 1️⃣ Try clipboard first
    clip = _get_clipboard_text()
    if clip and _looks_like_url(clip):
        url = clip

    # 2️⃣ Try text itself
    if not url:
        words = text.split()
        for w in words:
            if _looks_like_url(w):
                url = w
                break

    if not url:
        return (
            "Mujhe koi video link nahi mila. "
            "Ya toh link clipboard mein copy karo "
            "ya command mein bolo."
        )

    # -------------------------
    # Decide format
    # -------------------------

    # Audio intent
    if any(k in t for k in ["audio", "mp3", "song", "gana"]):
        return _download_audio(url)

    # Default → video
    return _download_video(url)


# -------------------------
# Download functions
# -------------------------

def _download_audio(url: str) -> str:
    """
    YouTube se MP3 download
    """
    out_dir = "downloads/audio"
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format",
        "mp3",
        "-o",
        f"{out_dir}/%(title)s.%(ext)s",
        url,
    ]

    try:
        subprocess.Popen(cmd)
        return (
            "Audio download shuru kar diya hai. "
            "MP3 file downloads folder mein aa jayegi."
        )
    except Exception as e:
        return f"Audio download fail ho gaya: {e}"


def _download_video(url: str) -> str:
    """
    YouTube se best quality video download
    """
    out_dir = "downloads/video"
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-f",
        "bestvideo+bestaudio/best",
        "-o",
        f"{out_dir}/%(title)s.%(ext)s",
        url,
    ]

    try:
        subprocess.Popen(cmd)
        return (
            "Video download shuru kar diya hai. "
            "File downloads folder mein aa jayegi."
        )
    except Exception as e:
        return f"Video download fail ho gaya: {e}"


# =========================
# END OF skills/tasks.py
# =========================
