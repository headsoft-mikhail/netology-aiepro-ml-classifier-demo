import dataclasses
import logging
import secrets
import sqlite3
import typing
from datetime import UTC, datetime

from classifier.api import models
from classifier.api.repositories.analysis_repository import AnalysisRepository
from classifier.api.repositories.cache_repository import AppCache
from classifier.api.repositories.predictions_repository import PredictionsRepository

LOGGER_OBJ: typing.Final = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubmitDemoRecordUseCase:
    app_cache: AppCache
    predictions_repository: PredictionsRepository
    analysis_repository: AnalysisRepository

    def __call__(self, request: models.SubmitDemoRequest) -> models.AnalysisDetails | None:
        case: typing.Final = self.app_cache.demo_cases.get(request.case_id)
        if case is None:
            return None
        prediction: typing.Final = self.predictions_repository.predict(models.PredictRequest(features=case.features))
        while True:
            record = models.AnalysisDetails(
                record_id=secrets.token_hex(4),
                case_id=case.case_id,
                created_at=datetime.now(UTC),
                prediction=prediction.prediction,
                reference=case.reference,
                features=case.features,
            )
            try:
                self.analysis_repository.save(record)
            except sqlite3.IntegrityError as error:
                if error.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY:
                    raise
                continue
            break
        LOGGER_OBJ.info(
            "Исследование %s: CLASS=%s NSP=%s",
            record.record_id,
            record.prediction.pattern.label,
            record.prediction.nsp.label,
        )
        return record
