import typing
from pathlib import Path

import pandas as pd

from classifier.api import models
from classifier.pipeline import dataset_schema


def load_demo_cases(demo_cases_path: Path) -> dict[str, models.DemoAnalysis]:
    demo_cases: typing.Final = {}
    for row in pd.read_csv(demo_cases_path).to_dict("records"):
        demo_cases[row["case_id"]] = models.DemoAnalysis(
            case_id=row["case_id"],
            features=models.AnalysisFeatures.model_validate(
                {key: value for key, value in row.items() if key not in {"case_id", "CLASS", "NSP"}},
            ),
            reference=models.AnalysisClassification(
                pattern=models.Category(
                    code=int(row["CLASS"]),
                    label=dataset_schema.ClassificationTarget.CLASS.mapping(int(row["CLASS"])),
                ),
                nsp=models.Category(
                    code=int(row["NSP"]),
                    label=dataset_schema.ClassificationTarget.NSP.mapping(int(row["NSP"])),
                ),
            ),
        )

    return demo_cases
