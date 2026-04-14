# =========================
# FILE: skills/image_gen_sd.py
# =========================

import time
import torch
from diffusers import StableDiffusionPipeline

from config import DEVICE, IMAGE_OUTPUT_DIR, SD_MODEL_PATH


class ImageGeneratorSD:
    """
    MOD:
    - Lazy load SD pipeline so startup fast (no SD load unless image intent used)
    """

    def __init__(self):
        self.pipe = None

    def _ensure_loaded(self):
        if self.pipe is not None:
            return
        print("⚙️ Loading Stable Diffusion (lazy-load)...")
        self.pipe = StableDiffusionPipeline.from_single_file(
            SD_MODEL_PATH,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            safety_checker=None,
        ).to(DEVICE)

    def generate(self, prompt: str) -> str:
        self._ensure_loaded()
        IMAGE_OUTPUT_DIR.mkdir(exist_ok=True)
        filename = f"img_{int(time.time())}.png"
        out_path = IMAGE_OUTPUT_DIR / filename
        image = self.pipe(prompt).images[0]
        image.save(out_path)
        return str(out_path)

# =========================
# END OF FILE: skills/image_gen_sd.py
# =========================
