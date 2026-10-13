import logging
import typing
from zipfile import ZipFile

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from classifier.pipeline.dataset_schema import DatasetSchema
from classifier.pipeline.settings import PipelineSettings

LOGGER_OBJ: typing.Final = logging.getLogger(__name__)


def prepare_dataset() -> None:
    pipeline_settings: typing.Final = PipelineSettings()
    schema: typing.Final = DatasetSchema()
    workbook: typing.Final = pipeline_settings.raw_dir / pipeline_settings.workbook_filename
    with ZipFile(pipeline_settings.raw_dir / "cardiotocography.zip") as archive:
        workbook.write_bytes(archive.read(pipeline_settings.workbook_filename))
    dataset: typing.Final = pd.read_excel(workbook, sheet_name=pipeline_settings.raw_sheet_name, engine="xlrd")
    cleaned: typing.Final = dataset.dropna().reset_index(drop=True)
    unique: typing.Final = cleaned.drop_duplicates(subset=cleaned.columns.drop("SegFile")).reset_index(drop=True)
    conflicts: typing.Final = (
        unique.groupby(schema.raw_feature_columns, dropna=False)[schema.target_columns]
        .transform("nunique")
        .gt(1)
        .any(axis=1)
    )
    records: typing.Final = unique.loc[~conflicts].reset_index(drop=True)
    pipeline_settings.prepared_dir.mkdir(parents=True, exist_ok=True)
    records.to_csv(pipeline_settings.prepared_dir / "ctg_cleaned.csv", index=False)

    records["duration"] = records["e"] - records["b"]
    features: typing.Final = records.drop(columns=[column for column in schema.drop_columns if column != "FileName"])

    splitter: typing.Final = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=pipeline_settings.random_state)
    folds: typing.Final = pd.Series(index=features.index, dtype="Int64")
    for fold_number, (_, indices) in enumerate(
        splitter.split(features, y=features["CLASS"], groups=features["FileName"]),
    ):
        folds.iloc[indices] = fold_number
    partitions: typing.Final = {
        "train": folds.isin([0, 1, 2]),
        "validation": folds.eq(3),
        "test": folds.eq(4),
    }
    for name, mask in partitions.items():
        prepared = features.loc[mask].drop(columns="FileName")
        prepared.to_csv(pipeline_settings.prepared_dir / f"{name}.csv", index=False)
        LOGGER_OBJ.info(
            "%s: %s записей, %s признаков",
            name,
            len(prepared),
            len(schema.feature_columns),
        )
