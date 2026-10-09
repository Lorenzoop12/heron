from heron.models import ParsedEmail, Verdict
from heron.scorer import PHISHING_THRESHOLD, SUSPICIOUS_THRESHOLD, triage, verdict_for
from tests.helpers import make_email


def test_suspicious_threshold_is_inclusive() -> None:
    assert verdict_for(SUSPICIOUS_THRESHOLD) == Verdict.SUSPICIOUS
    assert verdict_for(SUSPICIOUS_THRESHOLD - 1) == Verdict.BENIGN


def test_phishing_threshold_is_inclusive() -> None:
    assert verdict_for(PHISHING_THRESHOLD) == Verdict.PHISHING
    assert verdict_for(PHISHING_THRESHOLD - 1) == Verdict.SUSPICIOUS


def test_a_harmless_message_scores_zero() -> None:
    result = triage(make_email())
    assert result.score == 0
    assert result.verdict == Verdict.BENIGN
    assert result.findings == ()


def test_fixtures_are_injected_by_name(
    benign_email: ParsedEmail, phishing_email: ParsedEmail
) -> None:
    assert triage(benign_email).verdict == Verdict.BENIGN
    assert triage(phishing_email).verdict == Verdict.PHISHING


def test_the_score_is_the_sum_of_the_finding_weights(phishing_email: ParsedEmail) -> None:
    result = triage(phishing_email)
    assert result.score == sum(f.weight for f in result.findings)
    assert {f.code for f in result.findings} == {
        "urgency",
        "ip_link",
        "brand_mismatch",
        "auth_fail",
        "reply_to_mismatch",
        "lookalike_sender",
    }
