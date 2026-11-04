"""Command-line interface for running Heron email triage."""

import argparse
import json
import os
import sys
from dataclasses import asdict
import re # noqa: F401

from heron.scorer import triage
from heron.parser import parse_eml
from heron.models import TriageResult


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser configured for the Heron CLI.
    """

    parser = argparse.ArgumentParser(prog="heron", description="Triage of phishing.")
    parser.add_argument("folder", help="A folder containing the email files.")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    return parser


def check_mail(folder: str) -> list[TriageResult]:
    """Run triage on all ``.eml`` files in a folder.

    Parameters
    ----------
    folder : str
        Path to the folder containing email files.

    Returns
    -------
    list[TriageResult]
        Triage results for every ``.eml`` file found.
    """

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
    """Print triage results to standard output.

    Parameters
    ----------
    verdicts : list[TriageResult]
        Triage results to display.
    """

    for v in verdicts:
        print(f"{v.email_id:<28} {v.verdict} score={v.score}")


def main(argv: list[str] | None = None): #type: ignore
    """Run the CLI entrypoint.

    Parameters
    ----------
    argv : list[str] | None, optional
        Argument list passed to the parser. If ``None``, arguments are
        read from ``sys.argv``.
    """

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
