import pytest

from heron.features import levenshtein


def test_a_word_is_at_distance_zero_from_itself() -> None:
    assert levenshtein("paypal", "paypal") == 0


@pytest.mark.parametrize(
    ("a", "b", "distance"),
    [
        ("", "abc", 3),
        ("amazon", "", 6),
        ("paypal", "paypa1", 1),
        ("amazon", "amaz0n", 1),
        ("microsoft", "microsft", 1),
        ("ab", "ba", 2),
    ],
    ids=["insert-3", "delete-6", "replace-1", "digit-for-letter", "missing-letter", "swap-costs-2"],
)
def test_each_edit_costs_one(a: str, b: str, distance: int) -> None:
    assert levenshtein(a, b) == distance
