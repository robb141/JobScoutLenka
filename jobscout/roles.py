from __future__ import annotations

import re

from .location import normalize_text, strip_diacritics


# Words that describe seniority, contract type, or the generic "job" wrapper
# rather than the field itself. "Laboratory technician" should match any lab
# posting, not only ones that also spell out "technician"; "Biochemik" should
# match "Biochémia" too. Slovak and German equivalents are included because
# the boards are Slovak (Profesia) and German (karriere.at).
GENERIC_WORDS = {
    # English
    "junior",
    "senior",
    "medior",
    "lead",
    "principal",
    "staff",
    "assistant",
    "associate",
    "trainee",
    "intern",
    "internship",
    "technician",
    "specialist",
    "expert",
    "engineer",
    "scientist",
    "analyst",
    "worker",
    "officer",
    "manager",
    "coordinator",
    "position",
    "job",
    # Slovak
    "specialista",
    "specialistka",
    "odbornik",
    "odborny",
    "inzinier",
    "vedec",
    "vedecky",
    "pracovnik",
    "pracovnicka",
    "asistent",
    "asistentka",
    "praca",
    "ponuka",
    "brigada",
    # German
    "fachkraft",
    "mitarbeiter",
    "mitarbeiterin",
    "referent",
    "referentin",
    "stelle",
    "vollzeit",
    "teilzeit",
}

# Gender / inclusivity tags that pollute scraped titles: "(m/w/d)", "m/ž",
# "(w/m/x)", "/-in", "*in" and friends.
_TITLE_NOISE_RE = re.compile(
    r"\(?\b[mwfdxzž](?:\s*[/*_-]\s*[mwfdxzž]){1,3}\b\)?|[/*]-?in\b",
    re.IGNORECASE,
)


def _clean(text: str) -> str:
    return _TITLE_NOISE_RE.sub(" ", text)


def role_terms(roles: list[str]) -> list[tuple[str, str]]:
    """Map each configured role to its distinctive search term.

    Returns (term, role) pairs sorted longest-term-first so that a specific
    term ("analytical chemistry") wins over a short one ("chemistry").
    """
    terms: dict[str, str] = {}
    for role in roles:
        normalized = strip_diacritics(normalize_text(_clean(role)))
        words = [word for word in normalized.split() if word not in GENERIC_WORDS]
        term = " ".join(words) or normalized
        terms.setdefault(term, role)
    return sorted(terms.items(), key=lambda item: len(item[0]), reverse=True)


# How many trailing letters a term may pick up and still count as a match.
# Slovak and German inflect the stem ("laborant" -> "laboranta",
# "laborantka"; "chemik" -> "chemiker", "chemikom"), so an exact word
# boundary misses most real titles. Four is enough for those endings while
# still rejecting unrelated longer words.
_SUFFIX_SLACK = 4

# Terms at least this long are matched inside German compound words too
# ("labortechniker" inside "Chemielabortechniker"); shorter ones keep a
# strict word start so "chemik" does not fire on "Elektrochemikalien".
_COMPOUND_MIN = 7


def match_role(text: str, roles: list[str]) -> str:
    """Return the configured role whose term appears in text, or "".

    A short term must start on a word boundary; a long term may also sit
    inside a compound word. Either may be followed by a short inflectional
    ending, so "Laborantka" matches the term "laborant".
    """
    normalized = strip_diacritics(normalize_text(_clean(text)))
    for term, role in role_terms(roles):
        head = "" if len(term) >= _COMPOUND_MIN else r"(?<![a-z])"
        pattern = rf"{head}{re.escape(term)}[a-z]{{0,{_SUFFIX_SLACK}}}(?![a-z])"
        if re.search(pattern, normalized):
            return role
    return ""
