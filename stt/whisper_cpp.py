import tempfile

import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

from config import DEVICE


class WhisperSTT:
    """
    STT using faster-whisper (CTranslate2 backend).
    Works offline, supports Hindi + English, works on CPU and CUDA.
    """

    def __init__(self, lang: str = "auto", model_size: str = "small"):
        self.lang = lang

        device = DEVICE  # "cuda" if available else "cpu"
        # int8 is fine for both CPU and GPU, keeps memory usage low.
        compute_type = "int8"

        print(f"[faster-whisper] Loading model '{model_size}' on device '{device}'...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def record_to_wav(self, duration: int = 5, samplerate: int = 16000) -> str:
        print("🎙️ Listening...")
        audio = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio, samplerate)
        return tmp.name

    def transcribe_file(self, wav_path: str) -> str:
        # language=None → autodetect; else e.g. "hi" or "en"
        language = None if self.lang == "auto" else self.lang

        segments, info = self.model.transcribe(
            wav_path,
            language=language,
            beam_size=5,
        )

        texts = [seg.text for seg in segments]
        full_text = " ".join(texts).strip()
        return full_text

    def listen_and_transcribe(self, duration: int = 5) -> str:
        wav = self.record_to_wav(duration=duration)
        text = self.transcribe_file(wav)
        print(f"🗣️ You said: {text}")
        return text
