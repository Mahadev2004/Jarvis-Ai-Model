# skills/dev_agent.py

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Optional


# Dev projects folder – project root ke andar banayenge
ROOT_DIR = Path(__file__).resolve().parents[1]
DEV_DIR = ROOT_DIR / "dev_projects"
DEV_DIR.mkdir(parents=True, exist_ok=True)


def _detect_language(text: str) -> str:
    """
    User ki command se expected language guess karne ki koshish.
    """
    t = text.lower()
    if "python" in t or "py script" in t:
        return "python"
    if "javascript" in t or "node" in t or "js" in t:
        return "javascript"
    if "html" in t or "website" in t or "webpage" in t:
        return "html"
    if "css" in t:
        return "css"
    if "c++" in t or "cpp" in t:
        return "cpp"
    if "java " in t or t.startswith("java"):
        return "java"
    # default
    return "python"


def _default_extension(lang: str) -> str:
    if lang == "python":
        return ".py"
    if lang == "javascript":
        return ".js"
    if lang == "html":
        return ".html"
    if lang == "css":
        return ".css"
    if lang == "cpp":
        return ".cpp"
    if lang == "java":
        return ".java"
    return ".txt"


def _slugify(text: str, max_len: int = 32) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        text = "project"
    return text[:max_len]


def _extract_code_from_llm(raw: str) -> str:
    """
    LLM output me se ``` blocks detect karke code nikalne ki koshish.
    Agar nahi mila to pura text hi code ki tarah treat karenge.
    """
    if "```" not in raw:
        return raw.strip()

    parts = raw.split("```")
    # odd indices pe content aata hai
    for i in range(1, len(parts), 2):
        block = parts[i]
        # agar language tag laga ho to pehla line skip
        lines = block.splitlines()
        if not lines:
            continue
        if lines[0].strip().startswith(("python", "py", "js", "javascript", "html", "css")):
            code = "\n".join(lines[1:])
        else:
            code = "\n".join(lines)
        code = code.strip()
        if code:
            return code

    return raw.strip()


def handle(text: str, brain) -> str:
    """
    High-level dev / coding agent.

    Example commands:
      - "Jarvis ek python script banao jo ek folder me sare images resize kare"
      - "Mere liye ek simple todo CLI app banao"
      - "ek basic responsive website ka code likho"

    :param text: user ka raw command
    :param brain: BrainLLM instance
    """
    if brain is None:
        return "Mere paas abhi coding ke liye brain instance nahi hai."

    if not text:
        return "Dev agent ko clear command nahi mili."

    lang = _detect_language(text)
    ext = _default_extension(lang)

    # Short description nikalne ke liye
    desc = text
    if len(desc) > 80:
        desc = desc[:80] + "..."

    slug = _slugify(desc)
    ts = int(time.time())
    filename = f"{slug}_{ts}{ext}"
    filepath = DEV_DIR / filename

    # LLM prompt
    system = (
        "You are a senior software engineer and code generator. "
        "Your job is to produce COMPLETE, ready-to-run code for the user's request. "
        "Do not ask follow-up questions unless absolutely necessary. "
        "Assume reasonable defaults when something is ambiguous. "
        "Use clear English comments. "
        "Return the code inside proper fenced code blocks.\n\n"
        f"Target language preference: {lang}.\n"
    )

    prompt = (
        f"{system}\n"
        f"User request:\n{text}\n\n"
        "Please provide the full code implementation. "
        "Avoid long explanations; comments in code are enough."
    )

    history = [{"role": "user", "content": prompt}]
    raw_reply = brain.chat(history)

    if not raw_reply:
        return "Dev agent se koi output nahi aaya, shayad internal error hua."

    code = _extract_code_from_llm(raw_reply)

    try:
        filepath.write_text(code, encoding="utf-8")
    except Exception as e:
        return (
            "Code generate ho gaya tha, lekin file save karte waqt error aa gaya:\n"
            f"{e}\n\n"
            "Generated code yeh raha:\n"
            f"{code[:2000]}"
        )

    rel_path = os.path.relpath(filepath, ROOT_DIR)
    return (
        f"Abhay, maine tumhari request ke liye code generate kar diya.\n\n"
        f"Language guess: {lang}\n"
        f"File: {filepath}\n"
        f"(Project-relative path: {rel_path})\n\n"
        "Agar chaho to main tumhe code ka overview bhi samjha sakta hoon."
    )
