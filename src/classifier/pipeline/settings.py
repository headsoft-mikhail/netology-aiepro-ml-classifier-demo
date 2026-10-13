from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from classifier.pipeline import dataset_schema
from classifier.pipeline.models import RandomForestParameters


class MLflowSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MLFLOW_")

    host: str = "127.0.0.1"
    port: int = Field(default=5001, gt=0, le=65535)

    @property
    def tracking_uri(self) -> str:
        return f"http://{self.host}:{self.port}"


class RandomForestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RANDOM_FOREST_",
        env_nested_delimiter="__",
        env_parse_none_str="None",
    )

    baseline: RandomForestParameters
    class_parameters: RandomForestParameters
    nsp_parameters: RandomForestParameters

    @property
    def selected(self) -> dict[dataset_schema.ClassificationTarget, RandomForestParameters]:
        return {
            dataset_schema.ClassificationTarget.CLASS: self.class_parameters,
            dataset_schema.ClassificationTarget.NSP: self.nsp_parameters,
        }


class PipelineSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PIPELINE_")

    source_url: str = "https://archive.ics.uci.edu/static/public/193/cardiotocography.zip"
    workbook_filename: str = "CTG.xls"
    raw_sheet_name: str = "Raw Data"
    timeout: float = Field(default=60, gt=0)
    runtime_dir: Path = Path(dataset_schema.PROJECT_ROOT, "runtime")
    random_state: int = Field(default=42, ge=0, le=2**32 - 1)
    n_jobs: int = -1
    experiment_name: str = "classical_pipeline"

    @property
    def raw_dir(self) -> Path:
        return self.runtime_dir / "data/raw"

    @property
    def prepared_dir(self) -> Path:
        return self.runtime_dir / "data/prepared"

    @property
    def models_dir(self) -> Path:
        return self.runtime_dir / "models/classical"

    @property
    def reports_dir(self) -> Path:
        return self.runtime_dir / "reports"
