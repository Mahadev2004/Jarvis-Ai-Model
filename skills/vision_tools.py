# skills/vision_tools.py

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image
import mss
import pytesseract

from identity.face_db import FaceIdentityManager

# Global face identity manager
_FACE_MGR: Optional[FaceIdentityManager] = FaceIdentityManager()


# ---------------- SCREEN READING ---------------- #

def read_screen_now() -> str:
    """
    Current primary screen ka screenshot lekar OCR se text read karta hai.
    """
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.rgb)

        text = pytesseract.image_to_string(img, lang="eng")
        text = (text or "").strip()

        if not text:
            return "Screen par mujhe koi readable text clear nahi mila, shayad font ya background tricky hai."

        return f"Screen se mujhe yeh text mila hai:\n{text}"
    except Exception as e:
        return f"OCR run karte waqt error aaya: {e}"


# ---------------- CAMERA: FACE PRESENCE ---------------- #

def check_face_presence_from_camera(duration_seconds: int = 5) -> str:
    """
    Sirf itna check karta hai ki camera par koi face hai ya nahi.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Camera open nahi ho raha, please check webcam / permissions."

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    start = time.time()
    found = False

    while (time.time() - start) < duration_seconds:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        if len(faces) > 0:
            found = True
            break

    cap.release()

    if found:
        return "Camera par ek face dikh raha hai."
    else:
        return "Mujhe camera par koi clear face nahi dikh raha."


# ---------------- IMAGE ANALYSIS (FILE) ---------------- #

def analyze_image_file(path: str) -> str:
    """
    Local image file ko load karke simple analysis:
      - Agar face visible hai to count
      - OCR se kuch text ho to read
    """
    if not path:
        return "Kisi image ka path specify nahi kiya gaya."

    p = Path(path).expanduser()
    if not p.exists():
        return f"Image file nahi mili: {p}"

    img = cv2.imread(str(p))
    if img is None:
        return f"Image load nahi ho payi: {p}"

    msg_parts = []

    # Face detection
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        if len(faces) > 0:
            msg_parts.append(f"Image me mujhe {len(faces)} face(s) dikh rahe hain.")
        else:
            msg_parts.append("Image me mujhe koi clear face nahi dikha.")
    except Exception as e:
        msg_parts.append(f"Face detect karte waqt error aaya: {e}")

    # OCR
    try:
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        text = pytesseract.image_to_string(pil_img, lang="eng")
        text = (text or "").strip()
        if text:
            msg_parts.append("Image se mujhe yeh text mila hai:")
            msg_parts.append(text)
        else:
            msg_parts.append("Image me mujhe koi readable text nahi mila.")
    except Exception as e:
        msg_parts.append(f"OCR me error aaya: {e}")

    return "\n".join(msg_parts)


# ---------------- FACE IDENTITY (ENROLL + RECOGNIZE) ---------------- #

def enroll_my_face() -> str:
    """
    Default user (Abhay) ka face enroll karega.
    """
    if _FACE_MGR is None:
        return "Face identity manager initialize nahi ho paya."

    return _FACE_MGR.enroll_from_camera(name="Abhay")


def recognize_on_camera() -> str:
    """
    Camera se dekh kar try karega ki yeh Abhay hai ya koi aur registered profile.
    """
    if _FACE_MGR is None:
        return "Face identity manager initialize nahi ho paya."

    return _FACE_MGR.recognize_from_camera()


# ---------------- HIGH-LEVEL HANDLER ---------------- #

def handle(text: str) -> str:
    """
    Vision related high-level commands ka handler.
    Ye router se call hota hai jab intent == 'vision'.
    """

    if not text:
        return "Vision module ko command clear nahi aayi."

    t = text.lower().strip()

    # --- Face enroll commands ---
    if any(
        kw in t
        for kw in [
            "remember my face",
            "register my face",
            "meri shakal yaad kar",
            "meri shakal yaad rakh",
            "mera chehra yaad rakh",
            "mera face yaad rakh",
            "face register kar",
        ]
    ):
        return enroll_my_face()

    # --- Face recognize commands ---
    if any(
        kw in t
        for kw in [
            "who am i",
            "do you recognize me",
            "kya tum mujhe pehchante ho",
            "mera chehra pehchano",
            "dekho kaun hai",
            "do you see me",
        ]
    ):
        return recognize_on_camera()

    # --- Simple presence check / see someone on camera ---
    if any(
        kw in t
        for kw in [
            "see someone on camera",
            "camera par koi hai",
            "kya tumhe koi dikhta hai",
            "face detect",
            "check camera",
            "camera check karo",
        ]
    ):
        return check_face_presence_from_camera(duration_seconds=5)

    # --- Screen read (vision intent se bhi) ---
    if "screen" in t and any(
        w in t for w in ["read", "padh", "padho", "dekho", "dekh lo", "see"]
    ):
        return read_screen_now()

    # Fallback – generic message
    return (
        "Vision module ko yeh command thoda unclear lagi. "
        "Tum bol sakte ho:\n"
        "- 'remember my face' (face enroll)\n"
        "- 'do you recognize me' (face recognize)\n"
        "- 'see someone on camera' (face presence)\n"
        "- 'read the screen' (screen OCR)"
    )
