# =========================
# FILE: config.py
# =========================

from pathlib import Path
import torch

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

WHISPER_CPP_EXE = r"C:\Abhay\jarvis_assistant_win\models\whisper\whisper.cpp\build\bin\Release\main.exe"
WHISPER_MODEL = str(MODELS_DIR / "whisper" / "ggml-large-v3.bin")

LLM_MODEL_PATH = str(MODELS_DIR / "llm" / "Llama-3-8B-Instruct.Q4_K_M.gguf")

SD_MODEL_PATH = str(MODELS_DIR / "sd" / "v1-5-pruned-emaonly.safetensors")
SVD_MODEL_PATH = str(MODELS_DIR / "sdxl" / "svd_xt_1_1.safetensors")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
WAKE_WORD = "jarvis"

DOWNLOAD_DIR = BASE_DIR / "downloads"
IMAGE_OUTPUT_DIR = BASE_DIR / "generated_images"
VIDEO_OUTPUT_DIR = BASE_DIR / "generated_videos"

for p in (DOWNLOAD_DIR, IMAGE_OUTPUT_DIR, VIDEO_OUTPUT_DIR):
    p.mkdir(exist_ok=True)

# ========= AUDIO / STT CONFIG =========
AUDIO_INPUT_DEVICE: int | None = None   # set device index (e.g. 26) to lock mic
AUDIO_SAMPLERATE = 16000
AUDIO_CHANNELS = 1
AUDIO_MIN_RMS = 180  # silence gate (prevents blank/garbage loop)

KNOWN_SOFTWARE_SOURCES = {
    "python": {
        "name": "Python",
        "url": "https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe",
    },
    "vlc": {
        "name": "VLC media player",
        "url": "https://get.videolan.org/vlc/3.0.21/win64/vlc-3.0.21-win64.exe",
    },
    "vs code": {
        "name": "Visual Studio Code",
        "url": "https://update.code.visualstudio.com/latest/win32-x64-user/stable",
    },
    "chrome": {
        "name": "Google Chrome",
        "url": "https://dl.google.com/chrome/install/latest/chrome_installer.exe",
    },
}

# =========================
# END OF FILE: config.py
# =========================
