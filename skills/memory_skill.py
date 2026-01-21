# skills/memory_skill.py

from __future__ import annotations

from typing import Optional

from memory.memory_store import get_memory_store


def _clean_after_phrase(text: str, phrase: str) -> str:
    idx = text.lower().find(phrase)
    if idx == -1:
        return text.strip()
    cut = idx + len(phrase)
    return text[cut:].strip(" .:-").strip()


def handle_remember(text: str) -> str:
    """
    Explicit memory commands:
      - "remember that my favourite language is python"
      - "yaad rakhna ki mujhe dark theme pasand hai"
    """
    store = get_memory_store()
    t_low = text.lower()

    key_phrases = [
        "remember that",
        "remember this",
        "yaad rakhna ki",
        "yaad rakhna",
        "yaad rakh",
    ]

    content = text
    for p in key_phrases:
        if p in t_low:
            content = _clean_after_phrase(text, p)
            break

    if not content:
        return "Kya yaad rakhna hai, thoda clear bolna padega."

    store.add(
        text=content,
        category="fact",
        source="manual",
        tags=["manual_remember"],
    )
    return f"Theek hai, main yaad rakh lunga: {content}"


def handle_recall(limit: int = 15) -> str:
    """
    User ke baare me jo yaad hai wo summarize kara deta hai.
    """
    store = get_memory_store()
    items = store.last_n(limit)

    if not items:
        return "Abhi tak mere paas tumhare baare me koi khas memory nahi hai."

    lines = ["Mujhe tumhare baare me yeh cheezen yaad hain:"]
    for itm in items:
        lines.append(f"- ({itm.category}) {itm.text}")

    return "\n".join(lines)


def auto_learn_from_turn(user_text: str, reply: str, brain=None) -> None:
    """
    Simple auto-learning:
    - "my name is ..."
    - "mera naam ..."
    - "my favourite ... is ..."
    - "i like ..."
    - "i love ..."
    etc.
    """
    if not user_text:
        return

    store = get_memory_store()
    t = user_text.lower()

    # name
    if "my name is" in t or "mera naam" in t:
        store.add(
            text=user_text.strip(),
            category="fact",
            source="auto",
            tags=["name", "auto_learn"],
        )

    # favourites
    if "my favourite" in t or "my favorite" in t or "mera favourite" in t:
        store.add(
            text=user_text.strip(),
            category="preference",
            source="auto",
            tags=["favorite", "auto_learn"],
        )

    # likes
    if "i like" in t or "i love" in t or "mujhe pasand" in t or "mujhe acha lagta" in t:
        store.add(
            text=user_text.strip(),
            category="preference",
            source="auto",
            tags=["like", "auto_learn"],
        )

    # coding / study habits
    if "i code" in t or "coding" in t or "programming" in t or "padhta hoon" in t or "study" in t:
        store.add(
            text=user_text.strip(),
            category="habit",
            source="auto",
            tags=["work_habit", "auto_learn"],
        )


# Helper if router ever wants a generic handler
def handle(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in ["remember that", "remember this", "yaad rakh"]):
        return handle_remember(text)
    if "what do you remember about me" in t or "tum mere bare mein kya jante ho" in t:
        return handle_recall()
    return "Memory module ko yeh specific command samajh nahi aayi."
