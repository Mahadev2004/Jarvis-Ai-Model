# skills/screen_tools.py

from pathlib import Path
import tempfile

import mss
from PIL import Image
import pytesseract

from config import BASE_DIR

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# If Tesseract is not in PATH, set full path here, e.g.:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def capture_screen() -> str:
    """Take a full-screen screenshot and return image path."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        img = sct.grab(monitor)

        img_path = SCREENSHOTS_DIR / "screenshot_latest.png"
        Image.frombytes("RGB", img.size, img.rgb).save(img_path)

    return str(img_path)


def ocr_image(image_path: str) -> str:
    """Extract text from a given image using Tesseract OCR."""
    try:
        img = Image.open(image_path)
    except Exception as e:
        return f"Screen image open nahi ho paya: {e}"

    try:
        text = pytesseract.image_to_string(img, lang="eng+hin")
    except Exception as e:
        return f"OCR run karte waqt error aaya: {e}"

    text = text.strip()
    if not text:
        return "Screen par kuch clear text nahi mila. Shayad image ya video hoga."

    return text


def read_screen_now() -> str:
    """Capture screen and OCR it."""
    img_path = capture_screen()
    text = ocr_image(img_path)

    # Limit spoken length
    if len(text) > 800:
        text = text[:800] + "... (baaki text bohot lamba hai, main chhota hissa padh raha hoon.)"

    return f"Screen se mujhe yeh text mila hai:\n{text}"
