import subprocess
import webbrowser


def open_application(app_text: str) -> str:
    t = app_text.lower()

    if "chrome" in t:
        subprocess.Popen(["start", "chrome"], shell=True)
        return "Opening Google Chrome."

    if "notepad" in t:
        subprocess.Popen(["notepad"], shell=True)
        return "Opening Notepad."

    if "vs code" in t or "vscode" in t:
        subprocess.Popen(["code"], shell=True)
        return "Opening Visual Studio Code."

    if "explorer" in t or "file" in t or "folder" in t:
        subprocess.Popen(["explorer"], shell=True)
        return "Opening File Explorer."

    return "I don't know this application yet."


def open_website(query: str) -> str:
    query = query.strip()
    if query.startswith("http://") or query.startswith("https://"):
        url = query
    else:
        url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Opening browser for: {query}"
