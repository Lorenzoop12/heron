"""Launch heron with ``python -m heron <folder>``."""

import argparse
import json
import os
import sys
from dataclasses import asdict

from scorer import triage
from parser import parse_eml
from models import TriageResult

def build_parser() -> argparse.ArgumentParser:
    """Returns the parser of the CLI arguments."""

    parser = argparse.ArgumentParser(
        prog="heron",
        description="Triage of phishing."
    )
    parser.add_argument(
        "folder",
                    help="A folder containing the email files."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="machine-readable output"
    )
    return parser

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

def report(verdicts: list[TriageResult]) -> None:
    """Prints the verdicts and saves them to the results file."""

    for v in verdicts:
        print(f"{v.email_id:<28} {v.verdict} score={v.score}")


def main(argv: list[str] | None = None):
    """Run the triage on the given folder."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        verdicts = check_mail(args.folder)
        if args.json:
            with open("output.json", "w") as f:
                json.dump([asdict(v) for v in verdicts], f)
        report(verdicts)
    except FileNotFoundError:
        print("Error: folder not found", file=sys.stderr)