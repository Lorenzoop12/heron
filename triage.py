from email import message_from_string, policy
from email.utils import parseaddr
import re
import os
import sys

W_REPLY_TO_MISMATCH = 2

W_IP_LINK = 3

W_AUTH_FAIL = 2

W_BRAND_MISMATCH = 3

PHISHING_TRESHOLD = 5

SUSPICIOUS_TRESHOLD = 3

W_PUNYCODE_LINK = 3

W_KEYWORD = 1

BRANDS = ["paypal", "microsoft", "amazon"]

KEYWORDS = ["urgent", "verify", "suspended", "password", "expires", "act now",
            "congratulations", "winner", "claim", "immediately", "gift card"]

def sender_domain(header_value):
    """Returns the domain of an email address, or '?' if missing."""

    _, address = parseaddr(header_value)
    if "@" not in address:
        return None
    return address.split("@", 1)[1].lower()

def compute_verdict(score):
    """Map a score to a verdict."""

    if score >= PHISHING_TRESHOLD:
        return "PHISHING"
    elif score >= SUSPICIOUS_TRESHOLD:
        return "suspicious"
    else:
        return "ok"

def keyword_score(raw):
    """Assign one point for each keyword found in the email."""

    low = raw.lower()
    return sum(W_KEYWORD for kw in KEYWORDS if kw in low)

def link_score(raw):
    """Assign one point for each link found in the email."""

    s = 0
    urls = re.findall("https?://[^\\s\"'<>]+", raw)
    for u in urls:
        if re.match("https?://[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+", u):
            s = s + W_IP_LINK  # ip address url, very bad
        if "xn--" in u:
            s = s + W_PUNYCODE_LINK
    return s

def brand_score(frm):
    """Assign one point for each brand found in the email."""

    s = 0
    for brand in BRANDS:
        if brand in frm.lower() and f"{brand}.com" not in frm.lower():
            s = s + W_BRAND_MISMATCH
    return s

def auth_score(raw):
    """Assign one point when SPF or DMARC fails."""

    low = raw.lower()
    if "spf" not in low and "dmarc" not in low:
        return W_AUTH_FAIL
    return 0

def reply_to_score(frm, reply_to):
    """Assign one point when sender and reply-to fields mismatch."""

    from_domain = sender_domain(frm)
    reply_domain = sender_domain(reply_to)

    if from_domain and reply_domain and from_domain != reply_domain:
        return W_REPLY_TO_MISMATCH
    return 0

def score_email(raw):
    """Computes the score based on the indicators, given an email message."""

    msg = message_from_string(raw, policy=policy.default)
    frm = str(msg.get("From", ""))
    reply_to = str(msg.get("Reply-To", ""))

    score = (keyword_score(raw) + link_score(raw) + brand_score(frm) + auth_score(raw) + reply_to_score(frm, reply_to))
    return score

def check_mail(folder="/Users/Utente/PycharmProjects/heron/data/samples"):
    """Stores every email file in the given folder.
    Returns (file name, verditct, score) tuples."""

    scores = {}
    verdicts = []

    files = os.listdir(folder)
    for fn in files:
        if not fn.endswith(".eml"):
            continue
        with open(folder + "/" + fn, encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        s = score_email(raw)

        scores[fn] = s
        verdicts.append((fn, compute_verdict(s), s))

    return verdicts

def report(verdicts):
    """Prints the verdicts and saves them to the results file."""

    print("checked", len(verdicts), "mails")

    for v in verdicts:
        print(" ", v[0], "->", v[1], "(score", str(v[2]) + ")")
    with open("results.txt", "a") as out:
        out.write(str(verdicts))
    print("flagged:", [v[0] for v in verdicts if v[1] == "PHISHING"])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("You have to pass a folder as argument")
        sys.exit(2)
    try:
        verdicts = check_mail(sys.argv[1])
        report(verdicts)
    except FileNotFoundError:
        print("Error: folder not found", file=sys.stderr)