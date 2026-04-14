import pyttsx3

class SimpleTTS:
    def __init__(self):
        try:
            # SAPI5 engine (same as your working test)
            self.engine = pyttsx3.init("sapi5")
            self.engine.setProperty("rate", 175)  # thoda normal speed
        except Exception as e:
            print("[TTS INIT ERROR]:", e)
            self.engine = None

    def speak(self, text: str):
        # console pe hamesha text dikhayega
        print(f"🤖 Jarvis: {text}")

        if not self.engine:
            return

        # EXACTLY same pattern jo tumne manually chalaya tha
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print("[TTS ERROR]:", e)
