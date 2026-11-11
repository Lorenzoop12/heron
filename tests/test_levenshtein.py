import pytest

from heron.features import levenshtein


def test_distance_zero_with_identical_strings() -> None:
    assert levenshtein("paypal", "paypal") == 0


def test_distance_one_with_one_character_difference() -> None:
    assert levenshtein("paypa", "paypal") == 1
    assert levenshtein("paypal", "paypa") == 1
    assert levenshtein("paypa1", "paypal") == 1


@pytest.mark.parametrize(
    ("a", "b", "distance"),
    [
        ("paypa", "paypal", 1),
        ("paypal", "payp", 2),
        ("paypal", "pay", 3),
    ]
)
def test_multiple_distances(a:str, b:str, distance: int) -> None:
    assert levenshtein(a, b) == distance