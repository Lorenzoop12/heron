"""Compute the indicators scores and the classification outcome."""

from typing import Callable
from features import keyword_score, link_score, brand_score, auth_score, reply_to_score
from models import ParsedEmail, TriageResult, Verdict

SUSPICIOUS_TRESHOLD = 3
PHISHING_TRESHOLD = 5
ALL_CHECKS: tuple[Callable[[ParsedEmail], int], ...] = (
    keyword_score,
    link_score,
    brand_score,
    auth_score,
    reply_to_score
)

def triage(email: ParsedEmail) -> TriageResult:
    """Runs all checks on the email and returns the triage result."""

    score = sum(check(email) for check in ALL_CHECKS)
    return TriageResult(
        email_id=email.email_id,
        score=score,
        verdict=compute_verdict(score)
    )

def compute_verdict(score: int) -> Verdict:
    """Map a score to a verdict."""

    if score >= PHISHING_TRESHOLD:
        return Verdict.PHISHING
    elif score >= SUSPICIOUS_TRESHOLD:
        return Verdict.SUSPICIOUS
    else:
        return Verdict.BENIGN