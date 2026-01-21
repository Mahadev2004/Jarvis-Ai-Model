import re
from pathlib import Path

import requests

from config import DOWNLOAD_DIR, KNOWN_SOFTWARE_SOURCES


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name)


def detect_known_software(text: str):
    t = text.lower()
    for key, info in KNOWN_SOFTWARE_SOURCES.items():
        if key in t:
            return key, info
    return None, None


def download_file(url: str, suggested_name: str | None = None) -> str:
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    if not suggested_name:
        suggested_name = url.split("/")[-1] or "downloaded_file"
    safe_name = sanitize_filename(suggested_name)
    out_path = DOWNLOAD_DIR / safe_name

    print(f"⬇️ Downloading from {url} to {out_path}")

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return str(out_path)


def handle_download_intent(text: str) -> str:
    key, info = detect_known_software(text)
    if key and info:
        url = info["url"]
        name = info["name"]
        path = download_file(url, suggested_name=f"{key}_installer.exe")
        return f"I have downloaded {name} from its official source. File path: {path}"
    return (
        "No known safe software detected for auto-download. "
        "Try: 'download python', 'download vlc', 'download vs code', or 'download chrome'."
    )
