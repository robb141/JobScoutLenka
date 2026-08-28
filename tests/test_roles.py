from jobscout.roles import match_role, role_terms


ROLES = [
    "Biochemist",
    "Biochemistry",
    "Molecular biology",
    "Analytical chemist",
    "Laboratory technician",
    "QC analyst",
    "Microbiologist",
    "Biochemik",
    "Laborant",
    "Chemiker",
    "Qualitätskontrolle",
]


def test_generic_and_seniority_words_are_stripped():
    terms = dict(role_terms(ROLES))
    assert terms["biochemist"] == "Biochemist"
    assert terms["laboratory"] == "Laboratory technician"  # "technician" stripped
    assert terms["analytical chemist"] == "Analytical chemist"
    assert terms["qc"] == "QC analyst"  # "analyst" stripped


def test_diacritics_are_ignored_on_both_sides():
    assert match_role("Biochemik do laboratória", ROLES) == "Biochemik"
    assert match_role("Junior Biochémik", ["Biochemik"]) == "Biochemik"
    assert match_role("Stelle: Qualitatskontrolle Pharma", ROLES) == "Qualitätskontrolle"


def test_inflected_endings_still_match_the_stem():
    # Slovak / German inflect the stem; the term "laborant" must still hit.
    assert match_role("Zdravotnícky laborant/laborantka", ["Laborant"]) == "Laborant"
    assert match_role("Farmaceutický laboranta hľadáme", ["Laborant"]) == "Laborant"
    assert match_role("Wir suchen einen Chemiker", ["Chemik"]) == "Chemik"
    # ...but an unrelated longer word is still rejected.
    assert match_role("Laboratórne vybavenie na predaj", ["Laborant"]) == ""


def test_gender_tags_in_titles_do_not_break_matching():
    assert match_role("Biochemiker (m/w/d)", ["Biochemiker"]) == "Biochemiker"
    assert match_role("Laborant/ka - Bratislava", ["Laborant"]) == "Laborant"
    assert match_role("Chemik/chemička vo výrobe", ["Chemik"]) == "Chemik"


def test_word_boundaries_prevent_substring_hits():
    assert match_role("Chemické čistenie / dry cleaning", ["Chemik"]) == ""
    assert match_role("Microbiological safety cabinet sales", ["Microbiologist"]) == ""


def test_longer_terms_win_over_shorter():
    assert match_role("analytical chemist wanted", ROLES) == "Analytical chemist"


def test_no_match_returns_empty():
    assert match_role("Účtovník / Buchhalter", ROLES) == ""


def test_role_without_specific_words_uses_whole_role():
    assert dict(role_terms(["Scientist"])) == {"scientist": "Scientist"}
    assert match_role("scientist wanted", ["Scientist"]) == "Scientist"
