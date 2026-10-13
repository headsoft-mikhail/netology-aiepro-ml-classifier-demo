import pytest


@pytest.fixture(autouse=True)
def isolated_runtime_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PIPELINE_RUNTIME_DIR", str(tmp_path))
