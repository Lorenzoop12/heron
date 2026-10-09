"""Read the triage-relevant parts of a raw ``.eml`` message."""

import re
from email import message_from_string, policy
from email.utils import parseaddr

from heron.models import ParsedEmail

_URL_RE = re.compile("https?://[^\\s\"'<>]+")


def _domain(header_value: str) -> str | None:
    """Return the domain of the address in a From/Reply-To value, or None."""
    _, address = parseaddr(header_value)
    if "@" not in address:
        return None
    return address.rsplit("@", 1)[1].lower()


def parse_eml(raw: str, email_id: str) -> ParsedEmail:
    """Read one raw message once and keep only what the checks need.

    Parameters
    ----------
    raw : str
        The whole message, headers and body, as read from an ``.eml`` file.
    email_id : str
        The name of the message in the results, such as its file name.

    Returns
    -------
    ParsedEmail
        The parts of the message that the indicator checks read.
    """
    msg = message_from_string(raw, policy=policy.compat32)  # plain-text headers: never crash
    sender = str(msg.get("From", ""))
    return ParsedEmail(
        email_id=email_id,
        sender=sender,
        from_domain=_domain(sender),
        reply_to_domain=_domain(str(msg.get("Reply-To", ""))),
        auth_results=str(msg.get("Authentication-Results", "")).lower(),
        text=raw.lower(),
        links=tuple(_URL_RE.findall(raw)),
    )
