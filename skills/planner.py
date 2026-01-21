# skills/planner.py

from __future__ import annotations

from typing import Optional, List, Dict


def handle(text: str, brain) -> str:
    """
    High-level planner agent.

    Example commands:
      - "Jarvis, mere liye machine learning seekhne ka roadmap banao"
      - "Jarvis, web dev seekhne ke liye step by step plan do"
      - "Mujhe next 3 months ka study plan chahiye"

    :param text: user command
    :param brain: BrainLLM instance
    """
    if brain is None:
        return "Planner ke paas abhi brain instance nahi hai."

    if not text:
        return "Planner ko clear command nahi mili."

    system = (
        "You are a planning and strategy assistant. "
        "Given the user's goal, you produce a clear, structured, step-by-step plan.\n\n"
        "Rules:\n"
        "- Break into phases (Phase 1, Phase 2, ...), har phase me steps.\n"
        "- For each step, mention approximate time (e.g., 1–2 weeks, 2–3 days).\n"
        "- Keep it practical for a student like Abhay.\n"
        "- Use a mix of simple English + Hindi (Hinglish), but keep structure clean.\n"
        "- Avoid unnecessary motivational speeches; focus on concrete steps.\n"
    )

    prompt = (
        f"{system}\n"
        f"User goal / request:\n{text}\n\n"
        "Please respond as a structured plan, like:\n"
        "Phase 1: ...\n"
        "  - Step 1: ...\n"
        "  - Step 2: ...\n"
        "Phase 2: ...\n"
        "  - Step 3: ...\n"
        "and so on."
    )

    history: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
    reply = brain.chat(history)
    if not reply:
        return "Planner ko plan banate waqt problem aa gayi, koi output nahi mila."

    return reply.strip()
