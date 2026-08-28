from __future__ import annotations

import re
import unicodedata
from html import unescape


# Lenka lives in Kittsee (Burgenland, AT), right on the border, and is willing
# to commute to Bratislava, to Vienna, or to towns close to Kittsee. Every
# posting is sorted into one of these buckets; anything that lands nowhere is
# dropped from the report.
BRATISLAVA = "Bratislava"
VIENNA = "Vienna"
KITTSEE_AREA = "Kittsee area"
BRATISLAVA_REGION = "Bratislava region"
VIENNA_REGION = "Vienna region"


# Bratislava city boroughs (mestské časti). Boards usually write the borough
# name without the city, so this is what maps them back to Bratislava. Keys are
# lowercase with diacritics stripped.
BRATISLAVA_BOROUGHS: set[str] = {
    "stare mesto",
    "ruzinov",
    "nove mesto",
    "petrzalka",
    "karlova ves",
    "dubravka",
    "raca",
    "vrakuna",
    "podunajske biskupice",
    "devinska nova ves",
    "lamac",
    "devin",
    "zahorska bystrica",
    "vajnory",
    "jarovce",
    "rusovce",
    "cunovo",
}


# Vienna's 23 districts (Bezirke) by name -> number, diacritics stripped.
VIENNA_DISTRICTS: dict[str, int] = {
    "innere stadt": 1,
    "leopoldstadt": 2,
    "landstrasse": 3,
    "wieden": 4,
    "margareten": 5,
    "mariahilf": 6,
    "neubau": 7,
    "josefstadt": 8,
    "alsergrund": 9,
    "favoriten": 10,
    "simmering": 11,
    "meidling": 12,
    "hietzing": 13,
    "penzing": 14,
    "rudolfsheim-funfhaus": 15,
    "rudolfsheim funfhaus": 15,
    "ottakring": 16,
    "hernals": 17,
    "wahring": 18,
    "dobling": 19,
    "brigittenau": 20,
    "floridsdorf": 21,
    "donaustadt": 22,
    "liesing": 23,
}


# Austrian towns close enough to Kittsee for a daily commute (roughly within
# 25 km). Kittsee itself is in Burgenland; the rest straddle Burgenland and
# Lower Austria along the Danube. Bratislava is only ~7 km away but gets its
# own bucket above.
KITTSEE_TOWNS: set[str] = {
    "kittsee",
    "kitsee",
    "pama",
    "gattendorf",
    "edelstal",
    "berg",
    "wolfsthal",
    "deutsch jahrndorf",
    "potzneusiedl",
    "zurndorf",
    "nickelsdorf",
    "parndorf",
    "neusiedl am see",
    "bruckneudorf",
    "bruck an der leitha",
    "gols",
    "hainburg",
    "hainburg an der donau",
    "bad deutsch-altenburg",
    "bad deutsch altenburg",
    "petronell-carnuntum",
    "petronell carnuntum",
    "prellenkirchen",
    "hundsheim",
}


def _town_pattern(names: set[str], suffix: str = r"\b") -> re.Pattern[str]:
    ordered = sorted((re.escape(name) for name in names), key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(ordered) + r")" + suffix)


# The lookahead rejects same-named towns elsewhere: "Nové Mesto" is a
# Bratislava borough, but "Nové Mesto nad Váhom" / "pod Smrkom" is not.
_BOROUGH_RE = _town_pattern(BRATISLAVA_BOROUGHS, r"\b(?!\s+(?:nad|na|pod|pri)\b)")
_VIENNA_DISTRICT_RE = _town_pattern(set(VIENNA_DISTRICTS))
_KITTSEE_RE = _town_pattern(KITTSEE_TOWNS)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip().lower()


# Ligatures Unicode does not decompose on its own, folded for matching.
_LIGATURES = str.maketrans({"ß": "ss", "ẞ": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe"})


def strip_diacritics(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.translate(_LIGATURES))
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _ascii(value: str) -> str:
    return strip_diacritics(normalize_text(value))


def _vienna_district(normalized: str) -> int | None:
    """Vienna district number from a diacritics-stripped location string.

    Reads it from a 1xx0 postal code (1030 -> 3, 1220 -> 22) or from a
    district name ("Landstrasse" -> 3). Returns None when only the city is
    named.
    """
    plz = re.search(r"\b1([0-2]\d)0\b", normalized)
    if plz:
        number = int(plz.group(1))
        if 1 <= number <= 23:
            return number
    name = _VIENNA_DISTRICT_RE.search(normalized)
    if name:
        return VIENNA_DISTRICTS[name.group(1)]
    return None


def _vienna_label(normalized: str) -> str:
    number = _vienna_district(normalized)
    return f"Wien {number}" if number else VIENNA


def region_match(text: str, include_unspecified: bool = True) -> str | None:
    """Sort a location string into one of Lenka's target regions, or None.

    The check order matters: an explicit city name always wins over the vague
    "Bratislavský kraj" / "Wien-Umgebung" fallbacks, and a Vienna district
    name only counts when the text is clearly Austrian, never when it happens
    to appear inside a longer Slovak address.
    """
    normalized = _ascii(text)
    if not normalized:
        return None

    # "Wien-Umgebung" is a belt district, not the city; strip it before the
    # plain-Vienna test so it only feeds the vague "Vienna region" bucket.
    vienna_umgebung = bool(re.search(r"wien[- ]?umgebung|umgebung\s+wien", normalized))
    without_umgebung = re.sub(r"wien[- ]?umgebung|umgebung\s+wien", " ", normalized)

    mentions_vienna = bool(re.search(r"\b(wien|vienna|vieden)\b", without_umgebung))
    mentions_bratislava_city = bool(re.search(r"\bbratislava\b", normalized))
    mentions_bratislava_any = bool(re.search(r"\bbratislav", normalized))

    # Vienna postal codes look like 1010..1230 (1<district:2 digits>0).
    vienna_plz = re.search(r"\b1([0-2]\d)0\b", normalized)
    if mentions_vienna or vienna_plz:
        return _vienna_label(normalized)
    if not mentions_bratislava_any and _VIENNA_DISTRICT_RE.search(normalized):
        # District names are safe only away from a Slovak context.
        if not re.search(r"\bsloven|\bsk\b", normalized):
            return _vienna_label(normalized)

    if mentions_bratislava_city or _BOROUGH_RE.search(normalized):
        return BRATISLAVA

    if _KITTSEE_RE.search(normalized):
        return KITTSEE_AREA

    if include_unspecified:
        if re.search(r"bratislavsk\w*\s+kraj", normalized) or (
            mentions_bratislava_any and not mentions_bratislava_city
        ):
            return BRATISLAVA_REGION
        if vienna_umgebung:
            return VIENNA_REGION

    return None
