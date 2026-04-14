# stt/whisper_cpp.py
import tempfile
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
from config import DEVICE

class WhisperSTT:
    """
    STT using faster-whisper (CTranslate2).
    Fixes:
    - VAD enabled (vad_filter=True)
    - initial_prompt to bias "Jarvis" wake word
    - duration parameter supported
    """

    def __init__(self, lang: str = "auto", model_size: str = "base"):
        self.lang = lang
        device = DEVICE
        compute_type = "int8"
        print(f"[Whisper] Loading model '{model_size}' on device '{device}'...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def record_to_wav(self, duration: int = 6, samplerate: int = 16000) -> str:
        audio = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio, samplerate)
        return tmp.name

    def transcribe_file(self, wav_path: str) -> str:
        language = None if self.lang == "auto" else self.lang

        # Bias wake word + common commands
        prompt = "Jarvis. Hey Jarvis. Jarvis open. Jarvis close. Jarvis help."

        segments, _info = self.model.transcribe(
            wav_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 350},
            initial_prompt=prompt,
        )
        return " ".join(seg.text for seg in segments).strip()

    def listen_and_transcribe(self, duration: int = 6) -> str:
        wav = self.record_to_wav(duration=duration)
        return self.transcribe_file(wav)
