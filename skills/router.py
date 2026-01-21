# skills/router.py
from __future__ import annotations

from .image_gen_sd import ImageGeneratorSD
from .video_gen_svd import VideoGeneratorSVD

from . import download_manager
from . import web_tools
from . import calculator
from . import translator
from . import reader
from . import screen_tools
from . import vision_tools
from . import video_tools
from . import knowledge_web
from . import memory_skill
from . import desktop_control
from . import tasks


class IntentRouter:
    def __init__(self):
        self.jobs = []
        self.img_gen = ImageGeneratorSD()
        self.vid_gen = VideoGeneratorSVD()

    def detect_intent(self, text: str) -> str:
        if not text:
            return "chat"

        t = text.lower().strip()

        # Tasks (youtube download etc.)
        if "download" in t and any(kw in t for kw in ["youtube", "video", "audio", "song", "gana", "mp3"]):
            return "tasks"

        # Vision
        if any(kw in t for kw in ["read the screen", "read screen", "screen par", "screen pe", "what's on my screen",
                                  "camera", "webcam", "face detect", "mujhe camera pe"]):
            return "vision"

        # Desktop control (open/close/minimize/maximize)
        if any(kw in t for kw in ["open ", "launch ", "start ", "close ", "band ", "minimize", "maximize", "switch window", "alt tab"]):
            return "desktop_control"

        # Memory: remember
        if any(kw in t for kw in ["remember that", "remember this", "yaad rakh", "yaad rakhna"]):
            return "memory_add"

        # Memory: recall
        if any(kw in t for kw in ["what do you remember about me", "what do you know about me",
                                  "tum mere bare mein kya jante ho", "tumhe mere baare mein kya yaad hai"]):
            return "memory_query"

        # Knowledge Q&A
        if ("who is" in t) or ("who was" in t) or ("what is" in t) or t.startswith("tell me about") or ("kaun hai" in t) or ("kya hai" in t):
            return "knowledge"

        # Screen reading shortcut
        if "screen" in t and any(w in t for w in ["read", "padh", "padho", "dekho", "see"]):
            return "read_screen"

        # YouTube link summary
        if "youtube.com" in t or "youtu.be" in t:
            return "yt_summary"

        # Image gen
        if any(w in t for w in ["image bana", "photo bana", "wallpaper", "ai image", "image generate"]):
            return "image"

        # Video gen
        if any(w in t for w in ["video bana", "reel bana", "clip bana", "video generate"]):
            return "video"

        # Download/install
        if "download" in t or "install" in t:
            return "download"

        # Web search
        if any(w in t for w in ["search", "google", "internet pe", "on internet", "online"]):
            return "web"

        # Calculator
        if "calculate" in t or "calculator" in t:
            return "calc"

        # Translation
        if any(kw in t for kw in ["translate", "isko hindi me bolo", "isko english me bolo",
                                  "hindi me translate karo", "english me translate karo"]):
            return "translate"

        # Book reading
        if "read book" in t or "kitab" in t or ("book" in t and "screen" not in t):
            return "read_book"

        return "chat"

    def handle(self, text: str, brain=None, chat_history=None) -> str:
        intent = self.detect_intent(text)
        t = text

        try:
            if intent == "tasks":
                return tasks.handle(text) or "Theek hai, task start kar diya."

            if intent == "vision":
                return vision_tools.handle(text) or "Vision command execute kar diya."

            if intent == "memory_add":
                return memory_skill.handle_remember(text) or "Theek hai, yaad rakh liya."

            if intent == "memory_query":
                return memory_skill.handle_recall() or "Abhi mere paas tumhare baare me kuch saved nahi hai."

            if intent == "knowledge":
                return knowledge_web.answer_question(t) or "Mujhe iska answer nahi mila."

            if intent == "read_screen":
                return screen_tools.read_screen_now() or "Main screen read nahi kar paaya."

            if intent == "yt_summary":
                return video_tools.summarize_youtube_link(t) or "Main video ka summary nahi nikaal paaya."

            if intent == "image":
                path = self.img_gen.generate(t)
                return f"Image generate ho gayi. Saved at: {path}"

            if intent == "video":
                path = self.vid_gen.generate(t)
                return f"Video generate ho gaya (placeholder). Saved at: {path}"

            if intent == "download":
                return download_manager.handle_download_intent(t) or "Download task start kar diya."

            if intent == "web":
                return web_tools.search_web(t) or "Web search me issue aa gaya."

            if intent == "calc":
                return calculator.handle_calculation(t) or "Calculation me issue aa gaya."

            if intent == "translate":
                return translator.handle(text, brain=brain) if brain else translator.handle(text)

            if intent == "read_book":
                return reader.read_book_snippet(t) or "Book read nahi ho paayi."

            if intent == "desktop_control":
                return desktop_control.handle(text) or "Desktop command execute ho gaya."

            # fallback chat
            if brain is not None:
                # Provide minimal context
                hist = chat_history or [{"role": "user", "content": text}]
                return brain.chat(hist)

            return "Mujhe yeh command samajh nahi aayi."

        except Exception as e:
            print("[Router] handle error:", e)
            return "Mujhe command execute karne me issue aa gaya."
