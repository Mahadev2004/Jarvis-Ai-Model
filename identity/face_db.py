# identity/face_db.py

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, List

import cv2
import numpy as np


IDENTITY_DIR = Path(__file__).resolve().parent
MODEL_FILE = IDENTITY_DIR / "face_lbph.xml"
NAME_FILE = IDENTITY_DIR / "face_name.txt"


class FaceIdentityManager:
    """
    Simple OpenCV-based face identity (no dlib, no face_recognition).

    Limitations:
    - Best for ek primary user (Abhay).
    - Lighting, camera angle bohot matter karega.
    """

    def __init__(self):
        self.name: str = "Abhay"
        self.recognizer: Optional[cv2.face_LBPHFaceRecognizer] = None  # type: ignore
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._load_model()

    # ---------------- internal helpers ---------------- #

    def _ensure_lib(self) -> Optional[str]:
        if not hasattr(cv2, "face"):
            return (
                "Face recognition ke liye OpenCV ka 'contrib' module chahiye.\n"
                "PowerShell me yeh command chalao:\n"
                "  pip install opencv-contrib-python\n"
            )
        return None

    def _load_model(self) -> None:
        """Agar trained model / naam saved hai to load karo."""
        try:
            if MODEL_FILE.exists() and hasattr(cv2, "face"):
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(str(MODEL_FILE))
                print(f"[FaceID] Loaded LBPH model from {MODEL_FILE}")
            if NAME_FILE.exists():
                name = NAME_FILE.read_text(encoding="utf-8").strip()
                if name:
                    self.name = name
                    print(f"[FaceID] Loaded name: {self.name}")
        except Exception as e:
            print("[FaceID] Failed to load model:", e)
            self.recognizer = None

    def _save_model(self, name: str) -> None:
        try:
            if self.recognizer is not None:
                self.recognizer.write(str(MODEL_FILE))
                print(f"[FaceID] Saved LBPH model to {MODEL_FILE}")
            NAME_FILE.write_text(name.strip() or "Abhay", encoding="utf-8")
            print(f"[FaceID] Saved name: {name}")
        except Exception as e:
            print("[FaceID] Failed to save model:", e)

    # ---------------- PUBLIC: ENROLL ---------------- #

    def enroll_from_camera(
        self,
        name: str = "Abhay",
        camera_index: int = 0,
        num_samples: int = 15,
        timeout_sec: int = 30,
    ) -> str:
        """
        Webcam se multiple face samples lekar LBPH recognizer train karega.

        Steps:
        - Camera on karega
        - Tumhe center me dekhna hai, thoda head move kar sakte ho
        - 15 face crops lekar model train karega
        """

        lib_err = self._ensure_lib()
        if lib_err:
            return lib_err

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return "Camera open nahi ho raha, please webcam / permissions check karo."

        print("[FaceID] Enrolling Abhay's face. Please look at the camera...")

        samples: List[np.ndarray] = []
        labels: List[int] = []
        start = time.time()

        while len(samples) < num_samples and (time.time() - start) < timeout_sec:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(80, 80),
            )

            if len(faces) != 1:
                # ya to koi face nahi, ya multiple faces — skip
                continue

            (x, y, w, h) = faces[0]
            face_roi = gray[y : y + h, x : x + w]

            # thoda normalize size
            face_resized = cv2.resize(face_roi, (200, 200))
            samples.append(face_resized)
            labels.append(1)  # single identity label = 1

            print(f"[FaceID] Sample {len(samples)}/{num_samples} captured.")
            time.sleep(0.3)

        cap.release()

        if len(samples) < 5:
            return (
                "Mujhe tumhara face sufficient samples ke saath capture nahi ho paya. "
                "Light aur angle thoda better karke phir se try kar sakte ho."
            )

        # Train LBPH recognizer
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.train(samples, np.array(labels))
            self._save_model(name)
            self.name = name.strip() or "Abhay"
        except Exception as e:
            return f"Face model train karte waqt error aaya: {e}"

        return (
            f"Theek hai {self.name}, maine tumhara face register kar liya "
            f"({len(samples)} samples). Ab se camera pe tumhe pehchanne ki koshish karunga."
        )

    # ---------------- PUBLIC: RECOGNIZE ---------------- #

    def recognize_from_camera(
        self,
        camera_index: int = 0,
        timeout_sec: int = 15,
        threshold: float = 80.0,
    ) -> str:
        """
        Webcam se face dekh kar LBPH recognizer se predict karega.

        threshold: confidence (OpenCV LBPH me LOWER is better).
                   Typical: 50-80 range me threshold.
        """

        lib_err = self._ensure_lib()
        if lib_err:
            return lib_err

        if self.recognizer is None:
            return (
                "Abhi tak face model trained nahi hai. "
                "Pehle bolo: 'Jarvis, remember my face' taaki main tumhara face enroll kar saku."
            )

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return "Camera open nahi ho raha, please webcam / permissions check karo."

        print("[FaceID] Trying to recognize face from camera...")

        start = time.time()
        best_conf: Optional[float] = None

        while (time.time() - start) < timeout_sec:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(80, 80),
            )

            if not len(faces):
                continue

            # sirf first face consider karenge
            (x, y, w, h) = faces[0]
            face_roi = gray[y : y + h, x : x + w]
            face_resized = cv2.resize(face_roi, (200, 200))

            try:
                label, confidence = self.recognizer.predict(face_resized)
            except Exception as e:
                print("[FaceID] predict error:", e)
                continue

            print(f"[FaceID] label={label}, confidence={confidence:.2f} (thresh={threshold})")

            # LBPH me confidence jitna kam utna better
            if label == 1 and confidence <= threshold:
                best_conf = confidence
                break

        cap.release()

        if best_conf is None:
            return (
                "Mujhe camera pe tumhara face toh dikh raha hoga, "
                "lekin stored profile se confident match nahi mila. "
                "Light / angle thoda better karke dubara try kar sakte ho."
            )

        # Personalized message
        nm = self.name or "Abhay"
        if nm.lower() in ("abhay", "abhay pratap singh", "abhay singh"):
            return "Haan Abhay, main tumhe camera par clearly dekh sakta hoon. 👀"
        else:
            return f"Mujhe lagta hai tum {nm} ho. 👀 (confidence ~{best_conf:.1f})"
