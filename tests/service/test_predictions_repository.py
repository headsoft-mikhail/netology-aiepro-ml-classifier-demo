import typing

import pytest
from pydantic import ValidationError

from classifier.api import models


def test_prediction_uses_selected_classifiers(predictions_repository, analysis_features):
    response: typing.Final = predictions_repository.predict(models.PredictRequest(features=analysis_features))
    assert response.model == "RandomForest"
    assert response.prediction.pattern.label == "B"
    assert response.prediction.nsp.label == "Suspect"
    assert "class" in response.model_dump(by_alias=True)["prediction"]


@pytest.mark.parametrize("invalid_value", [float("nan"), float("inf")])
def test_non_finite_measurement_is_rejected(analysis_features, invalid_value):
    with pytest.raises(ValidationError):
        models.AnalysisFeatures.model_validate({**analysis_features.model_dump(), "FM": invalid_value})


def test_true_labels_cannot_be_sent_as_features(analysis_features):
    with pytest.raises(ValidationError):
        models.AnalysisFeatures.model_validate({**analysis_features.model_dump(), "CLASS": 1, "NSP": 1})


def test_missing_measurement_is_rejected(analysis_features):
    values: typing.Final = analysis_features.model_dump()
    values.pop("LB")
    with pytest.raises(ValidationError):
        models.AnalysisFeatures.model_validate(values)
