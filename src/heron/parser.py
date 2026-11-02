"""Read and parse relevant parts of the email file."""

import re
from email.utils import parseaddr
from email import message_from_string, policy
from models import ParsedEmail

_URL_RE = re.compile("https?://[^\\s\"'<>]+")

def parse_eml(raw: str, email_id: str) -> ParsedEmail:
    """Parse a raw email file and returns a data structure with the useful fields."""

    msg = message_from_string(raw, policy=policy.default)
    sender = str(msg.get("From", ""))
    reply_to = str(msg.get("Reply-To", ""))
    from_domain = _domain(sender)
    reply_to_domain = _domain(reply_to)
    auth_results = str(msg.get("Authentication-Results", "")).lower()
    links = tuple(re.findall(_URL_RE, raw))
    parsed_email = ParsedEmail(email_id=email_id,
                               sender=sender,
                               from_domain=from_domain,
                               reply_to_domain=reply_to_domain,
                               auth_results=auth_results,
                               text=raw.lower(),
                               links=links
                               )
    return parsed_email

def _domain(header_value: str) -> str | None:
    """Returns the domain of an email address, or None if '@' is missing."""

    _, address = parseaddr(header_value)
    if "@" not in address:
        return None
    return address.rsplit("@", 1)[1].lower()