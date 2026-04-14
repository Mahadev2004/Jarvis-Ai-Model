# =========================
# FILE: memory/background_learner.py
# =========================

from __future__ import annotations

import threading
import time


class BackgroundLearner(threading.Thread):
    def __init__(self, brain=None, interval_seconds: int = 600):
        super().__init__(daemon=True)
        self.brain = brain
        self.interval = max(60, int(interval_seconds))
        self._stop_flag = threading.Event()
        self._started_once = False  # MOD

    def start(self):
        # MOD: prevent accidental double-start
        if self._started_once:
            return
        self._started_once = True
        super().start()

    def run(self):
        print(f"[BackgroundLearner] Started with interval={self.interval} seconds")
        while not self._stop_flag.is_set():
            for _ in range(self.interval):
                if self._stop_flag.is_set():
                    break
                time.sleep(1)

            if self._stop_flag.is_set():
                break

            try:
                if self.brain is not None and hasattr(self.brain, "background_tick"):
                    self.brain.background_tick()
                else:
                    print("[BackgroundLearner] tick (no background_tick() on brain)")
            except Exception as e:
                print("[BackgroundLearner] error:", e)

        print("[BackgroundLearner] Stopped.")

    def stop(self):
        self._stop_flag.set()

# =========================
# END OF FILE: memory/background_learner.py
# =========================
