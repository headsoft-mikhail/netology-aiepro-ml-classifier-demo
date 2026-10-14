import typing
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from classifier.pipeline import dataset_schema


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SERVICE_")

    models_dir: Path = Path(dataset_schema.PROJECT_ROOT, "runtime/models")
    database_path: Path = Path(dataset_schema.PROJECT_ROOT, "runtime/service/analyses.db")
    demo_cases_path: Path = Path(__file__).parent / "resources/demo_cases.csv"


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_")

    host: str = "127.0.0.1"
    port: int = Field(default=8001, ge=1, le=65535)
    frontend_dir: Path = Path(__file__).resolve().parent.parent / "frontend"
    log_level: typing.Literal["critical", "error", "warning", "info", "debug"] = "info"


service_settings: typing.Final = ServiceSettings()
api_settings: typing.Final = APISettings()
