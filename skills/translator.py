# skills/translator.py

from __future__ import annotations

from typing import Optional
import re


def _contains_devanagari(text: str) -> bool:
    """
    Check if text contains Devanagari (Hindi) characters.
    """
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return True
    return False


def _detect_target_language(text: str) -> str:
    """
    Detect kis language me translate karna hai.

    Returns:
      "hi" -> target Hindi
      "en" -> target English
    """
    t = text.lower()

    # Explicit hints
    if any(kw in t for kw in ["hindi me", "hindi mein", "in hindi", "to hindi"]):
        return "hi"
    if any(kw in t for kw in ["english me", "english mein", "in english", "to english"]):
        return "en"

    # If text itself Devanagari hai, to English me translate
    if _contains_devanagari(text):
        return "en"

    # Default: English source -> Hindi target
    return "hi"


def _extract_text_to_translate(text: str) -> str:
    """
    User command se woh part nikalne ki koshish jo actual text hai.

    Examples:
      "Jarvis, is line ka Hindi me translation batao: Gravity is important."
      -> "Gravity is important."

      "translate this to English: मैं आज बहुत खुश हूँ।"
      -> "मैं आज बहुत खुश हूँ।"
    """
    # Common patterns
    patterns = [
        r"translation batao[:\- ]*(.*)",
        r"translate this[:\- ]*(.*)",
        r"translate to [a-zA-Z ]+[:\- ]*(.*)",
        r"isko [a-zA-Z ]+ me bolo[:\- ]*(.*)",
        r"is line ka [a-zA-Z ]+ me[:\- ]*(.*)",
    ]

    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            candidate = m.group(1).strip()
            if candidate:
                return candidate

    # Fallback: remove leading trigger words
    triggers = [
        "jarvis",
        "please",
        "translate",
        "isko",
        "is line ka",
        "is sentence ka",
        "ka translation",
        "batao",
        "bolo",
    ]
    cleaned = text
    for tr in triggers:
        cleaned = re.sub(r"\b" + re.escape(tr) + r"\b", "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip(" :,-\n\t")


def _translate_with_brain(brain, src_text: str, target_lang: str) -> str:
    """
    BrainLLM ka use karke translation karna.

    target_lang:
      "hi" -> Hindi
      "en" -> English
    """
    if brain is None:
        return "Mere paas translation ke liye LLM brain available nahi hai."

    src_text = src_text.strip()
    if not src_text:
        return "Mujhe kya translate karna hai, woh clear nahi hua."

    if target_lang == "hi":
        target_name = "natural Hinglish/Hindi"
    else:
        target_name = "natural English"

    prompt = (
        f"Translate the following text into {target_name}.\n"
        f"- Keep the meaning accurate.\n"
        f"- Do NOT explain, only give the translated sentence.\n\n"
        f"Text:\n{src_text}"
    )

    history = [
        {"role": "user", "content": prompt}
    ]
    translated = brain.chat(history)
    return translated.strip()


def handle(text: str, brain=None) -> str:
    """
    High-level translation handler.

    Examples (voice/text):
      - "Jarvis, is line ka Hindi me translation batao: Gravity is the force that keeps us on Earth."
      - "translate this to English: मैं कल दिल्ली जा रहा हूँ।"
      - "isko Hindi me bolo: Machine learning is powerful."
      - "isko English me bolo: मुझे AI pasand hai."
    """
    # Decide target language
    target_lang = _detect_target_language(text)
    # Extract source text
    src = _extract_text_to_translate(text)

    if not src:
        return (
            "Mujhe kya translate karna hai, yeh clear nahi hua. "
            "Example: 'isko Hindi me bolo: Machine learning is powerful.'"
        )

    return _translate_with_brain(brain, src, target_lang)
