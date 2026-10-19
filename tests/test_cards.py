from aimscribe.indexer import load_cards


def test_cards_valid_and_unique():
    cards = load_cards()
    assert cards
    ids = [c.card_id for c in cards]
    assert len(ids) == len(set(ids))


def test_all_diseases_and_categories_covered():
    cards = load_cards()
    for d in ("dengue", "hypertension", "cholera", "chikungunya"):
        cats = {c.category for c in cards if c.disease == d}
        assert {
            "probable_diagnosis",
            "investigation",
            "medication",
            "advice",
        } <= cats, d
