import logging
import os
import typing
from importlib.metadata import version

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from classifier.pipeline import dataset_schema
from classifier.pipeline.dataset_schema import DatasetSchema
from classifier.pipeline.models import ModelMetadata
from classifier.pipeline.settings import MLflowSettings, PipelineSettings, RandomForestSettings

LOGGER_OBJ: typing.Final = logging.getLogger(__name__)


class ClassificationEvaluation(BaseModel):
    metrics: dict[str, float]
    report: dict[str, typing.Any]
    confusion: list[list[int]]
    labels: list[str]


def evaluate_classifier(
    y_true: pd.Series,
    y_pred,
    target: dataset_schema.ClassificationTarget,
) -> ClassificationEvaluation:
    mapping: typing.Final = target.mappings
    labels: typing.Final = list(mapping)
    report: typing.Final = classification_report(
        y_true,
        y_pred,
        labels=labels,
        target_names=target.categories(),
        output_dict=True,
        zero_division=0,
    )
    metrics: typing.Final = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)),
        "macro_precision": float(report["macro avg"]["precision"]),
        "macro_recall": float(report["macro avg"]["recall"]),
    }
    for name in target.categories():
        for metric, report_key in [("precision", "precision"), ("recall", "recall"), ("f1", "f1-score")]:
            metrics[f"{name}_{metric}"] = float(report[name][report_key])
    return ClassificationEvaluation(
        metrics=metrics,
        report=report,
        confusion=confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        labels=target.categories(),
    )


def train_and_log() -> None:
    pipeline_settings: typing.Final = PipelineSettings()
    schema: typing.Final = DatasetSchema()
    random_forest_settings: typing.Final = RandomForestSettings()
    mlflow_settings: typing.Final = MLflowSettings()
    for variable in ["NO_PROXY", "no_proxy"]:
        os.environ[variable] = ",".join(
            filter(None, [os.environ.get(variable, ""), "localhost", "127.0.0.1", mlflow_settings.host]),
        )
    os.environ["MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT"] = "true"
    os.environ["MLFLOW_PRINT_MODEL_URLS_ON_CREATION"] = "false"
    logging.getLogger("mlflow").setLevel(logging.ERROR)
    mlflow.set_tracking_uri(mlflow_settings.tracking_uri)
    mlflow.set_experiment(pipeline_settings.experiment_name)

    splits: typing.Final = {
        name: pd.read_csv(pipeline_settings.prepared_dir / f"{name}.csv") for name in ["train", "validation", "test"]
    }
    train: typing.Final = splits["train"]
    features: typing.Final = schema.feature_columns
    model_requirements: typing.Final = [
        f"{package}=={version(package)}" for package in ["scikit-learn", "numpy", "pandas", "cloudpickle"]
    ]
    pipeline_settings.models_dir.mkdir(parents=True, exist_ok=True)
    pipeline_settings.reports_dir.mkdir(parents=True, exist_ok=True)
    rows: typing.Final = []

    for target in dataset_schema.ClassificationTarget:
        configurations = {
            "baseline": random_forest_settings.baseline,
            "selected": random_forest_settings.selected[target],
        }
        for variant, parameters in configurations.items():
            LOGGER_OBJ.info("Обучение %s: %s", target.value, variant)
            model = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "classifier",
                        RandomForestClassifier(
                            **parameters.model_dump(),
                            random_state=pipeline_settings.random_state,
                            n_jobs=pipeline_settings.n_jobs,
                        ),
                    ),
                ],
            )
            with mlflow.start_run(run_name=f"{target.value}_{variant}") as run:
                mlflow.set_tags({"target": target.value, "role": variant})
                mlflow.log_params({**parameters.model_dump(), "random_state": pipeline_settings.random_state})
                model.fit(train[features], train[target.value])
                evaluations = {}
                for name, part in splits.items():
                    evaluation = evaluate_classifier(
                        part[target.value],
                        model.predict(part[features]),
                        target,
                    )
                    evaluations[name] = evaluation
                    mlflow.log_metrics({f"{name}_{key}": value for key, value in evaluation.metrics.items()})
                    mlflow.log_dict(evaluation.model_dump(), f"{name}/evaluation.json")
                    rows.append(
                        {
                            "target": target.value,
                            "variant": variant,
                            "split": name,
                            **{
                                key: evaluation.metrics[key]
                                for key in [
                                    "accuracy",
                                    "macro_f1",
                                    "weighted_f1",
                                    "macro_precision",
                                    "macro_recall",
                                ]
                            },
                        },
                    )
                    LOGGER_OBJ.info(
                        "%s %s %s: macro-F1=%.3f, weighted-F1=%.3f, accuracy=%.3f",
                        target.value,
                        variant,
                        name,
                        evaluation.metrics["macro_f1"],
                        evaluation.metrics["weighted_f1"],
                        evaluation.metrics["accuracy"],
                    )
                mlflow.sklearn.log_model(
                    model,
                    name="model",
                    input_example=train[features].head(5),
                    pip_requirements=model_requirements,
                    serialization_format="cloudpickle",
                )
                if variant == "selected":
                    path = pipeline_settings.models_dir / f"{target.value.lower()}.joblib"
                    joblib.dump(model, path)
                    metadata = ModelMetadata(
                        target=target,
                        features=features,
                        target_mapping=target.mappings,
                        params=model.named_steps["classifier"].get_params(),
                        random_state=pipeline_settings.random_state,
                        mlflow_run_id=run.info.run_id,
                        validation_metrics=evaluations["validation"].metrics,
                        test_metrics=evaluations["test"].metrics,
                    )
                    path.with_suffix(".json").write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv(pipeline_settings.reports_dir / "trained_classifier_comparison_metrics.csv", index=False)
    LOGGER_OBJ.info("Модели: %s; отчёты: %s", pipeline_settings.models_dir, pipeline_settings.reports_dir)
