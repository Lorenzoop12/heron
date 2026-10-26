# quick phishing checker for the mail export - L. Garcia, march 2025
# TODO: make this nicer at some point
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

def header(raw, name):
    """Returns the value of the first occurrence of the 'name:' pattern in the
    email header, or '?' if missing."""

    match = re.search(name + ": (.*)", raw)
    if match is None:
        return "?"
    return match.group(1)

def sender_domain(address):
    """Returns the domain of an email address, or '?' if missing."""

    match = re.search("@([a-zA-Z0-9.-]+)", address)
    if match is None:
        return "?"
    return match.group(1)

def check_mail(folder="/Users/Utente/PycharmProjects/heron/data/samples", flagged=[]):

    if flagged is None:
        flagged = []

    scores = {}
    verdicts = []

    files = os.listdir(folder)
    for fn in files:
        if not fn.endswith(".eml"):
            continue
        with open(folder + "/" + fn, encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        s = 0

        frm = header(raw, "From")
        subj = header(raw, "Subject")

        low = raw.lower()
        for kw in KEYWORDS:
            if kw in low:
                s = s + W_KEYWORD
        # links that look bad
        urls = re.findall("https?://[^\\s\"'<>]+", raw)
        for u in urls:
            if re.match("https?://[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+", u):
                s = s + W_IP_LINK  # ip address url, very bad
            if "xn--" in u:
                s = s + W_PUNYCODE_LINK

        # sender says paypal/microsoft/amazon but domain is weird

        for brand in BRANDS:
            if brand in frm.lower() and f"{brand}.com" not in frm.lower():
                s = s + W_BRAND_MISMATCH

        if "spf=fail" in low or "dmarc=fail" in low:
            s = s + W_AUTH_FAIL

        # reply-to different from from

            from_domain = sender_domain(frm)
            reply_domain = sender_domain(header(raw, "Reply-To"))
            if from_domain and reply_domain and from_domain != reply_domain:
                s = s + W_REPLY_TO_MISMATCH

        scores[fn] = s
        if s >= PHISHING_TRESHOLD:
            verdicts.append((fn, "PHISHING", s))
            flagged.append(fn)
        elif s >= SUSPICIOUS_TRESHOLD:
            verdicts.append((fn, "suspicious", s))
        else:
            verdicts.append((fn, "ok", s))
    print("checked", len(scores), "mails")
    for v in verdicts:
        print(" ", v[0], "->", v[1], "(score", str(v[2]) + ")")

    with open("results.txt", "w") as out:
        out.write(str(verdicts))
    print("flagged:", flagged)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("You have to pass a folder as argument")
        sys.exit(2)
    try:
        check_mail(sys.argv[1])
    except FileNotFoundError:
        print("Error: folder not found", file=sys.stderr)