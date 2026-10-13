import dataclasses
import typing

from classifier.api import models
from classifier.pipeline import dataset_schema


@dataclasses.dataclass(kw_only=True, slots=True)
class AppCache:
    demo_cases: dict[str, models.DemoAnalysis] = dataclasses.field(default_factory=dict)
    classifiers: dict[dataset_schema.ClassificationTarget, typing.Any] = dataclasses.field(default_factory=dict)
