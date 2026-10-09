from pathlib import Path

import pytest

from heron.models import ParsedEmail
from heron.parser import parse_eml

SAMPLES = Path(__file__).parent.parent / "data" / "samples"


def load(name: str) -> ParsedEmail:
    return parse_eml((SAMPLES / name).read_text(encoding="utf-8"), name)


def test_parser_reads_the_sender_and_reply_to_domains() -> None:
    email = load("paypal-impersonation.eml")
    assert email.email_id == "paypal-impersonation.eml"
    assert email.sender == '"PayPal Support" <security@paypa1-secure.net>'
    assert email.from_domain == "paypa1-secure.net"
    assert email.reply_to_domain == "mail-verify.net"


def test_parser_lowercases_the_authentication_results() -> None:
    email = load("paypal-impersonation.eml")
    assert "spf=fail" in email.auth_results
    assert email.auth_results == email.auth_results.lower()


def test_a_missing_reply_to_gives_none() -> None:
    assert load("internal-meeting.eml").reply_to_domain is None


def test_parser_finds_every_link_in_the_raw_text() -> None:
    assert load("paypal-impersonation.eml").links == (
        "http://192.0.2.44/login",
        "https://www.paypal.com/signin",
    )


def test_a_link_repeated_in_two_parts_is_found_twice() -> None:
    links = load("receipt.eml").links
    assert len(links) == 2
    assert links[0] == links[1]


def test_the_link_pattern_keeps_a_trailing_full_stop() -> None:
    # a known limit of the regular expression: the sentence's "." sticks to the URL
    assert "https://www.example-shop.com/preferences." in load("newsletter.eml").links


@pytest.mark.parametrize("raw", ["", "not an email", "From: a@\n\n", "From: <>\n\nbody"])
def test_parser_survives_broken_input(raw: str) -> None:
    email = parse_eml(raw, "broken.eml")
    assert email.from_domain is None
    assert email.reply_to_domain is None
