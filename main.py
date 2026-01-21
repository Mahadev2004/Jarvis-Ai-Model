# main.py

from __future__ import annotations
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
}


def main():
    # ---- Init core components ----
    stt = WhisperSTT()
    brain = BrainLLM()
    router = IntentRouter()
    tts = SimpleTTS()

    # ---- Background learner (Memory v2) ----
    try:
        bg_learner = BackgroundLearner(brain=brain, interval_seconds=600)  # 10 min
        bg_learner.start()
        print("[BackgroundLearner] Started with interval=600 seconds")
    except Exception as e:
        print("[BackgroundLearner] Failed to start:", e)

    chat_history = []

    print("🤖 Jarvis: Namaste, main Jarvis hoon, ready for your command.\n")
    print("Speak your command, or say 'quit' to exit.\n")

    # announce completed background jobs (if any)
    try:
        done = router.jobs.pop_done_messages()
        for jr in done:
            msg = jr.message or "Background task done."
            print(f"🤖 Jarvis: {msg}")
            try:
                tts.speak(msg, stt=stt, enable_barge_in=True)
            except Exception:
                pass
    except Exception as e:
        print("[Main] background announce error:", e)


    # ---- Main loop: 1 turn = 1 command ----
    while True:
        print("🎙️ Listening...")
        user_text = stt.listen_and_transcribe(duration=5)

        if not user_text or not user_text.strip():
            msg = "Mujhe kuch samajh nahi aaya, please repeat."
            print(f"🤖 Jarvis: {msg}\n")
            try:
                tts.speak(msg)
            except Exception as e:
                print("[Main] TTS error (empty input):", e)
            continue

        user_text = user_text.strip()
        print(f"🗣️ You said: {user_text}")
        lower = user_text.lower()

        # ---- Exit ----
        if lower in EXIT_WORDS:
            bye = "Theek hai, main ab band ho raha hoon. Bye."
            print(f"🤖 Jarvis: {bye}")
            try:
                tts.speak(bye)
            finally:
                break

        # ---- Route + Brain reply ----
        try:
            reply = router.handle(user_text, brain=brain, chat_history=chat_history)
        except TypeError:
            # In case router.handle brain/chat_history accept nahi karta ho
            reply = router.handle(user_text)
        except Exception as e:
            print("[Main] Error in router.handle:", e)
            reply = "Mujhe command samajhne mein thoda issue aa gaya."

        reply = (reply or "").strip()
        if not reply:
            reply = "Mujhe samajh nahi aaya, ek baar phir se bol do."

        # ---- Chat history / learning ----
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": reply})

        try:
            brain.learn_from_turn(user_text, reply)
        except Exception as e:
            print("[Main] learn_from_turn error:", e)

        # Auto memory learning
        try:
            from skills import memory_skill
            memory_skill.auto_learn_from_turn(user_text, reply, brain=brain)
        except Exception as e:
            print("[Main] auto memory error:", e)

        # ---- Output (text + speech) ----
        print(f"🤖 Jarvis: {reply}\n")
        try:
            # BARGE-IN abhi off rakha hai → simple speak
            tts.speak(reply)
        except Exception as e:
            print("[Main] TTS error:", e)


if __name__ == "__main__":
    main()
