from formatter import normalize_title


def test_normalize_title() -> None:
    assert normalize_title("correct by construction") == "Correct By Construction"
