import time

import torch
from diffusers import StableDiffusionPipeline

from config import DEVICE, IMAGE_OUTPUT_DIR, SD_MODEL_PATH


class ImageGeneratorSD:
    def __init__(self):
        print("⚙️ Loading Stable Diffusion...")
        self.pipe = StableDiffusionPipeline.from_single_file(
            SD_MODEL_PATH,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            safety_checker=None,
        ).to(DEVICE)

    def generate(self, prompt: str) -> str:
        IMAGE_OUTPUT_DIR.mkdir(exist_ok=True)
        filename = f"img_{int(time.time())}.png"
        out_path = IMAGE_OUTPUT_DIR / filename
        image = self.pipe(prompt).images[0]
        image.save(out_path)
        return str(out_path)
