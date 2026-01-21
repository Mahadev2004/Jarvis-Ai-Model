import sounddevice as sd
import soundfile as sf


def record_wav(path: str, duration: int = 5, samplerate: int = 16000) -> str:
    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    sf.write(path, audio, samplerate)
    return path
