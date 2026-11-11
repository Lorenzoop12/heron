from hypothesis import given
from hypothesis import strategies as st

from heron.features import levenshtein


@given(a=st.text(), b=st.text())
def test_levenshtein_properties(a: str, b: str) -> None:
    distance = levenshtein(a, b)

    assert distance == levenshtein(b, a) # symmetry
    assert abs(len(a) - len(b)) <= distance <= max(len(a), len(b)) # bounds
    assert (distance == 0) == (a == b) # zero only for equal words