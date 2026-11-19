"""Command-line interface: ``python -m heron <path>``."""

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError
from pygments.lexers.robotframework import SETTING

from heron.config import Settings
from heron.models import TriageResult, Verdict
from heron.parser import parse_eml
from heron.scorer import triage


def build_parser() -> argparse.ArgumentParser:
    """Return the parser of the command-line arguments."""
    parser = argparse.ArgumentParser(prog="heron", description="Triage phishing emails.")
    parser.add_argument("path", type=Path, help="an .eml file or a folder of .eml files")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    return parser


def check_mail(path: Path) -> list[TriageResult]:
    """Triage one .eml file, or every .eml file in a folder, in name order."""
    files = sorted(path.glob("*.eml")) if path.is_dir() else [path]
    results = []
    for file in files:
        with open(file, encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        results.append(triage(parse_eml(raw, file.name)))
    return results


def report(results: list[TriageResult]) -> None:
    """Print each verdict with the findings behind it, then a summary."""
    for r in results:
        print(f"{r.email_id:<28} {r.verdict:<10} score={r.score}")
        for f in r.findings:
            print(f"    - {f.code} (+{f.weight}): {f.detail}")
    counts = Counter(r.verdict for r in results)
    print(
        f"{len(results)} emails: {counts[Verdict.PHISHING]} phishing, "
        f"{counts[Verdict.SUSPICIOUS]} suspicious, {counts[Verdict.BENIGN]} benign"
    )


def main(argv: list[str] | None = None) -> int:
    """Run the triage on the path given on the command line; return the exit code."""
    try:
        Settings()
    except ValidationError as e:
        print(f"error: invalid configuration:\n{e}", file=sys.stderr)
        return 2
    args = build_parser().parse_args(argv)
    try:
        results = check_mail(args.path)
    except FileNotFoundError:
        print("error: no such file or folder:", args.path, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        report(results)
    return 0
