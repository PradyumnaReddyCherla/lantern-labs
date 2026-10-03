import re

DASHES = {"", "-", "\u2013", "\u2014"}  # -, en-dash, em-dash
FOOT = re.compile(r"(?<=[\d)])\s*\(\d\)$|\*+$")  # trailing footnote markers

def to_number(cell: str, scale: float = 1.0):
    s = str(cell).strip()
    s = s.replace("$", "").replace(",", "")
    s = FOOT.sub("", s).strip()
    if s in DASHES:
        return 0.0  # policy: dash = nil
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()%").strip()
    try:
        v = float(s)
    except ValueError:
        return None  # label or unparseable
    return (-v if neg else v) * scale

def scale_from_caption(text: str) -> float:
    t = text.lower()
    if "in billions" in t:
        return 1e9
    if "in millions" in t:
        return 1e6
    if "in thousands" in t:
        return 1e3
    return 1.0