# skills/reader.py

from pathlib import Path
import PyPDF2

from config import BASE_DIR

BOOKS_DIR = BASE_DIR / "books"


def _list_books():
    BOOKS_DIR.mkdir(exist_ok=True)
    return list(BOOKS_DIR.glob("*.pdf")) + list(BOOKS_DIR.glob("*.txt"))


def _find_book(keyword: str):
    keyword = keyword.lower().strip()
    for f in _list_books():
        if keyword in f.stem.lower():
            return f
    return None


def read_book_snippet(text: str) -> str:
    # Try to extract a keyword after "read", "book", etc.
    t = text.lower()
    for w in ["read", "kitab", "book", "jarvis", "sakha", "please"]:
        t = t.replace(w, "")
    keyword = t.strip()

    if not keyword:
        # List available books
        books = _list_books()
        if not books:
            return "Books folder khaali hai. books/ mein PDF ya text files daalo."
        names = ", ".join(f.stem for f in books)
        return f"Kaunsi book padhni hai? Mere paas yeh books hain: {names}."

    BOOKS_DIR.mkdir(exist_ok=True)
    book_path = _find_book(keyword)

    if not book_path:
        return f"Mujhe '{keyword}' naam se koi book books folder mein nahi mili."

    if book_path.suffix.lower() == ".txt":
        data = book_path.read_text(encoding="utf-8", errors="ignore")
        snippet = data[:1500]
        return f"Main '{book_path.name}' se ek hissa padh raha hoon:\n{snippet}"

    if book_path.suffix.lower() == ".pdf":
        try:
            reader = PyPDF2.PdfReader(str(book_path))
            text_accum = ""
            # First 3 pages only, otherwise bohot lamba ho jayega
            for page in reader.pages[:3]:
                text_accum += page.extract_text() or ""
            snippet = (text_accum or "").strip()[:1500]
            if not snippet:
                return f"'{book_path.name}' se text extract nahi ho paya."
            return f"Main '{book_path.name}' ke first pages se hissa padh raha hoon:\n{snippet}"
        except Exception as e:
            return f"PDF padhte waqt error aaya: {e}"

    return f"'{book_path.name}' ka format abhi supported nahi hai."
