import sqlite3
import typing
from contextlib import closing
from pathlib import Path

import pandas as pd
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from classifier.api import app as service_app
from classifier.api.resources import database_resource
from classifier.api.settings import ServiceSettings


@pytest.fixture
def api_service_settings(tmp_path, model_directory, analysis_features) -> ServiceSettings:
    service_settings: typing.Final = ServiceSettings(
        models_dir=model_directory,
        database_path=tmp_path / "analyses.db",
        demo_cases_path=tmp_path / "cases.csv",
    )
    pd.DataFrame([{"case_id": "D01", **analysis_features.model_dump(), "CLASS": 3, "NSP": 1}]).to_csv(
        service_settings.demo_cases_path,
        index=False,
    )
    return service_settings


def create_test_client(service_settings: ServiceSettings) -> TestClient:
    return TestClient(service_app.AppBuilder(service_settings=service_settings).app)


def test_health_and_prediction(api_service_settings, analysis_features):
    with create_test_client(api_service_settings) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response: typing.Final = client.post("/predict", json={"features": analysis_features.model_dump()})
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "model": "RandomForest",
            "prediction": {"class": {"code": 2, "label": "B"}, "nsp": {"code": 2, "label": "Suspect"}},
        }


def test_demo_submission_stores_predictions_features_and_reference(api_service_settings, tmp_path):
    with create_test_client(api_service_settings) as client:
        demo_cases: typing.Final = client.get("/demo/cases").json()
        assert demo_cases[0]["case_id"] == "D01"
        assert demo_cases[0]["reference"]["nsp"]["code"] == 1
        assert len(demo_cases[0]["features"]) == 21  # noqa: PLR2004 — входные признаки для страницы.
        first: typing.Final = client.post("/demo/records", json={"case_id": "D01"})
        second: typing.Final = client.post("/demo/records", json={"case_id": "D01"})
        assert first.status_code == status.HTTP_201_CREATED
        record: typing.Final = first.json()
        assert len(record["record_id"]) == 8  # noqa: PLR2004 — согласованный короткий ID.
        assert record["record_id"] != second.json()["record_id"]
        assert record["prediction"]["nsp"]["label"] == "Suspect"
        assert record["reference"] == {"class": {"code": 3, "label": "C"}, "nsp": {"code": 1, "label": "Normal"}}
        assert "features" not in record
        details: typing.Final = client.get(f"/records/{record['record_id']}").json()
        assert len(details["features"]) == 21  # noqa: PLR2004 — входные признаки.
        assert len(client.get("/records").json()) == 2  # noqa: PLR2004 — две отправки.
    assert (tmp_path / "analyses.db").is_file()
    with create_test_client(api_service_settings) as client:
        assert client.get(f"/records/{record['record_id']}").status_code == status.HTTP_200_OK


def test_invalid_and_unknown_requests(api_service_settings, analysis_features):
    with create_test_client(api_service_settings) as client:
        assert client.post("/demo/records", json={"case_id": "unknown"}).status_code == status.HTTP_404_NOT_FOUND
        assert client.get("/records/unknown").status_code == status.HTTP_404_NOT_FOUND
        assert client.post("/predict", json={"features": {}}).status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert (
            client.post(
                "/predict",
                json={"features": {**analysis_features.model_dump(), "NSP": 1}},
            ).status_code
            == status.HTTP_422_UNPROCESSABLE_CONTENT
        )


def test_missing_models_stop_startup(tmp_path):
    service_settings: typing.Final = ServiceSettings(
        models_dir=tmp_path / "missing",
        database_path=tmp_path / "analyses.db",
    )
    with pytest.raises(FileNotFoundError), create_test_client(service_settings):
        pass


def test_request_connections_close_and_application_can_restart(api_service_settings, monkeypatch):
    opened_connections: typing.Final[list[sqlite3.Connection]] = []
    original_connect: typing.Final = sqlite3.connect

    def track_connection(database: Path, *, check_same_thread: bool, autocommit: bool) -> sqlite3.Connection:
        database_connection: typing.Final = original_connect(
            database,
            check_same_thread=check_same_thread,
            autocommit=autocommit,
        )
        opened_connections.append(database_connection)
        return database_connection

    monkeypatch.setattr(database_resource.sqlite3, "connect", track_connection)
    application: typing.Final = service_app.AppBuilder(service_settings=api_service_settings).app
    with TestClient(application) as client:
        assert client.get("/records").status_code == status.HTTP_200_OK
        assert client.get("/records").status_code == status.HTTP_200_OK
        assert len(opened_connections) == 3  # noqa: PLR2004 — startup и два запроса.
        for database_connection in opened_connections:
            with pytest.raises(sqlite3.ProgrammingError):
                database_connection.execute("SELECT 1")
    with TestClient(application) as client:
        assert client.get("/records").status_code == status.HTTP_200_OK
    for database_connection in opened_connections:
        with pytest.raises(sqlite3.ProgrammingError):
            database_connection.execute("SELECT 1")


def test_database_failure_does_not_return_success(api_service_settings):
    with create_test_client(api_service_settings) as client:
        with closing(sqlite3.connect(api_service_settings.database_path, autocommit=True)) as database_connection:
            database_connection.execute(
                "CREATE TRIGGER reject_insert BEFORE INSERT ON analyses "
                "BEGIN SELECT RAISE(FAIL, 'test write error'); END",
            )
        with pytest.raises(sqlite3.IntegrityError):
            client.post("/demo/records", json={"case_id": "D01"})
        assert client.get("/records").json() == []


def test_delete_record_is_persistent(api_service_settings):
    with create_test_client(api_service_settings) as client:
        record_id: typing.Final = client.post("/demo/records", json={"case_id": "D01"}).json()["record_id"]
        assert client.delete(f"/records/{record_id}").status_code == status.HTTP_204_NO_CONTENT
        assert client.get("/records").json() == []
        assert client.delete(f"/records/{record_id}").status_code == status.HTTP_404_NOT_FOUND
    with create_test_client(api_service_settings) as client:
        assert client.get(f"/records/{record_id}").status_code == status.HTTP_404_NOT_FOUND
