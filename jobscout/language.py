from __future__ import annotations

import re

from .location import strip_diacritics, normalize_text


# Ordered most-specific first. Each entry: (regex, Slovak label). The label is
# what shows in the report so Lenka can see at a glance how much German a
# posting needs.
_GERMAN_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"deutsch\w*\s*(?:niveau|level|kenntnisse|skills)?\s*[:(\-]?\s*(a1|a2|b1|b2|c1|c2)\b"), "Nemčina {0}"),
    (re.compile(r"\b(a1|a2|b1|b2|c1|c2)[-\s]?niveau\b.*deutsch|\bdeutsch\b.*\b(a1|a2|b1|b2|c1|c2)[-\s]?niveau\b"), "Nemčina {lvl}"),
    (re.compile(r"deutsch\s+(?:als\s+)?muttersprache|muttersprach\w*\s+deutsch|native\s+german"), "Nemčina: rodený hovoriaci"),
    (re.compile(r"verhandlungssicher\w*\s+deutsch|deutsch\w*\s+verhandlungssicher|fluent\s+german|fliessend\w*\s+deutsch|deutsch\w*\s+fliessend"), "Nemčina: plynulá (C1+)"),
    (re.compile(r"sehr\s+gute?\s+deutsch\w*|excellent\s+german"), "Nemčina: veľmi dobrá (C1)"),
    (re.compile(r"gute?\s+deutsch\w*|good\s+german|solide?\s+deutsch\w*"), "Nemčina: dobrá (B2)"),
    (re.compile(r"grundkenntnisse\s+deutsch|deutsch\w*\s+grundkenntnisse|basic\s+german|deutsch\w*\s+von\s+vorteil|deutsch\w*\s+erwuenscht|deutsch\w*\s+wuenschenswert"), "Nemčina: základy / výhodou"),
    (re.compile(r"\bdeutsch\w*\b"), "Nemčina: vyžaduje sa"),
    (re.compile(r"english\s+only|no\s+german\s+required|kein\s+deutsch\s+(?:noetig|erforderlich)|working\s+language\s+is\s+english"), "Nemčina: netreba (angličtina)"),
]


def german_requirement(text: str) -> str:
    """Best-effort Slovak note on the German-language level a posting asks for.

    Returns "" when the text says nothing about German. Only meant for
    German-language boards (karriere.at) and hand-written company notes;
    Slovak and English list views rarely mention it.
    """
    haystack = strip_diacritics(normalize_text(text))
    if not haystack:
        return ""
    for pattern, label in _GERMAN_RULES:
        match = pattern.search(haystack)
        if not match:
            continue
        level = next((group for group in match.groups() if group), "")
        return label.format(level.upper(), lvl=level.upper()) if level else label
    return ""
