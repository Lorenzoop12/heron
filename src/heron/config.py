"""Settings read from the environment (or a local ``.env`` file), checked at startup."""

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration. Field ``x`` is read from the variable ``HERON_X``."""

    model_config = SettingsConfigDict(env_prefix="HERON_", env_file=".env", extra="ignore")

    db: str | None = None  # SQLite file for the verdicts; None = do not store them
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # a secret, with its own name: SecretStr hides the value in repr() and in logs
    gemini_api_key: SecretStr | None = Field(default=None, validation_alias="GEMINI_API_KEY")
