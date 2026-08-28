from jobscout.collation import slovak_sort_key


def sorted_sk(words):
    return sorted(words, key=slovak_sort_key)


def test_c_hacek_sorts_right_after_c_not_after_z():
    words = ["cyklista", "čaj", "auto", "zebra", "cukor"]
    assert sorted_sk(words) == ["auto", "cukor", "cyklista", "čaj", "zebra"]


def test_ch_digraph_sorts_after_h():
    assert sorted_sk(["hodina", "chlieb", "iris"]) == ["hodina", "chlieb", "iris"]
    # every "h..." word precedes every "ch..." word
    assert sorted_sk(["chata", "hzzz"]) == ["hzzz", "chata"]


def test_other_hacek_letters():
    assert sorted_sk(["sto", "šterk", "tir"]) == ["sto", "šterk", "tir"]
    assert sorted_sk(["zima", "žaba"]) == ["zima", "žaba"]


def test_accented_vowels_file_next_to_base_letter():
    assert sorted_sk(["ada", "áda", "aby"]) == ["aby", "ada", "áda"]
    assert sorted_sk(["a", "ä", "b"]) == ["a", "ä", "b"]


def test_case_insensitive():
    assert sorted_sk(["Čokoláda", "cesta"]) == ["cesta", "Čokoláda"]


def test_non_alphabet_characters_sort_last():
    assert sorted_sk(["auto", "zebra", "3M"]) == ["auto", "zebra", "3M"]


def test_company_names_realistic_order():
    names = ["Zentiva", "Čapka Lab", "Bekaert", "Chemosvit", "Hameln"]
    assert sorted_sk(names) == ["Bekaert", "Čapka Lab", "Hameln", "Chemosvit", "Zentiva"]
