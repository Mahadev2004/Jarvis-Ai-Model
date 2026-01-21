# memory/background_learner.py

from __future__ import annotations

import threading
import time


class BackgroundLearner(threading.Thread):
    """
    Simple background learner thread.

    main.py me use:
        from memory.background_learner import BackgroundLearner

        bg_learner = BackgroundLearner(brain=brain, interval_seconds=600)
        bg_learner.start()

    - Har interval pe 'brain' ko halka sa learning tick dene ki koshish karega.
    - Agar brain me background_tick() method nahi hai to sirf log print karega.
    """

    def __init__(self, brain=None, interval_seconds: int = 600):
        super().__init__(daemon=True)
        self.brain = brain
        # safety: at least 60 sec
        self.interval = max(60, int(interval_seconds))
        self._stop_flag = threading.Event()

    # memory/background_learner.py
    def start(self):
        if getattr(self, "_started", False):
            return
        self._started = True
        # ... existing start logic ...

    def run(self):
        print(f"[BackgroundLearner] Started with interval={self.interval} seconds")
        while not self._stop_flag.is_set():
            # interval wait, but breakable per second
            for _ in range(self.interval):
                if self._stop_flag.is_set():
                    break
                time.sleep(1)

            if self._stop_flag.is_set():
                break

            try:
                if self.brain is not None and hasattr(self.brain, "background_tick"):
                    # Future ke liye hook: agar tum BrainLLM me yeh method banao
                    self.brain.background_tick()
                else:
                    # Abhi ke liye sirf log
                    print("[BackgroundLearner] tick (no background_tick() on brain)")
            except Exception as e:
                print("[BackgroundLearner] error:", e)

        print("[BackgroundLearner] Stopped.")

    def stop(self):
        self._stop_flag.set()
