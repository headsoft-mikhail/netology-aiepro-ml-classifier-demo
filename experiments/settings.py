from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from classifier.settings import PROJECT_ROOT


class MLPParameters(BaseModel):
    hidden_layers: list[int] = Field(default_factory=lambda: [32], min_length=1)
    dropout: float = Field(default=0.0, ge=0, lt=1)
    learning_rate: float = Field(default=0.001, gt=0)
    max_epochs: int = Field(default=50, gt=0)
    patience: int = Field(default=10, gt=0)
    weight_decay: float = Field(default=0.0, ge=0)
    use_class_weights: bool = False


class ExperimentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    random_state: int = Field(default=42, ge=0, le=2**32 - 1)
    batch_size: int = Field(default=32, gt=0)
    neural_hidden_size: int = Field(default=32, gt=0)
    neural_learning_rate: float = Field(default=0.001, gt=0)
    neural_max_epochs: int = Field(default=50, gt=0)
    neural_patience: int = Field(default=10, gt=0)
    neural_mlflow_experiment_name: str = "neural_classifiers"
    neural_optuna_budget: int = Field(default=25, gt=0)
    neural_search_max_epochs: int = Field(default=150, gt=0)
    neural_search_patience: int = Field(default=20, gt=0)
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
