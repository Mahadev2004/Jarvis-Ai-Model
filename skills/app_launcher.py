
# skills/app_launcher.py
from __future__ import annotations
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict

@dataclass
class LaunchResult:
    ok: bool
    message: str
    found_name: Optional[str] = None
    command: Optional[List[str]] = None

# Known winget IDs (best-effort). You can extend this list.
WINGET_IDS: Dict[str, str] = {
    "chrome": "Google.Chrome",
    "google chrome": "Google.Chrome",
    "brave": "Brave.Brave",
    "brave browser": "Brave.Brave",
    "firefox": "Mozilla.Firefox",
    "vlc": "VideoLAN.VLC",
    "whatsapp": "WhatsApp.WhatsApp",  # can vary; sometimes "9NKSQGP7F2NH" (Store)
    "discord": "Discord.Discord",
    "spotify": "Spotify.Spotify",
}

# Common aliases users speak
ALIASES: Dict[str, str] = {
    "yt": "youtube",
    "you tube": "youtube",
    "google": "chrome",
    "google chrome": "chrome",
    "brave browser": "brave",
}

def normalize_app_name(name: str) -> str:
    n = (name or "").strip().lower()
    n = re.sub(r"\s+", " ", n)
    return ALIASES.get(n, n)

def _start_menu_shortcut_dirs() -> List[Path]:
    dirs: List[Path] = []
    programdata = os.environ.get("ProgramData")
    appdata = os.environ.get("APPDATA")
    if programdata:
        dirs.append(Path(programdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    if appdata:
        dirs.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    return [d for d in dirs if d.exists()]

def _find_lnk_by_name(app_name: str) -> Optional[Path]:
    # Search Start Menu .lnk quickly
    targets = _start_menu_shortcut_dirs()
    app_tokens = set(app_name.split())
    for base in targets:
        for p in base.rglob("*.lnk"):
            stem = p.stem.lower()
            # loose match: all tokens present OR name contained
            if app_name in stem or all(t in stem for t in app_tokens if t):
                return p
    return None

def _resolve_lnk_target(lnk_path: Path) -> Optional[str]:
    # Use PowerShell COM to resolve .lnk target
    ps = f"""
    $s=(New-Object -COM WScript.Shell).CreateShortcut('{str(lnk_path)}');
    $s.TargetPath
    """
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        return out or None
    except Exception:
        return None

def _find_exe_in_app_paths(app_exe: str) -> Optional[str]:
    # Registry: HKLM/HKCU\Software\Microsoft\Windows\CurrentVersion\App Paths\<exe>
    # read via powershell (no external libs)
    ps = f"""
    $keys=@(
      'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{app_exe}',
      'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{app_exe}',
      'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{app_exe}'
    );
    foreach($k in $keys){{
      try {{
        $p=(Get-ItemProperty -Path $k -ErrorAction Stop).'(default)';
        if($p){{ Write-Output $p; break }}
      }} catch {{}}
    }}
    """
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        return out or None
    except Exception:
        return None

def find_launch_command(app_name: str) -> Optional[List[str]]:
    """
    Returns a command list suitable for subprocess.Popen, or None if not found.
    Strategy:
      1) Start Menu .lnk -> resolve target exe -> run exe
      2) Registry App Paths (common for chrome.exe, etc.)
      3) `where <exe>`
      4) fallback: `cmd /c start "" <app_name>` (works sometimes if registered)
    """
    n = normalize_app_name(app_name)

    # Special web targets
    if n == "youtube":
        return ["cmd", "/c", "start", "", "https://www.youtube.com"]

    # If user said "chrome", try exe names
    candidate_exes = []
    if n in ("chrome", "google chrome"):
        candidate_exes = ["chrome.exe"]
    elif n == "brave":
        candidate_exes = ["brave.exe"]
    elif n == "whatsapp":
        # WhatsApp desktop can be AppX; we'll still try start
        candidate_exes = ["WhatsApp.exe", "whatsapp.exe"]
    else:
        # generic: try "<name>.exe" if single token
        if " " not in n:
            candidate_exes = [f"{n}.exe"]
        else:
            candidate_exes = []

    # 1) Start Menu .lnk
    lnk = _find_lnk_by_name(n)
    if lnk:
        target = _resolve_lnk_target(lnk)
        if target and Path(target).exists():
            return [target]

    # 2) Registry App Paths
    for exe in candidate_exes:
        p = _find_exe_in_app_paths(exe)
        if p and Path(p).exists():
            return [p]

    # 3) where.exe
    for exe in candidate_exes:
        try:
            out = subprocess.check_output(["where", exe], text=True, stderr=subprocess.DEVNULL).splitlines()
            for line in out:
                line = line.strip()
                if line and Path(line).exists():
                    return [line]
        except Exception:
            pass

    # 4) Fallback start (registered app aliases)
    return ["cmd", "/c", "start", "", n]

def launch(app_name: str) -> LaunchResult:
    cmd = find_launch_command(app_name)
    if not cmd:
        return LaunchResult(False, f"'{app_name}' ka launch command nahi mila.")
    try:
        subprocess.Popen(cmd, close_fds=True)
        return LaunchResult(True, f"Opening {app_name}.", found_name=app_name, command=cmd)
    except Exception as e:
        return LaunchResult(False, f"{app_name} open karte waqt error: {e}", found_name=app_name, command=cmd)

def winget_available() -> bool:
    return shutil.which("winget") is not None

def install_with_winget(app_name: str) -> LaunchResult:
    n = normalize_app_name(app_name)
    if not winget_available():
        return LaunchResult(False, "Winget available nahi hai. (Windows App Installer missing)")
    pkg = WINGET_IDS.get(n)
    if not pkg:
        # Try winget search by name as fallback
        return LaunchResult(False, f"Is app ka winget id set nahi hai: {app_name}")

    # interactive agreement flags help reduce prompts; still UAC may appear.
    cmd = ["winget", "install", "--id", pkg, "-e", "--accept-source-agreements", "--accept-package-agreements"]
    try:
        subprocess.Popen(cmd, close_fds=True)
        return LaunchResult(True, f"Installing {app_name} via winget ({pkg}).", found_name=app_name, command=cmd)
    except Exception as e:
        return LaunchResult(False, f"Winget install error: {e}", found_name=app_name, command=cmd)
