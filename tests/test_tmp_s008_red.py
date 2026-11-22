"""TYMCZASOWY test S-008 – celowo czerwony; PR zostanie zamknięty."""


def test_deliberately_red() -> None:
    expected_sum = 3
    assert expected_sum == 1 + 1, "S-008: czerwone CI ma blokować scalenie"
