import requests


def _clean_question(text: str) -> str:
    t = text.strip()
    lower = t.lower()

    for w in [
        "jarvis",
        "sakha",
        "please",
        "can you",
        "could you",
        "tell me",
        "bolo",
        "batao",
        "batao na",
    ]:
        lower = lower.replace(w, "")

    lower = lower.strip()
    return lower or t


def _duckduckgo_instant_answer(query: str) -> str:
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "no_redirect": 1,
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return f"Internet se result laate waqt error aaya: {e}"

    text = data.get("AbstractText") or data.get("Abstract") or ""
    if not text and data.get("RelatedTopics"):
        first = data["RelatedTopics"][0]
        if isinstance(first, dict):
            text = first.get("Text", "")

    text = (text or "").strip()
    if not text:
        return f"Mujhe is query ke liye koi short summary nahi mili: {query}"

    return text


def answer_question(text: str) -> str:
    cleaned = _clean_question(text)
    summary = _duckduckgo_instant_answer(cleaned)
    return f"Internet ke hisaab se, {cleaned} ke baare mein yeh mila hai:\n{summary}"
