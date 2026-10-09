"""Command-line interface: ``python -m heron <path>``."""

import argparse
import json
import logging
import sys
import uuid
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError

from heron.config import Settings
from heron.logs import configure_logging, request_id
from heron.models import TriageResult, Verdict
from heron.parser import parse_eml
from heron.scorer import triage
from heron.storage import VerdictStore

logger = logging.getLogger("heron")


def build_parser() -> argparse.ArgumentParser:
    """Return the parser of the command-line arguments."""
    parser = argparse.ArgumentParser(prog="heron", description="Triage phishing emails.")
    parser.add_argument("path", type=Path, help="an .eml file or a folder of .eml files")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--db", help="also store the verdicts in this SQLite file ($HERON_DB)")
    parser.add_argument("-v", "--verbose", action="store_true", help="log every verdict")
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
        settings = Settings()
    except ValidationError as exc:
        print(f"error: invalid configuration:\n{exc}", file=sys.stderr)
        return 2
    args = build_parser().parse_args(argv)
    configure_logging("DEBUG" if args.verbose else settings.log_level)
    request_id.set(uuid.uuid4().hex[:12])
    try:
        results = check_mail(args.path)
    except FileNotFoundError:
        print("error: no such file or folder:", args.path, file=sys.stderr)
        return 2
    for r in results:
        logger.debug(
            "verdict", extra={"email_id": r.email_id, "verdict": r.verdict, "score": r.score}
        )
    flagged = sum(1 for r in results if r.verdict != Verdict.BENIGN)
    logger.info("triaged %d emails, %d flagged", len(results), flagged, extra={"flagged": flagged})
    db = args.db or settings.db
    if db:
        store = VerdictStore(db)
        saved = store.save(results)
        store.close()
        logger.info("stored %d verdicts", saved, extra={"db": db})
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        report(results)
    return 0
