import typing
from pathlib import Path

import joblib
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier

from classifier.api import models
from classifier.api.repositories.cache_repository import AppCache
from classifier.api.repositories.predictions_repository import PredictionsRepository
from classifier.pipeline import dataset_schema


@pytest.fixture
def analysis_features() -> models.AnalysisFeatures:
    values: typing.Final = dict.fromkeys(dataset_schema.DatasetSchema().feature_columns, 1.0)
    values["Tendency"] = 0
    return models.AnalysisFeatures.model_validate(values)


@pytest.fixture
def model_directory(tmp_path, analysis_features) -> Path:
    (tmp_path / "classical").mkdir()
    columns: typing.Final = list(reversed(analysis_features.model_dump()))
    inputs: typing.Final = pd.DataFrame([analysis_features.model_dump()], columns=columns)
    for target in dataset_schema.ClassificationTarget:
        filename = target.value.lower()
        classifier = DummyClassifier(strategy="constant", constant=2).fit(inputs, [2])
        joblib.dump(classifier, tmp_path / "classical" / f"{filename}.joblib")
    return tmp_path


@pytest.fixture
def predictions_repository(model_directory) -> PredictionsRepository:
    return PredictionsRepository(
        app_cache=AppCache(
            classifiers={
                target: joblib.load(model_directory / "classical" / f"{target.value.lower()}.joblib")
                for target in dataset_schema.ClassificationTarget
            },
        ),
    )
