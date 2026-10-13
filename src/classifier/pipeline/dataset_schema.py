import typing
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

PROJECT_ROOT: typing.Final = Path(__file__).resolve().parents[3]


class ClassificationTarget(StrEnum):
    CLASS = "CLASS"
    NSP = "NSP"

    __MAPPINGS__: typing.ClassVar[dict[str, dict[int, str]]] = {
        CLASS: {
            1: "A",
            2: "B",
            3: "C",
            4: "D",
            5: "E",
            6: "AD",
            7: "DE",
            8: "LD",
            9: "FS",
            10: "SUSP",
        },
        NSP: {1: "Normal", 2: "Suspect", 3: "Pathologic"},
    }

    @property
    def mappings(self) -> dict[int, str]:
        return self.__MAPPINGS__[self]

    def mapping(self, code: int) -> str:
        return self.mappings[code]

    def categories(self) -> list[str]:
        return list(self.mappings.values())


@dataclass
class DatasetSchema:
    identifier_columns: list[str] = field(default_factory=lambda: ["FileName", "SegFile"])
    date_columns: list[str] = field(default_factory=lambda: ["Date"])
    timestamp_columns: list[str] = field(default_factory=lambda: ["b", "e"])
    raw_feature_columns: list[str] = field(
        default_factory=lambda: [
            "LBE",
            "LB",
            "AC",
            "FM",
            "UC",
            "ASTV",
            "MSTV",
            "ALTV",
            "MLTV",
            "DL",
            "DS",
            "DP",
            "DR",
            "Width",
            "Min",
            "Max",
            "Nmax",
            "Nzeros",
            "Mode",
            "Mean",
            "Median",
            "Variance",
            "Tendency",
        ],
    )

    @property
    def target_columns(self) -> list[str]:
        return [target.value for target in ClassificationTarget]

    @property
    def categorical_cols(self) -> list[str]:
        return [*self.target_columns, "Tendency"]

    @property
    def pattern_columns(self) -> list[str]:
        return ClassificationTarget.CLASS.categories()

    @property
    def drop_columns(self) -> list[str]:
        return [
            *self.identifier_columns,
            *self.date_columns,
            *self.timestamp_columns,
            *self.pattern_columns,
            "LBE",
            "DR",
            "Width",
        ]

    @property
    def feature_columns(self) -> list[str]:
        return [column for column in self.raw_feature_columns if column not in self.drop_columns] + ["duration"]
