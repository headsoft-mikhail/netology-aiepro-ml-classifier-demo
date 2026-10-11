from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from classifier.settings import PROJECT_ROOT


class ExperimentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    random_state: int = Field(default=42, ge=0, le=2**32 - 1)
    optuna_budget_stage_1: int = Field(default=25, gt=0)
    optuna_budget_stage_2: int = Field(default=50, gt=0)
    mlflow_port: int = Field(default=5001, gt=0, le=65535)
    mlflow_experiment_name: str = "classical_classifiers"

    @property
    def raw_dir(self) -> Path:
        return PROJECT_ROOT / "runtime/data/raw"

    @property
    def prepared_dir(self) -> Path:
        return PROJECT_ROOT / "runtime/data/prepared"

    @property
    def cleaned_path(self) -> Path:
        return self.prepared_dir / "ctg_cleaned.csv"

    @property
    def mlflow_tracking_uri(self) -> str:
        return f"http://127.0.0.1:{self.mlflow_port}"
