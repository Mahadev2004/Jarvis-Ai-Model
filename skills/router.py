from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict

from identity.face_db import FaceDB  # adjust import if your folder name differs


# -----------------------------
# Small async-ish message queue
# -----------------------------
@dataclass
class JobQueue:
    _done: List[str] = field(default_factory=list)

    def add_done(self, msg: str):
        if msg:
            self._done.append(msg)

    def pop_done_messages(self) -> List[str]:
        msgs = self._done[:]
        self._done.clear()
        return msgs


# -----------------------------
# App Launcher helpers
# -----------------------------
ALIASES: Dict[str, str] = {
    "brave browser": "brave",
    "google chrome": "chrome",
    "you tube": "youtube",
    "yt": "youtube",
}

FILLER_WORDS = {
    "app", "application", "software", "program", "browser", "desktop"
}

# If you want winget installs later:
WINGET_IDS: Dict[str, str] = {
    "chrome": "Google.Chrome",
    "brave": "Brave.Brave",
    "firefox": "Mozilla.Firefox",
    "vlc": "VideoLAN.VLC",
    "discord": "Discord.Discord",
    "spotify": "Spotify.Spotify",
    "whatsapp": "WhatsApp.WhatsApp",  # may vary depending on install source
}


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _normalize_app_name(app: str) -> str:
    a = _norm(app)
    a = ALIASES.get(a, a)

    # Remove punctuation
    a = re.sub(r"[^\w\s-]", " ", a)
    a = re.sub(r"\s+", " ", a).strip()

    # remove filler words
    parts = [p for p in a.split() if p not in FILLER_WORDS]
    a = " ".join(parts).strip()

    # common STT issue: "brave draws" / "brave browse" etc.
    # if starts with known app, keep the first token only
    if a.startswith("brave"):
        return "brave"
    if a.startswith("chrome"):
        return "chrome"
    if a.startswith("whatsapp"):
        return "whatsapp"
    if a.startswith("youtube"):
        return "youtube"

    return a


def _winget_ok() -> bool:
    return shutil.which("winget") is not None


def _winget_install(app: str) -> bool:
    app = _normalize_app_name(app)
    if not _winget_ok():
        return False
    pkg = WINGET_IDS.get(app)
    if not pkg:
        return False
    cmd = ["winget", "install", "--id", pkg, "-e", "--accept-source-agreements", "--accept-package-agreements"]
    try:
        subprocess.Popen(cmd, close_fds=True)
        return True
    except Exception:
        return False


def _powershell_startapps_launch(app_query: str) -> bool:
    """
    MOST reliable on Windows 11:
    - Finds matching app from Start menu database (Get-StartApps)
    - Launches via shell:AppsFolder\\AppID  (works for Store apps too)
    """
    q = app_query.replace('"', "").strip()
    if not q:
        return False

    ps = rf"""
    $q="{q}".ToLower();
    $hit = Get-StartApps | Where-Object {{ $_.Name -and $_.Name.ToLower().Contains($q) }} | Select-Object -First 1;
    if ($null -ne $hit -and $hit.AppID) {{
        Start-Process ("shell:AppsFolder\" + $hit.AppID);
        exit 0
    }} else {{
        exit 1
    }}
    """
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return r.returncode == 0
    except Exception:
        return False


def _cmd_start_fallback(arg: str) -> bool:
    """
    Fallback: start via cmd (sometimes works for registered apps/urls).
    """
    try:
        subprocess.Popen(["cmd", "/c", "start", "", arg], close_fds=True)
        return True
    except Exception:
        return False


def _open_url(url: str) -> bool:
    try:
        subprocess.Popen(["cmd", "/c", "start", "", url], close_fds=True)
        return True
    except Exception:
        return False


def _launch_app(app: str) -> bool:
    app = _normalize_app_name(app)
    if not app:
        return False

    # youtube special case
    if app == "youtube":
        return _open_url("https://www.youtube.com")

    # 1) Best: StartApps database
    if _powershell_startapps_launch(app):
        return True

    # 2) Try cmd start fallback
    return _cmd_start_fallback(app)


