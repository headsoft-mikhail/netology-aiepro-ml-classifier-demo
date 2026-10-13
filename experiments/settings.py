import typing
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from classifier.pipeline import dataset_schema
from classifier.pipeline.settings import MLflowSettings


class ExperimentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXPERIMENT_")

    # Общие настройки.
    workbook_filename: str = "CTG.xls"
    raw_sheet_name: str = "Raw Data"
    random_state: int = Field(default=42, ge=0, le=2**32 - 1)
    # Классические модели: бюджет на каждую модель и каждую цель.
    classical_optuna_budget_stage_1: int = Field(default=25, gt=0)
    classical_optuna_budget_stage_2: int = Field(default=50, gt=0)
    classical_mlflow_experiment_name: str = "classical_classifiers"

    classical_n_jobs: int = -1
    classical_dummy_strategy: str = "most_frequent"
    classical_initial_parameters: dict[str, dict[str, typing.Any]] = Field(
        default_factory=lambda: {
            "LogisticRegression": {"max_iter": 2000},
            "LinearSVC": {"max_iter": 10000},
            "RandomForestClassifier": {"n_estimators": 200},
        },
    )
    classical_search_max_iter: int = Field(default=20000, gt=0)
    classical_model_selection_spaces: dict[str, dict[str, tuple[str, dict[str, typing.Any]]]] = Field(
        default_factory=lambda: {
            "RandomForestClassifier": {
                "n_estimators": ("int", {"low": 100, "high": 400, "step": 50}),
                "max_depth": ("categorical", {"choices": [None, 4, 8, 12, 20, 30]}),
                "min_samples_split": ("int", {"low": 2, "high": 12}),
                "min_samples_leaf": ("int", {"low": 1, "high": 10}),
                "max_features": ("categorical", {"choices": ["sqrt", "log2", 0.5, 1.0]}),
                "class_weight": ("categorical", {"choices": [None, "balanced"]}),
            },
            "LogisticRegression": {
                "C": ("float", {"low": 0.001, "high": 100.0, "log": True}),
                "class_weight": ("categorical", {"choices": [None, "balanced"]}),
                "solver": ("categorical", {"choices": ["lbfgs", "newton-cg"]}),
                "fit_intercept": ("categorical", {"choices": [True, False]}),
                "tol": ("float", {"low": 1e-06, "high": 0.001, "log": True}),
            },
            "LinearSVC": {
                "C": ("float", {"low": 0.001, "high": 100.0, "log": True}),
                "class_weight": ("categorical", {"choices": [None, "balanced"]}),
                "loss": ("categorical", {"choices": ["hinge", "squared_hinge"]}),
                "fit_intercept": ("categorical", {"choices": [True, False]}),
                "tol": ("float", {"low": 1e-06, "high": 0.001, "log": True}),
            },
        },
    )
    classical_selected_model_refinement_spaces: dict[str, dict[str, tuple[str, dict[str, typing.Any]]]] = Field(
        default_factory=lambda: {
            "CLASS": {
                "n_estimators": ("int", {"low": 50, "high": 200, "step": 50}),
                "max_depth": ("categorical", {"choices": [8, 12, 16]}),
                "min_samples_split": ("int", {"low": 4, "high": 8}),
                "min_samples_leaf": ("int", {"low": 1, "high": 3}),
                "max_features": ("categorical", {"choices": ["sqrt", "log2", 0.5, 1.0]}),
                "class_weight": ("categorical", {"choices": [None, "balanced"]}),
            },
            "NSP": {
                "n_estimators": ("int", {"low": 250, "high": 450, "step": 50}),
                "max_depth": ("categorical", {"choices": [16, 20, 24]}),
                "min_samples_split": ("int", {"low": 2, "high": 4}),
                "min_samples_leaf": ("int", {"low": 1, "high": 3}),
                "max_features": ("categorical", {"choices": ["sqrt", "log2", 0.5, 1.0]}),
                "class_weight": ("categorical", {"choices": [None, "balanced"]}),
            },
        },
    )
    # Нейросети: бюджет на каждую цель.
    neural_batch_size: int = Field(default=32, gt=0)
    neural_hidden_size: int = Field(default=32, gt=0)
    neural_learning_rate: float = Field(default=0.001, gt=0)
    neural_max_epochs: int = Field(default=50, gt=0)
    neural_patience: int = Field(default=10, gt=0)
    neural_mlflow_experiment_name: str = "neural_classifiers"
    neural_optuna_budget: int = Field(default=25, gt=0)
    neural_search_max_epochs: int = Field(default=150, gt=0)
    neural_search_patience: int = Field(default=20, gt=0)
    neural_architectures: dict[str, list[int]] = Field(
        default_factory=lambda: {
            "32": [32],
            "64": [64],
            "64–32": [64, 32],  # noqa: RUF001 — имена архитектур сохранены из экспериментов.
            "128–64": [128, 64],  # noqa: RUF001
            "64–32–16": [64, 32, 16],  # noqa: RUF001
        },
    )
    neural_dropout: float = Field(default=0.0, ge=0, lt=1)
    neural_weight_decay: float = Field(default=0.0, ge=0)
    neural_use_class_weights: bool = False
    neural_dropout_choices: list[float] = Field(default_factory=lambda: [0.0, 0.1, 0.2, 0.3])
    neural_learning_rate_range: tuple[float, float] = (0.0003, 0.01)
    neural_weight_decay_choices: list[float] = Field(default_factory=lambda: [0.0, 0.00001, 0.0001, 0.001, 0.01])
    neural_class_weight_choices: list[bool] = Field(default_factory=lambda: [False, True])

    @property
    def raw_dir(self) -> Path:
        return dataset_schema.PROJECT_ROOT / "runtime/data/raw"

    @property
    def prepared_dir(self) -> Path:
        return dataset_schema.PROJECT_ROOT / "runtime/data/prepared"

    @property
    def cleaned_path(self) -> Path:
        return self.prepared_dir / "ctg_cleaned.csv"

    @property
    def mlflow_tracking_uri(self) -> str:
        return MLflowSettings().tracking_uri
