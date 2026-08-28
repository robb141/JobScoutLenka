from datetime import date

from jobscout.dates import posted_label_sk, posted_sort_key


TODAY = date(2026, 8, 28)


def test_now_and_today_map_to_today():
    assert posted_sort_key("NEW", TODAY) == "2026-08-28"
    assert posted_sort_key("Teraz", TODAY) == "2026-08-28"
    assert posted_sort_key("Dnes", TODAY) == "2026-08-28"
    assert posted_sort_key("heute", TODAY) == "2026-08-28"


def test_yesterday_sk_and_de():
    assert posted_sort_key("Včera", TODAY) == "2026-08-27"
    assert posted_sort_key("gestern", TODAY) == "2026-08-27"


def test_iso_and_dmy_dates():
    assert posted_sort_key("2026-08-01", TODAY) == "2026-08-01"
    assert posted_sort_key("1. 8. 2026", TODAY) == "2026-08-01"
    assert posted_sort_key("28.08.2026", TODAY) == "2026-08-28"


def test_relative_days_sk_and_de():
    assert posted_sort_key("Pred 3 dňami", TODAY) == "2026-08-25"
    assert posted_sort_key("vor 7 Tagen veröffentlicht", TODAY) == "2026-08-21"
    assert posted_sort_key("3 days ago", TODAY) == "2026-08-25"


def test_relative_weeks_and_hours():
    assert posted_sort_key("pred týždňom", TODAY) == "2026-08-21"
    assert posted_sort_key("vor 2 Wochen", TODAY) == "2026-08-14"
    assert posted_sort_key("vor 5 Stunden", TODAY) == "2026-08-28"
    assert posted_sort_key("Pred 2 minútami", TODAY) == "2026-08-28"


def test_unknown_is_empty():
    assert posted_sort_key("", TODAY) == ""
    assert posted_sort_key("ktovie", TODAY) == ""


def test_invalid_calendar_date_is_empty():
    assert posted_sort_key("31. 2. 2026", TODAY) == ""


def test_posted_label_sk_normalises_every_language_to_slovak():
    assert posted_label_sk("NEW", TODAY) == "Dnes"
    assert posted_label_sk("Heute veröffentlicht", TODAY) == "Dnes"
    assert posted_label_sk("Teraz", TODAY) == "Dnes"
    assert posted_label_sk("gestern", TODAY) == "Včera"
    assert posted_label_sk("vor 3 Tagen veröffentlicht", TODAY) == "pred 3 dňami"
    assert posted_label_sk("1 week ago", TODAY) == "pred 7 dňami"
    assert posted_label_sk("vor 2 Wochen", TODAY) == "pred 2 týždňami"
    # anything older falls back to a Slovak-formatted absolute date
    assert posted_label_sk("2026-07-01", TODAY) == "1. 7. 2026"
    assert posted_label_sk("", TODAY) == ""
    assert posted_label_sk("kdovie", TODAY) == ""
