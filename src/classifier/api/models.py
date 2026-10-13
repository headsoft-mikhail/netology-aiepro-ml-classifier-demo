import typing
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnalysisFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    LB: float
    AC: float
    FM: float
    UC: float
    ASTV: float
    MSTV: float
    ALTV: float
    MLTV: float
    DL: float
    DS: float
    DP: float
    Min: float
    Max: float
    Nmax: float
    Nzeros: float
    Mode: float
    Mean: float
    Median: float
    Variance: float
    Tendency: typing.Literal[-1, 0, 1]
    duration: float = Field(gt=0)


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features: AnalysisFeatures


class Category(BaseModel):
    code: int
    label: str


class AnalysisClassification(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pattern: Category = Field(alias="class")
    nsp: Category


class PredictResponse(BaseModel):
    model: typing.Literal["RandomForest"] = "RandomForest"
    prediction: AnalysisClassification


class DemoCase(BaseModel):
    case_id: str


class DemoAnalysis(DemoCase):
    features: AnalysisFeatures
    reference: AnalysisClassification


class SubmitDemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)


class AnalysisRecord(PredictResponse):
    record_id: str
    case_id: str
    created_at: datetime
    reference: AnalysisClassification


class AnalysisDetails(AnalysisRecord):
    features: AnalysisFeatures


class HealthResponse(BaseModel):
    status: typing.Literal["ok"] = "ok"
