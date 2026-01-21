from . import system_control


def search_web(text: str) -> str:
    cleaned = text.lower()
    for w in ["search", "google", "on google", "internet pe", "on internet"]:
        cleaned = cleaned.replace(w, "")
    cleaned = cleaned.strip()
    return system_control.open_website(cleaned or text)
