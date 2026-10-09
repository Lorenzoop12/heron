from collections.abc import Iterable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from heron.api import _WIRE_VERDICT, MAX_EML_CHARS, app, get_repository
from heron.models import TriageResult, Verdict

client = TestClient(app)
SAMPLES = Path(__file__).parent.parent / "data" / "samples"


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_triage_the_prize_scam() -> None:
    raw = (SAMPLES / "prize-scam.eml").read_text(encoding="utf-8")
    body = client.post("/triage", json={"raw_eml": raw, "email_id": "p.eml"}).json()
    assert (body["email_id"], body["verdict"], body["score"]) == ("p.eml", "suspicious", 4)
    assert [f["code"] for f in body["findings"]] == ["urgency", "reply_to_mismatch"]


def test_triage_validates_input() -> None:
    assert client.post("/triage", json={"raw_eml": ""}).status_code == 422
    assert client.post("/triage", json={"raw_eml": "definitely not an email"}).status_code == 422


class FakeRepository:
    """An in-memory VerdictRepository: no file, no SQLite."""

    def __init__(self) -> None:
        self.saved: list[TriageResult] = []

    def save(self, results: Iterable[TriageResult]) -> int:
        batch = list(results)
        self.saved.extend(batch)
        return len(batch)

    def count(self, verdict: str | None = None) -> int:
        return sum(1 for r in self.saved if verdict is None or r.verdict == verdict)


@pytest.fixture
def fake_repo() -> Iterator[FakeRepository]:
    repo = FakeRepository()
    app.dependency_overrides[get_repository] = lambda: repo
    yield repo
    app.dependency_overrides.clear()


def test_triage_saves_through_the_injected_repository(fake_repo: FakeRepository) -> None:
    raw = (SAMPLES / "prize-scam.eml").read_text(encoding="utf-8")
    client.post("/triage", json={"raw_eml": raw})
    assert [r.verdict for r in fake_repo.saved] == [Verdict.SUSPICIOUS]


def test_count_reads_the_injected_repository(fake_repo: FakeRepository) -> None:
    raw = (SAMPLES / "prize-scam.eml").read_text(encoding="utf-8")
    client.post("/triage", json={"raw_eml": raw})
    client.post("/triage", json={"raw_eml": raw})  # POST is not idempotent: two rows
    assert client.get("/verdicts/count").json() == {"count": 2}
    assert client.get("/verdicts/count", params={"verdict": "phishing"}).json() == {"count": 0}


def test_unknown_verdict_filter_is_rejected(fake_repo: FakeRepository) -> None:
    assert client.get("/verdicts/count", params={"verdict": "maybe"}).status_code == 422


def test_verdicts_count_unconfigured() -> None:
    response = client.get("/verdicts/count")
    assert response.status_code == 503
    assert response.json()["detail"] == "no verdict store configured"


def test_verdicts_persisted_via_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERON_DB", str(tmp_path / "api.db"))
    raw = (SAMPLES / "prize-scam.eml").read_text(encoding="utf-8")
    client.post("/triage", json={"raw_eml": raw})
    assert client.get("/verdicts/count").json() == {"count": 1}
    assert client.get("/verdicts/count", params={"verdict": "suspicious"}).json() == {"count": 1}


def test_errors_are_problem_details() -> None:
    response = client.post("/triage", json={"raw_eml": ""})
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert (body["status"], body["title"]) == (422, "Unprocessable Content")
    assert body["detail"] == "the request is not valid"
    assert body["errors"][0]["loc"] == ["body", "raw_eml"]


def test_wrong_method_is_a_problem_with_its_title() -> None:
    response = client.delete("/health")
    assert (response.status_code, response.json()["title"]) == (405, "Method Not Allowed")


def test_a_bad_setting_stops_the_service_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERON_LOG_LEVEL", "LOUD")
    with pytest.raises(ValidationError), TestClient(app):  # `with` runs the lifespan
        pass


def test_lifespan_logs_startup_and_shutdown(capsys: pytest.CaptureFixture[str]) -> None:
    with TestClient(app) as started:
        assert started.get("/health").status_code == 200
    err = capsys.readouterr().err
    assert "api starting" in err and "api stopping" in err


def test_a_request_id_is_generated_and_echoed() -> None:
    assert len(client.get("/health").headers["X-Request-ID"]) == 12


def test_a_well_formed_request_id_is_kept(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("INFO", logger="heron"):
        response = client.get("/health", headers={"X-Request-ID": "proxy-42"})
    assert response.headers["X-Request-ID"] == "proxy-42"
    (line,) = [r for r in caplog.records if r.getMessage() == "request"]
    assert (line.__dict__["path"], line.__dict__["status"]) == ("/health", 200)


def test_a_malformed_request_id_is_replaced() -> None:
    # the header is attacker-controlled and ends up in the logs: never copy it blindly
    response = client.get("/health", headers={"X-Request-ID": "x\n{fake log line}"})
    assert response.headers["X-Request-ID"] != "x\n{fake log line}"


def test_an_oversized_message_is_rejected_before_parsing() -> None:
    response = client.post("/triage", json={"raw_eml": "x" * (MAX_EML_CHARS + 1)})
    assert response.status_code == 422


def test_the_contract_lists_the_verdict_values() -> None:
    schema = client.get("/openapi.json").json()["components"]["schemas"]["TriageResponse"]
    assert schema["properties"]["verdict"]["enum"] == ["benign", "suspicious", "phishing"]
    assert set(_WIRE_VERDICT) == set(Verdict)
