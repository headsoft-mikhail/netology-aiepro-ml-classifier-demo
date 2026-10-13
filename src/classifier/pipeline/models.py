import typing

from pydantic import BaseModel, Field

from classifier.pipeline import dataset_schema


class RandomForestParameters(BaseModel):
    n_estimators: int = Field(gt=0)
    max_depth: int | None = Field(gt=0)
    min_samples_split: int = Field(ge=2)
    min_samples_leaf: int = Field(ge=1)
    max_features: typing.Literal["sqrt", "log2"] | float
    class_weight: typing.Literal["balanced", "balanced_subsample"] | None


class ModelMetadata(BaseModel):
    target: dataset_schema.ClassificationTarget
    model_type: str = "RandomForestClassifier"
    features: list[str]
    target_mapping: dict[int, str]
    params: dict[str, typing.Any]
    random_state: int
    mlflow_run_id: str
    validation_metrics: dict[str, float]
    test_metrics: dict[str, float]
