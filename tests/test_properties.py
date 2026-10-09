from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from heron.features import BRANDS, KEYWORDS, check_lookalike_sender, levenshtein
from heron.models import ParsedEmail
from heron.parser import parse_eml
from heron.scorer import triage
from tests.helpers import make_email


@given(st.text(), st.text())
def test_levenshtein_is_symmetric_and_bounded(a: str, b: str) -> None:
    distance = levenshtein(a, b)
    assert distance == levenshtein(b, a)
    assert abs(len(a) - len(b)) <= distance <= max(len(a), len(b))
    assert (distance == 0) == (a == b)


domains = st.one_of(
    st.none(), st.from_regex(r"[a-z0-9]{1,10}([.-][a-z0-9]{1,10}){0,3}", fullmatch=True)
)
emails = st.builds(
    make_email,
    sender=st.text(max_size=60),
    from_domain=domains,
    reply_to_domain=domains,
    auth_results=st.sampled_from(
        ["spf=pass; dmarc=pass", "spf=fail", "dmarc=fail", "spf=softfail", ""]
    ),
    text=st.text(max_size=200),
    links=st.lists(
        st.sampled_from(
            ["http://192.0.2.1/x", "https://xn--pypal-4ve.com/", "https://example.com/"]
        )
    ).map(tuple),
)


@given(emails)
def test_the_score_is_never_negative_and_adds_up(email: ParsedEmail) -> None:
    result = triage(email)
    assert result.score >= 0
    assert result.score == sum(f.weight for f in result.findings)


@given(emails, st.sampled_from(KEYWORDS))
def test_a_pressure_word_never_lowers_the_score(email: ParsedEmail, keyword: str) -> None:
    louder = replace(email, text=email.text + " " + keyword)
    assert triage(louder).score >= triage(email).score


@given(st.sampled_from(BRANDS), st.sampled_from([".com", ".example", "-support.net"]))
def test_a_brand_never_imitates_itself(brand: str, rest: str) -> None:
    assert check_lookalike_sender(make_email(from_domain=brand + rest)) == []


header_lines = st.lists(
    st.tuples(
        st.sampled_from(["From", "Reply-To", "Authentication-Results"]),
        st.text(alphabet='az@<>":;,.[]=() ', max_size=20),
    ),
    max_size=4,
)


@given(header_lines)
def test_parser_never_crashes_on_odd_headers(lines: list[tuple[str, str]]) -> None:
    raw = "".join(f"{name}: {value}\n" for name, value in lines) + "\nbody\n"
    email = parse_eml(raw, "fuzz.eml")
    assert email.text == raw.lower()
