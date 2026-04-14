# tts/tts_edge.py

from __future__ import annotations

import asyncio
import os
import tempfile
import threading
from typing import Optional

import edge_tts
import playsound


class SimpleTTS:
    """
    Edge TTS based text-to-speech.

    - Hindi + English dono ke liye suitable voices (Neerja / Madhur etc.)
    - main.py ke barge-in logic ke saath compatible:
        - speak(text, stt=None, enable_barge_in=True)  -> params accept karta hai
        - is_speaking() -> bool
        - stop()        -> speaking flag false (real audio stop har player me possible nahi)
    """

    def __init__(self, voice: str = "hi-IN-MadhurNeural"):
        # Default voice tum already MadhurNeural rakh chuke ho
        self.voice = voice
        self._speaking = False
        self._stop_flag = False
        self._lock = threading.Lock()
        self._current_thread: Optional[threading.Thread] = None

    # ------------- internal audio playback ------------ #

    def _play_audio(self, path: str):
        try:
            # playsound blocking hai, isliye isko alag thread me chala rahe hain
            playsound.playsound(path, block=True)
        except Exception as e:
            print("[TTS] playsound error:", e)
        finally:
            with self._lock:
                self._speaking = False
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    async def _speak_async(self, text: str):
        if not text:
            return

        # Agar pehle se bol raha hai aur tum fir se speak call kar do
        # to pehle wale ko logically stop mark kar dete hain
        with self._lock:
            self._stop_flag = False
            self._speaking = True

        # Temp file for MP3
        fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(tmp_path)
        except Exception as e:
            with self._lock:
                self._speaking = False
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            print("[TTS] edge-tts error:", e)
            return

        # Agar bolne se pehle hi stop flag set ho gaya
        with self._lock:
            if self._stop_flag:
                self._speaking = False
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass
                return

            # Start playback in separate thread
            t = threading.Thread(target=self._play_audio, args=(tmp_path,), daemon=True)
            self._current_thread = t
            t.start()

    # ------------- public API ------------ #

    def speak(self, text: str, stt=None, enable_barge_in: bool = False):
        """
        main.py isse call karta hai:
            tts.speak(reply, stt=stt, enable_barge_in=True)

        yahan stt / enable_barge_in ignore ho rahe hain, kyunki
        real barge-in logic main.py me hai (loop + is_speaking + stop).
        """
        try:
            asyncio.run(self._speak_async(text))
        except RuntimeError:
            # agar already event loop chal raha ho (rare case),
            # fallback thread me run kara sakte hain
            def _runner():
                asyncio.run(self._speak_async(text))

            threading.Thread(target=_runner, daemon=True).start()

    def is_speaking(self) -> bool:
        with self._lock:
            return self._speaking

    def stop(self):
        """
        Sirf logical stop:
        - _stop_flag = True  => next playback skip ho jayega
        - _speaking  = False => main.py ko lagega ki bolna band ho gaya

        NOTE: playsound 1.2.2 me beech me audio ko truly stop karna possible nahi hai
        without external player. Practical effect:
        - barge-in hone par hum next STT loop pe chale jaate hain,
          audio thoda sa background me bajta reh sakta hai, but control tumhare paas aa jaata hai.
        """
        with self._lock:
            self._stop_flag = True
            self._speaking = False
