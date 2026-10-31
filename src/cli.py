"""Launch heron with ``python -m heron <folder>``."""

import os
import sys
from scorer import triage
from parser import parse_eml
from models import TriageResult

def check_mail(folder: str) -> list[TriageResult]:
    """Stores every email file in the given folder.
    Returns (file name, verditct, score) tuples."""

    verdicts = []

    files = os.listdir(folder)
    for fn in files:
        if not fn.endswith(".eml"):
            continue
        with open(folder + "/" + fn, encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        parsed_email = parse_eml(raw, fn)
        result = triage(parsed_email)
        verdicts.append(result)

    return verdicts

def report(verdicts):
    """Prints the verdicts and saves them to the results file."""

    print("checked", len(verdicts), "mails")

    for v in verdicts:
        print(" ", v[0], "->", v[1], "(score", str(v[2]) + ")")
    with open("../results.txt", "a") as out:
        out.write(str(verdicts))
    print("flagged:", [v[0] for v in verdicts if v[1] == "PHISHING"])


def main(argv: list[str] | None = None):
    """Run the triage on the given folder."""

    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("You have to pass a folder as argument", file=sys.stderr)
        sys.exit(2)
    try:
        verdicts = check_mail(sys.argv[1])
        report(verdicts)
    except FileNotFoundError:
        print("Error: folder not found", file=sys.stderr)