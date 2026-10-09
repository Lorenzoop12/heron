import pytest
from pydantic import ValidationError

from heron.cli import main
from heron.config import Settings


def test_defaults_work_without_any_configuration() -> None:
    settings = Settings()
    assert (settings.db, settings.log_level) == (None, "INFO")


def test_values_come_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERON_DB", "verdicts.db")
    monkeypatch.setenv("HERON_LOG_LEVEL", "DEBUG")
    settings = Settings()
    assert (settings.db, settings.log_level) == ("verdicts.db", "DEBUG")


def test_the_secret_is_hidden_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "not-a-real-key")
    settings = Settings()
    assert "not-a-real-key" not in repr(settings)
    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "not-a-real-key"


def test_a_bad_value_fails_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERON_LOG_LEVEL", "LOUD")
    with pytest.raises(ValidationError):
        Settings()


def test_cli_rejects_bad_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("HERON_LOG_LEVEL", "LOUD")
    assert main(["."]) == 2
    assert "invalid configuration" in capsys.readouterr().err
