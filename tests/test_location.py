from jobscout.location import normalize_text, region_match, tidy_location


def test_normalize_text_collapses_whitespace_and_lowercases():
    assert normalize_text("  Wien\n 1010 &amp; Umgebung ") == "wien 1010 & umgebung"


def test_vienna_bare_city_has_no_district():
    assert region_match("Wien") == "Vienna"
    assert region_match("Vienna, Austria") == "Vienna"


def test_vienna_district_from_postal_code():
    assert region_match("1200 Wien, Brigittenau") == "Vienna 20"
    assert region_match("1010") == "Vienna 1"
    assert region_match("1030 Wien") == "Vienna 3"
    assert region_match("1230 Wien, Liesing") == "Vienna 23"


def test_vienna_district_from_name():
    assert region_match("Favoriten") == "Vienna 10"
    assert region_match("Wien, Landstraße") == "Vienna 3"
    assert region_match("Rudolfsheim-Fünfhaus") == "Vienna 15"


def test_tidy_location_collapses_repeated_neighbours():
    assert tidy_location("Vienna, Vienna, Austria") == "Vienna, Austria"
    assert tidy_location("Bratislava, Bratislava, Slovakia") == "Bratislava, Slovakia"
    assert tidy_location("Wien") == "Wien"
    assert tidy_location("Prague 9, Prague, Czechia") == "Prague 9, Prague, Czechia"
    assert tidy_location("") == ""


def test_bratislava_borough_not_mistaken_for_vienna_district():
    assert region_match("Bratislava - Ružinov") == "Bratislava"


def test_bratislava_city_and_boroughs():
    assert region_match("Bratislava") == "Bratislava"
    assert region_match("Petržalka") == "Bratislava"
    assert region_match("Bratislava-Dúbravka 1187/, Bratislava") == "Bratislava"


def test_kittsee_border_towns():
    assert region_match("Kittsee") == "Kittsee area"
    assert region_match("Hainburg an der Donau") == "Kittsee area"
    assert region_match("Bruck an der Leitha") == "Kittsee area"
    assert region_match("Parndorf") == "Kittsee area"


def test_unspecified_regions_respect_flag():
    assert region_match("Bratislavský kraj", True) == "Bratislava region"
    assert region_match("Bratislavský kraj", False) is None
    assert region_match("Wien-Umgebung", True) == "Vienna region"
    assert region_match("Wien-Umgebung", False) is None


def test_explicit_city_beats_unspecified():
    assert region_match("Bratislavský kraj, Bratislava", True) == "Bratislava"


def test_out_of_scope_places_return_none():
    assert region_match("Košice") is None
    assert region_match("Graz") is None
    assert region_match("Eisenstadt") is None
    assert region_match("Sankt Pölten") is None
    assert region_match("") is None


def test_slovak_town_named_like_vienna_district_is_not_vienna():
    # A Slovak address that happens to contain "Berg" style tokens should not
    # be pulled into Vienna via a district-name collision.
    assert region_match("Slovenská republika, Nové Mesto nad Váhom") is None
