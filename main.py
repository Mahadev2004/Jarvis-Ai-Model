from __future__ import annotations

import inspect
import re
import time

from stt.whisper_cpp import WhisperSTT
from brain.llm_offline import BrainLLM
from skills.router import IntentRouter
from tts.tts_edge import SimpleTTS
from memory.background_learner import BackgroundLearner


EXIT_WORDS = {
    "quit",
    "exit",
    "band ho jao",
    "close yourself",
    "stop jarvis",
    "jarvis stop",
    "jarvis band ho jao",
    "jarvis exit",
    "jarvis quit",
}

WAKE_WORDS = {"jarvis", "jervis", "darvis", "derrish", "douglas"}  # common mishears


def _safe_listen_and_transcribe(stt: WhisperSTT):
    fn = stt.listen_and_transcribe
    try:
        sig = inspect.signature(fn)
    except Exception:
        sig = None

    if sig is None:
        return fn()

    params = sig.parameters
    if "duration" in params:
        return fn(duration=5)
    return fn()


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _has_wake_word(text: str) -> bool:
    t = _normalize(text)
    if not t:
        return False
    # if any wake word appears anywhere
    return any(w in t.split() for w in WAKE_WORDS) or any(w in t for w in WAKE_WORDS)


def _strip_all_wake_words(text: str) -> str:
    """
    Removes ALL wake words (not just first), fixes "Jarvis. Jarvis." -> empty.
    """
    t = (text or "").strip()
    if not t:
        return t

    low = t.lower()
    for w in WAKE_WORDS:
        # remove occurrences with word boundaries
        low = re.sub(rf"\b{re.escape(w)}\b", " ", low)

    # restore using lower-cleaned string (we don't need original casing)
    low = re.sub(r"[^\w\s-]", " ", low)
    low = re.sub(r"\s+", " ", low).strip()
    return low


def main():
    stt = WhisperSTT()
    brain = BrainLLM()
    router = IntentRouter()
    tts = SimpleTTS()

    # Background learner compatibility
    try:
        bg = BackgroundLearner(brain)
        if hasattr(bg, "start"):
            bg.start()
    except Exception:
        try:
            bg = BackgroundLearner()
            if hasattr(bg, "start"):
                bg.start()
        except Exception:
            pass

    print("🤖 Jarvis: Namaste, main Jarvis hoon, ready for your command.")
    print("Say wake word then command (e.g., 'Jarvis open brave'). Say 'quit' to exit.\n")

    while True:
        print("🎙️ Listening...")

        start_stt = time.time()
        try:
            user_text = _safe_listen_and_transcribe(stt)
        except Exception as e:
            print(f"[STT] Error: {e}")
            time.sleep(0.2)
            continue

        stt_latency = time.time() - start_stt
        clean = _normalize(user_text)

        # show exactly what STT heard
        if clean:
            print(f"🗣️ Heard: {user_text}  | stt={stt_latency:.2f}s")

        # blank transcript -> do nothing
        if not clean:
            time.sleep(0.12)
            continue

        # HARD EXIT works even without wake word
        if any(w in clean for w in EXIT_WORDS):
            print("🤖 Jarvis: Theek hai, exit kar raha hoon.")
            return

        # Wake gate
        if not _has_wake_word(user_text):
            print(f"[Wake] Wake word nahi mila → ignoring. | stt={stt_latency:.2f}s")
            continue

        # Remove ALL wake words
        command = _strip_all_wake_words(user_text)
        cmd_clean = _normalize(command)

        # Wake-only
        if not cmd_clean:
            tts.speak("Haan Abhay, bolo.")
            continue

        # route
        start_brain = time.time()
        try:
            reply = router.handle(cmd_clean, brain=brain)
        except Exception as e:
            reply = f"Sorry, ek error aaya: {e}"
        brain_latency = time.time() - start_brain

        print(f"[Latency] stt={stt_latency:.2f}s | brain/router={brain_latency:.2f}s")

        try:
            tts.speak(reply)
        except Exception as e:
            print(f"[TTS] Error: {e}")

        # drain job queue
        try:
            for msg in router.jobs.pop_done_messages():
                tts.speak(msg)
        except Exception:
            pass


if __name__ == "__main__":
    main()
