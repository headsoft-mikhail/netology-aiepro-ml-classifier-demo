import dataclasses
import logging
import typing

import pandas as pd

from classifier.api import models
from classifier.api.repositories.cache_repository import AppCache
from classifier.pipeline import dataset_schema

LOGGER_OBJ: typing.Final = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class PredictionsRepository:
    app_cache: AppCache

    def predict(self, request: models.PredictRequest) -> models.PredictResponse:
        categories: typing.Final = {}
        values: typing.Final = request.features.model_dump()
        for target in dataset_schema.ClassificationTarget:
            classifier = self.app_cache.classifiers[target]
            inputs = pd.DataFrame([values], columns=classifier.feature_names_in_)
            code = int(classifier.predict(inputs)[0])
            categories[target] = models.Category(code=code, label=target.mapping(code))
        return models.PredictResponse(
            prediction=models.AnalysisClassification(
                pattern=categories[dataset_schema.ClassificationTarget.CLASS],
                nsp=categories[dataset_schema.ClassificationTarget.NSP],
            ),
        )
