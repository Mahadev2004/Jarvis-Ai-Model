# skills/desktop_control.py
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List

import psutil

# Optional (UI/window control)
try:
    import pygetwindow as gw
except Exception:
    gw = None

try:
    import pyautogui
except Exception:
    pyautogui = None


# ----------------------------
# Helpers
# ----------------------------

KNOWN_APP_ALIASES = {
    "brave": ["brave", "brave browser"],
    "chrome": ["chrome", "google chrome"],
    "edge": ["edge", "microsoft edge"],
    "firefox": ["firefox"],
    "notepad": ["notepad"],
    "calculator": ["calculator", "calc"],
    "explorer": ["explorer", "file explorer"],
    "cmd": ["cmd", "command prompt"],
    "powershell": ["powershell"],
    "vs code": ["code", "vscode", "vs code", "visual studio code"],
}


KNOWN_EXE_HINTS = {
    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "vscode": [
        r"C:\Program Files\Microsoft VS Code\Code.exe",
        r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
        r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    ],
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _expand(p: str) -> str:
    return os.path.expandvars(p)


def _is_probably_path(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    # drive path or UNC or contains slashes
    return bool(re.match(r"^[a-zA-Z]:\\", t)) or t.startswith("\\\\") or ("\\" in t) or ("/" in t)


def _windows_start_open(target: str) -> None:
    # Use cmd "start" to open apps/urls/files/folders
    # /D handles directory, quotes required
    subprocess.Popen(['cmd', '/c', 'start', '', target], shell=False)


def _try_startfile(target: str) -> bool:
    try:
        os.startfile(target)  # type: ignore[attr-defined]
        return True
    except Exception:
        return False


def _which_exe(name: str) -> Optional[str]:
    # try PATH
    if not name.lower().endswith(".exe"):
        name_exe = name + ".exe"
    else:
        name_exe = name
    p = shutil.which(name_exe)
    return p


def _guess_app_key(user_app: str) -> str:
    t = _norm(user_app)
    for key, aliases in KNOWN_APP_ALIASES.items():
        if t == key or t in aliases:
            return key
    # if "brave browser" etc.
    for key, aliases in KNOWN_APP_ALIASES.items():
        for a in aliases:
            if a in t:
                return key
    return t


def _find_exe_for_app(app_name: str) -> Optional[str]:
    """
    Best-effort exe resolver:
    1) known hints
    2) where.exe
    3) shutil.which
    """
    key = _guess_app_key(app_name)

    # 1) known hints
    if key in KNOWN_EXE_HINTS:
        for p in KNOWN_EXE_HINTS[key]:
            ep = _expand(p)
            if os.path.isfile(ep):
                return ep

    # 2) where.exe (works for PATH + registered)
    try:
        res = subprocess.run(
            ["where", key if key.endswith(".exe") else (key + ".exe")],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            line = (res.stdout.splitlines() or [""])[0].strip()
            if line and os.path.isfile(line):
                return line
    except Exception:
        pass

    # 3) PATH
    p = _which_exe(key)
    if p and os.path.isfile(p):
        return p

    return None


def _extract_after_keywords(text: str, keywords: List[str]) -> str:
    t = text.strip()
    low = t.lower()
    for kw in keywords:
        idx = low.find(kw)
        if idx != -1:
            return t[idx + len(kw) :].strip(" :,-")
    return t


def _get_active_window_title() -> Optional[str]:
    if gw is None:
        return None
    try:
        w = gw.getActiveWindow()
        if w:
            return (w.title or "").strip() or None
    except Exception:
        return None
    return None


def _find_windows_by_title_contains(q: str):
    if gw is None:
        return []
    qn = _norm(q)
    wins = []
    try:
        for w in gw.getAllWindows():
            title = _norm(w.title or "")
            if title and qn in title:
                wins.append(w)
    except Exception:
        return []
    return wins


def _close_windows_by_title_contains(q: str) -> int:
    wins = _find_windows_by_title_contains(q)
    closed = 0
    for w in wins:
        try:
            w.close()
            closed += 1
        except Exception:
            pass
    return closed


def _kill_processes_by_name(name: str) -> int:
    """
    Kill processes matching name (exe base match).
    """
    key = _guess_app_key(name)
    killed = 0
    # try kill by exact exe name
    targets = set()

    # If user said "brave", process is brave.exe
    targets.add(key if key.endswith(".exe") else f"{key}.exe")

    # also include alias exe guesses
    if key in ("brave", "chrome", "edge", "firefox", "vscode"):
        targets.add(f"{key}.exe")

    # psutil iterate
    for p in psutil.process_iter(["pid", "name"]):
        try:
            pname = (p.info.get("name") or "").lower()
            if pname in targets or any(pname == t.lower() for t in targets):
                p.terminate()
                killed += 1
        except Exception:
            pass

    # wait a bit then force kill if still alive
    if killed:
        try:
            gone, alive = psutil.wait_procs(
                [p for p in psutil.process_iter(["name"]) if (p.info.get("name") or "").lower() in {t.lower() for t in targets}],
                timeout=1.5,
            )
            for p in alive:
                try:
                    p.kill()
                except Exception:
                    pass
        except Exception:
            pass

    # fallback: taskkill (helps when psutil permissions fail)
    if killed == 0:
        try:
            for t in targets:
                subprocess.run(["taskkill", "/F", "/IM", t], capture_output=True, text=True)
                # can't know exact count reliably
        except Exception:
            pass

    return killed


# ----------------------------
# Main handler
# ----------------------------

def handle(text: str) -> str:
    """
    Desktop control:
    - open <app/folder/path>
    - close <app> / close active / close this
    - minimize / maximize / switch window
    """
    if not text or not text.strip():
        return "Kya open ya close karna hai?"

    raw = text.strip()
    t = _norm(raw)

    # ---- OPEN ----
    if t.startswith("open ") or t.startswith("launch ") or t.startswith("start ") or " open " in t or "launch " in t:
        target = _extract_after_keywords(raw, ["open", "launch", "start"])
        if not target:
            return "Kya open karna hai? App ya folder ka naam bolo."

        # If user spoke a path
        if _is_probably_path(target):
            path = target.replace("/", "\\")
            if os.path.isdir(path) or os.path.isfile(path):
                if _try_startfile(path):
                    return f"Open kar diya: {Path(path).name}"
                _windows_start_open(path)
                return f"Open kar diya: {Path(path).name}"
            # even if not exists, attempt open (maybe URL)
            try:
                _windows_start_open(target)
                return f"Open kar raha hoon: {target}"
            except Exception:
                return f"Mujhe yeh path nahi mila: {target}"

        # Known folders quick
        folder_map = {
            "downloads": str(Path.home() / "Downloads"),
            "documents": str(Path.home() / "Documents"),
            "desktop": str(Path.home() / "Desktop"),
            "pictures": str(Path.home() / "Pictures"),
            "videos": str(Path.home() / "Videos"),
        }
        key = _norm(target)
        for k, p in folder_map.items():
            if k in key and os.path.isdir(p):
                _try_startfile(p) or _windows_start_open(p)
                return f"{k.capitalize()} folder open kar diya."

        # Find exe
        exe = _find_exe_for_app(target)
        if exe:
            try:
                subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"{target} open kar diya."
            except Exception:
                # fallback to start
                try:
                    _windows_start_open(exe)
                    return f"{target} open kar diya."
                except Exception:
                    return f"{target} open karne me issue aa gaya."

        # Last fallback: Windows start with name
        try:
            _windows_start_open(target)
            return f"{target} open kar raha hoon."
        except Exception:
            return f"Main {target} ko open nahi kar paaya. App ka exact naam ya path bolo."

    # ---- CLOSE ----
    if t.startswith("close ") or t.startswith("band ") or " close " in t:
        # close active
        if any(x in t for x in ["close active", "close this", "close current", "isko band", "isko close", "active band"]):
            title = _get_active_window_title()
            if title:
                closed = _close_windows_by_title_contains(title)
                if closed:
                    return "Active window close kar di."
            # fallback alt+f4
            if pyautogui:
                try:
                    pyautogui.hotkey("alt", "f4")
                    return "Active window close kar di."
                except Exception:
                    pass
            return "Active window close nahi ho paayi."

        target = _extract_after_keywords(raw, ["close", "band", "quit", "exit"])
        if not target:
            return "Kis app ko close karna hai?"

        # First try close windows by title (graceful)
        closed_w = _close_windows_by_title_contains(target)
        if closed_w:
            return f"{target} close kar diya."

        # Then kill process
        killed = _kill_processes_by_name(target)
        if killed > 0:
            return f"{target} close kar diya."
        return f"Mujhe {target} close karne ke liye exact app name nahi mila."

    # ---- MINIMIZE / MAXIMIZE / SWITCH ----
    if any(w in t for w in ["minimize", "minimise", "small", "minim"]):
        if gw:
            try:
                w = gw.getActiveWindow()
                if w:
                    w.minimize()
                    return "Window minimize kar di."
            except Exception:
                pass
        if pyautogui:
            try:
                pyautogui.hotkey("win", "down")
                return "Window minimize kar di."
            except Exception:
                pass
        return "Window minimize nahi ho paayi."

    if "maximize" in t or "full screen" in t or "fullscreen" in t:
        if gw:
            try:
                w = gw.getActiveWindow()
                if w:
                    w.maximize()
                    return "Window maximize kar di."
            except Exception:
                pass
        if pyautogui:
            try:
                pyautogui.hotkey("win", "up")
                return "Window maximize kar di."
            except Exception:
                pass
        return "Window maximize nahi ho paayi."

    if any(w in t for w in ["switch", "next window", "tab change", "window change", "alt tab"]):
        if pyautogui:
            try:
                pyautogui.hotkey("alt", "tab")
                return "Window switch kar di."
            except Exception:
                pass
        return "Window switch nahi ho paayi."

    # fallback
    return "Desktop control me yeh command match nahi hui. Try: open/close/minimize/maximize."
