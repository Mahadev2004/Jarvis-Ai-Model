from pathlib import Path
import torch

# ========= BASE PATHS =========

# Folder where config.py lives (your project root)
BASE_DIR = Path(__file__).resolve().parent

# Models folder inside the project
MODELS_DIR = BASE_DIR / "models"

# ========= MODELS & BINARIES =========
# IMPORTANT: adjust WHISPER_CPP_EXE to where your compiled whisper.cpp `main.exe` is.

# Example: if you have whisper.cpp in D:\tools\whisper.cpp\
WHISPER_CPP_EXE = r"C:\Abhay\jarvis_assistant_win\models\whisper\whisper.cpp\build\bin\Release\main.exe"

# When you download the Whisper ggml model, put it in:
# models/whisper/ggml-large-v3.bin  (or whatever name you use)
WHISPER_MODEL   = str(MODELS_DIR / "whisper" / "ggml-large-v3.bin")

# LLaMA 3 model:
# models/llm/Llama-3-8B-Instruct.Q4_K_M.gguf
LLM_MODEL_PATH = str(MODELS_DIR / "llm" / "Llama-3-8B-Instruct.Q4_K_M.gguf")

# Stable Diffusion model:
# models/sd/v1-5-pruned-emaonly.safetensors
SD_MODEL_PATH = str(MODELS_DIR / "sd" / "v1-5-pruned-emaonly.safetensors")

# Stable Video Diffusion model:
# models/sdxl/svd_xt_1_1.safetensors
SVD_MODEL_PATH = str(MODELS_DIR / "sdxl" / "svd_xt_1_1.safetensors")

# ========= RUNTIME CONFIG =========

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
WAKE_WORD = "jarvis"

DOWNLOAD_DIR = BASE_DIR / "downloads"
IMAGE_OUTPUT_DIR = BASE_DIR / "generated_images"
VIDEO_OUTPUT_DIR = BASE_DIR / "generated_videos"

for p in (DOWNLOAD_DIR, IMAGE_OUTPUT_DIR, VIDEO_OUTPUT_DIR):
    p.mkdir(exist_ok=True)


# Known safe software for auto-download
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

