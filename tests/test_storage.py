from concurrent.futures import ThreadPoolExecutor
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


def test_the_store_works_from_another_thread(tmp_path: Path) -> None:
    # FastAPI may open the store in one worker thread and use it in another
    store = VerdictStore(tmp_path / "v.db")
    with ThreadPoolExecutor(max_workers=1) as pool:
        assert pool.submit(store.count).result() == 0
    store.close()
