# skills/browser_control.py

from __future__ import annotations

from typing import Callable

import pyautogui

# Safety: fail-safe on top-left corner
pyautogui.FAILSAFE = True


def _safe_action(fn: Callable, *args, **kwargs) -> str:
    """
    Helper to run pyautogui actions safely with basic error handling.
    """
    try:
        fn(*args, **kwargs)
        return ""
    except Exception as e:
        return f"Action error: {e}"


def handle(text: str) -> str:
    """
    High-level browser (ya active window) control handler.

    Voice examples:
      - "scroll down"
      - "scroll down thoda"
      - "scroll down zyada"
      - "scroll up"
      - "go back"
      - "go forward"
      - "refresh page"
      - "reload"
      - "new tab open karo"
      - "close this tab"
      - "next tab"
      - "previous tab"
    """
    if not text:
        return "Mere paas browser command clear nahi aayi."

    t = text.lower().strip()

    # ---------- SCROLLING ---------- #
    if "scroll" in t or "page down" in t or "page up" in t:
        amount = -800  # default down

        if "up" in t or "upar" in t or "top" in t:
            amount = 800  # scroll up

        # fine control
        if any(w in t for w in ["thoda", "little", "kam"]):
            amount = int(amount / 2)
        if any(w in t for w in ["zyada", "fast", "bahut"]):
            amount = amount * 2

        err = _safe_action(pyautogui.scroll, amount)
        if err:
            return "Scrolling karte waqt kuch error aa gaya: " + err

        direction = "up" if amount > 0 else "down"
        return f"Page ko {direction} scroll kar diya."

    # ---------- NAVIGATION: BACK / FORWARD ---------- #
    if any(w in t for w in ["go back", "back ja", "peeche ja", "peeche chalo"]):
        # Alt + Left
        err = _safe_action(pyautogui.hotkey, "alt", "left")
        if err:
            return "Back jaane me thoda issue aa gaya: " + err
        return "Browser ko ek page peeche kar diya."

    if any(w in t for w in ["go forward", "aage ja", "aage chalo"]):
        # Alt + Right
        err = _safe_action(pyautogui.hotkey, "alt", "right")
        if err:
            return "Forward jaane me thoda issue aa gaya: " + err
        return "Browser ko ek page aage kar diya."

    # ---------- REFRESH / RELOAD ---------- #
    if any(w in t for w in ["refresh", "reload", "page reload", "page refresh"]):
        err = _safe_action(pyautogui.press, "f5")
        if err:
            return "Page refresh karte waqt problem aa gayi: " + err
        return "Page ko refresh kar diya."

    # ---------- NEW TAB / CLOSE TAB ---------- #
    if any(w in t for w in ["new tab", "naya tab", "open new tab"]):
        err = _safe_action(pyautogui.hotkey, "ctrl", "t")
        if err:
            return "Naya tab open karne me issue aa gaya: " + err
        return "Naya tab open kar diya."

    if any(
        w in t
        for w in [
            "close this tab",
            "close tab",
            "ye tab band karo",
            "tab band karo",
        ]
    ):
        err = _safe_action(pyautogui.hotkey, "ctrl", "w")
        if err:
            return "Tab band karte waqt issue aa gaya: " + err
        return "Current tab close kar diya."

    # ---------- TAB SWITCHING ---------- #
    if any(w in t for w in ["next tab", "agli tab", "aage wala tab"]):
        err = _safe_action(pyautogui.hotkey, "ctrl", "tab")
        if err:
            return "Next tab me switch karne me problem aa gayi: " + err
        return "Next tab pe switch kar diya."

    if any(w in t for w in ["previous tab", "pichla tab", "pehle wala tab"]):
        err = _safe_action(pyautogui.hotkey, "ctrl", "shift", "tab")
        if err:
            return "Previous tab me switch karne me problem aa gayi: " + err
        return "Previous tab pe switch kar diya."

    # ---------- TOP / BOTTOM (HOME / END) ---------- #
    if any(w in t for w in ["top of page", "page top", "bilkul upar"]):
        err = _safe_action(pyautogui.press, "home")
        if err:
            return "Page ke top par le jaate waqt problem aa gayi: " + err
        return "Page ke top par le gaya."

    if any(w in t for w in ["bottom of page", "page end", "bilkul niche"]):
        err = _safe_action(pyautogui.press, "end")
        if err:
            return "Page ke end par le jaate waqt problem aa gayi: " + err
        return "Page ke end par le gaya."

    # ---------- ADDRESS BAR FOCUS ---------- #
    if any(
        w in t
        for w in [
            "address bar",
            "url bar",
            "search bar",
            "focus url",
            "focus address bar",
        ]
    ):
        err = _safe_action(pyautogui.hotkey, "ctrl", "l")
        if err:
            return "Address bar focus karte waqt error aa gaya: " + err
        return "Address bar par focus kar diya."

    return "Browser control ko yeh specific command samajh nahi aayi."
