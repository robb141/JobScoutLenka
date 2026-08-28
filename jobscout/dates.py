from __future__ import annotations

import re
from datetime import date, timedelta

from .location import strip_diacritics, normalize_text


def posted_sort_key(value: str, today: date | None = None) -> str:
    """Best-effort ISO date for a scraped posted-date string, "" if unknown.

    The boards mix languages and formats ("Teraz", "Pred 3 dňami", "vor 7
    Tagen veröffentlicht", "28.08.2026", "2026-08-28", "NEW"); this maps them
    onto sortable ISO dates while the report keeps showing the original text.
    """
    today = today or date.today()
    normalized = strip_diacritics(normalize_text(value))
    if not normalized:
        return ""

    # "now" / "today" in EN, SK, DE
    if re.search(r"\b(new|nova|dnes|teraz|heute|neu|gerade eben|prave|pred chvilou)\b", normalized):
        return today.isoformat()
    # "yesterday"
    if re.search(r"\b(yesterday|vcera|gestern)\b", normalized):
        return (today - timedelta(days=1)).isoformat()

    iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", normalized)
    if iso:
        return _safe_date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))

    dmy = re.search(r"\b(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\b", normalized)
    if dmy:
        return _safe_date(int(dmy.group(3)), int(dmy.group(2)), int(dmy.group(1)))

    # "X days ago" in EN, SK (pred X dnami), DE (vor X Tagen)
    days = re.search(
        r"(?:pred|vor)\s+(\d+)\s+(?:dn|tag)|(\d+)\s+days?\s+ago",
        normalized,
    )
    if days:
        count = int(days.group(1) or days.group(2))
        return (today - timedelta(days=count)).isoformat()

    # "a week / X weeks ago"
    weeks = re.search(
        r"(?:pred|vor)\s+(\d+)?\s*(?:tyzd|woche|wochen)|(\d+)\s+weeks?\s+ago",
        normalized,
    )
    if weeks:
        count = int(weeks.group(1) or weeks.group(2) or 1)
        return (today - timedelta(weeks=count)).isoformat()

    # "X hours / minutes ago" -> treat as today
    if re.search(
        r"(?:pred|vor)\s+\d*\s*(?:hodin|minut|stunde|minute)|(?:hours?|minutes?)\s+ago",
        normalized,
    ):
        return today.isoformat()

    return ""


def _safe_date(year: int, month: int, day: int) -> str:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return ""


def posted_label_sk(value: str, today: date | None = None) -> str:
    """Slovak display text for a scraped posted-date string.

    The boards post in Slovak, German and English; this normalises whatever
    they say to one Slovak phrasing for the report's "Zverejnené" column.
    Returns "" when the date cannot be worked out.
    """
    today = today or date.today()
    iso = posted_sort_key(value, today)
    if not iso:
        return ""

    posted = date.fromisoformat(iso)
    days = (today - posted).days
    if days <= 0:
        return "Dnes"
    if days == 1:
        return "Včera"
    if days < 14:
        return f"pred {days} dňami"
    if days < 28:
        return f"pred {days // 7} týždňami"
    return f"{posted.day}. {posted.month}. {posted.year}"
