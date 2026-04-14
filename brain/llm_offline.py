# brain/llm_offline.py
from __future__ import annotations
import json
from typing import List, Dict, Any
from llama_cpp import Llama
from config import LLM_MODEL_PATH  # tumhare config.py me defined

# Optional defaults; agar future me config me add karna ho to easy hai
LLM_CTX = 4096
LLM_MAX_TOKENS = 512


class BrainLLM:
    """
    Offline LLaMA-3 based brain.

    Features:
    - Hinglish friendly (English + Hindi mix).
    - ChatGPT-style reasoning + coding help.
    - Dev / coding tasks ke liye bahut detail code dega.
    """

    def __init__(self):
        print(f"[BrainLLM] Loading LLaMA model from: {LLM_MODEL_PATH}")
        self.llm = Llama(
            model_path=LLM_MODEL_PATH,
            n_ctx=LLM_CTX,
            logits_all=False,
            n_threads=0,   # 0 => auto-detect based on CPU cores
        )

        # Base identity / behaviour prompt
        self.system_prompt = (
            "You are Jarvis (also called Sakha), a personal AI assistant for Abhay. "
            "You speak in a natural, relaxed Hinglish style: mix of simple English "
            "and Hindi, but avoid overusing English where Hindi is more natural.\n\n"
            "CORE BEHAVIOUR:\n"
            "- Be calm, friendly, and practical.\n"
            "- Focus on clarity. Avoid very long essays unless specifically asked.\n"
            "- For facts or explanations, be accurate and step-by-step.\n"
            "- You can reason deeply about math, physics, computer science, and coding.\n"
            "- If the user sounds confused, explain gently with small simple steps.\n\n"
            "CODING / DEV MODE:\n"
            "- If the user asks for code, programs, scripts, or 'bana do', "
            "  switch to DEV mindset.\n"
            "- Always give COMPLETE usable code blocks, not half code.\n"
            "- Prefer Python for scripts unless the user explicitly asks for a language.\n"
            "- For websites, create minimal but functional HTML/CSS/JS.\n"
            "- Add short, useful comments in English.\n"
            "- If some requirement is underspecified, assume reasonable defaults "
            "  instead of forcing the user to clarify.\n\n"
            "PLANNING / STEPS:\n"
            "- If the user asks for a plan, roadmap, or step-by-step approach, "
            "  produce a clear numbered list of steps.\n"
            "- Distinguish between phases (e.g., Phase 1: Setup, Phase 2: Core Logic, etc.).\n\n"
            "STYLE:\n"
            "- Address Abhay directly as 'tum' in Hindi, but respectfully.\n"
            "- Avoid very heavy Shuddh Hindi; keep it conversational.\n"
            "- Occasionally add small motivational or friendly tone, but do NOT overdo.\n"
            "- Important formulas or code should not be mixed with Hindi; keep them clean.\n\n"
            "SAFETY:\n"
            "- Do not provide any harmful, illegal, or unsafe instructions.\n"
            "- Do not invent sensitive personal details.\n"
        )

    # ---------------- core chat ---------------- #

    def chat(self, history: List[Dict[str, str]]) -> str:
        """
        :param history: list of {role: 'user'|'assistant'|'system', content: str}
        """
        if not isinstance(history, list) or not history:
            history = []

        # System message ko ensure karo
        messages: List[Dict[str, str]] = [{"role": "system", "content": self.system_prompt}]
        for m in history:
            role = m.get("role", "user")
            content = m.get("content", "")
            if not content:
                continue
            if role not in ("system", "user", "assistant"):
                role = "user"
            messages.append({"role": role, "content": content})

        # llama_cpp chat completion
        res: Dict[str, Any] = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=LLM_MAX_TOKENS,
            temperature=0.7,
            top_p=0.9,
        )

        try:
            return res["choices"][0]["message"]["content"].strip()
        except Exception:
            return "Mujhe reply generate karte waqt ek internal error aa gaya."
        
        # ------------------ NEW: Intent classifier ------------------ #
    def classify_intent(self, text: str, allowed_intents: list[str]) -> str:
        """
        LLaMA se poochta hai: user ne kya bola, aur in allowed_intents me se
        kaunsa sabse sahi intent hai?

        Expected output from model (strict JSON):
        {"intent": "camera_check"}
        """

        if not text or not text.strip():
            return "chat"

        # Safety: agar model crash ho jaaye to fallback
        try:
            system_prompt = (
                "You are an intent classifier for a voice assistant named Jarvis.\n"
                "Your job is ONLY to choose the best intent from a fixed list.\n"
                "You MUST respond in strict JSON, e.g.:\n"
                '{"intent": "camera_check"}\n\n'
                "Rules:\n"
                " - Only choose from the allowed intents list.\n"
                " - If you are not sure, use \"chat\".\n"
                " - Do not add explanations.\n"
            )

            user_prompt = (
                "User said (might be Hindi, English or Hinglish):\n"
                f"\"{text}\"\n\n"
                "Allowed intents:\n"
                + ", ".join(f'"{i}"' for i in allowed_intents)
                + "\n\n"
                "Return JSON now."
            )

            res = self.llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=64,
            )

            reply = res["choices"][0]["message"]["content"].strip()

            # Kabhi kabhi model JSON ke bahar text de deta hai, to thoda clean karte hain
            # Try to find the first '{' and last '}' and parse between them
            if "{" in reply and "}" in reply:
                start = reply.index("{")
                end = reply.rindex("}") + 1
                reply = reply[start:end]

            data = json.loads(reply)
            intent = str(data.get("intent", "")).strip()

            if not intent or intent not in allowed_intents:
                return "chat"

            return intent

        except Exception as e:
            print("[BrainLLM.classify_intent] Error:", e)
            return "chat"


    # ---------------- learning hook ---------------- #

    def learn_from_turn(self, user_text: str, reply: str) -> None:
        """
        Simple hook: future me isko smarter banaya ja sakta hai.

        Abhi ke liye:
        - conversation ko memory store me as-is save kar deta hai (optional).
        """
        if not user_text or not reply:
            return

        try:
            from memory.memory_store import get_memory_store

            store = get_memory_store()
            combined = f"user: {user_text.strip()}\nassistant: {reply.strip()}"
            store.add(
                text=combined,
                category="conversation",
                source="auto",
                tags=["turn_pair"],
            )
        except Exception as e:
            print("[BrainLLM] learn_from_turn error:", e)
