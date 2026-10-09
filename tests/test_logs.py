import json
import logging
from pathlib import Path

import pytest

from heron.cli import main
from heron.logs import JsonFormatter, request_id

SAMPLES = Path(__file__).parent.parent / "data" / "samples"


def make_record(msg: str, **extra: object) -> logging.LogRecord:
    record = logging.makeLogRecord({"name": "heron", "levelname": "INFO", "msg": msg})
    record.__dict__.update(extra)
    return record


def test_each_line_is_valid_json_even_with_quotes_and_backslashes() -> None:
    line = JsonFormatter().format(make_record('subject "URGENT" from C:\\temp'))
    assert json.loads(line)["msg"] == 'subject "URGENT" from C:\\temp'


def test_extra_fields_and_the_request_id_are_included() -> None:
    token = request_id.set("abc123")
    try:
        data = json.loads(JsonFormatter().format(make_record("triaged", flagged=3)))
    finally:
        request_id.reset(token)
    assert (data["flagged"], data["request_id"]) == (3, "abc123")


def test_cli_writes_json_lines_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(SAMPLES), "-v"]) == 0
    lines = [json.loads(line) for line in capsys.readouterr().err.splitlines()]
    assert len([line for line in lines if line["msg"] == "verdict"]) == 6
    assert len({line["request_id"] for line in lines}) == 1  # one run, one id
    assert lines[-1]["flagged"] == 3
