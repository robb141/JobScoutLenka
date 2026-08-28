from jobscout.language import german_requirement


def test_explicit_cefr_level_is_picked_up():
    assert german_requirement("Deutsch B2 erforderlich") == "Nemčina B2"
    assert german_requirement("Deutschkenntnisse (C1)") == "Nemčina C1"
    assert german_requirement("gute Deutsch- und Englischkenntnisse") == "Nemčina: dobrá (B2)"


def test_fluency_phrases():
    assert german_requirement("verhandlungssicheres Deutsch") == "Nemčina: plynulá (C1+)"
    assert german_requirement("sehr gute Deutschkenntnisse") == "Nemčina: veľmi dobrá (C1)"
    assert german_requirement("Deutsch als Muttersprache") == "Nemčina: rodený hovoriaci"


def test_optional_and_none():
    assert german_requirement("Deutsch von Vorteil") == "Nemčina: základy / výhodou"
    assert german_requirement("Working language is English") == "Nemčina: netreba (angličtina)"


def test_bare_mention_falls_back_to_required():
    assert german_requirement("Sie sprechen Deutsch und Englisch") == "Nemčina: vyžaduje sa"


def test_no_mention_returns_empty():
    assert german_requirement("Lab Analyst for chemical testing, Vienna") == ""
    assert german_requirement("") == ""
