import json
from pathlib import Path

import pytest

from heron.cli import main

SAMPLES = Path(__file__).parent.parent / "data" / "samples"


def test_cli_triages_the_six_samples(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([str(SAMPLES)])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert out.splitlines()[-1] == "6 emails: 2 phishing, 1 suspicious, 3 benign"


def test_cli_json_gives_one_object_per_file(capsys: pytest.CaptureFixture[str]) -> None:
    main([str(SAMPLES / "prize-scam.eml"), "--json"])

    [result] = json.loads(capsys.readouterr().out)
    assert result["email_id"] == "prize-scam.eml"
    assert result["verdict"] == "suspicious"
    assert [f["code"] for f in result["findings"]] == ["urgency", "reply_to_mismatch"]


def test_cli_exits_with_2_for_a_missing_path(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["no/such/folder"]) == 2
    assert "no such file or folder" in capsys.readouterr().err
