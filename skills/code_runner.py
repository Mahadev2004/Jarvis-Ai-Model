# skills/code_runner.py

from __future__ import annotations

import re
import time
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Workspace root: project ke root se "workspace" folder
ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR / "workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = WORKSPACE_DIR / "last_code_path.txt"


# ----------------- Helpers: language detection ----------------- #

def _detect_language(text: str) -> str:
    """
    User ke command se target language guess.

    Returns: "python", "html", "javascript", "css", "txt"
    """
    t = text.lower()

    if any(kw in t for kw in ["flask", "fastapi", "django", "python", "py script", "py code", "python script"]):
        return "python"
    if any(kw in t for kw in ["html", "landing page", "frontend page", "web page", "portfolio page"]):
        return "html"
    if any(kw in t for kw in ["javascript", "node", "react", "js code"]):
        return "javascript"
    if "css" in t:
        return "css"

    # Default
    return "python"


def _language_extension(lang: str) -> str:
    lang = lang.lower()
    if lang == "python":
        return "py"
    if lang == "html":
        return "html"
    if lang == "javascript":
        return "js"
    if lang == "css":
        return "css"
    return "txt"


# ----------------- Helpers: code fences & prompts ----------------- #

def _clean_code_fences(text: str) -> str:
    """
    LLM kabhi kabhi ```python ... ``` style code block deta hai.
    Yeh function fences remove karke sirf pure code return karega.
    """
    fence_pattern = r"```(?:[a-zA-Z0-9_+-]+)?\s*(.*?)```"
    matches = re.findall(fence_pattern, text, flags=re.DOTALL)
    if matches:
        code = matches[0]
        return code.strip()

    return text.strip()


def _build_code_prompt(user_request: str, language: str) -> str:
    """
    BrainLLM ko code generate karne ke liye special instruction.
    """
    lang_name = language.capitalize()

    return (
        f"You are Jarvis, an expert {lang_name} developer.\n"
        f"User request:\n{user_request}\n\n"
        f"Task:\n"
        f"- Write a complete, working {lang_name} code file that satisfies the request.\n"
        f"- Focus on clarity, best practices, and readability.\n"
        f"- Do NOT add any explanation, comments, or markdown text outside the code.\n"
        f"- Do NOT wrap the code in triple backticks if possible.\n"
        f"- Only output the raw {lang_name} code."
    )


# ----------------- Helpers: track last generated file ----------------- #

def _save_last_code_path(path: Path) -> None:
    try:
        STATE_FILE.write_text(str(path), encoding="utf-8")
    except Exception as e:
        print("[code_runner] Warning: couldn't write STATE_FILE:", e)


def _load_last_code_path() -> Optional[Path]:
    try:
        if not STATE_FILE.exists():
            return None
        txt = STATE_FILE.read_text(encoding="utf-8").strip()
        if not txt:
            return None
        p = Path(txt)
        return p if p.exists() else None
    except Exception as e:
        print("[code_runner] Warning: couldn't read STATE_FILE:", e)
        return None


# ----------------- Run Python safely inside workspace ----------------- #

def _run_python_file(path: Path) -> str:
    """
    Python script ko run karke stdout/stderr capture karega.
    """
    try:
        # Just in case: ensure file under WORKSPACE_DIR
        try:
            path.relative_to(WORKSPACE_DIR)
        except Exception:
            return "Safety ke liye main sirf workspace ke andar wali Python files run karunga."

        cmd = [sys.executable, str(path)]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR),
            timeout=60,
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()

        msg_parts = []

        if out:
            msg_parts.append(f"Output:\n{out}")
        if err:
            msg_parts.append(f"Errors:\n{err}")

        if not msg_parts:
            return "Script successfully run ho gayi, lekin koi visible output nahi aaya."

        msg = "\n\n".join(msg_parts)

        # Thoda truncate taaki Jarvis ka jawab manageable rahe
        if len(msg) > 1500:
            msg = msg[:1500] + "\n\n[... output truncated ...]"

        return msg

    except subprocess.TimeoutExpired:
        return "Script run karte waqt timeout ho gaya (60 seconds se zyada lag gaye)."
    except Exception as e:
        return f"Script run karte waqt unexpected error aaya: {e}"


# ----------------- Main handler ----------------- #

def handle(text: str, brain=None) -> str:
    """
    High-level handler for code generation / execution.

    Examples (voice):

      - "Jarvis, ek Python script banao jo mera Downloads folder scan kare."
      - "Jarvis, ek Flask app bana do jisme /hello route 'Hello Abhay' return kare."
      - "Jarvis, ek simple HTML landing page generate karo mera portfolio ke liye."
      - "Jarvis, abhi jo code banaya tha usko run karo."
      - "Jarvis, is code ko execute karo."
    """
    if brain is None:
        return "Mere paas abhi coding ke liye brain object available nahi hai."

    t = text.lower()

    # -------- RUN MODE: "run/execute/chalao" type commands -------- #
    run_keywords = [
        "run", "execute", "chalao", "isko run karo", "isko chala do",
        "code run karo", "script run karo", "program run karo",
    ]
    if any(kw in t for kw in run_keywords):
        last_path = _load_last_code_path()
        if not last_path:
            return (
                "Abhi mere paas koi recent generated code file ka record nahi hai.\n"
                "Pehle mujhe bolo 'ek python script banao...' phir main usko run kar sakta hoon."
            )

        if last_path.suffix.lower() == ".py":
            result = _run_python_file(last_path)
            return (
                f"Thik hai Abhay, maine yeh Python file run kar di hai:\n"
                f"{last_path}\n\n"
                f"{result}"
            )
        else:
            # Non-Python: run directly nahi karenge, sirf info denge
            return (
                f"Last generated file Python script nahi hai, balki '{last_path.suffix}' type hai.\n"
                f"Path:\n{last_path}\n\n"
                f"Isko run karne ke bajaye tum browser/editor se open kar sakte ho."
            )

    # -------- GENERATE MODE: new code file banana -------- #
    language = _detect_language(text)
    ext = _language_extension(language)

    code_prompt = _build_code_prompt(text, language)

    history = [
        {"role": "user", "content": code_prompt}
    ]
    raw = brain.chat(history)
    code = _clean_code_fences(raw)

    if not code:
        return "Mujhe code generate karne mein thoda issue aaya. Thoda aur clear instruction do."

    ts = time.strftime("%Y%m%d_%H%M%S")
    base_name = f"jarvis_{language}_code_{ts}.{ext}"
    file_path = WORKSPACE_DIR / base_name

    try:
        file_path.write_text(code, encoding="utf-8")
        _save_last_code_path(file_path)
    except Exception as e:
        print("[code_runner] Error writing file:", e)
        return (
            "Code to generate ho gaya tha, lekin file likhte waqt error aaya. "
            "Console logs check karo."
        )

    return (
        f"Abhay, maine ek {language} code file generate kar di hai.\n"
        f"File path:\n{file_path}\n\n"
        f"Ab agar bolo 'Jarvis, is code ko run karo', to main is file ko Python se run karke "
        f"output bhi bata sakta hoon (agar yeh .py script hai)."
    )