# -----------------------------
# Router
# -----------------------------
class IntentRouter:
    """
    Fixes:
    ✅ Vision priority above app open (so "open camera" won't become "file camera").
    ✅ App launching via Get-StartApps/AppID (works for WhatsApp store app too).
    ✅ Optional winget install flow.
    """

    def __init__(self):
        self.jobs = JobQueue()
        self.face_db = FaceDB(camera_index=0)

        self._pending_install_app: Optional[str] = None

    def detect_intent(self, text: str) -> str:
        t = _norm(text)

        # pending install confirmation
        if self._pending_install_app and t in {"yes", "haan", "han", "y", "ok", "kardo", "kar do", "install"}:
            return "install_yes"
        if self._pending_install_app and t in {"no", "nahin", "nahi", "mat", "cancel"}:
            return "install_no"

        # exit safety (main also checks)
        if any(w in t for w in ("exit", "quit", "band ho jao", "close")):
            return "exit"

        # ✅ Vision should be checked BEFORE app_open
        vision_keywords = ("camera", "cam", "face", "recognize", "detect", "enroll", "remember my face")
        if any(k in t for k in vision_keywords):
            return "vision"

        # WhatsApp messaging explicit
        if "whatsapp" in t and ("send" in t or "message" in t or "msg" in t):
            return "whatsapp_send"

        # app open
        if re.search(r"\b(open|start|launch)\b", t):
            return "app_open"

        return "chat"

    def handle(self, text: str, brain) -> str:
        t = _norm(text)
        intent = self.detect_intent(t)

        if intent == "exit":
            return "Theek hai, exit kar raha hoon."

        # -------------------------
        # install flow
        # -------------------------
        if intent == "install_yes":
            app = self._pending_install_app
            self._pending_install_app = None
            if not app:
                return "ठीक है."
            if not _winget_ok():
                return "Winget available nahi hai, main install nahi kar paunga."
            if _winget_install(app):
                return f"ठीक है, main {app} install kar raha hoon. Install ke baad bolo: 'Jarvis open {app}'."
            return "Install start nahi ho paya."

        if intent == "install_no":
            app = self._pending_install_app
            self._pending_install_app = None
            return f"ठीक है, {app} install nahi karta."

        # -------------------------
        # WhatsApp send (placeholder)
        # -------------------------
        if intent == "whatsapp_send":
            return "Main WhatsApp message send kar sakta hoon. Kisko aur kya message bhejna hai?"

        # -------------------------
        # Vision
        # -------------------------
        if intent == "vision":
            # enroll
            if "remember my face" in t or "enroll" in t:
                name = "abhay"
                mm = re.search(r"(?:remember my face|enroll)\s+(.*)$", t)
                if mm and mm.group(1).strip():
                    name = mm.group(1).strip()
                ok = self.face_db.enroll(name=name)
                return f"Face enroll ho gaya: {name}" if ok else "Face enroll nahi ho paya. Light/camera check karo."

            # recognize
            if "recognize" in t or "do you recognize" in t or "detect" in t:
                match = self.face_db.recognize()
                if not match:
                    return "Mujhe camera se clear face nahi mila."
                if match.name == "unknown":
                    return "Face dikh raha hai, par main sure nahi hoon kaun hai. Pehle 'remember my face <name>' bolo."
                return f"Main tumhe recognize kar raha hoon: {match.name}"

            # camera generic
            return (
                "Vision command samajh aayi. Try:\n"
                "- 'remember my face <name>'\n"
                "- 'do you recognize me'\n"
            )

        # -------------------------
        # App open
        # -------------------------
        if intent == "app_open":
            m = re.search(r"\b(open|start|launch)\b\s+(.*)$", t)
            app = (m.group(2).strip() if m else "").strip()
            app = _normalize_app_name(app)

            if not app:
                return "Kis app ko open karna hai? (e.g., 'open brave')"

            ok = _launch_app(app)
            if ok:
                return f"ठीक है, main {app} open kar raha hoon."

            # ask install if winget
            if _winget_ok():
                self._pending_install_app = app
                return f"Mujhe {app} nahi mila. Kya main isko install kar du? (haan / nahi)"
            return f"Mujhe {app} nahi mila."

        # -------------------------
        # Default chat (LLM)
        # -------------------------
        if hasattr(brain, "chat"):
            return brain.chat(text)
        if hasattr(brain, "respond"):
            return brain.respond(text)

        return "Sorry, brain module me chat/respond method nahi mili."
