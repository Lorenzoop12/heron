from pathlib import Path

from heron.cli import main
from heron.models import ParsedEmail
from heron.scorer import triage
from heron.storage import VerdictStore

SAMPLES = Path(__file__).parent.parent / "data" / "samples"


def test_results_roundtrip(tmp_path: Path, phishing_email: ParsedEmail) -> None:
    store = VerdictStore(tmp_path / "v.db")
    assert store.save([triage(phishing_email)]) == 1
    assert store.count() == 1
    assert store.count(verdict="phishing") == 1
    assert store.count(verdict="benign") == 0
    store.close()


def test_cli_stores_every_verdict(tmp_path: Path) -> None:
    db = tmp_path / "out.db"
    assert main([str(SAMPLES), "--db", str(db)]) == 0
    assert main([str(SAMPLES), "--db", str(db)]) == 0
    store = VerdictStore(db)
    assert (store.count(), store.count(verdict="phishing")) == (12, 4)
    store.close()
