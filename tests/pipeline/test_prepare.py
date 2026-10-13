import typing
from itertools import combinations
from zipfile import ZipFile

import pandas as pd

from classifier.pipeline.dataset_schema import DatasetSchema
from classifier.pipeline.prepare import prepare_dataset
from classifier.pipeline.settings import PipelineSettings


def test_preparation_keeps_research_groups_separate(monkeypatch):
    pipeline_settings: typing.Final = PipelineSettings()
    schema: typing.Final = DatasetSchema()
    pipeline_settings.raw_dir.mkdir(parents=True)
    with ZipFile(pipeline_settings.raw_dir / "cardiotocography.zip", "w") as archive:
        archive.writestr(pipeline_settings.workbook_filename, b"test workbook")
    rows: typing.Final = [
        {
            **dict.fromkeys(schema.raw_feature_columns, 0),
            "FileName": f"file-{group}",
            "SegFile": f"segment-{group}-{segment}",
            "Date": "2026-01-01",
            "b": segment * 10,
            "e": segment * 10 + 5,
            "LB": group * 10 + segment,
            "LBE": group * 10 + segment,
            "Min": 1,
            "Max": 2,
            "Width": 1,
            "DR": 0,
            "Tendency": 0,
            "CLASS": 1,
            "NSP": 1,
            **dict.fromkeys(schema.pattern_columns, 0),
            "A": 1,
        }
        for group in range(10)
        for segment in range(3)
    ]
    duplicate: typing.Final = {**rows[0], "SegFile": "duplicate"}
    conflicting: typing.Final = {**rows[1], "SegFile": "conflict", "NSP": 2}
    raw: typing.Final = pd.DataFrame([*rows, duplicate, conflicting])
    monkeypatch.setattr(pd, "read_excel", lambda *_args, **_kwargs: raw)

    prepare_dataset()

    parts: typing.Final = [
        pd.read_csv(pipeline_settings.prepared_dir / f"{name}.csv") for name in ["train", "validation", "test"]
    ]
    assert sum(map(len, parts)) == len(rows) - 1
    for part in parts:
        assert len(part.columns) == 23  # noqa: PLR2004 — 21 признак и две цели.
        assert set(part.columns).isdisjoint(schema.drop_columns)
        assert part["duration"].eq(5).all()
        assert not part["LB"].eq(1).any()
    for first, second in combinations(parts, 2):
        assert set(first["LB"] // 10).isdisjoint(second["LB"] // 10)
