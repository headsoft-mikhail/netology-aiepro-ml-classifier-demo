import logging
import typing

import joblib

from classifier.api.settings import ServiceSettings
from classifier.pipeline import dataset_schema

LOGGER_OBJ: typing.Final = logging.getLogger(__name__)


def load_models(service_settings: ServiceSettings) -> dict[dataset_schema.ClassificationTarget, typing.Any]:
    classifiers: typing.Final = {
        target: joblib.load(service_settings.models_dir / "classical" / f"{target.value.lower()}.joblib")
        for target in dataset_schema.ClassificationTarget
    }
    LOGGER_OBJ.info("Загружены RandomForest для CLASS и NSP из %s", service_settings.models_dir)
    return classifiers
