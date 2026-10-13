import typing

import fastapi
import modern_di_fastapi

from classifier.api import models
from classifier.api.repositories.analysis_repository import AnalysisRepository
from classifier.api.repositories.cache_repository import AppCache
from classifier.api.repositories.predictions_repository import PredictionsRepository
from classifier.api.use_cases.submit_demo_record_use_case import SubmitDemoRecordUseCase

ROUTER_OBJ: typing.Final = fastapi.APIRouter()


@ROUTER_OBJ.get("/health", response_model=models.HealthResponse, tags=["service"])
def health() -> models.HealthResponse:
    return models.HealthResponse()


@ROUTER_OBJ.post("/predict", response_model=models.PredictResponse, tags=["prediction"])
def predict(
    payload: models.PredictRequest,
    predictions_repository: PredictionsRepository = modern_di_fastapi.FromDI(PredictionsRepository),
) -> models.PredictResponse:
    return predictions_repository.predict(payload)


@ROUTER_OBJ.get("/demo/cases", response_model=list[models.DemoAnalysis], tags=["demo"])
def demo_cases(
    app_cache: AppCache = modern_di_fastapi.FromDI(AppCache),
) -> list[models.DemoAnalysis]:
    return list(app_cache.demo_cases.values())


@ROUTER_OBJ.post("/demo/records", response_model=models.AnalysisRecord, status_code=201, tags=["demo"])
def submit_demo(
    payload: models.SubmitDemoRequest,
    submit_use_case: SubmitDemoRecordUseCase = modern_di_fastapi.FromDI(SubmitDemoRecordUseCase),
) -> models.AnalysisDetails:
    record: typing.Final = submit_use_case(payload)
    if record is None:
        raise fastapi.HTTPException(status_code=404, detail="Контрольный пример не найден")
    return record


@ROUTER_OBJ.get("/records", response_model=list[models.AnalysisDetails], tags=["records"])
def records(
    analysis_repository: AnalysisRepository = modern_di_fastapi.FromDI(AnalysisRepository),
) -> list[models.AnalysisDetails]:
    return analysis_repository.list_records()


@ROUTER_OBJ.get("/records/{record_id}", response_model=models.AnalysisDetails, tags=["records"])
def record_details(
    record_id: str,
    analysis_repository: AnalysisRepository = modern_di_fastapi.FromDI(AnalysisRepository),
) -> models.AnalysisDetails:
    record: typing.Final = analysis_repository.get(record_id)
    if record is None:
        raise fastapi.HTTPException(status_code=404, detail="Исследование не найдено")
    return record


@ROUTER_OBJ.delete("/records/{record_id}", status_code=204, tags=["records"])
def delete_record(
    record_id: str,
    analysis_repository: AnalysisRepository = modern_di_fastapi.FromDI(AnalysisRepository),
) -> fastapi.Response:
    if not analysis_repository.delete(record_id):
        raise fastapi.HTTPException(status_code=404, detail="Исследование не найдено")
    return fastapi.Response(status_code=204)
