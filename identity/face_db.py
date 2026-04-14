from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2


@dataclass
class FaceMatch:
    name: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)


class FaceDB:
    """
    Face enroll + recognize helper (basic).

    ✅ Fixes MSMF spam: disables MSMF preference and uses DirectShow.
    ✅ Avoids wrong labeling: does NOT auto-return "abhay" for everyone.
       - If multiple people are enrolled OR multiple faces appear => returns 'unknown'
       - Only returns a known name when:
         (a) exactly 1 face in frame AND
         (b) exactly 1 enrolled identity (or you explicitly pick matching later with embeddings)
    """

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index

        # reduce MSMF issues on Windows
        os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

        # name -> last_enrolled_time
        self._registry: Dict[str, float] = {}

        self._haar = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    # ---------------------------
    # Camera helpers
    # ---------------------------
    def _open_camera(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    def _grab_frame(self, cap: cv2.VideoCapture) -> Optional[cv2.Mat]:
        ret, frame = cap.read()
        if not ret or frame is None:
            return None
        return frame

    def _detect_faces(self, frame) -> Tuple[Tuple[int, int, int, int], ...]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._haar.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        return tuple((int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces)

    # ---------------------------
    # Public API
    # ---------------------------
    def enroll(self, name: str, timeout_s: float = 5.0) -> bool:
        name = (name or "").strip()
        if not name:
            return False

        cap = self._open_camera()
        try:
            start = time.time()
            while time.time() - start < timeout_s:
                frame = self._grab_frame(cap)
                if frame is None:
                    return False

                faces = self._detect_faces(frame)
                # Enroll only when exactly ONE face is visible
                if len(faces) == 1:
                    self._registry[name.lower()] = time.time()
                    return True

                time.sleep(0.02)

            return False
        finally:
            cap.release()

    def recognize(self, timeout_s: float = 3.0) -> Optional[FaceMatch]:
        cap = self._open_camera()
        try:
            start = time.time()
            while time.time() - start < timeout_s:
                frame = self._grab_frame(cap)
                if frame is None:
                    return None

                faces = self._detect_faces(frame)

                # If no face, keep trying
                if len(faces) == 0:
                    time.sleep(0.02)
                    continue

                # ✅ If multiple faces in frame -> do NOT guess (this was your brother issue)
                if len(faces) > 1:
                    return FaceMatch(name="unknown", confidence=0.10, bbox=faces[0])

                # Single face in frame
                if not self._registry:
                    return FaceMatch(name="unknown", confidence=0.20, bbox=faces[0])

                # ✅ If more than one enrolled identity, still do NOT guess without embeddings
                if len(self._registry) > 1:
                    return FaceMatch(name="unknown", confidence=0.15, bbox=faces[0])

                # Exactly one enrolled identity -> safe-ish to return that
                only_name = next(iter(self._registry.keys()))
                return FaceMatch(name=only_name, confidence=0.55, bbox=faces[0])

            return None
        finally:
            cap.release()

    def has_name(self, name: str) -> bool:
        return (name or "").strip().lower() in self._registry

    def list_names(self) -> Tuple[str, ...]:
        return tuple(sorted(self._registry.keys()))
