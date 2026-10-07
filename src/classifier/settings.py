import typing
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT: typing.Final = Path(__file__).resolve().parents[2]


class WorkspaceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore", populate_by_name=True)

    @property
    def workspace(self) -> Path:
        return PROJECT_ROOT / "runtime"
