from __future__ import annotations

import unicodedata

# Slovak collating order. Each tuple is one "letter" bucket: members share a
# primary weight and differ only at the secondary (accent) level, the way
# Slovak dictionaries order words. Accented vowels file next to their base
# letter, while č/š/ž and the digraph "ch" are letters in their own right:
# "ch" sorts after all of "h", and č/š/ž right after c/s/z.
_ALPHABET: tuple[tuple[str, ...], ...] = (
    ("a", "á", "ä"),
    ("b",),
    ("c",),
    ("č",),
    ("d", "ď"),
    ("dz",),
    ("dž",),
    ("e", "é"),
    ("f",),
    ("g",),
    ("h",),
    ("ch",),
    ("i", "í"),
    ("j",),
    ("k",),
    ("l", "ĺ", "ľ"),
    ("m",),
    ("n", "ň"),
    ("o", "ó", "ô"),
    ("p",),
    ("q",),
    ("r", "ŕ"),
    ("s",),
    ("š",),
    ("t", "ť"),
    ("u", "ú"),
    ("v",),
    ("w",),
    ("x",),
    ("y", "ý"),
    ("z",),
    ("ž",),
)

# Multi-character "letters" are matched greedily before single characters.
_DIGRAPHS = ("dž", "dz", "ch")

_PRIMARY: dict[str, int] = {}
_SECONDARY: dict[str, int] = {}
for _weight, _group in enumerate(_ALPHABET, start=1):
    for _rank, _token in enumerate(_group):
        _PRIMARY[_token] = _weight
        _SECONDARY[_token] = _rank

# Anything outside the Slovak alphabet (digits, punctuation, other scripts)
# sorts after every Slovak letter, ordered among itself by code point.
_AFTER = len(_ALPHABET) + 1


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        pair = text[index : index + 2]
        if pair in _DIGRAPHS:
            tokens.append(pair)
            index += 2
        else:
            tokens.append(text[index])
            index += 1
    return tokens


def slovak_sort_key(text: str) -> tuple[list[int], list[int]]:
    """Sort key that orders strings the way Slovak does (č after c, ch after h).

    Case-insensitive. Non-alphabet characters keep a stable order so the
    overall ordering is total.
    """
    text = unicodedata.normalize("NFC", text).casefold()
    primary: list[int] = []
    secondary: list[int] = []
    for token in _tokenize(text):
        if token in _PRIMARY:
            primary.append(_PRIMARY[token])
            secondary.append(_SECONDARY[token])
        else:
            primary.append(_AFTER)
            secondary.append(ord(token[0]))
    return primary, secondary
