# utils/clipboard.py
from __future__ import annotations

def get_clipboard_text() -> str:
    """
    Returns clipboard text using 'pyperclip' if available.
    """
    try:
        import pyperclip  # type: ignore
        txt = pyperclip.paste()
        return (txt or "").strip()
    except Exception:
        return ""
