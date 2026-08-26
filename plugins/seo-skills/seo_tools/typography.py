"""Pixel width estimation for titles and descriptions.

Character counts are the wrong unit. "Illinois" and "Wholesale" are both nine
characters and one is roughly half the width of the other, so a title that
counts as safe can still truncate. Google renders result titles in Arial, so
measuring against Arial advance widths gets much closer than counting.

What this is: the published Arial advance widths (units per 1000 em) summed and
scaled to a font size. What this is not: a rendering engine. It ignores
kerning, ligatures, font fallback for scripts Arial does not cover, and the
fact that Google sometimes rewrites the title anyway. Treat every number here
as an estimate, and label it as one in any output, per PRINCIPLES.md.

The truncation thresholds are observed SERP behaviour reported consistently
across the industry, not values Google documents. They are constants here so
they can be corrected in one place when they move.
"""
from __future__ import annotations

from typing import Dict

# Arial advance widths, units per 1000 em. These are the font metrics, not a guess.
ARIAL: Dict[str, int] = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
    "8": 556, "9": 556, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556,
    "@": 1015,
    "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722,
    "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778, "P": 667,
    "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944, "X": 667,
    "Y": 667, "Z": 611,
    "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556, "`": 333,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556, "h": 556,
    "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556, "p": 556,
    "q": 556, "r": 333, "s": 500, "t": 278, "u": 556, "v": 500, "w": 722, "x": 500,
    "y": 500, "z": 500,
    "{": 334, "|": 260, "}": 334, "~": 584,
    # Punctuation and accents that turn up in real titles and would otherwise
    # fall through to DEFAULT_WIDTH. Written as escapes so this file stays inside
    # the repo-wide dash ban described in PRINCIPLES.md.
    "–": 556,   # en dash
    "—": 1000,  # em dash
    "‘": 222, "’": 222,  # single quotes
    "“": 333, "”": 333,  # double quotes
    "…": 1000,  # ellipsis
    " ": 278,   # non-breaking space
    "ä": 556, "ö": 556, "ü": 556, "ß": 556,
    "Ä": 667, "Ö": 778, "Ü": 722,
    "é": 556, "è": 556, "á": 556, "ú": 556,
    "ó": 556, "í": 278, "ñ": 556,
}
DEFAULT_WIDTH = 556  # a lowercase-letter width, for anything not tabulated

# Rendering sizes Google uses on desktop results.
TITLE_FONT_PX = 20
DESCRIPTION_FONT_PX = 14

# Observed truncation points, desktop. Industry-reported, not Google-documented.
TITLE_LIMIT_PX = 580
DESCRIPTION_LIMIT_PX = 920

# Character guidance, kept because it is what most briefs are written against.
TITLE_CHARS_MIN = 30
TITLE_CHARS_MAX = 60
DESCRIPTION_CHARS_MIN = 70
DESCRIPTION_CHARS_MAX = 160

METHOD = "Arial advance widths scaled to the SERP font size. Estimate, not a render."


def measure_px(text: str, font_px: int) -> float:
    """Estimated rendered width of `text` in pixels at `font_px`."""
    if not text:
        return 0.0
    units = sum(ARIAL.get(char, DEFAULT_WIDTH) for char in text)
    return round(units / 1000.0 * font_px, 1)


def truncate_to_px(text: str, limit_px: float, font_px: int) -> str:
    """What the reader would see if the renderer cut at `limit_px`.

    Cuts on a word boundary and appends an ellipsis, which is what Google does.
    """
    if measure_px(text, font_px) <= limit_px:
        return text
    ellipsis_px = measure_px("…", font_px)
    budget = limit_px - ellipsis_px
    kept: list = []
    used = 0.0
    for word in text.split(" "):
        word_px = measure_px((" " if kept else "") + word, font_px)
        if used + word_px > budget:
            break
        kept.append(word)
        used += word_px
    if not kept:
        return "…"
    return " ".join(kept) + "…"


def measure_title(text: str) -> Dict[str, object]:
    """Character count, estimated width, and whether it truncates."""
    width = measure_px(text, TITLE_FONT_PX)
    return {
        "text": text,
        "chars": len(text),
        "px": width,
        "px_limit": TITLE_LIMIT_PX,
        "px_used_pct": round(width / TITLE_LIMIT_PX * 100, 1) if TITLE_LIMIT_PX else None,
        "truncates": width > TITLE_LIMIT_PX,
        "truncated_preview": truncate_to_px(text, TITLE_LIMIT_PX, TITLE_FONT_PX),
        "font_px": TITLE_FONT_PX,
        "method": METHOD,
    }


def measure_description(text: str) -> Dict[str, object]:
    """Character count, estimated width, and whether it truncates."""
    width = measure_px(text, DESCRIPTION_FONT_PX)
    return {
        "text": text,
        "chars": len(text),
        "px": width,
        "px_limit": DESCRIPTION_LIMIT_PX,
        "px_used_pct": round(width / DESCRIPTION_LIMIT_PX * 100, 1) if DESCRIPTION_LIMIT_PX else None,
        "truncates": width > DESCRIPTION_LIMIT_PX,
        "truncated_preview": truncate_to_px(text, DESCRIPTION_LIMIT_PX, DESCRIPTION_FONT_PX),
        "font_px": DESCRIPTION_FONT_PX,
        "method": METHOD,
    }
