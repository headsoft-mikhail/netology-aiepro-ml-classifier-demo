import typing
from enum import StrEnum


class ClassificationTarget(StrEnum):
    CLASS = "CLASS"
    NSP = "NSP"


class_mapping: typing.Final = {
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
}
nsp_mapping: typing.Final = {1: "Normal", 2: "Suspect", 3: "Pathologic"}

str_cols: typing.Final = ["FileName", "SegFile"]
date_cols: typing.Final = ["Date"]
timestamp_cols: typing.Final = ["b", "e"]
target_cols: typing.Final = [target.value for target in ClassificationTarget]
categorical_cols: typing.Final = [*target_cols, "Tendency"]
class_cols: typing.Final = list(class_mapping.values())

workbook_filename: typing.Final = "CTG.xls"
raw_sheet_name: typing.Final = "Raw Data"
