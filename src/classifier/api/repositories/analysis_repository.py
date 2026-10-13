import dataclasses
import sqlite3
import typing

from classifier.api import models


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class AnalysisRepository:
    database_connection: sqlite3.Connection

    def save(self, record: models.AnalysisDetails) -> None:
        self.database_connection.execute(
            "INSERT INTO analyses (record_id, created_at, payload) VALUES (?, ?, ?)",
            (record.record_id, record.created_at.isoformat(), record.model_dump_json(by_alias=True)),
        )

    def get(self, record_id: str) -> models.AnalysisDetails | None:
        row: typing.Final = self.database_connection.execute(
            "SELECT payload FROM analyses WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        return models.AnalysisDetails.model_validate_json(row[0]) if row else None

    def list_records(self) -> list[models.AnalysisDetails]:
        rows: typing.Final = self.database_connection.execute(
            "SELECT payload FROM analyses ORDER BY created_at DESC",
        ).fetchall()
        records: typing.Final = [models.AnalysisDetails.model_validate_json(row[0]) for row in rows]
        return sorted(records, key=lambda record: record.prediction.nsp.code, reverse=True)

    def delete(self, record_id: str) -> bool:
        cursor: typing.Final = self.database_connection.execute(
            "DELETE FROM analyses WHERE record_id = ?",
            (record_id,),
        )
        return cursor.rowcount > 0
