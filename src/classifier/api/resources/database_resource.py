import sqlite3

from classifier.api.settings import ServiceSettings


def create_database_connection(service_settings: ServiceSettings) -> sqlite3.Connection:
    return sqlite3.connect(service_settings.database_path, check_same_thread=False, autocommit=True)


def create_analysis_table(database_connection: sqlite3.Connection) -> None:
    database_connection.execute(
        "CREATE TABLE IF NOT EXISTS analyses (record_id TEXT PRIMARY KEY, created_at TEXT, payload TEXT)",
    )
