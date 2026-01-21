# skills/calculator.py

import re

def _parse_expression(text: str) -> str:
    """Convert a voice sentence into a math expression string."""
    t = text.lower()

    # Remove unnecessary words
    for w in ["calculate", "calculator", "please", "jarvis", "sakha", "hey"]:
        t = t.replace(w, "")

    # Map word-operators to symbols
    replacements = {
        "plus": "+",
        "add": "+",
        "minus": "-",
        "subtract": "-",
        "multiplied by": "*",
        "times": "*",
        "into": "*",
        "x": "*",
        "divided by": "/",
        "by": "/",
        "mod": "%",
        "remainder": "%",
        "power of": "**",
        "to the power of": "**",
    }
    # Replace longer phrases first
    for k in sorted(replacements, key=len, reverse=True):
        t = t.replace(k, f" {replacements[k]} ")

    # Keep only safe characters
    allowed = "0123456789.+-*/()% "
    expr = "".join(ch for ch in t if ch in allowed)
    return expr.strip()


def handle_calculation(text: str) -> str:
    expr = _parse_expression(text)
    if not expr:
        return "Mujhe calculation samajh nahi aayi. Please bolo: 'calculate 25 plus 37'."

    try:
        # VERY restricted eval: no builtins
        result = eval(expr, {"__builtins__": {}})
    except Exception as e:
        return f"Expression evaluate nahi ho paya. Error: {e}"

    return f"{expr} ka result {result} hai."
