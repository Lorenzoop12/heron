from dataclasses import dataclass
from enum import StrEnum

@dataclass(frozen=True)
class ParsedEmail:
    """Dataclass that holds the pased email attributes."""

    email_id : str
    sender : str
    from_domain : str | None
    reply_to_domain : str | None
    auth_results : str
    text : str
    links : tuple[str]

@dataclass(frozen=True)
class TriageResult:
    """The outcome of an email message."""

    email_id : str
    score: int
    verdict: "Verdict"

class Verdict(StrEnum):
    """Outcome verdict of the triage."""

    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    PHISHING = "phishing"