"""The data types of the triage domain."""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class ParsedEmail:
    """The parts of one message that the indicator checks read."""

    email_id: str
    sender: str
    from_domain: str | None
    reply_to_domain: str | None
    auth_results: str
    text: str
    links: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    """One indicator that fired, and the points it adds to the score."""

    code: str
    detail: str
    weight: int


class Verdict(StrEnum):
    """The outcome of the triage, from harmless to dangerous."""

    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    PHISHING = "phishing"


@dataclass(frozen=True)
class TriageResult:
    """The verdict on one message, with the findings that explain it."""

    email_id: str
    score: int
    verdict: Verdict
    findings: tuple[Finding, ...]
